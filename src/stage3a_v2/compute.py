"""Logical synthetic tasks. Preflight and evaluation streams never overlap."""
import time
import numpy as np
from .spec import CONFIG,rng
from .design import context
from .generators import generate,equivalence
from .models import LPeer,predictive,subset
from .association import test

def plain(x):
    if isinstance(x,dict):return {k:plain(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [plain(v) for v in x]
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    return x

def tasks():
    for sc in CONFIG['scenarios']:
        for r in range(CONFIG['R']):yield ('L',sc,'prediction',r,0.,1)
    for sc in CONFIG['association_nulls']:
        for exp in ['complete','partial']:
            for r in range(CONFIG['R']):yield ('A',sc,exp,r,0.,1)
    for strength in CONFIG['positive_strengths']:
        for sign in [-1,1]:
            for r in range(CONFIG['R_positive']):yield ('A','N1','positive',r,strength,sign)
    for sc in ['N9','N10']:
        for r in range(CONFIG['R_specificity']):yield ('A',sc,'specificity',r,0.,1)
    yield ('E','N10','equivalence',0,0.,1)

def task_id(t):
    return '__'.join(str(v) for v in t)

def preflight_tasks():
    return ([('L',sc,'prediction',0,0.,1) for sc in CONFIG['scenarios']]
        +[('A',sc,e,0,0.,1) for sc in CONFIG['association_nulls'] for e in ['complete','partial']]
        +[('A','N1','positive',0,s,z) for s in CONFIG['positive_strengths'] for z in [-1,1]]
        +[('A',sc,'specificity',0,0.,1) for sc in ['N9','N10']])

def compute(t,stream):
    wall=time.perf_counter();cpu=time.process_time();c=context();design_time=time.perf_counter()-wall
    family,sc,exp,r,strength,sign=t;d=c['d'];start=time.perf_counter()
    y=generate(d,sc,r,stream=stream+'/'+exp,strength=strength,sign=sign,target=r%10,
               experiment='partial' if exp=='partial' else 'complete')
    gen_time=time.perf_counter()-start;start=time.perf_counter();events=[]
    if family=='L':
        fold=int(rng(stream,'L',sc,r,'selected_fold').integers(0,5));ix=c['train'][fold]
        model=LPeer().fit(c['frames'][fold],subset(y,ix));model._neighbour_cache=c['neighbours'][fold]
        scores={};ok=model.success;error=None
        try:
            for cell in range(8):
                row=int(rng(stream,'L',sc,r,'probe',cell).choice(c['pools'][fold,cell]))
                z=predictive(model,d,y,row,rng(stream,'L',sc,r,'prediction',cell))
                assert np.isfinite(z['log_score_joint']) and np.isfinite(z['pit']).all()
                assert np.all((np.asarray(z['pit'])>=-1e-12)&(np.asarray(z['pit'])<=1+1e-12))
                _,_,level=model.neighbours(d,row)
                z.update(row_index=row,uuid=d.uuid[row],donor_level=level,
                         sampling_probability=1/(5*len(c['pools'][fold,cell])))
                scores[str(cell)]=z
        except (ValueError,RuntimeError,FloatingPointError,AssertionError) as e:
            ok=False;error=type(e).__name__+': '+str(e)
        events.append((f'L/{sc}/fit',int(ok)))
        for cell in range(8):
            for j in range(12):events.append((f'L/{sc}/{cell}/{j}/coverage',int(scores[str(cell)]['coverage'][j]) if ok else 0))
        result=dict(success=ok,error=error,fold=fold,scores=scores,support=int(c['eligible'].sum()))
    elif family=='A':
        result=test(d,y,c['pairs'],[stream,sc,exp,r,strength,sign])
        result.pop('parent_scores',None);ok=result['status']=='IDENTIFIED'
        null=[j for j in range(10) if exp!='partial' or j not in y['partial_targets']]
        result.update(true_null_parties=null,target_party=r%10,partial_targets=y['partial_targets'])
        if exp in ['complete','partial']:
            events=[(f'A/{sc}/{exp}/fit',int(ok)),(f'A/{sc}/{exp}/FWER',int(np.min(result['p_holm'][null])<=.05) if ok else None)]
    elif family=='E':
        e=equivalence(y)
        result=dict(identification=e['identification'],same_observables=bool(np.array_equal(e['observed_a'],e['observed_b'])),
                    different_baselines=bool(not np.array_equal(e['baseline_a'],e['baseline_b'])),
                    mechanism_claim=False,real_quantities=False)
    else:raise ValueError(t)
    science=plain(dict(task_id=task_id(t),task=t,stream=stream,synthetic_only=True,result=result,events=events))
    timing=dict(task_id=task_id(t),family=family,scenario=sc,experiment=exp,design_seconds=design_time,
                generation_seconds=gen_time,procedure_seconds=time.perf_counter()-start,
                wall_seconds=time.perf_counter()-wall,cpu_seconds=time.process_time()-cpu)
    return science,timing
