"""Recorded synthetic-only qualification. Every invocation writes a fresh attempt directory."""
import argparse
from dataclasses import replace
from fractions import Fraction as F
import hashlib
import inspect
import json
from pathlib import Path
import random
import resource
import signal
import sys
import time
import traceback
from unittest.mock import patch
from .common import (Row,SyntheticFrame,SMZError,validate,guard,canonical,fingerprint,wire,
                     LEVELS,SOURCES,UNKNOWN,NOT_DEFINED,PARTIES,shares)
from . import abc,d,api

ROOT=Path(__file__).resolve().parents[2]
FREEZE=ROOT/'outputs/scenario_model_zoo/20260929_v1'
CASES=[]; FIXTURES={}
SEED=202609290731

def case(name,families,covers=(),expected_status=False):
    def decorate(fn):
        CASES.append((name,tuple(families),tuple(covers),expected_status,fn)); return fn
    return decorate

def frame(name,rows,source='primary'):
    f=SyntheticFrame('syn:'+name,tuple(rows),source)
    try:
        FIXTURES[fingerprint(f)]=wire(f)
    except SMZError:
        # Deliberately invalid typed input must reach the domain gate, not an output encoder.
        raw=repr(f)
        FIXTURES[hashlib.sha256(raw.encode()).hexdigest()]={'invalid_fixture_repr':raw}
    return f

def row(i,n=1000,issued=500,valid=400,er=100,tik='t',region='r',invalid=5):
    return Row('syn:'+str(i),'syn:'+region,'syn:'+tik,n,issued,valid,
               (valid-er,er,0,0,0,0,0,0,0,0),invalid)

def af(name='a',same=False,unknown=False):
    rows=[]
    for i in range(40):
        issued=100+20*i; valid=issued-20
        er=valid//4 if same else (valid//4 if i<25 else valid*3//4)
        rows.append(row(i,issued=issued,valid=valid,er=er,invalid=None if unknown else 5))
    return frame(name,rows)

def df(name='d',tail=(240,240),fit=(20,20),source='primary'):
    rows=[]
    for i in range(6):
        rows.append(row(i,n=10000,issued=1000 if i<3 else 2000,valid=100,er=fit[0 if i<3 else 1]))
    for k,er in enumerate(tail):
        rows.append(row(6+k,n=10000,issued=5000+k*1000,valid=1200,er=er))
    return frame(name,rows,source)

def ad(f=None,design='R1-T1-D1-M2'): return abc.build(f or af(),design)
def supported(result): return [r for r in result['rows'] if r['status']=='SUPPORTED']
def ds(f=None,spec='D0'): return next(iter(d.execute(f or df(),spec)['strata'].values()))
def raises(status,fn):
    try: fn()
    except SMZError as exc:
        assert exc.status==status,(status,exc.status,exc.reason); return
    raise AssertionError('expected '+status)

def same_source(result,f):
    by={r.uuid:r for r in f.rows}
    for out in result['rows']:
        r=by[out['uuid']]
        assert (out['n'],out['issued'],out['valid'],out['parties'])==(r.n,r.issued,r.valid,r.parties)

@case('A_lambda_zero_identity','A',('ABC_SYN_01',))
def _():
    f=af(); same_source(abc.A(ad(f),0),f)

@case('A_party_permutation_and_eligibility','A',('ABC_SYN_02',))
def _():
    f=af(); perm=tuple(reversed(range(10)))
    g=frame('perm',[replace(r,parties=tuple(r.parties[j] for j in perm)) for r in f.rows])
    a,b=ad(f),ad(g); x,y=abc.A(a,1),abc.A(b,1)
    assert [(r.uuid,r.status,r.donors) for r in a.targets]==[(r.uuid,r.status,r.donors) for r in b.targets]
    assert all(tuple(i['parties'][j] for j in perm)==k['parties'] for i,k in zip(x['rows'],y['rows']))

@case('A_identical_composition_zero','A',('ABC_SYN_03',))
def _():
    f=af(same=True); same_source(abc.A(ad(f),1),f)

@case('A_sum_nonnegative_fixed_quantities','A',('ABC_SYN_04','ABC_SYN_05'))
def _():
    f=af(); by={r.uuid:r for r in f.rows}
    for lam in LEVELS:
        for r in abc.A(ad(f),lam)['rows']:
            original=by[r['uuid']]
            assert sum(r['parties'])==original.valid and min(r['parties'])>=0
            assert (r['n'],r['issued'],r['valid'],r['invalid'])==(original.n,original.issued,original.valid,original.invalid)

