"""All fixtures generated analytically; memory-only providers; zero real source opens."""
from pathlib import Path
import csv,io,json,gzip,copy,time,resource,sys,hashlib
from dataclasses import replace
from unittest.mock import patch
from . import adapter as a
from .plans import compile_plan
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'outputs/smz_real_party_adapter/20260929_v1'
OUT=BASE/'attempt03'

def csv_bytes(header,rr):
    s=io.StringIO(newline='');w=csv.DictWriter(s,fieldnames=header);w.writeheader();w.writerows(rr);return s.getvalue().encode()
def mock_fixture():
    real=json.loads((BASE/'frozen_source_profile.json').read_text())
    # Only already-audited HEADER/NA/schema metadata reused; no source counts.
    header=next(v['header'] for k,v in real['source_files'].items() if k.endswith('/paper_primary.csv.gz'))
    rr=[]
    for i in range(6):
        r={k:'' for k in header};r.update(uuid=f'mock:u{i}',voters='1000',issued='250',valid='100',invalid='5' if i%2==0 else '')
        r.update({k:'10' for k in a.COLUMNS});rr.append(r)
    alt=copy.deepcopy(rr);fresh=copy.deepcopy(rr)
    for i in (0,1):alt[i].update(voters='1200',issued='300',valid='200',invalid='7');alt[i].update({k:'20' for k in a.COLUMNS})
    fresh[0].update(voters='900',issued='180',valid='150',invalid='');fresh[0].update({k:'15' for k in a.COLUMNS})
    sources={'mock://canonical.csv.gz':gzip.compress(csv_bytes(header,rr),mtime=0),'mock://alternative.csv.gz':gzip.compress(csv_bytes(header,alt),mtime=0),'mock://fresh.csv.gz':gzip.compress(csv_bytes(header,fresh),mtime=0)}
    p=dict(real);p['source_files']={k:dict(sha256=a.digest(b),header=header,compression='gzip') for k,b in sources.items()};p['metadata_files']={};p['variants']={};metadata={}
    for variant in a.VARIANTS:
        ids=[i for i in range(6) if variant!='S1' or i not in (0,1)];mapping=[];design=[]
        for i in ids:
            src='mock://alternative.csv.gz' if variant=='S2a' and i in (0,1) else 'mock://fresh.csv.gz' if variant=='S2b' and i==0 else 'mock://canonical.csv.gz'
            n=1200 if src=='mock://alternative.csv.gz' else 900 if src=='mock://fresh.csv.gz' else 1000
            uid=f'mock:u{i}';commit=a.digest(json.dumps([p['source_files'][src]['sha256'],uid,a.COUNTS],ensure_ascii=False,separators=(',',':')).encode())
            mapping.append(dict(uuid=uid,source_file=src,source_sha256=p['source_files'][src]['sha256'],selector_commitment=commit))
            design.append(dict(uuid=uid,region=f'mock:r{i//4}',tik_uuid=f'mock:t{i//2}',voters=n))
        mp=f'mock://{variant}_mapping.csv';dp=f'mock://{variant}_design.csv'
        metadata[mp]=csv_bytes(list(mapping[0]),mapping);metadata[dp]=csv_bytes(list(design[0]),design)
        p['metadata_files'].update({mp:a.digest(metadata[mp]),dp:a.digest(metadata[dp])})
        p['variants'][variant]=dict(mapping_path=mp,mapping_sha256=a.digest(metadata[mp]),mapping_source_column='source_file',design_path=dp,design_sha256=a.digest(metadata[dp]),expected_rows=len(ids),universe='MOCK_ONLY_'+variant)
    pb=a.canonical(p).encode();plans={v:compile_plan(pb,v,metadata.__getitem__,expected_profile_sha256=a.digest(pb)) for v in a.VARIANTS}
    mb=a.canonical(dict(origin='SMZ_GENERATED_MOCK_SOURCE_V1',plans=plans)).encode()
    return a.MockBundle(mb,tuple(sorted(sources.items()))),pb,metadata

