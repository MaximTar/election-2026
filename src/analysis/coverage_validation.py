"""Stage 1.5: source integrity, explicit evidence overlays, coverage; no anomaly models."""
import argparse
import csv
import gzip
import json
from pathlib import Path
import platform

import pandas as pd

from src.analysis.audit import read_csv, verify_snapshot, write_json
from src.data.ingest import sha256
from src.data.schema import COLUMNS, COUNTS, PARTIES


def save_csv(frame, path):
    if path.suffix == '.gz':
        with path.open('wb') as raw:
            with gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0,compresslevel=6) as gz:
                gz.write(frame.to_csv(index=False,lineterminator='\n').encode())
    else:
        frame.to_csv(path,index=False,lineterminator='\n')


def verify_evidence(path):
    manifest=json.loads((path/'manifest.json').read_text())
    for item in manifest['artifacts']:
        if 'sha256' in item:
            assert sha256(path/item['file'])==item['sha256'], item['file']
    return manifest


def protocol_record(u, parties, region, code, evidence_file, pointer, district=''):
    protocol=u['protocol']
    assert len(protocol)==12 and len(parties)==len(u['votes'])
    assert set(parties)==set(PARTIES)
    # No upstream "suspicious", "clean", "fixed" or electoral ranking fields are read.
    assert all(type(v) is int and v>=0 for v in protocol+u['votes'])
    row=dict(region_code=code,region=region,district=str(district or ''),tik=u['tik'],
             uik=str(u['num']),uuid=u['guid'],voters=str(protocol[0]),
             issued=str(sum(protocol[2:5])),invalid=str(protocol[8]),valid=str(protocol[9]),
             **{p:str(v) for p,v in zip(parties,u['votes'])})
    row.update({f'line_{i:02}':v for i,v in enumerate(protocol,1)})
    row.update(evidence_file=evidence_file,evidence_pointer=pointer,match_method='uuid')
    return row


def field_conflicts(main, alternative):
    """Only compare known main counts; NULL is not an alias for zero."""
    return [c for c in COUNTS if main[c] != '' and int(main[c]) != int(alternative[c])]


