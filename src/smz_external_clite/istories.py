from fractions import Fraction as F
from .common import IntegrityError, SyntheticFrame, filtered, trace_call, validate


def bin_index(issued, voters):
    if voters <= 0 or not 0 <= issued <= voters:
        raise IntegrityError('turnout domain')
    return min(99, 100 * issued // voters)


def denominator_status(value):
    return 'DEFINED' if value > 0 else 'NOT_DEFINED_SCENARIO_DENOMINATOR'


def run(data, window=(F(1, 5), F(3, 10)), estimator='ROS', excluded_region=None):
    trace_call('ISTORIES', len(data.rows))
    try:
        validate(data)
        view = filtered(data, excluded_region)
    except IntegrityError:
        return {'status': 'FAIL_SOURCE_INTEGRITY_ABORT_VARIANT'}
    if not view.rows:
        return {'status': 'NOT_DEFINED_EMPTY_ELIGIBLE'}
    lo, hi = map(F, window)
    reference = [r for r in view.rows if lo <= F(r.I, r.n) < hi]
    if not reference:
        return {'status': 'NOT_DEFINED_EMPTY_REFERENCE'}
    bins = {j: [0, 0] for j in range(100)}
    for r in reference:
        b = bin_index(r.I, r.n)
        bins[b][0] += r.L
        bins[b][1] += r.V - r.L
    if estimator == 'ROS':
        numerator, denominator = sum(r.L for r in reference), sum(r.V - r.L for r in reference)
    elif estimator == 'LS':
        numerator = sum(L * O for L, O in bins.values())
        denominator = sum(O * O for L, O in bins.values())
    else:
        raise ValueError('non-frozen coefficient estimator')
    if denominator == 0:
        return {'status': 'NOT_DEFINED_REFERENCE_ZERO_OTHERS'}
    alpha = F(numerator, denominator)
    L, O = sum(r.L for r in view.rows), sum(r.V - r.L for r in view.rows)
    L_star, V_star = alpha * O, (alpha + 1) * O
    status = denominator_status(V_star)
    if status != 'DEFINED':
        return {'status': status}
    residual_bins = {}
    row_results = []
    for r in view.rows:
        b = bin_index(r.I, r.n)
        residual = F(r.L) - alpha * (r.V - r.L)
        residual_bins[b] = residual_bins.get(b, F(0)) + residual
        parties = list(map(F, r.parties))
        parties[1] = alpha * (r.V - r.L)
        row_results.append({'uuid': r.uuid, 'parties': parties, 'V_star': sum(parties),
                            'other9': [p for j, p in enumerate(parties) if j != 1]})
    return {'status': 'DEFINED', 'alpha': alpha, 'E': F(L) - L_star,
            'L_star': L_star, 'V_star': V_star, 'share': L_star / V_star,
            'residual_bins': residual_bins, 'rows': row_results,
            'eligible_count': len(view.rows), 'reference_count': len(reference),
            'source_valid': L + O,
            'geography_status': 'NO_CHANGE_EMPTY_REGION' if excluded_region is not None and
            len(view.rows) == len(data.rows) else 'FILTERED_OR_DEFAULT'}