def run():
    start=time.monotonic();OUT.mkdir(exist_ok=True)
    need=lambda c,m: a.need(c,m)
    assert not (OUT/'qualification.json').exists()
    fixture,pb,metadata=mock_fixture()
    # Saving mock sources is safe: generated formulas above, explicitly mock identifiers.
    fd=OUT/'mock_fixtures';fd.mkdir()
    (fd/'profile.json').write_bytes(pb);(fd/'bundle_manifest.json').write_bytes(fixture.manifest_bytes)
    for name,b in fixture.files+tuple(metadata.items()):(fd/name.split('/')[-1]).write_bytes(b)
    checks=[];frames={};repairs=[]
    def load(bundle=fixture,variant='primary',**kw):
        opts=dict(expected_manifest_sha256=a.digest(bundle.manifest_bytes),run_id='mock:qualification',created_at='2026-09-29T00:00:00Z');opts.update(kw)
        return a.qualify_mock(bundle,variant,**opts)
    def positive(name,fn):
        try:fn();checks.append(dict(id=name,kind='positive',status='PASS'))
        except Exception as e:checks.append(dict(id=name,kind='positive',status='FAIL',reason=type(e).__name__+':'+str(e)))
    def negative(name,fn,expected=None):
        try:fn();checks.append(dict(id=name,kind='negative',status='FAIL',reason='not rejected'))
        except (a.AdapterError,) as e:checks.append(dict(id=name,kind='negative',status='PASS' if expected is None or e.code==expected else 'FAIL',rejection=e.code))
        except Exception as e:checks.append(dict(id=name,kind='negative',status='FAIL',reason=repr(e)))
    def meta_change(fn):
        m=json.loads(fixture.manifest_bytes);fn(m);return a.MockBundle(a.canonical(m).encode(),fixture.files)
    def raw_change(fn,rehash=True):
        m=json.loads(fixture.manifest_bytes);ff=dict(fixture.files);name='mock://canonical.csv.gz'
        rr=list(csv.DictReader(io.StringIO(gzip.decompress(ff[name]).decode())));header=list(rr[0]);fn(rr,header)
        ff[name]=gzip.compress(csv_bytes(header,rr),mtime=0)
        if rehash:
            for plan in m['plans'].values():
                if name in plan['source_files']:plan['source_files'][name]['sha256']=a.digest(ff[name]);plan['source_files'][name]['header']=header
                for uid,src in plan['selectors'].items():
                    if src==name:plan['selector_commitments'][uid]=a.digest(json.dumps([a.digest(ff[name]),uid,a.COUNTS],ensure_ascii=False,separators=(',',':')).encode())
        return a.MockBundle(a.canonical(m).encode(),tuple(sorted(ff.items())))
    # Mock mode must never open any project raw/processed/source-party file.
    accesses=[]
    def file_guard(event,args):
        if event!='open' or not isinstance(args[0],(str,bytes)):return
        path=Path(args[0]).resolve()
        if path.is_relative_to(ROOT/'data'):raise AssertionError('REAL_SOURCE_OPEN_FORBIDDEN')
        if path.is_relative_to(ROOT):accesses.append(str(path.relative_to(ROOT)))
    sys.addaudithook(file_guard)
    for variant in a.VARIANTS:
        def pos(v=variant):
            f=load(variant=v);frames[v]=f;need(len(f.rows)==(4 if v=='S1' else 6),'ROWS');need(all(r.source_variant==v for r in f.rows),'VARIANT')
            if v=='S2a':need(f.rows[0].voters==1200 and f.rows[0].issued==300 and f.rows[0].valid==200 and f.rows[0].parties==(20,)*10,'FULL_VECTOR')
            if v=='S2b':need(f.rows[0].voters==900 and f.rows[0].issued==180 and f.rows[0].valid==150 and f.rows[0].parties==(15,)*10,'FULL_VECTOR')
        positive(variant, pos)
    positive('known_invalid_defined',lambda:need(frames['primary'].rows[0].known_invalid==a.KnownInvalid('DEFINED',5),'J'))
    positive('known_invalid_unknown_not_I_minus_V',lambda:need(frames['primary'].rows[1].known_invalid==a.KnownInvalid('UNKNOWN'),'UNKNOWN'))
    positive('deterministic_provenance_replay',lambda:need(a.serialize_provenance(load())==a.serialize_provenance(load()),'DETERMINISM'))
    positive('S3_identity_metadata_only',lambda:need(a.source_alias('S3')==dict(status='IDENTITY_WITH_PRIMARY',execute=False,alias='primary'),'S3'))
    negative('wrong_source_hash',lambda:load(raw_change(lambda rr,h:rr[0].update(issued='249'),False)),'SOURCE_HASH_MISMATCH')
    negative('wrong_contract_hash',lambda:load(meta_change(lambda m:m['plans']['primary'].update(contract_sha256='bad'))),'CONTRACT_HASH_MISMATCH')
    negative('unknown_variant',lambda:load(variant='other'),'UNKNOWN_SOURCE_VARIANT')
    negative('S3_independent_load',lambda:load(variant='S3'),'S3_NOT_EXECUTABLE')
    negative('duplicate_UUID',lambda:load(raw_change(lambda rr,h:rr.append(rr[0]))),'DUPLICATE_UUID')
    def remove_party(rr,h):
        col=a.COLUMNS[-1];h.remove(col)
        for r in rr:del r[col]
    negative('missing_party',lambda:load(raw_change(remove_party)),'PARTY_SCHEMA_MISMATCH')
    def reorder(rr,h):
        i,j=h.index(a.COLUMNS[0]),h.index(a.COLUMNS[1]);h[i],h[j]=h[j],h[i]
    negative('wrong_party_order',lambda:load(raw_change(reorder)),'PARTY_SCHEMA_MISMATCH')
    negative('negative_party',lambda:load(raw_change(lambda rr,h:rr[0].update({a.COLUMNS[0]:'-1'}))),'COUNT_DOMAIN')
    negative('party_sum_mismatch',lambda:load(raw_change(lambda rr,h:rr[0].update({a.COLUMNS[0]:'11'}))),'PARTY_SUM_MISMATCH')
    negative('mixed_variants',lambda:load(meta_change(lambda m:m['plans']['primary']['design']['mock:u0'].update(source_variant='S2b'))),'MIXED_SOURCE_VARIANTS')
    def primary_substitution():
        ff=dict(fixture.files);ff['mock://alternative.csv.gz']=ff['mock://canonical.csv.gz'];return a.MockBundle(fixture.manifest_bytes,tuple(ff.items()))
    negative('primary_values_substituted_for_S2a',lambda:load(primary_substitution(),'S2a'),'SOURCE_HASH_MISMATCH')
    negative('primary_n_design_used_for_S2a',lambda:load(meta_change(lambda m:m['plans']['S2a']['design']['mock:u0'].update(voters=1000)),'S2a'),'VARIANT_VOTERS_MISMATCH')
    negative('dropped_selected_row',lambda:load(raw_change(lambda rr,h:rr.pop())),'MISSING_SELECTED_ROW')
    negative('extra_unexpected_selected_row',lambda:load(meta_change(lambda m:m['plans']['primary']['selectors'].update({'mock:extra':'mock://canonical.csv.gz'}))),'MEMBERSHIP_MISMATCH')
    negative('extra_raw_row_changed_frozen_bytes',lambda:load(raw_change(lambda rr,h:rr.append(dict(rr[0],uuid='mock:extra')),False)),'SOURCE_HASH_MISMATCH')
    negative('invalid_known_state',lambda:a.KnownInvalid('NOT_DEFINED',3),'INVALID_SEMANTIC_STATE')
    negative('invalid_exceeds_issued',lambda:load(raw_change(lambda rr,h:rr[0].update(invalid='200'))),'KNOWN_INVALID_COUNT_INTEGRITY')
    negative('synthetic_origin_spoof',lambda:load(meta_change(lambda m:m.update(origin='SMZ_SYNTHETIC_QUALIFICATION_V1'))),'MOCK_ORIGIN_MISMATCH')
    negative('synthetic_ID_spoof',lambda:load(meta_change(lambda m:m['plans']['primary']['selectors'].update({'syn:fake':'mock://canonical.csv.gz'}))),'MOCK_IDENTITY_REQUIRED')
    negative('actual_path_not_mock_bundle',lambda:a.qualify_mock(str(ROOT/'data/processed/primary.csv'),'primary',expected_manifest_sha256='x',run_id='mock:x',created_at='2026-09-29T00:00:00Z'),'MOCK_MEMORY_BUNDLE_REQUIRED')
    negative('actual_path_inside_mock_bundle',lambda:load(a.MockBundle(fixture.manifest_bytes,fixture.files+((str(ROOT/'data/processed/primary.csv'),b'x'),))),'MOCK_MEMORY_BUNDLE_REQUIRED')
    negative('ordinary_real_load',lambda:a.load_real('primary',authorization=True),'SEALED_COORDINATOR_AUTHORIZATION_REQUIRED')
    negative('untrusted_frame_constructor',lambda:a.RealPartyFrame(rows=()),'FRAME_CONSTRUCTOR_PRIVATE')
    if set(frames)!=set(a.VARIANTS):
        (OUT/'qualification.json').write_text(json.dumps(dict(status='FAIL',checks=checks,reason='positive frame unavailable; dependent guard checks NOT_RUN'),indent=2)+'\n')
        raise AssertionError('positive frame qualification failed')
    # Separate attestation/provenance and metadata failure fixtures.
    negative('wrong_profile_hash',lambda:compile_plan(pb,'primary',metadata.__getitem__,expected_profile_sha256='wrong'),'PROFILE_HASH_MISMATCH')
    negative('wrong_metadata_hash',lambda:compile_plan(pb,'primary',lambda _:b'wrong',expected_profile_sha256=a.digest(pb)),'METADATA_HASH_MISMATCH')
    negative('wrong_implementation_hash',lambda:load(meta_change(lambda m:m['plans']['primary'].update(implementation_manifest_sha256='wrong'))),'IMPLEMENTATION_HASH_MISMATCH')
    negative('wrong_bundle_hash',lambda:load(expected_manifest_sha256='wrong'),'BUNDLE_HASH_MISMATCH')
    def tamper():
        f=load();object.__setattr__(f,'origin','SMZ_SYNTHETIC_QUALIFICATION_V1');a.verify_frame(f)
    negative('frame_origin_tamper',tamper,'FRAME_ATTESTATION_FAILURE')
    def bad_provider():
        plan=json.loads(fixture.manifest_bytes)['plans']['primary']
        return a._decode(plan,'primary',lambda *_:io.BytesIO(b'corrupt'),run_id='mock:x',created_at='2026-09-29T00:00:00Z',bundle_sha='mock',origin='SMZ_MOCK_REAL_ADAPTER_QUALIFICATION')
    negative('provider_cannot_waive_source_hash',bad_provider,'SOURCE_HASH_MISMATCH')
    # Kernel guard only; all model entry points patched to forbid transformations.
    from src.smz import abc,d,api,common
    with patch.object(abc,'build',side_effect=AssertionError('NO_MODEL_CALL')),patch.object(abc,'C',side_effect=AssertionError('NO_MODEL_CALL')),patch.object(d,'execute',side_effect=AssertionError('NO_MODEL_CALL')):
        for obj,label in [(frames['primary'],'mock_RealPartyFrame'),({},'raw_dict')]:
            try:common.validate(obj);checks.append(dict(id='kernel_reject_'+label,kind='negative',status='FAIL'))
            except common.SMZError as e:checks.append(dict(id='kernel_reject_'+label,kind='negative',status='PASS' if e.status=='REAL_DATA_REVEAL_BLOCKED' else 'FAIL'))
    for variant,frame in frames.items():(OUT/f'mock_{variant}_provenance.json').write_text(a.serialize_provenance(frame)+'\n')
    qualification=dict(status='PASS' if all(c['status']=='PASS' for c in checks) else 'FAIL',checks=checks,positive=sum(c['kind']=='positive' for c in checks),negative=sum(c['kind']=='negative' for c in checks),failed=sum(c['status']=='FAIL' for c in checks),REAL_PARTY_ROWS_PROCESSED=0,scenario_transformations_run=False,resources=dict(wall_seconds=time.monotonic()-start,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,processes=1))
    (OUT/'qualification.json').write_text(json.dumps(qualification,indent=2)+'\n');(OUT/'negative_test_results.json').write_text(json.dumps([c for c in checks if c['kind']=='negative'],indent=2)+'\n')
    (OUT/'file_access_audit.json').write_text(json.dumps(dict(project_files=sorted(set(accesses)),real_data_opens=0,mock_sources='memory bytes only'),indent=2)+'\n')
    (OUT/'mock_fixture_manifest.json').write_text(json.dumps(dict(origin='analytically generated; no real values',formulas='6 mock rows; primary10perparty;alt20perparty;fresh15perparty;2regions/3TIKs;S1removes2',files={str(p.relative_to(ROOT)):a.file_sha(p) for p in fd.iterdir()},bundle_sha256=a.digest(fixture.manifest_bytes)),indent=2)+'\n')
    print(json.dumps(qualification,indent=2));assert qualification['status']=='PASS'
if __name__=='__main__':run()
