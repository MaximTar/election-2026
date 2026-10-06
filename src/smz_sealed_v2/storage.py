"""Encrypted staging; signed atomic commit; manifest-closed, token-gated reader."""
import json,os,secrets,re
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey,Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from .core import enc,sha,need,bindings,verify_plan,reconcile_ledger,SealError

def durable(path,data):
    with path.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
def syncdir(path):
    fd=os.open(path,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)
def files_in(path):
    need(not any(p.is_symlink() for p in path.rglob('*')),'SYMLINK_FORBIDDEN')
    return sorted(p.relative_to(path).as_posix() for p in path.rglob('*') if p.is_file())

class Store:
    """Service-owned root. Public readers accept registered run IDs, never result paths.

    Encryption and signatures enforce API/disk-corruption isolation. Administrator access
    to the private vault/Python internals is outside this application threat model.
    """
    def __init__(self,root):
        self.root=Path(root).resolve();self.root.mkdir(parents=True,exist_ok=True)
        for name in ('staging','committed','vault','registry'):(self.root/name).mkdir(exist_ok=True)
        os.chmod(self.root/'vault',0o700)
        keypath=self.root/'vault/signing.key'
        if not keypath.exists():durable(keypath,Ed25519PrivateKey.generate().private_bytes(serialization.Encoding.Raw,serialization.PrivateFormat.Raw,serialization.NoEncryption()));os.chmod(keypath,0o600)
        self.__key=Ed25519PrivateKey.from_private_bytes(keypath.read_bytes());self.__public=self.__key.public_key()
    def _sign(self,payload):return {'payload':payload,'signature':self.__key.sign(enc(payload)).hex()}
    def _verify_signature(self,envelope):
        try:self.__public.verify(bytes.fromhex(envelope['signature']),enc(envelope['payload']))
        except Exception:raise SealError('SIGNATURE_INVALID')
        return envelope['payload']
    def _id(self,run):need(type(run) is str and re.fullmatch(r'[A-Za-z0-9_-]{1,100}',run),'RUN_ID_NOT_PATH')
    def _start(self,run,plan):
        self._id(run);verify_plan(plan)
        need(not any((self.root/k/run).exists() for k in ('staging','committed')) and not (self.root/'registry'/f'{run}.json').exists(),'RUN_ID_IMMUTABLE_FRESH_RETRY_REQUIRED')
        stage=self.root/'staging'/run;stage.mkdir();(stage/'cells').mkdir();(stage/'references').mkdir()
        key=AESGCM.generate_key(bit_length=256);kp=self.root/'vault'/f'{run}.key';durable(kp,key);os.chmod(kp,0o600)
        durable(stage/'execution_plan.json',enc(plan));syncdir(stage)
        return stage
    def _write_secret(self,run,relative,payload):
        stage=self.root/'staging'/run;target=stage/relative
        need(target.resolve().is_relative_to(stage.resolve()) and relative.endswith('.aes'),'SECRET_PATH')
        nonce=secrets.token_bytes(12);key=(self.root/'vault'/f'{run}.key').read_bytes()
        aad=enc([run,relative]);durable(target,nonce+AESGCM(key).encrypt(nonce,enc(payload),aad))
    def _decrypt(self,path,run,relative):
        blob=(path/relative).read_bytes();key=(self.root/'vault'/f'{run}.key').read_bytes()
        try:return json.loads(AESGCM(key).decrypt(blob[:12],blob[12:],enc([run,relative])))
        except Exception:raise SealError('SEALED_PAYLOAD_CORRUPTION')
    def _commit(self,run,plan,ledger,provenance,resource_report,checkpoint):
        stage=self.root/'staging'/run;verify_plan(plan)
        need((stage/'execution_plan.json').read_bytes()==enc(plan),'PLAN_ON_DISK_CHANGED')
        reconciliation=reconcile_ledger(plan,ledger)
        expected_cells={r['artifact'] for r in ledger}
        need({p.relative_to(stage).as_posix() for p in (stage/'cells').iterdir()}==expected_cells,'RESULT_FILE_CLOSURE')
        for row in ledger:
            need(sha((stage/row['artifact']).read_bytes())==row['artifact_sha256'],'RESULT_HASH')
            payload=self._decrypt(stage,run,row['artifact'])
            need(payload['cell_id']==row['cell_id'] and payload['reconciliation']=='PASS','RESULT_ENVELOPE')
            need(sha(enc(payload['result']))==row['result_sha256'],'RESULT_PAYLOAD_HASH')
        checkpoint('during_serialization')
        for name,obj in [('terminal_ledger.json',sorted(ledger,key=lambda x:x['cell_id'])),('reconciliation.json',reconciliation),('source_provenance.json',provenance),('resources.json',resource_report())]:durable(stage/name,enc(obj))
        checkpoint('after_serialization')
        inventory={p:sha((stage/p).read_bytes()) for p in files_in(stage)}
        manifest=dict(run_id=run,plan_sha256=sha(enc(plan)),bindings=plan['bindings'],source_provenance_sha256=inventory['source_provenance.json'],files=inventory)
        durable(stage/'manifest.json',enc(manifest));checkpoint('after_manifest')
        need(files_in(stage)==sorted(list(inventory)+['manifest.json']),'EXTRA_ARTIFACT')
        for p,h in inventory.items():need(sha((stage/p).read_bytes())==h,'SERIALIZATION_HASH')
        record=self._sign(dict(run_id=run,manifest_sha256=sha(enc(manifest)),execution_plan_sha256=sha(enc(plan)),contract_sha256=plan['bindings']['contract_sha256'],source_provenance_sha256=inventory['source_provenance.json'],status='COMMITTED'))
        # No partial marker ever qualifies. Marker content and full closure are reverified.
        if checkpoint('interrupt_marker',probe=True):
            durable(stage/'commit.json.partial',enc(record)[:17]);raise SealError('CRASH_INTERRUPT_MARKER')
        durable(stage/'commit.json.partial',enc(record));os.replace(stage/'commit.json.partial',stage/'commit.json');syncdir(stage)
        destination=self.root/'committed'/run;os.rename(stage,destination);syncdir(self.root/'committed')
        registration=self._sign(dict(run_id=run,commit_sha256=sha((destination/'commit.json').read_bytes()),manifest_sha256=sha((destination/'manifest.json').read_bytes())))
        durable(self.root/'registry'/f'{run}.json',enc(registration));syncdir(self.root/'registry')
        checkpoint('commit_complete')
        return registration['payload']
    def _finalize(self,run,resources):
        need(not (self.root/'registry'/f'{run}.failed').exists(),'FAILED_RUN')
        reg=json.loads((self.root/'registry'/f'{run}.json').read_bytes())
        durable(self.root/'registry'/f'{run}.released',enc(self._sign({'run_id':run,'registration_sha256':sha(enc(reg)),'status':'RESOURCE_AND_TRANSACTION_COMPLETE','final_resources':resources})))
        syncdir(self.root/'registry')
    def _fail(self,run):
        fp=self.root/'registry'/f'{run}.failed'
        if not fp.exists():durable(fp,enc(self._sign({'run_id':run,'status':'FAILED_NO_REVEAL'})))
    def _verified(self,run):
        self._id(run)
        need(not (self.root/'registry'/f'{run}.failed').exists(),'FAILED_RUN_NO_REVEAL')
        release=self.root/'registry'/f'{run}.released'
        need(release.is_file(),'TRANSACTION_NOT_FINALIZED')
        release_payload=self._verify_signature(json.loads(release.read_bytes()))
        regpath=self.root/'registry'/f'{run}.json'
        need(regpath.is_file(),'RUN_NOT_COMMITTED')
        need({k:release_payload[k] for k in ('run_id','registration_sha256','status')}=={'run_id':run,'registration_sha256':sha(regpath.read_bytes()),'status':'RESOURCE_AND_TRANSACTION_COMPLETE'} and 'final_resources' in release_payload,'RELEASE_RECEIPT')
        reg=self._verify_signature(json.loads(regpath.read_bytes()));path=self.root/'committed'/run
        need(path.is_dir(),'MISSING_COMMITTED_RUN')
        need(sha((path/'commit.json').read_bytes())==reg['commit_sha256'],'COMMIT_HASH')
        commit=self._verify_signature(json.loads((path/'commit.json').read_bytes()))
        need(commit['run_id']==reg['run_id']==run and commit['status']=='COMMITTED','COMMIT_RUN')
        mb=(path/'manifest.json').read_bytes();need(sha(mb)==reg['manifest_sha256']==commit['manifest_sha256'],'MANIFEST_HASH')
        m=json.loads(mb);need(m['run_id']==run and m['bindings']==bindings(),'FROZEN_PROVENANCE_CHANGED')
        need(files_in(path)==sorted(list(m['files'])+['manifest.json','commit.json']),'MANIFEST_CLOSURE')
        for name,h in m['files'].items():need(sha((path/name).read_bytes())==h,'ARTIFACT_HASH')
        plan=json.loads((path/'execution_plan.json').read_bytes());verify_plan(plan)
        need(sha(enc(plan))==m['plan_sha256']==commit['execution_plan_sha256'],'PLAN_HASH')
        need(commit['contract_sha256']==plan['bindings']['contract_sha256'],'CONTRACT_HASH')
        need(m['files']['source_provenance.json']==m['source_provenance_sha256']==commit['source_provenance_sha256'],'PROVENANCE_HASH')
        ledger=json.loads((path/'terminal_ledger.json').read_bytes());reconcile_ledger(plan,ledger)
        need(json.loads((path/'reconciliation.json').read_bytes())['status']=='PASS','RECONCILIATION')
        prov=json.loads((path/'source_provenance.json').read_bytes())
        need(set(prov)=={'primary','S1','S2a','S2b'},'PROVENANCE_VARIANTS')
        for v,p in prov.items():
            need(p['source_variant']==v and p['contract_sha256']==plan['bindings']['contract_sha256'],'SOURCE_PROVENANCE')
            need(all(plan['bindings']['code_hashes'][k]==h for k,h in p['adapter_code_hashes'].items()),'ADAPTER_PROVENANCE')
        return path,commit,reg,ledger
    def authorize_reveal(self,run):
        _,commit,reg,_=self._verified(run)
        return self._sign(dict(run_id=run,manifest_sha256=commit['manifest_sha256'],contract_sha256=commit['contract_sha256'],execution_plan_sha256=commit['execution_plan_sha256'],commit_record_sha256=reg['commit_sha256'],purpose='REVEAL_COMMITTED_RESULTS'))
    def read(self,run,authorization):
        path,commit,reg,ledger=self._verified(run);token=self._verify_signature(authorization)
        need(token==dict(run_id=run,manifest_sha256=commit['manifest_sha256'],contract_sha256=commit['contract_sha256'],execution_plan_sha256=commit['execution_plan_sha256'],commit_record_sha256=reg['commit_sha256'],purpose='REVEAL_COMMITTED_RESULTS'),'REVEAL_BINDING')
        # Only here are substantive result objects exposed to the public API.
        return [self._decrypt(path,run,row['artifact']) for row in ledger]
    def status(self,run):
        self._id(run)
        if (self.root/'registry'/f'{run}.json').exists():self._verified(run);return {'run_id':run,'status':'COMMITTED'}
        path=self.root/'staging'/run
        if (path/'failure.json').exists():return json.loads((path/'failure.json').read_bytes())
        return {'run_id':run,'status':'SEALED_INCOMPLETE' if path.exists() else 'ABSENT'}
