"""Synthetic equivalence only. Does not import or call the actual response loader."""
from src.analysis import descriptive_env
import argparse,json,time,unittest,hashlib
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from src.stage3a_v2.design import context
from src.stage3a_v2.generators import generate
from src.stage3a_v2 import association
from src.stage3a_qualification import lb
from src.stage3a_qualification.spec import verify as verify_old,plain
from .spec import ROOT,OUT,PLAN,UNIVERSE,CFG,sha,write,verify
from . import adapters as ad

def prepare():
    verify_old();d=OUT/'freeze';d.mkdir(parents=True,exist_ok=False)
    c=context();assert (len(c['d']),int(c['eligible'].sum()),len(c['pairs']))==(87736,87729,1796)
    write(d/'config.json',CFG)
    design=c['d'].copy();design['fold']=c['fold'];design['cell']=c['cell'];design['eligible']=c['eligible']
    design['cell_weight']=0.;design['equal_cell_weight']=0.
    for (f,j),ix in c['pools'].items():design.loc[ix,'cell_weight']=1/(5*len(ix));design.loc[ix,'equal_cell_weight']=1/(40*len(ix))
    design.to_csv(d/'reporting_design.csv',index=False)
    write(d/'extracted_kernel_hashes.json',dict(A_numeric_AST=ad.A_BODY_SHA,L_fit_numeric_AST=ad.L_FIT_BODY_SHA,
        change='Removal of first synthetic-only entry guard only; numeric body unchanged'))
    import scipy,sys,matplotlib
    write(d/'software.json',dict(python=sys.version,numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__,matplotlib=matplotlib.__version__))
    # Include immutable evidence, not mutable historical handoff publications.
    files=[PLAN,*sorted((ROOT/'src/stage3a_real').glob('*.py')),ROOT/'tests/test_stage3a_real.py',
       *sorted(d.glob('*')),UNIVERSE/'universe_freeze.json',UNIVERSE/'membership_sources.csv',UNIVERSE/'design.csv',
       ROOT/'src/data/schema.py',ROOT/'src/stage3a_v2/association.py',ROOT/'src/stage3a_v2/models.py',ROOT/'src/stage3a_qualification/lb.py',
       ROOT/'outputs/stage3a_v2/calibration/20260927_v2_clean_01/completion.json',
       ROOT/'outputs/stage3a_v2/calibration/20260927_v2_clean_01/gate_decisions.csv',
       ROOT/'outputs/stage3a_qualification/20260928/future_calibration/20260928_lb_fresh_01/completion.json',
       ROOT/'outputs/stage3a_qualification/20260928/future_calibration/20260928_lb_fresh_01/gates.csv',
       ROOT/'outputs/reports/20260928_lb_fresh_calibration_review.md',
       ROOT/'outputs/stage3a_hc_final_gate/20260928_FE2/summary.json']
    write(d/'manifest.json',dict(created_at=datetime.now(timezone.utc).isoformat(),before_real_responses=True,
        files={str(p.relative_to(ROOT)):sha(p) for p in files}))

def checks():
    verify();dest=OUT/'checks';dest.mkdir(exist_ok=False);start=time.monotonic()
    suite=unittest.defaultTestLoader.loadTestsFromName('tests.test_stage3a_real')
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        write(dest/'summary.json',dict(status='FAIL',tests=result.testsRun,real_response_reads=0));return
    c=context();reports=[]
    for s in range(1,11):
        sc=f'N{s}';fold=(s-1)%5;y=generate(c['d'],sc,0,stream=CFG['preopen_namespace'])
        yy={**y,'origin':'synthetic_preopen','synthetic':False};key=[CFG['preopen_namespace'],'A',sc]
        reference=association.test(c['d'],y,c['pairs'],key)
        actual=ad.association(c['d'],yy,c['pairs'],key);ad.equivalent(reference,actual)
        old=lb.predict(c,y,fold,sc,0,CFG['preopen_namespace']);model=ad.fit_fold(c,yy,fold)
        for cell,z in old.items():
            new=ad.target(c,yy,model,z['row'],np.asarray(z['calibration_rows']))
            for field in ['observed','denominator','mean','sd','interval','comparator']:ad.equivalent(z[field],new[field])
        reports.append(dict(scenario=sc,fold=fold,A='PASS',LB_reference_targets=8,LB='PASS',
                            real_response_reads=0,synthetic_flag_in_adapter=False))
    write(dest/'actual_design_equivalence.json',reports)
    write(dest/'summary.json',dict(status='PASS',unit_tests=result.testsRun,actual_design_synthetic_datasets=10,
        A_complete_result_comparisons=10,LB_target_comparisons=80,real_response_reads=0,
        new_scientific_calibration=False,elapsed_seconds=time.monotonic()-start,
        predictive_pvalues_or_scores_reported=False,numeric=CFG['numeric']))
    write(dest/'manifest.json',dict(files={str(p.relative_to(ROOT)):sha(p) for p in dest.iterdir() if p.is_file()}))
    print(json.dumps(dict(status='PASS',real_response_reads=0,actual_design_synthetic_datasets=10)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','checks']);a=p.parse_args();globals()[a.command]()
