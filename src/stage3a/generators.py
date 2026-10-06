"""Count-level synthetic worlds. No election response is an input."""
import numpy as np
from scipy.special import expit, softmax
from .spec import CONFIG, rng


def multinomial_rows(n, p, random):
    # Sequential binomials are exactly multinomial; no rounding of compositions.
    n = np.asarray(n, dtype=np.int64); p = np.asarray(p, float)
    out = np.zeros((len(n), p.shape[1]), np.int64); remaining = n.copy()
    mass = np.ones(len(n))
    for j in range(p.shape[1]-1):
        prob = np.clip(p[:, j]/np.maximum(mass, 1e-15), 0, 1)
        out[:, j] = random.binomial(remaining, prob)
        remaining -= out[:, j]; mass -= p[:, j]
    out[:, -1] = remaining
    return out


def validate_protocol(d, y):
    n = d.voters.to_numpy(); I, V, C = y['issued'], y['valid'], y['votes']
    assert I.shape == V.shape == (len(d),) and C.shape == (len(d), 10)
    assert np.issubdtype(I.dtype, np.integer) and np.issubdtype(C.dtype, np.integer)
    assert np.all((0 < V)&(V <= I)&(I <= n))
    assert np.all(C >= 0) and np.array_equal(C.sum(axis=1), V)


def generate(d, scenario, replicate, stream='evaluation', strength=0., sign=1, target=0):
    if scenario not in CONFIG['scenarios']: raise ValueError(scenario)
    if strength not in [0., *CONFIG['positive_strengths']] or sign not in [-1, 1] or not 0 <= target < 10:
        raise ValueError('Unfrozen positive specification')
    key = [stream, scenario, replicate, strength, sign, target]
    rr = lambda label: rng(*key, label)
    n = d.voters.to_numpy(np.int64); z = np.clip(np.log(n/1000.), -5., 5.)
    _, r = np.unique(d.region, return_inverse=True); _, t = np.unique(d.tik_uuid, return_inverse=True)
    nr, nt = r.max()+1, t.max()+1
    phi = 2*np.pi*np.arange(10)/10
    aT = .25*rr('T_region').normal(size=nr)[r]+.35*rr('T_tik').normal(size=nt)[t]
    aY = .25*rr('Y_region').normal(size=(nr, 10))[r]+.35*rr('Y_tik').normal(size=(nt, 10))[t]
    fT = .45*np.sin(z)+.2*np.tanh(z)
    fY = .35*np.sin(z[:, None]+phi)+.15*np.cos(2*z[:, None])*np.cos(phi)
    eT = rr('T_row').normal(size=len(d)); eY = rr('Y_row').normal(size=(len(d), 10))
    sT = np.full(len(d), .2); sY = np.full(len(d), .25)
    latent = np.zeros(len(d)); true_n = n.copy()
    if scenario == 'N2':
        fT = 2*np.tanh(80*np.sin(z))
        fY = 1.5*np.tanh(80*np.sin(z[:, None]))*np.cos(phi)
    elif scenario == 'N3':
        fT += .45*rr('T_curve').normal(size=nt)[t]*np.sin(3*z)+.2*rr('T_slope').normal(size=nt)[t]*z
        fY += .45*rr('Y_curve').normal(size=(nt, 10))[t]*np.sin(3*z[:, None])+.2*rr('Y_slope').normal(size=(nt, 10))[t]*z[:, None]
    elif scenario == 'N4':
        sT = .1+.5*expit(z); sY = .1+.7*expit(-z)
    elif scenario == 'N5':
        eT = rr('T_skew').exponential(size=len(d))-1
        eY = rr('Y_skew').exponential(size=(len(d), 10))-1
    elif scenario == 'N6':
        fT += 1.3*(2*rr('T_type').binomial(1, .5, len(d))-1)
        fY += 1.6*(2*rr('Y_type').binomial(1, .5, len(d))-1)[:, None]*np.cos(phi)
    elif scenario == 'N7':
        # Shared within-cluster shocks, independent between response families.
        fT += .6*rr('T_region_shock').normal(size=nr)[r]+.5*rr('T_tik_shock').normal(size=nt)[t]
        fY += .6*rr('Y_region_shock').normal(size=(nr, 10))[r]+.5*rr('Y_tik_shock').normal(size=(nt, 10))[t]
    elif scenario == 'N8':
        fT = .8*np.sin(2*z)+.3*z
        fY = .7*np.cos(3*z[:, None]+phi)-.25*z[:, None]*np.sin(phi)
    elif scenario == 'N9':
        # Observed n stays actual; latent effective electorate and preferences vary.
        measured = rr('measurement').uniform(size=len(d)) < .1
        true_n[measured] = np.maximum(1, np.floor(.8*n[measured]).astype(int))
        latent = measured.astype(float)
        fY += .8*latent[:, None]*np.cos(phi)
    elif scenario == 'N10':
        latent = rr('shared_type').binomial(1, expit(.5*z), len(d)).astype(float)
        fT += 1.2*(latent-.5); fY += 1.4*(latent-.5)[:, None]*np.cos(phi)
    etaT = .2+aT+fT+sT*eT
    etaY = aY+fY+sY[:, None]*eY
    # Positive loadings alter logits, not a purported fixed correlation.
    # eT is the sole deliberately shared innovation; zero strength means none.
    contrast = np.full(10, -1/9); contrast[target] = 1.
    etaY += sign*strength*eT[:, None]*contrast
    pT = expit(etaT); pY = softmax(etaY, axis=1)
    if scenario == 'N5':
        g = rr('Y_dirichlet').gamma(12*pY); pY = g/g.sum(axis=1, keepdims=True)
    q = .98-.03*expit(z)
    counts = rr('turnout_valid_counts')
    I = counts.binomial(true_n, pT); V = counts.binomial(I, q)
    for attempt in range(100000):
        bad = V == 0
        if not bad.any(): break
        I[bad] = counts.binomial(true_n[bad], pT[bad]); V[bad] = counts.binomial(I[bad], q[bad])
    else: raise RuntimeError('Positive-valid truncation sampler failed; no imputation')
    C = multinomial_rows(V, pY, rr('party_counts'))
    y = {'issued': I, 'valid': V, 'votes': C, 'pT': pT, 'pY': pY, 'q': q,
         'true_n': true_n, 'latent': latent, 'innovation_T': eT, 'innovation_Y': eY,
         'synthetic': True, 'scenario': scenario, 'stream': stream}
    validate_protocol(d, y)
    return y


def equivalence(y):
    """Exact observed-law equivalence; ordinary preferences vs latent relabelling."""
    observed = y['votes'].copy()
    baseline_a = observed.copy()
    baseline_b = observed.copy()
    moved = baseline_b[:, 0]//5
    baseline_b[:, 0] -= moved; baseline_b[:, 1] += moved
    # B's hypothetical mechanism transfers moved votes back from party1 to party0.
    reconstructed = baseline_b.copy(); reconstructed[:, 1] -= moved; reconstructed[:, 0] += moved
    assert np.array_equal(observed, reconstructed)
    removed=observed.copy();removed[:,0]-=moved
    return {'observed_a': observed, 'observed_b': reconstructed,
            'baseline_a': baseline_a, 'baseline_b': baseline_b,
            'baseline_c_votes': removed, 'baseline_c_issued': y['issued']-moved,
            'baseline_c_valid': y['valid']-moved,
            'identification': 'NOT_IDENTIFIED', 'mechanism_b_transfer': moved}
