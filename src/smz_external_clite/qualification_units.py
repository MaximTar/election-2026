"""Additional implementation tests. Not additional scientific fixtures."""
import copy
from fractions import Fraction as F
import numpy as np
from . import gaussian1d as n, gmm2d as g


def run():
    results = []

    def test(name, family, function):
        try:
            observed = function()
            results.append({'id': name, 'family': family, 'status': 'PASS', 'observed': observed})
        except Exception as error:
            results.append({'id': name, 'family': family, 'status': 'FAIL',
                            'error': type(error).__name__ + ': ' + str(error)})

    def require(condition, value):
        assert condition, str(value)
        return value

    base = np.array([[.18, .04, 1], [.5, .05, .8], [.82, .035, .6]])

    def n_case(change, expected, h=F(1, 100), flag=None):
        p = base.copy()
        change(p)
        r = n.reportability(p, h)
        assert r['status'] == expected, r
        if flag:
            assert r['flags'][flag], r
        return r

    for h in [F(1, 200), F(1, 100), F(1, 50)]:
        test('UNIT_U1_FLOOR_' + str(h), 'NOVAYA_1D',
             lambda h=h: n_case(lambda p: p.__setitem__((0, 1), float(h) / 2),
                                'NOT_DEFINED_RESOLUTION_LIMIT', h, 'RESOLUTION_LIMIT'))
    test('UNIT_U1_DISAPPEARED', 'NOVAYA_1D', lambda: n_case(
        lambda p: p.__setitem__((0, 2), 0), 'NOT_DEFINED_COMPONENT_DISAPPEARED'))
    test('UNIT_U1_TINY', 'NOVAYA_1D', lambda: n_case(
        lambda p: p.__setitem__((0, 2), 1e-10), 'NOT_DEFINED_COMPONENT_DISAPPEARED'))
    test('UNIT_U1_IDENTICAL', 'NOVAYA_1D', lambda: n_case(
        lambda p: p.__setitem__((1, slice(0, 2)), p[0, :2]), 'NOT_DEFINED_COMPONENT_IDENTITY'))
    test('UNIT_U1_UPPER', 'NOVAYA_1D', lambda: n_case(
        lambda p: p.__setitem__((0, 1), 1), 'NOT_DEFINED_WIDTH_LIMIT'))
    for edge in [0, 1]:
        test('UNIT_U1_MEAN_ENDPOINT_' + str(edge), 'NOVAYA_1D', lambda edge=edge: n_case(
            lambda p: p.__setitem__((0, 0), edge), 'DEFINED', flag='MEAN_BOUNDARY_CONTACT'))
    test('UNIT_U1_NEAR_MEANS_DISTINCT_WIDTH', 'NOVAYA_1D', lambda: n_case(
        lambda p: (p.__setitem__((1, 0), .18), p.__setitem__((1, 1), .08)),
        'DEFINED', flag='NEAR_COINCIDENT_MEANS'))

    def n_no_rescue():
        good = {'parameters': base.copy(), 'sse': 1., 'converged': True, 'start_id': 1}
        bad = copy.deepcopy(good)
        bad['parameters'][0, 2] = 0
        bad.update(sse=0., start_id=0)
        r = n.select([good, bad], F(1, 100))
        assert r['status'] == 'NOT_DEFINED_COMPONENT_DISAPPEARED' and r['selected_start_id'] == 0, r
        return r

    test('UNIT_U1_BEST_NOT_RESCUED', 'NOVAYA_1D', n_no_rescue)

    def n_priority():
        p = base.copy()
        p[0, 2] = 0
        p[0, 1] = .005
        r = n.reportability(p, F(1, 100))
        assert r['status'] == 'NOT_DEFINED_COMPONENT_DISAPPEARED'
        assert r['flags']['RESOLUTION_LIMIT'] and r['flags']['COMPONENT_DISAPPEARED']
        return r

    test('UNIT_U1_ALL_FLAGS_PRIORITY', 'NOVAYA_1D', n_priority)

    def n_bad_domain():
        p = base.copy()
        p[0, 0] = -.01
        r = n.select([{'parameters': p, 'sse': 0., 'converged': True, 'start_id': 0}], F(1, 100))
        return require(r['status'] == 'NOT_DEFINED_PARAMETER_DOMAIN', r)

    test('UNIT_U1_DOMAIN', 'NOVAYA_1D', n_bad_domain)

    def candidate(covtype='full'):
        cov = np.array([np.eye(2) * .0004] * 3) if covtype == 'full' else np.array([[.0004, .0004]] * 3)
        return {'means': np.array([[.2, .15], [.5, .45], [.82, .8]]), 'weights': np.array([.3, .3, .4]),
                'covariances': cov, 'posterior': np.array([[.3, .3, .4]] * 8),
                'covariance_type': covtype, 'converged': True, 'score': -1., 'seed': g.SEEDS[0]}

    def g_floor(covtype, value, component, expected_dominance):
        c = candidate(covtype)
        c['covariances'][component] = np.eye(2) * value if covtype == 'full' else [value, value]
        r = g.select([c])
        assert r['status'] == 'DEFINED', r
        assert r['diagnostics'][component]['floor_dominated'] == expected_dominance, r
        if component == 0:
            assert r['REGULARIZATION_DOMINATED_CORE'] == expected_dominance, r
        return {k: v for k, v in r.items() if not k.startswith('_')}

    for covtype in ['full', 'diag']:
        for component in [0, 1]:
            test(f'UNIT_U2_FLOOR_{covtype}_{component}', 'NOVAYA_2D',
                 lambda covtype=covtype, component=component: g_floor(covtype, 1e-6, component, True))
        test('UNIT_U2_INCLUSIVE_' + covtype, 'NOVAYA_2D', lambda covtype=covtype: g_floor(covtype, 2e-6, 0, True))
        test('UNIT_U2_NO_TOLERANCE_' + covtype, 'NOVAYA_2D', lambda covtype=covtype:
             g_floor(covtype, float(np.nextafter(2e-6, np.inf)), 0, False))

    def contact():
        c = candidate()
        delta = 64 * 2 ** -52
        c['covariances'][0] = np.eye(2) * (1e-6 - delta / 2)
        r = g.select([c])
        assert r['status'] == 'DEFINED' and r['diagnostics'][0]['floor_contact']
        assert r['diagnostics'][0]['delta'] == delta
        return r['diagnostics']

    test('UNIT_U2_EXACT_CONTACT_DELTA', 'NOVAYA_2D', contact)

    def covariance_failure():
        c = candidate()
        c['covariances'][0] = np.eye(2) * (1e-6 - 2 * 64 * 2 ** -52)
        r = g.select([c])
        return require(r['status'] == 'NOT_DEFINED_COVARIANCE_DOMAIN', r)

    test('UNIT_U2_BELOW_FLOOR', 'NOVAYA_2D', covariance_failure)

    def empty_responsibility():
        c = candidate()
        c['posterior'][:, 0] = 0
        worse = candidate()
        worse['score'] = -2
        r = g.select([worse, c])
        return require(r['status'] == 'NOT_DEFINED_COMPONENT_EMPTY' and r['selected_score'] == -1.,
                       {k: v for k, v in r.items() if not k.startswith('_')})

    test('UNIT_U2_EMPTY_BEST_NOT_RESCUED', 'NOVAYA_2D', empty_responsibility)

    def no_cutoff():
        c = candidate()
        c['weights'] = np.array([1e-100, .4, .6])
        c['posterior'] = np.array([[1e-100, .4, .6]] * 8)
        r = g.select([c])
        return require(r['status'] == 'DEFINED', {'status': r['status'], 'responsibility_sums': r['responsibility_sums']})

    test('UNIT_U2_NO_POSITIVE_WEIGHT_CUTOFF', 'NOVAYA_2D', no_cutoff)

    def identity():
        c = candidate()
        c['means'][:] = [.2, .15]
        c['weights'][:] = 1 / 3
        c['posterior'][:] = 1 / 3
        r = g.select([c])
        return require(r['status'] == 'NOT_DEFINED_COMPONENT_IDENTITY',
                       {k: v for k, v in r.items() if not k.startswith('_')})

    test('UNIT_U2_UNRESOLVED_IDENTITY', 'NOVAYA_2D', identity)
    return {'category': 'ADDITIONAL_IMPLEMENTATION_UNIT_TESTS', 'not_scientific_fixture_count': True,
            'count': len(results), 'results': results,
            'status': 'PASS' if all(r['status'] == 'PASS' for r in results) else 'FAIL'}
