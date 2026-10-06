"""Single bounded synthetic-only equivalence battery, no rejection-rate analysis."""
from src.analysis import descriptive_env
import argparse,io,json,signal,time,unittest,traceback
import numpy as np
import pandas as pd
from src.stage3a_v2.generators import generate
from src.stage3a_v2 import association
from src.stage3a_v2.models import LPeer,subset
from src.stage3a_qualification import lb
from src.stage3a_qualification.spec import plain
from src.stage3a_real import adapters as ad
from .spec import ROOT,OUT,CFG,verify,write,sha,read
from .design import context,support

def serialized(value):return json.dumps(plain(value),sort_keys=True,separators=(',',':'),allow_nan=False)
def job(c,variant,scenario,experiment):
    number=int(scenario[1:]);fold=(number-1)%5;namespace=CFG['namespace']+'/'+variant
    y=generate(c['d'],scenario,0,stream=namespace,experiment=experiment)
    yy={**y,'origin':'synthetic_preopen','synthetic':False};key=[namespace,'A',scenario,experiment]
    ref=association.test(c['d'],y,c['pairs'],key);act=ad.association(c['d'],yy,c['pairs'],key);ad.equivalent(ref,act)
    out=dict(variant=variant,scenario=scenario,experiment=experiment,fold=fold,A=plain(act),LB={})
    if experiment=='complete':
        old=lb.predict(c,y,fold,scenario,0,namespace);model=ad.fit_fold(c,yy,fold)
        raw_model=LPeer().fit(c['frames'][fold],subset(y,c['train'][fold]))
        for cell,z in old.items():
            row=int(z['row']);cal=np.asarray(z['calibration_rows']);new=ad.target(c,yy,model,row,cal)
            # Every selected target/calibration donor-cache entry checked against original no-cache function.
            for i in np.r_[row,cal]:
                cached=model.neighbours(c['d'],int(i));uncached=raw_model.neighbours(c['d'],int(i));ad.equivalent(cached,uncached)
            for field in ['observed','denominator','mean','sd','interval','comparator']:ad.equivalent(z[field],new[field])
            sample=ad.sample(c,row,namespace=namespace)
            assert row not in sample and len(np.unique(sample))==len(sample)
            assert set(sample)<=set(c['pools'][fold,int(cell)])
            # Separate per-target all-target sampler replay without altering qualification reference target.
            np.testing.assert_array_equal(sample,ad.sample(c,row,namespace=namespace))
            out['LB'][cell]=plain(new)
        if scenario=='N1':
            # Predetermined reverse chunk ordering; no second fit/selection or new RNG.
            for cell,z in reversed(list(old.items())):
                new=ad.target(c,yy,model,int(z['row']),np.asarray(z['calibration_rows']))
                ad.equivalent(out['LB'][cell],plain(new))
            # All heldout responses may be mutated; actual training records remain identical.
            mutated={**yy,'votes':yy['votes'].copy()};held=c['fold']==fold
            mutated['votes'][held]=np.roll(mutated['votes'][held],1,axis=1)
            other=ad.fit_fold(c,mutated,fold)
            for k in ['issued','valid','votes']:np.testing.assert_array_equal(model.y[k],other.y[k])
    return out

def design_checks(c):
    d=c['d'];s=support(c);assert s['A']['supported']
    rows=set(c['pairs'].left)|set(c['pairs'].right);assert len(rows)==2*len(c['pairs'])
    assert d.voters.iloc[c['pairs'].left].reset_index(drop=True).equals(d.voters.iloc[c['pairs'].right].reset_index(drop=True))
    weight=0
    for (f,j),pool in c['pools'].items():
        assert len(pool)>0 and c['eligible'][pool].all() and (c['fold'][pool]==f).all() and (c['cell'][pool]==j).all()
        assert not set(pool)&set(c['train'][f]);weight+=len(pool)/(40*len(pool))
        assert set(c['train'][f])==set(np.flatnonzero(c['fold']!=f))
        for row in pool:
            ix,w,level=c['neighbours'][f][int(row)]
            assert len(ix)==len(w) and len(ix)<=32 and len(set(ix))==len(ix)
            assert (ix>=0).all() and (ix<len(c['frames'][f])).all() and np.isfinite(w).all() and (w>=0).all()
            np.testing.assert_allclose(w.sum(),1,atol=1e-12)
            assert row not in c['train'][f][ix]
            assert level in ['tik','region','global']
    np.testing.assert_allclose(weight,1,atol=1e-12)
    return s

