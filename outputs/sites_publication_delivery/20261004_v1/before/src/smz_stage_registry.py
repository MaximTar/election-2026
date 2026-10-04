"""Explicit versioned SMZ publications, outcomes, and task qualification requirements.

No data loader or scenario call. Unknown nodes fail closed. New publications require a
new declared registry version (exact prefix/predecessor), hashes and deterministic builder.
"""
import hashlib,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'outputs/sites_publication_data/20261004_v1'
REGISTRY=PACKAGE/'stage_registry.json'
REGISTRY_SHA='46403732537911626dd4d864984d0d5c924dbb420df8c39cee9acf28a44fefa0'
CONTRACT_SHA='34f19240c282fa27268891c9d04da7372ce5ba20f9c3f2ff3f3ef7d9d75286e5'
def need(ok,reason):
    if not ok:raise RuntimeError('SMZ_STAGE_REGISTRY: '+reason)
_HASH_CACHE={}
def sha(p):
    # Process-local verification reuse only; any file metadata change invalidates it.
    # No persistent hash cache or mtime-only acceptance across checker invocations.
    p=Path(p);st=p.stat();key=(str(p.absolute()),st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)
    if key in _HASH_CACHE:return _HASH_CACHE[key]
    with p.open('rb') as f:value=hashlib.file_digest(f,'sha256').hexdigest()
    after=p.stat();need((st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'file changed while hashing')
    _HASH_CACHE[key]=value;return value
def read(p):return json.loads(Path(p).read_text())
def load_registry():
    need(sha(REGISTRY)==REGISTRY_SHA,'registry hash')
    registry=read(REGISTRY)
    current=registry;seen={str(REGISTRY)}
    while current.get('previous_registry'):
        old=ROOT/current['previous_registry'];need(str(old) not in seen,'registry cycle');seen.add(str(old))
        need(sha(old)==current['previous_registry_sha256'],'registry predecessor hash')
        previous=read(old)
        need(len(current['stages'])>len(previous['stages']) and current['stages'][:len(previous['stages'])]==previous['stages'],'registry prefix rewritten')
        current=previous
    return registry

def resolve_artifact(path,expected,registry=None):
    path=Path(path)
    if path.exists() and sha(path)==expected:return path
    r=registry or load_registry()
    try:relative=str(path.relative_to(ROOT))
    except ValueError:return path
    # Only explicitly archived engineering checker versions. Scientific paths never resolve.
    candidates=[x for x in r['engineering_resolutions'] if x['path']==relative and x['sha256']==expected]
    need(len(candidates)<=1,'ambiguous historical code resolution')
    if candidates:
        resolved=ROOT/candidates[0]['archive'];need(sha(resolved)==expected,'archived checker changed');return resolved
    return path

def artifact_hash(path,expected,registry=None):return sha(resolve_artifact(path,expected,registry))
def verify_manifest(path,expected,registry=None,cache=None):
    r=registry or load_registry();need(sha(path)==expected,'manifest hash '+str(path))
    manifest=read(path)
    for relative,h in manifest['files'].items():
        key=(relative,h)
        if cache is not None and key in cache:continue
        need(artifact_hash(ROOT/relative,h,r)==h,'artifact hash '+relative)
        if cache is not None:cache.add(key)
    return manifest

def get_value(obj,keys):
    for key in keys:obj=obj[key]
    return obj

def verify_records(registry,records,live_state,live_handoff):
    declarations=registry['stages']
    need([r['id'] for r in records]==[d['id'] for d in declarations],'missing/reordered/unregistered publication')
    need(len({d['id'] for d in declarations})==len(declarations),'duplicate registration')
    previous=None
    for d,r in zip(declarations,records):
        need(r['verified'] is True,'unverified publication')
        need(r['contract_sha256']==CONTRACT_SHA,'contract mismatch')
        need(r['after_state']==r['expected_state'],'builder mismatch '+r['id'])
        need(r['after_state']['current_stage']==d['id'],'publication identity mismatch')
        need(r['outcome']==d['outcome'],'historical outcome changed')
        need(d['previous_id']==(previous['id'] if previous else None),'transition declaration')
        need(r['after_handoff'].startswith(r['before_handoff']),'handoff not append-only')
        if previous:
            need(r['before_state']==previous['after_state'],'skipped/replaced state predecessor')
            need(r['before_handoff']==previous['after_handoff'],'skipped/replaced handoff predecessor')
        previous=r
    need(previous is not None and live_state==previous['after_state'],'live state not latest registered publication')
    need(live_handoff==previous['after_handoff'],'live handoff not latest registered publication')
    return {'status':'PASS','publications':len(records),'stage_outcomes':{r['id']:r['outcome'] for r in records}}

def prerequisite(registry,records,task):
    need(task in registry['task_requirements'],'unknown prerequisite request')
    observed={r['id']:r['outcome'] for r in records}
    for stage,allowed in registry['task_requirements'][task].items():
        need(stage in observed,'missing prerequisite '+stage)
        need(observed[stage] in allowed,'nonqualifying outcome '+stage)
    return {'task':task,'status':'PASS','required_outcomes':registry['task_requirements'][task]}

def load_records(registry):
    records=[];cache=set()
    for d in registry['stages']:
        verify_manifest(ROOT/d['manifest'],d['manifest_sha256'],registry,cache)
        for path,h in d['evidence_hashes'].items():need(artifact_hash(ROOT/path,h,registry)==h,'publication/builder evidence '+path)
        for check in registry.get('stage_assertions',{}).get(d['id'],[]):
            need(sha(ROOT/check['path'])==check['sha256'],'outcome evidence hash')
            need(get_value(read(ROOT/check['path']),check['keys'])==check['expected'],'stage qualification evidence '+d['id'])
        before=read(ROOT/d['before_state']);after=read(ROOT/d['after_state'])
        builder=d['builder'];p=ROOT/builder['path']
        need(sha(p)==builder['sha256'],'builder hash')
        spec=importlib.util.spec_from_file_location('_registered_'+d['id'],p);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        # Preserve original builder filesystem context when executing its archived source.
        module.ROOT=ROOT;module.PACKAGE=ROOT/d['package']
        if hasattr(module,'REPAIR'):module.REPAIR=ROOT/d['package']
        args=[before]
        for arg in builder.get('arguments',[]):args.append(read(ROOT/arg['json']) if 'json' in arg else arg['literal'])
        expected=getattr(module,builder['function'])(*args)
        records.append(dict(id=d['id'],verified=True,contract_sha256=d['contract_sha256'],before_state=before,after_state=after,expected_state=expected,
            before_handoff=(ROOT/d['before_handoff']).read_text(),after_handoff=(ROOT/d['after_handoff']).read_text(),outcome=get_value(after,d['outcome_path'])))
    return records

def verify_history(required=None):
    registry=load_registry();records=load_records(registry)
    result=verify_records(registry,records,read(ROOT/'outputs/metadata/research_state.json'),(ROOT/'docs/RESEARCH_HANDOFF.md').read_text())
    if required:
        task=registry.get('aliases',{}).get(required,required)
        if task in registry['task_requirements']:result['prerequisite']=prerequisite(registry,records,task)
        else:need(task in {r['id'] for r in records},'required publication absent')
    if (PACKAGE/'code_freeze.json').exists():
        for path,h in read(PACKAGE/'code_freeze.json')['files'].items():need(sha(ROOT/path)==h,'current governance code changed '+path)
    return result

def check_stage(identifier):
    result=verify_history(identifier)
    result.update(stage=identifier,outcome=result['stage_outcomes'][identifier],scenario_execution_authorized=False,mock_scenario_executions=0,real_party_rows_processed=0)
    return result
