import dataclasses
import functools
import json
from pathlib import Path
import warnings
import numpy as np
from sklearn.mixture import GaussianMixture
from .common import IntegrityError, ResourceStop, digest, filtered, trace_call, trace_fit, validate

EPSILON = 1e-6
LABEL_TOL = 1e-10
SEEDS = tuple(range(202610020, 202610030))
ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / 'outputs/smz_v2_external_qualification/20261002_v1/phase_2_budget_gate.json'


def budget_gate():
    if json.loads(GATE.read_text())['status'] != 'PASS':
        raise IntegrityError('PHASE_2_BUDGET_BLOCKED')


@dataclasses.dataclass(frozen=True)
class SyntheticPoints:
    points: object
    UUIDs: tuple
    regions: tuple
    voters: tuple
    origin: str = 'SYNTHETIC_QUALIFICATION'

    def __post_init__(self):
        if self.origin != 'SYNTHETIC_QUALIFICATION' or any(not u.startswith('mock:') for u in self.UUIDs):
            raise IntegrityError('REAL_INPUT_FORBIDDEN')
        n = len(self.UUIDs)
        if len(set(self.UUIDs)) != n or len(self.regions) != n or len(self.voters) != n:
            raise IntegrityError('point identity')
        X = np.asarray(self.points, dtype=np.float64)
        if X.shape != (n, 2) or not np.all(np.isfinite(X)) or np.any((X < 0) | (X > 1)):
            raise IntegrityError('raw ratio domain; no clipping')
        if any(type(v) is not int or v <= 0 for v in self.voters):
            raise IntegrityError('registered voters')


def ordered_points(data, excluded_region=None):
    if not isinstance(data, SyntheticPoints):
        raise IntegrityError('REAL_INPUT_FORBIDDEN')
    indices = sorted([j for j, r in enumerate(data.regions) if r != excluded_region], key=lambda j: data.UUIDs[j])
    return np.asarray(data.points, dtype=np.float64)[indices], indices


def full_covariances(candidate):
    c = np.asarray(candidate['covariances'], dtype=np.float64)
    return np.array([np.diag(row) for row in c]) if candidate['covariance_type'] == 'diag' else c


def canonical_rows(candidate):
    c = full_covariances(candidate)
    return sorted([tuple([float(m[1]), float(m[0]), *map(float, c[j].ravel()), float(candidate['weights'][j])])
                   for j, m in enumerate(candidate['means'])])


def core_identity(candidate):
    cov = full_covariances(candidate)
    rows = [tuple([float(m[1]), float(m[0]), *map(float, cov[j].ravel()), float(candidate['weights'][j])])
            for j, m in enumerate(candidate['means'])]

    def compare(a, b):
        for x, y in zip(rows[a], rows[b]):
            if abs(x - y) > LABEL_TOL:
                return -1 if x < y else 1
        return 0

    # A tolerance comparator can be ambiguous/non-transitive. Frozen unresolved-identity
    # failure applies rather than allowing component slot order to decide the core.
    if any(compare(a, b) == 0 for a in range(3) for b in range(a + 1, 3)):
        return None
    order = sorted(range(3), key=functools.cmp_to_key(compare))
    if any(compare(order[a], order[b]) >= 0 for a in range(3) for b in range(a + 1, 3)):
        return None
    return order[0]


def covariance_diagnostics(candidate):
    c = np.asarray(candidate['covariances'], dtype=np.float64)
    output = []
    for j in range(3):
        eigenvalues = np.sort(c[j]) if candidate['covariance_type'] == 'diag' else np.linalg.eigvalsh(c[j])
        minimum, maximum = map(float, [eigenvalues[0], eigenvalues[-1]])
        delta = 64 * 2 ** -52 * max(1, maximum)
        output.append({'component': j, 'eigenvalues_or_variances': eigenvalues.tolist(),
                       'lambda_min': minimum, 'lambda_max': maximum, 'delta': delta,
                       'rho': EPSILON / minimum if minimum > 0 else None,
                       'floor_dominated': bool(minimum <= 2 * EPSILON),
                       'floor_contact': bool(abs(minimum - EPSILON) <= delta),
                       'covariance_domain_valid': bool(minimum >= EPSILON - delta)})
    return output


