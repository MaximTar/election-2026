"""Task-wise intersection-union clearance. Marginal exact binomial bounds."""
import numpy as np
import pandas as pd
from scipy.stats import beta
from .spec import CONFIG

def registry():
    out=[]
    def add(identifier,task,scenario,metric,lo=0.,hi=1.):
        out.append(dict(gate_id=identifier,task=task,scenario=scenario,metric=metric,lower=lo,upper=hi,R=CONFIG['R']))
    for sc in CONFIG['scenarios']:
        add(f'L/{sc}/fit','P',sc,'fit',lo=.99)
        for c in range(8):
            for j in range(12):add(f'L/{sc}/{c}/{j}/coverage','P',sc,'coverage',lo=.92)
    for sc in CONFIG['association_nulls']:
        for exp in ['complete','partial']:
            add(f'A/{sc}/{exp}/fit','A',sc,'fit',lo=.99)
            add(f'A/{sc}/{exp}/FWER','A',sc,'FWER',hi=.075)
    return pd.DataFrame(out)

def decide(k,n,lo=0.,hi=1.,missing=0):
    if not 0<=k<=n-missing or not 0<=missing<=n:raise ValueError('invalid counts')
    delta=CONFIG['gate']['delta_each_task']
    lower=0. if k==0 else float(beta.ppf(delta,k,n-k+1))
    upper=1. if k+missing==n else float(beta.ppf(1-delta,k+missing+1,n-k-missing))
    status='PASS' if lower>=lo and upper<=hi else ('FAIL' if upper<lo or lower>hi else 'INDETERMINATE')
    return dict(status=status,lower_bound=lower,upper_bound=upper,successes=k,total=n,missing=missing)

def aggregate_counts(counts):
    out=[]
    for g in registry().to_dict('records'):
        n,k,m=counts.get(g['gate_id'],(0,0,0))
        result=decide(k,n,g['lower'],g['upper'],m) if n==g['R'] else dict(status='NOT_RUN_INCOMPLETE',total=n,successes=k,missing=m)
        out.append({**g,**result})
    return pd.DataFrame(out)

def task_decision(values):
    statuses=set(values)
    if 'NOT_RUN_INCOMPLETE' in statuses:return 'NOT_RUN_INCOMPLETE'
    if 'FAIL' in statuses:return 'FAIL'
    return 'PASS' if statuses=={'PASS'} else 'INDETERMINATE'