@case('A_exact_size_boundaries_no_cross_TIK','A',('ABC_SYN_07','ABC_SYN_08'))
def _():
    target=row('target',n=1000)
    refs=[row(i,n=n) for i,n in enumerate((799,800,1000,1250,1251))]
    refs.append(row('elsewhere',n=1000,tik='other'))
    assert tuple(r.n for r in abc.local_donors(target,refs,F(5,4)))==(800,1000,1250)
    refs2=[row(i,n=n) for i,n in enumerate((999,1000,2250,2251))]
    assert tuple(r.n for r in abc.local_donors(row('t2',n=1500),refs2,F(3,2)))==(1000,2250)

@case('A_midrank_tie_groups_and_thresholds','A',('ABC_SYN_08',))
def _():
    rows=[row(i,issued=200 if i<4 else 800,valid=100,er=20) for i in range(8)]
    f=frame('ties',rows); a=ad(f,'R1-T1-D1-M1')
    assert [abc.midranks(rows)[r.uuid] for r in rows]==[F(1,4)]*4+[F(3,4)]*4
    assert sum(t.status=='SUPPORTED' for t in a.targets)==4
    assert all(len(t.donors)==4 for t in a.targets if t.status=='SUPPORTED')
    g=frame('equal',[row(i) for i in range(8)])
    assert set(abc.midranks(g.rows).values())=={F(1,2)}
    assert abc.A(ad(g),1)['status']=='NOT_APPLICABLE_ON_THIS_DESIGN'

@case('A_row_order_and_repeat','A',('ABC_SYN_10',))
def _():
    f=af(); shuffled=list(f.rows); random.Random(SEED).shuffle(shuffled)
    g=frame('shuffle',shuffled)
    assert canonical(abc.A(ad(f),1))==canonical(abc.A(ad(g),1))
    assert canonical(abc.A(ad(f),1))==canonical(abc.A(ad(f),1))

@case('A_small_TIK_and_minimum_donors','A',('ABC_SYN_09',),True)
def _():
    f=frame('small',[row(i,issued=100+i*100,valid=50,er=10) for i in range(4)])
    t=[x for x in ad(f).targets if x.status!='NOT_SELECTED']
    assert t and all(x.status=='INSUFFICIENT_DONORS' for x in t)
    refs=[row(i) for i in range(5)]
    assert abc.donor_status(refs,refs[:2],3)=='INSUFFICIENT_DONORS'
    assert abc.donor_status(refs,refs[:3],3)=='SUPPORTED'
    assert abc.donor_status(refs,refs[:4],5)=='INSUFFICIENT_DONORS'
    assert abc.donor_status(refs,refs,5)=='SUPPORTED'

@case('A_no_reference_then_no_local_donors','A',('ABC_SYN_09',),True)
def _():
    # One low row and seven tied high rows => reference rank interval has no group.
    f=frame('no_ref',[row(i,issued=100 if i<4 else (500 if i<8 else 900),valid=50,er=10) for i in range(10)])
    assert all(t.status=='NO_REFERENCE_IN_TIK' for t in ad(f).targets if t.status!='NOT_SELECTED')
    assert abc.donor_status((),(),3)=='NO_REFERENCE_IN_TIK'
    # Direct status and integrated no-local-donor frame.
    f0=af(); f=frame('no_local',[replace(r,n=10000,issued=r.issued*10) if int(r.uuid[4:])>=30 else r for r in f0.rows])
    assert all(t.status=='NO_SIZE_LOCAL_DONOR' for t in ad(f).targets if t.status!='NOT_SELECTED')
    assert abc.donor_status([row(1)],(),3)=='NO_SIZE_LOCAL_DONOR'

@case('A_dominance_exact_half_and_beyond','A',('ABC_SYN_09',),True)
def _():
    refs=[row(i,valid=v,er=0) for i,v in enumerate((200,100,100))]
    assert abc.donor_status(refs,refs,3)=='SUPPORTED'
    refs[0]=row(0,valid=201,er=0)
    assert abc.donor_status(refs,refs,3)=='DONOR_DOMINANCE'

@case('A_zero_valid_support_primitive_and_source_STOP','A',('ABC_SYN_09',),True)
def _():
    refs=[row(i,valid=0,er=0) for i in range(3)]
    assert abc.donor_status(refs,refs,3)=='ZERO_REFERENCE_VALID'
    raises('SOURCE_FRAME_UNSUPPORTED',lambda: ad(frame('zero_valid',refs)))

