"""One-use supplement transaction; stdout contains only operational metadata."""
import collections
import datetime
import json
import os
import resource
import time
from pathlib import Path
from src.smz_external_clite.common import canonical, ResourceStop
from src.smz_external_real.coordinator import compact
from . import preflight as p, transport, loader, source, arithmetic


def put(path,value,wire=False):
    data=(canonical(value) if wire else json.dumps(value,sort_keys=True,indent=2,allow_nan=False).encode())+b'\n'
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o400)
    with os.fdopen(fd,'wb') as f:
        f.write(data);f.flush();os.fsync(f.fileno())


def artifact_bytes():
    return sum(f.stat().st_size for f in p.RUN.iterdir() if f.is_file())


def run():
    start=time.monotonic();started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    auth,states,environment=p.check_authorization()
    p.RUN.mkdir(parents=True,mode=0o700,exist_ok=False)
    commitment=p.read(p.AUTH/'execution_commitment_template.json')
    assert commitment['authorization_sha256']==p.sha(p.AUTH/'authorization.json')
    put(p.RUN/'execution_commitment.json',commitment)
    assert p.read(p.RUN/'execution_commitment.json')==commitment
    assert len(commitment['state_ids'])==83
    put(p.RUN/'authorization_consumed.json',{'run_id':auth['run_id'],
        'authorization_sha256':p.sha(p.AUTH/'authorization.json'),
        'commitment_sha256':p.sha(p.RUN/'execution_commitment.json'),
        'consumed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'state':'CONSUMED','reveal_authorized':False})
    context={'run_id':auth['run_id'],'created_at':started,
             'commitment_sha256':p.sha(p.RUN/'execution_commitment.json'),'access_log':[]}
    ledger=[];failure=None
    try:
        resource.setrlimit(resource.RLIMIT_AS,(10*1024**3,10*1024**3))
        transport.activate(context)
        frame=source.load_primary()
        modules={'ISTORIES':loader.load('istories'),'CEDAR':loader.load('cedar')}
        h=arithmetic.cedar_histogram(modules['CEDAR'],frame)
        assert len(frame.rows)==87736 and h['eligible_count']==71438
        for index,state in enumerate(states):
            result=arithmetic.execute(state,frame,modules,h)
            if result['status'].startswith('FAIL'):
                raise RuntimeError('SOURCE_INTEGRITY_ABORT')
            permitted=commitment['terminal_statuses'][state['family']]
            assert result['status'] in permitted,'UNFROZEN_TERMINAL_STATUS'
            arithmetic.reconcile(state,frame,result,h)
            name=f'state_{index:03d}.json'
            packet={'run_id':auth['run_id'],'state':state,'contract_sha256':commitment['contracts'][state['family']],
                    'source':'primary','source_profile_sha256':commitment['source_profile_sha256'],
                    'eligible_view_id':f'EXTERNAL_C_LITE_V1__primary__{state["family"]}__ELIGIBLE',
                    'result':compact(result)}
            put(p.RUN/name,packet,wire=True)
            ledger.append({'state_id':state['state_id'],'family':state['family'],
                           'terminal':result['status'],'artifact':name,'sha256':p.sha(p.RUN/name)})
            del result,packet
            if artifact_bytes()>250*1024**2:
                raise ResourceStop('ARTIFACT_CAP')
        assert [r['state_id'] for r in ledger]==commitment['state_ids']
        assert len(ledger)==83 and transport.COUNTERS['real_model_fits']==0
    except (Exception,MemoryError) as error:
        failure={'category':'RESOURCE' if isinstance(error,(MemoryError,ResourceStop)) else 'ENGINEERING_SOURCE_ENVIRONMENT',
                 'exception_type':type(error).__name__,'message':str(error)}
    terminal={r['state_id']:r for r in ledger}
    complete=[terminal.get(s['state_id'],{'state_id':s['state_id'],'family':s['family'],
               'terminal':'FAIL_NOT_EXECUTED_AFTER_ABORT','artifact':None,'sha256':None}) for s in states]
    runtime={'started_at':started,'finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'wall_seconds':time.monotonic()-start,'peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
             'optimizer_fits':transport.COUNTERS['real_model_fits'],'source_rows_loaded':transport.COUNTERS['real_party_rows'],
             'state_count':len(complete),'status_counts':dict(collections.Counter(r['terminal'] for r in complete)),
             'reveal_authorized':False}
    put(p.RUN/'terminal_ledger.json',{'states':complete,'access':context['access_log'],
        'counters':transport.COUNTERS,'failure':failure,'environment':environment,'reveal_authorized':False})
    put(p.RUN/'resource_usage.json',runtime)
    status='ABORTED_AFTER_AUTHORIZATION_CONSUMPTION' if failure else 'COMMITTED_NOT_REVEALED'
    manifestname='aborted_manifest.json' if failure else 'immutable_manifest.json'
    put(p.RUN/manifestname,{'run_id':auth['run_id'],'state':status,'states':83,
        'files':{f.name:p.sha(f) for f in p.RUN.iterdir() if f.is_file()},
        'authorization_sha256':p.sha(p.AUTH/'authorization.json'),
        'commitment_sha256':p.sha(p.RUN/'execution_commitment.json'),'reveal_authorization':False})
    recordname='abort_commit_record.json' if failure else 'commit_record.json'
    put(p.RUN/recordname,{'state':status,'manifest_sha256':p.sha(p.RUN/manifestname)})
    # Technical totals only; never print packet content/model values.
    print(json.dumps({'status':status,'states':83,'manifest_sha256':p.sha(p.RUN/manifestname),
        'runtime_seconds':runtime['wall_seconds'],'peak_RSS_bytes':runtime['peak_RSS_bytes'],
        'artifact_bytes':artifact_bytes(),'status_counts':runtime['status_counts'],
        'failure':failure,'reveal_authorized':False},sort_keys=True),flush=True)


if __name__=='__main__':run()
