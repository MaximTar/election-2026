"""Exact selected-source parser and typed, attested input frame.

Public qualification consumes memory-only mock:// bundles. Real loading remains locked
until the separately qualified sealed coordinator supplies its authorization bridge.
No synthetic kernel/guard is modified and this module never imports a scenario engine.
"""
from dataclasses import dataclass
from decimal import Decimal,InvalidOperation
from pathlib import Path
import csv,gzip,hashlib,hmac,io,json,secrets
from src.data.schema import PARTIES,COUNTS
VERSION='SMZ_REAL_PARTY_ADAPTER_v1'
CONTRACT='34f19240c282fa27268891c9d04da7372ce5ba20f9c3f2ff3f3ef7d9d75286e5'
IMPLEMENTATION='e4e2754c90b568cc57c0d04bca0380cf245b6374fa25f1b83fb524f628c4a250'
VARIANTS=('primary','S1','S2a','S2b')
ORDER=tuple(PARTIES.values());COLUMNS=tuple(PARTIES)
ROOT=Path(__file__).resolve().parents[2]
PROFILE=ROOT/'outputs/smz_real_party_adapter/20260929_v1/frozen_source_profile.json'
_SECRET=secrets.token_bytes(32)
class AdapterError(ValueError):
    def __init__(self,code):self.code=code;super().__init__(code)
def need(ok,code):
    if not ok:raise AdapterError(code)
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def digest(b):return hashlib.sha256(b).hexdigest()
def file_sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def source_alias(v):
    if v=='S3':return {'status':'IDENTITY_WITH_PRIMARY','execute':False,'alias':'primary'}
    need(v in VARIANTS,'UNKNOWN_SOURCE_VARIANT');return {'variant':v,'execute':'FUTURE_AUTHORIZATION_REQUIRED'}
def integer(x):
    need(type(x) is str and bool(x.strip()),'COUNT_MISSING')
    try:v=Decimal(x)
    except InvalidOperation:raise AdapterError('COUNT_DOMAIN')
    need(v.is_finite() and v==v.to_integral_value() and v>=0,'COUNT_DOMAIN');return int(v)
@dataclass(frozen=True,slots=True)
class KnownInvalid:
    status:str
    value:int|None=None
    def __post_init__(self):
        need((self.status=='DEFINED' and type(self.value) is int and self.value>=0) or (self.status=='UNKNOWN' and self.value is None),'INVALID_SEMANTIC_STATE')
@dataclass(frozen=True,slots=True)
class RealPartyRow:
    uuid:str
    region:str
    tik_uuid:str
    voters:int
    issued:int
    valid:int
    parties:tuple
    known_invalid:KnownInvalid
    source_variant:str
    source_id:str
    source_sha256:str
    selector_commitment:str
@dataclass(frozen=True,slots=True,init=False)
class RealPartyFrame:
    rows:tuple
    source_variant:str
    origin:str
    provenance_json:str
    _attestation:str
    def __init__(self,*args,**kwargs):raise AdapterError('FRAME_CONSTRUCTOR_PRIVATE')
@dataclass(frozen=True,slots=True)
class MockBundle:
    """Memory bytes only. This is not a path loader or real authorization token."""
    manifest_bytes:bytes
    files:tuple

def _row_wire(r):
    return [r.uuid,r.region,r.tik_uuid,r.voters,r.issued,r.valid,list(r.parties),[r.known_invalid.status,r.known_invalid.value],r.source_variant,r.source_id,r.source_sha256,r.selector_commitment]
def _frame_digest(rows):
    h=hashlib.sha256()
    for r in rows:h.update(canonical(_row_wire(r)).encode());h.update(b'\n')
    return h.hexdigest()
def _signature(rows,variant,origin,provenance):
    return hmac.new(_SECRET,canonical([_frame_digest(rows),variant,origin,provenance]).encode(),'sha256').hexdigest()
def _mint(rows,variant,origin,provenance):
    f=object.__new__(RealPartyFrame);payload=canonical(provenance)
    for k,v in dict(rows=tuple(rows),source_variant=variant,origin=origin,provenance_json=payload,_attestation=_signature(rows,variant,origin,payload)).items():object.__setattr__(f,k,v)
    return f

def verify_frame(frame):
    need(type(frame) is RealPartyFrame and all(hasattr(frame,k) for k in RealPartyFrame.__slots__),'UNQUALIFIED_FRAME')
    need(hmac.compare_digest(frame._attestation,_signature(frame.rows,frame.source_variant,frame.origin,frame.provenance_json)),'FRAME_ATTESTATION_FAILURE')
    return json.loads(frame.provenance_json)
def serialize_provenance(frame):
    verify_frame(frame);return frame.provenance_json