@case('A_original_reference_immutable','A',('ABC_SYN_10',))
def _():
    design=ad(); before=canonical(design)
    for lam in LEVELS: abc.A(design,lam)
    assert canonical(design)==before
    ref=next(t for t in design.targets if t.status=='SUPPORTED')
    rows={r.uuid:r for r in design.frame.rows}; donor=[rows[k] for k in ref.donors]
    assert ref.q==tuple(F(sum(r.parties[j] for r in donor),sum(r.valid for r in donor)) for j in range(10))

@case('B_mu_zero','B',('ABC_SYN_01',))
def _():
    f=af(); same_source(abc.B(ad(f),0),f)

@case('B_mu_one_and_fractional_exact_handcheck','B',('ABC_SYN_05','ABC_SYN_06'))
def _():
    design=ad(); t=next(t for t in design.targets if t.status=='SUPPORTED'); rows={r.uuid:r for r in design.frame.rows}
    donors=[rows[k] for k in t.donors]; r=rows[t.uuid]
    tau=F(sum(k.issued for k in donors),sum(k.n for k in donors))
    for mu in LEVELS:
        out=next(x for x in abc.B(design,mu)['rows'] if x['uuid']==t.uuid)
        scale=(1-mu)+mu*r.n*tau/r.issued
        assert out['issued']==(1-mu)*r.issued+mu*r.n*tau
        assert out['valid']==scale*r.valid and out['parties']==tuple(scale*c for c in r.parties)
    assert any(x.denominator>1 for x in supported(abc.B(design,F(1,4)))[0]['parties'])

@case('B_composition_VI_JI_remainder_ratios','B',('ABC_SYN_04','ABC_SYN_05'))
def _():
    f=af(); source={r.uuid:r for r in f.rows}
    for out in abc.B(ad(f),F(3,4))['rows']:
        r=source[out['uuid']]
        assert out['n']==r.n
        assert out['valid']/out['issued']==F(r.valid,r.issued)
        assert out['invalid']/out['issued']==F(r.invalid,r.issued)
        assert out['valid']+out['invalid']+out['remainder']==out['issued']
        assert tuple(c/out['valid'] for c in out['parties'])==tuple(F(c,r.valid) for c in r.parties)

@case('B_unknown_invalid_not_imputed','B',('ABC_SYN_05',))
def _():
    for out in abc.B(ad(af(unknown=True)),1)['rows']:
        assert out['invalid']==out['remainder']==UNKNOWN
        assert out['combined_issued_minus_valid']==out['issued']-out['valid']

@case('B_invariant_violation_is_not_clipped','B',('ABC_SYN_06',),True)
def _():
    a=ad(); ts=list(a.targets); ix=next(i for i,t in enumerate(ts) if t.status=='SUPPORTED')
    ts[ix]=replace(ts[ix],tau=F(1)); bad=replace(a,targets=tuple(ts))
    # Rehash corrupted object to reach the scientific invariant check itself.
    ident=fingerprint({'source':bad.frame.source_id,'rows':validate(bad.frame),'design':bad.design_id,'targets':bad.targets})
    raises('ABC_DESIGN_INVARIANT_FAILURE',lambda: abc.B(replace(bad,object_id=ident),1))

@case('B_unsupported_shared_and_replay','B',('ABC_SYN_10','ABC_SYN_11'))
def _():
    f=frame('Bsmall',[row(i,issued=100+i*100,valid=50,er=10) for i in range(4)])
    a=ad(f); x,y=abc.A(a,1),abc.B(a,1)
    assert [r['status'] for r in x['rows']]==[r['status'] for r in y['rows']]
    same_source(y,f); assert canonical(y)==canonical(abc.B(a,1))

@case('C_identity_and_both_edge_aliases_all_levels','C',('ABC_SYN_01','ABC_SYN_11'))
def _():
    a=ad(); same_source(abc.C(a,0,0),a.frame)
    for v in LEVELS:
        assert abc.C(a,v,0)==abc.A(a,v)
        assert abc.C(a,0,v)==abc.B(a,v)

