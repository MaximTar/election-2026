"""Metadata-only gate and authorized source transport. Never fits a model."""
import collections,csv,gzip,hashlib,json
from pathlib import Path
from src.smz_real_adapter.plans import compile_plan
from src.smz_real_adapter import adapter as qualified

ROOT=Path(__file__).resolve().parents[2]
FREEZE=ROOT/'outputs/smz_v2_external_freeze/20261002_v2'
PROFILE=ROOT/'outputs/smz_real_party_adapter/20260929_v1/frozen_source_profile.json'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(ok,reason):
    if not ok:raise RuntimeError('EXTERNAL_REAL_ADAPTER: '+reason)
def plans():
    p=PROFILE.read_bytes();h=sha(PROFILE)
    need(h=='78385131591910684ebfa3115f27159d4e78be76b5690fdcebc7c72500a84aa3','PROFILE_HASH')
    return {v:compile_plan(p,v,lambda x:(ROOT/x).read_bytes(),expected_profile_sha256=h)
            for v in ['primary','S1','S2a','S2b']}
def metadata_check():
    all_plans=plans();profile=json.loads(PROFILE.read_text())
    # Source headers and opaque file hashes only; no source count/party rows parsed.
    headers={}
    for path,spec in profile['source_files'].items():
        need(sha(ROOT/path)==spec['sha256'],'SOURCE_SNAPSHOT_HASH')
        with gzip.open(ROOT/path,'rt',encoding='utf-8-sig',newline='') as f:header=next(csv.reader(f))
        need(header==spec['header'],'SOURCE_HEADER')
        headers[path]={'schema_verified':True,'party_columns_numeric_read':False,'source_sha256':spec['sha256']}
    region_rows=json.loads((FREEZE/'region_index.json').read_text())['regions']
    region_names={r['official_region_id']:r['name'] for r in region_rows}
    regions=set(region_names)
    need(len(regions)==84,'REGION_COUNT')
    metadata={s:{} for s in all_plans}
    with gzip.open(FREEZE/'membership_metadata.csv.gz','rt',newline='') as f:
        for z in csv.DictReader(f):
            s,u=z['source'],z['uuid'];need(u not in metadata[s],'DUPLICATE_METADATA_UUID')
            need(z['official_region_id'] in regions,'OFFICIAL_REGION_ID')
            plan=all_plans[s];need(u in plan['selectors'] and region_names[z['official_region_id']]==plan['design'][u]['region'],'SOURCE_REGION_MEMBERSHIP')
            n,I,V=map(int,[z['voters'],z['issued'],z['valid']])
            need(n==plan['design'][u]['voters'] and 0<V<=I<=n,'METADATA_DOMAIN')
            J=None if z['invalid_status']=='UNKNOWN' else int(z['known_invalid'])
            need(z['invalid_status'] in ['DEFINED','UNKNOWN'] and (J is None or 0<=J and V+J<=I),'INVALID_MAPPING')
            reason='REGISTERED_LE_100' if n<=100 else 'INVALID_UNKNOWN' if J is None else 'CAST_NONPOSITIVE' if V+J<=0 else 'CAST_GT_REGISTERED' if V+J>n else ''
            need(reason==z['cedar_exclusion_reason'] and (not reason)==(z['eligible_CEDAR']=='1'),'CEDAR_ELIGIBILITY')
            metadata[s][u]=z
    expected=list(csv.DictReader((FREEZE/'cross_family_eligibility_summary.csv').open()))
    summary=[]
    for row in expected:
        s,family=row['source'],row['family'];zs=metadata[s]
        need(set(zs)==set(all_plans[s]['selectors']) and len(zs)==int(row['source_frame_UIKs']),'SOURCE_MEMBERSHIP')
        kept=[z for z in zs.values() if family!='CEDAR' or z['eligible_CEDAR']=='1']
        reasons=collections.Counter(z['cedar_exclusion_reason'] for z in zs.values() if family=='CEDAR' and z['cedar_exclusion_reason'])
        need(len(kept)==int(row['eligible_UIKs']) and len(zs)-len(kept)==int(row['excluded_UIKs']),'ELIGIBILITY_COUNTS')
        need(dict(reasons)==json.loads(row['exclusion_reason_counts']),'EXCLUSIVE_REASONS')
        for field,col in [('voters','eligible_voters'),('valid','eligible_valid')]:
            need(sum(int(z[field]) for z in kept)==int(row[col]),'ELIGIBILITY_DENOMINATOR')
        need({z['official_region_id'] for z in kept}==regions,'FAMILY_REGION_COVERAGE')
        summary.append({'source':s,'family':family,'source_rows':len(zs),'eligible_rows':len(kept),
                        'excluded_rows':len(zs)-len(kept),'reason_counts':dict(reasons),'regions':84,
                        'UUID_membership_sha256':hashlib.sha256('\n'.join(sorted(z['uuid'] for z in kept)).encode()).hexdigest()})
    states=list(csv.DictReader((FREEZE/'state_index.csv').open()))
    need(len(states)==362 and len({z['state_id'] for z in states})==362,'STATE_IDS')
    for family in ['ISTORIES','CEDAR','NOVAYA_1D','NOVAYA_2D']:
        rows=[z for z in states if z['family']==family];b=[z for z in rows if json.loads(z['method_control_values']).get('preset')=='B']
        need(len(b)==88,'OFAT_B_COUNT')
        need({z['source'] for z in b if not z['excluded_region_id']}==set(all_plans),'OFAT_SOURCES')
        need({z['excluded_region_id'] for z in b if z['excluded_region_id']}==regions,'LOO_ALL_84')
        need(all(z['source']=='primary' for z in rows if z['excluded_region_id']),'SOURCE_LOO_CROSS')
        need(all(z['source']=='primary' and not z['excluded_region_id'] for z in rows if z not in b),'CONTROL_CROSS')
    need(sum(z['visibility']=='public' for z in states)==361,'PUBLIC_COUNT')
    need(sum(z['requires_fit']=='true' for z in states if z['family']=='NOVAYA_2D')==89,'2D_FITS')
    return {'status':'PASS','metadata_rows_inspected':sum(len(v) for v in metadata.values()),'source_variants':list(all_plans),
            'summary':summary,'source_headers':headers,'source_membership_exact':True,'regions':84,
            'topology':{'states':362,'public':361,'internal':1,'2D_fits':89,'2D_outputs':91},
            'real_party_rows_fit':0,'real_party_counts_numeric_read':0,'real_fit_invocations':0,
            'real_adapter_model_execution_performed':False,'new_exclusions':0,'whole_region_exclusions':0,'collateral_region_exclusions':0}