def qualify():
    dest=OUT/'qualification';dest.mkdir(exist_ok=False);start=time.monotonic();statuses={v:'FAIL' for v in CFG['variants']};ledger=[]
    def timeout(*args):raise TimeoutError('Frozen 3600s qualification deadline')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(CFG['deadline_seconds'])
    fixtures=False
    try:
        verify()
        names=['tests.test_stage3a_real','tests.test_stage3a_sensitivity',
          *['tests.test_stage3a_qualification.QualificationTests.'+n for n in ['test_rank_finite_population_exact','test_comparator_finite_population_exact','test_ties_zero_variance','test_rank_small_sample_full_support']],
          *['tests.test_stage3a_v2.V2Tests.'+n for n in ['test_partial_only_changes_target_probabilities','test_joint_parent_randomization','test_holm','test_projection_composition']]]
        suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in names);buf=io.StringIO()
        result=unittest.TextTestRunner(stream=buf,verbosity=2).run(suite);(dest/'fixtures.txt').write_text(buf.getvalue())
        if not result.wasSuccessful():raise RuntimeError('Binding fixtures FAIL')
        fixtures=True
        for variant in CFG['variants']:
            try:
                c=context(variant);s=design_checks(c);write(dest/f'{variant}_support.json',s)
                for experiment,scenarios in [('complete',CFG['scenarios']),('partial',CFG['partial_scenarios'])]:
                    for scenario in scenarios:
                        t=time.monotonic();out=job(c,variant,scenario,experiment)
                        if scenario=='N1' and experiment=='complete':
                            replay=job(c,variant,scenario,experiment)
                            assert serialized(replay)==serialized(out),'N1 deterministic replay mismatch'
                        path=dest/f'{variant}_{scenario}_{experiment}.json';write(path,out)
                        ledger.append(dict(variant=variant,scenario=scenario,experiment=experiment,status='PASS',LB_targets=len(out['LB']),elapsed_seconds=time.monotonic()-t))
                statuses[variant]='PASS';print(json.dumps(dict(variant=variant,status='PASS',synthetic_datasets=18)),flush=True)
            except Exception as e:
                write(dest/f'{variant}_FAIL.json',dict(error=type(e).__name__+': '+str(e),trace=traceback.format_exc(),retry=False));statuses[variant]='FAIL'
                if isinstance(e,TimeoutError):raise
    except Exception as e:
        write(dest/'STOP.json',dict(error=type(e).__name__+': '+str(e),trace=traceback.format_exc(),retry=False))
    finally:
        signal.alarm(0);pd.DataFrame(ledger).to_csv(dest/'ledger.csv',index=False)
        write(dest/'summary.json',dict(variants=statuses,fixtures_PASS=fixtures,synthetic_datasets=len(ledger),A_comparisons=len(ledger),
          LB_target_comparisons=sum(r['LB_targets'] for r in ledger),sensitivity_response_reads=0,empirical_calibration=False,
          elapsed_seconds=time.monotonic()-start,S3='IDENTITY_WITH_PRIMARY',automatic_real_execution=False))
        write(dest/'manifest.json',dict(files={str(p.relative_to(ROOT)):sha(p) for p in dest.iterdir() if p.is_file()}))
    print(json.dumps(read(dest/'summary.json')))

if __name__=='__main__':qualify()
