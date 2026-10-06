"""Bounded dispatch reusing qualified iStories/Cedar arithmetic, with no fit path."""
import json
from fractions import Fraction


def controls(state):
    c = json.loads(state['method_control_values'])
    if state['source'] != 'primary' or state['excluded_region_id']:
        raise ValueError('FORBIDDEN_FRAME_CROSS')
    if state['visibility'] != 'public' or state['requires_fit'] != 'false':
        raise ValueError('FORBIDDEN_VISIBILITY_OR_FIT')
    if state['family'] == 'ISTORIES':
        if set(c) != {'window_percent', 'coefficient'} or c['coefficient'] != 'ROS':
            raise ValueError('FORBIDDEN_ISTORIES_CONTROL')
        lo, hi = c['window_percent']
        if lo not in [10, 15, 20, 25, 30] or hi-lo not in [5, 10, 15]:
            raise ValueError('WINDOW_OUTSIDE_CATALOG')
        if (lo, hi) in [(15,25), (20,30), (25,35)]:
            raise ValueError('BASE_STATE_REEXECUTION_FORBIDDEN')
    elif state['family'] == 'CEDAR':
        if set(c) != {'fixed_anchor_right_edge_percent', 'bin_index'}:
            raise ValueError('FORBIDDEN_CEDAR_CONTROL')
        p = c['fixed_anchor_right_edge_percent']
        if type(p) is not int or not 10 <= p <= 80 or c['bin_index'] != p-1:
            raise ValueError('FIXED_ANCHOR_DOMAIN')
    else:
        raise ValueError('UNAUTHORIZED_FAMILY')
    return c


def cedar_histogram(module, frame):
    view = module.filtered(frame)
    rows = [r for r in view.rows if not module.eligible_reason(r)]
    L, O = [0]*100, [0]*100
    for r in rows:
        b = module.bin_index(r.V+r.invalid, r.n)
        L[b] += r.L
        O[b] += r.V+r.invalid-r.L
    return {'L': L, 'O': O, 'rows': rows, 'eligible_count': len(rows)}


def execute(state, frame, modules, cedar_hist=None):
    c = controls(state)
    if state['family'] == 'ISTORIES':
        m = modules['ISTORIES']
        window = tuple(Fraction(p,100) for p in c['window_percent'])
        return m.run(frame, window=window, estimator='ROS', excluded_region=None)
    h = cedar_hist if cedar_hist is not None else cedar_histogram(modules['CEDAR'], frame)
    if not h['eligible_count']:
        return {'status':'NOT_DEFINED_EMPTY_ELIGIBLE'}
    result = modules['CEDAR'].single_anchor(h['L'], h['O'], c['bin_index'])
    result.update(eligible_count=h['eligible_count'], anchor_rule='FIXED_RIGHT_EDGE',
                  anchor_right_edge_percent=c['fixed_anchor_right_edge_percent'])
    return result


def reconcile(state, frame, result, cedar_hist):
    """Exact bookkeeping only. No alternate estimator or substantive logging."""
    if state['family'] == 'ISTORIES':
        rows = frame.rows
    else:
        rows = cedar_hist['rows']
    result['input_coverage'] = {'eligible_UIKs':len(rows), 'voters':sum(r.n for r in rows),
                                'valid':sum(r.V for r in rows), 'excluded_region_id':None}
    if result['status'] != 'DEFINED':
        return
    if state['family'] == 'ISTORIES':
        L, O = sum(r.L for r in rows), sum(r.V-r.L for r in rows)
        assert result['L_star'] == result['alpha']*O
        assert result['V_star'] == result['L_star']+O
        assert result['E'] == L-result['L_star']
        assert result['share'] == result['L_star']/result['V_star']
        assert sum(result['residual_bins'].values()) == result['E']
        parties = [sum(r.parties[j] for r in rows) for j in range(10)]
        parties[1] = result['L_star']
        assert sum(parties) == result['V_star']
        result['scenario_party_totals'] = parties
    else:
        L, O = cedar_hist['L'], cedar_hist['O']
        r = controls(state)['bin_index']
        assert result['alpha'] == Fraction(L[r],O[r])
        assert result['E'] == sum(L)-result['alpha']*sum(O)
        assert result['main'] == result['E']/sum(L)