def load(source):
    """Future authorized coordinator only; real counts never read by metadata_check."""
    from .transport import require_active,RealRow,RealFrame
    ctx=require_active();need(source in ['primary','S1','S2a','S2b'],'SOURCE_NOT_EXECUTABLE')
    plan=plans()[source]
    def provider(path,h):
        ctx['access_log'].append({'source':source,'path':path,'event':'REAL_COUNT_SOURCE_OPEN'})
        need(sha(ROOT/path)==h,'SOURCE_CHANGED');return (ROOT/path).open('rb')
    frame=qualified._decode(plan,source,provider,run_id=ctx['run_id'],created_at=ctx['created_at'],
                            bundle_sha=sha(PROFILE),origin='EXTERNAL_C_LITE_AUTHORIZED_REAL_SOURCE')
    qualified.verify_frame(frame)
    with gzip.open(FREEZE/'membership_metadata.csv.gz','rt',newline='') as f:
        frozen_rows={z['uuid']:z for z in csv.DictReader(f) if z['source']==source}
    output=[]
    for r in frame.rows:
        z=frozen_rows[r.uuid]
        need((r.voters,r.issued,r.valid)==tuple(int(z[k]) for k in ['voters','issued','valid']),'FROZEN_METADATA_CHANGED')
        need(r.known_invalid.status==z['invalid_status'] and
             (r.known_invalid.status=='UNKNOWN' or r.known_invalid.value==int(z['known_invalid'])),'FROZEN_INVALID_CHANGED')
        statuses=tuple((family,'ELIGIBLE' if family!='CEDAR' or z['eligible_CEDAR']=='1' else 'EXCLUDED',
                        z['cedar_exclusion_reason'] if family=='CEDAR' else '')
                       for family in ['ISTORIES','CEDAR','NOVAYA_1D','NOVAYA_2D'])
        output.append(RealRow(r.uuid,z['official_region_id'],r.voters,r.issued,r.valid,r.parties[1],
                             r.known_invalid.value if r.known_invalid.status=='DEFINED' else None,r.parties,
                             r.source_variant,r.source_id,r.source_sha256,r.selector_commitment,r.tik_uuid,statuses))
    ctx['access_log'].append({'source':source,'event':'REAL_ROWS_DECODED','count':len(output)})
    from .transport import COUNTERS
    COUNTERS['real_party_rows']+=len(output)
    return RealFrame(tuple(output),source)
