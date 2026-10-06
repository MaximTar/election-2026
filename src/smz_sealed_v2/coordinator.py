"""One-process fail-closed transaction. No retries, resume, fallback, or real grant issuer."""
import json,time,os,signal,resource,threading
from dataclasses import dataclass
from pathlib import Path
from src.smz_real_adapter import adapter as a
from .core import *
from .authorization import _activate,_revoke,verify_capability,_real_frames
from .storage import Store,durable

@dataclass(frozen=True)
class Budget:
    wall_seconds:int
    rss_bytes:int
    processes:int
LIMITS={'ABC':Budget(14400,16*1024**3,4),'D':Budget(3600,8*1024**3,1)}
class Watchdog:
    """Serial worker is this process. SIGALRM checks even while a cell is computing.

    No worker subprocesses are created. Any child is a forbidden concurrency change.
    RSS includes coordinator/staging buffers; family clocks are cumulative, disjoint.
    """
    def __init__(self,limits=None):
        self.limits=limits or LIMITS
        for k,b in self.limits.items():
            need(k in LIMITS and 0<b.wall_seconds<=LIMITS[k].wall_seconds and 0<b.rss_bytes<=LIMITS[k].rss_bytes and 0<b.processes<=LIMITS[k].processes,'RESOURCE_LIMIT_RELAXATION')
        need(set(self.limits)==set(LIMITS),'RESOURCE_FAMILIES')
        self.elapsed={'ABC':0.,'D':0.};self.peak={'ABC':0,'D':0};self.active=None
    def measure(self):
        fields=dict(line.split(':',1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
        rss=int(fields['VmRSS'].strip().split()[0])*1024
        children=Path(f'/proc/self/task/{os.getpid()}/children').read_text().split()
        return rss,1+len(children)
    def check(self,*args):
        if self.active is None:return
        rss,processes=self.measure();self.peak[self.active]=max(self.peak[self.active],rss)
        b=self.limits[self.active]
        self.check_sample(self.active,self.elapsed[self.active]+time.monotonic()-self.started,rss,processes)
    def check_sample(self,family,wall,rss,processes):
        b=self.limits[family]
        need(processes<=b.processes and processes==1,'RESOURCE_PROCESS_STOP')
        need(wall<=b.wall_seconds,'RESOURCE_WALL_STOP');need(rss<=b.rss_bytes,'RESOURCE_RAM_STOP')
    def enter(self,family):
        need(threading.current_thread() is threading.main_thread(),'WATCHDOG_MAIN_THREAD_REQUIRED')
        need(self.active is None,'RESOURCE_PHASE_OVERLAP')
        self.active=family;self.started=time.monotonic();self.previous=signal.getsignal(signal.SIGALRM)
        signal.signal(signal.SIGALRM,self.check);signal.setitimer(signal.ITIMER_REAL,.1,.1)
        try:self.check()
        except BaseException:self.leave();raise
    def leave(self):
        signal.setitimer(signal.ITIMER_REAL,0)
        if self.active is not None:
            self.elapsed[self.active]+=time.monotonic()-self.started;self.active=None;signal.signal(signal.SIGALRM,self.previous)
    def report(self):return {'phase_wall_nanoseconds':{k:int((v+(time.monotonic()-self.started if self.active==k else 0))*1000000000) for k,v in self.elapsed.items()},'peak_RSS_bytes':self.peak,'CPU_processes':1,'parallel_workers':0,'retry_count':0,'limits':{k:vars(v) for k,v in self.limits.items()}}

class Coordinator:
    def __init__(self,root):self.store=Store(root)
    def _fresh(self,run_id):
        self.store._id(run_id)
        need(not any((self.store.root/k/run_id).exists() for k in ('staging','committed')) and not any((self.store.root/'registry'/f'{run_id}{suffix}').exists() for suffix in ('.json','.failed','.released')),'RUN_ID_IMMUTABLE_FRESH_RETRY_REQUIRED')
    def _preparation_failed(self,run_id,plan,watch):
        # No scenario payload exists; preserve all planned cells as not executed STOP.
        watch.leave();stage=self.store._start(run_id,plan);self.store._fail(run_id)
        ledger=[{'cell_id':c['id'],'terminal':'FROZEN_STOP','reconciliation':'NOT_RUN','reason':'INPUT_OR_AUTHORIZATION_PREPARATION_STOP'} for c in plan['cells']]
        durable(stage/'failure_terminal_ledger.json',enc(ledger))
        durable(stage/'failure.json',enc({'run_id':run_id,'status':'FAILED_NO_REVEAL','failure_category':'PREPARATION_STOP','completed_cells':0,'remaining_cells':1620,'retry_policy':'NEW_RUN_ID_FRESH_EXECUTION_ONLY'}))
        durable(stage/'failure_resources.json',enc(watch.report()))
    def run_mock(self,bundle,*,expected_bundle_sha256,run_id,limits=None,_fault=None,_reverse=False):
        preflight=ROOT/'outputs/smz_sealed_coordinator/20260929_attempt02/preflight/result.json'
        need(sha(preflight.read_bytes())=='934847c594bdebd208b616305d2efbeed7464ee2e462775b9d0cb9191a760b2c' and json.loads(preflight.read_bytes())['status']=='PASS','CLEAN_PREFLIGHT_REQUIRED')
        self._fresh(run_id);plan=compile_plan();watch=Watchdog(limits)
        try:
            need(type(bundle) is a.MockBundle,'MOCK_BUNDLE_REQUIRED');watch.enter('ABC')
            frames={v:a.qualify_mock(bundle,v,expected_manifest_sha256=expected_bundle_sha256,run_id='mock:'+run_id,created_at='2026-09-29T00:00:00Z') for v in a.VARIANTS}
        except BaseException:
            self._preparation_failed(run_id,plan,watch);raise SealError('PREPARATION_STOP_NO_REVEAL') from None
        finally:watch.leave()
        return self._run(run_id,frames,'mock_sealed_execution',sha(bundle.manifest_bytes),limits,_fault,_reverse,watch)
    def run_closed_real(self,*,run_id,authorization):
        plan=compile_plan();verify_plan(plan)
        # Fixed trust + separately signed future PASS readiness and explicit authorization.
        # No trust/key/authorization is created here, even when user passes a truthy value.
        need(self.store.root==(ROOT/'outputs/smz_sealed_runs').resolve(),'REAL_RUN_ROOT_FIXED')
        self._fresh(run_id);watch=Watchdog()
        try:
            watch.enter('ABC');frames,grant=_real_frames(authorization,plan,run_id)
        except BaseException:
            self._preparation_failed(run_id,plan,watch);raise SealError('PREPARATION_STOP_NO_REVEAL') from None
        finally:watch.leave()
        return self._run(run_id,frames,'closed_real_execution',sha(enc(authorization)),None,None,False,watch)
    def _run(self,run_id,frames,mode,authorization_sha,limits,fault,reverse,watch):
        plan=compile_plan();verify_plan(plan);plan_hash=sha(enc(plan))
        provenance={v:a.verify_frame(f) for v,f in frames.items()}
        for v,p in provenance.items():
            need(p['source_variant']==v and p['contract_sha256']==a.CONTRACT,'INPUT_PROVENANCE')
            need(all(plan['bindings']['code_hashes'][k]==h for k,h in p['adapter_code_hashes'].items()),'ADAPTER_HASH')
        cap=_activate(run_id,mode,{v:p['input_frame_sha256'] for v,p in provenance.items()},authorization_sha)
        verify_capability(cap,frames);stage=self.store._start(run_id,plan)
        durable(stage/'authorization_metadata.json',enc({'mode':mode,'authorization_sha256':authorization_sha,'real_authorization_issued':mode=='closed_real_execution'}))
        kernel=KernelSession(frames,cap);ledger=[];position=0;current_cell=None
        def checkpoint(name,probe=False):
            hit=fault==name
            if probe:return hit
            if hit:raise SealError('INJECTED_CRASH_'+name)
            watch.check()
        try:
            checkpoint('before_first_cell')
            for family in ('ABC','D'):
                watch.enter(family)
                cells=[c for c in plan['cells'] if c['family']==family]
                if reverse:cells.reverse()
                for cell in cells:
                    current_cell=cell
                    watch.check();need(cell in plan['cells'],'PLAN_CELL_MUTATION')
                    if fault=='plan_mutation':raise SealError('PLAN_MUTATION')
                    if fault=='fallback':raise SealError('FALLBACK_NOT_IN_FROZEN_PLAN')
                    if fault=='worker_crash':raise SealError('WORKER_CRASH_NO_RETRY')
                    key=(cell['source'],cell['spec'])
                    if family=='ABC' and key not in kernel.designs:
                        obj=kernel.abc['build'](kernel.views[cell['source']],cell['spec']);kernel.designs[key]=obj
                        self.store._write_secret(run_id,f'references/{cell["source"]}_{cell["spec"]}.aes',{'object_id':obj.object_id,'targets':obj.targets})
                    result=kernel.calculate(cell);watch.check()
                    artifact=f'cells/{cell["id"].replace(":","_")}.aes'
                    self.store._write_secret(run_id,artifact,{'cell_id':cell['id'],'result':result,'reconciliation':'PASS'})
                    ledger.append(dict(cell_id=cell['id'],terminal=terminal(result),reconciliation='PASS',artifact=artifact,artifact_sha256=sha((stage/artifact).read_bytes()),result_sha256=sha(enc(result))))
                    position+=1;current_cell=None
                    # Progress deliberately excludes party-specific values or extrema.
                    if position==1:
                        checkpoint('mid_ABC')
                        if fault=='resource_during_run':watch.check_sample('ABC',LIMITS['ABC'].wall_seconds+1,0,1)
                watch.check();watch.leave()
                if family=='ABC':checkpoint('between_ABC_D')
            checkpoint('before_reconciliation')
            verify_capability(cap,frames);verify_plan(plan)
            if fault=='failed_reconciliation':ledger.pop()
            reconciliation=reconcile_ledger(plan,ledger)
            watch.enter('ABC')
            registration=self.store._commit(run_id,plan,ledger,provenance,watch.report,checkpoint)
            watch.check();watch.leave();self.store._finalize(run_id,watch.report());self.store._verified(run_id)
            _revoke(cap)
            return {'run_id':run_id,'status':'COMMITTED','canonical_cells':1620,'commit':registration,'reconciliation':reconciliation}
        except BaseException as exc:
            watch.leave();_revoke(cap);self.store._fail(run_id)
            # Preserve every planned cell, including those that could not be started.
            completed={r['cell_id'] for r in ledger}
            missing=[dict(cell_id=c['id'],terminal='FROZEN_STOP',reconciliation='NOT_RUN',reason='RUN_ABORT_NO_RETRY') for c in plan['cells'] if c['id'] not in completed]
            if current_cell is not None and not str(exc).startswith(('RESOURCE_','INJECTED_CRASH')):
                for row in missing:
                    if row['cell_id']==current_cell['id']:row.update(terminal='IMPLEMENTATION_FAILURE',reason='CELL_FAILED_NO_RETRY')
            failure={'run_id':run_id,'status':'FAILED_NO_REVEAL','failure_category':type(exc).__name__,'completed_cells':len(completed),'remaining_cells':len(missing),'retry_policy':'NEW_RUN_ID_FRESH_EXECUTION_ONLY'}
            # Exception text may contain internal values: never expose it as public log.
            if not stage.exists():stage=self.store.root/'committed'/run_id
            if stage.exists():
                durable(stage/'failure_terminal_ledger.json',enc(sorted(ledger+missing,key=lambda r:r['cell_id'])))
                durable(stage/'failure.json',enc(failure));durable(stage/'failure_resources.json',json.dumps(watch.report(),sort_keys=True).encode())
            raise SealError('RUN_FAILED_NO_REVEAL') from exc
        finally:
            watch.leave();_revoke(cap)
