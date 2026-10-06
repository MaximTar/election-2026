"""Build the prospective artifact package once, before actual timing outcomes."""
import json
import platform
import subprocess
import sys
import numpy as np
import pandas as pd
import scipy
from .spec import ROOT,OUT,UNIVERSE,CONFIG,write_json,digest
from .design import context,association_support
from .gates import registry

def freeze():
    if (OUT/'manifest.json').exists():raise FileExistsError('Already frozen')
    OUT.mkdir(parents=True,exist_ok=True)
    tests=subprocess.run([sys.executable,'-m','unittest','tests.test_stage3a_v2','-v'],cwd=ROOT,text=True,capture_output=True)
    (OUT/'unit_tests.txt').write_text(tests.stdout+tests.stderr)
    if tests.returncode:raise RuntimeError('Unit tests failed; no freeze')
    c=context();d=c['d'];a=association_support(d,c['pairs']);e=c['eligible']
    c['pairs'].to_csv(OUT/'association_pairs.csv',index=False)
    c['membership'].to_csv(OUT/'association_membership.csv',index=False)
    prediction=d.assign(fold=c['fold'],cell=c['cell'],eligible=e,original_tik_n=c['size'])
    prob=np.zeros(len(d))
    for (f,j),ix in c['pools'].items():prob[ix]=1/(5*len(ix))
    prediction['sampling_probability_within_cell']=prob
    prediction.to_csv(OUT/'prediction_membership.csv',index=False)
    cells=[]
    for (f,j),ix in c['pools'].items():cells.append(dict(fold=f,cell=j,heldout_rows=len(ix),voters=int(d.voters.iloc[ix].sum()),probability=1/(5*len(ix))))
    pd.DataFrame(cells).to_csv(OUT/'prediction_cell_support.csv',index=False)
    for j in range(8):assert np.isclose(prob[(c['cell']==j)&e].sum(),1.)
    support=dict(universe=CONFIG['universe'],rows=len(d),regions=int(d.region.nunique()),tiks=int(d.tik_uuid.nunique()),
        voters=int(d.voters.sum()),A=a,
        L=dict(rows=int(e.sum()),excluded_rows=int((~e).sum()),regions=int(d.loc[e,'region'].nunique()),
               tiks=int(d.loc[e,'tik_uuid'].nunique()),voters=int(d.loc[e,'voters'].sum()),excluded_voters=int(d.loc[~e,'voters'].sum()),
               exclusion='original official TIK N=1; no collateral regional exclusions'))
    assert support['rows']==support['L']['rows']+support['L']['excluded_rows']
    write_json(OUT/'support.json',support);write_json(OUT/'config.json',CONFIG)
    registry().to_csv(OUT/'binding_gates.csv',index=False)
    write_json(OUT/'software.json',dict(python=sys.version,platform=platform.platform(),numpy=np.__version__,scipy=scipy.__version__,pandas=pd.__version__,threads=1,git_commit=None))
    (OUT/'overnight_command.txt').write_text('OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python3 -m src.stage3a_v2.execution calibrate --run-id 20260927_v2_clean_01 --workers 8 --authorized-full-calibration\n')
    # Design-only dependencies inherited from v1 are frozen explicitly. H is not a callable v2 candidate.
    files=sorted(p for p in OUT.rglob('*') if p.is_file())
    files+=sorted(p for p in (ROOT/'src/stage3a_v2').glob('*.py'))
    files+=[ROOT/'tests/test_stage3a_v2.py',ROOT/'docs/STAGE_3A_V2_FROZEN_PLAN.md',ROOT/'src/stage3a/spec.py',ROOT/'src/stage3a/design.py',ROOT/'src/stage3a/__init__.py',ROOT/'src/analysis/descriptive_env.py']
    u=json.loads((UNIVERSE/'universe_freeze.json').read_text())
    inputs={**u['files'],**u['sources'],str((UNIVERSE/'universe_freeze.json').relative_to(ROOT)):digest(UNIVERSE/'universe_freeze.json')}
    write_json(OUT/'manifest.json',dict(status='FROZEN_CALIBRATION_NOT_RUN',files={str(p.relative_to(ROOT)):digest(p) for p in files},inputs=inputs,
        plan_sha256=digest(ROOT/'docs/STAGE_3A_V2_FROZEN_PLAN.md'),config_sha256=digest(OUT/'config.json'),
        scientific_results_inspected=False,real_outcomes_for_model_selection=False))
    print(json.dumps(support,ensure_ascii=False));print('PLAN',digest(ROOT/'docs/STAGE_3A_V2_FROZEN_PLAN.md'))

if __name__=='__main__':freeze()
