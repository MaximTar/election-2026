"""Generated mock input, 1620-cell transactions, crash/corruption and authorization tests."""
import copy,csv,io,json,gzip,time,resource,tempfile,sys,shutil
from pathlib import Path
from unittest.mock import patch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from src.smz_real_adapter import adapter as a
from src.smz_real_adapter.qualification import mock_fixture,csv_bytes
from src.smz_real_adapter.plans import compile_plan as source_plan
from src.smz import abc,d,common
from .core import *
from .coordinator import Coordinator,Watchdog,Budget,LIMITS
from .storage import Store,durable
from .authorization import verify_signed_authorization,REAL_TRUST
OUT=ROOT/'outputs/smz_sealed_coordinator/20260929_attempt02/qualification02'

def fixture():
    original,pb,meta=mock_fixture();p=json.loads(pb)
    header=next(iter(p['source_files'].values()))['header']
    base=[]
    for i in range(86):
        issued=200+25*i if i<24 else 200 if i<26 else 200+20*(i-26) if i<46 else 200+20*(i-46) if i<66 else 200+5*(i-66) if i<84 else 800
        valid=issued-20
        focal=valid//4 if i%3==0 else 3*valid//4
        if 26<=i<46:focal=valid # degenerate reference
        if 46<=i<66:focal=valid//2 # exact proportional zero-adjustment
        if i>=66:focal=9*valid//10 if i<84 else valid//10 # electorate ceiling
        others=valid-focal;counts=[];non=0
        for j in range(10):
            if j==1:counts.append(focal)
            else:counts.append(others//9+(non<others%9));non+=1
        r={k:'' for k in header};r.update(uuid=f'mock:u{i:02}',voters='1000',issued=str(issued),valid=str(valid),invalid='5' if i%2==0 else '')
        r.update({k:str(v) for k,v in zip(a.COLUMNS,counts)});base.append(r)
    variants={'primary':copy.deepcopy(base),'S1':copy.deepcopy(base[2:]),'S2a':copy.deepcopy(base),'S2b':copy.deepcopy(base)}
    # Full vectors, not party-only patches; still entirely analytic mock quantities.
    for variant,factor,n in [('S2a',2,2000),('S2b',1,1100)]:
        r=variants[variant][0];r['voters']=str(n)
        for k in ['issued','valid',*a.COLUMNS]:r[k]=str(int(r[k])*factor)
        r['invalid']=str(5*factor)
    files={};metadata={};p['source_files']={};p['variants']={};p['metadata_files']={}
    for variant,rows in variants.items():
        name=f'mock://{variant}.csv.gz';blob=gzip.compress(csv_bytes(header,rows),mtime=0);files[name]=blob
        p['source_files'][name]=dict(sha256=sha(blob),header=header,compression='gzip')
        mapping=[];design=[]
        for r in rows:
            i=int(r['uuid'].split('u')[-1]);group=0 if i<24 else 1 if i<26 else 2 if i<46 else 3 if i<66 else 4
            mapping.append(dict(uuid=r['uuid'],source_file=name,source_sha256=sha(blob),selector_commitment=sha(json.dumps([sha(blob),r['uuid'],a.COUNTS],ensure_ascii=False,separators=(',',':')).encode())))
            design.append(dict(uuid=r['uuid'],region=f'mock:r{group}',tik_uuid=f'mock:t{group}',voters=int(r['voters'])))
        mp=f'mock://{variant}_mapping.csv';dp=f'mock://{variant}_design.csv'
        for path,rr in [(mp,mapping),(dp,design)]:metadata[path]=csv_bytes(list(rr[0]),rr);p['metadata_files'][path]=sha(metadata[path])
        p['variants'][variant]=dict(mapping_path=mp,mapping_sha256=sha(metadata[mp]),mapping_source_column='source_file',design_path=dp,design_sha256=sha(metadata[dp]),expected_rows=len(rows),universe='MOCK_ONLY_'+variant)
    pb=a.canonical(p).encode();plans={v:source_plan(pb,v,metadata.__getitem__,expected_profile_sha256=sha(pb)) for v in a.VARIANTS}
    manifest=a.canonical(dict(origin='SMZ_GENERATED_MOCK_SOURCE_V1',plans=plans)).encode()
    return a.MockBundle(manifest,tuple(sorted(files.items()))),pb,metadata

def run():
    started=time.monotonic();OUT.mkdir(parents=True,exist_ok=False);checks=[];accesses=[]
    (OUT/'started.json').write_bytes(enc({'preflight':'../preflight/result.json','qualification':'FRESH_NO_PRIOR_RESULTS','started_ns':time.time_ns()}))
    def audit(event,args):
        if event=='open' and isinstance(args[0],(str,bytes)):
            p=Path(args[0]).absolute()
            if p.is_relative_to(ROOT/'data'):raise AssertionError('ACTUAL_DATA_OPEN_FORBIDDEN')
            if p.is_relative_to(ROOT):accesses.append(str(p.relative_to(ROOT)))
    sys.addaudithook(audit)
    need(not REAL_TRUST.exists(),'REAL_AUTHORITY_ALREADY_PRESENT_UNEXPECTED')
    bundle,pb,metadata=fixture();small,_,_=mock_fixture()
    ff=OUT/'fixtures';ff.mkdir()
    (ff/'bundle_manifest.json').write_bytes(bundle.manifest_bytes);(ff/'profile.json').write_bytes(pb)
    for name,b in bundle.files+tuple(metadata.items()):(ff/name.split('/')[-1]).write_bytes(b)
    work=Path(tempfile.mkdtemp(prefix='smz-sealed02-mock-'));(OUT/'work_store.txt').write_text(str(work));c=Coordinator(work);plan=compile_plan()
    (OUT/'execution_plan.json').write_bytes(enc(plan))
    def record():
        (OUT/'checks_progress.json').write_text(json.dumps(checks,indent=2))
    def ok(name,fn):
        try:
            fn();checks.append(dict(id=name,kind='positive',status='PASS'));record();print('PASS '+name,flush=True)
        except Exception as e:checks.append(dict(id=name,kind='positive',status='FAIL',error=repr(e)));record();raise
    def no(name,fn):
        try:fn()
        except (SealError,a.AdapterError,common.SMZError,FileNotFoundError,KeyError,ValueError) as e:checks.append(dict(id=name,kind='negative',status='PASS',rejection=type(e).__name__));record();print('PASS rejection '+name,flush=True);return
        checks.append(dict(id=name,kind='negative',status='FAIL'));record();raise AssertionError('not rejected: '+name)
    def launch(run,b=bundle,**kw):return c.run_mock(b,expected_bundle_sha256=sha(b.manifest_bytes),run_id=run,**kw)
    no('real_authorization_not_issued',lambda:c.run_closed_real(run_id='forbidden',authorization=True))
    no('ordinary_adapter_real_load',lambda:a.load_real('primary',authorization=True))
    no('precommit_reveal',lambda:c.store.authorize_reveal('absent'))
    ok('wire_equivalence',lambda:need(enc({'r':F(1,3),'m':common.NOT_DEFINED,'x':[1,True,'z',None]})==common.canonical({'r':F(1,3),'m':common.NOT_DEFINED,'x':[1,True,'z',None]}).encode(),'WIRE_EQUIVALENCE'))
    ok('clean_full_1620_run',lambda:need(launch('complete')['status']=='COMMITTED','COMMIT'))
    token=c.store.authorize_reveal('complete');results=c.store.read('complete',token)
    ok('full_terminal_ledger',lambda:need(len(results)==1620 and sum(x['cell_id'].startswith('ABC:') for x in results)==1600 and sum(x['cell_id'].startswith('D:') for x in results)==20,'CELLS'))
    ok('reveal_after_commit',lambda:need(token['payload']['purpose']=='REVEAL_COMMITTED_RESULTS','TOKEN'))
    ok('canonical_result_order',lambda:need([x['cell_id'] for x in results]==sorted(x['cell_id'] for x in results),'ORDER'))
    ok('aliases_are_views_only',lambda:need(sum('A' in x.get('aliases',[]) for x in plan['cells'])==320 and sum('B' in x.get('aliases',[]) for x in plan['cells'])==320,'ALIASES'))
    ok('all_runtime_reconciliation',lambda:need(all(x['reconciliation']=='PASS' for x in results),'RECONCILIATION'))
    dr=[x['result'] for x in results if x['cell_id'].startswith('D:')]
    ok('D_positive_and_negative_residuals',lambda:need(any(s['positive_residual_sum'].get('numerator',0)>0 for r in dr for s in r['strata'].values()) and any(s['negative_residual_sum'].get('numerator',0)<0 for r in dr for s in r['strata'].values()),'SIGNED_FIXTURE'))
    ok('D_unsupported_states_exercised',lambda:need(any(s['status']=='NO_TARGET_SUPPORT' for r in dr for s in r['strata'].values()) and any(s['status']=='DEGENERATE_REFERENCE' for r in dr for s in r['strata'].values()),'D_FIXTURE'))
    ok('D_electorate_failure',lambda:need(any(s['status']=='UNDEFINED_SCENARIO_TOTAL' for r in dr for s in r['strata'].values()),'CEILING_FIXTURE'))
    ok('D_zero_adjustment',lambda:need(any(s['status']=='APPLICABLE' and s['signed_stratum_residual']['numerator']==0 for r in dr for s in r['strata'].values()),'ZERO_FIXTURE'))
    ok('source_variants_preserved',lambda:need(set(json.loads((work/'committed/complete/source_provenance.json').read_bytes()))==set(a.VARIANTS),'SOURCES'))
    ok('deterministic_reverse_worker_order_run',lambda:need(launch('replay',_reverse=True)['status']=='COMMITTED','REPLAY'))
    replay=c.store.read('replay',c.store.authorize_reveal('replay'))
    ok('equivalent_results_modulo_run_crypto_resources',lambda:need(enc(results)==enc(replay),'DETERMINISM'))
    no('token_reused_other_run',lambda:c.store.read('replay',token))
    no('manual_reveal_flag',lambda:c.store.read('complete',{'revealed':True}))
    no('arbitrary_directory_reader',lambda:c.store.read(str(work/'committed/complete'),token))
    no('rerun_existing_ID',lambda:launch('complete'))
    ledger=json.loads((work/'committed/complete/terminal_ledger.json').read_bytes())
    no('missing_cell',lambda:reconcile_ledger(plan,ledger[:-1]))
    no('duplicate_cell',lambda:reconcile_ledger(plan,ledger[:-1]+[ledger[0]]))
    no('extra_cell',lambda:reconcile_ledger(plan,ledger+[dict(ledger[0],cell_id='extra')]))
    no('unknown_cell',lambda:reconcile_ledger(plan,ledger[:-1]+[dict(ledger[-1],cell_id='unknown')]))
    no('nonterminal_cell',lambda:reconcile_ledger(plan,[dict(ledger[0],terminal='RUNNING')]+ledger[1:]))
    for name,fn in [('unknown_design',lambda p:p['cells'][0].update(spec='deferred')),('unknown_source',lambda p:p['cells'][0].update(source='other')),('S3_cell',lambda p:p['cells'][0].update(source='S3')),('plan_parameter_mutation',lambda p:p['cells'][0].update(lambda_quarters=7))]:
        bad=copy.deepcopy(plan);fn(bad);no(name,lambda p=bad:verify_plan(p))
    frame=a.qualify_mock(bundle,'primary',expected_manifest_sha256=sha(bundle.manifest_bytes),run_id='mock:guard',created_at='2026-09-29T00:00:00Z')
    no('direct_kernel_RealPartyFrame',lambda:abc.build(frame,'R1-T1-D1-M2'))
    no('direct_D_RealPartyFrame',lambda:d.execute(frame,'D0'))
    no('unqualified_frame',lambda:a.RealPartyFrame())
    no('coordinator_kernel_without_capability',lambda:KernelSession({'primary':frame},True))
    def altered_frame():
        f=a.qualify_mock(bundle,'primary',expected_manifest_sha256=sha(bundle.manifest_bytes),run_id='mock:guard',created_at='2026-09-29T00:00:00Z');object.__setattr__(f,'provenance_json','{}');a.verify_frame(f)
    no('wrong_source_provenance',altered_frame)
    badmeta=json.loads(bundle.manifest_bytes);badmeta['plans']['primary']['contract_sha256']='wrong';badbundle=a.MockBundle(a.canonical(badmeta).encode(),bundle.files)
    no('wrong_contract_before_load',lambda:launch('wrongcontract',badbundle))
    no('wrong_bundle_hash',lambda:c.run_mock(bundle,expected_bundle_sha256='wrong',run_id='badbundle'))
    # Isolated signed future-authorization verifier; no actual real authority installed.
    key=Ed25519PrivateKey.generate();ready={'decision':'PRE_RELEASE_REVIEW_PASS','contract_sha256':a.CONTRACT,'coordinator_code_sha256':bindings()['coordinator_code_sha256'],'adapter_manifest_sha256':ADAPTER_MANIFEST}
    rb=enc(ready);trust={'mode':'mock_sealed_execution','public_key':key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw).hex(),'readiness_sha256':sha(rb)}
    payload=dict(mode='mock_sealed_execution',readiness_sha256=sha(rb),contract_sha256=a.CONTRACT,execution_plan_sha256=sha(enc(plan)),coordinator_code_sha256=bindings()['coordinator_code_sha256'],adapter_manifest_sha256=ADAPTER_MANIFEST,explicit_user_authorization=True,run_id='mock-only',authorization_id='mock-only')
    def signed(p):return dict(payload=p,signature=key.sign(enc(p)).hex())
    ok('signed_authorization_binding_mock_only',lambda:verify_signed_authorization(signed(payload),trust,plan,rb))
    for field in ['contract_sha256','execution_plan_sha256','coordinator_code_sha256','adapter_manifest_sha256','readiness_sha256']:
        bad=dict(payload);bad[field]='wrong';no('authorization_wrong_'+field,lambda b=bad:verify_signed_authorization(signed(b),trust,plan,rb))
    no('authorization_signature_forgery',lambda:verify_signed_authorization({'payload':payload,'signature':'00'},trust,plan,rb))
    # All eight crash points use generated small mock frame and preserve failed evidence.
    crashes=['before_first_cell','mid_ABC','between_ABC_D','before_reconciliation','during_serialization','after_serialization','after_manifest','interrupt_marker']
    for fault in crashes+['failed_reconciliation','plan_mutation','fallback','worker_crash','resource_during_run']:
        name='stop_'+fault
        no('crash_'+fault,lambda n=name,f=fault:launch(n,small,_fault=f))
        no('no_reveal_'+fault,lambda n=name:c.store.authorize_reveal(n))
        path=work/'staging'/name
        fl=json.loads((path/'failure_terminal_ledger.json').read_bytes())
        ok('terminal_failure_accounting_'+fault,lambda ll=fl:need(len(ll)==1620 and len({x['cell_id'] for x in ll})==1620,'FAILURE_CLOSURE'))
    for family in ('ABC','D'):
        w=Watchdog()
        no(family+'_process_ceiling',lambda f=family: w.check_sample(f,0,0,LIMITS[f].processes+1))
        no(family+'_wall_ceiling',lambda f=family:w.check_sample(f,LIMITS[f].wall_seconds+1,0,1))
        no(family+'_RAM_ceiling',lambda f=family:w.check_sample(f,0,LIMITS[f].rss_bytes+1,1))
    limits=dict(LIMITS);limits['ABC']=Budget(1,1,1)
    no('whole_run_resource_STOP',lambda:launch('resource_stop',small,limits=limits))
    no('resource_STOP_no_reveal',lambda:c.store.authorize_reveal('resource_stop'))
    for run in ('resource_stop','wrongcontract','badbundle'):
        ll=json.loads((work/'staging'/run/'failure_terminal_ledger.json').read_bytes())
        ok('preparation_failure_ledger_'+run,lambda rows=ll:need(len(rows)==1620 and all(r['terminal']=='FROZEN_STOP' for r in rows),'PREPARATION_CLOSURE'))
        no('preparation_failure_reuse_'+run,lambda name=run:launch(name,small))
    # Corrupt then restore immutable mock copies. Original package retained unmodified.
    original=work/'committed/complete';corruptions=[]
    changes=[('changed_result',ledger[0]['artifact'],'change'),('corrupt_manifest','manifest.json','change'),('missing_file',ledger[0]['artifact'],'delete'),('extra_result','extra_result.json','extra'),('wrong_plan','execution_plan.json','change'),('wrong_adapter_provenance','source_provenance.json','change'),('wrong_contract','execution_plan.json','change'),('duplicate_ledger','terminal_ledger.json','duplicate'),('missing_ledger_cell','terminal_ledger.json','missing'),('modified_commit','commit.json','change')]
    for label,relative,action in changes:
        target=original/relative;saved=target.read_bytes() if target.exists() else None
        try:
            if action=='delete':target.unlink()
            elif action in ('duplicate','missing'):
                ll=json.loads(saved);ll=ll+[ll[0]] if action=='duplicate' else ll[:-1];target.write_bytes(enc(ll))
            else:target.write_bytes(b'CORRUPTED_OR_EXTRA')
            no('corruption_'+label,lambda:c.store.read('complete',token));corruptions.append(label)
        finally:
            if saved is None:target.unlink()
            else:target.write_bytes(saved)
    ok('restored_mock_commit_verifies',lambda:c.store._verified('complete'))
    # Actual ciphertext does not carry clear substantive fields, even in failed stages.
    encrypted=next((work/'staging/stop_mid_ABC/cells').iterdir()).read_bytes()
    ok('staging_payload_encrypted',lambda:need(b'scenario_parties' not in encrypted and b'scenario_valid' not in encrypted,'PLAINTEXT_LEAK'))
    no('partial_run_reuse',lambda:launch('stop_mid_ABC',small))
    no('partial_commit_marker_not_commit',lambda:c.store.authorize_reveal('stop_interrupt_marker'))
    # Record complete successful encrypted package, public verification key and reveal receipt.
    shutil.copytree(original,OUT/'committed_mock_run')
    (OUT/'mock_reveal_authorization.json').write_bytes(enc(token))
    (OUT/'mock_result_determinism.json').write_bytes(enc({'first_semantic_sha256':sha(enc(results)),'replay_semantic_sha256':sha(enc(replay)),'equal':enc(results)==enc(replay),'non_deterministic_fields':['run_id','resource_timing','random_encryption_nonce','signature/commit bindings to run']}))
    stops=OUT/'stop_evidence';stops.mkdir()
    for path in (work/'staging').iterdir():
        dest=stops/path.name;dest.mkdir()
        for name in ['failure.json','failure_terminal_ledger.json','failure_resources.json','execution_plan.json','commit.json.partial']:
            if (path/name).exists():shutil.copyfile(path/name,dest/name)
    result={'status':'PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL','checks':checks,'positive':sum(x['kind']=='positive' for x in checks),'negative':sum(x['kind']=='negative' for x in checks),'failures':sum(x['status']!='PASS' for x in checks),'canonical_cells':1620,'ABC':1600,'D':20,'REAL_PARTY_ROWS_PROCESSED':0,'REAL_EXECUTION_AUTHORIZATION':'NOT_ISSUED','resources':{'wall_seconds':time.monotonic()-started,'peak_RSS_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'processes':1},'temporary_evidence_store':str(work)}
    (OUT/'qualification.json').write_text(json.dumps(result,indent=2)+'\n')
    (OUT/'file_access_audit.json').write_text(json.dumps({'project_files':sorted(set(accesses)),'real_data_opens':0},indent=2)+'\n')
    (OUT/'fixture_manifest.json').write_bytes(enc({'origin':'ANALYTIC_GENERATED_MOCK_ONLY','rows':{'primary':86,'S1':84,'S2a':86,'S2b':86},'files':{str(p.relative_to(OUT)):sha(p.read_bytes()) for p in ff.iterdir()}}))
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2));need(result['status']=='PASS','QUALIFICATION_FAILURE')
if __name__=='__main__':
    try:run()
    except BaseException as exc:
        OUT.mkdir(parents=True,exist_ok=True)
        (OUT/'interrupted.json').write_text(json.dumps({'status':'FAIL_SUBATTEMPT_PRESERVED','exception':type(exc).__name__,'detail':str(exc),'REAL_PARTY_ROWS_PROCESSED':0},indent=2))
        raise
