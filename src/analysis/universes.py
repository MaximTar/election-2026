"""Materialize explicit descriptive universes; no electoral selection or anomaly model."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import pandas as pd

from src.analysis.coverage_validation import save_csv
from src.analysis.research_handoff import digest, metrics, read
from src.data.schema import COUNTS, PARTIES

ID = 'universe_revision_v2'
POLICY = Path('docs/universe_policy_v2.json')
BASE = Path('data/processed/20260923T112207Z_coverage_validation')
OLD_TABLES = Path('outputs/tables/20260923T112207Z_coverage_validation')
OUT = Path('data/processed') / ID
TABLES = Path('outputs/tables') / ID
HISTORY = Path('outputs/metadata/history/handoff_setup_20260923')
STATE = Path('outputs/metadata/research_state.json')
HANDOFF = Path('docs/RESEARCH_HANDOFF.md')
REPORT = Path('outputs/reports/20260923_universe_revision_v2.md')


def numeric(frame):
    return frame[COUNTS].replace('', pd.NA).apply(pd.to_numeric, errors='raise').astype('Int64')


def row_flags(frame):
    """All selection predicates are counts/availability checks, never electoral cutoffs."""
    n = numeric(frame)
    parties = n[list(PARTIES)]
    inv = pd.to_numeric(frame.resolved_invalid.replace('', pd.NA)).astype('Int64')
    flags = pd.DataFrame(index=frame.index)
    flags['not_paper'] = frame.voting_mode.ne('paper')
    flags['region_unresolved'] = frame.resolved_region.isna() | frame.resolved_region.isin(['', 'None'])
    flags['voters_not_positive_or_missing'] = ~n.voters.gt(0).fillna(False)
    flags['issued_negative_or_missing'] = ~n.issued.ge(0).fillna(False)
    flags['issued_gt_voters'] = n.issued.gt(n.voters).fillna(False)
    flags['valid_not_positive_or_missing'] = ~n.valid.gt(0).fillna(False)
    flags['valid_gt_issued'] = n.valid.gt(n.issued).fillna(False)
    flags['negative_party_count'] = parties.lt(0).any(axis=1)
    flags['party_sum_uncheckable'] = parties.isna().any(axis=1) | n.valid.isna()
    flags['party_sum_ne_valid'] = parties.sum(axis=1, min_count=len(PARTIES)).ne(n.valid).fillna(False)
    flags['known_counted_gt_issued'] = (n.valid + inv).gt(n.issued).fillna(False)
    return flags


def coverage_mask(frame, threshold):
    """Integer cross multiplication avoids rounded coverage decisions."""
    value = Decimal(str(threshold))
    scale = 10 ** max(0, -value.as_tuple().exponent)
    threshold_scaled = int(value * scale)
    expected = pd.to_numeric(frame.registry_expected).astype('Int64')
    observed = pd.to_numeric(frame.observed).astype('Int64')
    return (expected.gt(0) & (observed * 100 * scale).ge(expected * threshold_scaled)).fillna(False)


def refresh(frame):
    result = frame.copy()
    n = numeric(result)
    inv = pd.to_numeric(result.resolved_invalid.replace('', pd.NA)).astype('Int64')
    result['issued_rate'] = n.issued.astype('Float64') / n.voters.where(n.voters.gt(0))
    result['resolved_counted_ballots'] = n.valid + inv
    result['counted_rate'] = result.resolved_counted_ballots.astype('Float64') / n.voters.where(n.voters.gt(0))
    result['flag_counted_invariant_uncheckable'] = inv.isna() | n.valid.isna() | n.issued.isna()
    result['flag_resolved_invalid_negative'] = inv.lt(0).fillna(False)
    result['rate_metrics_available'] = n.voters.gt(0).fillna(False)
    result['party_share_metrics_available'] = n.valid.gt(0).fillna(False)
    for party, alias in PARTIES.items():
        result['share_valid_' + alias] = n[party].astype('Float64') / n.valid.where(n.valid.gt(0))
    flags = row_flags(result)
    for key in flags:
        result['integrity_' + key] = flags[key]
    result['observed_core_eligible'] = ~flags.any(axis=1)
    result['row_integrity_exclusion_reasons'] = flags.apply(lambda r: '|'.join(r.index[r]), axis=1)
    # Version-specific protocol arithmetic; mirrors may disagree, keep this distinct from inclusion.
    line = lambda k: pd.to_numeric(result[f'alt_line_{k:02}'].replace('',pd.NA)).astype('Int64')
    result['flag_full_protocol_invariants_uncheckable'] = pd.concat([line(k) for k in range(1,13)],axis=1).isna().any(axis=1)
    result['flag_boxes_ne_counted'] = (line(7)+line(8)).ne(line(9)+line(10)).fillna(False)
    result['flag_received_balance'] = (line(2)+line(12)).ne(line(3)+line(4)+line(5)+line(6)+line(11)).fillna(False)
    result['flag_counted_gt_issued'] = flags.known_counted_gt_issued
    result['flag_party_sum_ne_valid'] = flags.party_sum_ne_valid | flags.party_sum_uncheckable
    matches = result.alternative_matches.eq('True') | result.count_version.eq('alternative')
    result['paper_ballot_box_rate'] = ((line(7)+line(8)).astype('Float64') / line(1).where(line(1).gt(0))).where(matches)
    return result


def amounts(frame):
    return metrics(frame)


def differences(before, after):
    before_ids, after_ids = set(before.uuid), set(after.uuid)
    removed = before[~before.uuid.isin(after_ids)]
    added = after[~after.uuid.isin(before_ids)]
    a, b = amounts(before), amounts(after)
    changes = {}
    for label, cols in [('regions',['resolved_region']),('tik_proxy',['resolved_region','tik'])]:
        keys = lambda f: set(map(tuple,f[cols].to_numpy()))
        x,y = keys(before),keys(after)
        changes[label] = dict(input=len(x),removed=len(x-y),added=len(y-x),output=len(y))
        assert len(x)-len(x-y)+len(y-x)==len(y)
    return dict(removed=amounts(removed),added=amounts(added),distinct_key_changes=changes,
        output_minus_input={key:{stat:b['counts'][key][stat]-a['counts'][key][stat] for stat in ['sum_known','missing_rows']} for key in a['counts']})


def partition(name, whole, parts):
    assert len(whole) == sum(len(p) for p in parts.values()), name
    assert set(whole.uuid) == set().union(*(set(p.uuid) for p in parts.values())), name
    a, b = amounts(whole), {key:amounts(p) for key,p in parts.items()}
    for column in a['counts']:
        for stat in ['sum_known','missing_rows']:
            assert a['counts'][column][stat] == sum(v['counts'][column][stat] for v in b.values()), (name,column,stat)
    for cols in [['resolved_region'],['resolved_region','tik']]:
        keys=lambda f:set(map(tuple,f[cols].to_numpy()))
        assert keys(whole)==set().union(*(keys(p) for p in parts.values()))
    return dict(name=name,input=a,parts=b,verified=True,distinct_counts_note='Set union checked; distinct region/TIK counts need not add when parts overlap.')


def build():
    policy = json.loads(POLICY.read_text())
    old = json.loads((HISTORY/'research_state.json').read_text())
    for path, sha in old['input_sha256'].items():
        assert digest(path)==sha, path
    original = read(BASE/'validated_union.csv.gz')
    data = original[original.voting_mode.eq('paper')].copy()
    assert data.uuid.is_unique
    data = data.rename(columns={c:'legacy_'+c for c in ['analysis_ready_subset','row_integrity_ready','subset_exclusion_reasons']})
    data['canonical_source'] = data.record_origin.map({'main':'author_main_snapshot','supplemental_neshodilina':'neshodilina_supplemental'})
    data['canonical_source_file'] = data.record_origin.map({'main':'data/raw/20260923T110217085076Z/uik_federal_parties.csv.gz'})
    supmask = data.record_origin.ne('main')
    data.loc[supmask,'canonical_source_file'] = 'data/raw/validation_20260923T112207Z/' + data.loc[supmask,'evidence_file']
    data['canonical_source_sha256'] = data.canonical_source_file.map({f:digest(f) for f in data.canonical_source_file.unique()})
    data['canonical_source_metadata'] = data.aux_source
    data['alternative_source'] = data.has_alternative.map({'True':'neshodilina','False':''})
    data['source_conflict'] = data.has_alternative.eq('True') & data.alternative_matches.eq('False')
    data['flag_no_alternative'] = data.has_alternative.eq('False')
    data['count_version'] = 'canonical'
    data['selected_source'] = data.canonical_source
    data['selected_source_file'] = data.canonical_source_file
    data['selected_source_sha256'] = data.canonical_source_sha256
    data['selected_protocol_lines_source'] = 'alternative_evidence_not_canonical_primary_document'
    cov = read(OLD_TABLES/'coverage_matrix.csv').rename(columns={'expected_uiks':'registry_expected','expected_uiks_author':'author_expected','observed_paper_uiks':'observed','coverage_pct':'registry_coverage'})
    expected = pd.to_numeric(cov.author_expected.replace('',pd.NA)).astype('Float64')
    cov['author_coverage'] = 100*pd.to_numeric(cov.observed)/expected.where(expected.gt(0))
    cov['denominator_conflict_flag'] = cov.denominator_status.eq('conflict')
    cov['systematic_loss_exclusion'] = cov.region.isin(policy['systematic_loss_exclusions'])
    cov['systematic_loss_evidence'] = cov.region.map(policy['systematic_loss_exclusions']).fillna('not_established_from_available_evidence; not proof of representativeness')
    covcols=['region','author_expected','registry_expected','observed','author_coverage','registry_coverage','missing_uiks','denominator_status','denominator_conflict_flag','in_base_frame','systematic_loss_exclusion','systematic_loss_evidence']
    data=data.merge(cov[covcols].rename(columns={'region':'resolved_region'}),on='resolved_region',how='left',validate='many_to_one')
    assert data.registry_expected.notna().all()
    data['foreign_registry_flag']=data.resolved_region.eq('Иностранные участки')
    data=refresh(data)
    core=data[data.observed_core_eligible].copy()
    numeric_ready=numeric(data)[['voters','issued','valid',*PARTIES]].notna().all(axis=1)
    all_observed=data[numeric_ready].copy()
    base_ok=core.in_base_frame.eq('True') & ~core.systematic_loss_exclusion
    primary=core[base_ok & coverage_mask(core,policy['primary_coverage_percent'])].copy()
    assert set(primary.uuid) <= set(core.uuid)
    supplements=read(BASE/'supplemental_protocols.csv.gz').set_index('uuid')
    assert supplements.index.is_unique
    conflicts=data[data.source_conflict].copy()
    alt=conflicts.copy()
    for column in COUNTS:
        alt[column]=alt.uuid.map(supplements[column])
    assert alt[COUNTS].notna().all().all()
    alt['resolved_invalid']=alt.invalid
    alt['invalid_evidence_recovered']='False'
    alt['count_version']='alternative'
    alt['selected_source']='neshodilina'
    alt['selected_source_file']='data/raw/validation_20260923T112207Z/'+alt.evidence_file
    alt['selected_source_sha256']=alt.evidence_sha256
    alt['selected_protocol_lines_source']='selected_alternative_version'
    alt=refresh(alt)
    replace_ids=set(alt.loc[alt.observed_core_eligible,'uuid']) & set(primary.uuid)
    alt_rep=primary.copy().set_index('uuid',drop=False)
    selected=alt[alt.uuid.isin(replace_ids)].set_index('uuid',drop=False)
    alt_rep.loc[selected.index,selected.columns]=selected
    alt_rep=alt_rep.reset_index(drop=True)
    alt_rep['alternative_replacement_unavailable']=alt_rep.source_conflict & ~alt_rep.uuid.isin(replace_ids)
    assert set(alt_rep.uuid)==set(primary.uuid)
    assert row_flags(alt_rep).any(axis=1).sum()==0
    records=[]; conflict_diffs=[]
    canonical_lookup=conflicts.set_index('uuid');alt_lookup=alt.set_index('uuid')
    for uuid,c in canonical_lookup.iterrows():
        a=alt_lookup.loc[uuid]
        def vector(r): return {PARTIES.get(k,k):None if r[k]=='' else int(r[k]) for k in COUNTS}
        cv,av=vector(c),vector(a)
        ds={k:abs(cv[k]-av[k]) for k in cv if cv[k] is not None and cv[k]!=av[k]}
        records.append(dict(uuid=uuid,region=c.resolved_region,canonical_source=c.canonical_source,
            canonical_source_file=c.canonical_source_file,canonical_sha256=c.canonical_source_sha256,
            alternative_source='neshodilina',alternative_file=a.evidence_file,alternative_sha256=a.evidence_sha256,
            evidence_pointer=a.evidence_pointer,canonical_counts=cv,alternative_counts=av,
            differing_fields=list(ds),absolute_differences=ds,conflict_flag=True,
            canonical_core_eligible=bool(c.observed_core_eligible),alternative_core_eligible=bool(a.observed_core_eligible),
            primary_member=uuid in set(primary.uuid),replaced_in_alt_representation=uuid in replace_ids))
        for key,value in ds.items():conflict_diffs.append(dict(uuid=uuid,region=c.resolved_region,field=key,canonical=cv[key],alternative=av[key],alternative_minus_canonical=av[key]-cv[key],absolute_difference=value))
    frames={
        'paper_observed_core':core,
        'paper_primary':primary,
        'paper_primary_no_source_conflicts':primary[~primary.source_conflict].copy(),
        'paper_primary_alt_conflict_versions':alt_rep,
        'paper_complete_regions':core[pd.to_numeric(core.missing_uiks).eq(0)].copy(),
        'paper_all_observed':all_observed,
        'paper_foreign_observed':all_observed[all_observed.foreign_registry_flag].copy(),
        'paper_strict_complete_regions_legacy':read(BASE/'analysis_ready_paper_subset.csv.gz'),
    }
    for threshold in policy['coverage_sensitivity_percent']:
        name='paper_primary_coverage_'+threshold.replace('.','p')
        frames[name]=core[base_ok & coverage_mask(core,threshold)].copy()
    assert set(frames['paper_primary_coverage_99'].uuid)==set(primary.uuid)
    assert set(frames['paper_strict_complete_regions_legacy'].uuid) <= set(primary.uuid)
    main=data[data.record_origin.eq('main')]
    maincore=core[core.record_origin.eq('main')]
    integrity=main[~main.observed_core_eligible]
    coverage_excluded=maincore[~maincore.uuid.isin(primary.uuid)]
    recovered=primary[~primary.uuid.isin(frames['paper_strict_complete_regions_legacy'].uuid)]
    comparisons=[
        partition('main_paper_to_core',main,{'included':maincore,**{f'reason:{k}':g for k,g in integrity.groupby('row_integrity_exclusion_reasons')}}),
        partition('core_composition',core,{'main_paper':maincore,'foreign_supplemental':core[core.foreign_registry_flag]}),
        partition('main_core_to_primary',maincore,{'included':primary,**{f'coverage:{k}':g for k,g in coverage_excluded.groupby('resolved_region')}}),
        partition('all_paper_to_core',data,{'included':core,**{f'reason:{k}':g for k,g in data[~data.observed_core_eligible].groupby('row_integrity_exclusion_reasons')}}),
        partition('core_to_primary',core,{'included':primary,'outside_base_foreign':core[core.foreign_registry_flag],'coverage_below_99':coverage_excluded}),
        partition('primary_no_conflicts',primary,{'included':frames['paper_primary_no_source_conflicts'],'source_conflicts':primary[primary.source_conflict]}),
        partition('primary_vs_legacy',primary,{'legacy_members':primary[primary.uuid.isin(frames['paper_strict_complete_regions_legacy'].uuid)],'newly_retained':recovered}),
    ]
    # Exact per-region membership and losses, including metadata-only zero-observation territories.
    regions=cov.copy()
    for name,frame in frames.items():regions[name+'_rows']=regions.region.map(frame.groupby('resolved_region').size()).fillna(0).astype(int)
    regions['primary_region_eligible']=regions.in_base_frame.eq('True') & coverage_mask(regions,policy['primary_coverage_percent']) & ~regions.systematic_loss_exclusion
    regions['primary_region_exclusion_reason']=regions.apply(lambda r:'|'.join(([ 'outside_base_frame'] if r.in_base_frame!='True' else [])+(['registry_coverage_below_99'] if not bool(coverage_mask(pd.DataFrame([r]),99).iloc[0]) else [])+(['documented_systematic_loss'] if r.systematic_loss_exclusion else [])),axis=1)
    retained=primary.groupby('resolved_region').agg(rows=('uuid','size'))
    for f in ['voters','issued','valid']:retained[f]=primary.assign(**{f:pd.to_numeric(primary[f])}).groupby('resolved_region')[f].sum()
    exclusions=data[~data.observed_core_eligible][['uuid','record_origin','resolved_region','row_integrity_exclusion_reasons']].copy()
    definitions={
        'paper_observed_core':('all_paper_rows','observed_core_eligible','Row-only requested predicate, including foreign; missing invalid and source conflicts do not exclude.'),
        'paper_primary':('paper_observed_core','in_base_frame and registry_coverage >= 99 and not systematic_loss_exclusion','Domestic descriptive/model default, conditional on purpose and coverage limitations.'),
        'paper_primary_no_source_conflicts':('paper_primary','not source_conflict','Remove individual disputed versions only.'),
        'paper_primary_alt_conflict_versions':('paper_primary','same UUIDs; replace full counts vectors for eligible conflicting alternatives','Paired version sensitivity; no averaging.'),
        'paper_complete_regions':('paper_observed_core','missing_uiks == 0','Coverage sensitivity only, no regional integrity cascade.'),
        'paper_all_observed':('all_paper_rows','numeric voters,issued,valid,all parties known','Local/coverage diagnostics; zero denominators retained with undefined rates; not national representative.'),
        'paper_foreign_observed':('paper_all_observed','foreign_registry_flag','Separate foreign frame, never domestic primary.'),
        'paper_strict_complete_regions_legacy':('main_paper_v1','legacy analysis_ready_subset == True','Deprecated strict regional universe; exactly preserved, never primary.'),
    }
    for t in policy['coverage_sensitivity_percent']:
        definitions['paper_primary_coverage_'+t.replace('.','p')]=('paper_observed_core',f'in_base_frame and registry_coverage >= {t} and not systematic_loss_exclusion','Operational coverage sensitivity; no statistical analysis.')
    universes=[]
    for name,frame in frames.items():
        parent,expression,purpose=definitions[name]
        previous=frames.get(parent,main if parent=='main_paper_v1' else data)
        universes.append(dict(name=name,snapshot=policy['base_snapshot'],evidence_snapshot=policy['evidence_snapshot'],
            artifact=str(OUT/(name+'.csv.gz')),inclusion=expression,exclusion='Complement of inclusion; reasons retained per row/region.',
            policy=str(POLICY),purpose=purpose,previous_universe=parent,
            membership_sha256=hashlib.sha256(('\n'.join(sorted(frame.uuid))+'\n').encode()).hexdigest(),
            **amounts(frame),difference=differences(previous,frame)))
    results=dict(policy=policy,universes=universes,reconciliations=comparisons,
        primary_vs_legacy=differences(frames['paper_strict_complete_regions_legacy'],primary),
        alternative_vs_canonical=differences(primary,alt_rep),
        primary_conflict_rows=int(primary.source_conflict.sum()),conflict_regions=int(primary[primary.source_conflict].resolved_region.nunique()),
        alternative_replacements=len(replace_ids),unavailable_alternative_replacements=int(alt_rep.alternative_replacement_unavailable.sum()),
        primary_invalid_unknown=int(primary.resolved_invalid.eq('').sum()),primary_no_alternative=int(primary.flag_no_alternative.sum()),
        primary_denominator_conflict_rows=int(primary.denominator_conflict_flag.sum()),
        main_integrity_failed=len(integrity),main_integrity_regions=sorted(integrity.resolved_region.unique()),
        primary_excluded_base_regions=regions.loc[regions.in_base_frame.eq('True')&~regions.primary_region_eligible,['region','registry_expected','observed','registry_coverage','primary_region_exclusion_reason']].to_dict('records'),
        absent_special_territories=regions.loc[regions.in_base_frame.eq('False')&pd.to_numeric(regions.observed).eq(0),['region','registry_expected','observed','missing_uiks']].to_dict('records'),
        party_aliases={alias:name for name,alias in PARTIES.items()},no_anomaly_analysis=True)
    tables={'coverage_metadata.csv':regions,'primary_regions.csv':retained.reset_index(),'integrity_exclusions.csv':exclusions,
        'source_conflict_differences.csv':pd.DataFrame(conflict_diffs),
        'primary_newly_retained.csv.gz':recovered[['uuid','resolved_region','voters','issued','valid','source_conflict','flag_counted_invariant_uncheckable']]}
    membership=[]
    for name,frame in frames.items():
        membership.extend(dict(universe=name,uuid=uuid) for uuid in frame.uuid)
    tables['universe_membership.csv.gz']=pd.DataFrame(membership)
    summary=pd.DataFrame([dict(universe=u['name'],rows=u['rows'],regions=u['regions'],tik_proxy_count=u['tik_proxy_count'],electorate=u['counts']['voters']['sum_known'],issued=u['counts']['issued']['sum_known'],valid=u['counts']['valid']['sum_known']) for u in universes])
    tables['universe_summary.csv']=summary
    tables['coverage_threshold_sensitivity.csv']=summary[summary.universe.str.startswith('paper_primary_coverage_')]
    return old,frames,tables,results,records


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run',action='store_true');mode.add_argument('--write',action='store_true');mode.add_argument('--check',action='store_true')
    args=p.parse_args(argv)
    old,frames,tables,results,conflicts=build()
    if args.dry_run:
        print(tables['universe_summary.csv'].to_string(index=False));print(json.dumps({k:results[k] for k in ['main_integrity_failed','primary_conflict_rows','alternative_replacements','primary_excluded_base_regions']},ensure_ascii=False,indent=2));return
    from src.analysis.universe_handoff import make_state, render
    current=json.loads(STATE.read_text()) if args.check else None
    stamp=current['last_updated'] if current else datetime.now(timezone.utc).isoformat()
    if args.write:
        OUT.mkdir(parents=True,exist_ok=True);TABLES.mkdir(parents=True,exist_ok=True)
        for name,frame in frames.items():
            path=OUT/(name+'.csv.gz')
            if name=='paper_strict_complete_regions_legacy':path.write_bytes((BASE/'analysis_ready_paper_subset.csv.gz').read_bytes())
            else:save_csv(frame,path)
        for name,frame in tables.items():save_csv(frame,TABLES/name)
        (TABLES/'source_conflicts.json').write_text(json.dumps(conflicts,ensure_ascii=False,indent=2)+'\n')
        (TABLES/'summary.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    else:
        assert json.loads((TABLES/'summary.json').read_text())==results
        assert json.loads((TABLES/'source_conflicts.json').read_text())==conflicts
        for name,frame in frames.items():
            saved=read(OUT/(name+'.csv.gz'))
            assert list(saved.uuid)==list(frame.uuid),name
            assert amounts(saved)==amounts(frame),name
        assert (OUT/'paper_strict_complete_regions_legacy.csv.gz').read_bytes()==(BASE/'analysis_ready_paper_subset.csv.gz').read_bytes()
    inputs=[POLICY,BASE/'validated_union.csv.gz',BASE/'supplemental_protocols.csv.gz',BASE/'analysis_ready_paper_subset.csv.gz',OLD_TABLES/'coverage_matrix.csv',HISTORY/'research_state.json',HISTORY/'RESEARCH_HANDOFF.md']
    outputs=sorted(OUT.glob('*'))+sorted(TABLES.glob('*'))
    state=make_state(old,results,stamp,{str(f):digest(f) for f in inputs},{str(f):digest(f) for f in outputs})
    markdown=render(state,results)
    if args.write:
        STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n');HANDOFF.write_text(markdown);REPORT.write_text(markdown)
        print(tables['universe_summary.csv'].to_string(index=False));print('Written universes, handoff and state. Legacy/raw preserved; no anomaly analysis.')
    else:
        assert state==current,'Current state differs from recomputed universes, code or artifact hashes.'
        assert HANDOFF.read_text()==markdown and REPORT.read_text()==markdown
        print('PASS: policy, UUID memberships, legacy bytes, all counts/missingness, partitions, thresholds, alternative versions, source conflicts, hashes, handoff/state.')


if __name__=='__main__':main()
