import dataclasses
from fractions import Fraction as F
import numpy as np
from scipy.optimize import least_squares
from .common import IntegrityError, ResourceStop, filtered, trace_call, trace_fit, validate

TAU = 1e-8
MEAN_STARTS = ((.10, .45, .80), (.15, .50, .85), (.05, .35, .70), (.20, .55, .90))
SIGMA_STARTS = (.05, .10, .20)


@dataclasses.dataclass(frozen=True)
class SyntheticHistogram:
    h: F
    mass: object
    origin: str = 'SYNTHETIC_QUALIFICATION'

    def __post_init__(self):
        if self.origin != 'SYNTHETIC_QUALIFICATION' or F(self.h) not in [F(1, 200), F(1, 100), F(1, 50)]:
            raise IntegrityError('REAL_INPUT_OR_UNFROZEN_WIDTH_FORBIDDEN')


def grid(h):
    h = F(h)
    return np.array([float((F(j) + F(1, 2)) * h) for j in range(int(1 / h))])


def bin_index(L, V, h):
    h = F(h)
    n = int(1 / h)
    if V <= 0 or not 0 <= L <= V:
        raise IntegrityError('party share domain')
    return min(n - 1, L * n // V)


def canonical_params(parameters):
    p = np.asarray(parameters, dtype=float).reshape(3, 3)
    return np.asarray(sorted(p.tolist(), key=lambda row: (row[0], row[1], row[2])))


def shapes(x, parameters):
    p = np.asarray(parameters).reshape(3, 3)
    return np.exp(-(x[None, :] - p[:, 0, None]) ** 2 / (2 * p[:, 1, None] ** 2))


def curve(x, parameters):
    p = np.asarray(parameters).reshape(3, 3)
    return np.sum(p[:, 2, None] * shapes(x, p), axis=0)


def start_parameters():
    return [np.array([[mu, sigma, 1 / 3] for mu in means]).ravel()
            for means in sorted(MEAN_STARTS) for sigma in SIGMA_STARTS]


def admissible(candidate, h):
    p = np.asarray(candidate['parameters']).reshape(3, 3)
    return (candidate.get('converged', False) and np.all(np.isfinite(p)) and
            np.isfinite(candidate['sse']) and candidate['sse'] >= 0 and
            np.all((0 <= p[:, 0]) & (p[:, 0] <= 1)) and
            np.all((float(h) / 2 <= p[:, 1]) & (p[:, 1] <= 1)) and np.all(p[:, 2] >= 0))


def reportability(parameters, h):
    p = canonical_params(parameters)
    G = shapes(grid(h), p)
    peaks = np.max(p[:, 2, None] * G, axis=1)
    disappeared = np.flatnonzero(peaks <= TAU).tolist()
    identities, near_means = [], []
    for k in range(3):
        for l in range(k + 1, 3):
            distance = float(np.max(np.abs(G[k] - G[l])))
            if distance <= TAU:
                identities.append([k, l])
            elif abs(p[k, 0] - p[l, 0]) <= TAU:
                near_means.append([k, l])
    lower = np.flatnonzero(p[:, 1] - float(h) / 2 <= TAU).tolist()
    upper = np.flatnonzero(1 - p[:, 1] <= TAU).tolist()
    means = np.flatnonzero((p[:, 0] <= TAU) | (1 - p[:, 0] <= TAU)).tolist()
    flags = {'COMPONENT_DISAPPEARED': disappeared, 'COMPONENT_IDENTITY': identities,
             'RESOLUTION_LIMIT': lower, 'WIDTH_LIMIT': upper,
             'MEAN_BOUNDARY_CONTACT': means, 'NEAR_COINCIDENT_MEANS': near_means}
    status = 'DEFINED'
    for name in ['COMPONENT_DISAPPEARED', 'COMPONENT_IDENTITY', 'RESOLUTION_LIMIT', 'WIDTH_LIMIT']:
        if flags[name]:
            status = 'NOT_DEFINED_' + name
            break
    return {'status': status, 'core_center': float(p[0, 0]) if status == 'DEFINED' else None,
            'parameters': p.tolist(), 'component_peaks': peaks.tolist(), 'flags': flags,
            'sigma_min': float(h) / 2, 'tau': TAU}


def select(candidates, h):
    survivors = [c for c in candidates if admissible(c, h)]
    if not survivors:
        finite_converged = any(c.get('converged', False) and np.isfinite(c['sse']) and
                               np.all(np.isfinite(c['parameters'])) for c in candidates)
        return {'status': 'NOT_DEFINED_PARAMETER_DOMAIN' if finite_converged else
                'NOT_DEFINED_OPTIMIZER_NO_CONVERGED_START', 'candidate_count': len(candidates)}
    best_sse = min(c['sse'] for c in survivors)
    ties = [c for c in survivors if c['sse'] <= best_sse + 1e-12]
    chosen = min(ties, key=lambda c: tuple(canonical_params(c['parameters']).ravel()))
    # No reportability filtering of survivors: a failed best fit is final.
    result = reportability(chosen['parameters'], h)
    result.update(selected_start_id=chosen['start_id'], selected_sse=float(chosen['sse']),
                  converged_admissible_starts=len(survivors), second_best_rescue=False)
    return result


def fit(histogram, optimizer=None):
    if not isinstance(histogram, SyntheticHistogram):
        raise IntegrityError('REAL_INPUT_FORBIDDEN')
    h = F(histogram.h)
    Y = np.asarray(histogram.mass, dtype=np.float64)
    if Y.shape != (int(1 / h),) or not np.all(np.isfinite(Y)) or np.any(Y < 0):
        return {'status': 'NOT_DEFINED_PARAMETER_DOMAIN'}
    if not np.any(Y):
        return {'status': 'NOT_DEFINED_ZERO_MASS'}
    trace_call('NOVAYA_1D', len(Y))
    Y = Y / np.max(Y)
    x = grid(h)
    backend = least_squares if optimizer is None else optimizer
    lower = np.tile([0, float(h) / 2, 0], 3)
    upper = np.tile([1, 1, np.inf], 3)
    candidates, failures = [], []
    for j, initial in enumerate(start_parameters()):
        trace_fit('NOVAYA_1D' if optimizer is None else 'NOVAYA_1D_INJECTED_BACKEND')
        try:
            res = backend(lambda params: curve(x, params) - Y, initial, method='trf',
                          bounds=(lower, upper), ftol=1e-10, xtol=1e-10, gtol=1e-10, max_nfev=5000)
            p = np.asarray(res.x)
            residuals = np.asarray(res.fun)
            finite = np.all(np.isfinite(p)) and np.all(np.isfinite(residuals))
            sse = float(np.dot(residuals, residuals))
            candidates.append({'parameters': p, 'sse': sse, 'start_id': j,
                               'converged': bool(res.success and res.status > 0 and finite)})
        except (MemoryError, TimeoutError, ResourceStop):
            raise
        except Exception as error:
            failures.append({'start_id': j, 'exception_type': type(error).__name__})
    result = select(candidates, h)
    result.update(start_attempts=12, failed_starts=failures, bounded_global_optimum_claimed=False)
    if result['status'] == 'DEFINED':
        result['normalized_curve_RMSE'] = float(np.sqrt(result['selected_sse'] / len(Y)))
    return result


def run_frame(data, h=F(1, 100), excluded_region=None):
    validate(data)
    view = filtered(data, excluded_region)
    if not view.rows:
        return {'status': 'NOT_DEFINED_EMPTY_ELIGIBLE'}
    mass = [0] * int(1 / h)
    for row in view.rows:
        mass[bin_index(row.L, row.V, h)] += row.L
    result = fit(SyntheticHistogram(h, mass))
    result.update(trace=['filter_region', 'rebuild_histogram', 'full_12_start_fit'],
                  postfilter_UUIDs=[r.uuid for r in view.rows],
                  geography_status='NO_CHANGE_EMPTY_REGION' if excluded_region is not None and
                  len(view.rows) == len(data.rows) else 'FILTERED_OR_DEFAULT')
    return result
