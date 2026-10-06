"""Whitelist-only source/design freeze. Never loads issued/valid/party responses."""
from datetime import datetime,timezone
import argparse,json,hashlib,time
import numpy as np
import pandas as pd
from src.data.schema import COUNTS
from src.stage3a_v2.models import LPeer
from .spec import ROOT,OUT,UF,PLAN,CFG,PRIMARY,sha,write,read,verify_primary
from .design import build,support

BASE='data/processed/universe_revision_v2/paper_primary.csv.gz'
ALT='data/processed/universe_revision_v2/paper_primary_alt_conflict_versions.csv.gz'
FRESH='data/external/zhizhin_20260927/uik_federal_parties.csv.gz'
REVISIONS={'2a4215bc-677c-4eea-8bd4-2b79322c2303','76a335c7-fa2a-4e79-9b55-1e8c865ca350'}

def prepare():
    verify_primary();OUT.mkdir(parents=True,exist_ok=False);sources=OUT/'sources';sources.mkdir()
    inputs=set()
    def take(p,columns):
        inputs.add(p);return pd.read_csv(ROOT/p,usecols=columns)
    old=take(BASE,['uuid','source_conflict']);conf=sorted(old.loc[old.source_conflict,'uuid']);assert len(conf)==88
    alt=take(ALT,['uuid','voters','count_version','alternative_replacement_unavailable','selected_source_file','selected_source_sha256','evidence_pointer'])
    assert alt.uuid.is_unique
    selected=alt[alt.uuid.isin(conf)].copy();assert len(selected)==88 and selected.count_version.eq('alternative').all()
    assert not selected.alternative_replacement_unavailable.any()
    for path,h in selected[['selected_source_file','selected_source_sha256']].drop_duplicates().itertuples(index=False,name=None):
        assert sha(ROOT/path)==h;inputs.add(path)
    fresh=take(FRESH,['uuid','voters']);assert fresh.uuid.is_unique
    version=take(str((UF/'source_version_changes.csv').relative_to(ROOT)),['file','uuid','changed_fields'])
    v=version[version.file.eq('uik_federal_parties.csv.gz') & version.changed_fields.ne('district')]
    assert set(v.uuid)==REVISIONS and REVISIONS<=set(conf)
    primary=take(str((UF/'design.csv').relative_to(ROOT)),['uuid','region','tik_uuid','voters'])
    mapping=take(str((UF/'membership_sources.csv').relative_to(ROOT)),['uuid','canonical_source']).rename(columns={'canonical_source':'source_file'})
    assert mapping.uuid.is_unique and set(mapping.uuid)==set(primary.uuid)
    for path in mapping.source_file.unique():inputs.add(path)
    mappings={}
    for name in ['S1','S2a','S2b','S3']:
        m=mapping.copy()
        if name=='S1':m=m[~m.uuid.isin(conf)].copy()
        if name=='S2a':m.loc[m.uuid.isin(conf),'source_file']=ALT
        if name=='S2b':m.loc[m.uuid.isin(REVISIONS),'source_file']=FRESH
        m=m.sort_values('uuid').reset_index(drop=True)
        m['source_sha256']=m.source_file.map({p:sha(ROOT/p) for p in m.source_file.unique()})
        m['selector_commitment']=m.apply(lambda r:hashlib.sha256(json.dumps([r.source_sha256,r.uuid,COUNTS],ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),axis=1)
        m.to_csv(sources/f'{name}_source_mapping.csv',index=False);mappings[name]=m
    pd.DataFrame({'uuid':conf}).to_csv(sources/'conflict_UUIDs.csv',index=False)
    selected.drop(columns=['voters']).to_csv(sources/'S2a_upstream_evidence.csv',index=False)
    v.to_csv(sources/'S2b_revision_metadata.csv',index=False)
    write(sources/'overlap.json',dict(S2a=88,S2b=2,intersection=sorted(REVISIONS),hybrid_allowed=False,
        count_vector_columns=COUNTS,count_vector_binding='Exact source bytes SHA256 + unique UUID + ordered full count-vector column projection. Selector commitment is not a plaintext count-value digest.',
        outcome_values_loaded=False,voters_read_as_design_only=True))
    # Recompute registry gaps before integrity exclusions, from immutable paper UUID observations.
    registry=take('outputs/tables/20260923T112207Z_coverage_validation/registry.csv.gz',['uuid','region'])
    live=take(str((UF/'leningrad_live_hierarchy.csv').relative_to(ROOT)),['uuid','region'])
    assert len(live)==1020 and live.uuid.is_unique and live.region.eq('Ленинградская область').all()
    registry=pd.concat([registry[~registry.region.eq('Ленинградская область')],live],ignore_index=True)
    assert registry.uuid.is_unique
    observed=take('data/processed/20260923T112207Z_coverage_validation/validated_union.csv.gz',['uuid','voting_mode'])
    oldcore=take('data/processed/universe_revision_v2/paper_observed_core.csv.gz',['uuid','resolved_region'])
    newids=set(primary.uuid)-set(old.uuid);assert len(newids)==2 and not newids&set(conf)
    paper=set(observed.loc[observed.voting_mode.eq('paper'),'uuid'])|newids
    records=[]
    for region,g in registry.groupby('region',sort=True):
        ids=set(g.uuid);records.append(dict(region=region,registry_expected=len(ids),observed=len(ids&paper),missing_uiks=len(ids-paper)))
    ledger=pd.DataFrame(records);ledger.to_csv(sources/'S3_completeness.csv',index=False)
    core=pd.concat([oldcore.rename(columns={'resolved_region':'region'}),primary.loc[primary.uuid.isin(newids),['uuid','region']]])
    ids=set(core.loc[core.region.isin(ledger.loc[ledger.missing_uiks.eq(0),'region']),'uuid'])
    if ids!=set(primary.uuid):raise ValueError('S3_IDENTITY_FAILED_MEMBERSHIP_STOP')
    # S3 inherits canonical versions from CURRENT observed core, never fresh revisions.
    pd.testing.assert_frame_equal(mappings['S3'][['uuid','source_file']],mapping.sort_values('uuid').reset_index(drop=True))
    hierarchy=take('data/external/cik_temporal_2026/data/processed/commission_hierarchy.csv.gz',['uik_uuid','tik_uuid','region_name']).set_index('uik_uuid')
    assert hierarchy.index.is_unique
    assert primary.tik_uuid.eq(primary.uuid.map(hierarchy.tik_uuid)).all()
    assert primary.region.eq(primary.uuid.map(hierarchy.region_name)).all()
    main=build(primary);reconciliation={};start=time.monotonic()
    for name in ['S1','S2a','S2b','S3']:
        dest=OUT/'designs'/name;dest.mkdir(parents=True)
        d=primary[primary.uuid.isin(mappings[name].uuid)].copy()
        replacement=selected.set_index('uuid').voters if name=='S2a' else fresh.set_index('uuid').loc[sorted(REVISIONS),'voters'] if name=='S2b' else pd.Series(dtype=float)
        mask=d.uuid.isin(replacement.index);d.loc[mask,'voters']=d.loc[mask,'uuid'].map(replacement)
        c=build(d);d=c['d'];d.to_csv(dest/'design.csv',index=False)
        z=d.assign(fold=c['fold'],cell=c['cell'],eligible=c['eligible'],tik_size=c['size'],equal_cell_weight=0.,cell_weight=0.)
        for (f,j),ix in c['pools'].items():z.loc[ix,'equal_cell_weight']=1/(40*len(ix));z.loc[ix,'cell_weight']=1/(5*len(ix))
        z.to_csv(dest/'reporting_design.csv',index=False);c['pairs'].to_csv(dest/'A_pairs.csv',index=False);c['membership'].to_csv(dest/'A_membership.csv',index=False)
        counts=[]
        if name=='S3':
            for key in ['d','pairs','membership']:pd.testing.assert_frame_equal(c[key],main[key])
            for key in ['fold','cell','eligible','size']:np.testing.assert_array_equal(c[key],main[key])
            counts=['IDENTITY_WITH_PRIMARY; same source selectors, design and deterministic neighbour algorithm']
        else:
            for fold in range(5):
                held=np.flatnonzero((c['fold']==fold)&c['eligible']);model=LPeer();model.d=c['frames'][fold]
                indices=np.full((len(held),32),-1,dtype=np.int64);weights=np.zeros((len(held),32));lengths=np.zeros(len(held),int);levels=[]
                # Exact frozen neighbour function; only design fields exist on this object.
                for k,row in enumerate(held):
                    ix,w,level=model.neighbours(d,int(row));indices[k,:len(ix)]=ix;weights[k,:len(w)]=w;lengths[k]=len(ix);levels.append(level)
                np.savez_compressed(dest/f'neighbours_{fold}.npz',targets=held,indices=indices,weights=weights,lengths=lengths,levels=np.array(levels))
                np.savez_compressed(dest/f'fold_{fold}.npz',training=c['train'][fold],**{f'cell_{j}':c['pools'][fold,j] for j in range(8)})
                counts.append(dict(fold=fold,training=len(model.d),targets=len(held),fallback=pd.Series(levels).value_counts().to_dict()))
                print(json.dumps(dict(stage='design_only',variant=name,fold=fold,targets=len(held))),flush=True)
        s=support(c);aligned=primary.set_index('uuid').loc[d.uuid]
        s.update(variant=name,removed_rows=len(primary)-len(d),added_rows=0,voters_changed_rows=int(np.sum(aligned.voters.to_numpy()!=d.voters.to_numpy())),
          voters_delta=int(d.voters.sum()-primary.voters.sum()),fold_changed_common_rows=int(np.sum(main['fold'][primary.uuid.isin(d.uuid)]!=c['fold'])),
          cell_changed_common_rows=int(np.sum(main['cell'][primary.uuid.isin(d.uuid)]!=c['cell'])),
          new_A_pairs=len(set(zip(c['pairs'].left_uuid,c['pairs'].right_uuid))-set(zip(main['pairs'].left_uuid,main['pairs'].right_uuid))),
          removed_A_pairs=len(set(zip(main['pairs'].left_uuid,main['pairs'].right_uuid))-set(zip(c['pairs'].left_uuid,c['pairs'].right_uuid))),
          fallback=counts,status='IDENTITY_WITH_PRIMARY' if name=='S3' else 'DESIGN_REBUILT',sensitivity_response_reads=0)
        write(dest/'support.json',s);reconciliation[name]=s
    write(OUT/'reconciliation.json',reconciliation)
    write(sources/'provenance.json',dict(authority='Previously frozen source snapshots/official hierarchy; original provenance metadata linked',
        baseline_universe=str(UF.relative_to(ROOT)),new_source_searches=0,source_value_selection=False,generated_at=datetime.now(timezone.utc).isoformat()))
    inputs.update([str((UF/'universe_freeze.json').relative_to(ROOT)),str((UF/'source_manifest.json').relative_to(ROOT)),str((UF/'reconciliation.json').relative_to(ROOT)),'docs/universe_policy_v2.json',str((PRIMARY/'manifest.json').relative_to(ROOT))])
    write(sources/'manifest.json',dict(files={p:sha(ROOT/p) for p in sorted(inputs)},artifacts={str(p.relative_to(ROOT)):sha(p) for p in sorted(sources.iterdir()) if p.is_file()},response_values_opened=False))
    dest=OUT/'freeze';dest.mkdir();write(dest/'config.json',CFG)
    import scipy,sys
    write(dest/'software.json',dict(python=sys.version,numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__,BLAS_threads=1))
    files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'src/stage3a_sensitivity').glob('*.py'))+[PLAN,ROOT/'tests/test_stage3a_sensitivity.py',ROOT/'tests/test_stage3a_real.py',ROOT/'tests/test_stage3a_qualification.py',ROOT/'tests/test_stage3a_v2.py']
    write(dest/'manifest.json',dict(files={str(p.relative_to(ROOT)):sha(p) for p in files},created_at=datetime.now(timezone.utc).isoformat(),before_qualification=True,plan_sha256=sha(PLAN),source_manifest_sha256=sha(sources/'manifest.json'),preparation_seconds=time.monotonic()-start))
    print(json.dumps(dict(status='FROZEN',plan_sha256=sha(PLAN),source_manifest_sha256=sha(sources/'manifest.json'))))

if __name__=='__main__':prepare()
