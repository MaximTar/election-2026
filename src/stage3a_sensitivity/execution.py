"""Future authorized sensitivity release only. Qualification never calls loader."""
from src.analysis import descriptive_env
import argparse,time
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from src.data.schema import PARTIES,COUNTS
from src.stage3a_real import adapters as ad
from src.stage3a_real.spec import CFG as REAL
from src.stage3a_real.execution import write_csv_gzip,frame_records,summaries,commit_package
from .spec import ROOT,OUT,PLAN,PRIMARY,CFG,read,write,sha,verify
from .design import context,support

def load_responses(c,variant,authorized):
    if not authorized:raise ad.Stop('Separate sensitivity authorization required BEFORE response loading')
    if variant not in CFG['variants']:raise ad.Stop('Only frozen distinct variants; S3 is identity')
    m=pd.read_csv(OUT/f'sources/{variant}_source_mapping.csv');d=c['d'];pieces=[]
    assert m.uuid.is_unique and set(m.uuid)==set(d.uuid)
    for path,g in m.groupby('source_file',sort=True):
        if not g.source_sha256.eq(sha(ROOT/path)).all():raise ad.Stop('Source hash mismatch')
        f=pd.read_csv(ROOT/path,usecols=['uuid',*COUNTS])
        if f.uuid.duplicated().any():raise ad.Stop('Duplicate source UUID')
        z=f[f.uuid.isin(g.uuid)].copy()
        if len(z)!=len(g):raise ad.Stop('Missing source UUID')
        pieces.append(z)
    f=pd.concat(pieces).set_index('uuid').loc[d.uuid]
    if not np.array_equal(f.voters.to_numpy(),d.voters.to_numpy()):raise ad.Stop('Frozen voters mismatch')
    known=f.invalid.notna()
    if ((f.loc[known,'invalid']<0)|(f.loc[known,'valid']+f.loc[known,'invalid']>f.loc[known,'issued'])).any():raise ad.Stop('Known invalid count integrity')
    y=dict(origin='authorized_real_loader',synthetic=False,issued=f.issued.to_numpy(),valid=f.valid.to_numpy(),votes=f[list(PARTIES)].to_numpy())
    ad.validate(d,y)
    for k in ['issued','valid','votes']:y[k]=y[k].astype(np.int64)
    return y

def delta_tables(dest):
    a=pd.read_csv(dest/'tables/A_primary.csv');b=pd.read_csv(PRIMARY/'tables/A_primary.csv')
    a=a.merge(b,on='party',suffixes=('_sensitivity','_primary'),validate='one_to_one')
    for col in ['realised_projection_effect','standardized_statistic','raw_add_one_p','holm_p','projection_averaged_descriptive_effect']:
        a[col+'_delta']=a[col+'_sensitivity']-a[col+'_primary']
    a.to_csv(dest/'tables/A_delta.csv',index=False)
    for name,keys in [('response_equal_cell',['method','response']),('cell_equal_fold',['method','cell','response']),('response_row_weighted',['method','response'])]:
        a=pd.read_csv(dest/f'tables/{name}.csv').merge(pd.read_csv(PRIMARY/f'tables/{name}.csv'),on=keys,suffixes=('_sensitivity','_primary'),validate='one_to_one')
        for col in ['below_fraction','inside_fraction','above_fraction','empty_fraction','normalized_width','normalized_interval_score','near_trivial_fraction']:
            x=a[col+'_sensitivity'].to_numpy();y=a[col+'_primary'].to_numpy();finite=np.isfinite(x)&np.isfinite(y)
            value=np.full(len(a),np.nan);value[finite]=x[finite]-y[finite];a[col+'_delta']=value
            a[col+'_delta_status']=np.where(finite,'FINITE',np.where(np.isinf(x)&np.isinf(y),'BOTH_INFINITE_NOT_SUBTRACTED','NONFINITE_NOT_SUBTRACTED'))
        a.to_csv(dest/f'tables/{name}_delta.csv',index=False)