def candidate_domain(candidate):
    if not candidate.get('converged', False):
        return 'NOT_DEFINED_NO_CONVERGED_START'
    arrays = [np.asarray(candidate[k]) for k in ['means', 'weights', 'covariances', 'posterior']]
    if not np.isfinite(candidate['score']) or not all(np.all(np.isfinite(a)) for a in arrays):
        return 'NOT_DEFINED_LIKELIHOOD_NONFINITE'
    means, weights, cov, posterior = arrays
    if means.shape != (3, 2) or weights.shape != (3,) or posterior.ndim != 2 or posterior.shape[1] != 3:
        return 'NOT_DEFINED_COMPONENT_IDENTITY'
    if np.any((weights < 0) | (weights > 1)) or np.any((posterior < 0) | (posterior > 1)):
        return 'NOT_DEFINED_LIKELIHOOD_NONFINITE'
    if candidate['covariance_type'] == 'full':
        if cov.shape != (3, 2, 2) or not np.allclose(cov, cov.transpose(0, 2, 1), rtol=0, atol=64 * 2 ** -52):
            return 'NOT_DEFINED_COVARIANCE_DOMAIN'
    elif candidate['covariance_type'] == 'diag':
        if cov.shape != (3, 2):
            return 'NOT_DEFINED_COVARIANCE_DOMAIN'
    else:
        return 'NOT_DEFINED_COVARIANCE_DOMAIN'
    if not all(d['covariance_domain_valid'] for d in covariance_diagnostics(candidate)):
        return 'NOT_DEFINED_COVARIANCE_DOMAIN'
    return 'DEFINED'


def select(candidates):
    survivors = [c for c in candidates if candidate_domain(c) == 'DEFINED']
    if not survivors:
        statuses = [candidate_domain(c) for c in candidates]
        status = next((s for s in ['NOT_DEFINED_COVARIANCE_DOMAIN', 'NOT_DEFINED_LIKELIHOOD_NONFINITE',
                                  'NOT_DEFINED_COMPONENT_IDENTITY'] if s in statuses), 'NOT_DEFINED_NO_CONVERGED_START')
        return {'status': status, 'candidate_statuses': statuses}
    best = max(c['score'] for c in survivors)
    ties = [c for c in survivors if c['score'] >= best - 1e-10]
    chosen = min(ties, key=lambda c: (tuple(x for row in canonical_rows(c) for x in row), c['seed']))
    diagnostics = covariance_diagnostics(chosen)
    weights = np.asarray(chosen['weights'])
    posterior = np.asarray(chosen['posterior'])
    totals = np.sum(posterior, axis=0)
    core = core_identity(chosen)
    for d in diagnostics:
        d['role'] = 'UNRESOLVED_IDENTITY' if core is None else 'CORE' if d['component'] == core else 'NONCORE'
    result = {'status': 'DEFINED', 'selected_seed': chosen['seed'], 'selected_score': float(chosen['score']),
              'core_index': core, 'diagnostics': diagnostics, 'responsibility_sums': totals.tolist(),
              'weights': weights.tolist(), 'means': np.asarray(chosen['means']).tolist(),
              'covariances': np.asarray(chosen['covariances']).tolist(),
              'covariance_type': chosen['covariance_type'], 'second_best_rescue': False}
    # Weight/empty/identity reportability is applied only to the selected candidate.
    if np.any(weights <= 0) or not np.all(np.isfinite(totals)) or np.any(totals <= 0):
        result['status'] = 'NOT_DEFINED_COMPONENT_EMPTY'
    elif core is None:
        result['status'] = 'NOT_DEFINED_COMPONENT_IDENTITY'
    else:
        result['core_center'] = result['means'][core]
        result['REGULARIZATION_DOMINATED_CORE'] = diagnostics[core]['floor_dominated']
        result['_core_posterior'] = posterior[:, core].copy()
        result['_selected_candidate'] = chosen
        result['fit_blob_sha256'] = digest({'parameters': canonical_rows(chosen), 'covariance_type': chosen['covariance_type'],
                                          'epsilon': EPSILON, 'score': float(chosen['score'])})
    return result


