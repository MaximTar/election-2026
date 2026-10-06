"""Source-only reconciliation. Counts accessed only for inclusion/arithmetic audit."""
import csv
import gzip
import hashlib
import json
import zipfile
from collections import Counter
import pandas as pd
from src.stage3a.spec import ROOT, digest, write_json, frozen
from src.data.schema import PARTIES

OUT = ROOT/'outputs/stage3a_v2/universe_20260927'
NEW = ROOT/'data/external/zhizhin_20260927'
OLD = ROOT/'data/raw/20260923T110217085076Z'
CEC = ROOT/'data/external/cik_duma2026_lenoblast_report453_20260927T172843Z.json'
SUMMARY = ROOT/'data/external/cik_duma2026_lenoblast_report453_summary_20260927T172843Z.csv'
ZIP = ROOT/'data/external/kartanarusheniy_dump.zip'
BASE = ROOT/'data/processed/universe_revision_v2/paper_primary.csv.gz'
HIER = ROOT/'data/external/cik_temporal_2026/data/processed/commission_hierarchy.csv.gz'
NAME = 'paper_primary__evidence_20260927'


def records(path):
    with gzip.open(path,'rt') as f:
        values=list(csv.DictReader(f))
    assert len(values)==len({r['uuid'] for r in values}),path
    return {r['uuid']:r for r in values}


