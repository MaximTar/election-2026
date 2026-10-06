"""Future one-shot execution route. Import and pre-real review do not execute it."""
import csv,datetime,hashlib,json,math,os,resource,signal
from fractions import Fraction as F
from pathlib import Path
from . import preflight,adapter,transport,kernel_loader

ROOT=preflight.ROOT;PACKAGE=preflight.PACKAGE;RUN=preflight.RUN
def put(path,value,mode=0o400):
    # Exact rational/binary64 wire format from qualified common serializer.
    data=transport.canonical(value)+b'\n'
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,mode)
    with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
def plain_put(path,value,mode=0o400):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,mode)
    with os.fdopen(fd,'w') as f:json.dump(value,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
def compact(value):
    import numpy as np
    if isinstance(value,np.ndarray):return compact(value.tolist())
    if isinstance(value,np.generic):return value.item()
    if isinstance(value,dict):return {k:compact(v) for k,v in value.items() if (not isinstance(k,str) or not k.startswith('_')) and k not in
                                     ['rows','postfilter_UUIDs','eligible_UUIDs','histogram_L','histogram_O','member_indices']}
    if isinstance(value,(tuple,list)):return [compact(x) for x in value]
    return value
def cedar_B(module,frame,excluded):
    # Frozen C pure functions; wrapper avoids computing offset states outside grid.
    view=transport.filtered(frame,excluded);rows=[r for r in view.rows if not module.eligible_reason(r)]
    if not rows:return {'status':'NOT_DEFINED_EMPTY_ELIGIBLE'}
    L,O=[0]*100,[0]*100
    for r in rows:
        b=module.bin_index(r.V+r.invalid,r.n);L[b]+=r.L;O[b]+=r.V+r.invalid-r.L
    selected=module.auto_selector(O)
    result=module.single_anchor(L,O,selected['anchor']) if selected['status']=='DEFINED' else dict(selected)
    result.update(selector=selected,eligible_count=len(rows),histogram_L=L,histogram_O=O,
                  geography_status='NO_CHANGE_EMPTY_REGION' if excluded and len(rows)==sum(not module.eligible_reason(r) for r in frame.rows) else 'FILTERED_OR_DEFAULT')
    return result
def execute_state(state,frame,modules,parents):
    family=state['family'];control=json.loads(state['method_control_values']);excluded=state['excluded_region_id'] or None
    if family=='ISTORIES':
        window=tuple(F(x) for x in control.get('window',['1/5','3/10']))
        return modules[family].run(frame,window=window,estimator=control.get('coefficient','ROS'),excluded_region=excluded)
    if family=='CEDAR':
        m=modules[family]
        if 'auto_offset_bins' in control:
            parent=parents[state['parent_state_id']];selected=parent.get('selector',parent)
            if selected['status']!='DEFINED':return dict(selected)
            return m.single_anchor(parent['histogram_L'],parent['histogram_O'],selected['anchor']+control['auto_offset_bins'])
        return cedar_B(m,frame,excluded)
    if family=='NOVAYA_1D':return modules[family].run_frame(frame,h=F(control.get('bin_width','1/100')),excluded_region=excluded)
    if family=='NOVAYA_2D':
        m=modules[family]
        if state['requires_fit']=='false':fitted=parents[state['parent_state_id']]
        else:fitted=m.run_frame(frame,excluded_region=excluded,covariance_type=control.get('covariance','full'))
        output=m.threshold_output(fitted,float(F(control.get('threshold','1/2'))))
        return {**fitted,'threshold_output':output}
    raise RuntimeError('CARD_ONLY_OR_UNKNOWN_FAMILY_NO_ROUTE')
def state_reconcile(state,frame,result,parents,modules):
    # Exact bookkeeping of already-frozen outputs, never an alternative estimator.
    view=transport.filtered(frame,state['excluded_region_id'] or None)
    family=state['family']
    if family=='CEDAR':view_rows=[r for r in view.rows if not modules[family].eligible_reason(r)]
    else:view_rows=view.rows
    result['input_coverage']={'eligible_UIKs':len(view_rows),'voters':sum(r.n for r in view_rows),
                             'valid':sum(r.V for r in view_rows),'excluded_region_id':state['excluded_region_id'] or None}
    if result['status']!='DEFINED':return
    if family=='ISTORIES':
        L=sum(r.L for r in view_rows);O=sum(r.V-r.L for r in view_rows)
        if not (result['L_star']==result['alpha']*O and result['V_star']==result['L_star']+O and
                result['E']==L-result['L_star'] and result['share']==result['L_star']/result['V_star']):
            raise RuntimeError('ISTORIES_ACCOUNTING_MISMATCH')
        party_totals=[sum(r.parties[j] for r in view_rows) for j in range(10)]
        party_totals[1]=result['L_star']
        if sum(party_totals)!=result['V_star']:raise RuntimeError('TEN_PARTY_RECONCILIATION')
        result['scenario_party_totals']=party_totals
    if family=='CEDAR':
        if 'auto_offset_bins' in json.loads(state['method_control_values']):
            parent=parents[state['parent_state_id']];L=sum(parent['histogram_L']);O=sum(parent['histogram_O'])
        else:L=sum(result['histogram_L']);O=sum(result['histogram_O'])
        if result['E']!=L-result['alpha']*O or result['main']!=result['E']/L:raise RuntimeError('CEDAR_ACCOUNTING_MISMATCH')
    if family=='NOVAYA_1D' and not 0<=result['core_center']<=1:raise RuntimeError('CORE_CENTER_DOMAIN')
    if family=='NOVAYA_2D':
        output=result['threshold_output']
        if output['core_center']!=result['core_center'] or output['fit_blob_sha256']!=result['fit_blob_sha256']:
            raise RuntimeError('THRESHOLD_CHANGED_FIT')
        if not 0<=output['membership_count']<=len(view_rows) or not 0<=output['registered_voter_coverage']<=1:
            raise RuntimeError('MEMBERSHIP_COVERAGE_DOMAIN')
        if state['requires_fit']=='false':
            base=parents[state['parent_state_id']]['threshold_output']
            if output['membership_count']>base['membership_count'] or output['registered_voters']>base['registered_voters']:
                raise RuntimeError('THRESHOLD_MEMBERSHIP_NOT_NESTED')
def result_reconcile(ledger,states):
    if [r['state_id'] for r in ledger]!=[s['state_id'] for s in states] or len(ledger)!=362:raise RuntimeError('INCOMPLETE_GRID')
    for row in ledger:
        if not (row['terminal']=='DEFINED' or row['terminal'].startswith('NOT_DEFINED_')):raise RuntimeError('FAILED_RESULT_NOT_REVEALABLE')
        if preflight.sha(RUN/row['artifact'])!=row['sha256']:raise RuntimeError('STATE_ARTIFACT_CHANGED')
def run():
    # No execution is triggered on import. A separate user-authorized task invokes run.
    auth,environment=preflight.check_execution()
    RUN.parent.mkdir(parents=True,exist_ok=True);RUN.mkdir(mode=0o700)
    template=preflight.read(PACKAGE/'execution_commitment_template.json')
    plain_put(RUN/'execution_commitment.json',template)
    ctx={'run_id':auth['run_id'],'run_path':str(RUN),'authorization_sha256':preflight.sha(PACKAGE/'authorization.json'),
         'commitment_sha256':preflight.sha(RUN/'execution_commitment.json'),'committed_before_first_fit':True,
         'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'access_log':[]}
    plain_put(RUN/'authorization_consumed.json',{'run_id':ctx['run_id'],'authorization_sha256':ctx['authorization_sha256'],
              'commitment_sha256':ctx['commitment_sha256'],'consumed_at':ctx['created_at']})
    states=list(csv.DictReader((ROOT/template['state_index']['path']).open()))
    frames={};parents={};ledger=[];failure=None
    try:
        transport.activate(ctx)
        resource.setrlimit(resource.RLIMIT_AS,(10*1024**3,10*1024**3))
        deadline=datetime.datetime.fromisoformat(auth['hard_deadline_UTC'])
        def timeout(signum,frame):raise transport.ResourceStop('E2_HARD_DEADLINE')
        signal.signal(signal.SIGALRM,timeout)
        signal.alarm(max(1,math.ceil((deadline-datetime.datetime.now(datetime.timezone.utc)).total_seconds())))
        modules={f:kernel_loader.load(n) for f,n in [('ISTORIES','istories'),('CEDAR','cedar'),('NOVAYA_1D','gaussian1d'),('NOVAYA_2D','gmm2d')]}
        for state in states:
            preflight.verify_claim(ctx)
            source=state['source']
            if source not in frames:frames[source]=adapter.load(source)
            result=execute_state(state,frames[source],modules,parents)
            state_reconcile(state,frames[source],result,parents,modules)
            if state['state_id'] in template['retained_parent_states']:parents[state['state_id']]=result
            terminal=result['status']
            # Source failures abort the transaction; NOT_DEFINED model diagnostics do not.
            if terminal.startswith('FAIL_'):raise RuntimeError('SOURCE_INTEGRITY_ABORT')
            artifact=f"state_{len(ledger):03d}.json"
            packet={'state_id':state['state_id'],'family':state['family'],'spec':state['family_spec_id'],
                    'output_type':state['expected_output_type'],'source':source,'excluded_region_id':state['excluded_region_id'],
                    'eligible_view_id':f'EXTERNAL_C_LITE_V1__{source}__{state["family"]}__ELIGIBLE',
                    'result':compact(result)}
            put(RUN/artifact,packet)
            ledger.append({'state_id':state['state_id'],'terminal':terminal,'artifact':artifact,'sha256':preflight.sha(RUN/artifact)})
            if sum(p.stat().st_size for p in RUN.iterdir() if p.is_file())>template['resource_stops']['artifact_bytes']:
                raise transport.ResourceStop('ARTIFACT_HARD_STOP')
            # Technical status only; no intermediate fitted/output values printed.
            print(json.dumps({'state_id':state['state_id'],'terminal':terminal,'completed':len(ledger)}),flush=True)
        result_reconcile(ledger,states)
    except (Exception,MemoryError) as error:
        failure={'category':'RESOURCE' if isinstance(error,(transport.ResourceStop,MemoryError)) else 'ENGINEERING_OR_SOURCE',
                 'exception_type':type(error).__name__,'message':str(error)}
    if failure:
        terminal={r['state_id']:r for r in ledger}
        complete=[terminal.get(s['state_id'],{'state_id':s['state_id'],'terminal':'FAIL_NOT_EXECUTED_AFTER_ABORT','artifact':None,'sha256':None}) for s in states]
        plain_put(RUN/'failed_ledger.json',{'status':'FAILED_NO_RESULT_REVEAL','failure':failure,'states':complete,'access':ctx['access_log'],
                                        'counters':transport.COUNTERS,'reveal_authorized':False})
        return {'status':'FAILED_NO_RESULT_REVEAL','real_result_revealed':False}
    plain_put(RUN/'terminal_ledger.json',{'states':ledger,'access':ctx['access_log'],'counters':transport.COUNTERS,
                                       'RSS_peak_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'environment':environment})
    files={p.name:preflight.sha(p) for p in RUN.iterdir() if p.is_file()}
    plain_put(RUN/'immutable_manifest.json',{'run_id':ctx['run_id'],'files':files,'states':362,
               'authorization_sha256':ctx['authorization_sha256'],'commitment_sha256':ctx['commitment_sha256'],
               'state':'COMMITTED_NOT_REVEALED','reveal_authorization':False})
    plain_put(RUN/'commit_record.json',{'manifest_sha256':preflight.sha(RUN/'immutable_manifest.json'),'state':'COMMITTED_NOT_REVEALED'})
    return {'status':'COMMITTED_NOT_REVEALED','states':362,'manifest_sha256':preflight.sha(RUN/'immutable_manifest.json'),
            'real_result_revealed':False}
if __name__=='__main__':print(json.dumps(run()))
