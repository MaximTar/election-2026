"""Metadata/hash preflight only; never reads party rows or base result packets."""
import csv
import hashlib
import json
from pathlib import Path
from src.smz_external_real.preflight import verify_environment

ROOT=Path(__file__).resolve().parents[2]
FREEZE=ROOT/'outputs/smz_v2_external_c_lite_plus_a_freeze/20261003_v1'
QUAL=ROOT/'outputs/smz_v2_external_c_lite_plus_a_qualification/20261003_v1'
AUTH=ROOT/'outputs/smz_v2_external_c_lite_plus_a_pre_real_authorization/20261003_v1'
RUN=ROOT/'outputs/smz_v2_external_c_lite_plus_a_real_execution/20261003_run01'
BASE=ROOT/'outputs/smz_v2_external_real_execution/20261002_run02'


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def read(path):return json.loads(path.read_text())


def check_frozen():
    from .loader import transform
    for name in ['istories','cedar']:
        assert transform(name)[1]['all_function_AST_identical']
    for relative,h in read(FREEZE/'bindings.json')['files'].items():
        assert sha(ROOT/relative)==h,relative
    for relative,h in read(FREEZE/'manifest.json')['files'].items():
        assert sha(ROOT/relative)==h,relative
    states=list(csv.DictReader((FREEZE/'state_index.csv').open()))
    assert len(states)==len({s['state_id'] for s in states})==83
    assert sum(s['family']=='ISTORIES' for s in states)==12
    assert sum(s['family']=='CEDAR' for s in states)==71
    base_index=ROOT/'outputs/smz_v2_external_freeze/20261002_v2/state_index.csv'
    old={s['state_id'] for s in csv.DictReader(base_index.open())}
    assert not old.intersection(s['state_id'] for s in states)
    from .arithmetic import controls
    for s in states:controls(s)
    assert read(BASE/'commit_record.json')['state']=='COMMITTED_NOT_REVEALED'
    assert read(BASE/'immutable_manifest.json')['reveal_authorization'] is False
    assert sha(BASE/'immutable_manifest.json')=='c56d4c8cee7635e88ed050aeb011288163ca3ed862ae6404a11064ad8b2333c6'
    assert sha(BASE/'commit_record.json')=='9e510fed050b77043a988a0ce059ef9b5488408a46ca152f86d18ed0ae741a5d'
    return states


def check_authorization(fresh=True):
    states=check_frozen()
    a=read(AUTH/'authorization.json')
    assert a['state']=='UNCONSUMED' and a['reveal']=='NOT_AUTHORIZED'
    assert a['run_id']=='external-c-lite-plus-a-20261003-run01'
    assert a['REAL_RUN_AUTHORIZATION'] is True
    assert a['expected_states']==83 and a['new_optimizer_fits']==0
    for rel,h in a['bindings'].items():assert sha(ROOT/rel)==h,rel
    for rel,h in read(AUTH/'manifest.json')['files'].items():assert sha(ROOT/rel)==h,rel
    q=read(QUAL/'qualification_results.json')
    assert q['status']=='PASS' and q['count']==q['passed']==14
    assert q['no_real_data']['real_party_rows']==q['no_real_data']['optimizer_fits']==0
    from src.smz_stage_registry import load_registry
    registry=load_registry()
    assert registry['stages'][-1]['id']==a['issuer_stage']
    assert sha(ROOT/registry['previous_registry'])==registry['previous_registry_sha256']
    assert read(ROOT/'outputs/metadata/research_state.json')['current_stage']==a['issuer_stage']
    assert sha(ROOT/'src/smz_stage_registry.py')==a['governance_pointer_sha256']
    assert read(AUTH/'resource_ledger.json')['pre_authorization_projection_checkpoint']=='PASS'
    environment=verify_environment()
    if fresh:assert not RUN.exists(),'FRESH_EXCLUSIVE_RUN_REQUIRED'
    return a,states,environment