def _decode(plan,variant,open_stream,*,run_id,created_at,bundle_sha,origin):
    """Shared parser. Caller must pass an already bound plan and authorized provider.

    No filesystem/source discovery or execution authorization occurs here. Mock public
    caller is the only installed caller. Future coordinator integration requires review.
    """
    need(variant in VARIANTS,'S3_NOT_EXECUTABLE' if variant=='S3' else 'UNKNOWN_SOURCE_VARIANT')
    need(plan['contract_sha256']==CONTRACT,'CONTRACT_HASH_MISMATCH')
    need(plan['implementation_manifest_sha256']==IMPLEMENTATION,'IMPLEMENTATION_HASH_MISMATCH')
    need(tuple(plan['party_order'])==ORDER and tuple(plan['party_source_columns'])==COLUMNS,'PARTY_SCHEMA_MISMATCH')
    need(plan['variant']==variant,'MIXED_SOURCE_VARIANTS')
    selected=plan['selectors'];design=plan['design'];need(len(selected)==len(design)==plan['expected_rows'] and set(selected)==set(design),'MEMBERSHIP_MISMATCH')
    need(bool(selected),'EMPTY_FRAME')
    parent={};output={};raw_account=[]
    files=plan['source_files']
    need(set(selected.values())<=files.keys(),'UNREGISTERED_SOURCE')
    for source_id in sorted(set(selected.values())):
        spec=files[source_id];wanted={u for u,s in selected.items() if s==source_id}
        stream=open_stream(source_id,spec['sha256'])
        # Adapter independently verifies bytes; a future provider cannot waive this gate.
        need(stream.seekable(),'SOURCE_STREAM_MUST_BE_REPLAYABLE')
        stream.seek(0);actual_hash=hashlib.file_digest(stream,'sha256').hexdigest()
        need(actual_hash==spec['sha256'],'SOURCE_HASH_MISMATCH');stream.seek(0)
        if spec['compression']=='gzip':stream=gzip.GzipFile(fileobj=stream,mode='rb')
        elif spec['compression']!='plain':raise AdapterError('UNKNOWN_COMPRESSION')
        with io.TextIOWrapper(stream,encoding='utf-8-sig',newline='') as f:
            reader=csv.reader(f);header=next(reader)
            need(header==spec['header'] and len(header)==len(set(header)),'SOURCE_HEADER_MISMATCH')
            need([k for k in header if k in COLUMNS]==list(COLUMNS),'PARTY_SCHEMA_MISMATCH')
            need(all(header.count(k)==1 for k in ['uuid',*COUNTS]),'REQUIRED_FIELD_MISSING')
            indices={k:header.index(k) for k in ['uuid',*COUNTS]};seen=set();kept=0
            for record in reader:
                need(len(record)==len(header),'ROW_SCHEMA_MISMATCH')
                uid=record[indices['uuid']];need(uid and uid not in seen,'DUPLICATE_UUID');seen.add(uid)
                if uid not in wanted:continue # source superset rows accounted, not eligible-frame exclusions
                need(uid not in output,'DUPLICATE_SELECTED_UUID')
                z=design[uid];need(z['source_variant']==variant,'MIXED_SOURCE_VARIANTS')
                need(z['region'] and z['tik_uuid'],'HIERARCHY_MISSING')
                need(parent.setdefault(z['tik_uuid'],z['region'])==z['region'],'HIERARCHY_CONFLICT')
                n,i,v=(integer(record[indices[k]]) for k in ['voters','issued','valid'])
                need(type(z['voters']) is int and n==z['voters'],'VARIANT_VOTERS_MISMATCH')
                need(0<v<=i<=n,'STRUCTURAL_COUNT_DOMAIN')
                counts=tuple(integer(record[indices[k]]) for k in COLUMNS)
                need(len(counts)==10 and sum(counts)==v,'PARTY_SUM_MISMATCH')
                raw_j=record[indices['invalid']]
                j=KnownInvalid('UNKNOWN') if raw_j in plan['invalid_missing_tokens'] else KnownInvalid('DEFINED',integer(raw_j))
                need(j.status=='UNKNOWN' or v+j.value<=i,'KNOWN_INVALID_COUNT_INTEGRITY')
                selector=digest(json.dumps([spec['sha256'],uid,COUNTS],ensure_ascii=False,separators=(',',':')).encode())
                if 'selector_commitments' in plan:need(selector==plan['selector_commitments'][uid],'SELECTOR_MISMATCH')
                output[uid]=RealPartyRow(uid,z['region'],z['tik_uuid'],n,i,v,counts,j,variant,source_id,spec['sha256'],selector);kept+=1
            need(wanted<=seen and kept==len(wanted),'MISSING_SELECTED_ROW')
            raw_account.append(dict(source_id=source_id,sha256=spec['sha256'],raw_rows=len(seen),selected_rows=kept,unselected_source_superset_rows=len(seen)-kept))
    need(set(output)==set(selected) and len(output)==plan['expected_rows'],'FINAL_MEMBERSHIP_MISMATCH')
    ordered=tuple(output[u] for u in sorted(output));del output
    code={str(p.relative_to(ROOT)):file_sha(p) for p in sorted(Path(__file__).parent.glob('*.py'))}
    provenance=dict(adapter_version=VERSION,adapter_code_hashes=code,adapter_code_bundle_sha256=digest(canonical(code).encode()),contract_version='SMZ-2026-v1',contract_sha256=CONTRACT,implementation_manifest_sha256=IMPLEMENTATION,source_variant=variant,source_universe=plan['universe'],source_mapping_version=plan['mapping_version'],source_mapping_sha256=plan['mapping_sha256'],source_profile_sha256=plan.get('profile_sha256',bundle_sha),metadata_hashes=plan.get('metadata_hashes',{}),party_schema_source_sha256=plan['schema_sha256'],party_order=list(ORDER),source_files=raw_account,selected_rows=len(ordered),regions=len({r.region for r in ordered}),official_TIKs=len({r.tik_uuid for r in ordered}),known_invalid_defined_rows=sum(r.known_invalid.status=='DEFINED' for r in ordered),known_invalid_unknown_rows=sum(r.known_invalid.status=='UNKNOWN' for r in ordered),invalid_semantics='selected invalid; unknown source stays UNKNOWN; never issued-valid',run_id=run_id,created_at=created_at,origin=origin,bundle_sha256=bundle_sha,input_frame_sha256=_frame_digest(ordered),scenario_results='NOT_COMPUTED',execution_authorized=False)
    return _mint(ordered,variant,origin,provenance)

