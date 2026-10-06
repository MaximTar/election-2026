"""Single coordinator commits; workers never write scientific ledgers."""
import argparse
from concurrent.futures import ProcessPoolExecutor,wait,FIRST_COMPLETED
from collections import defaultdict
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import statistics
import time
from .spec import ROOT,OUT,CONFIG,write_json,frozen,digest
from .compute import compute,tasks,task_id,preflight_tasks
from .gates import aggregate_counts,task_decision

def encoded(obj):return json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()

def atomic(path,obj):
    payload=encoded(obj)
    if path.exists():
        if path.read_bytes()!=payload:raise RuntimeError('Non-idempotent result '+str(path))
        return False
    tmp=path.with_suffix('.tmp');tmp.write_bytes(payload);os.replace(tmp,path);return True

def work(args):return compute(*args)

def bounded_map(items,stream,workers,limit_seconds):
    start=time.monotonic()
    if workers==1:
        for t in items:
            if time.monotonic()-start>limit_seconds:raise TimeoutError('Predeclared wall budget')
            yield compute(t,stream)
        return
    pool=ProcessPoolExecutor(workers,mp_context=mp.get_context('spawn'))
    pending=set();it=iter(items);exhausted=False
    try:
        while pending or not exhausted:
            while not exhausted and len(pending)<2*workers:
                try:t=next(it)
                except StopIteration:exhausted=True;break
                pending.add(pool.submit(work,(t,stream)))
            if not pending:break
            if time.monotonic()-start>limit_seconds:raise TimeoutError('Predeclared wall budget')
            done,pending=wait(pending,timeout=1,return_when=FIRST_COMPLETED)
            for f in done:yield f.result()
    except BaseException:
        for process in pool._processes.values():process.terminate()
        pool.shutdown(wait=True,cancel_futures=True)
        raise
    else:pool.shutdown()

def preflight():
    freeze_hash=frozen();dest=ROOT/'outputs/stage3a_v2/preflight'
    if dest.exists():raise FileExistsError('Preflight immutable; investigate before restart')
    dest.mkdir();schedule=preflight_tasks();write_json(dest/'schedule.json',schedule)
    records=[];reference={};replay=[];phases=[];global_start=time.monotonic()
    for phase,workers in [('serial',1),('parallel1',8),('parallel2',8)]:
        start=time.monotonic();folder=dest/phase;folder.mkdir()
        remaining=CONFIG['preflight']['max_wall_seconds']-(start-global_start)
        for science,timing in bounded_map(schedule,CONFIG['preflight']['stream'],workers,remaining):
            tid=science['task_id'];atomic(folder/(tid+'.json'),science)
            sha=hashlib.sha256(encoded(science)).hexdigest()
            if phase=='serial':reference[tid]=sha
            else:replay.append(dict(phase=phase,task_id=tid,identical=sha==reference[tid]))
            records.append(dict(phase=phase,**timing))
        phases.append(dict(phase=phase,workers=workers,wall_seconds=time.monotonic()-start))
        print(json.dumps(phases[-1]),flush=True)
    assert len(reference)==34 and len(replay)==68 and all(r['identical'] for r in replay)
    # Weighted by actual full task inventory. Per-type timings are never inferred
    # from H/v1; use the slowest measured steady per-task wall across these runs.
    count=defaultdict(int)
    for t in tasks():count[(t[0],t[1],t[2])]+=1
    projection=[];base_seconds=0.
    for key,n in count.items():
        if key[0]=='E':seconds=1.
        else:
            values=[r['generation_seconds']+r['procedure_seconds'] for r in records
                    if (r['family'],r['scenario'],r['experiment'])==key]
            seconds=max(values)
        projection.append(dict(family=key[0],scenario=key[1],experiment=key[2],tasks=n,
                               seconds_per_task=seconds,projected_worker_seconds=n*seconds))
        base_seconds+=n*seconds
    startup=max(r['design_seconds'] for r in records)*8
    # Actual JSON commit/IPC/process overhead from complete measured pool phases.
    overhead=max(0.,max(p['wall_seconds'] for p in phases if p['workers']==8)
                 -sum(r['generation_seconds']+r['procedure_seconds'] for r in records if r['phase']=='parallel2')/8)
    raw_hours=(base_seconds/8+startup+overhead)/3600
    conservative_hours=(1.5*(base_seconds/8+startup+overhead)+900)/3600
    summary=dict(status='ENGINEERING_PREFLIGHT_ONLY',freeze_sha256=freeze_hash,
        logical_tasks=34,executions=102,scientific_calibration_rows=0,
        replay_comparisons=len(replay),replay_identical=sum(r['identical'] for r in replay),
        full_tasks=sum(count.values()),workers=8,phases=phases,
        projected_raw_hours=raw_hours,projected_headroom_hours=conservative_hours,
        timing_rule='maximum observed per scenario/type steady wall; weighted full inventory /8; startup+IPC; 1.5 headroom plus900s audit',
        SAFE_TO_LAUNCH_FULL_CALIBRATION=conservative_hours<=10,
        real_models=False,full_calibration_started=False,
        target_met=conservative_hours<=8)
    write_json(dest/'timings.json',records);write_json(dest/'replay.json',replay)
    write_json(dest/'runtime_projection.json',projection);write_json(dest/'summary.json',summary)
    write_json(dest/'manifest.json',dict(freeze_sha256=freeze_hash,files={str(p.relative_to(ROOT)):digest(p) for p in sorted(dest.rglob('*')) if p.is_file()}))
    print(json.dumps(summary),flush=True)

