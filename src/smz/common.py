"""Exact values, immutable synthetic inputs, and closed execution boundary."""
from dataclasses import dataclass, fields, is_dataclass
from fractions import Fraction as F
import hashlib
import json

VERSION = 'SMZ-2026-v1'
ORIGIN = 'SMZ_SYNTHETIC_QUALIFICATION_V1'
SOURCES = ('primary', 'S1', 'S2a', 'S2b')
PARTIES = ('rodina', 'er', 'kprf', 'pensioners', 'new_people', 'direct_democracy',
           'greens', 'communists_russia', 'ldpr', 'sr')
LEVELS = tuple(F(i, 4) for i in range(5))

class SMZError(ValueError):
    def __init__(self, status, reason):
        self.status, self.reason = status, reason
        super().__init__(f'{status}: {reason}')

def require(condition, reason, status='NUMERICAL_OR_IMPLEMENTATION_FAILURE'):
    if not condition:
        raise SMZError(status, reason)

@dataclass(frozen=True)
class Missing:
    status: str
    reason: str

UNKNOWN = Missing('UNKNOWN', 'source invalid unavailable; not inferred')
NOT_DEFINED = Missing('NOT_DEFINED', 'not defined by this model')

@dataclass(frozen=True)
class Row:
    uuid: str
    region: str
    tik: str
    n: int
    issued: int
    valid: int
    parties: tuple
    invalid: int | None = None

@dataclass(frozen=True)
class SyntheticFrame:
    fixture_id: str
    rows: tuple
    source_id: str = 'primary'
    origin: str = ORIGIN


def guard(frame, mode='synthetic_qualification'):
    require(mode == 'synthetic_qualification', 'future stages require a separate implementation/authorization transition', 'REAL_DATA_REVEAL_BLOCKED')
    require(type(frame) is SyntheticFrame and frame.origin == ORIGIN,
            'only explicit synthetic fixture objects accepted; no paths/loaders', 'REAL_DATA_REVEAL_BLOCKED')
    require(frame.fixture_id.startswith('syn:'), 'synthetic fixture namespace required', 'REAL_DATA_REVEAL_BLOCKED')
    require(frame.source_id in SOURCES, 'unknown source or non-executable S3 alias', 'SOURCE_FRAME_UNSUPPORTED')
    require(type(frame.rows) is tuple and bool(frame.rows), 'nonempty immutable frame required', 'SOURCE_FRAME_UNSUPPORTED')
    for r in frame.rows:
        require(type(r) is Row and all(type(x) is str and x.startswith('syn:') for x in (r.uuid, r.region, r.tik)),
                'synthetic identities required', 'REAL_DATA_REVEAL_BLOCKED')
    return frame


def validate(frame):
    guard(frame)
    keys, hierarchy = set(), {}
    for r in frame.rows:
        fail = lambda ok, msg: require(ok, msg, 'SOURCE_FRAME_UNSUPPORTED')
        fail(r.uuid not in keys, 'duplicate UUID'); keys.add(r.uuid)
        fail(hierarchy.setdefault(r.tik, r.region) == r.region, 'TIK belongs to multiple regions')
        fail(type(r.parties) is tuple and len(r.parties) == 10, 'exact ten-party vector required')
        fail(all(type(x) is int for x in (r.n, r.issued, r.valid, *r.parties)), 'counts must be integers, not bool/float')
        fail(r.n > 0 and 0 < r.valid <= r.issued <= r.n, 'n/I/V domain')
        fail(min(r.parties) >= 0 and sum(r.parties) == r.valid, 'party domain/sum')
        fail(r.invalid is None or (type(r.invalid) is int and r.invalid >= 0 and r.valid + r.invalid <= r.issued), 'known-invalid domain')
    return tuple(sorted(frame.rows, key=lambda x: x.uuid))


def level(x):
    require(type(x) in (int, F) and x in LEVELS, 'parameter outside frozen rational grid', 'UNKNOWN_PARAMETER')
    return F(x)


def wire(x):
    """Lossless, deterministic representation. No ambiguous nulls or float rounding."""
    if isinstance(x, F):
        return {'status': 'DEFINED', 'numerator': x.numerator, 'denominator': x.denominator}
    if isinstance(x, Missing):
        return {'status': x.status, 'reason': x.reason}
    if is_dataclass(x):
        return {f.name: wire(getattr(x, f.name)) for f in fields(x)}
    if isinstance(x, dict):
        return {str(k): wire(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
    if isinstance(x, (tuple, list)):
        return [wire(v) for v in x]
    if x is None:
        return {'status': 'UNKNOWN', 'reason': 'absent source value'}
    require(not isinstance(x, float), 'floating output prohibited')
    return x


def canonical(x):
    return json.dumps(wire(x), sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def fingerprint(x):
    return hashlib.sha256(canonical(x).encode()).hexdigest()


def shares(counts, denominator):
    return tuple(F(c) / denominator for c in counts) if denominator else tuple(
        Missing('NULL', 'UNDEFINED_ZERO_DENOMINATOR') for _ in counts)


def totals(rows):
    return tuple(sum((F(r.parties[j]) for r in rows), F(0)) for j in range(10))


def coverage(rows, denominator):
    return {'UIKs': len(rows), 'voters': sum(r.n for r in rows), 'source_valid': sum(r.valid for r in rows),
            'TIKs': len({r.tik for r in rows}), 'regions': len({r.region for r in rows}),
            'denominator': {'UIKs': len(denominator), 'voters': sum(r.n for r in denominator),
                            'source_valid': sum(r.valid for r in denominator)}}