def execute(variant,run_id,authorized):
    if not authorized:raise ad.Stop('Separate sensitivity authorization required BEFORE response loading')
    verify()
    q=read(OUT/'qualification/summary.json')
    if q['variants'].get(variant)!='PASS':raise ad.Stop('Transport NOT_QUALIFIED')
    for path,h in read(OUT/'qualification/manifest.json')['files'].items():
        if sha(ROOT/path)!=h:raise ad.Stop('Qualification evidence mismatch')
    if any(x in run_id for x in ['..','/','\\']) or not run_id:raise ad.Stop('Invalid run ID')
    parent=OUT/'real';parent.mkdir(exist_ok=True);final=parent/run_id;dest=parent/(run_id+'.building')
    if dest.exists() or final.exists():raise ad.Stop('No overwrite, retry or resume')
    dest.mkdir();start=time.monotonic()
    try:
        c=context(variant);y=load_responses(c,variant,True)
        for folder in ['tables/folds','samples','metadata']:(dest/folder).mkdir(parents=True)
        c['d'].assign(fold=c['fold'],cell=c['cell'],eligible=c['eligible']).to_csv(dest/'samples/design_index.csv',index_label='row_index')
        a=ad.association(c['d'],y,c['pairs'],[REAL['namespace'],'A'])
        p=c['pairs'];left=p.left.to_numpy();right=p.right.to_numpy();T=y['issued']/c['d'].voters.to_numpy();Y=y['votes']/y['valid'][:,None]
        averaged=((T[left]-T[right])[:,None]*(Y[left]-Y[right])).sum(0)/(2*len(p))
        rows=[]
        for j,party in enumerate(REAL['party_order']):
            rows.append(dict(party=party,realised_projection_effect=a['effect'][j],standardized_statistic=a['score'][j],raw_add_one_p=a['p_raw'][j],holm_p=a['p_holm'][j],holm_reject=bool(a['p_holm'][j]<=.05),projection_averaged_descriptive_effect=averaged[j],UIKs=2*len(p),pairs=len(p),TIKs=p.tik_uuid.nunique(),regions=p.region.nunique(),voters=int(2*p.voters.sum()),identification_status=a['status']))
        pd.DataFrame(rows).to_csv(dest/'tables/A_primary.csv',index=False);p.to_csv(dest/'samples/A_pairs.csv',index=False)
        from src.stage3a_qualification.spec import plain
        write(dest/'metadata/A_diagnostics.json',plain(a))
        for fold in range(5):
            model=ad.fit_fold(c,y,fold);memo={};held=np.flatnonzero((c['fold']==fold)&c['eligible'])
            matrix=np.full((len(held),99),-1,dtype=np.int64);lengths=np.zeros(len(held),int)
            def stream():
                for k,row in enumerate(held):
                    cal=ad.sample(c,int(row));matrix[k,:len(cal)]=cal;lengths[k]=len(cal)
                    yield from frame_records(c,y,model,ad.target(c,y,model,int(row),cal,memo),cal,fold)
            write_csv_gzip(dest/f'tables/folds/fold_{fold}.csv.gz',stream())
            np.savez_compressed(dest/f'samples/fold_{fold}_calibration.npz',targets=held,members=matrix,lengths=lengths)
        summaries(dest,expected_rows=int(c['eligible'].sum()));delta_tables(dest)
        write(dest/'metadata/support.json',support(c))
        write(dest/'metadata/run.json',dict(variant=variant,contract_sha256=sha(PLAN),source_manifest_sha256=sha(OUT/'sources/manifest.json'),freeze_sha256=sha(OUT/'freeze/manifest.json'),primary_manifest_sha256=sha(PRIMARY/'manifest.json'),generated_at=datetime.now(timezone.utc).isoformat(),new_empirical_calibration=False))
        write(dest/'completion.json',dict(status='COMPLETE_FOR_REVIEW',variant=variant,elapsed_seconds=time.monotonic()-start,automatic_next_stage=False))
        commit_package(dest,final)  # frozen publisher additionally binds original primary contract
        print(str(final))
    except Exception as e:
        write(dest/'ABORTED.json',dict(error=type(e).__name__+': '+str(e),retry=False,partial_release=False));raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['run']);p.add_argument('--variant',choices=CFG['variants'],required=True);p.add_argument('--run-id',required=True);p.add_argument('--authorized-sensitivity-execution',action='store_true');a=p.parse_args();execute(a.variant,a.run_id,a.authorized_sensitivity_execution)