def build():
    frozen()
    if (OUT/'universe_freeze.json').exists():
        raise FileExistsError('Universe evidence already frozen')
    OUT.mkdir(parents=True,exist_ok=True)
    j=json.loads(CEC.read_text())
    # Reconstruct hierarchy from retained raw classifier responses, not summary counts.
    nodes={}
    for response in j['classifier_responses'].values():
        assert response['http_status']==200
        raw=json.loads(response['raw_text']);assert raw==response['json']
        stack=[raw]
        while stack:
            n=stack.pop();stack.extend(n.get('children',[]))
            key=n['externalId'];value={k:n.get(k) for k in ['externalId','id','parentId','type','number','name']}
            if key in nodes:assert nodes[key]==value,key
            nodes[key]=value
    uiks={k:v for k,v in nodes.items() if v['type']==5}
    tiks={k:v for k,v in nodes.items() if v['type']==4}
    assert len(uiks)==1020 and len(tiks)==19
    rec={r['uik']['externalId']:r for r in j['records']}
    assert len(rec)==len(j['records']) and set(rec)==set(uiks)
    assert {x['externalId'] for x in j['classifier_nodes'] if x['type']==5}==set(uiks)
    summaries=pd.read_csv(SUMMARY,encoding='utf-8-sig',dtype=str).set_index('uik_uuid')
    assert summaries.index.is_unique and set(summaries.index)==set(uiks)
    report_status=Counter();times=set();observations=0
    hierarchy=[]
    for u,r in rec.items():
        assert uiks[u]['parentId']==r['tik']['id']
        assert r['tik']['externalId'] in tiks
        assert summaries.loc[u,'tik_uuid']==r['tik']['externalId']
        response=r['report_453'];report_status[str(response['http_status'])]+=1
        assert int(summaries.loc[u,'report_http_status'])==response['http_status']
        if response['http_status']==200:
            payload=json.loads(response['raw_text']);assert payload==response['json']
            assert str(payload['reportType'])=='453'
            for cell in payload['body']['commissionClassifiers']:
                assert {'time','votersCount','votersPercent'}<=set(cell)
                times.add(cell['time']);observations+=1
        hierarchy.append(dict(uuid=u,tik_uuid=r['tik']['externalId'],region=r['region']['name'],uik_number=r['uik']['number']))
    pd.DataFrame(hierarchy).sort_values('uuid').to_csv(OUT/'leningrad_live_hierarchy.csv',index=False)
    with zipfile.ZipFile(ZIP) as z:
        assert z.testzip() is None
        inventory=[dict(path=i.filename,bytes=i.file_size,CRC=i.CRC) for i in z.infolist()]
        upstream=json.loads(z.read('kartanarusheniy_dump/manifest.json'))
    write_json(OUT/'incident_package_inventory.json',dict(files=inventory,manifest=upstream,
               role='QUARANTINED_EXTERNAL_EVIDENCE_NOT_USED_FOR_UNIVERSE_OR_MODELS',content_analysis=False))
    manifest=[]
    for path,role in [(CEC,'official CEC temporal/hierarchy; not final counts'),(SUMMARY,'derived browser summary'),
                      (ZIP,'independent incidents; excluded'),(NEW/'uik_protocols.csv.gz','provided Zhizhin final-protocol snapshot'),
                      (NEW/'uik_federal_parties.csv.gz','provided Zhizhin final-party snapshot')]:
        manifest.append(dict(path=str(path.relative_to(ROOT)),sha256=digest(path),bytes=path.stat().st_size,
           role=role,acquisition='user-provided immutable local snapshot',
           retrieved_at_utc=j['metadata']['finished_at_utc'] if path in [CEC,SUMMARY] else None,
           provenance_note='CEC request URLs/timestamps retained in raw; exact Zhizhin retrieval URL/time not supplied' if path!=ZIP else 'package manifest retained; no incident content used'))
    write_json(OUT/'source_manifest.json',dict(sources=manifest,CEC_metadata=j['metadata']))
    changes=[];diffs={};new_maps={}
    for name in ['uik_protocols.csv.gz','uik_federal_parties.csv.gz']:
        a,b=records(OLD/name),records(NEW/name);new_maps[name]=b
        fields=Counter();changed=0
        for u in sorted(a.keys()&b.keys()):
            different=[k for k in a[u] if a[u][k]!=b[u][k]]
            if different:
                changed+=1;fields.update(different)
                changes.append(dict(file=name,uuid=u,changed_fields='|'.join(different),
                                    old_row_sha256=hashlib.sha256(json.dumps(a[u],sort_keys=True,ensure_ascii=False).encode()).hexdigest(),
                                    new_row_sha256=hashlib.sha256(json.dumps(b[u],sort_keys=True,ensure_ascii=False).encode()).hexdigest()))
        diffs[name]=dict(old_rows=len(a),fresh_rows=len(b),added=sorted(b.keys()-a.keys()),removed=sorted(a.keys()-b.keys()),
                        changed_rows=changed,changed_field_counts=dict(fields),leningrad_exact_UUID=len(set(uiks)&b.keys()))
    pd.DataFrame(changes).to_csv(OUT/'source_version_changes.csv',index=False)
    write_json(OUT/'snapshot_comparison.json',diffs)
    f=new_maps['uik_federal_parties.csv.gz'];old_ids=set(records(OLD/'uik_federal_parties.csv.gz'))
    p=new_maps['uik_protocols.csv.gz']
    h=pd.read_csv(HIER,dtype=str).set_index('uik_uuid');assert h.index.is_unique
    base=pd.read_csv(BASE,usecols=['uuid','resolved_region','voters','issued','valid',*PARTIES],dtype={'uuid':str})
    d=base[['uuid','resolved_region','voters']].rename(columns={'resolved_region':'region'})
    additions=[];rejected=[]
    for u in sorted(f.keys()-old_ids):
        row=f[u];num={k:(None if row[k]=='' else int(float(row[k]))) for k in ['voters','issued','valid','invalid',*PARTIES]}
        reasons=[]
        if u not in h.index:reasons.append('hierarchy_unresolved')
        if p.get(u,{}).get('is_deg') not in ['0','False','false']:reasons.append('not_established_paper')
        if row['region'] not in set(base.resolved_region):reasons.append('regional_gate_requires_new_audit')
        n,I,V=num['voters'],num['issued'],num['valid'];counts=[num[k] for k in PARTIES]
        if not (n is not None and I is not None and V is not None and n>0 and 0<=I<=n and 0<V<=I):reasons.append('row_denominator_integrity')
        if any(v is None or v<0 for v in counts) or sum(v or 0 for v in counts)!=V:reasons.append('party_sum_integrity')
        if num['invalid'] is not None and V+num['invalid']>I:reasons.append('known_counted_gt_issued')
        if reasons:rejected.append(dict(uuid=u,reasons=reasons))
        else:additions.append(dict(uuid=u,resolved_region=row['region'],**num))
    assert not rejected,('STOP additional audit needed',rejected)
    added=pd.DataFrame(additions)
    d=pd.concat([d,added[['uuid','resolved_region','voters']].rename(columns={'resolved_region':'region'})],ignore_index=True)
    d['tik_uuid']=d.uuid.map(h.tik_uuid);assert d.tik_uuid.notna().all() and d.uuid.is_unique
    assert all(d.region==d.uuid.map(h.region_name))
    d=d[['uuid','region','tik_uuid','voters']].sort_values('uuid').reset_index(drop=True)
    d.voters=d.voters.astype('int64');d.to_csv(OUT/'design.csv',index=False)
    membership=d[['uuid']].copy();membership['canonical_source']=str(BASE.relative_to(ROOT))
    membership.loc[membership.uuid.isin(added.uuid),'canonical_source']=str((NEW/'uik_federal_parties.csv.gz').relative_to(ROOT))
    membership['source_rule']='accepted counts for existing UUID; fresh main only for previously absent UUID'
    membership.to_csv(OUT/'membership_sources.csv',index=False)
    totals={k:int(base[k].sum()) for k in ['voters','issued','valid',*PARTIES]}
    delta={k:int(added[k].sum()) for k in totals};final={k:totals[k]+delta[k] for k in totals}
    # Registry coverage: added UUIDs are precisely the two formerly absent Bashkortostan UIKs.
    bash=h[h.region_name.eq('Республика Башкортостан')]
    assert len(bash)==3250 and set(added.uuid)<=set(bash.index)
    assert len(set(bash.index)&f.keys())==3250
    assert len(set(uiks)&f.keys())==1
    reconciliation=dict(name=NAME,election_snapshot='20260923T110217085076Z',evidence_freeze='20260927',
       status='REFROZEN_WITH_TWO_NEW_ELIGIBLE_ROWS',rows=len(d),regions=int(d.region.nunique()),tiks=int(d.tik_uuid.nunique()),
       before_rows=len(base),added_rows=len(added),removed_rows=0,rejected_new_rows=rejected,
       aggregates_before=totals,aggregate_additions=delta,aggregates_after=final,
       old_canonical_counts_preserved=True,old_primary_unchanged=True,
       added_UUIDs=added.uuid.tolist(),source_version_conflicts_not_promoted=True,
       leningrad=dict(registry=1020,tiks=19,final=1,missing_final=1019,coverage=1/1020,
                     excluded_existing_rows=1,decision='EXCLUDE_COVERAGE_BELOW_99_PERCENT',
                     report453='TEMPORAL_NOT_FINAL',http_status=dict(report_status),control_times=sorted(times),cells=observations,
                     no_claim_about_unpublished_protocols=True),
       bashkortostan=dict(registry=3250,before=3248,after=3250,coverage_after=1.),
       real_outcome_use='INCLUSION_AND_ARITHMETIC_AUDIT_ONLY_NO_MODEL_EVALUATION',
       policy='docs/universe_policy_v2.json',canonical_policy_note='Preserve accepted counts for existing UUIDs, append new canonical UUIDs; updated counts in two existing UUIDs remain version evidence, not silently substituted')
    write_json(OUT/'reconciliation.json',reconciliation)
    paths=[p for p in OUT.iterdir() if p.is_file()]+[BASE,HIER,ROOT/'docs/universe_policy_v2.json',ROOT/'src/stage3a_v2/audit.py']
    write_json(OUT/'universe_freeze.json',dict(name=NAME,files={str(p.relative_to(ROOT)):digest(p) for p in paths},
               sources={m['path']:m['sha256'] for m in manifest},old_raw_sha256=digest(OLD/'uik_federal_parties.csv.gz')))
    print(json.dumps({k:reconciliation[k] for k in ['status','rows','regions','tiks','added_rows','leningrad']},ensure_ascii=False))


if __name__=='__main__':build()
