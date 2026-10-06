import dataclasses
import hashlib
import json
from fractions import Fraction

COUNTERS = {'real_party_rows': 0, 'real_model_fits': 0, 'model_calls': {}, 'synthetic_fit_attempts': {}}


class IntegrityError(ValueError):
    pass


class ResourceStop(RuntimeError):
    pass


@dataclasses.dataclass(frozen=True)
class MockRow:
    uuid: str
    region: str
    n: int
    I: int
    V: int
    L: int
    invalid: int | None
    parties: tuple


@dataclasses.dataclass(frozen=True)
class SyntheticFrame:
    rows: tuple
    origin: str = 'SYNTHETIC_QUALIFICATION'

    def __post_init__(self):
        if self.origin != 'SYNTHETIC_QUALIFICATION' or any(
                not r.uuid.startswith('mock:') or not r.region.startswith('mock:') for r in self.rows):
            raise IntegrityError('REAL_INPUT_FORBIDDEN')


def frame(raw, name='fixture'):
    rows = []
    for j, r in enumerate(raw):
        L, V = r.get('L', 0), r['V']
        # Fixed ten-party schema: ER slot 1. These counts are mock literals only.
        parties = r.get('parties', (V - L, L, 0, 0, 0, 0, 0, 0, 0, 0))
        rows.append(MockRow(r.get('uuid', f'mock:{name}:{j:05d}'), r.get('region', 'mock:region:A'),
                           r['n'], r['I'], V, L, r.get('invalid'), tuple(parties)))
    return SyntheticFrame(tuple(sorted(rows, key=lambda row: row.uuid)))


def validate(data):
    if not isinstance(data, SyntheticFrame) or data.origin != 'SYNTHETIC_QUALIFICATION':
        raise IntegrityError('REAL_INPUT_FORBIDDEN')
    if len({r.uuid for r in data.rows}) != len(data.rows):
        raise IntegrityError('duplicate UUID')
    for r in data.rows:
        counts = (r.n, r.I, r.V, r.L, *r.parties)
        if any(type(x) is not int or x < 0 for x in counts):
            raise IntegrityError('nonintegral or negative count')
        if not 0 < r.V <= r.I <= r.n or not 0 <= r.L <= r.V:
            raise IntegrityError('count domain')
        if len(r.parties) != 10 or sum(r.parties) != r.V or r.parties[1] != r.L:
            raise IntegrityError('party vector')
        if r.invalid is not None and (type(r.invalid) is not int or r.invalid < 0 or r.V + r.invalid > r.I):
            raise IntegrityError('known invalid domain')


def trace_call(family, n):
    COUNTERS['model_calls'][family] = COUNTERS['model_calls'].get(family, 0) + 1


def trace_fit(family):
    COUNTERS['synthetic_fit_attempts'][family] = COUNTERS['synthetic_fit_attempts'].get(family, 0) + 1


def filtered(data, excluded_region=None):
    validate(data)
    return SyntheticFrame(tuple(sorted((r for r in data.rows if r.region != excluded_region),
                                      key=lambda row: row.uuid)))


def encoded(value):
    if isinstance(value, Fraction):
        return {'exact': str(value)}
    if isinstance(value, float):
        import math
        if not math.isfinite(value):
            raise ValueError('nonfinite serialization')
        return {'float_hex': value.hex(), 'decimal17': format(value, '.17g')}
    if isinstance(value, dict):
        return {str(k): encoded(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [encoded(v) for v in value]
    return value


def canonical(value):
    return json.dumps(encoded(value), ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()
