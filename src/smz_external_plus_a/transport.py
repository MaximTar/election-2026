"""Supplement-only typed transport with a verified one-use consumption boundary."""
from dataclasses import dataclass
from pathlib import Path
import json
from src.smz_external_clite.common import IntegrityError, ResourceStop, canonical

ACTIVE = None
COUNTERS = {'real_party_rows':0,'real_model_fits':0,'model_calls':{}}


def require_active():
    if ACTIVE is None:
        raise IntegrityError('SUPPLEMENT_COMMITMENT_REQUIRED')
    from .preflight import sha, AUTH, RUN
    a = json.loads((AUTH/'authorization.json').read_text())
    marker = json.loads((RUN/'authorization_consumed.json').read_text())
    if marker['authorization_sha256'] != sha(AUTH/'authorization.json') or marker['run_id'] != a['run_id']:
        raise IntegrityError('AUTHORIZATION_CONSUMPTION_MISMATCH')
    if sha(RUN/'execution_commitment.json') != ACTIVE['commitment_sha256']:
        raise IntegrityError('COMMITMENT_CHANGED')
    return ACTIVE


def activate(context):
    global ACTIVE
    if ACTIVE is not None:
        raise IntegrityError('ONE_TRANSACTION_ONLY')
    ACTIVE = context
    require_active()


@dataclass(frozen=True)
class RealRow:
    uuid:str;region:str;n:int;I:int;V:int;L:int;invalid:int|None;parties:tuple
    source_variant:str;source_id:str;source_sha256:str;selector_commitment:str;tik_uuid:str
    family_eligibility:tuple


@dataclass(frozen=True)
class RealFrame:
    rows:tuple
    source_variant:str='primary'
    origin:str='EXTERNAL_C_LITE_PLUS_A_AUTHORIZED_REAL_SOURCE'
    def __post_init__(self):
        require_active()
        if self.source_variant != 'primary' or self.origin != 'EXTERNAL_C_LITE_PLUS_A_AUTHORIZED_REAL_SOURCE':
            raise IntegrityError('SUPPLEMENT_PRIMARY_ONLY')


SyntheticFrame = RealFrame


def validate(frame):
    require_active()
    if not isinstance(frame, RealFrame) or len({r.uuid for r in frame.rows}) != len(frame.rows):
        raise IntegrityError('REAL_FRAME_IDENTITY')
    for r in frame.rows:
        if r.source_variant != 'primary':
            raise IntegrityError('SOURCE_CROSS')
        if any(type(x) is not int or x<0 for x in (r.n,r.I,r.V,r.L,*r.parties)):
            raise IntegrityError('COUNT_DOMAIN')
        if not 0<r.V<=r.I<=r.n or len(r.parties)!=10 or sum(r.parties)!=r.V or r.parties[1]!=r.L:
            raise IntegrityError('PARTY_VECTOR_OR_DOMAIN')
        if r.invalid is not None and (type(r.invalid) is not int or r.invalid<0 or r.V+r.invalid>r.I):
            raise IntegrityError('INVALID_DOMAIN')


def filtered(frame, excluded_region=None):
    if excluded_region is not None:
        raise IntegrityError('LOO_NOT_AUTHORIZED')
    validate(frame)
    return RealFrame(tuple(sorted(frame.rows,key=lambda r:r.uuid)))


def trace_call(family,n):
    require_active()
    COUNTERS['model_calls'][family] = COUNTERS['model_calls'].get(family,0)+1


def trace_fit(family):
    raise ResourceStop('OPTIMIZER_FIT_FORBIDDEN_IN_VARIANT_A')