def merge_append_only(base, supplemental):
    if base.uuid.duplicated().any() or supplemental.uuid.duplicated().any():
        raise ValueError('Ambiguous UUID; merge is not allowed')
    main=base.copy()
    main['record_origin']='main'
    extra=supplemental.loc[~supplemental.uuid.isin(base.uuid), COLUMNS].copy()
    extra['record_origin']='supplemental_neshodilina'
    return pd.concat([main,extra.sort_values('uuid')],ignore_index=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path,required=True)
    p.add_argument('--latest',type=Path,required=True)
    p.add_argument('--evidence',type=Path,required=True)
    p.add_argument('--output-root',type=Path,default=Path('outputs'))
    p.add_argument('--processed-root',type=Path,default=Path('data/processed'))
    args=p.parse_args()
    base_manifest=verify_snapshot(args.base); verify_snapshot(args.latest)
    em=verify_evidence(args.evidence)
    sid=args.evidence.name.removeprefix('validation_')
    tables=args.output_root/'tables'/f'{sid}_coverage_validation'
    processed=args.processed_root/f'{sid}_coverage_validation'
    tables.mkdir(parents=True,exist_ok=True); processed.mkdir(parents=True,exist_ok=True)
    base=read_csv(args.base/'uik_federal_parties.csv.gz')
    aux=read_csv(args.base/'uik_protocols.csv.gz')
    assert not aux.uuid.duplicated().any()
    published=json.loads((args.base/'shpilkin.json').read_text())
    meta=json.loads((args.evidence/'neshodilina_meta.json').read_text())
    status=json.loads((args.evidence/'neshodilina_status.json').read_text())
    code_by_name={r['name'].strip():str(r['code']) for r in published['regions']}
    expected_by_name={r['name'].strip():r['uik'] for r in published['regions']}
    names_by_code={str(r['code']):r['name'].strip() for r in published['regions']}
    manifest_by_file={r['file']:r for r in em['artifacts']}
    reg_records=[]; sup_records=[]; consistency=[]
    district_by_uuid={}
    for path in sorted(args.evidence.glob('neshodilina_mand_r*.json')):
        doc=json.loads(path.read_text())
        for u in doc['uiks']:
            if u.get('district') is not None:
                district_by_uuid[u['guid']]=(str(u['district']),path.name)
    for region in meta['regions']:
        rid=region['id'];name=region['name'];code=code_by_name.get(name,'')
        rf=f'neshodilina_uiks_r{rid}.json'; ff=f'neshodilina_fed_r{rid}.json'
        roster=json.loads((args.evidence/rf).read_text());fed=json.loads((args.evidence/ff).read_text())
        assert roster['region']==fed['region']==name
        s=next(x for x in status['regions'] if x['id']==rid)
        consistency.append(dict(region=name,roster_rows=len(roster['rows']),expected_status=s['total'],
            federal_rows=len(fed['uiks']),federal_status=s['federal'],
            agrees=len(roster['rows'])==s['total'] and len(fed['uiks'])==s['federal']))
        for idx,row in enumerate(roster['rows']):
            r=dict(zip(roster['cols'],row))
            reg_records.append(dict(uuid=r['guid'],region=name,region_code=code,tik=r['tik'],uik=str(r['num']),
                source_has_federal=r['federal'],source_has_mandate=r['mandate'],evidence_file=rf,
                evidence_pointer=f'/rows/{idx}'))
        for idx,u in enumerate(fed['uiks']):
            sup_records.append(protocol_record(u,fed['parties'],name,code,ff,f'/uiks/{idx}',
                                               district_by_uuid.get(u['guid'],('',))[0]))
    registry=pd.DataFrame(reg_records); supplemental=pd.DataFrame(sup_records)
    assert registry.uuid.is_unique and supplemental.uuid.is_unique
    save_csv(registry,tables/'registry.csv.gz')
    save_csv(pd.DataFrame(consistency),tables/'source_internal_consistency.csv')
    supplemental['evidence_sha256']=supplemental.evidence_file.map(lambda f:manifest_by_file[f]['sha256'])
    save_csv(supplemental,processed/'supplemental_protocols.csv.gz')
    registry_index=registry.set_index('uuid'); alt=supplemental.set_index('uuid')
    data=merge_append_only(base,supplemental)
    auxcols=['uuid','is_deg','source','entered_at','federal_entered_at','repeated']
    data=data.merge(aux[auxcols].rename(columns={c:'aux_'+c for c in auxcols if c!='uuid'}),on='uuid',how='left',validate='one_to_one')
    added=data.record_origin.ne('main')
    data['voting_mode']=data.aux_is_deg.map({'0':'paper','1':'deg'}).fillna('unknown')
    data.loc[added,'voting_mode']='paper'
    data['region_evidence']=data.uuid.map(registry_index.region)
    data['resolved_region']=data.region_code.map(names_by_code)
    data.loc[data.resolved_region.isna(),'resolved_region']=data.loc[data.resolved_region.isna(),'region_evidence']
    data['region_resolution_flag']=data.region_code.eq('')&data.region_evidence.notna()
    data['resolved_region_code']=data.region_code.mask(data.region_code.eq(''),data.uuid.map(registry_index.region_code))
    data['in_base_geographic_frame']=data.resolved_region.isin([k for k,v in expected_by_name.items() if v>0])
    data['resolved_district']=data.district
    data['district_evidence_file']=''
    for i,r in data[data.district.eq('')].iterrows():
        if r.uuid in district_by_uuid:
            value,file=district_by_uuid[r.uuid]
            data.at[i,'resolved_district']=value;data.at[i,'district_evidence_file']=file
    # DEG alternative has no UUID: use a unique (region,district) pair, with full count agreement.
    deg=json.loads((args.evidence/'neshodilina_deg.json').read_text())
    deg_by_key={(r['region'],str(r['district'])):(i,r) for i,r in enumerate(deg['districts']) if r.get('deg')}
    assert len(deg_by_key)==sum(bool(r.get('deg')) for r in deg['districts'])
    overlays=[];conflicts=[]
    for row in data.to_dict('records'):
        evidence=None
        if row['voting_mode']=='paper' and row['uuid'] in alt.index:
            evidence=alt.loc[row['uuid']].to_dict()
        elif row['voting_mode']=='deg':
            hit=deg_by_key.get((row['resolved_region'],row['district']))
            if hit:
                idx,r=hit;pr=r['deg']['fp']
                evidence=protocol_record(dict(guid=row['uuid'],num=int(row['uik']),tik=row['tik'],
                    protocol=pr,votes=r['deg']['f']),deg['parties'],r['region'],row['region_code'],
                    'neshodilina_deg.json',f'/districts/{idx}/deg',row['district'])
                evidence['match_method']='region_and_district_all_known_counts'
        out=dict(uuid=row['uuid'],evidence_file='',evidence_pointer='',evidence_sha256='',match_method='',
                 has_alternative=evidence is not None,alternative_matches=False,conflict_fields='',
                 resolved_invalid=row['invalid'],invalid_evidence_recovered=False)
        if evidence is not None:
            bad=field_conflicts(row,evidence)
            out.update(evidence_file=evidence['evidence_file'],evidence_pointer=evidence['evidence_pointer'],
                       evidence_sha256=manifest_by_file[evidence['evidence_file']]['sha256'],
                       match_method=evidence['match_method'],alternative_matches=not bad,conflict_fields='|'.join(bad))
            for i in range(1,13):out[f'alt_line_{i:02}']=evidence[f'line_{i:02}']
            if bad:
                for c in bad:conflicts.append(dict(uuid=row['uuid'],region=row['resolved_region'],field=c,
                    main_value=row[c],alternative_value=evidence[c],evidence_file=evidence['evidence_file']))
            elif row['invalid']=='':
                out.update(resolved_invalid=evidence['invalid'],invalid_evidence_recovered=True)
        overlays.append(out)
    data=data.merge(pd.DataFrame(overlays),on='uuid',validate='one_to_one')
    data['source_breakdown_label']=data.record_origin.where(added,'main_companion_'+data.aux_source.fillna('unknown'))
    n=data[COUNTS].replace('',pd.NA).astype('Int64')
    inv=data.resolved_invalid.replace('',pd.NA).astype('Int64')
    data['issued_rate']=n.issued.astype('Float64')/n.voters.where(n.voters.gt(0))
    data['resolved_counted_ballots']=n.valid+inv
    data['counted_rate']=data.resolved_counted_ballots.astype('Float64')/n.voters.where(n.voters.gt(0))
    line=lambda i:pd.to_numeric(data[f'alt_line_{i:02}'],errors='coerce').astype('Int64')
    data['paper_ballot_box_rate']=((line(7)+line(8)).astype('Float64')/line(1).where(line(1).gt(0))).where(data.voting_mode.eq('paper')&data.alternative_matches)
    data['flag_counted_gt_issued']=(n.valid+inv).gt(n.issued).fillna(False)
    data['flag_party_sum_ne_valid']=n[list(PARTIES)].sum(axis=1,min_count=len(PARTIES)).ne(n.valid).fillna(True)
    data['flag_boxes_ne_counted']=(line(7)+line(8)).ne(line(9)+line(10)).fillna(False)
    data['flag_received_balance']=(line(2)+line(12)).ne(line(3)+line(4)+line(5)+line(6)+line(11)).fillna(False)
    save_csv(pd.DataFrame(conflicts,columns=['uuid','region','field','main_value','alternative_value','evidence_file']),tables/'source_conflicts.csv')
    save_csv(data[added],processed/'supplemental_added_rows.csv.gz')
    paper=data[data.voting_mode.eq('paper')]
    coverage=[];missing=[];tik_rows=[]
    for name,g in registry.groupby('region',sort=True):
        observed=paper[paper.resolved_region.eq(name)]
        expected_ids=set(g.uuid);present=set(observed.uuid);not_present=expected_ids-present
        original=observed[observed.record_origin.eq('main')]
        for r in g[g.uuid.isin(not_present)].to_dict('records'):
            missing.append({**r,'reason':'absent_from_main_and_available_supplemental'})
        coverage.append(dict(region=name,region_code=code_by_name.get(name,''),
            expected_uiks=len(g),expected_uiks_author=expected_by_name.get(name),
            observed_paper_uiks=len(present&expected_ids),observed_paper_main=len(original),
            supplemental_added=len(observed)-len(original),missing_uiks=len(not_present),
            coverage_pct=100*len(present&expected_ids)/len(g) if len(g) else None,
            missing_pct=100*len(not_present)/len(g) if len(g) else None,
            observed_outside_registry=len(present-expected_ids),
            source_breakdown=json.dumps(observed.source_breakdown_label.value_counts().to_dict(),ensure_ascii=False,sort_keys=True),
            expected_source='neshodilina_UUID_registry',in_base_frame=expected_by_name.get(name,0)>0))
        for tik,gg in g.groupby('tik',sort=True):
            ids=set(gg.uuid)
            tik_rows.append(dict(region=name,tik=tik,expected_uiks=len(ids),observed_paper_uiks=len(ids&present),
                                 missing_uiks=len(ids-present),coverage_pct=100*len(ids&present)/len(ids)))
    cov=pd.DataFrame(coverage)
    cov['denominator_status']='agreement'
    cov.loc[cov.expected_uiks_author.isna(),'denominator_status']='outside_original_frame'
    cov.loc[cov.expected_uiks_author.notna()&cov.expected_uiks.ne(cov.expected_uiks_author),'denominator_status']='conflict'
    # Explicit UUID evidence, not a geographic inference: this previously unassigned
    # main commission belongs to the alternative Karelia roster, which has 473 UUIDs.
    karelia_uuid='eda740cd-03d4-49fb-94ad-06273cc13303'
    if (karelia_uuid in registry_index.index and registry_index.loc[karelia_uuid,'region']=='Республика Карелия'
            and len(base.loc[base.uuid.eq(karelia_uuid)&base.region_code.eq('')])==1):
        cov.loc[cov.region.eq('Республика Карелия')&cov.expected_uiks.eq(473)&cov.expected_uiks_author.eq(472),
                'denominator_status']='reconciled_by_explicit_Karelia_UUID'
    cov['missing_vs_author_denominator']=(cov.expected_uiks_author-cov.observed_paper_uiks).clip(lower=0)
    save_csv(cov,tables/'coverage_matrix.csv')
    save_csv(cov.sort_values(['missing_uiks','region'],ascending=[False,True]),tables/'coverage_rank_absolute.csv')
    save_csv(cov.sort_values(['missing_pct','missing_uiks'],ascending=[False,False]),tables/'coverage_rank_relative.csv')
    save_csv(pd.DataFrame(tik_rows),tables/'coverage_tik.csv')
    save_csv(pd.DataFrame(missing),tables/'missing_registry_uiks.csv.gz')
    # Conservative readiness uses integrity and coverage only, never party shares or rate thresholds.
    data['row_integrity_ready']=(data.voting_mode.eq('paper')&data.alternative_matches&inv.notna()
        &n.voters.ge(0)&n.issued.le(n.voters)&~n.lt(0).any(axis=1)&~data.flag_counted_gt_issued
        &~data.flag_party_sum_ne_valid&~data.flag_boxes_ne_counted&~data.flag_received_balance
        &data.resolved_region.notna()).fillna(False)
    region_integrity=paper.assign(row_ready=data.loc[paper.index,'row_integrity_ready']).groupby('resolved_region').row_ready.all()
    ready_regions=set(cov.loc[cov.in_base_frame&cov.missing_uiks.eq(0)&cov.observed_outside_registry.eq(0)
        &cov.denominator_status.isin(['agreement','reconciled_by_explicit_Karelia_UUID']),'region'])
    ready_regions &= set(region_integrity[region_integrity].index)
    data['analysis_ready_subset']=data.row_integrity_ready&data.resolved_region.isin(ready_regions)&n.voters.gt(0)&n.valid.gt(0)
    reasons=[]
    for r in data.to_dict('records'):
        why=[]
        if r['voting_mode']!='paper':why.append('DEG_or_unknown_semantics')
        if not r['in_base_geographic_frame']:why.append('outside_base_geographic_frame')
        if not r['has_alternative']:why.append('no_alternative_protocol')
        elif not r['alternative_matches']:why.append('conflicting_source_versions')
        if r['resolved_invalid']=='':why.append('invalid_unknown')
        if int(r['voters'])==0 or int(r['valid'])==0:why.append('undefined_rate_or_share_denominator')
        for flag in ['flag_counted_gt_issued','flag_party_sum_ne_valid','flag_boxes_ne_counted','flag_received_balance']:
            if r[flag]:why.append(flag)
        if r['resolved_region'] not in ready_regions:why.append('region_not_fully_covered_and_integrity_verified')
        reasons.append('|'.join(why))
    data['subset_exclusion_reasons']=reasons
    save_csv(data,processed/'validated_union.csv.gz')
    save_csv(data[data.analysis_ready_subset],processed/'analysis_ready_paper_subset.csv.gz')
    save_csv(data[['uuid','record_origin','resolved_region','voting_mode','analysis_ready_subset','subset_exclusion_reasons']],tables/'subset_membership.csv.gz')
    save_csv(pd.DataFrame({'region':sorted(ready_regions)}),tables/'analysis_ready_regions.csv')
    original=data[data.record_origin.eq('main')].copy()
    original['invalid_missing']=original.invalid.eq('')
    original['federal_source_date']=original.aux_federal_entered_at.fillna('').str.slice(0,10).replace('','UNKNOWN')
    original['district_missing']=original.district.eq('')
    original['region_code_missing']=original.region_code.eq('')
    original['issued_equals_valid']=original.issued.eq(original.valid)
    groupings={'region':['resolved_region'],'source':['aux_source'],'mode':['voting_mode'],
        'region_source_mode':['resolved_region','aux_source','voting_mode'],
        'protocol_date_source_mode':['federal_source_date','aux_source','voting_mode'],
        'structural_fields':['district_missing','region_code_missing','aux_repeated','issued_equals_valid']}
    for label,cols in groupings.items():
        t=original.groupby(cols,dropna=False).agg(rows=('uuid','size'),invalid_missing=('invalid_missing','sum'),
            recovered_from_explicit_evidence=('invalid_evidence_recovered','sum')).reset_index()
        t['missing_pct']=100*t.invalid_missing/t.rows
        save_csv(t,tables/f'invalid_missing_by_{label}.csv')
    numeric_profile=[]
    for absent,g in original.groupby('invalid_missing'):
        for field in COUNTS:
            values=pd.to_numeric(g[field],errors='coerce')
            numeric_profile.append(dict(invalid_missing=bool(absent),field=field,rows=len(g),
                known=int(values.notna().sum()),minimum=values.min(),maximum=values.max(),
                mean=values.mean(),median=values.median()))
    save_csv(pd.DataFrame(numeric_profile),tables/'invalid_missing_numeric_profile.csv')
    save_csv(original[original.invalid_missing][['uuid','resolved_region','voting_mode','aux_source','aux_federal_entered_at',
        'invalid','resolved_invalid','invalid_evidence_recovered','alternative_matches','conflict_fields','evidence_file','evidence_pointer']],tables/'invalid_evidence.csv.gz')
    origviol=(pd.to_numeric(base.valid)+pd.to_numeric(base.invalid,errors='coerce')>pd.to_numeric(base.issued))
    violations=original[original.uuid.isin(base.loc[origviol,'uuid'])].copy()
    violations['violation_amount']=pd.to_numeric(violations.valid)+pd.to_numeric(violations.invalid)-pd.to_numeric(violations.issued)
    save_csv(violations[[*COLUMNS,'aux_source','aux_federal_entered_at','violation_amount','alternative_matches',
        'evidence_file','evidence_pointer',*[f'alt_line_{i:02}' for i in range(1,13)]]],tables/'arithmetic_evidence.csv')
    save_csv(original[original.district.eq('')][['uuid','region','tik','uik','district','resolved_district','district_evidence_file',
        'aux_source','aux_entered_at','aux_federal_entered_at','has_alternative']],tables/'district_missing_evidence.csv')
    save_csv(original[original.region_code.eq('')][['uuid','region_code','region','resolved_region_code','resolved_region',
        'region_resolution_flag','region_evidence','evidence_file','evidence_pointer']],tables/'region_missing_evidence.csv')
    # Independent CSV reader confirms the region is absent before pandas/join/normalisation.
    with gzip.open(args.base/'uik_federal_parties.csv.gz','rt',encoding='utf-8',newline='') as f:
        direct=list(csv.DictReader(f))
    len_ids=set(registry.loc[registry.region.eq('Ленинградская область'),'uuid'])
    len_checks=dict(raw_rows=len(direct),raw_region_code_47=sum(r['region_code']=='47' for r in direct),
        raw_region_name_matches=sum('ленинград' in r['region'].lower() for r in direct),
        raw_district_112_113_114=sum(r['district'] in ['112','113','114'] for r in direct),
        raw_leningrad_registry_uuid_matches=sum(r['uuid'] in len_ids for r in direct),
        companion_leningrad_registry_uuid_matches=int(aux.uuid.isin(len_ids).sum()),
        companion_leningrad_uuid_without_main=int((aux.uuid.isin(len_ids)&~aux.uuid.isin(base.uuid)).sum()),
        processed_original_cells_preserved=data.iloc[:len(base)][COLUMNS].fillna('').astype('string').equals(base),
        latest_csv_identical=gzip.decompress((args.base/'uik_federal_parties.csv.gz').read_bytes())==gzip.decompress((args.latest/'uik_federal_parties.csv.gz').read_bytes()),
        latest_companion_identical=gzip.decompress((args.base/'uik_protocols.csv.gz').read_bytes())==gzip.decompress((args.latest/'uik_protocols.csv.gz').read_bytes()),
        recovered_leningrad_rows=int((data.resolved_region.eq('Ленинградская область')&added).sum()))
    write_json(tables/'leningrad_validation.json',len_checks)
    # Do not infer universal NULL semantics from the matched sample.
    summary=dict(base_snapshot=base_manifest['snapshot_id'],latest_snapshot=args.latest.name,evidence_snapshot=args.evidence.name,
        union_rows=len(data),main_rows=len(base),supplemental_rows=len(supplemental),supplemental_added=int(added.sum()),
        supplemental_added_base_frame=int((added&data.in_base_geographic_frame).sum()),
        supplemental_added_outside_frame=int((added&~data.in_base_geographic_frame).sum()),
        supplemental_added_base_frame_zero_counts=int((added&data.in_base_geographic_frame&n[COUNTS].eq(0).all(axis=1)).sum()),
        invalid_original_missing=int(original.invalid_missing.sum()),
        invalid_recovered=int(original.invalid_evidence_recovered.sum()),
        invalid_remaining_unknown=int(original.resolved_invalid.eq('').sum()),
        invalid_recovered_paper=int((original.invalid_evidence_recovered&original.voting_mode.eq('paper')).sum()),
        invalid_recovered_deg=int((original.invalid_evidence_recovered&original.voting_mode.eq('deg')).sum()),
        source_conflict_rows=int((original.has_alternative&~original.alternative_matches).sum()),
        source_conflict_fields=len(conflicts),paper_main_without_alternative=int((original.voting_mode.eq('paper')&~original.has_alternative).sum()),
        district_missing=int(original.district.eq('').sum()),district_missing_resolved=int((original.district.eq('')&original.resolved_district.ne('')).sum()),
        region_missing_resolved=int(original.region_resolution_flag.sum()),
        registry_rows=len(registry),registry_regions=registry.region.nunique(),
        expected_original_national=published['progress']['total'],expected_original_regions=sum(expected_by_name.values()),
        expected_registry_base_frame=int(cov.loc[cov.in_base_frame,'expected_uiks'].sum()),
        paper_union_base_frame=int((data.voting_mode.eq('paper')&data.in_base_geographic_frame).sum()),
        missing_registry_base_frame=int(cov.loc[cov.in_base_frame,'missing_uiks'].sum()),
        analysis_ready_rows=int(data.analysis_ready_subset.sum()),analysis_ready_regions=len(ready_regions),
        alternative_registries_stable=(args.evidence/'neshodilina_meta.json').read_bytes()==(args.evidence/'neshodilina_meta_after.json').read_bytes(),
        all_regions_internally_consistent=bool(pd.DataFrame(consistency).agrees.all()),
        conclusion='B',no_anomaly_models=True)
    write_json(tables/'summary.json',summary)
    write_json(tables/'run_manifest.json',dict(inputs={str(args.base/'manifest.json'):sha256(args.base/'manifest.json'),
        str(args.latest/'manifest.json'):sha256(args.latest/'manifest.json'),str(args.evidence/'manifest.json'):sha256(args.evidence/'manifest.json')},
        code_sha256={str(path):sha256(path) for path in sorted(Path('src').rglob('*.py'))},
        python=platform.python_version(),pandas=pd.__version__,
        processed_sha256={str(path):sha256(path) for path in sorted(processed.glob('*.csv.gz'))}))
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