@case('C_full_application_handcheck','C',('ABC_SYN_11',))
def _():
    a=ad(); rby={r.uuid:r for r in a.frame.rows}; tby={t.uuid:t for t in a.targets}
    for out in supported(abc.C(a,1,1)):
        r=rby[out['uuid']]; donor=[rby[x] for x in tby[r.uuid].donors]
        iref=F(r.n*sum(k.issued for k in donor),sum(k.n for k in donor))
        valid=iref*F(r.valid,r.issued)
        expected=tuple(valid*F(sum(k.parties[j] for k in donor),sum(k.valid for k in donor)) for j in range(10))
        assert out['parties']==expected

@case('C_exact_decomposition_and_aggregation','C',('ABC_SYN_11',))
def _():
    a=ad()
    for lam,mu in ((F(1,4),F(3,4)),(F(1),F(1))):
        result=abc.C(a,lam,mu)
        for r in (*result['rows'],result['aggregate']):
            assert all(z==x+y+w for z,x,y,w in zip(r['delta'],r['composition'],r['intensity'],r['interaction']))
        assert sum(result['aggregate']['parties'])==result['scenario_valid']
        assert any(v for r in result['rows'] for v in r['interaction'])

@case('C_references_donors_unchanged_across_surface','C',('ABC_SYN_10','ABC_SYN_11'))
def _():
    a=ad(); saved=canonical(a)
    for lam in LEVELS:
        for mu in LEVELS:
            result=abc.C(a,lam,mu)
            assert result['reference_object_id']==a.object_id
            assert [r['status'] for r in result['rows']]==[t.status for t in a.targets]
    assert saved==canonical(a)

@case('C_party_equivariance','C',('ABC_SYN_02',))
def _():
    f=af(); perm=(1,0,2,3,4,5,6,7,8,9)
    g=frame('Cperm',[replace(r,parties=tuple(r.parties[j] for j in perm)) for r in f.rows])
    x,y=abc.C(ad(f),F(1,2),F(3,4)),abc.C(ad(g),F(1,2),F(3,4))
    for a,b in zip(x['rows'],y['rows']):
        for key in ('parties','composition','intensity','interaction'):
            assert tuple(a[key][j] for j in perm)==b[key]

@case('ABC_all_designs_canonical_alias_counts','ABC',('ABC_SYN_11',))
def _():
    cells=abc.canonical_cells(); assert len(cells)==len(set(cells))==1600
    assert len(abc.DESIGNS)==16
    for design in abc.DESIGNS:
        a=ad(design=design)
        assert abc.A(a,1)==abc.C(a,1,0) and abc.B(a,1)==abc.C(a,0,1)

@case('ABC_source_variants_rebuilt_never_stacked','ABC',('ABC_SYN_12',))
def _():
    base=af(); originals=list(base.rows)
    a=ad(base)
    s1=frame('source_s1',originals[5:],'S1')
    s2a=frame('source_s2a',[replace(r,parties=tuple(reversed(r.parties))) for r in originals],'S2a')
    s2b=frame('source_s2b',[replace(r,issued=r.issued+1) if i==0 else r for i,r in enumerate(originals)],'S2b')
    results=[ad(x) for x in (s1,s2a,s2b)]
    assert len({a.object_id,*[x.object_id for x in results]})==4
    assert results[2].frame.rows[1:]==base.rows[1:]
    assert results[0].targets!=a.targets

@case('ABC_serial_chunk_order_equivalence','ABC',('ABC_SYN_10',))
def _():
    a=ad(); grid=[(l,m) for l in LEVELS for m in LEVELS]
    serial={(l,m):fingerprint(abc.C(a,l,m)) for l,m in grid}
    chunks=[grid[i::3] for i in range(3)]
    reordered={(l,m):fingerprint(abc.C(a,l,m)) for chunk in reversed(chunks) for l,m in reversed(chunk)}
    assert serial==reordered

@case('ABC_ordinary_heterogeneity_nonzero','ABC',('ABC_CONCEPTUAL',))
def _():
    a=ad(); assert any(abc.A(a,1)['aggregate']['delta'])
    assert abc.B(a,1)['scenario_valid']<abc.B(a,1)['source_valid']
    assert any(abc.C(a,1,1)['aggregate']['delta'])

