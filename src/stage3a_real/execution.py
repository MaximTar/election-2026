"""Authorization before loading; immutable primary commit; no sensitivities."""
from src.analysis import descriptive_env
import argparse,csv,gzip,hashlib,json,os,time
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from src.data.schema import PARTIES
from src.stage3a_v2.design import context
from src.stage3a_qualification.spec import plain
from .spec import ROOT,OUT,PLAN,UNIVERSE,CFG,sha,write,verify
from . import adapters as ad

def authorize(flag):
    if not flag:raise ad.Stop('Separate explicit user authorization required BEFORE response loading')

def load_responses(c,authorized):
    authorize(authorized)
    membership=pd.read_csv(UNIVERSE/'membership_sources.csv',dtype=str)
    d=c['d'];assert membership.uuid.is_unique and set(membership.uuid)==set(d.uuid)
    uf=json.loads((UNIVERSE/'universe_freeze.json').read_text());hashes={**uf['files'],**uf['sources']}
    pieces=[]
    for path,group in membership.groupby('canonical_source',sort=True):
        p=ROOT/path
        if path not in hashes or sha(p)!=hashes[path]:raise ad.Stop('Canonical source hash mismatch: '+path)
        cols=['uuid','voters','issued','valid',*PARTIES]
        frame=pd.read_csv(p,usecols=cols,dtype={'uuid':str})
        if frame.uuid.duplicated().any():raise ad.Stop('Duplicate source UUID')
        subset=frame[frame.uuid.isin(group.uuid)].copy()
        if len(subset)!=len(group):raise ad.Stop('Missing canonical rows')
        pieces.append(subset)
    frame=pd.concat(pieces).set_index('uuid').loc[d.uuid].reset_index()
    if not np.array_equal(frame.voters.to_numpy(),d.voters.to_numpy()):raise ad.Stop('Changed design voters')
    y=dict(origin='authorized_real_loader',synthetic=False,issued=frame.issued.to_numpy(),
           valid=frame.valid.to_numpy(),votes=frame[list(PARTIES)].to_numpy())
    if list(PARTIES.values())!=CFG['party_order']:raise ad.Stop('Party order mismatch')
    ad.validate(d,y)
    for key in ['issued','valid','votes']:y[key]=y[key].astype(np.int64)
    return y

def frame_records(c,y,model,result,cal,fold):
    row=result['row'];d=c['d'];v=d.iloc[row];cell=int(c['cell'][row]);M=len(c['pools'][fold,cell])
    ix,w,level=model.neighbours(d,row)
    sample_sha=hashlib.sha256(np.asarray(cal,dtype='<i8').tobytes()).hexdigest()
    for method in ['interval','comparator']:
        z=result[method]
        for j,response in enumerate(CFG['responses']):
            yield dict(uuid=v.uuid,region=v.region,tik_uuid=v.tik_uuid,voters=int(v.voters),fold=fold,cell=cell,response=response,
                method='LB' if method=='interval' else 'cell_only',observed=int(result['observed'][j]),
                denominator=int(result['denominator'][j]),lower=int(z['lower'][j]),upper=int(z['upper'][j]),
                position=ad.position(z['lower'][j],z['upper'][j],result['observed'][j]),
                normalized_width=float(z['normalized_width'][j]),interval_score=z['interval_score'][j],
                normalized_interval_score=z['normalized_interval_score'][j],empty=bool(z['empty_interval'][j]),
                score_infinite=bool(z['score_infinite'][j]),near_trivial=bool(z['near_trivial'][j]),
                fallback=level if method=='interval' else 'cell_only_no_training_predictor',
                training_rows=len(c['train'][fold]) if method=='interval' else 0,
                donors=len(ix) if method=='interval' else 0,calibration_m=len(cal),
                calibration_sample_sha256=sample_sha,equal_cell_weight=1/(40*M),cell_weight=1/(5*M))

def write_csv_gzip(p,rows):
    with p.open('wb') as raw, gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as gz:
        import io
        with io.TextIOWrapper(gz,encoding='utf-8',newline='') as f:
            writer=None
            for row in rows:
                if writer is None:writer=csv.DictWriter(f,fieldnames=list(row));writer.writeheader()
                writer.writerow(row)

