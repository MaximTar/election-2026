"""Executable synthetic evaluation. No real-response loader or real-model command."""
import argparse
import json
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from .spec import CONFIG, OUT, ROOT, rng, frozen, write_json
from .design import actual, toy, folds, pairs, strata, association_support
from .generators import generate, equivalence
from .models import HCount, LPeer, predictive, subset
from .association import test
from .gates import registry, evaluate, overall


def predictive_rep(d,y,family,task,scenario,replicate,stream):
    assignments=folds(d,task); size=d.groupby('tik_uuid').uuid.transform('size').to_numpy()
    eligible=size>=2 if task=='known_tik' else np.ones(len(d),bool)
    groups=strata(d); probes={}
    for name, mask in groups.items():
        pool=np.flatnonzero(mask&eligible)
        if not len(pool):raise ValueError('Empty required prediction stratum: '+name)
        probes[name]=int(rng(stream,scenario,replicate,'probe',task,name).choice(pool))
    scores={};good=True;diagnostics=[]
    for f in range(CONFIG['folds']):
        train=np.flatnonzero(assignments!=f)
        if len(train)<8:raise ValueError('Insufficient training support')
        try:
            model=(HCount() if family=='H_count_ridge' else LPeer()).fit(d.iloc[train].reset_index(drop=True),subset(y,train))
            good=good and model.success;diagnostics.append({'fold':f,'details':model.diagnostics})
            for name,i in probes.items():
                if assignments[i]==f and model.success:
                    result=predictive(model,d,y,i,rng(stream,scenario,replicate,'predict',family,task,name))
                    if not np.isfinite(result['log_score_joint']) or not np.isfinite(result['pit']).all():
                        raise FloatingPointError('Nonfinite prediction')
                    weights=d.voters.to_numpy()[groups[name]&eligible]
                    result['voter_weight']=float(d.voters.iloc[i]/weights.mean())
                    scores[name]=result
        except (ValueError,RuntimeError,FloatingPointError) as error:
            good=False;diagnostics.append({'fold':f,'failure':type(error).__name__+': '+str(error)})
    events=[];prefix=f'{family}/{task}/{scenario}'
    def event(suffix,value):events.append({'gate_id':prefix+'/'+suffix,'replicate':replicate,'value':value})
    event('fit',int(good))
    for st in CONFIG['strata']:
        value=scores.get(st) if good else None
        for j in range(12):
            event(f'{st}/{j}/coverage',int(value['coverage'][j]) if value else 0)
            for u in CONFIG['gate']['pit_points']:
                event(f'{st}/{j}/pit/{u}',int(value['pit'][j]<=u) if value else None)
    return events,{'diagnostics':diagnostics,'probes':probes,'scores':scores,'success':good,
                  'support':int(eligible.sum()),'excluded':int((~eligible).sum())}


def assoc_events(result,scenario,replicate):
    ok=result['status']=='IDENTIFIED';pre=f'A/{scenario}'
    events=[{'gate_id':pre+'/fit','replicate':replicate,'value':int(ok)},
            {'gate_id':pre+'/FWER','replicate':replicate,'value':int(np.min(result['p_holm'])<=.05) if ok else None}]
    for j in range(10):
        for u in CONFIG['association']['null_cdf_points']:
            events.append({'gate_id':pre+f'/{j}/cdf/{u}','replicate':replicate,
                           'value':int(result['p_raw'][j]<=u) if ok else None})
    return events


