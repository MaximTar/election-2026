"""Entirely generated mock bundles. No project source-file I/O."""
import copy,json,gzip
from src.smz_real_adapter import adapter as a
from src.smz_real_adapter.qualification import mock_fixture,csv_bytes
from src.smz_real_adapter.plans import compile_plan

def generated(n,large=False):
    _,pb,_=mock_fixture();p=json.loads(pb);header=next(iter(p['source_files'].values()))['header']
    base=[];geo={};tik=0;pos=0;size=19
    for i in range(n):
        if pos==size:tik+=1;pos=0;size=(401+(tik*17%127)) if large else 19+(tik*17%25)
        voters=900+(tik*113%1500) if tik%3 else 700+(i*37+tik*17)%1800
        issued=voters*(15+70*pos//max(1,size-1))//100;valid=issued-7-(i%13)
        focal=valid*(25+(i*11+tik*7)%41)//100;other=valid-focal
        parties=[];j9=0
        for j in range(10):
            if j==1:parties.append(focal)
            else:parties.append(other//9+(j9<other%9));j9+=1
        factor=10**30+2*i+1 if large else 1
        r={k:'' for k in header};r.update(uuid=f'mock:u{i:07}',voters=str(voters*factor),issued=str(issued*factor),valid=str(valid*factor),invalid=str(3*factor) if i%2 else '')
        r.update({k:str(v*factor) for k,v in zip(a.COLUMNS,parties)});base.append(r)
        geo[r['uuid']]=(f'mock:r{tik%84:03}',f'mock:t{tik:05}');pos+=1
    variants={'primary':base,'S1':base[88 if n>=10000 else 2:],'S2a':[],'S2b':[]}
    for name,step,factor in [('S2a',997,2),('S2b',881,3)]:
        for i,original in enumerate(base):
            r=dict(original)
            if i%step==0:
                for k in ('voters','issued','valid',*a.COLUMNS):r[k]=str(int(r[k])*factor)
                if r['invalid']:r['invalid']=str(int(r['invalid'])*factor)
                if name=='S2b':r['voters']=str(int(r['voters'])+13)
            variants[name].append(r)
    files={};metadata={};p['source_files']={};p['variants']={};p['metadata_files']={}
    for variant,rows in variants.items():
        name=f'mock://{variant}.csv.gz';blob=gzip.compress(csv_bytes(header,rows),mtime=0);files[name]=blob;h=a.digest(blob)
        p['source_files'][name]=dict(sha256=h,header=header,compression='gzip')
        mapping=[];design=[]
        for r in rows:
            uuid=r['uuid'];region,tik=geo[uuid]
            mapping.append(dict(uuid=uuid,source_file=name,source_sha256=h,selector_commitment=a.digest(json.dumps([h,uuid,a.COUNTS],ensure_ascii=False,separators=(',',':')).encode())))
            design.append(dict(uuid=uuid,region=region,tik_uuid=tik,voters=int(r['voters'])))
        mp=f'mock://{variant}_mapping.csv';dp=f'mock://{variant}_design.csv'
        for path,rr in ((mp,mapping),(dp,design)):metadata[path]=csv_bytes(list(rr[0]),rr);p['metadata_files'][path]=a.digest(metadata[path])
        p['variants'][variant]=dict(mapping_path=mp,mapping_sha256=a.digest(metadata[mp]),mapping_source_column='source_file',design_path=dp,design_sha256=a.digest(metadata[dp]),expected_rows=len(rows),universe='ARCH_B_GENERATED_N'+str(n)+'_'+variant)
    pb=a.canonical(p).encode();plans={v:compile_plan(pb,v,metadata.__getitem__,expected_profile_sha256=a.digest(pb)) for v in a.VARIANTS}
    manifest=a.canonical(dict(origin='SMZ_GENERATED_MOCK_SOURCE_V1',plans=plans)).encode()
    return a.MockBundle(manifest,tuple(sorted(files.items()))),dict(generator='ARCH_B_DETERMINISTIC_1',n=n,large_products=large,profile_sha256=a.digest(pb),bundle_sha256=a.digest(manifest),rows={v:len(r) for v,r in variants.items()},regions=len({v[0] for v in geo.values()}),TIKs=len({v[1] for v in geo.values()}))