@case('ABC_fixed_seed_property_frames','ABC',('ABC_SYN_04','ABC_SYN_05','ABC_SYN_10'))
def _():
    rng=random.Random(SEED)
    for trial in range(8):
        rows=[]
        for i in range(40):
            issued=100+i*20; v=issued-20
            cuts=sorted([0,v]+[rng.randrange(v+1) for _ in range(9)])
            p=tuple(b-a for a,b in zip(cuts,cuts[1:]))
            rows.append(replace(row(i,issued=issued,valid=v),parties=p))
        f=frame('random'+str(trial),rows); a=ad(f)
        for lam,mu in ((F(1,4),F(1,2)),(F(1),F(1))):
            result=abc.C(a,lam,mu)
            assert all(sum(r['parties'])==r['valid'] and min(r['parties'])>=0 for r in result['rows'])
            assert result==abc.C(a,lam,mu)

@case('D_known_proportionality','D',('D_SYN_01',))
def _(): assert ds()['alpha']==F(1,4)

@case('D_zero_residual_identity','D',('D_SYN_02',))
def _():
    result=d.execute(df(),'D0'); s=next(iter(result['strata'].values()))
    assert s['status']=='APPLICABLE' and s['signed_stratum_residual']==0
    assert result['source_parties']==result['extended']['scenario_parties']

@case('D_signed_mixed_residual_and_cancellation','D',('D_SYN_03',))
def _():
    s=ds(df('mixed',(400,80)))
    assert s['positive_residual_sum']==200 and s['negative_residual_sum']==-200
    assert s['signed_stratum_residual']==0 and s['status']=='APPLICABLE'

@case('D_negative_aggregate_adjustment_not_clipped','D',('D_SYN_03',))
def _():
    s=ds(df('negative',(80,80)))
    assert s['signed_stratum_residual']==-400
    assert s['scenario_valid']==s['source_valid']+400

@case('D_alpha_zero_and_empty_bin_NULL','D',('D_SYN_05','D_SYN_09'))
def _():
    f=df('alpha0',(1200,240),(0,0)); s=ds(f)
    assert s['status']=='APPLICABLE' and s['alpha']==0
    b=d.bin_index(5000,10000,F(1,200))
    assert s['candidate_bins'][b]['valid']==0
    assert all(v.status=='NULL' for v in s['candidate_bins'][b]['shares'])

@case('D_degenerate_reference','D',('D_SYN_05','D_SYN_11'),True)
def _(): assert ds(df('degenerate',fit=(100,100)))['status']=='DEGENERATE_REFERENCE'

@case('D_one_informative_bin','D',('D_SYN_05',),True)
def _():
    s=ds(df('onebin',fit=(20,100)))
    assert s['status']=='INSUFFICIENT_FIT_SUPPORT' and s['reason']=='INFORMATIVE_BINS'

@case('D_less_than_five_fit_rows','D',('D_SYN_05','D_SYN_11'),True)
def _():
    f=df(); rows=list(f.rows[:2])+list(f.rows[3:5])+[replace(r,valid=800,parties=(640,160,0,0,0,0,0,0,0,0)) for r in f.rows[6:]]
    s=ds(frame('fourfit',rows))
    assert s['status']=='INSUFFICIENT_FIT_SUPPORT' and s['reason']=='FIT_ROWS' and s['fit_UIKs']==4

@case('D_no_target_status_precedes_other_failures','D',('D_SYN_05','D_SYN_11'),True)
def _():
    s=ds(frame('notail',[row('a',valid=100,er=100)]))
    assert s['status']=='NO_TARGET_SUPPORT' and s['flags']['FIT_ROWS'] and s['flags']['DEGENERATE_REFERENCE']

@case('D_whole_threshold_bin_exact_weight','D',('D_SYN_04',))
def _():
    s=ds(); assert s['threshold_bin']==40 and s['fit_valid_fraction']==F(1,5) and s['fit_UIKs']==6
    s=ds(spec='D1'); assert s['threshold_bin']==20 and s['fit_valid_fraction']==F(1,10)
    # q=.3 reaches first large tail bin, not a fraction of that bin.
    s=ds(spec='D2'); assert s['threshold_bin']==100 and s['fit_valid_fraction']==F(3,5)

@case('D_exact_boundaries_both_widths_zero_one','D',('D_SYN_04',))
def _():
    for h in (F(1,200),F(1,100)):
        count=int(1/h)
        assert d.bin_index(0,10000,h)==0 and d.bin_index(10000,10000,h)==count-1
        for b in range(1,count):
            n=count*100; boundary=b*100
            assert d.bin_index(boundary,n,h)==b
            assert d.bin_index(boundary-1,n,h)==b-1
    assert len(ds()['bins'])==200 and len(ds(spec='D3')['bins'])==100
    assert sum(b['UIKs']==0 for b in ds()['bins'])==196

