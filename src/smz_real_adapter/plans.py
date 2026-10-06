"""Compile hash-bound identity/source metadata to a selected-row plan; no party I/O."""
import csv,io,json
from .adapter import need,digest,integer,VARIANTS,CONTRACT,IMPLEMENTATION,ORDER,COLUMNS

def compile_plan(profile,variant,read_metadata,*,expected_profile_sha256):
    # profile bytes are separately frozen; providers may read ONLY hash-bound metadata.
    need(type(profile) is bytes and digest(profile)==expected_profile_sha256,'PROFILE_HASH_MISMATCH')
    p=json.loads(profile)
    need(p['contract_sha256']==CONTRACT,'CONTRACT_HASH_MISMATCH')
    need(p['implementation_manifest_sha256']==IMPLEMENTATION,'IMPLEMENTATION_HASH_MISMATCH')
    need(tuple(p['party_order'])==ORDER and tuple(p['party_source_columns'])==COLUMNS,'PARTY_SCHEMA_MISMATCH')
    need(variant in VARIANTS,'S3_NOT_EXECUTABLE' if variant=='S3' else 'UNKNOWN_SOURCE_VARIANT')
    v=p['variants'][variant]
    def fetch(path,h):
        need(p['metadata_files'].get(path)==h,'UNBOUND_METADATA')
        b=read_metadata(path);need(type(b) is bytes and digest(b)==h,'METADATA_HASH_MISMATCH')
        reader=csv.DictReader(io.StringIO(b.decode('utf-8-sig')))
        need(len(reader.fieldnames)==len(set(reader.fieldnames)),'METADATA_SCHEMA')
        return list(reader)
    mappings=fetch(v['mapping_path'],v['mapping_sha256']);designs=fetch(v['design_path'],v['design_sha256'])
    selectors={};design={};commitments={}
    for r in mappings:
        uid=r['uuid'];need(uid and uid not in selectors,'DUPLICATE_UUID');source=r[v['mapping_source_column']]
        need(source in p['source_files'],'UNREGISTERED_SOURCE')
        if 'source_sha256' in r:need(r['source_sha256']==p['source_files'][source]['sha256'],'SOURCE_SELECTOR_HASH_MISMATCH')
        selectors[uid]=source
        if 'selector_commitment' in r:commitments[uid]=r['selector_commitment']
    for r in designs:
        uid=r['uuid'];need(uid and uid not in design,'DUPLICATE_UUID')
        design[uid]=dict(region=r['region'],tik_uuid=r['tik_uuid'],voters=integer(r['voters']),source_variant=variant)
    need(len(selectors)==v['expected_rows'] and set(selectors)==set(design),'MEMBERSHIP_MISMATCH')
    plan=dict(variant=variant,selectors=selectors,design=design,expected_rows=v['expected_rows'],source_files={path:p['source_files'][path] for path in set(selectors.values())},party_order=p['party_order'],party_source_columns=p['party_source_columns'],invalid_missing_tokens=p['invalid_missing_tokens'],contract_sha256=CONTRACT,implementation_manifest_sha256=IMPLEMENTATION,universe=v['universe'],mapping_version=p['version'],mapping_sha256=v['mapping_sha256'],schema_sha256=p['schema_sha256'],metadata_hashes={v['mapping_path']:v['mapping_sha256'],v['design_path']:v['design_sha256']},profile_sha256=expected_profile_sha256)
    if commitments:need(set(commitments)==set(selectors),'SELECTOR_COMMITMENT_MISSING');plan['selector_commitments']=commitments
    return plan
