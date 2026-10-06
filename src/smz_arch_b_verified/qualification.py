"""Fresh mock-only qualification entry points; project data tree denied at runtime."""
import sys,json,time,resource,copy,shutil,os,traceback
from pathlib import Path
from fractions import Fraction as F
from src.smz import abc,d,common
from src.smz_real_adapter import adapter
from src.smz_sealed_v2.qualification import fixture
from src.smz_sealed_v2.core import KernelSession
from src.smz_sealed_v2.authorization import _activate,_revoke
from . import codec,basis,native_d,fixtures
from .engine import Coordinator,Store,plan,_access,preflight,PACKAGE,ROOT
from .storage import need,Blocked
from .reader import Reader
from src.smz_arch_b_publication import publication,website
def save(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def deny_data(event,args):
    if event=='open' and isinstance(args[0],(str,bytes)):
        p=Path(os.fsdecode(args[0])).absolute()
        if p.is_relative_to(ROOT/'data'):raise Blocked('REAL_PARTY_IO_FORBIDDEN')
def stats(start):return dict(wall_seconds=time.monotonic()-start,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,processes=1,real_party_rows_processed=0)

def equivalence(out):
    bundle,_,_=fixture();frames={v:adapter.qualify_mock(bundle,v,expected_manifest_sha256=codec.sha(bundle.manifest_bytes),run_id='mock:oracle',created_at='2026-09-29T00:00:00Z') for v in adapter.VARIANTS}
    cap=_activate('arch_b_oracle','mock_sealed_execution',{v:adapter.verify_frame(f)['input_frame_sha256'] for v,f in frames.items()},'MOCK_ONLY')
    session=KernelSession(frames,cap);checks=[];rows_compared=0;cells=plan()['cells']
    try:
        for v in adapter.VARIANTS:
            rows=session.views[v].rows
            with _access(rows):
                for design in abc.DESIGNS:
                    b=basis.build(rows,design);agg=basis.aggregate_basis(rows,b)
                    for li in range(5):
                        for mi in range(5):
                            cell=next(c for c in cells if c['family']=='ABC' and c['source']==v and c['spec']==design and c['lambda_quarters']==li and c['mu_quarters']==mi)
                            oracle=session.calculate(cell);lam=F(li,4);mu=F(mi,4)
                            reconstructed=tuple(basis.reconstruct(r,b['statuses'][i],b['sparse'].get(i),lam,mu) for i,r in enumerate(rows))
                            need(reconstructed==oracle['rows'],'EXACT_ROW_EQUIVALENCE');rows_compared+=len(rows)
                            full=basis.evaluate(agg['full'],lam,mu);native=basis.evaluate(agg['native'],lam,mu)
                            for field in ('parties','delta','composition','intensity','interaction'):
                                need(full['scenario_parties' if field=='parties' else field]==oracle['aggregate'][field],'ABC_AGGREGATE_'+field)
                            need(full['scenario_valid']==oracle['scenario_valid'] and full['coverage']==oracle['coverage'] and full['actually_transformed_units']==oracle['actually_transformed_units'],'ABC_STRUCTURE')
                            need(native['scenario_parties']==oracle['native']['scenario_parties'] and native['source_parties']==oracle['native']['source_parties'],'ABC_NATIVE')
                            for name,scope in agg.items():
                                if not name.startswith('region:'):continue
                                rr=[x for x,r in zip(reconstructed,rows) if r.region==name[7:]]
                                need(basis.evaluate(scope,lam,mu)['scenario_parties']==tuple(sum(x['parties'][j] for x in rr) for j in range(10)),'ABC_REGION')
                            checks.append(dict(id=cell['id'],status='PASS'))
                    print('EQUIVALENT',v,design,flush=True)
                for spec in d.SPECS:
                    captured={};r=native_d.run(rows,spec,lambda k,x:captured.setdefault(k,x));r['source_id']=v
                    cell=next(c for c in cells if c['family']=='D' and c['source']==v and c['spec']==spec)
                    oracle=session.calculate(cell)
                    need({k:native_d.expand(x) for k,x in captured.items()}==oracle['strata'],'D_NATIVE_EQUIVALENCE')
                    need(r=={k:x for k,x in oracle.items() if k!='strata'},'D_AGGREGATE_EQUIVALENCE');checks.append(dict(id=cell['id'],status='PASS'))
    finally:_revoke(cap)
    save(out/'equivalence.json',dict(status='PASS',canonical_cells=len(checks),ABC=1600,D=20,exact_rows_compared=rows_compared,checks=checks))

def boundaries(out):
    checks=[]
    def ok(name,fn):fn();checks.append(dict(id=name,status='PASS'))
    def eq(a,b):need(a==b,'BOUNDARY_EQUIVALENCE')
    def frame_test(multiplier=1):
        rows=[]
        for i in range(40):
            n=(1000+(i%5)*250)*multiplier;I=(200+i*17)*multiplier;V=I-20*multiplier;p=[V//10]*10;p[0]+=V-sum(p)
            rows.append(common.Row('syn:'+str(i).zfill(3),'syn:r','syn:t',n,I,V,tuple(p),None if i%2 else 3*multiplier))
        f=common.SyntheticFrame('syn:arch-b-boundary',tuple(rows),'primary')
        with _access(f.rows):
            for design in abc.DESIGNS:
                b=basis.build(f.rows,design);old=abc.build(f,design)
                for lam in common.LEVELS:
                    for mu in common.LEVELS:
                        eq(tuple(basis.reconstruct(r,b['statuses'][i],b['sparse'].get(i),lam,mu) for i,r in enumerate(f.rows)),abc.transform(old,lam,mu)['rows'])
    ok('all_designs_grids_diverse_calipers_known_unknown',frame_test)
    ok('arbitrary_precision_products',lambda:frame_test(10**35+39))
    ok('binary_roundtrip_beyond_decimal_digit_limit',lambda:eq(codec.decode(codec.encode(F(10**10000+7,10**9999+9))),F(10**10000+7,10**9999+9)))
    ok('zero_valid_reference_status',lambda:eq(abc.donor_status([1],[common.Row('syn:x','syn:r','syn:t',100,10,0,(0,)*10,None)]*5,5),'ZERO_REFERENCE_VALID'))
    for h in (F(1,200),F(1,100)):
        ok('bin_boundaries_'+str(h),lambda h=h:eq(tuple(d.bin_index(i,1000,h) for i in (0,5,10,1000)),tuple(min(int(F(i,1000)/h),int(1/h)-1) for i in (0,5,10,1000))))
    rows=[common.Row('syn:'+str(i),'syn:r','syn:t',1000,500,490,(49,)*10,None) for i in range(40)]
    with _access(tuple(rows)):
        ok('all_equal_midrank',lambda:eq(set(abc.midranks(rows).values()),{F(1,2)}))
    ok('unknown_invalid_codec',lambda:eq(codec.decode(codec.encode(common.UNKNOWN)),common.UNKNOWN))
    save(out/'boundaries.json',dict(status='PASS',checks=checks))

def run_production(out,n,only=None,large=False):
    bundle,meta=fixtures.generated(n,large);save(out/'fixture_manifest.json',meta)
    co=Coordinator(out/'store')
    result=co.run_mock(bundle,codec.sha(bundle.manifest_bytes),'complete',only=only,probe_sources=('primary',) if large else None)
    save(out/'rehearsal.json',result);return result

def read_export(out,storepath):
    co=Coordinator(storepath);token=co.store.authorize('complete');reader=Reader(co.store,'complete',token)
    cid='ABC:primary:R1-T1-D1-M2:L4:M4';result=reader.cell(cid);need(result['engine']=='ABC','READER')
    r=reader.target(cid,0);need(r['uuid'].startswith('mock:'),'TARGET_RECONSTRUCTION');need(reader.target('D:primary:D0',0)==common.NOT_DEFINED,'D_NO_UIK')
    need(len(reader.compare([cid,'D:primary:D0']))==2,'BOUNDED_COMPARE')
    need(len(reader.surface('primary','R1-T1-D1-M2'))==25,'SURFACE')
    publication(co.store,'complete',token,out/'P');website(out/'P',out/'W')
    def size(p):return sum(x.stat().st_size for x in p.rglob('*') if x.is_file())
    save(out/'exports.json',dict(status='PASS',R_bytes=size(Path(storepath)/'committed/complete'),P_bytes=size(out/'P'),W_bytes=size(out/'W'),W_initial_bytes=(out/'W/initial.json.gz').stat().st_size,W_max_lazy_bytes=max(x.stat().st_size for x in (out/'W').glob('*.json.gz') if x.name!='initial.json.gz')))

def safety(out):
    bundle,_,_=fixture();co=Coordinator(out/'store');h=codec.sha(bundle.manifest_bytes);checks=[]
    def no(name,fn):
        try:fn()
        except (Exception,) as e:checks.append(dict(id=name,status='PASS',rejected=type(e).__name__));return
        raise AssertionError('NOT_REJECTED:'+name)
    no('real_loading_blocked',lambda:co.run_real('primary'))
    no('raw_basis_blocked',lambda:basis.build((),abc.DESIGNS[0]))
    no('synthetic_endpoint_rejects_realframe',lambda:common.guard(adapter.qualify_mock(bundle,'primary',expected_manifest_sha256=h,run_id='mock:guard',created_at='2026-09-29T00:00:00Z')))
    no('precommit_reader',lambda:co.store.authorize('absent'))
    for point in ('before_first','mid_ABC','between_families','after_calculation','after_serialization','after_manifest','commit_write','missing_basis','missing_cell','duplicate_cell','semantic_mismatch','physical_mismatch','parameter_mutation','after_release_resource','verified_cache_mutation'):
        run='crash_'+point;no(point,lambda run=run,point=point:co.run_mock(bundle,h,run,failpoint=point));no(point+'_reveal',lambda run=run:co.store.authorize(run))
    for name,limits in [('wall',{'ABC':(0,16*1024**3,4),'D':(3600,8*1024**3,1)}),('RAM',{'ABC':(14400,1,4),'D':(3600,8*1024**3,1)}),('process',{'ABC':(14400,16*1024**3,0),'D':(3600,8*1024**3,1)})]:
        no('resource_'+name,lambda name=name,limits=limits:co.run_mock(bundle,h,'stop_'+name,limits=limits));no('resource_reveal_'+name,lambda name=name:co.store.authorize('stop_'+name))
    for name,lim in [('D_wall',(0,8*1024**3,1)),('D_RAM',(3600,1,1)),('D_process',(3600,8*1024**3,0))]:
        no(name,lambda name=name,lim=lim:co.run_mock(bundle,h,'stop_'+name,limits={'ABC':(14400,16*1024**3,4),'D':lim}))
    co.run_mock(bundle,h,'complete');token=co.store.authorize('complete')
    co.run_mock(bundle,h,'replay');replay=co.store.authorize('replay')
    p,m,_,_=co.store.verify('complete');_,m2,_,_=co.store.verify('replay')
    # Run identifiers are provenance metadata; science cell results must be identical.
    for name in m['artifacts']:
        if name.startswith('cells/'):need(m['artifacts'][name]['semantic']==m2['artifacts'][name]['semantic'],'DETERMINISTIC_RESULTS')
    checks.append(dict(id='complete_1620_and_deterministic_replay',status='PASS'))
    no('token_other_run',lambda:co.store.read('replay',token,'plan'))
    no('arbitrary_path',lambda:co.store.read('../complete',token,'plan'))
    for name in ('plan','ledger','manifest','commit',next(n for n in m['artifacts'] if '/basis/' in n),next(n for n in m['artifacts'] if n.endswith('/aggregate_basis'))):
        original=(p/name).read_bytes();(p/name).write_bytes(original+b'CORRUPT')
        no('corruption_'+name,lambda:co.store.read('complete',token,'plan'));(p/name).write_bytes(original)
    (p/'unregistered').write_bytes(b'not a result');no('unregistered_file',lambda:co.store.authorize('complete'));(p/'unregistered').unlink()
    name=next(n for n in m['artifacts'] if '/basis/' in n);original=(p/name).read_bytes();(p/name).unlink();no('missing_basis',lambda:co.store.authorize('complete'));(p/name).write_bytes(original)
    stat=(p/name).stat();changed=bytearray(original);changed[-1]^=1;(p/name).write_bytes(changed);os.utime(p/name,ns=(stat.st_atime_ns,stat.st_mtime_ns));no('cache_invalidation_with_mtime_preserved',lambda:co.store.authorize('complete'));(p/name).write_bytes(original)
    from .storage import validate_ledger
    ledger=co.store.read('complete',token,'ledger');pp=plan()
    for label,ll in [('missing',ledger[:-1]),('duplicate',ledger+(ledger[0],)),('extra',ledger+({'id':'X'},))]:no(label+'_cell',lambda ll=ll:validate_ledger(pp,ll,m['artifacts']))
    changed=copy.deepcopy(pp);changed['cells'][0]['source']='S3'
    from .engine import verify_plan
    no('S3_cell',lambda:verify_plan(changed));changed=copy.deepcopy(pp);changed['cells'][0]['lambda_quarters']=5;no('parameter_substitution',lambda:verify_plan(changed))
    no('partial_reuse',lambda:co.run_mock(bundle,h,'crash_before_first'))
    no('wrong_bundle',lambda:co.run_mock(bundle,'0'*64,'bad_bundle'))
    raw=common.Row('mock:raw','mock:r','mock:t',100,90,80,(8,)*10,None)
    no('direct_raw_reconstruction',lambda:basis.reconstruct(raw,'SUPPORTED',None,F(1),F(1)))
    changed=copy.deepcopy(pp);changed['contract']='0'*64;no('wrong_contract_plan',lambda:verify_plan(changed))
    changed=copy.deepcopy(pp);changed['cells'][0]['spec']='UNKNOWN';no('unknown_design',lambda:verify_plan(changed))
    changed=copy.deepcopy(pp);changed['cells'][0]['source']='UNKNOWN';no('unknown_source',lambda:verify_plan(changed))
    save(out/'safety.json',dict(status='PASS',checks=checks,canonical_cells=1620,real_party_rows=0))

def main():
    sys.addaudithook(deny_data);mode=sys.argv[1];out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=False);start=time.monotonic()
    save(out/'start.json',dict(mode=mode,preflight_sha256=adapter.file_sha(PACKAGE/'preflight/result.json'),architecture_sha256=adapter.file_sha(PACKAGE/'architecture_spec.md')))
    try:
        preflight()
        if mode=='equivalence':equivalence(out);boundaries(out)
        elif mode=='safety':safety(out)
        elif mode=='probe':run_production(out,int(sys.argv[3]),only=('R1-T1-D1-M2','R2-T1-D2-M1','D0','D4'))
        elif mode=='near':run_production(out,87736)
        elif mode=='stress':run_production(out,25000,only=('R2-T1-D2-M1',),large=True)
        elif mode=='export':read_export(out,sys.argv[3])
        else:raise ValueError('UNKNOWN_QUALIFICATION_MODE')
        save(out/'result.json',dict(status='PASS',**stats(start)))
    except BaseException as e:
        save(out/'result.json',dict(status='FAIL',error=repr(e),traceback=traceback.format_exc(),**stats(start)));raise
if __name__=='__main__':main()
