"""Coordinator-owned mock input, immutable plan and bounded design lifecycle."""
import json,time,resource,os,signal,gc,secrets,contextvars
from pathlib import Path
from contextlib import contextmanager
from fractions import Fraction as F
from src.smz import abc,d,common
from src.smz_real_adapter import adapter
from src.smz_sealed_v2.core import compile_plan as old_plan,bindings as old_bindings
from . import codec,basis,native_d
from .storage import Store,need,Blocked,file_sha,durable
ROOT=Path(__file__).resolve().parents[2]
PACKAGE=ROOT/'outputs/smz_architecture_b/20260929_v1'
_ACCESS=contextvars.ContextVar('ARCH_B_ACCESS',default=None)
def guard_rows(rows):need(_ACCESS.get() is rows,'COORDINATOR_QUALIFIED_INPUT_REQUIRED')
def guard_row(row):need(_ACCESS.get() is not None and any(r is row for r in _ACCESS.get()),'AUTHORIZED_RECONSTRUCTION_REQUIRED')
@contextmanager
def _access(rows):
    token=_ACCESS.set(rows)
    try:yield
    finally:_ACCESS.reset(token)
def code_hashes():return {str(p.relative_to(ROOT)):file_sha(p) for p in sorted((ROOT/'src/smz_arch_b_verified').glob('*.py'))}
_LOADED_CODE_HASHES=code_hashes()
def plan():
    need(code_hashes()==_LOADED_CODE_HASHES,'LOADED_CODE_CHANGED_RESTART_REQUIRED')
    old=old_plan()
    return dict(version='SMZ_ARCH_B_PLAN_1',contract=adapter.CONTRACT,bindings=old['bindings'],architecture=file_sha(PACKAGE/'architecture_spec.md'),
        architecture_code=code_hashes(),cells=old['cells'],default=old['default'],D_primary='D0',S3=old['S3'])
def verify_plan(p):need(codec.digest(p)==codec.digest(plan()),'PLAN_MUTATION_OR_UNKNOWN_CELL')
def preflight(mock=True):
    need(json.loads((PACKAGE/'preflight/result.json').read_text())['status']=='PASS','CLEAN_PREFLIGHT_REQUIRED')
    need(file_sha(PACKAGE/'architecture_spec.md')==(PACKAGE/'architecture_spec.sha256').read_text().split()[0],'ENGINEERING_SPEC_CHANGED')
    if mock:need(not (ROOT/'outputs/smz_execution_authorization/trust_anchor.json').exists(),'REAL_AUTHORIZATION_UNEXPECTED')
    old_bindings()

