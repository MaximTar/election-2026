"""Keep frozen numeric statements; replace only synthetic-only entry guards."""
import ast,inspect,hashlib,json
import numpy as np
from src.stage3a_v2 import association as a
from src.stage3a_v2.models import LPeer,subset
from src.stage3a_qualification import lb
from .spec import CFG,rng

class Stop(RuntimeError):pass

def extracted(fn):
    import textwrap
    tree=ast.parse(textwrap.dedent(inspect.getsource(fn)));node=tree.body[0]
    expected=ast.parse("if not y.get('synthetic', False): raise RuntimeError('x')").body[0]
    assert isinstance(node.body[0],ast.If)
    assert ast.dump(node.body[0].test)==ast.dump(expected.test)
    assert len(node.body[0].body)==1 and isinstance(node.body[0].body[0],ast.Raise)
    assert isinstance(node.body[0].body[0].exc,ast.Call) and node.body[0].body[0].exc.func.id=='RuntimeError'
    node.body=node.body[1:];fingerprint=hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest()
    env=dict(fn.__globals__);exec(compile(ast.fix_missing_locations(tree),'<frozen-numeric-body>','exec'),env)
    return env[node.name],fingerprint

_association,A_BODY_SHA=extracted(a.test)
_fit,L_FIT_BODY_SHA=extracted(LPeer.fit)

def validate(d,y):
    if y.get('origin') not in ['synthetic_preopen','authorized_real_loader']:raise Stop('Unrecognized provenance')
    if y.get('origin')=='authorized_real_loader' and y.get('synthetic') is not False:raise Stop('Real data cannot be synthetic')
    if d.uuid.duplicated().any() or d[['uuid','region','tik_uuid','voters']].isna().any().any():raise Stop('Identity mismatch')
    if d.groupby('tik_uuid').region.nunique().max()!=1:raise Stop('Hierarchy nesting mismatch')
    n=d.voters.to_numpy();I=np.asarray(y['issued']);V=np.asarray(y['valid']);C=np.asarray(y['votes'])
    if I.shape!=(len(d),) or V.shape!=I.shape or C.shape!=(len(d),10):raise Stop('Count shape')
    for v in [n,I,V,C]:
        if not np.isfinite(v).all() or not np.equal(v,np.floor(v)).all():raise Stop('Nonfinite/noninteger counts')
    if np.any(n<=0) or np.any(V<=0) or np.any(V>I) or np.any(I>n) or np.any(C<0) or not np.array_equal(C.sum(1),V):raise Stop('Count integrity')

def association(d,y,pairs,key,diagnostic=False):
    validate(d,y)
    if diagnostic and y['origin']!='synthetic_preopen':raise Stop('Real support cannot be bypassed')
    result=_association(d,y,pairs,key,diagnostic)
    if result['status']!='IDENTIFIED':raise Stop(result['status'])
    return result

class Peer(LPeer):
    def fit(self,d,y):
        validate(d,y);result=_fit(self,d,y)
        if not self.success:raise Stop('Insufficient training pool')
        return result

def sample(c,row,namespace=None):
    fold=int(c['fold'][row]);cell=int(c['cell'][row]);pool=c['pools'][fold,cell]
    others=pool[pool!=row]
    if len(others)!=len(pool)-1:raise Stop('Target not exactly once in pool')
    return rng('LB','calibration',fold,cell,str(c['d'].uuid.iloc[row]),namespace=namespace).choice(
        others,size=min(99,len(others)),replace=False)

def fit_fold(c,y,fold):
    ix=c['train'][fold];model=Peer().fit(c['frames'][fold],subset(y,ix))
    model._neighbour_cache=c['neighbours'][fold];return model

def target(c,y,model,row,cal,memo=None):
    memo={} if memo is None else memo;d=c['d'];fold=int(c['fold'][row]);cell=int(c['cell'][row])
    if len(set(map(int,cal)))!=len(cal) or row in cal or not set(map(int,cal))<=set(c['pools'][fold,cell]):raise Stop('Calibration membership')
    def moment(i):
        i=int(i)
        if i not in memo:memo[i]=lb.moments(model,d,y,i)
        mu,sd,_=memo[i]
        if not np.isfinite(mu).all() or not np.isfinite(sd).all():raise Stop('Nonfinite working moments')
        return memo[i]
    def obs(i):return np.r_[y['issued'][i],y['valid'][i],y['votes'][i]]
    def den(i):return np.r_[d.voters.iloc[i],y['issued'][i],np.repeat(y['valid'][i],10)]
    mu,sd,_=moment(row);cv=np.array([lb.scores(obs(i),*moment(i)[:2]) for i in cal])
    # The frozen rank primitive permits m=0 via its k>m full-support branch.
    if len(cal)==0:cv=np.empty((0,12))
    lo,hi,q=lb.rank_interval(mu,sd,cv,den(row))
    counts=np.array([obs(i) for i in cal]).reshape(-1,12);dens=np.array([den(i) for i in cal]).reshape(-1,12)
    cl,ch=lb.comparator(counts,dens,den(row))
    return dict(row=int(row),calibration_rows=np.asarray(cal),observed=obs(row),denominator=den(row),mean=mu,sd=sd,
                interval=lb.metrics(lo,hi,obs(row),den(row)),comparator=lb.metrics(cl,ch,obs(row),den(row)))

def position(lo,hi,y):return 'empty' if lo>hi else ('below' if y<lo else ('above' if y>hi else 'inside'))

def equivalent(x,y):
    if isinstance(x,dict):
        assert set(x)==set(y)
        for k in x:equivalent(x[k],y[k])
    elif isinstance(x,(list,tuple)):
        assert len(x)==len(y)
        for a0,b0 in zip(x,y):equivalent(a0,b0)
    elif isinstance(x,(str,bool)) or x is None:assert x==y
    else:np.testing.assert_allclose(x,y,**CFG['numeric'])

