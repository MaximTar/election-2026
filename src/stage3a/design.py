"""Identity-only design. No response columns are requested by the real-data reader."""
import numpy as np
import pandas as pd
from .spec import ROOT, CONFIG, DESIGN_SOURCE, HIERARCHY_SOURCE, seed


def validate(d):
    required = {'uuid', 'region', 'tik_uuid', 'voters'}
    if set(d) != required or d[list(required)].isna().any().any():
        raise ValueError('Design whitelist/null violation')
    if d.uuid.duplicated().any() or (d.voters <= 0).any() or (d.voters != np.floor(d.voters)).any():
        raise ValueError('UUID/denominator violation')
    if d.groupby('tik_uuid').region.nunique().max() != 1:
        raise ValueError('TIK not nested in region')
    return d.sort_values('uuid').reset_index(drop=True)


def actual():
    d = pd.read_csv(ROOT/DESIGN_SOURCE, usecols=['uuid', 'resolved_region', 'voters'])
    h = pd.read_csv(ROOT/HIERARCHY_SOURCE, usecols=['uik_uuid', 'tik_uuid'])
    if h.uik_uuid.duplicated().any():
        raise ValueError('Hierarchy UUID duplicates')
    d = d.merge(h, left_on='uuid', right_on='uik_uuid', how='left', validate='one_to_one')
    d = validate(d.rename(columns={'resolved_region': 'region'}).drop(columns='uik_uuid'))
    summary = {'rows': len(d), 'regions': d.region.nunique(), 'tiks': d.tik_uuid.nunique(), 'voters': int(d.voters.sum())}
    if summary != CONFIG['actual_design']:
        raise ValueError(('Actual design changed', summary))
    return d


def toy():
    # Pure synthetic identities/sizes, independent of election outcomes and support.
    rows = []
    for r in range(4):
        for t in range(12):
            for i in range([6,16,36][t % 3]):
                rows.append((f'fake-{r:02}-{t:02}-{i:02}', f'r{r}', f't{r}-{t}',
                             30 + 150*(i//2) + 11*t))
    return validate(pd.DataFrame(rows, columns=['uuid', 'region', 'tik_uuid', 'voters']))


def folds(d, task):
    out = np.empty(len(d), dtype=int)
    if task == 'known_tik':
        for _, ind in d.groupby('tik_uuid', sort=True).groups.items():
            order = sorted(ind, key=lambda i: (seed('fold', task, d.uuid[i]), d.uuid[i]))
            for j, i in enumerate(order): out[i] = j % CONFIG['folds']
    elif task == 'heldout_tik':
        for _, group in d.groupby('region', sort=True):
            order = sorted(group.tik_uuid.unique(), key=lambda t: (seed('fold', task, t), t))
            for j, t in enumerate(order): out[group.index[group.tik_uuid == t]] = j % CONFIG['folds']
    else: raise ValueError(task)
    return out


def pairs(d):
    records = []; reasons = np.full(len(d), 'odd_exact_size_cell', dtype=object)
    for (tik, n), ind in d.groupby(['tik_uuid', 'voters'], sort=True).groups.items():
        ix = sorted(ind, key=lambda i: d.uuid[i])
        for a, b in zip(ix[0::2], ix[1::2]):
            records.append((len(records), a, b, d.uuid[a], d.uuid[b], tik, d.region[a], int(n)))
            reasons[[a, b]] = 'matched'
    p = pd.DataFrame(records, columns=['pair_id', 'left', 'right', 'left_uuid', 'right_uuid', 'tik_uuid', 'region', 'voters'])
    return p, pd.DataFrame({'uuid': d.uuid, 'reason': reasons})


def association_support(d, p):
    a = CONFIG['association']
    values = {'rows': 2*len(p), 'pairs': len(p), 'regions': p.region.nunique(),
              'tiks': p.tik_uuid.nunique(), 'voters': int(2*p.voters.sum()),
              'fraction': 2*len(p)/len(d)}
    values['supported'] = bool(values['rows'] >= a['min_rows'] and values['regions'] >= a['min_regions']
                               and values['tiks'] >= a['min_tiks'] and values['fraction'] >= a['min_fraction'])
    values['excluded_rows'] = len(d)-values['rows']
    return values


def strata(d):
    # Rank quartiles resolve ties by immutable UUID; used for audit, never conditioning.
    order = np.lexsort((d.uuid.to_numpy(), d.voters.to_numpy()))
    q = np.empty(len(d), dtype=int); q[order] = np.minimum(3, np.arange(len(d))*4//len(d))
    sizes = d.groupby('tik_uuid').uuid.transform('size').to_numpy()
    return {'all': np.ones(len(d), bool), **{f'size_q{k}': q == k for k in range(4)},
            'tik_n_lt10': sizes < 10, 'tik_n_10_29': (sizes >= 10)&(sizes < 30), 'tik_n_ge30': sizes >= 30}
