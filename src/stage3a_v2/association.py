"""Exact-size, one-category randomized coarsening. No finite-caliper approximation."""
import numpy as np
from .spec import CONFIG, rng
from .design import association_support


def projection(votes, valid, random):
    if np.any(valid <= 0) or not np.array_equal(votes.sum(axis=1), valid):
        raise ValueError('Invalid composition')
    u = random.random(len(valid))
    category = np.minimum(9, np.sum(u[:, None] >= np.cumsum(votes/valid[:, None], axis=1), axis=1))
    return np.eye(10, dtype=int)[category]


def orientation_scores(parent_scores, random, B):
    signs = 2*random.integers(0, 2, size=(B, len(parent_scores)), dtype=np.int8)-1
    return signs @ parent_scores, signs


def holm(p):
    p=np.asarray(p);order=np.argsort(p,kind='stable');out=np.empty_like(p)
    out[order]=np.minimum(1.,np.maximum.accumulate((len(p)-np.arange(len(p)))*p[order]))
    return out


def test(d, y, pairs, key, diagnostic=False):
    if not y.get('synthetic', False): raise RuntimeError('Real-response execution not implemented')
    if not diagnostic and not association_support(d, pairs)['supported']:
        return {'status': 'UNSUPPORTED'}
    a, b = pairs.left.to_numpy(), pairs.right.to_numpy()
    if not len(a): return {'status': 'UNSUPPORTED'}
    Z = projection(y['votes'], y['valid'], rng(*key, 'projection'))
    T = y['issued']/d.voters.to_numpy()
    products = (T[a]-T[b])[:, None]*(Z[a]-Z[b])
    parent, inv = np.unique(pairs.tik_uuid, return_inverse=True)
    S = np.zeros((len(parent), 10)); np.add.at(S, inv, products)
    scale = np.sqrt(np.square(S).sum(axis=0))
    if np.any(scale <= 0): return {'status': 'NOT_IDENTIFIED_ZERO_SCALE'}
    score = S.sum(axis=0)/scale
    references, _ = orientation_scores(S, rng(*key, 'orientations'), CONFIG['association']['B'])
    reference_z = references/scale
    # Add-one rule with >= ties, whole-party-vector joint max statistic.
    raw = (1+(np.abs(reference_z) >= np.abs(score)).sum(axis=0))/(len(references)+1)
    adjusted = (1+(np.max(np.abs(reference_z), axis=1)[:, None] >= np.abs(score)).sum(axis=0))/(len(references)+1)
    return {'status': 'IDENTIFIED', 'effect': products.sum(axis=0)/(2*len(pairs)),
            'score': score, 'p_raw': raw, 'p_holm': holm(raw), 'p_maxT_diagnostic': adjusted, 'parent_scores': S,
            'support_rows': len(a)*2, 'parents': len(parent)}
