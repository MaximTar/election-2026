import warnings
from fractions import Fraction as F
import numpy as np
from scipy.optimize import curve_fit
from .common import IntegrityError, ResourceStop, filtered, trace_call, trace_fit, validate


def eligible_reason(row):
    if row.n <= 100:
        return 'REGISTERED_LE_100'
    if row.invalid is None:
        return 'INVALID_UNKNOWN'
    if row.V + row.invalid <= 0:
        return 'CAST_NONPOSITIVE'
    if row.V + row.invalid > row.n:
        return 'CAST_GT_REGISTERED'
    return ''


def bin_index(cast, n):
    if n <= 0 or not 0 < cast <= n:
        raise IntegrityError('cast domain')
    return (100 * cast + n - 1) // n - 1


def gaussian(x, mu, sigma, A):
    return A * np.exp(-(x - mu) ** 2 / (2 * sigma ** 2))


def bimodal(x, mu1, sigma1, A1, mu2, sigma2, A2):
    return gaussian(x, mu1, sigma1, A1) + gaussian(x, mu2, sigma2, A2)


def smoothing(O):
    y = np.convolve(np.asarray(O, dtype=np.float64), np.ones(5) / 5, mode='same')
    y[-2:] = O[-2:]
    return y


def auto_selector(O, fit_backend=None):
    O = np.asarray(O, dtype=np.float64)
    if O.shape != (100,) or not np.all(np.isfinite(O)) or np.any(O < 0):
        raise IntegrityError('histogram domain')
    backend = curve_fit if fit_backend is None else fit_backend
    x = np.linspace(0, 1, 101)[1:]
    y = smoothing(O)
    mu1 = np.argmax(y) / 100
    initial = (mu1, .1, max(y), mu1 + (1 - mu1) / 2, .01,
               y[int(mu1 * 100 + (1 - mu1) / 2 * 100)])
    diagnostics = {'initial': list(map(float, initial)), 'warning_types': []}
    try:
        trace_fit('CEDAR' if fit_backend is None else 'CEDAR_INJECTED_BACKEND')
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            params, _ = backend(bimodal, x[:-3], y[:-3], p0=initial, method='lm',
                                ftol=1.49012e-8, xtol=1.49012e-8, gtol=0,
                                maxfev=1400, epsfcn=None, factor=100, diag=None)
        diagnostics['warning_types'] = [type(z.message).__name__ for z in w]
        if not np.all(np.isfinite(params)):
            return {'status': 'NOT_DEFINED_SELECTOR_NONFINITE', 'diagnostics': diagnostics}
        with np.errstate(divide='ignore', invalid='ignore', over='ignore'):
            finite_curve = np.all(np.isfinite(bimodal(x, *params)))
        if not finite_curve:
            return {'status': 'NOT_DEFINED_SELECTOR_NONFINITE', 'diagnostics': diagnostics}
        mu, sigma = params[:2] if params[0] < params[3] else params[3:5]
        a, b = int((mu - sigma) * 100), int((mu + sigma) * 100)
        anchor = a + int(np.argmax(y[a:b]))
        diagnostics.update(parameters=list(map(float, params)), slice=[a, b])
        path = 'FIT'
    except (MemoryError, TimeoutError, ResourceStop):
        raise
    except Exception as error:
        anchor = int(np.argmax(O[:-3]))
        path = 'PUBLISHED_EXCEPTION_FALLBACK'
        diagnostics['exception_type'] = type(error).__name__
    if not 0 <= anchor <= 99:
        return {'status': 'NOT_DEFINED_ANCHOR_DOMAIN', 'diagnostics': diagnostics}
    return {'status': 'DEFINED', 'anchor': anchor, 'path': path, 'diagnostics': diagnostics}


def single_anchor(L, O, anchor):
    if not 0 <= anchor <= 99:
        return {'status': 'NOT_DEFINED_ANCHOR_DOMAIN'}
    if O[anchor] == 0:
        return {'status': 'NOT_DEFINED_ANCHOR_ZERO_OTHERS'}
    if sum(L) == 0:
        return {'status': 'NOT_DEFINED_FOCAL_DENOMINATOR'}
    alpha = F(int(L[anchor]), int(O[anchor]))
    E = F(sum(L)) - alpha * sum(O)
    return {'status': 'DEFINED', 'anchor': anchor, 'alpha': alpha, 'E': E, 'main': E / sum(L)}


def offset_outputs(L, O, selected, offsets=(-5, 0, 5)):
    if selected['status'] != 'DEFINED':
        return {offset: dict(selected) for offset in offsets}
    return {offset: single_anchor(L, O, selected['anchor'] + offset) for offset in offsets}


def run(data, excluded_region=None, fit_backend=None):
    trace_call('CEDAR', len(data.rows))
    trace = ['eligibility_filter']
    try:
        validate(data)
        view = filtered(data, excluded_region)
    except IntegrityError:
        return {'status': 'FAIL_SOURCE_INTEGRITY_ABORT_VARIANT'}
    rows = [r for r in view.rows if not eligible_reason(r)]
    if not rows:
        return {'status': 'NOT_DEFINED_EMPTY_ELIGIBLE', 'trace': trace}
    L, O = [0] * 100, [0] * 100
    for row in rows:
        b = bin_index(row.V + row.invalid, row.n)
        L[b] += row.L
        O[b] += row.V + row.invalid - row.L
    trace.extend(['rebuild_histogram', 'AUTO_selector'])
    selected = auto_selector(O, fit_backend)
    if selected['status'] != 'DEFINED':
        return {**selected, 'trace': trace}
    trace.extend(['coefficient', 'output'])
    result = single_anchor(L, O, selected['anchor'])
    result.update(selector=selected, offsets=offset_outputs(L, O, selected), trace=trace,
                  eligible_UUIDs=[r.uuid for r in rows], eligible_count=len(rows), histogram_L=L, histogram_O=O)
    result['geography_status'] = 'NO_CHANGE_EMPTY_REGION' if excluded_region is not None and len(rows) == sum(
        not eligible_reason(r) for r in data.rows) else 'FILTERED_OR_DEFAULT'
    return result
