"""Encrypted chunks, complete closure, signed atomic commit and bounded reads."""
import os,json,secrets,hashlib
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from . import codec
class Blocked(RuntimeError):pass
def need(ok,message):
    if not ok:raise Blocked(message)
def durable(path,b):
    with path.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
_HASH_CACHE={}
def signature(path):
    s=path.stat();return (str(path.absolute()),s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def file_sha(path):
    key=signature(path)
    if key not in _HASH_CACHE:
        with path.open('rb') as f:value=hashlib.file_digest(f,'sha256').hexdigest()
        need(signature(path)==key,'FILE_CHANGED_DURING_HASH');_HASH_CACHE[key]=value
    return _HASH_CACHE[key]

class Store:
    def __init__(self,root):
        self.root=Path(root).resolve();self.root.mkdir(parents=True,exist_ok=True)
        for name in ('staging','committed','vault'): (self.root/name).mkdir(exist_ok=True)
        key=self.root/'vault/signing_key'
        if not key.exists():durable(key,Ed25519PrivateKey.generate().private_bytes_raw());os.chmod(key,0o600)
        self._signer=Ed25519PrivateKey.from_private_bytes(key.read_bytes())
        self._semantic_verified=set()
    def _name(self,run):need(type(run) is str and run and all(c.isalnum() or c in '-_' for c in run),'RUN_ID');return run
    def _sign(self,p):return dict(payload=p,signature=self._signer.sign(codec.encode(p)))
    def _verify(self,x):
        try:self._signer.public_key().verify(x['signature'],codec.encode(x['payload']))
        except Exception as e:raise Blocked('SIGNATURE') from e
        return x['payload']
    def begin(self,run,plan):
        self._name(run);p=self.root/'staging'/run
        need(not p.exists() and not (self.root/'committed'/run).exists(),'FRESH_RUN_REQUIRED')
        p.mkdir();key=secrets.token_bytes(32);durable(self.root/'vault'/run,key)
        tx=_Writer(self,run,p,key,plan);tx.put('plan',plan);return tx
    def verify(self,run,_internal=False):
        self._name(run);p=self.root/'committed'/run
        need(p.is_dir(),'NOT_COMMITTED')
        marker=codec.decode((p/'commit').read_bytes());commit=self._verify(marker)
        need(commit['run']==run,'COMMIT_RUN')
        if not _internal:
            receipt=self._verify(codec.decode((self.root/'vault'/(run+'.release')).read_bytes()))
            need(receipt['commit']==codec.digest(marker) and receipt['run']==run and receipt['resources']=='PASS','FINAL_RESOURCE_RELEASE')
        manifest=codec.decode((p/'manifest').read_bytes());need(codec.digest(manifest)==commit['manifest'],'MANIFEST_HASH')
        expected=set(manifest['artifacts'])|{'manifest','commit'}
        actual={str(x.relative_to(p)) for x in p.rglob('*') if x.is_file()}
        need(actual==expected and not any(x.is_symlink() for x in p.rglob('*')),'MANIFEST_CLOSURE')
        key=(self.root/'vault'/run).read_bytes()
        for name,entry in manifest['artifacts'].items():
            need(file_sha(p/name)==entry['physical'],'PHYSICAL_HASH')
            observed=(signature(p/name),entry['physical'],entry['semantic'],run)
            if observed not in self._semantic_verified:
                self._decode(p,name,entry,key,run)
                need(signature(p/name)==observed[0],'FILE_CHANGED_DURING_VERIFY')
                self._semantic_verified.add(observed)
        plan=self._decode(p,'plan',manifest['artifacts']['plan'],key,run)
        need(codec.digest(plan)==commit['plan'],'PLAN_HASH')
        from .engine import verify_plan
        verify_plan(plan)
        ledger=self._decode(p,'ledger',manifest['artifacts']['ledger'],key,run)
        validate_ledger(plan,ledger,manifest['artifacts'])
        need(commit['reconciliation']=='PASS' and commit['resources']=='PASS','COMMIT_GATES')
        return p,manifest,commit,codec.digest(marker)
    def _decode(self,p,name,entry,key,run):
        blob=(p/name).read_bytes()
        need(codec.sha(blob)==entry['physical'],'PHYSICAL_HASH')
        try:value=codec.unpack(AESGCM(key).decrypt(blob[:12],blob[12:],(run+':'+name).encode()))
        except Exception as e:raise Blocked('SEALED_CHUNK') from e
        need(codec.digest(value)==entry['semantic'],'SEMANTIC_HASH');return value
    def authorize(self,run):
        _,m,c,ch=self.verify(run)
        return self._sign(dict(purpose='REVEAL',run=run,manifest=codec.digest(m),commit=ch,plan=c['plan'],contract=c['contract']))
    def read(self,run,token,name):
        return self.read_many(run,token,(name,))[0]
    def read_many(self,run,token,names):
        need(0<len(names)<=64,'BOUNDED_QUERY')
        p,m,c,ch=self.verify(run);t=self._verify(token)
        need(t==dict(purpose='REVEAL',run=run,manifest=codec.digest(m),commit=ch,plan=c['plan'],contract=c['contract']),'REVEAL_BINDING')
        need(all(name in m['artifacts'] for name in names),'UNREGISTERED_QUERY')
        key=(self.root/'vault'/run).read_bytes()
        values=tuple(self._decode(p,name,m['artifacts'][name],key,run) for name in names)
        need(self.verify(run)[3]==ch,'PACKAGE_CHANGED_DURING_QUERY')
        return values

def validate_ledger(plan,ledger,artifacts):
    ids=[c['id'] for c in plan['cells']]
    need(len(ledger)==1620 and len({c['id'] for c in ledger})==1620 and sorted(c['id'] for c in ledger)==ids,'TERMINAL_LEDGER')
    for c in ledger:
        need(c['parameters']==next(x for x in plan['cells'] if x['id']==c['id']),'CELL_PARAMETER_BINDING')
        need(c['terminal'] in ('COMPUTED','CONTRACT_UNSUPPORTED') and c['reconciliation']=='PASS','FAILED_CELL')
        need(c['result'] in artifacts and c['result_semantic']==artifacts[c['result']]['semantic'],'CELL_RESULT_BINDING')
        for path,semantic in c['dependencies'].items():need(path in artifacts and artifacts[path]['semantic']==semantic,'CELL_DEPENDENCY')
        need(c['commitment']==codec.digest({k:v for k,v in c.items() if k!='commitment'}),'CELL_COMMITMENT')

class _Writer:
    def __init__(self,store,run,path,key,plan):self.store=store;self.run=run;self.path=path;self.key=key;self.plan=plan;self.index={};self.ledger=[]
    def put(self,name,value):
        need(name not in self.index and name not in ('manifest','commit') and all(x not in ('','..','.') for x in name.split('/')) and not name.startswith('/'),'ARTIFACT_PATH')
        p=self.path/name;p.parent.mkdir(parents=True,exist_ok=True)
        nonce=secrets.token_bytes(12);blob=nonce+AESGCM(self.key).encrypt(nonce,codec.pack(value),(self.run+':'+name).encode())
        durable(p,blob);entry=dict(physical=codec.sha(blob),semantic=codec.digest(value),bytes=len(blob));self.index[name]=entry;return entry['semantic']
    def cell(self,cell,result,dependencies):
        need(cell in self.plan['cells'],'UNPLANNED_CELL')
        need(result['source_id']==cell['source'] and result.get('design_id',result.get('spec_id'))==cell['spec'],'CELL_SCIENTIFIC_IDENTITY')
        if cell['family']=='ABC':
            from fractions import Fraction
            need(result['lambda_']==Fraction(cell['lambda_quarters'],4) and result['mu']==Fraction(cell['mu_quarters'],4),'CELL_PARAMETERS')
        name='cells/'+cell['id'];semantic=self.put(name,result)
        item=dict(id=cell['id'],terminal='COMPUTED' if result['status']=='APPLICABLE' else 'CONTRACT_UNSUPPORTED',reconciliation='PASS',result=name,result_semantic=semantic,dependencies=dependencies,parameters=cell)
        item['commitment']=codec.digest(item);self.ledger.append(item)
    def finish(self,meter,failpoint=None):
        need(codec.digest(self.plan)==self.index['plan']['semantic'],'PLAN_MUTATION')
        self.ledger.sort(key=lambda c:c['id']);validate_ledger(self.plan,self.ledger,self.index)
        self.put('ledger',self.ledger);self.put('reconciliation',dict(status='PASS',cells=1620,ABC=1600,D=20))
        verified={}
        for name,e in self.index.items():
            observed=signature(self.path/name)
            self.store._decode(self.path,name,e,self.key,self.run)
            need(signature(self.path/name)==observed,'FILE_CHANGED_DURING_PRECOMMIT_VERIFY')
            verified[name]=observed

        if failpoint=='after_serialization':raise Blocked('INJECTED_CRASH')
        meter.check();self.put('resources',meter.report())
        manifest=dict(version='SMZ_ARCH_B_R1',run=self.run,artifacts=self.index)
        durable(self.path/'manifest',codec.encode(manifest))
        if failpoint=='after_manifest':raise Blocked('INJECTED_CRASH')
        meter.check()
        commit=dict(run=self.run,manifest=codec.digest(manifest),plan=self.index['plan']['semantic'],contract=self.plan['contract'],reconciliation='PASS',resources='PASS')
        marker=codec.encode(self.store._sign(commit))
        if failpoint=='commit_write':durable(self.path/'commit.partial',marker[:10]);raise Blocked('INJECTED_CRASH')
        durable(self.path/'commit',marker)
        destination=self.store.root/'committed'/self.run
        os.rename(self.path,destination)
        # Still no reveal authorization; final verification and resource accounting must pass.
        try:
            # Atomic same-filesystem rename preserves each child file identity.
            # Transfer only the certificate for the exact bytes already decoded;
            # final verification still checks complete closure and physical hashes.
            for name,observed in verified.items():
                current=signature(destination/name)
                if current[1:]==observed[1:]:
                    e=self.index[name]
                    self.store._semantic_verified.add((current,e['physical'],e['semantic'],self.run))
            if failpoint=='verified_cache_mutation':
                name=next(k for k in self.index if '/basis/' in k)
                path=destination/name;blob=bytearray(path.read_bytes());blob[-1]^=1;path.write_bytes(blob)
            self.store.verify(self.run,_internal=True);meter.check()
            final_bytes=sum(x.stat().st_size for x in destination.rglob('*') if x.is_file())
            final_report=meter.report()
            receipt=self.store._sign(dict(run=self.run,commit=codec.digest(codec.decode(marker)),resources='PASS',resource_report=final_report))
            durable(self.store.root/'vault'/(self.run+'.release'),codec.encode(receipt))
            if failpoint=='after_release_resource':raise Blocked('RESOURCE_STOP_D_INJECTED_AFTER_RELEASE')
            meter.check()
        except BaseException:
            release=self.store.root/'vault'/(self.run+'.release')
            if release.exists():os.rename(release,self.store.root/'vault'/(self.run+'.failed_release'))
            os.rename(destination,self.path);raise
        return dict(status='COMMITTED',run=self.run,resources=final_report,final_bytes=final_bytes)