class Meter:
    """One process, cumulative family clocks; shared phases charged to both."""
    def __init__(self,limits=None):
        self.limits=limits or {'ABC':(14400,16*1024**3,4),'D':(3600,8*1024**3,1)}
        self.elapsed={'ABC':0.,'D':0.};self.peak={'ABC':0,'D':0};self.phase='shared';self.last=time.monotonic();self.started=self.last
    def check(self,*_):
        now=time.monotonic();dt=now-self.last;self.last=now
        rss=int(Path('/proc/self/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')
        children=Path('/proc/self/task/'+str(os.getpid())+'/children').read_text().split()
        processes=1+len(children)
        for pid in children:
            try:rss+=int(Path('/proc/'+pid+'/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')
            except FileNotFoundError:pass
        for fam in ('ABC','D') if self.phase=='shared' else (self.phase,):
            self.elapsed[fam]+=dt;self.peak[fam]=max(self.peak[fam],rss)
            wall,ram,procs=self.limits[fam]
            need(self.elapsed[fam]<=wall and rss<=ram and processes<=procs,'RESOURCE_STOP_'+fam)
    def switch(self,phase):self.check();self.phase=phase
    def report(self):
        self.check();return dict(status='PASS',family_wall_seconds={k:int(v*1000) for k,v in self.elapsed.items()},time_unit='milliseconds',peak_bytes=self.peak.copy(),processes=1,whole_wall_milliseconds=int((time.monotonic()-self.started)*1000),shared_charged_to_both=True)
    def __enter__(self):
        self.handler=signal.getsignal(signal.SIGALRM);signal.signal(signal.SIGALRM,self.check);signal.setitimer(signal.ITIMER_REAL,.2,.2);return self
    def __exit__(self,*exc):signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,self.handler)

SOURCE_FIELDS=('uuid','region','tik','n','issued','valid',*('p'+str(j) for j in range(10)),'invalid','source_variant','source_id','source_sha256','selector_commitment')
def source_record(r,metadata):return (r.uuid,r.region,r.tik,r.n,r.issued,r.valid,*r.parties,common.UNKNOWN if r.invalid is None else r.invalid,metadata.source_variant,metadata.source_id,metadata.source_sha256,metadata.selector_commitment)
def row_from_record(r):return common.Row(r[0],r[1],r[2],r[3],r[4],r[5],tuple(r[6:16]),None if r[16]==common.UNKNOWN else r[16])
def emit_table(tx,prefix,records,fields,chunk=1024):
    batch=[];chunks=[];count=0
    for r in records:
        batch.append(r);count+=1
        if len(batch)==chunk:
            name=prefix+'/'+str(len(chunks));tx.put(name,codec.columnar(batch,fields));chunks.append(name);batch=[]
    if batch:
        name=prefix+'/'+str(len(chunks));tx.put(name,codec.columnar(batch,fields));chunks.append(name)
    tx.put(prefix+'/index',dict(fields=fields,chunks=tuple(chunks),rows=count));return prefix+'/index'
def emit_basis(tx,prefix,rows,b):
    index=emit_table(tx,prefix+'/status',((i,b['ranks'][i],s,b['donor_ids'][i]) for i,s in enumerate(b['statuses'])),('source_index','rank','status','donor_set'))
    donors=emit_table(tx,prefix+'/donors',((i,v) for i,v in enumerate(b['donor_sets'])),('donor_set','source_indices'))
    sparse=emit_table(tx,prefix+'/basis',((i,*v) for i,v in b['sparse'].items()),('source_index','donor_set','M','K','L','P','H','d','U'))
    roots={name:tx.index[name]['semantic'] for name in tx.index if name.startswith(prefix+'/')}
    return tx.put(prefix+'/root',dict(design=b['design'],source_rows=len(rows),status_index=index,donor_index=donors,basis_index=sparse,dependencies=roots))

class Coordinator:
    def __init__(self,root):self.root=Path(root);self._store=None
    @property
    def store(self):
        if self._store is None:self._store=Store(self.root)
        return self._store
    def run_real(self,run_id,authorization=None):
        return self._run(None,None,run_id,mode='real',authorization=authorization)
    def run_mock(self,bundle,expected_hash,run_id,*,limits=None,failpoint=None,only=None,probe_sources=None):
        return self._run(bundle,expected_hash,run_id,limits=limits,failpoint=failpoint,only=only,probe_sources=probe_sources)
    def _run(self,bundle,expected_hash,run_id,*,limits=None,failpoint=None,only=None,probe_sources=None,mode='mock',authorization=None):
        # Timer starts before binding/plan/source validation. No actual source loader here.
        with Meter(limits) as meter:
            need(mode in ('mock','real'),'EXECUTION_MODE');preflight(mock=mode=='mock');p=plan();verify_plan(p)
            if mode=='mock':
                need(codec.sha(bundle.manifest_bytes)==expected_hash,'MOCK_BUNDLE_HASH')
                load=lambda variant:adapter.qualify_mock(bundle,variant,expected_manifest_sha256=expected_hash,run_id='mock:'+run_id,created_at='2026-09-29T00:00:00Z')
            else:
                need(limits is None and failpoint is None and only is None and probe_sources is None,'REAL_EXECUTION_NO_TEST_OPTIONS')
                from .authorization import provider
                load=provider(authorization,run_id,p)
            if only:need(set(only)<=set(abc.DESIGNS)|set(d.SPECS),'UNKNOWN_PROBE_SPEC')
            if probe_sources:need(only and set(probe_sources)<=set(adapter.VARIANTS),'UNKNOWN_PROBE_SOURCE')
            need(failpoint in (None,'before_first','mid_ABC','between_families','after_calculation','after_serialization','after_manifest','commit_write','missing_basis','missing_cell','duplicate_cell','semantic_mismatch','physical_mismatch','parameter_mutation','after_release_resource','verified_cache_mutation'),'UNKNOWN_TEST_FAULT')
            tx=self.store.begin(run_id,p)
            try:
                if failpoint=='before_first':raise Blocked('INJECTED_CRASH')
                for variant in adapter.VARIANTS:
                    if probe_sources and only and variant not in probe_sources:continue
                    meter.switch('shared')
                    frame=load(variant)
                    provenance=adapter.verify_frame(frame)
                    need(frame.source_variant==variant and provenance['contract_sha256']==adapter.CONTRACT and provenance['implementation_manifest_sha256']==adapter.IMPLEMENTATION,'SOURCE_VARIANT_PROVENANCE')
                    need(frame.origin==('SMZ_MOCK_REAL_ADAPTER_QUALIFICATION' if mode=='mock' else 'SMZ_CLOSED_REAL_ADAPTER'),'ORIGIN_MODE')
                    rows=tuple(common.Row(r.uuid,r.region,r.tik_uuid,r.voters,r.issued,r.valid,r.parties,r.known_invalid.value) for r in frame.rows)
                    if mode=='mock':need(all(r.uuid.startswith('mock:') for r in rows),'REAL_PROVENANCE_IN_MOCK')
                    sr='source_frames/'+variant;emit_table(tx,sr+'/table',(source_record(r,meta) for r,meta in zip(rows,frame.rows)),SOURCE_FIELDS)
                    source_root=tx.put(sr+'/root',dict(provenance=provenance,dependencies={k:v['semantic'] for k,v in tx.index.items() if k.startswith(sr+'/')}))
                    del frame
                    with _access(rows):
                        meter.switch('ABC')
                        for design in abc.DESIGNS:
                            if only and design not in only:continue
                            b=basis.build(rows,design);prefix='abc_design/'+variant+'/'+design
                            br=emit_basis(tx,prefix,rows,b);agg=basis.aggregate_basis(rows,b)
                            ar=tx.put(prefix+'/aggregate_basis',agg)
                            for cell in p['cells']:
                                if cell['family']!='ABC' or cell['source']!=variant or cell['spec']!=design:continue
                                lam=F(cell['lambda_quarters'],4);mu=F(cell['mu_quarters'],4)
                                result=dict(engine='ABC',source_id=variant,design_id=design,lambda_=lam,mu=mu,status='APPLICABLE' if b['sparse'] else 'NOT_APPLICABLE_ON_THIS_DESIGN',scopes={name:basis.evaluate(scope,lam,mu) for name,scope in agg.items()})
                                tx.cell(cell,result,{sr+'/root':source_root,prefix+'/root':br,prefix+'/aggregate_basis':ar})
                            del b,agg,result
                            if failpoint=='mid_ABC':raise Blocked('INJECTED_CRASH')
                        gc.collect();meter.switch('D')
                        if failpoint=='between_families':raise Blocked('INJECTED_CRASH')
                        for spec in d.SPECS:
                            if only and spec not in only:continue
                            prefix='D/'+variant+'/'+spec;strata=[]
                            def emit(name,value):
                                path=prefix+'/strata/'+name;tx.put(path,value);strata.append(path)
                            result=native_d.run(rows,spec,emit);result['source_id']=variant
                            dr=tx.put(prefix+'/root',dict(strata=strata,dependencies={k:tx.index[k]['semantic'] for k in strata}))
                            cell=next(c for c in p['cells'] if c['family']=='D' and c['source']==variant and c['spec']==spec)
                            tx.cell(cell,result,{sr+'/root':source_root,prefix+'/root':dr})
                            del result
                    del rows;gc.collect()
                meter.switch('shared')
                if failpoint=='after_calculation':raise Blocked('INJECTED_CRASH')
                if only:
                    report=meter.report();tx.put('probe_resources',report)
                    return dict(status='TARGETED_PROBE_NOT_COMMITTED',resources=report,bytes=sum(x.stat().st_size for x in tx.path.rglob('*') if x.is_file()),cells=len(tx.ledger))
                if failpoint=='missing_basis':(tx.path/next(k for k in tx.index if '/basis/' in k)).unlink()
                if failpoint=='missing_cell':tx.ledger.pop()
                if failpoint=='duplicate_cell':tx.ledger.append(tx.ledger[0])
                if failpoint=='semantic_mismatch':tx.index[next(k for k in tx.index if '/basis/' in k)]['semantic']='0'*64
                if failpoint=='physical_mismatch':
                    k=next(k for k in tx.index if '/basis/' in k);(tx.path/k).write_bytes(b'corrupt')
                if failpoint=='parameter_mutation':tx.ledger[0]['parameters']['lambda_quarters']=5
                return tx.finish(meter,failpoint)
            except BaseException as e:
                # A timer/late return failure must revoke any just-published receipt.
                release=self.store.root/'vault'/(run_id+'.release')
                if release.exists():
                    os.rename(release,self.store.root/'vault'/(run_id+'.failed_release'))
                    committed=self.store.root/'committed'/run_id
                    if committed.exists():os.rename(committed,tx.path)
                if tx.path.exists():
                    done={x['id']:x for x in tx.ledger}
                    failed_ledger=tuple(done.get(c['id'],dict(id=c['id'],terminal='FROZEN_STOP',reason=type(e).__name__)) for c in p['cells'])
                    if not (tx.path/'failed_ledger').exists():durable(tx.path/'failed_ledger',codec.encode(failed_ledger))
                    evidence=dict(status='STOP',category=type(e).__name__,message=str(e),terminal_cells=len(tx.ledger),real_party_rows=0)
                    if not (tx.path/'failure').exists():durable(tx.path/'failure',codec.encode(evidence))
                raise
