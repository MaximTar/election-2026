"""Hash/environment/deadline gate. Does not load party rows or execute kernels."""
import datetime,hashlib,importlib.metadata,json,os,platform
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PACKAGE=ROOT/'outputs/smz_v2_external_pre_real_authorization/20261002_v1'
RUN=ROOT/'outputs/smz_v2_external_real_execution/20261002_run01'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text())
def need(ok,reason):
    if not ok:raise RuntimeError('EXTERNAL_PRE_REAL: '+reason)
def verify_environment():
    expected=read(ROOT/'outputs/smz_v2_external_qualification/20261002_v1/environment.json')
    actual={'python':platform.python_version(),'versions':{k:importlib.metadata.version(k) for k in expected['versions']},
            'distribution_record_hashes':{k:sha(Path(importlib.metadata.distribution(k)._path)/'RECORD') for k in expected['versions']}}
    need(actual['python']==expected['python'] and actual['versions']==expected['versions'],'EXACT_ENVIRONMENT_REQUIRED')
    need(actual['distribution_record_hashes']==expected['distribution_record_hashes'],'ENVIRONMENT_RECORD_CHANGED')
    need(all(os.environ.get(k)=='1' for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']),'SINGLE_THREAD_ENVIRONMENT_REQUIRED')
    return actual
def binding_check():
    b=read(PACKAGE/'execution_code_bindings.json')
    for p,h in b['files'].items():need(sha(ROOT/p)==h,'CODE_OR_BINDING_CHANGED '+p)
    implementation=read(PACKAGE/'implementation_bindings.json')
    for key in ['synthetic_qualified_files','source_selector_snapshot_files','qualified_source_decoder_files','successor_contracts']:
        for p,h in implementation[key].items():need(sha(ROOT/p)==h,'FROZEN_INPUT_CHANGED '+p)
    for key in ['state_index','source_profile','eligibility_registry','eligibility_metadata','region_index','environment']:
        z=implementation[key];need(sha(ROOT/z['path'])==z['sha256'],'FROZEN_BINDING_CHANGED '+key)
    return {'status':'PASS','files':len(b['files'])}
def check_execution():
    auth=read(PACKAGE/'authorization.json')
    need(auth['REAL_RUN_AUTHORIZATION'] is True and auth['REAL_2D_ACTIVATION'] is True,'EXECUTION_NOT_AUTHORIZED')
    from src.smz_stage_registry import load_registry,verify_manifest
    registry=load_registry();stage=registry['stages'][-1]
    need(stage['id']==auth['issuer_stage'],'GOVERNANCE_TIP_CHANGED')
    need(stage['evidence_hashes'].get(str((PACKAGE/'authorization.json').relative_to(ROOT)))==sha(PACKAGE/'authorization.json'),'AUTHORIZATION_HASH_CHANGED')
    need(read(ROOT/'outputs/metadata/research_state.json')['current_stage']==auth['issuer_stage'],'LIVE_GOVERNANCE_CHANGED')
    verify_manifest(ROOT/stage['manifest'],stage['manifest_sha256'],registry)
    for field,name in [('execution_commitment_template_sha256','execution_commitment_template.json'),
                       ('execution_code_bindings_sha256','execution_code_bindings.json'),
                       ('real_adapter_contract_sha256','real_adapter_contract.json'),
                       ('implementation_bindings_sha256','implementation_bindings.json'),
                       ('failure_policy_sha256','failure_policy.json')]:
        need(sha(PACKAGE/name)==auth[field],'AUTHORIZATION_BINDING_CHANGED '+name)
    binding_check();environment=verify_environment()
    deadline=datetime.datetime.fromisoformat(auth['hard_deadline_UTC'])
    now=datetime.datetime.now(datetime.timezone.utc)
    need((deadline-now).total_seconds()/3600>auth['estimated_real_phase_hours']+auth['reserve_hours'],
         'INSUFFICIENT_EXECUTION_TIME_WITH_RESERVE')
    need(not RUN.exists(),'FRESH_RUN_REQUIRED')
    need(not (PACKAGE/'real_results.json').exists(),'RESULT_IN_AUTHORIZATION_PACKAGE')
    return auth,environment
def verify_claim(ctx):
    need(ctx.get('run_path')==str(RUN) and ctx['authorization_sha256']==sha(PACKAGE/'authorization.json'),'EXECUTION_CLAIM_BINDING')
    expected=read(PACKAGE/'execution_commitment_template.json')
    need(read(RUN/'execution_commitment.json')==expected,'COMMITMENT_MISMATCH')
    need(sha(RUN/'execution_commitment.json')==ctx['commitment_sha256'],'COMMITMENT_MUTATED')
    claim=read(RUN/'authorization_consumed.json')
    need(claim['authorization_sha256']==ctx['authorization_sha256'] and claim['run_id']==ctx['run_id'],'AUTHORIZATION_CONSUMPTION_MISMATCH')
