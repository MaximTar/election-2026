"""Plan, capability-bound unchanged kernels, and exact runtime reconciliation."""
from dataclasses import dataclass
from fractions import Fraction as F
from pathlib import Path
import hashlib,json,types
from src.smz import abc,d,common
from src.smz_real_adapter import adapter as a
VERSION='SMZ_SEALED_COORDINATOR_v2_ATTEMPT02'
ROOT=Path(__file__).resolve().parents[2]
ADAPTER_MANIFEST='87510d1e1c12ed1d67cb0e708bdede03875a7055fd7acb0ada71893405e3fd85'
class SealError(RuntimeError):pass
def need(ok,code):
    if not ok:raise SealError(code)
def _wire(x):
    # Exact same wire algebra as qualified common.wire; fast primitive dispatch.
    if type(x) in (str,int,bool):return x
    if isinstance(x,F):return {'status':'DEFINED','numerator':x.numerator,'denominator':x.denominator}
    if isinstance(x,dict):return {str(k):_wire(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)):return [_wire(v) for v in x]
    return common.wire(x)
def enc(x):return json.dumps(_wire(x),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
_HASH_CACHE={}
def file_hash(path):
    path=Path(path);st=path.stat();key=(str(path),st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)
    if key not in _HASH_CACHE:
        value=a.file_sha(path);after=path.stat()
        need((st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'FILE_CHANGED_WHILE_HASHING');_HASH_CACHE[key]=value
    return _HASH_CACHE[key]
def hashes():
    return {str(p.relative_to(ROOT)):file_hash(p) for folder in ('src/smz','src/smz_real_adapter','src/smz_sealed_v2') for p in sorted((ROOT/folder).glob('*.py'))}
def bindings():
    for relative,expected in [('outputs/scenario_model_zoo_implementation/20260929_v1/manifest.json',a.IMPLEMENTATION),('outputs/smz_real_party_adapter/20260929_v1/manifest.json',ADAPTER_MANIFEST)]:
        mp=ROOT/relative;need(file_hash(mp)==expected,'BINDING_MANIFEST_HASH')
        for path,h in json.loads(mp.read_text())['files'].items():
            if path.startswith(('src/smz/','src/smz_real_adapter/')):need(file_hash(ROOT/path)==h,'FROZEN_CODE_HASH')
    need(file_hash(ROOT/'docs/SCENARIO_MODEL_ZOO_CONTRACT_20260929_V1.md')==a.CONTRACT,'FROZEN_CONTRACT_HASH')
    hh=hashes()
    return dict(contract_sha256=a.CONTRACT,implementation_manifest_sha256=a.IMPLEMENTATION,adapter_manifest_sha256=ADAPTER_MANIFEST,
                source_profile_sha256=file_hash(a.PROFILE),coordinator_version=VERSION,code_hashes=hh,coordinator_code_sha256=sha(enc({k:v for k,v in hh.items() if '/smz_sealed_v2/' in k})))
def compile_plan():
    cells=[]
    for source in a.VARIANTS:
        for design in abc.DESIGNS:
            for li in range(5):
                for mi in range(5):
                    cells.append(dict(id=f'ABC:{source}:{design}:L{li}:M{mi}',family='ABC',source=source,spec=design,lambda_quarters=li,mu_quarters=mi,
                                      aliases=(['A'] if mi==0 else [])+(['B'] if li==0 else [])))
        for spec in d.SPECS:cells.append(dict(id=f'D:{source}:{spec}',family='D',source=source,spec=spec))
    for c in cells:
        c['dependencies']=['qualified:'+c['source'],'original_source_only','ABC_shared_reference:'+c['spec'] if c['family']=='ABC' else 'D_independent_histogram:'+c['spec']]
        c['permitted_terminal_states']=['COMPUTED','CONTRACT_UNSUPPORTED','FROZEN_STOP','IMPLEMENTATION_FAILURE']
    cells.sort(key=lambda c:c['id'])
    return dict(version='SMZ-2026-v1',bindings=bindings(),cells=cells,terminal_states=['COMPUTED','CONTRACT_UNSUPPORTED','FROZEN_STOP','IMPLEMENTATION_FAILURE'],S3='IDENTITY_WITH_PRIMARY_NOT_EXECUTED',default='R1-T1-D1-M2',D_primary='D0')
def verify_plan(plan):
    need(enc(plan)==enc(compile_plan()),'PLAN_MUTATION_OR_UNKNOWN_CELL')
    need(len(plan['cells'])==1620 and len({c['id'] for c in plan['cells']})==1620,'PLAN_ACCOUNTING')

@dataclass(frozen=True)
class _KernelView:
    rows:tuple
    source_id:str
    origin:str
    attestation:str

class KernelSession:
    """Private per-transaction namespace; no mutation of global scientific modules.

    Scientific function code objects are identical. Only input validation/guard bindings
    differ. No SyntheticFrame, syn: ID, or global guard relaxation is used.
    """
    def __init__(self,frames,capability):
        from .authorization import verify_capability
        verify_capability(capability,frames)
        self._check=lambda:verify_capability(capability)
        self.frames=frames;self.views={};self.designs={}
        for variant,frame in frames.items():
            prov=a.verify_frame(frame)
            need(frame.source_variant==variant and prov['contract_sha256']==a.CONTRACT,'FRAME_PROVENANCE')
            rows=tuple(common.Row(r.uuid,r.region,r.tik_uuid,r.voters,r.issued,r.valid,r.parties,r.known_invalid.value) for r in frame.rows)
            self.views[variant]=_KernelView(rows,variant,frame.origin,prov['input_frame_sha256'])
        def guard(view,*args):
            self._check();need(any(view is x for x in self.views.values()),'COORDINATOR_CAPABILITY_REQUIRED');return view
        def validate(view):
            guard(view);a.verify_frame(self.frames[view.source_id]);return tuple(sorted(view.rows,key=lambda r:r.uuid))
        def bind(module):
            ns=dict(vars(module));ns.update(guard=guard,validate=validate)
            for name,value in vars(module).items():
                if isinstance(value,types.FunctionType) and value.__module__==module.__name__:
                    f=types.FunctionType(value.__code__,ns,value.__name__,value.__defaults__,value.__closure__);f.__kwdefaults__=value.__kwdefaults__;ns[name]=f
            return ns
        self.abc=bind(abc);self.d=bind(d)
    def calculate(self,cell):
        self._check();v=self.views[cell['source']]
        if cell['family']=='ABC':
            key=(cell['source'],cell['spec'])
            if key not in self.designs:self.designs[key]=self.abc['build'](v,cell['spec'])
            result=self.abc['transform'](self.designs[key],F(cell['lambda_quarters'],4),F(cell['mu_quarters'],4))
        else:result=self.d['execute'](v,cell['spec'])
        reconcile_cell(cell,result,v.rows)
        return result

def reconcile_cell(cell,r,source):
    need(r['source_id']==cell['source'],'SOURCE_RESULT_MISMATCH')
    original={x.uuid:x for x in source};st=common.totals(source)
    need(r['source_parties']==st and r['source_valid']==sum(st),'SOURCE_RECONCILIATION')
    if cell['family']=='ABC':
        need(r['design_id']==cell['spec'] and r['lambda']==F(cell['lambda_quarters'],4) and r['mu']==F(cell['mu_quarters'],4),'PARAMETERS')
        need({x['uuid'] for x in r['rows']}==set(original) and len(r['rows'])==len(original),'ROW_RECONCILIATION')
        supported=selected=0
        statuses={'NOT_SELECTED','NO_REFERENCE_IN_TIK','NO_SIZE_LOCAL_DONOR','INSUFFICIENT_DONORS','ZERO_REFERENCE_VALID','DONOR_DOMINANCE','SUPPORTED'}
        for out in r['rows']:
            old=original[out['uuid']];need(out['status'] in statuses,'SUPPORT_STATUS')
            selected+=out['status']!='NOT_SELECTED';supported+=out['status']=='SUPPORTED'
            need(sum(out['parties'])==out['valid'] and min(out['parties'])>=0,'PARTY_SUM')
            need(out['n']==old.n and 0<=out['valid']<=out['issued']<=old.n,'ABC_DOMAIN')
            need(all(out['delta'][j]==out['parties'][j]-old.parties[j]==out['composition'][j]+out['intensity'][j]+out['interaction'][j] for j in range(10)),'DECOMPOSITION')
            if out['status']!='SUPPORTED':need(out['parties']==old.parties and out['issued']==old.issued and out['valid']==old.valid,'IDENTITY_EXTENSION')
            if not cell['mu_quarters']:need(out['issued']==old.issued and out['valid']==old.valid and out['invalid']==(common.UNKNOWN if old.invalid is None else old.invalid),'A_SLICE')
            if not cell['lambda_quarters']:need(all(out['parties'][j]*old.valid==old.parties[j]*out['valid'] for j in range(10)),'B_SLICE')
            if old.invalid is None:need(out['invalid']==common.UNKNOWN and out['remainder']==common.UNKNOWN,'UNKNOWN_INVALID')
            else:need(out['valid']+out['invalid']+out['remainder']==out['issued'] and out['invalid']==out['scale']*old.invalid,'KNOWN_INVALID')
        need(selected==r['selected_targets'] and supported==r['supported_targets'],'SUPPORT_RECONCILIATION')
        need(sum(r['aggregate']['parties'])==r['scenario_valid']==sum(x['valid'] for x in r['rows']),'AGG_VALID')
        for field in ('parties','delta','composition','intensity','interaction'):
            need(r['aggregate'][field]==tuple(sum(x[field][j] for x in r['rows']) for j in range(10)),'AGGREGATE_RECONCILIATION')
        native=tuple(sum(x['parties'][j] for x in r['rows'] if x['status']=='SUPPORTED') for j in range(10))
        need(r['native']['scenario_parties']==native and r['native']['scenario_valid']==sum(native),'NATIVE')
    else:
        need(r['spec_id']==cell['spec'],'D_SPEC')
        need(all(v==common.NOT_DEFINED for v in r['undefined'].values()) and set(r['undefined'])==set(d.UNDEFINED),'D_UNDEFINED')
        allowed={'APPLICABLE','NO_TARGET_SUPPORT','INSUFFICIENT_FIT_SUPPORT','DEGENERATE_REFERENCE','UNDEFINED_SCENARIO_TOTAL'}
        for s in r['strata'].values():
            need(s['status'] in allowed,'D_STATUS')
            need(tuple(sum(b['parties'][j] for b in s['bins']) for j in range(10))==s['source_parties'],'D_BINS')
            need(all(x==common.NOT_DEFINED for x in s['undefined'].values()),'D_UNDEFINED')
            if s['status']=='APPLICABLE':
                need(s['scenario_valid']==sum(s['scenario_parties'])==s['source_valid']-sum(s['signed_bin_residual']),'D_SIGNED')
                need(all(s['scenario_parties'][j]==s['source_parties'][j] for j in range(10) if j!=1),'D_NONFOCAL')
                for b,o in zip(s['bins'],s['candidate_bins']):need(sum(o['parties'])==o['valid'] and 0<=o['valid']<=b['n'],'D_ELECTORATE')
        ex=tuple(sum(s['scenario_parties'][j] if s['status']=='APPLICABLE' else s['source_parties'][j] for s in r['strata'].values()) for j in range(10))
        need(ex==r['extended']['scenario_parties'] and sum(ex)==r['extended']['scenario_valid'],'D_EXTENSION')
        need(all(ex[j]==st[j] for j in range(10) if j!=1),'D_NONFOCAL_FRAME')

def terminal(result):return 'COMPUTED' if result['status']=='APPLICABLE' else 'CONTRACT_UNSUPPORTED'
def reconcile_ledger(plan,ledger):
    verify_plan(plan);expected={c['id']:c for c in plan['cells']}
    need(len(ledger)==1620 and len({r['cell_id'] for r in ledger})==1620 and {r['cell_id'] for r in ledger}==set(expected),'TERMINAL_CELL_CLOSURE')
    need(all(r['terminal'] in plan['terminal_states'] for r in ledger),'NON_TERMINAL_CELL')
    need(all(r['terminal'] in ('COMPUTED','CONTRACT_UNSUPPORTED') and r['reconciliation']=='PASS' for r in ledger),'FAILURE_PREVENTS_COMMIT')
    return dict(status='PASS',cells=1620,ABC=1600,D=20,aliases='A:mu=0;B:lambda=0;no additional execution',source_variants=list(a.VARIANTS))
