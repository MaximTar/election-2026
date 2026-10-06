"""Exhaustive gate registry, simultaneous exact binomial bounds, no discretionary PASS."""
import numpy as np
import pandas as pd
from scipy.stats import beta
from .spec import CONFIG


def registry():
    rows=[]
    def add(identifier,task,family,scenario,metric,lo=0.,hi=1.,**extra):
        rows.append(dict(gate_id=identifier,task=task,family=family,scenario=scenario,metric=metric,
                         required_lower=lo,required_upper=hi,R=CONFIG['R_null'],**extra))
    for fam in CONFIG['predictors']:
        for task in CONFIG['prediction_tasks']:
            for sc in CONFIG['scenarios']:
                prefix=f'{fam}/{task}/{sc}'
                add(prefix+'/fit','predictive:'+task,fam,sc,'fit',lo=.99)
                for st in CONFIG['strata']:
                    for j in range(12):
                        base=f'{prefix}/{st}/{j}'
                        add(base+'/coverage','predictive:'+task,fam,sc,'coverage',lo=.92,stratum=st,response=j)
                        for u in CONFIG['gate']['pit_points']:
                            add(base+f'/pit/{u}','predictive:'+task,fam,sc,'pit',
                                lo=max(0.,u-.05),hi=min(1.,u+.05),stratum=st,response=j,u=u)
    for sc in CONFIG['association_nulls']:
        pre=f'A/{sc}'
        add(pre+'/fit','association','A_exact_size_categorical_projection',sc,'fit',lo=.99)
        add(pre+'/FWER','association','A_exact_size_categorical_projection',sc,'FWER',hi=.075)
        for j in range(10):
            for u,limit in zip(CONFIG['association']['null_cdf_points'],CONFIG['association']['null_cdf_upper_limits']):
                add(pre+f'/{j}/cdf/{u}','association','A_exact_size_categorical_projection',sc,'cdf',hi=limit,response=j,u=u)
    return pd.DataFrame(rows)


def bounds(successes, total, missing=0, K=None):
    if K is None: K=len(registry())
    if not (0<=successes<=total-missing and 0<=missing<=total): raise ValueError('Invalid calibration counts')
    delta=CONFIG['gate']['simultaneous_error']/(2*K)
    # Missing outcomes span both possibilities; never silently reduce denominator.
    lo=0. if successes==0 else float(beta.ppf(delta,successes,total-successes+1))
    upper_success=successes+missing
    hi=1. if upper_success==total else float(beta.ppf(1-delta,upper_success+1,total-upper_success))
    return lo,hi


def decide(successes,total,lower=0.,upper=1.,missing=0,K=None):
    lo,hi=bounds(successes,total,missing,K)
    if lo>=lower and hi<=upper: status='PASS'
    elif hi<lower or lo>upper: status='FAIL'
    else: status='INDETERMINATE'
    return {'status':status,'lower_bound':lo,'upper_bound':hi,'successes':successes,
            'total':total,'missing':missing,'required_lower':lower,'required_upper':upper}


def overall(statuses):
    statuses=list(statuses)
    if not statuses:return 'NOT_RUN'
    if 'FAIL' in statuses:return 'FAIL'
    if any(s!='PASS' for s in statuses):return 'INDETERMINATE'
    return 'PASS'


def evaluate(events):
    reg=registry();out=[]
    if events.duplicated(['gate_id','replicate']).any():raise ValueError('Duplicate calibration event')
    if not events.value.dropna().isin([0,1]).all():raise ValueError('Non-Bernoulli gate event')
    unknown=set(events.gate_id)-set(reg.gate_id)
    if unknown:raise ValueError(('Unregistered gates',unknown))
    for g in reg.to_dict('records'):
        data=events.loc[events.gate_id==g['gate_id']]
        if len(data)!=g['R'] or set(data.replicate)!=set(range(g['R'])):
            out.append({**g,'status':'NOT_RUN_INCOMPLETE','evaluated':len(data)});continue
        value=data.value
        result=decide(int(value.fillna(0).sum()),len(value),g['required_lower'],g['required_upper'],int(value.isna().sum()),len(reg))
        out.append({**g,**result})
    return pd.DataFrame(out)