@case('D_row_order_replay','D',('D_SYN_06',))
def _():
    f=df(); g=frame('Dreverse',reversed(f.rows))
    for spec in d.SPECS:
        assert d.execute(f,spec)==d.execute(g,spec)==d.execute(f,spec)

@case('D_histogram_aggregation_nonfocal_conservation','D',('D_SYN_07','D_SYN_08'))
def _():
    f=df('nonzero',(400,240)); result=d.execute(f,'D0'); s=next(iter(result['strata'].values()))
    assert sum(b['valid'] for b in s['bins'])==sum(r.valid for r in f.rows)
    assert sum(b['UIKs'] for b in s['bins'])==len(f.rows)
    assert s['scenario_valid']==sum(s['scenario_parties'])
    for j in range(10):
        assert sum(b['parties'][j] for b in s['bins'])==sum(r.parties[j] for r in f.rows)
        if j!=1: assert s['scenario_parties'][j]==s['source_parties'][j]

@case('D_electorate_ceiling_no_cap','D',('D_SYN_09',),True)
def _():
    rows=[row(i,n=1000,issued=100 if i<3 else 200,valid=100,er=80,invalid=0) for i in range(6)]
    rows += [row(6+i,n=1000,issued=800+i*50,valid=800,er=0,invalid=0) for i in range(3)]
    s=ds(frame('ceiling',rows))
    assert s['status']=='UNDEFINED_SCENARIO_TOTAL'
    assert any(b['valid']>src['n'] for b,src in zip(s['candidate_bins'],s['bins']))
    assert s['scenario_parties']==NOT_DEFINED

@case('D_no_UIK_allocation_and_typed_undefined','D',('D_SYN_10',))
def _():
    f=df(); result=d.execute(f,'D0')
    assert set(result['undefined'])==set(d.UNDEFINED)
    assert all(v==NOT_DEFINED for v in result['undefined'].values())
    assert 'rows' not in result
    data=json.loads(api.serialize(f,result))['result']
    assert all(v['status']=='NOT_DEFINED' for v in data['undefined'].values())
    for s in result['strata'].values(): assert 'uuid' not in canonical(s)

@case('D_native_identity_extension_and_none_applicable','D',('D_SYN_11',))
def _():
    f=df(); extra=row('unsupported',tik='t2',region='r2')
    result=d.execute(frame('mixed_support',f.rows+(extra,)),'D0')
    assert result['strata']['syn:r2']['status']=='NO_TARGET_SUPPORT'
    assert tuple(result['extended']['scenario_parties'][j]-result['native']['scenario_parties'][j] for j in range(10))==extra.parties
    result=d.execute(frame('none',[extra]),'D0')
    assert result['status']=='NOT_APPLICABLE_ON_THIS_DESIGN' and result['extended']['scenario_parties']==extra.parties

@case('D_fatal_source_and_numerical_no_identity_workaround','D',('D_SYN_11',),True)
def _():
    raises('SOURCE_FRAME_UNSUPPORTED',lambda: d.execute(frame('bad',[replace(row(1),valid=0)]),'D0'))
    with patch.object(d,'stratum',side_effect=ArithmeticError('injected engineering failure')):
        raises('NUMERICAL_OR_IMPLEMENTATION_FAILURE',lambda: d.execute(df(),'D0'))

@case('D_source_variants_rebuild_histograms','D',('D_SYN_12',))
def _():
    f=df(); a=d.execute(f,'D0')
    for source in SOURCES[1:]:
        g=frame('D'+source,[replace(r,issued=r.issued+51) for r in f.rows],source)
        b=d.execute(g,'D0')
        assert b['source_id']==source and b['strata']['syn:r']['bins']!=a['strata']['syn:r']['bins']

@case('D_ordinary_heterogeneity_nonzero','D',('D_CONCEPTUAL',))
def _():
    s=ds(df('ordinary',(400,240)))
    assert s['status']=='APPLICABLE' and s['signed_stratum_residual']==200

@case('D_all_specs_all_synthetic_source_ids','D',('D_SYN_06','D_SYN_12'))
def _():
    cells=set()
    for source in SOURCES:
        for spec in d.SPECS:
            result=d.execute(df(source=source),spec)
            assert result['source_id']==source and result['spec_id']==spec
            cells.add((source,spec))
    assert len(cells)==20