def fit(data, covariance_type='full', excluded_region=None, model_factory=None):
    budget_gate()
    X, indices = ordered_points(data, excluded_region)
    trace_call('NOVAYA_2D', len(X))
    if len(X) < 3:
        return {'status': 'NOT_DEFINED_NO_CONVERGED_START', 'reason': 'MINIMUM_ROWS_3', 'start_attempts': 0}
    if covariance_type not in ['full', 'diag']:
        raise ValueError('unfrozen covariance')
    factory = GaussianMixture if model_factory is None else model_factory
    candidates, errors, warning_types = [], [], []
    for seed in SEEDS:
        trace_fit('NOVAYA_2D' if model_factory is None else 'NOVAYA_2D_INJECTED_BACKEND')
        try:
            model = factory(n_components=3, covariance_type=covariance_type, reg_covar=EPSILON,
                            tol=1e-6, max_iter=500, n_init=1, init_params='kmeans', random_state=seed)
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter('always')
                model.fit(X)
            warning_types.extend(type(z.message).__name__ for z in w)
            scores = model.score_samples(X)
            posterior = model.predict_proba(X)
            candidates.append({'converged': bool(model.converged_), 'seed': seed,
                               'score': float(np.mean(scores)), 'means': model.means_, 'weights': model.weights_,
                               'covariances': model.covariances_, 'posterior': posterior,
                               'covariance_type': covariance_type})
        except (MemoryError, TimeoutError, ResourceStop):
            raise
        except Exception as error:
            errors.append({'seed': seed, 'exception_type': type(error).__name__})
    result = select(candidates)
    result.update(start_attempts=10, seed_schedule=list(SEEDS), errors=errors, warning_types=warning_types,
                  postfilter_UUIDs=[data.UUIDs[j] for j in indices],
                  _voters=np.array([data.voters[j] for j in indices], dtype=np.int64),
                  geography_status='NO_CHANGE_EMPTY_REGION' if excluded_region is not None and
                  len(indices) == len(data.UUIDs) else 'FILTERED_OR_DEFAULT',
                  trace=['filter_region', 'rebuild_raw_features', 'full_10_start_fit'])
    return result


def threshold_output(fitted, threshold=.5):
    if threshold not in [.5, .7, .9]:
        raise ValueError('unfrozen threshold')
    if fitted['status'] != 'DEFINED':
        return {'status': fitted['status']}
    posterior = fitted['_core_posterior']
    voters = fitted.get('_voters', np.ones(len(posterior), dtype=np.int64))
    membership = np.asarray(posterior) > threshold
    return {'status': 'DEFINED', 'threshold': threshold, 'operator': '>',
            'core_center': fitted['core_center'], 'fit_blob_sha256': fitted['fit_blob_sha256'],
            'membership_count': int(np.sum(membership)), 'registered_voters': int(np.sum(voters[membership])),
            'registered_voter_coverage': float(np.sum(voters[membership]) / np.sum(voters)),
            'member_indices': np.flatnonzero(membership).tolist()}


def run_frame(data, excluded_region=None, covariance_type='full'):
    validate(data)
    points = SyntheticPoints(np.array([[r.I / r.n, r.L / r.V] for r in data.rows]),
                             tuple(r.uuid for r in data.rows), tuple(r.region for r in data.rows), tuple(r.n for r in data.rows))
    return fit(points, covariance_type, excluded_region)
