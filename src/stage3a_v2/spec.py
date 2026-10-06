"""Prospective v2 constants. Distinct from immutable v1; no real-response loader."""
import hashlib
import json
import os
for _k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:
    os.environ[_k]='1'
import numpy as np
from src.stage3a.spec import ROOT,digest,write_json

OUT=ROOT/'outputs/stage3a_v2/freeze'
UNIVERSE=ROOT/'outputs/stage3a_v2/universe_20260927'
CONFIG={
 'version':'stage3a-v2-20260927', 'seed_namespace':'stage3a-v2-independent-20260927-final-design',
 'universe':'paper_primary__evidence_20260927', 'folds':5,
 'scenarios':[f'N{i}' for i in range(1,11)], 'association_nulls':[f'N{i}' for i in range(1,9)],
 'L':{'min_pool':8,'k':32,'min_bandwidth':float(np.log(1.10)),'pseudocount':.5},
 'association':{'min_tiks':40,'min_regions':20,'min_rows':2000,'min_fraction':.02,
                'B':1999,'alpha':.05,'projection_draws':1,'primary_correction':'Holm'},
 'R':2500,'predictive_draws':1999,'partial_loading':1.,
 'positive_strengths':[.10,.30,.60],'positive_signs':[-1,1],'R_positive':200,'R_specificity':200,
 'gate':{'delta_each_task':.025,'success_floor':.99,'coverage_floor':.92,'FWER_ceiling':.075,
         'nominal_coverage':.95,'required_predictive_cells':8,'responses':12,
         'numeric_atol':1e-12,'numeric_rtol':1e-10,'sequential_extension':False},
 'preflight':{'workers':8,'parallel_replays':2,'stream':'timing-preflight-never-calibration',
              'max_wall_seconds':1800,'target_hours':8.,'maximum_hours':10.,
              'headroom':1.5,'audit_allowance_seconds':900,
              'protocol':'34 fixed tasks, serial once and two fresh 8-worker pools; replay science identical; cache initialization included'},
 'real_execution':False,'H_binding':False,'counterfactual':'NOT_IDENTIFIED',
 'party_order':['rodina','er','kprf','pensioners','new_people','direct_democracy','greens','communists_russia','ldpr','sr'],
 'sensitivity_policy':'No automatic real execution; re-pair changed designs; transport proof or separately budgeted calibration before inferential sensitivity',
}

def seed(*parts):
    payload=json.dumps([CONFIG['seed_namespace'],*parts],ensure_ascii=False,separators=(',',':'))
    return int.from_bytes(hashlib.sha256(payload.encode()).digest()[:16],'big')

def rng(*parts):return np.random.Generator(np.random.PCG64(seed(*parts)))

def frozen():
    m=json.loads((OUT/'manifest.json').read_text())
    for category in ['files','inputs']:
        for p,h in m[category].items():assert digest(ROOT/p)==h,p
    assert json.loads((OUT/'config.json').read_text())==CONFIG
    return digest(OUT/'manifest.json')
