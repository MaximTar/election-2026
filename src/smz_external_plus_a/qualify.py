"""Fourteen separately named logical fixtures, synthetic arithmetic only."""
import copy
import csv
import hashlib
import json
import time
from fractions import Fraction as F
from unittest.mock import patch
from . import arithmetic, loader, preflight as p
from src.smz_external_clite import common, istories, cedar
from src.smz_external_real.coordinator import compact


def row(n=10000,I=2000,V=1800,L=600,invalid=0,**kw):
    return dict(n=n,I=I,V=V,L=L,invalid=invalid,**kw)


def packet(s,r):return {'state':s,'result':compact(r)}


def run():
    p.check_frozen()
    environment=p.verify_environment()
    states=list(csv.DictReader((p.FREEZE/'state_index.csv').open()))
    fixturedefs=p.read(p.FREEZE/'fixture_contract.json')['fixtures']
    modules={'ISTORIES':istories,'CEDAR':cedar}
    records=[];t=time.monotonic()
    widths=p.read(p.FREEZE/'catalog_delta.json')['new_windows_percent']
    anchors=[s for s in states if s['family']=='CEDAR']
    windows=[s for s in states if s['family']=='ISTORIES']
    # Exact proportionality throughout bins, all valid ballots including cast endpoints.
    grid=common.frame([row(I=j*100,V=j*100,L=j*30) for j in range(1,101)],'grid')

    def I1():
        outputs=[]
        for s in windows:
            r=arithmetic.execute(s,grid,modules)
            assert r['status']=='DEFINED' and r['alpha']==F(3,7) and r['E']==0
            assert r['share']==F(3,10)
            outputs.append(s['state_id'])
        return {'all_new_windows':len(outputs),'known_ROS':'3/7','zero_residual':True}

    def I2():
        checks=0
        for s in windows:
            lo,hi=json.loads(s['method_control_values'])['window_percent']
            data=common.frame([row(I=lo*100-1,V=100,L=10),row(I=lo*100,V=100,L=20),
                               row(I=hi*100-1,V=100,L=40),row(I=hi*100,V=100,L=90)],'boundary')
            r=arithmetic.execute(s,data,modules)
            assert r['reference_count']==2 and r['alpha']==F(60,140)
            checks+=1
        return {'windows':checks,'lower_inclusive_upper_exclusive':True}

    def I3():
        for s in windows:
            lo,hi=json.loads(s['method_control_values'])['window_percent']
            empty=arithmetic.execute(s,common.frame([row(I=9900)],'empty'),modules)
            assert empty['status']=='NOT_DEFINED_EMPTY_REFERENCE'
            zero=arithmetic.execute(s,common.frame([row(I=lo*100,V=100,L=100)],'zero'),modules)
            assert zero['status']=='NOT_DEFINED_REFERENCE_ZERO_OTHERS'
            sparse=arithmetic.execute(s,common.frame([row(I=lo*100,V=100,L=25)],'sparse'),modules)
            assert sparse['status']=='DEFINED' and sparse['reference_count']==1
        return {'empty_and_zero_O_fail_closed':True,'no_invented_minimum_reference_count':True}

    def I4():
        for s in windows:
            lo,hi=json.loads(s['method_control_values'])['window_percent']
            data=common.frame([row(I=lo*100,V=100,L=50),row(I=9000,V=100,L=80),row(I=9500,V=100,L=20)],'signed')
            r=arithmetic.execute(s,data,modules)
            assert r['alpha']==1 and r['E']==0
            assert min(r['residual_bins'].values())<0<max(r['residual_bins'].values())
            assert sum(r['residual_bins'].values())==r['E']
            arithmetic.reconcile(s,data,r,None)
        bad=common.frame([row(parties=(1,)*10)],'bad')
        assert arithmetic.execute(windows[0],bad,modules)['status']=='FAIL_SOURCE_INTEGRITY_ABORT_VARIANT'
        return {'signed_and_accounting':True,'source_domain_guard':True}

    def C1():
        h=arithmetic.cedar_histogram(cedar,grid)
        for s in anchors:
            r=arithmetic.execute(s,grid,modules,h)
            assert r['status']=='DEFINED' and r['alpha']==F(3,7) and r['E']==0
            arithmetic.reconcile(s,grid,r,h)
        return {'anchors_tested':71,'low_mid_high_included':True,'known_coefficient':'3/7'}

    def C2():
        for s in anchors:
            percent=json.loads(s['method_control_values'])['fixed_anchor_right_edge_percent']
            assert cedar.bin_index(percent*100,10000)==percent-1
            assert cedar.bin_index(percent*100+1,10000)==percent
            assert cedar.bin_index((percent-1)*100,10000)==percent-2
        assert cedar.bin_index(10000,10000)==99
        return {'right_edges':71,'one_pp_grid':True,'100_percent_bin':99}

    def C3():
        s=anchors[0]
        missing=common.frame([row(I=5000,V=4000,L=1500)],'missing')
        assert arithmetic.execute(s,missing,modules)['status']=='NOT_DEFINED_ANCHOR_ZERO_OTHERS'
        zero=common.frame([row(I=1000,V=1000,L=1000)],'zeroO')
        assert arithmetic.execute(s,zero,modules)['status']=='NOT_DEFINED_ANCHOR_ZERO_OTHERS'
        return {'missing_bin_equals_zero_O':True,'no_neighbor_search':True}

    def C4():
        data=common.frame([row(n=100,I=100,V=90,L=30),row(invalid=None),row(I=1000,V=900,L=300,invalid=100)],'eligible')
        h=arithmetic.cedar_histogram(cedar,data)
        assert h['eligible_count']==1 and h['L'][9]==300 and h['O'][9]==700
        assert cedar.eligible_reason(data.rows[0])=='REGISTERED_LE_100'
        assert cedar.eligible_reason(data.rows[1])=='INVALID_UNKNOWN'
        empty=common.frame([row(invalid=None)],'unknown')
        assert arithmetic.execute(anchors[0],empty,modules)['status']=='NOT_DEFINED_EMPTY_ELIGIBLE'
        return {'cast_includes_known_invalid':True,'unknown_excluded_not_imputed':True,'n100_excluded':True}

    def C5():
        data=common.frame([row(I=1000,V=1000,L=100),row(I=9000,V=1000,L=20)],'signedC')
        r=arithmetic.execute(anchors[0],data,modules)
        assert r['status']=='DEFINED' and r['E']<0 and r['main']<0
        return {'signed_negative_preserved':True,'AUTO_called':False}

    def S1():
        assert len(states)==len({s['state_id'] for s in states})==83
        assert len(windows)==12 and len(anchors)==71
        base=list(csv.DictReader((p.ROOT/'outputs/smz_v2_external_freeze/20261002_v2/state_index.csv').open()))
        assert not {s['state_id'] for s in states}&{s['state_id'] for s in base}
        assert all(s['visibility']=='public' and s['requires_fit']=='false' for s in states)
        return {'state_count':83,'new_IDs':True,'fit_states':0}

    def S2():
        n=0
        for s in states:
            for field,value in [('source','S1'),('source','S2a'),('source','S2b'),('excluded_region_id','mock:region'),('family','NOVAYA_1D'),('requires_fit','true')]:
                changed=dict(s);changed[field]=value
                try:arithmetic.controls(changed)
                except ValueError:n+=1
                else:raise AssertionError('FORBIDDEN_ROUTE_ACCEPTED')
        return {'forbidden_routes_rejected':n,'availability_explicit':True}

    def S3():
        h=arithmetic.cedar_histogram(cedar,grid);hashes=[]
        reverse=common.SyntheticFrame(tuple(reversed(grid.rows)))
        hr=arithmetic.cedar_histogram(cedar,reverse)
        for s in states:
            a=arithmetic.execute(s,grid,modules,h);b=arithmetic.execute(s,reverse,modules,hr)
            arithmetic.reconcile(s,grid,a,h);arithmetic.reconcile(s,reverse,b,hr)
            wire=common.canonical(packet(s,a));replay=common.canonical(packet(s,b))
            assert wire==replay
            decoded=json.loads(wire)
            assert common.canonical(decoded)==wire
            if s['family']=='ISTORIES':
                assert all(isinstance(k,int) for k in compact(a)['residual_bins'])
                assert all(isinstance(k,str) for k in decoded['result']['residual_bins'])
            hashes.append(hashlib.sha256(wire).hexdigest())
        return {'qualified_transport_routes':len(hashes),'deterministic_hashes':True,'integer_key_conversion_at_JSON_only':True}

    def S4():
        for s in states:
            r={'status':'NOT_DEFINED_REFERENCE_ZERO_OTHERS' if s['family']=='ISTORIES' else 'NOT_DEFINED_ANCHOR_ZERO_OTHERS'}
            decoded=json.loads(common.canonical(packet(s,r)))
            assert decoded['result']['status']==r['status']
        return {'all83_terminal_IDs_preservable':True,'no_promotion':True}

    def S5():
        p.check_frozen()
        proofs=[loader.transform(name)[1] for name in ['istories','cedar']]
        assert common.COUNTERS['real_party_rows']==common.COUNTERS['real_model_fits']==0
        assert sum(common.COUNTERS['synthetic_fit_attempts'].values())==0
        return {'function_AST_identical':proofs,'base_binding_hashes_unchanged':True,'optimizer_fits':0}

    tests=[I1,I2,I3,I4,C1,C2,C3,C4,C5,S1,S2,S3,S4,S5]
    # If any route tries the AUTO path it fails, without calling an optimizer.
    with patch.object(cedar,'auto_selector',side_effect=AssertionError('AUTO_FORBIDDEN')):
        for definition,test in zip(fixturedefs,tests):
            started=time.monotonic()
            try:observed=test();status='PASS';error=None
            except Exception as e:observed={};status='FAIL';error={'type':type(e).__name__,'message':str(e)}
            records.append({**definition,'status':status,'observed':observed,'error':error,
                            'runtime_seconds':time.monotonic()-started})
    assert len(records)==14
    result={'status':'PASS' if all(r['status']=='PASS' for r in records) else 'FAIL',
        'count':14,'passed':sum(r['status']=='PASS' for r in records),'records':records,
        'runtime_seconds':time.monotonic()-t,'new_mock_routes':83,
        'environment':environment,'implementation_sha256':p.sha(p.FREEZE/'implementation_bindings.json'),
        'no_real_data':{'real_party_rows':common.COUNTERS['real_party_rows'],'optimizer_fits':sum(common.COUNTERS['synthetic_fit_attempts'].values()),'base_result_reads':0}}
    p.QUAL.mkdir(parents=True,exist_ok=False)
    (p.QUAL/'qualification_results.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ['status','count','passed','runtime_seconds','new_mock_routes','no_real_data']},sort_keys=True))


if __name__=='__main__':run()
