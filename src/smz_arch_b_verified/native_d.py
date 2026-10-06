"""Native-bin D; immutable qualified stratum function, no ABC reference dependency."""
from fractions import Fraction as F
from src.smz import d,common
from .basis import sum_exact
from .codec import columnar,records

def compact(r):
    out={k:v for k,v in r.items() if k not in ('bins','candidate_bins')}
    out['bin_domain']=len(r['bins'])
    out['bins']=columnar(((b['bin'],b['n'],b['valid'],b['UIKs'],*b['parties']) for b in r['bins'] if b['UIKs']),('bin','n','valid','UIKs',*('p'+str(j) for j in range(10))))
    out['candidate_defined']=r['candidate_bins']!=common.NOT_DEFINED
    return out
def expand(r):
    out={k:v for k,v in r.items() if k not in ('bin_domain','candidate_defined','bins')}
    bins=[dict(bin=i,n=0,valid=0,UIKs=0,parties=[0]*10) for i in range(r['bin_domain'])]
    for row in records(r['bins']):bins[row[0]]=dict(bin=row[0],n=row[1],valid=row[2],UIKs=row[3],parties=list(row[4:]))
    out['bins']=tuple(bins)
    if r['candidate_defined']:
        candidate=[]
        for b,e in zip(bins,r['signed_bin_residual']):
            p=list(map(F,b['parties']));p[1]-=e;v=sum(p)
            candidate.append(dict(parties=tuple(p),valid=v,shares=common.shares(p,v)))
        out['candidate_bins']=tuple(candidate)
    else:out['candidate_bins']=common.NOT_DEFINED
    return out
def run(rows,spec,emit):
    from .engine import guard_rows
    guard_rows(rows)
    geography,q,h=d.SPECS[spec];groups={}
    for i,r in enumerate(rows):groups.setdefault(getattr(r,geography),[]).append(i)
    summary={};app=[];targets=[]
    for name in sorted(groups):
        indices=groups[name];rr=[rows[i] for i in indices]
        result=d.stratum(rr,q,h);c=compact(result);emit(name,c)
        assert expand(c)==result,'D_COMPACT_EQUIVALENCE'
        summary[name]={k:result[k] for k in ('status','source_parties','source_valid','scenario_parties','scenario_valid','tail_UIKs')}
        if result['status']=='APPLICABLE':app.extend(indices)
        targets.extend(i for i in indices if d.bin_index(rows[i].issued,rows[i].n,h)>result['threshold_bin'])
    source=common.totals(rows)
    native=tuple(sum_exact(v['scenario_parties'][j] for v in summary.values() if v['status']=='APPLICABLE') for j in range(10))
    extended=tuple(sum_exact(v['scenario_parties'][j] if v['status']=='APPLICABLE' else v['source_parties'][j] for v in summary.values()) for j in range(10))
    ns=common.totals([rows[i] for i in app]);assert all(extended[j]==source[j] for j in range(10) if j!=1)
    return dict(engine='D',spec_id=spec,status='APPLICABLE' if app else 'NOT_APPLICABLE_ON_THIS_DESIGN',source_parties=source,source_valid=sum(source),
        native=dict(source_parties=ns,scenario_parties=native,source_valid=sum(ns),scenario_valid=sum(native),shares=common.shares(native,sum(native))),
        extended=dict(scenario_parties=extended,scenario_valid=sum(extended),shares=common.shares(extended,sum(extended)),identity_extended_status={k:'APPLIED' if v['status']=='APPLICABLE' else 'SCENARIO_NOT_APPLIED' for k,v in summary.items()}),
        selected_targets=len(targets),supported_targets=sum(v['tail_UIKs'] for v in summary.values() if v['status']=='APPLICABLE'),coverage=common.coverage([rows[i] for i in app],rows),
        target_coverage=common.coverage([rows[i] for i in targets],rows),undefined={k:common.NOT_DEFINED for k in d.UNDEFINED})