@case('governance_engines_do_not_call_each_other','ABCD')
def _():
    with patch.object(d,'execute',side_effect=AssertionError('D invoked by ABC')):
        api.execute(af(),'C','R1-T1-D1-M2',lam=1,mu=1)
    with patch.object(abc,'build',side_effect=AssertionError('ABC invoked by D')):
        api.execute(df(),'D','D0')
    assert 'from .abc' not in inspect.getsource(d) and 'from .d ' not in inspect.getsource(abc)

@case('governance_deferred_unknown_fail_closed','ABCD',expected_status=True)
def _():
    for name in ('H','HC','KYHT','smooth','historical','envelope','unknown'):
        raises('UNKNOWN_MODEL',lambda:api.execute(af(),name,'R1-T1-D1-M2'))
    raises('UNKNOWN_PARAMETER',lambda:api.execute(af(),'A','other'))
    raises('UNKNOWN_PARAMETER',lambda:api.execute(df(),'D','D5'))
    for value in (F(1,3),-1,2,.25,True):
        raises('UNKNOWN_PARAMETER',lambda:api.execute(af(),'C','R1-T1-D1-M2',lam=value))
    raises('UNKNOWN_PARAMETER',lambda:api.execute(af(),'A','R1-T1-D1-M2',mu=1))
    raises('UNKNOWN_PARAMETER',lambda:api.execute(df(),'D','D0',lam=1))

@case('governance_S3_alias_not_execution_unknown_source','ABCD',expected_status=True)
def _():
    assert api.source_alias('S3')=={'status':'IDENTITY_WITH_PRIMARY','execute':False,'alias':'primary'}
    for source in ('S3','other','S2a+S2b'):
        raises('SOURCE_FRAME_UNSUPPORTED',lambda:api.execute(replace(af(),source_id=source),'A','R1-T1-D1-M2'))

@case('governance_real_reveal_modes_paths_identity_rejected','ABCD',expected_status=True)
def _():
    f=af(); result=abc.A(ad(f),1)
    for mode in ('design_audit','closed_real_execution','real',''):
        raises('REAL_DATA_REVEAL_BLOCKED',lambda:api.execute(f,'A','R1-T1-D1-M2',mode=mode))
        raises('REAL_DATA_REVEAL_BLOCKED',lambda:api.serialize(f,result,mode=mode))
    for value in ('paper_primary__evidence_20260927','data/processed/primary.csv',{},None):
        raises('REAL_DATA_REVEAL_BLOCKED',lambda:api.execute(value,'A','R1-T1-D1-M2'))
    raises('REAL_DATA_REVEAL_BLOCKED',lambda:api.execute(replace(f,origin='REAL'),'A','R1-T1-D1-M2'))
    g=replace(f,rows=(replace(f.rows[0],uuid='real-id'),))
    raises('REAL_DATA_REVEAL_BLOCKED',lambda:api.execute(g,'A','R1-T1-D1-M2'))

@case('governance_source_integrity_closed_no_exclusions','ABCD',expected_status=True)
def _():
    r=row(0)
    bad=[replace(r,n=0),replace(r,issued=1001),replace(r,valid=501),replace(r,invalid=101),
         replace(r,parties=(400,)*10),replace(r,n=1000.0),replace(r,valid=True)]
    for k,b in enumerate(bad):
        f=frame('invalid'+str(k),[b])
        raises('SOURCE_FRAME_UNSUPPORTED',lambda:validate(f))
    raises('SOURCE_FRAME_UNSUPPORTED',lambda:validate(frame('duplicates',[r,r])))
    raises('SOURCE_FRAME_UNSUPPORTED',lambda:validate(frame('hierarchy',[r,replace(row(1),region='syn:another')])))

@case('governance_common_output_schema_and_lossless_serialization','ABCD')
def _():
    interface=json.loads((FREEZE/'output_interface.json').read_text())
    for family in 'ABCD':
        f=df() if family=='D' else af(); design='D0' if family=='D' else 'R1-T1-D1-M2'
        result=api.execute(f,family,design)
        records=api.common_records(f,result,family)
        assert len(records)==10
        assert all(set(interface['required_fields'])<=set(r) for r in records)
        if family=='D': assert all(set(interface['D_additional_required_fields'])<=set(r) for r in records)
        assert api.serialize(f,result)==api.serialize(f,result)
        assert fingerprint(json.loads(api.serialize(f,result)))
    # Frozen party/schema metadata only; no source responses read.
    from src.data.schema import PARTIES as SOURCE_PARTIES
    assert tuple(SOURCE_PARTIES.values())==PARTIES