def serializable(x):
    if isinstance(x,dict):return {k:serializable(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [serializable(v) for v in x]
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    return x


def dry_run():
    d=toy();p,_=pairs(d);results={'mode':'SYNTHETIC_ENGINEERING_ONLY','calibration_status':'NOT_RUN',
                               'toy_rows':len(d),'actual_outcomes_loaded':False,'scenarios':{}}
    for sc in CONFIG['scenarios']:
        y=generate(d,sc,0,stream='dry-run')
        a=test(d,y,p,['dry-run',sc,0],diagnostic=True)
        results['scenarios'][sc]={'protocol_consistency':True,'association_kernel_status':a['status']}
    y=generate(d,'N1',0,stream='dry-run')
    # Complete five-fold prediction runner on a wholly artificial design.
    for family in CONFIG['predictors']:
        for task in CONFIG['prediction_tasks']:
            events,result=predictive_rep(d,y,family,task,'N1',0,'dry-run')
            results[family+'/'+task]={'event_count':len(events),'result':result,'engineering_fit_success':result['success']}
    e=equivalence(y);results['equivalence']={'same_observed':bool(np.array_equal(e['observed_a'],e['observed_b'])),
                 'different_baselines':bool(not np.array_equal(e['baseline_a'],e['baseline_b'])),'status':e['identification']}
    for strength in CONFIG['positive_strengths']:
        for sign in [-1,1]:
            for target in range(10):generate(d,'N1',0,'dry-run-positive',strength,sign,target)
    results['positive_generator_cases']=60
    return serializable(results)


def evaluate_chunk(scenario,replicate,task,family):
    frozen()
    if scenario not in CONFIG['scenarios'] or not 0<=replicate<CONFIG['R_null']:raise ValueError('Unfrozen scenario/replicate')
    d=actual();y=generate(d,scenario,replicate);root=ROOT/'outputs/stage3a/calibration'/scenario/task/family
    dest=root/f'{replicate:05}.json'
    if dest.exists():raise FileExistsError(dest)
    if task=='association':
        if scenario not in CONFIG['association_nulls'] or family!='A_exact_size_categorical_projection':raise ValueError('Not an association null')
        p,_=pairs(d)
        if not association_support(d,p)['supported']:raise ValueError('UNSUPPORTED; STOP')
        result=test(d,y,p,['evaluation',scenario,replicate]);events=assoc_events(result,scenario,replicate)
        result.pop('parent_scores',None)
    else:
        if task not in CONFIG['prediction_tasks'] or family not in CONFIG['predictors']:raise ValueError('Unfrozen task/model')
        events,result=predictive_rep(d,y,family,task,scenario,replicate,'evaluation')
    write_json(dest,serializable({'scenario':scenario,'replicate':replicate,'task':task,'family':family,
                               'synthetic_only':True,'events':events,'result':result,
                               'generated_at_utc':datetime.now(timezone.utc).isoformat(),
                               'freeze_hashes':json.loads((OUT/'manifest.json').read_text())['files']}))


def positive_chunk(strength,sign,replicate):
    frozen()
    if strength not in CONFIG['positive_strengths'] or sign not in [-1,1] or not 0<=replicate<CONFIG['R_positive_per_strength_sign']:
        raise ValueError('Unfrozen positive specification')
    d=actual();p,_=pairs(d);target=replicate%10
    y=generate(d,'N1',replicate,'positive',strength,sign,target)
    result=test(d,y,p,['positive',strength,sign,replicate]);result.pop('parent_scores',None)
    dest=ROOT/'outputs/stage3a/calibration/positive'/f'{strength}_{sign}_{replicate:04}.json'
    if dest.exists():raise FileExistsError(dest)
    write_json(dest,serializable({'strength_loading':strength,'sign':sign,'target':target,'replicate':replicate,'result':result,
               'synthetic_only':True,'generated_at_utc':datetime.now(timezone.utc).isoformat(),
               'freeze_hashes':json.loads((OUT/'manifest.json').read_text())['files']}))


def aggregate():
    frozen();events=[]
    records=[]
    current=json.loads((OUT/'manifest.json').read_text())['files']
    for path in sorted((ROOT/'outputs/stage3a/calibration').glob('N*/*/*/*.json')):
        record=json.loads(path.read_text())
        if record['freeze_hashes']!=current or not record['synthetic_only']:raise ValueError('Calibration provenance mismatch')
        events.extend(record['events']);records.append(record)
    table=evaluate(pd.DataFrame(events,columns=['gate_id','replicate','value']))
    dest=ROOT/'outputs/stage3a/calibration/gate_decisions.csv'
    if dest.exists():raise FileExistsError(dest)
    dest.parent.mkdir(parents=True,exist_ok=True);table.to_csv(dest,index=False)
    summary={f'{f}/{t}':overall(g.status) for (f,t),g in table.groupby(['family','task'])}
    write_json(dest.with_suffix('.json'),{'gates':summary,'real_data_release':'NOT_AUTHORIZED',
                                        'identification':'NOT_IDENTIFIED','positive_results_required_before_release':True})
    # Comparison remains stratified by task/scenario; no overall winner score.
    metrics=[]
    for r in records:
        if r['task']=='association':continue
        for st,v in r['result'].get('scores',{}).items():
            if not r['result']['success']:continue
            for j in range(12):
                error=v['mean'][j]-v['observed'][j]
                metrics.append({'family':r['family'],'task':r['task'],'scenario':r['scenario'],
                                'replicate':r['replicate'],'stratum':st,'response':j,'error':error,
                                'squared_error':error**2,'coverage':v['coverage'][j],'width':v['width'][j],
                                'crps':v['crps_marginals'][j],'joint_log_score':v['log_score_joint'],
                                'voter_weight':v['voter_weight'],'family_gate':summary[r['family']+'/'+('predictive:'+r['task'])]})
    pd.DataFrame(metrics).to_csv(dest.parent/'predictive_metrics.csv',index=False)
    from scipy.stats import beta
    positives=[]
    for path in sorted((dest.parent/'positive').glob('*.json')):
        r=json.loads(path.read_text())
        if r['freeze_hashes']!=current or not r['synthetic_only']:raise ValueError('Positive provenance mismatch')
        positives.append(r)
    power=[]
    for strength in CONFIG['positive_strengths']:
        for sign in CONFIG['positive_signs']:
            rows=[r for r in positives if r['strength_loading']==strength and r['sign']==sign]
            if len(rows)!=1000 or {r['replicate'] for r in rows}!=set(range(1000)):
                power.append({'strength':strength,'sign':sign,'status':'NOT_RUN_INCOMPLETE'});continue
            for label in ['all',*range(10)]:
                part=rows if label=='all' else [r for r in rows if r['target']==label]
                hits=sum(r['result']['status']=='IDENTIFIED' and r['result']['p_holm'][r['target']]<=.05 for r in part)
                identified=sum(r['result']['status']=='IDENTIFIED' for r in part)
                n=len(part)
                power.append({'strength':strength,'sign':sign,'target':label,'status':'COMPLETE','datasets':n,
                              'identified':identified,'rejections':hits,'power':hits/n,
                              'lower_95':0. if hits==0 else float(beta.ppf(.025,hits,n-hits+1)),
                              'upper_95':1. if hits==n else float(beta.ppf(.975,hits+1,n-hits))})
    pd.DataFrame(power).to_csv(dest.parent/'positive_power.csv',index=False)


def main():
    a=argparse.ArgumentParser();sub=a.add_subparsers(dest='cmd',required=True)
    sub.add_parser('dry-run');sub.add_parser('aggregate')
    p=sub.add_parser('calibrate');p.add_argument('--scenario',required=True);p.add_argument('--replicate',type=int,required=True)
    p.add_argument('--task',required=True);p.add_argument('--family',required=True)
    p=sub.add_parser('positive');p.add_argument('--strength',type=float,required=True);p.add_argument('--sign',type=int,required=True);p.add_argument('--replicate',type=int,required=True)
    args=a.parse_args()
    if args.cmd=='dry-run':print(json.dumps(dry_run(),ensure_ascii=False,allow_nan=False))
    elif args.cmd=='aggregate':aggregate()
    elif args.cmd=='positive':positive_chunk(args.strength,args.sign,args.replicate)
    else:evaluate_chunk(args.scenario,args.replicate,args.task,args.family)


if __name__=='__main__':main()
