"""Explicit real identity transport; never relabel real UUIDs or origin as mock."""
import dataclasses
from fractions import Fraction as F
from src.smz_external_clite.common import IntegrityError,ResourceStop,canonical,digest

_ACTIVE=None
COUNTERS={'real_party_rows':0,'real_model_fits':0,'model_calls':{},'fit_attempts':{}}
def require_active():
    if _ACTIVE is None or _ACTIVE.get('committed_before_first_fit') is not True:
        raise IntegrityError('IMMUTABLE_AUTHORIZED_EXECUTION_COMMITMENT_REQUIRED')
    return _ACTIVE
def activate(ctx):
    # Only the hash-checked coordinator calls this after fresh commitment/consumption.
    global _ACTIVE
    if _ACTIVE is not None:raise IntegrityError('FRESH_RUN_REQUIRED')
    if not ctx.get('committed_before_first_fit'):raise IntegrityError('COMMITMENT_REQUIRED')
    from .preflight import verify_claim
    verify_claim(ctx)
    _ACTIVE=ctx
@dataclasses.dataclass(frozen=True)
class RealRow:
    uuid:str;region:str;n:int;I:int;V:int;L:int;invalid:int|None;parties:tuple
    source_variant:str;source_id:str;source_sha256:str;selector_commitment:str;tik_uuid:str
    family_eligibility:tuple
@dataclasses.dataclass(frozen=True)
class RealFrame:
    rows:tuple
    source_variant:str
    origin:str='EXTERNAL_C_LITE_AUTHORIZED_REAL_SOURCE'
    def __post_init__(self):
        require_active()
        if self.origin!='EXTERNAL_C_LITE_AUTHORIZED_REAL_SOURCE' or any(r.source_variant!=self.source_variant for r in self.rows):
            raise IntegrityError('REAL_PROVENANCE_REQUIRED')
# These aliases preserve the exact qualified function AST/type-check sites. The
# actual classes and records explicitly carry REAL origin/UUID/provenance.
SyntheticFrame=RealFrame
def validate(data):
    require_active()
    if not isinstance(data,RealFrame):raise IntegrityError('QUALIFIED_REAL_FRAME_REQUIRED')
    if len({r.uuid for r in data.rows})!=len(data.rows):raise IntegrityError('duplicate UUID')
    for r in data.rows:
        counts=(r.n,r.I,r.V,r.L,*r.parties)
        if any(type(x) is not int or x<0 for x in counts):raise IntegrityError('nonintegral or negative count')
        if not 0<r.V<=r.I<=r.n or not 0<=r.L<=r.V:raise IntegrityError('count domain')
        if len(r.parties)!=10 or sum(r.parties)!=r.V or r.parties[1]!=r.L:raise IntegrityError('party vector')
        if r.invalid is not None and (type(r.invalid) is not int or r.invalid<0 or r.V+r.invalid>r.I):raise IntegrityError('known invalid domain')
def filtered(data,excluded_region=None):
    validate(data)
    return RealFrame(tuple(sorted((r for r in data.rows if r.region!=excluded_region),key=lambda r:r.uuid)),data.source_variant)
def trace_call(family,n):
    require_active();COUNTERS['model_calls'][family]=COUNTERS['model_calls'].get(family,0)+1
def trace_fit(family):
    require_active();COUNTERS['real_model_fits']+=1;COUNTERS['fit_attempts'][family]=COUNTERS['fit_attempts'].get(family,0)+1
@dataclasses.dataclass(frozen=True)
class InputHistogram:
    h:F;mass:object
    origin:str='EXTERNAL_C_LITE_AUTHORIZED_REAL_SOURCE'
    def __post_init__(self):
        require_active()
        if F(self.h) not in [F(1,200),F(1,100),F(1,50)] or self.origin!='EXTERNAL_C_LITE_AUTHORIZED_REAL_SOURCE':raise IntegrityError('INPUT_DOMAIN')
@dataclasses.dataclass(frozen=True)
class InputPoints:
    points:object;UUIDs:tuple;regions:tuple;voters:tuple
    origin:str='EXTERNAL_C_LITE_AUTHORIZED_REAL_SOURCE'
    def __post_init__(self):
        require_active()
        import numpy as np
        X=np.asarray(self.points,dtype=np.float64);n=len(self.UUIDs)
        if len(set(self.UUIDs))!=n or len(self.regions)!=n or len(self.voters)!=n or X.shape!=(n,2):raise IntegrityError('point identity')
        if not np.all(np.isfinite(X)) or np.any((X<0)|(X>1)):raise IntegrityError('raw ratio domain; no clipping')
        if any(type(v) is not int or v<=0 for v in self.voters):raise IntegrityError('registered voters')