def summarize_table(frame,keys,weight=None):
    rows=[]
    for labels,g in frame.groupby(keys,sort=True,dropna=False):
        if not isinstance(labels,tuple):labels=(labels,)
        w=np.ones(len(g)) if weight is None else g[weight].to_numpy();w=w/w.sum()
        r=dict(zip(keys,labels));r.update(rows=len(g),voters=int(g.voters.sum()))
        for state in ['below','inside','above','empty']:
            mask=g.position.eq(state).to_numpy();r[state+'_count']=int(mask.sum());r[state+'_fraction']=float(w@mask)
        r['miss_fraction']=1-r['inside_fraction'];r['normalized_width']=float(w@g.normalized_width)
        infinite=g.score_infinite.to_numpy(dtype=bool)
        r['normalized_interval_score']='inf' if infinite.any() else float(w@g.normalized_interval_score)
        r['finite_score_contribution']=float(w@np.where(infinite,0,g.normalized_interval_score.fillna(0)))
        r['score_infinite_count']=int(infinite.sum());r['near_trivial_fraction']=float(w@g.near_trivial.to_numpy())
        r['weighting']='row' if weight is None else weight;rows.append(r)
    return pd.DataFrame(rows)

def summaries(dest,expected_rows=87729):
    paths=sorted((dest/'tables/folds').glob('*.csv.gz'))
    cols=['uuid','region','tik_uuid','voters','fold','cell','response','method','position','normalized_width',
          'normalized_interval_score','score_infinite','near_trivial','equal_cell_weight','cell_weight']
    # Full 2-method census; summary definitions never depend on observed values.
    frame=pd.concat([pd.read_csv(p,usecols=cols) for p in paths],ignore_index=True)
    assert len(frame)==expected_rows*12*2
    assert not frame.duplicated(['uuid','response','method']).any()
    definitions=[('response_equal_cell',['method','response'],'equal_cell_weight'),
        ('cell_equal_fold',['method','cell','response'],'cell_weight'),('response_row_weighted',['method','response'],None),
        ('region_descriptive',['region','method','response'],None),('tik_descriptive',['region','tik_uuid','method','response'],None)]
    for name,keys,w in definitions:summarize_table(frame,keys,w).to_csv(dest/'tables'/f'{name}.csv',index=False)
    for method in ['LB','cell_only']:
        g=frame[frame.method.eq(method)]
        for response in CFG['responses']:
            h=g[g.response.eq(response)];assert len(h)==expected_rows
            np.testing.assert_allclose(h.equal_cell_weight.sum(),1,atol=1e-12)
            for _,z in h.groupby('cell'):np.testing.assert_allclose(z.cell_weight.sum(),1,atol=1e-12)
    write(dest/'summary_integrity.json',dict(status='PASS',output_rows=len(frame),uiKs=expected_rows,methods=2,responses=12,
                                           position_partition='below+inside+above+empty=N'))
    figures(dest)

def figures(dest):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    f=dest/'figures';f.mkdir();responses=CFG['responses']
    data=pd.read_csv(dest/'tables/response_equal_cell.csv');fig,axes=plt.subplots(1,2,figsize=(12,6))
    for method,color in [('LB','steelblue'),('cell_only','darkorange')]:
        d=data[data.method.eq(method)].set_index('response').loc[responses]
        for ax,field in zip(axes,['normalized_width','miss_fraction']):
            ax.plot(d[field],np.arange(12),'o-',label=method,color=color);ax.set_yticks(np.arange(12),responses);ax.set_xlabel(field);ax.legend()
    fig.suptitle('Support-wide equal-cell summaries; misses are descriptive');fig.tight_layout()
    for ext in ['png','svg']:fig.savefig(f/f'response_intervals.{ext}',dpi=160)
    plt.close(fig);data.to_csv(f/'response_intervals_data.csv',index=False)
    cells=pd.read_csv(dest/'tables/cell_equal_fold.csv');fig,axes=plt.subplots(2,2,figsize=(13,9))
    for row,method in enumerate(['LB','cell_only']):
        for col,metric in enumerate(['normalized_width','miss_fraction']):
            mat=cells[cells.method.eq(method)].pivot(index='response',columns='cell',values=metric).loc[responses,list(range(8))]
            im=axes[row,col].imshow(mat,aspect='auto',vmin=0,vmax=1,cmap='viridis');axes[row,col].set_yticks(range(12),responses)
            axes[row,col].set_xticks(range(8));axes[row,col].set_xlabel('Frozen cell');axes[row,col].set_title(method+' '+metric);fig.colorbar(im,ax=axes[row,col])
    fig.tight_layout()
    for ext in ['png','svg']:fig.savefig(f/f'cell_intervals.{ext}',dpi=160)
    plt.close(fig);cells.to_csv(f/'cell_intervals_data.csv',index=False)
    write(f/'metadata.json',dict(interpretation='No calibrated regional/pointwise/anomaly significance',
        response_order=responses,cells=list(range(8)),underlying_tables='CSV beside figures',generated_at=datetime.now(timezone.utc).isoformat()))

def commit_package(dest,final):
    if final.exists():raise ad.Stop('Immutable run already exists')
    files=sorted(p for p in dest.rglob('*') if p.is_file())
    write(dest/'manifest.json',dict(files={str(p.relative_to(dest)):sha(p) for p in files},plan_sha256=sha(PLAN)))
    os.rename(dest,final)