def run(output):
    start=time.monotonic(); cpu=time.process_time()
    output.mkdir(parents=True,exist_ok=False)
    output=output.resolve()
    accesses=set()
    def io_boundary(event,args):
        if event!='open' or not isinstance(args[0],(str,bytes)): return
        path=Path(args[0]).resolve()
        if not path.is_relative_to(ROOT): return
        mode,flags=args[1:3]
        writes=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags & 3 != 0)
        if writes:
            if not path.is_relative_to(output): raise PermissionError('SYNTHETIC_STAGE_WRITE_BOUNDARY: '+str(path))
        elif not (path.is_relative_to(ROOT/'src') or path.is_relative_to(FREEZE) or path.is_relative_to(output)):
            raise PermissionError('SYNTHETIC_STAGE_REAL_INPUT_BLOCKED: '+str(path))
        accesses.add((str(path.relative_to(ROOT)), 'WRITE' if writes else 'READ'))
    sys.addaudithook(io_boundary)
    resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,8*1024**3))
    signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('RESOURCE_STOP')))
    signal.alarm(3600)
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'src/smz').glob('*.py'))}
    (output/'execution_freeze.json').write_text(json.dumps({'code':hashes,'seed':SEED,'mode':'synthetic_qualification'},indent=2)+'\n')
    checks=[]
    for name,families,covers,expected,fn in CASES:
        before=time.monotonic()
        try: fn(); status='PASS'; error=None
        except Exception:
            status='FAIL'; error=traceback.format_exc()
        checks.append({'id':name,'families':families,'covers':covers,'status':status,
                       'expected_contract_failure_fixture':expected,'error':error,'wall_seconds':time.monotonic()-before})
    families={}
    for family in 'ABCD':
        subset=[c for c in checks if family in c['families']]
        families[family]={'fixture_check_count':len(subset),'pass_count':sum(x['status']=='PASS' for x in subset),
                          'fail_count':sum(x['status']=='FAIL' for x in subset),
                          'expected_failure_fixture_count':sum(x['expected_contract_failure_fixture'] for x in subset),
                          'status':'PASS' if all(x['status']=='PASS' for x in subset) else 'FAIL'}
    registry=json.loads((FREEZE/'qualification_registry.json').read_text())['checks']
    mapping={}
    for item in registry:
        matching=[x for x in checks if item['id'] in x['covers']]
        mapping[item['id']]={'status':('PASS' if matching and all(x['status']=='PASS' for x in matching) else 'FAIL') if item['phase']=='SYNTHETIC_BEFORE_REAL' else 'NOT_RUN',
                             'checks':[x['id'] for x in matching],'phase':item['phase']}
    for path,sha in hashes.items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=sha: raise RuntimeError('POST_FREEZE_MODIFICATION')
    result={'status':'PASS' if all(x['status']=='PASS' for x in checks) and all(x['status']!='FAIL' for x in mapping.values()) else 'FAIL',
            'families':families,'checks':checks,'frozen_registry_mapping':mapping,
            'resources':{'wall_seconds':time.monotonic()-start,'cpu_seconds':time.process_time()-cpu,
                         'peak_RSS_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'process_count':1},
            'REAL_2026_SCENARIO_ROWS_PROCESSED':0,'REAL_SUPPORT_AUDIT_RUN':False,'REAL_SCENARIO_OUTPUTS_OPENED':False,
            'scientific_calibration':'NOT_PERFORMED_NOT_CLAIMED'}
    (output/'fixtures.json').write_text(json.dumps({'seed':SEED,'construction':'analytic and fixed-seed generic synthetic only','fixtures':FIXTURES},indent=2)+'\n')
    (output/'qualification.json').write_text(json.dumps(result,indent=2)+'\n')
    (output/'file_access_audit.json').write_text(json.dumps({'project_file_accesses':sorted(accesses),
        'boundary':'reads: source code, frozen contract metadata, own attempt; writes: own attempt only',
        'real_source_row_files_opened':0},indent=2)+'\n')
    signal.alarm(0)
    print(json.dumps({k:v for k,v in result.items() if k not in ('checks','frozen_registry_mapping')},indent=2))
    for c in checks:
        if c['status']=='FAIL': print(c['id'],c['error'])
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--output',required=True)
    args=parser.parse_args(); result=run(Path(args.output))
    raise SystemExit(0 if result['status']=='PASS' else 1)
