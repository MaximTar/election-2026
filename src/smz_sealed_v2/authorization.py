"""Signed future authorization and process-private execution capabilities.

No real authority key, readiness PASS, or authorization is issued by this module.
Mock trust cannot satisfy the real trust anchor.
"""
import json,secrets
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from src.smz_real_adapter import adapter as a
from src.smz_real_adapter.plans import compile_plan
from .core import ROOT,need,enc,sha,bindings,SealError
REAL_TRUST=ROOT/'outputs/smz_execution_authorization/trust_anchor.json'
_LIVE={}
class _Capability:
    __slots__=('_nonce',)
    def __init__(self):raise SealError('CAPABILITY_CONSTRUCTOR_PRIVATE')
def _activate(run_id,mode,frame_digests,authorization_sha):
    need(mode in ('mock_sealed_execution','closed_real_execution'),'MODE')
    cap=object.__new__(_Capability);cap._nonce=secrets.token_hex(32)
    _LIVE[cap._nonce]=(cap,run_id,mode,dict(frame_digests),authorization_sha);return cap
def verify_capability(cap,frames=None):
    need(type(cap) is _Capability and getattr(cap,'_nonce',None) in _LIVE and _LIVE[cap._nonce][0] is cap,'COORDINATOR_CAPABILITY_REQUIRED')
    entry=_LIVE[cap._nonce]
    if frames is not None:
        need(set(frames)==set(a.VARIANTS),'FRAME_VARIANTS')
        for v,f in frames.items():
            p=a.verify_frame(f);need(p['input_frame_sha256']==entry[3][v],'CAPABILITY_FRAME_BINDING')
            need(p['contract_sha256']==a.CONTRACT and p['implementation_manifest_sha256']==a.IMPLEMENTATION,'FRAME_PROVENANCE')
            expected='SMZ_MOCK_REAL_ADAPTER_QUALIFICATION' if entry[2]=='mock_sealed_execution' else 'SMZ_CLOSED_REAL_ADAPTER'
            need(f.origin==expected,'ORIGIN_MODE_MISMATCH')
    return entry
def _revoke(cap):_LIVE.pop(cap._nonce,None)

def verify_signed_authorization(envelope,trust,plan,readiness_bytes):
    """Pure verifier; used with isolated mock trust in qualification.

    The public real bridge reads the fixed operator-installed trust anchor itself.
    Callers cannot pass their own trust root to activate real I/O.
    """
    try:Ed25519PublicKey.from_public_bytes(bytes.fromhex(trust['public_key'])).verify(bytes.fromhex(envelope['signature']),enc(envelope['payload']))
    except Exception:raise SealError('AUTHORIZATION_SIGNATURE')
    p=envelope['payload'];b=bindings();r=json.loads(readiness_bytes)
    need(p['mode']==trust['mode'],'AUTHORIZATION_MODE')
    need(p['readiness_sha256']==sha(readiness_bytes)==trust['readiness_sha256'],'READINESS_HASH')
    need(r['decision']=='PRE_RELEASE_REVIEW_PASS' and r['contract_sha256']==a.CONTRACT,'READINESS_NOT_PASS')
    need(p['contract_sha256']==a.CONTRACT and p['execution_plan_sha256']==sha(enc(plan)),'AUTHORIZATION_BINDING')
    need(p['coordinator_code_sha256']==b['coordinator_code_sha256'] and p['adapter_manifest_sha256']==b['adapter_manifest_sha256'],'AUTHORIZATION_CODE')
    need(r['coordinator_code_sha256']==b['coordinator_code_sha256'] and r['adapter_manifest_sha256']==b['adapter_manifest_sha256'],'READINESS_CODE')
    need(p['explicit_user_authorization'] is True and p['run_id'] and p['authorization_id'],'EXPLICIT_AUTHORIZATION_REQUIRED')
    return p

def _real_frames(envelope,plan,run_id):
    # No actual source read is reachable without an externally installed authority,
    # immutable PASS readiness, and a signature over this exact run/plan/code.
    need(REAL_TRUST.is_file(),'REAL_EXECUTION_AUTHORIZATION_NOT_ISSUED')
    from src.smz_stage_registry import verify_history
    verify_history('sealed_coordinator_attempt02_qualified')
    trust=json.loads(REAL_TRUST.read_text());need(trust['mode']=='closed_real_execution','REAL_TRUST_MODE')
    manifest_path=(ROOT/trust['readiness_manifest_path']).resolve()
    need(manifest_path.is_relative_to(ROOT/'outputs'),'READINESS_MANIFEST_PATH')
    need(a.file_sha(manifest_path)==trust['readiness_manifest_sha256'],'READINESS_MANIFEST_HASH')
    manifest=json.loads(manifest_path.read_text())
    for relative,h in manifest['files'].items():
        p=(ROOT/relative).resolve();need(p.is_relative_to(ROOT),'READINESS_ARTIFACT_PATH');need(a.file_sha(p)==h,'READINESS_ARTIFACT_HASH')
    need(manifest['files'][trust['readiness_path']]==trust['readiness_sha256'],'READINESS_MANIFEST_LINK')
    readiness_path=ROOT/trust['readiness_path']
    need(readiness_path.resolve().is_relative_to(ROOT/'outputs'),'READINESS_PATH')
    readiness_bytes=readiness_path.read_bytes()
    readiness=json.loads(readiness_bytes)
    history=verify_history(readiness['publication_id'])
    need(history['stage_outcomes'].get(readiness['publication_id'])=='PRE_RELEASE_REVIEW_PASS','REGISTERED_READINESS_NOT_PASS')
    p=verify_signed_authorization(envelope,trust,plan,readiness_bytes)
    need(p['run_id']==run_id and p['mode']=='closed_real_execution','AUTHORIZATION_RUN')
    profile=a.PROFILE.read_bytes();expected='78385131591910684ebfa3115f27159d4e78be76b5690fdcebc7c72500a84aa3'
    need(sha(profile)==expected,'FROZEN_SOURCE_PROFILE')
    def metadata(path):
        actual=(ROOT/path).resolve();need(actual.is_relative_to(ROOT/'outputs'),'METADATA_PATH');return actual.read_bytes()
    frames={}
    for variant in a.VARIANTS:
        selected=compile_plan(profile,variant,metadata,expected_profile_sha256=expected)
        def provider(path,h):
            actual=(ROOT/path).resolve();need(actual.is_relative_to(ROOT/'data'),'SOURCE_PATH');return actual.open('rb')
        # Only the qualified adapter parses/count-validates; coordinator never parses rows.
        frames[variant]=a._decode(selected,variant,provider,run_id=run_id,created_at=p['created_at'],bundle_sha=expected,origin='SMZ_CLOSED_REAL_ADAPTER')
    return frames,p