def execute(run_id,authorized):
    authorize(authorized);verify()
    checks=json.loads((OUT/'checks/summary.json').read_text())
    if checks['status']!='PASS':raise ad.Stop('Pre-open equivalence not PASS')
    for path,h in json.loads((OUT/'checks/manifest.json').read_text())['files'].items():
        if sha(ROOT/path)!=h:raise ad.Stop('Pre-open evidence hash mismatch')
    if not run_id or any(x in run_id for x in ['..','/','\\']):raise ad.Stop('Invalid run ID')
    root=ROOT/'outputs/stage3a_real';root.mkdir(exist_ok=True);final=root/run_id;dest=root/(run_id+'.building')
    if final.exists() or dest.exists():raise ad.Stop('No overwrite/resume/retry')
    dest.mkdir();started=time.monotonic()
    try:
        c=context()
        y=load_responses(c,True)
        (dest/'tables/folds').mkdir(parents=True);(dest/'metadata').mkdir();(dest/'samples').mkdir()
        write(dest/'metadata/run.json',dict(run_id=run_id,namespace=CFG['namespace'],universe=CFG['universe'],
            contract_sha256=sha(PLAN),freeze_sha256=sha(OUT/'freeze/manifest.json'),generated_at=datetime.now(timezone.utc).isoformat(),
            preopen_checks_sha256=sha(OUT/'checks/summary.json'),real_response_origin=y['origin'],scientific_specification_changed=False))
        c['d'].assign(fold=c['fold'],cell=c['cell'],eligible=c['eligible']).to_csv(dest/'samples/design_index.csv',index_label='row_index')
        a=ad.association(c['d'],y,c['pairs'],[CFG['namespace'],'A'])
        p=c['pairs'];left=p.left.to_numpy();right=p.right.to_numpy();T=y['issued']/c['d'].voters.to_numpy();Y=y['votes']/y['valid'][:,None]
        averaged=((T[left]-T[right])[:,None]*(Y[left]-Y[right])).sum(0)/(2*len(p))
        records=[]
        for j,party in enumerate(CFG['party_order']):
            records.append(dict(party=party,realised_projection_effect=a['effect'][j],standardized_statistic=a['score'][j],
                raw_add_one_p=a['p_raw'][j],holm_p=a['p_holm'][j],holm_reject=bool(a['p_holm'][j]<=.05),
                projection_averaged_descriptive_effect=averaged[j],UIKs=2*len(p),pairs=len(p),TIKs=p.tik_uuid.nunique(),
                regions=p.region.nunique(),voters=int(2*p.voters.sum()),identification_status=a['status']))
        pd.DataFrame(records).to_csv(dest/'tables/A_primary.csv',index=False)
        write(dest/'metadata/A_diagnostics.json',plain(a));p.to_csv(dest/'samples/A_pairs.csv',index=False)
        for fold in range(5):
            model=ad.fit_fold(c,y,fold);memo={};held=np.flatnonzero((c['fold']==fold)&c['eligible'])
            matrix=np.full((len(held),99),-1,dtype=np.int64);lengths=np.empty(len(held),int)
            def rows():
                for k,row in enumerate(held):
                    cal=ad.sample(c,int(row));matrix[k,:len(cal)]=cal;lengths[k]=len(cal)
                    result=ad.target(c,y,model,int(row),cal,memo)
                    yield from frame_records(c,y,model,result,cal,fold)
            write_csv_gzip(dest/'tables/folds'/f'fold_{fold}.csv.gz',rows())
            np.savez_compressed(dest/'samples'/f'fold_{fold}_calibration.npz',targets=held,members=matrix,lengths=lengths)
            del model,memo
        summaries(dest)
        support=json.loads((ROOT/'outputs/stage3a_v2/freeze/support.json').read_text())
        support['L_B']=support.pop('L');write(dest/'metadata/support.json',support)
        write(dest/'completion.json',dict(status='COMPLETE_FOR_REVIEW',run_id=run_id,elapsed_seconds=time.monotonic()-started,
            interpreted=False,automatic_next_stage=False,source_sensitivities='NOT_RUN_REQUIRES_SEPARATE_TRANSPORT_ROUTE',
            primary_rows=87736,LB_rows=87729,A_rows=3592))
        commit_package(dest,final)
        print(json.dumps(dict(status='COMPLETE_FOR_REVIEW',path=str(final))))
    except Exception as e:
        write(dest/'ABORTED.json',dict(error=type(e).__name__+': '+str(e),automatic_retry=False,partial_release=False))
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['run']);p.add_argument('--run-id',required=True)
    p.add_argument('--authorized-real-stage3a',action='store_true');args=p.parse_args();execute(args.run_id,args.authorized_real_stage3a)
