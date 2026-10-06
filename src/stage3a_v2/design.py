"""Only voters and identities enter model design. Immutable process-local caches."""
from functools import lru_cache
import numpy as np
import pandas as pd
from .spec import CONFIG,UNIVERSE,OUT,seed
from src.stage3a.design import validate,pairs

def folds(d):
    out=np.empty(len(d),int)
    for _,ix in d.groupby('tik_uuid',sort=True).groups.items():
        order=sorted(ix,key=lambda i:(seed('known_tik_fold',d.uuid[i]),d.uuid[i]))
        for j,i in enumerate(order):out[i]=j%5
    return out

def cells(d):
    order=np.lexsort((d.uuid.to_numpy(),d.voters.to_numpy()))
    q=np.empty(len(d),int);q[order]=np.minimum(3,np.arange(len(d))*4//len(d))
    size=d.groupby('tik_uuid').uuid.transform('size').to_numpy()
    return q*2+(size>=10).astype(int),size>=2,size

def association_support(d,p):
    a=CONFIG['association'];v=dict(rows=2*len(p),pairs=len(p),regions=int(p.region.nunique()),
        tiks=int(p.tik_uuid.nunique()),voters=int(2*p.voters.sum()),fraction=2*len(p)/len(d))
    v['supported']=v['rows']>=a['min_rows'] and v['tiks']>=a['min_tiks'] and v['regions']>=a['min_regions'] and v['fraction']>=a['min_fraction']
    v['excluded_rows']=len(d)-v['rows'];return v

@lru_cache(maxsize=1)
def context():
    d=validate(pd.read_csv(UNIVERSE/'design.csv',usecols=['uuid','region','tik_uuid','voters']))
    f=folds(d);c,eligible,size=cells(d);p,m=pairs(d)
    train={k:np.flatnonzero(f!=k) for k in range(5)}
    pools={(k,j):np.flatnonzero((f==k)&(c==j)&eligible) for k in range(5) for j in range(8)}
    if any(len(v)==0 for v in pools.values()):raise ValueError('Empty frozen prediction fold/cell')
    if not association_support(d,p)['supported']:raise ValueError('A support gate failed')
    return dict(d=d,fold=f,cell=c,eligible=eligible,size=size,pairs=p,membership=m,
                train=train,pools=pools,frames={k:d.iloc[v].reset_index(drop=True) for k,v in train.items()},
                neighbours={k:{} for k in range(5)})