def aggregate(run):
    counts=defaultdict(lambda:[0,0,0]);families=defaultdict(int);seen=set();positives=[];challenges=[]
    expected={task_id(t) for t in tasks()}
    for path in sorted((run/'results').glob('*.json')):
        r=json.loads(path.read_text());tid=r['task_id']
        assert tid in expected and tid not in seen and r['stream']=='evaluation-v2'
        seen.add(tid);families[r['task'][0]]+=1
        for gate,value in r['events']:
            c=counts[gate];c[0]+=1;c[1]+=int(value or 0);c[2]+=int(value is None)
        if r['task'][2]=='positive':positives.append(r)
        if r['task'][2] in ['specificity','equivalence']:challenges.append(r)
    table=aggregate_counts(counts);table.to_csv(run/'gate_decisions.csv',index=False)
    decisions={t:task_decision(g.status) for t,g in table.groupby('task')}
    write_json(run/'completion.json',dict(expected=len(expected),complete=len(seen),pending=len(expected-seen),
       tasks_by_family=dict(families),gate_decisions=decisions,real_data_release=False,counterfactual='NOT_IDENTIFIED'))
    write_json(run/'positive_controls.json',positives);write_json(run/'identification_challenges.json',challenges)
    # All predictive diagnostics remain in raw task artifacts; no selection by score.
    write_json(run/'manifest.json',dict(freeze_sha256=digest(OUT/'manifest.json'),
       files={str(p.relative_to(ROOT)):digest(p) for p in sorted(run.rglob('*')) if p.is_file() and p.name!='manifest.json'}))

def calibrate(run_id,workers,confirmation):
    frozen()
    if not confirmation:raise RuntimeError('Explicit separately authorized execution required')
    pre=json.loads((ROOT/'outputs/stage3a_v2/preflight/summary.json').read_text())
    if not pre['SAFE_TO_LAUNCH_FULL_CALIBRATION']:raise RuntimeError('Runtime gate STOP')
    if workers!=8:raise ValueError('Frozen execution/preflight worker count is8')
    if not run_id.replace('_','').replace('-','').isalnum():raise ValueError('Invalid run id')
    run=ROOT/'outputs/stage3a_v2/calibration'/run_id;run.mkdir(parents=True,exist_ok=True)
    (run/'results').mkdir(exist_ok=True)
    lock=run/'coordinator.lock'
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    try:
        metadata=dict(run_id=run_id,freeze_sha256=digest(OUT/'manifest.json'),workers=workers,stream='evaluation-v2')
        atomic(run/'run.json',metadata)
        todo=[]
        for t in tasks():
            p=run/'results'/(task_id(t)+'.json')
            if p.exists():
                r=json.loads(p.read_text());assert r['task_id']==task_id(t) and r['stream']=='evaluation-v2'
            else:todo.append(t)
        for science,timing in bounded_map(todo,'evaluation-v2',workers,10*3600):
            atomic(run/'results'/(science['task_id']+'.json'),science)
            with (run/'completion_ledger.jsonl').open('a') as f:
                f.write(json.dumps(dict(task_id=science['task_id'],sha256=hashlib.sha256(encoded(science)).hexdigest(),timing=timing))+'\n')
    finally:
        os.close(fd);lock.unlink()
        aggregate(run)

if __name__=='__main__':
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='command',required=True)
    s.add_parser('preflight')
    c=s.add_parser('calibrate');c.add_argument('--run-id',required=True);c.add_argument('--workers',type=int,default=8)
    c.add_argument('--authorized-full-calibration',action='store_true')
    a=p.parse_args()
    if a.command=='preflight':preflight()
    else:calibrate(a.run_id,a.workers,a.authorized_full_calibration)
