"""Future real authorization verifier. No authority/key/authorization is issued."""
import json
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from src.smz_real_adapter import adapter
from src.smz_real_adapter.plans import compile_plan
from . import codec
from .storage import need,file_sha
from .engine import ROOT,code_hashes
TRUST=ROOT/'outputs/smz_execution_authorization/trust_anchor.json'
def provider(envelope,run_id,plan):
    need(TRUST.is_file(),'REAL_EXECUTION_AUTHORIZATION_NOT_ISSUED')
    from src.smz_stage_registry import verify_history
    trust=json.loads(TRUST.read_text());need(trust['mode']=='closed_real_execution','REAL_TRUST_MODE')
    manifest_path=(ROOT/trust['readiness_manifest_path']).resolve()
    need(manifest_path.is_relative_to(ROOT/'outputs') and file_sha(manifest_path)==trust['readiness_manifest_sha256'],'READINESS_MANIFEST')
    manifest=json.loads(manifest_path.read_text())
    for name,h in manifest['files'].items():
        path=(ROOT/name).resolve();need(path.is_relative_to(ROOT) and file_sha(path)==h,'READINESS_HASH_CLOSURE')
    path=ROOT/trust['readiness_path'];need(path.resolve().is_relative_to(ROOT/'outputs'),'READINESS_PATH')
    raw=path.read_bytes();need(codec.sha(raw)==trust['readiness_sha256']==manifest['files'][trust['readiness_path']],'READINESS_LINK')
    readiness=json.loads(raw);history=verify_history(readiness['publication_id'])
    need(readiness['decision']=='PRE_RELEASE_REVIEW_PASS' and history['stage_outcomes'][readiness['publication_id']]=='PRE_RELEASE_REVIEW_PASS','FRESH_REGISTERED_READINESS_PASS_REQUIRED')
    try:Ed25519PublicKey.from_public_bytes(bytes.fromhex(trust['public_key'])).verify(bytes.fromhex(envelope['signature']),codec.encode(envelope['payload']))
    except Exception as e:raise ValueError('REAL_AUTHORIZATION_SIGNATURE') from e
    p=envelope['payload'];bindings=dict(contract_sha256=adapter.CONTRACT,adapter_manifest_sha256=plan['bindings']['adapter_manifest_sha256'],architecture_code_sha256=codec.digest(code_hashes()),execution_plan_sha256=codec.digest(plan))
    need(all(p[k]==v and readiness[k]==v for k,v in bindings.items()),'REAL_AUTHORIZATION_BINDINGS')
    need(p['run_id']==run_id and p['mode']=='closed_real_execution' and p['explicit_user_authorization'] is True and p['readiness_sha256']==codec.sha(raw),'EXPLICIT_AUTHORIZATION_RUN')
    expected='78385131591910684ebfa3115f27159d4e78be76b5690fdcebc7c72500a84aa3'
    profile=adapter.PROFILE.read_bytes();need(codec.sha(profile)==expected,'FROZEN_SOURCE_PROFILE')
    def metadata(name):
        path=(ROOT/name).resolve();need(path.is_relative_to(ROOT/'outputs'),'SOURCE_METADATA_PATH');return path.read_bytes()
    def load(variant):
        selected=compile_plan(profile,variant,metadata,expected_profile_sha256=expected)
        def opener(name,h):
            path=(ROOT/name).resolve();need(path.is_relative_to(ROOT/'data'),'FROZEN_SOURCE_PATH');return path.open('rb')
        return adapter._decode(selected,variant,opener,run_id=run_id,created_at=p['created_at'],bundle_sha=expected,origin='SMZ_CLOSED_REAL_ADAPTER')
    return load