def qualify_mock(bundle,variant,*,expected_manifest_sha256,run_id,created_at,mode='mock_real_adapter_qualification'):
    need(mode=='mock_real_adapter_qualification','REAL_LOADING_NOT_AUTHORIZED')
    need(type(bundle) is MockBundle and type(bundle.manifest_bytes) is bytes and type(bundle.files) is tuple,'MOCK_MEMORY_BUNDLE_REQUIRED')
    need(digest(bundle.manifest_bytes)==expected_manifest_sha256,'BUNDLE_HASH_MISMATCH')
    meta=json.loads(bundle.manifest_bytes);need(meta['origin']=='SMZ_GENERATED_MOCK_SOURCE_V1','MOCK_ORIGIN_MISMATCH')
    need(variant in VARIANTS,'S3_NOT_EXECUTABLE' if variant=='S3' else 'UNKNOWN_SOURCE_VARIANT')
    plan=meta['plans'][variant];need(all(u.startswith('mock:') for u in plan['selectors']),'MOCK_IDENTITY_REQUIRED')
    need(all(z['region'].startswith('mock:') and z['tik_uuid'].startswith('mock:') for z in plan['design'].values()),'MOCK_IDENTITY_REQUIRED')
    files=dict(bundle.files);need(len(files)==len(bundle.files),'DUPLICATE_SOURCE_ID')
    need(all(type(k) is str and k.startswith('mock://') and type(v) is bytes for k,v in bundle.files),'MOCK_MEMORY_BUNDLE_REQUIRED')
    need(set(plan['source_files'])<=files.keys(),'MISSING_MOCK_SOURCE')
    def provider(name,expected):
        need(name.startswith('mock://') and name in files,'MOCK_SOURCE_BOUNDARY')
        need(digest(files[name])==expected,'SOURCE_HASH_MISMATCH');return io.BytesIO(files[name])
    need(type(run_id) is str and run_id.startswith('mock:') and type(created_at) is str and created_at.endswith('Z'),'MOCK_RUN_METADATA')
    return _decode(plan,variant,provider,run_id=run_id,created_at=created_at,bundle_sha=expected_manifest_sha256,origin='SMZ_MOCK_REAL_ADAPTER_QUALIFICATION')

def load_real(variant,*,mode='closed_real_execution',authorization=None):
    """Reserved coordinator interface: fails before any source I/O in this release.

    No authorization issuer/verifier is installed. Blocker E02 must qualify that bridge;
    no truthy flag, SyntheticFrame or mock bundle can turn this into a real load.
    """
    source_alias(variant)
    if variant=='S3':raise AdapterError('S3_NOT_EXECUTABLE')
    raise AdapterError('SEALED_COORDINATOR_AUTHORIZATION_REQUIRED')
