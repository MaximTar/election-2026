"""Exact sparse ABC basis, independent of storage and without source loaders."""
from fractions import Fraction as F
from collections import Counter
from src.smz import abc,common
from .codec import digest

def sum_exact(values):
    """Balanced reduction avoids repeated huge-denominator left folds."""
    stack=[]
    for value in values:
        value=F(value);i=0
        while i<len(stack) and stack[i] is not None:
            value+=stack[i];stack[i]=None;i+=1
        if i==len(stack):stack.append(value)
        else:stack[i]=value
    return sum((v for v in stack if v is not None),F(0))

def build(rows,design):
    from .engine import guard_rows
    guard_rows(rows)
    lo,hi,cut,ratio,minimum=abc.parameters(design)
    ranks=abc.midranks(rows);refs={}
    for i,r in enumerate(rows):
        if lo<=ranks[r.uuid]<=hi:refs.setdefault(r.tik,[]).append(i)
    statuses=[];donor_ids=[];sets=[];set_ids={};sparse={}
    for i,r in enumerate(rows):
        if ranks[r.uuid]<cut:statuses.append('NOT_SELECTED');donor_ids.append(-1);continue
        candidates=refs.get(r.tik,())
        ds=tuple(k for k in candidates if max(rows[k].n,r.n)*ratio.denominator<=min(rows[k].n,r.n)*ratio.numerator)
        status=abc.donor_status(candidates,tuple(rows[k] for k in ds),minimum)
        if ds not in set_ids:set_ids[ds]=len(sets);sets.append(ds)
        di=set_ids[ds];donor_ids.append(di);statuses.append(status)
        if status!='SUPPORTED':continue
        M=sum(rows[k].valid for k in ds);K=sum(rows[k].n for k in ds);L=sum(rows[k].issued for k in ds)
        P=tuple(sum(rows[k].parties[j] for k in ds) for j in range(10))
        H=r.issued*K;d=r.n*L-H
        assert d<=0,'ABC_DESIGN_INVARIANT_FAILURE'
        U=tuple(r.valid*p-c*M for p,c in zip(P,r.parties))
        assert sum(U)==0 and M>0 and H>0 and -H<d<=0
        sparse[i]=(di,M,K,L,P,H,d,U)
    return dict(design=design,ranks=tuple(ranks[r.uuid] for r in rows),statuses=tuple(statuses),
                donor_ids=tuple(donor_ids),donor_sets=tuple(sets),sparse=sparse)

def coefficients(r,b):
    _,M,K,L,P,H,d,U=b
    return (tuple(F(u,M) for u in U),tuple(F(c*d,H) for c in r.parties),tuple(F(u*d,M*H) for u in U))

def reconstruct(r,status,b,lam,mu):
    from .engine import guard_row
    guard_row(r)
    lam,mu=common.level(lam),common.level(mu)
    aa,bb,xx=coefficients(r,b) if b is not None else ((F(0),)*10,)*3
    scale=1+mu*F(b[6],b[5]) if b is not None else F(1)
    comp=tuple(lam*v for v in aa);inte=tuple(mu*v for v in bb);inter=tuple(lam*mu*v for v in xx)
    delta=tuple(a+b+c for a,b,c in zip(comp,inte,inter));counts=tuple(c+d for c,d in zip(r.parties,delta))
    issued=scale*r.issued;valid=scale*r.valid
    invalid=common.UNKNOWN if r.invalid is None else scale*r.invalid
    remainder=common.UNKNOWN if r.invalid is None else scale*(r.issued-r.valid-r.invalid)
    assert sum(counts)==valid and min(counts)>=0 and 0<valid<=issued<=r.n
    return dict(uuid=r.uuid,status=status,scenario_applied=status=='SUPPORTED',actually_transformed=counts!=r.parties or issued!=r.issued,
        n=r.n,issued=issued,valid=valid,parties=counts,invalid=invalid,remainder=remainder,
        combined_issued_minus_valid=issued-valid,scale=scale,source_parties=r.parties,source_valid=r.valid,
        delta=delta,composition=comp,intensity=inte,interaction=inter)

def aggregate_basis(rows,b):
    supported=tuple(b['sparse']);scopes={'full':tuple(range(len(rows))),'native':supported}
    for region in sorted({r.region for r in rows}):scopes['region:'+region]=tuple(i for i,r in enumerate(rows) if r.region==region)
    # Only supported coefficients are retained for one design; no lambda/mu rows.
    co={i:coefficients(rows[i],v) for i,v in b['sparse'].items()}
    result={}
    for name,indices in scopes.items():
        native=[i for i in indices if i in co]
        source=tuple(sum(rows[i].parties[j] for i in indices) for j in range(10))
        coeff=tuple(tuple(sum_exact(co[i][k][j] for i in native) for j in range(10)) for k in range(3))
        vb=sum_exact(F(rows[i].valid*b['sparse'][i][6],b['sparse'][i][5]) for i in native)
        ib=sum_exact(F(rows[i].issued*b['sparse'][i][6],b['sparse'][i][5]) for i in native)
        assert sum(coeff[0])==sum(coeff[2])==0 and sum(coeff[1])==vb
        result[name]=dict(source=source,coeff=coeff,source_valid=sum(source),source_issued=sum(rows[i].issued for i in indices),valid_basis=vb,issued_basis=ib,
            coverage=common.coverage([rows[i] for i in native],[rows[i] for i in indices]),
            selected=sum(b['statuses'][i]!='NOT_SELECTED' for i in indices),supported=len(native),
            composition_moving=sum(any(b['sparse'][i][7]) for i in native),intensity_moving=sum(b['sparse'][i][6]!=0 for i in native),
            either_moving=sum(any(b['sparse'][i][7]) or b['sparse'][i][6]!=0 for i in native))
    return result

def evaluate(scope,lam,mu):
    lam,mu=common.level(lam),common.level(mu)
    comp=tuple(lam*x for x in scope['coeff'][0]);inte=tuple(mu*x for x in scope['coeff'][1]);inter=tuple(lam*mu*x for x in scope['coeff'][2])
    delta=tuple(a+b+c for a,b,c in zip(comp,inte,inter));counts=tuple(c+d for c,d in zip(scope['source'],delta))
    valid=scope['source_valid']+mu*scope['valid_basis'];issued=scope['source_issued']+mu*scope['issued_basis']
    assert sum(counts)==valid and min(counts,default=0)>=0 and valid<=issued
    return dict(source_parties=scope['source'],source_valid=scope['source_valid'],scenario_parties=counts,scenario_valid=valid,scenario_issued=issued,
        shares=common.shares(counts,valid),source_shares=common.shares(scope['source'],scope['source_valid']),
        delta=delta,composition=comp,intensity=inte,interaction=inter,coverage=scope['coverage'],selected_targets=scope['selected'],supported_targets=scope['supported'],
        actually_transformed_units=(scope['either_moving'] if lam and mu else scope['composition_moving'] if lam else scope['intensity_moving'] if mu else 0))
