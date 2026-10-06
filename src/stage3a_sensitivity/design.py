"""Same frozen design algorithms, rebuilt for a selected whole universe."""
import numpy as np
import pandas as pd
from src.stage3a.design import validate,pairs
from src.stage3a_v2.design import folds,cells,association_support
from .spec import OUT

def build(d):
    d=validate(d);f=folds(d);cell,eligible,size=cells(d);p,m=pairs(d)
    if not association_support(d,p)['supported']:raise ValueError('A_SUPPORT_UNDEFINED')
    train={k:np.flatnonzero(f!=k) for k in range(5)}
    pools={(k,j):np.flatnonzero((f==k)&(cell==j)&eligible) for k in range(5) for j in range(8)}
    if any(len(x)==0 for x in pools.values()):raise ValueError('EMPTY_FOLD_CELL')
    return dict(d=d,fold=f,cell=cell,eligible=eligible,size=size,pairs=p,membership=m,train=train,pools=pools,
      frames={k:d.iloc[x].reset_index(drop=True) for k,x in train.items()},neighbours={k:{} for k in range(5)})

def context(variant,cache=True):
    c=build(pd.read_csv(OUT/f'designs/{variant}/design.csv'))
    if cache:
        for fold in range(5):
            with np.load(OUT/f'designs/{variant}/neighbours_{fold}.npz') as z:
                targets=z['targets'];indices=z['indices'];weights=z['weights'];lengths=z['lengths'];levels=z['levels']
            c['neighbours'][fold]={int(row):(indices[k,:lengths[k]],weights[k,:lengths[k]],str(levels[k])) for k,row in enumerate(targets)}
    return c

def support(c):
    d=c['d'];e=c['eligible'];a=association_support(d,c['pairs'])
    return dict(rows=len(d),regions=int(d.region.nunique()),tiks=int(d.tik_uuid.nunique()),voters=int(d.voters.sum()),A=a,
      LB=dict(rows=int(e.sum()),regions=int(d.loc[e,'region'].nunique()),tiks=int(d.loc[e,'tik_uuid'].nunique()),
              voters=int(d.loc[e,'voters'].sum()),excluded_rows=int((~e).sum()),excluded_voters=int(d.loc[~e,'voters'].sum())))
