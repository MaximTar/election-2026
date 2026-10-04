"""Append a publication-engineering stage; never replace a historical publication."""
import copy
import datetime
import importlib.util
import json
import re
from pathlib import Path
from src import smz_stage_registry as registry

ROOT=Path(__file__).resolve().parents[3]
P=Path(__file__).resolve().parent
STAGE='SMZ_SITES_PUBLICATION_DATA_V1_READY'
def sha(p):return registry.sha(p)
def read(p):return json.loads(Path(p).read_text())
def put(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
def rel(p):return str(Path(p).relative_to(ROOT))

def main():
    assert read(P/'checker_results.json')['status']=='PASS'
    assert read(P/'determinism.json')['status']=='PASS'
    assert read(P/'decoder_regression.json')['status']=='PASS'
    before=read(P/'before/outputs/metadata/research_state.json')
    assert read(ROOT/'outputs/metadata/research_state.json')==before
    for name in ['docs/RESEARCH_HANDOFF.md','src/smz_stage_registry.py','src/analysis/research_handoff.py']:
        assert (ROOT/name).read_bytes()==(P/'before'/name).read_bytes()
    reg=registry.load_registry();assert len(reg['stages'])==52
    old_pointer=(ROOT/'src/smz_stage_registry.py').read_text()
    old_package=re.search(r"PACKAGE=ROOT/'([^']+)'",old_pointer).group(1)
    decision={'publication_id':STAGE,'predecessor':before['current_stage'],'published_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'decision':'PASS','state_field':'sites_publication_data_v1','scope':'Only a separately authorized next publication-engineering task. Article and site implementation have not started; roadmap-99 remains paused before item54.',
              'public_manifest_sha256':sha(ROOT/'publication/sites/v1/manifest.json'),
              'public_states':2064,'scenario_frozen':1620,'scenario_public':1620,'additional_frozen':445,'additional_public':444,'additional_internal_excluded':1,
              'card_only_methods':2,'new_scientific_calls':0,'new_fits':0,'new_scientific_states':0,'new_exclusions':0,'universe_changes':0,
              'article_edited':False,'site_implemented':False,'roadmap_99_changed':False,'item54_started':False,
              'formal_roadmap_position':'PAUSED_BEFORE_54_FINALIZE_ARTICLE_STRUCTURE',
              'checker_sha256':sha(P/'checker_results.json'),'determinism_sha256':sha(P/'determinism.json')}
    put(P/'decision.json',decision)
    (P/'publication.py').write_text('''import copy,json
from pathlib import Path
P=Path(__file__).resolve().parent
def build_state(before):
 d=json.loads((P/'decision.json').read_text());assert before['current_stage']==d['predecessor']
 after=copy.deepcopy(before)
 after.update(current_stage=d['publication_id'],last_updated=d['published_at'],safe_to_proceed='YES WITH LIMITATIONS',proceed_scope=d['scope'])
 after[d['state_field']]=d
 after['methodological_decisions'].extend(json.loads((P/'decision_ledger.json').read_text())['decisions'])
 after['open_issues'].append({'id':'SITES_PUBLICATION_EDITORIAL_PENDING','status':'ACCEPTED LIMITATION','issue':'Final reader copy, license/release metadata and future UI review remain separate; no scientific blocker. Large exact sidecars are lazy.','artifact':'publication/sites/v1/CONTRACT.md'})
 return after
''')
    spec=importlib.util.spec_from_file_location('_sites_publication',P/'publication.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    after=module.build_state(before);put(P/'publication/research_state.json',after)
    public_manifest=read(ROOT/'publication/sites/v1/manifest.json')
    total_bytes=sum(v['bytes'] for v in public_manifest['files'].values())+(ROOT/'publication/sites/v1/manifest.json').stat().st_size
    index_bytes=sum(v['bytes'] for k,v in public_manifest['files'].items() if k.startswith('states/'))
    appendix=f'''

## SMZ_SITES_PUBLICATION_DATA_V1_READY — static publication data only

### Analysis universes
Primary paper_primary__evidence_20260927 unchanged:87,736UIKs,84regions,2,818officialTIKs;99,360,758registered voters,55,674,920issued ballots,54,723,201valid votes. DEG outside core and overseas separate. No membership/row/region/TIK/electorate/issued/valid/party-vote or field-semantics change. S1/S2a/S2b remain frozen source views;S1 has87,648UIKs. Cedar primary71,438native/87,736source frame,16,298outside=2,758REGISTERED_LE_100+13,540INVALID_UNKNOWN,exclusive inherited reasons. No new exclusions or collateral region gate.

### Methodological decisions
Scientific choices:0. User requirement:one static API at publication/sites/v1,no article/UI/new science. Source constraint:all1,620canonical published cells exported(1,600joint ABC grid+20D);A/B remain slices,full/native do not create new states. Additional445frozen=444PUBLIC+1INTERNAL;the INTERNAL LS state is excluded. Export2064PUBLICstates,six executable entries,twoCARD_ONLY entries without project numeric result. Researcher/Codex engineering choices:stable reversible publication aliases,lossless lazy gzip integer-string pool,explicit availability,schemas and deterministic generator. No new scenario,fit,sourceview,estimand or control. Model outputs copied from revealed stored records,not article prose. Pipeline decomposition details remain at frozen provenance rather than duplicating large raw payloads.

### Open issues
RESOLVED:static typed export,all required chart inputs,schema/hash/exact-source checks,zeroINTERNALleakage,and byte-identical second generation. Missing requested publication derivatives:NONE. ACCEPTED LIMITATION:reader prose pending,known public-source fidelity gaps and release metadata pending;exact downloads make total package{total_bytes:,}bytes but initial state indices{index_bytes:,}bytes. Do not interpret partial native support as clean/honest territory. No public ROS/LS toggle,K sensitivity,new anchor choice or reference-window preference. External side branch remains CLOSED;G remainsNO_GO;roadmap99unchanged,pausedbefore54,item54notstarted.

### Reviewer attention
Fourestimands remain distinct:CedarE/Lnotpartyshare;1Dcorecenternotnationalcounterfactual;2Dposteriornotfraud/honesty;Dundefinedneverzero;window/anchorgridsnotCI;LOOnotbad-regionclassification;native/sourcecoverage distinct. Default states predeclared,notpreferredafterreveal. Exact integer strings must never pass through JavaScript Number. Available controls are marginal descriptions,not a Cartesian product. Public labels omit branch chronology;original identifiers remain technical provenance. Independent decoder comparison,lossless pool roundtrips,protected-file hashes and separate selfreview completed. Generic handoff dispatcher adds only this new engineering-stage route;prior dispatcher and registry pointer archived byte-for-byte,registry53extends52prefix. No historical report/seal/packet modified.

### Handoff
Stage completed:Publication layer for Sites v1.
Primary universe:paper_primary__evidence_20260927,unchanged.
Input rows:existing1,620scenario cells and445disclosedadditional states;0real source rows passed to kernels.
Output/analysed rows:2,064PUBLICstoredstates;2CARD_ONLYcatalogentries,0fakecalculations.
Rows excluded:0newsourceexclusions;1INTERNALstate omitted solely from public API,not removed from research.
Regions included/excluded:84primary/0newexclusions;own frozen LOO/native frames retained.
New methodological choices:0;serialization and governance engineering choices logged separately.
Important unresolved issues:no scientific/publication-data blocker;copy/release metadata pending.
Reviewer attention:typed results,native support,lazy exact numbers,availability and no internal promotion.
Safe to proceed:YES WITH LIMITATIONS—separate authorized publication-engineering step only;no article/site work begun.
'''
    (P/'handoff_append.md').write_text(appendix)
    handoff=(P/'before/docs/RESEARCH_HANDOFF.md').read_text()+appendix
    (P/'publication/RESEARCH_HANDOFF.md').write_text(handoff)
    # Extend the current baseline checker ONLY for this new engineering stage.
    # Historical scientific-stage dispatch remains byte-preserved in before/.
    dispatcher=(P/'before/src/analysis/research_handoff.py').read_text()
    anchor="    if STATE.exists() and json.loads(STATE.read_text()).get('schema_version',1)>=12:\n"
    assert dispatcher.count(anchor)==1
    route="""    if STATE.exists() and json.loads(STATE.read_text()).get('current_stage')=='SMZ_SITES_PUBLICATION_DATA_V1_READY':
        if not args.check:
            raise SystemExit('Publication data stage is read-only here; use its explicit generator.')
        from src.smz_stage_registry import verify_history
        print(json.dumps(verify_history('SMZ_SITES_PUBLICATION_DATA_V1_READY')))
        import subprocess
        subprocess.run(['/usr/bin/python3','-m','src.publication_sites','check'],check=True)
        return
"""
    new_dispatcher=dispatcher.replace(anchor,route+anchor)
    (ROOT/'src/analysis/research_handoff.py').write_text(new_dispatcher)
    codefiles=list((ROOT/'src/publication_sites').glob('*.py'))+[ROOT/'src/analysis/research_handoff.py']
    put(P/'code_freeze.json',{'files':{rel(f):sha(f) for f in codefiles}})
    put(P/'publication_seal.json',{'status':'PASS','files':{rel(f):sha(f) for f in P.rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.name not in ['manifest.json','publication_seal.json']}})
    reg=copy.deepcopy(reg);reg.update(version='SMZ_IMMUTABLE_STAGE_REGISTRY_53',previous_registry=old_package+'/stage_registry.json',previous_registry_sha256=sha(ROOT/old_package/'stage_registry.json'))
    for path in ['src/smz_stage_registry.py','src/analysis/research_handoff.py']:
        reg['engineering_resolutions'].append({'path':path,'sha256':sha(P/'before'/path),'archive':rel(P/'before'/path)})
    reg['stages'].append({'id':STAGE,'previous_id':before['current_stage'],'package':rel(P),'manifest':rel(P/'publication_seal.json'),'manifest_sha256':sha(P/'publication_seal.json'),'contract_sha256':reg['stages'][-1]['contract_sha256'],
                         'before_state':rel(P/'before/outputs/metadata/research_state.json'),'after_state':rel(P/'publication/research_state.json'),'before_handoff':rel(P/'before/docs/RESEARCH_HANDOFF.md'),'after_handoff':rel(P/'publication/RESEARCH_HANDOFF.md'),
                         'builder':{'path':rel(P/'publication.py'),'sha256':sha(P/'publication.py'),'function':'build_state','arguments':[]},'outcome':'PASS','outcome_path':['sites_publication_data_v1','decision'],
                         'evidence_hashes':{rel(P/x):sha(P/x) for x in ['decision.json','decision_ledger.json','report.md','self_review.json','determinism.json','checker_results.json']}})
    put(P/'stage_registry.json',reg)
    pointer=old_pointer.replace("PACKAGE=ROOT/'"+old_package+"'","PACKAGE=ROOT/'"+rel(P)+"'")
    pointer=re.sub(r"REGISTRY_SHA='[a-f0-9]+'","REGISTRY_SHA='"+sha(P/'stage_registry.json')+"'",pointer,count=1)
    (ROOT/'src/smz_stage_registry.py').write_text(pointer)
    (ROOT/'outputs/metadata/research_state.json').write_bytes((P/'publication/research_state.json').read_bytes())
    (ROOT/'docs/RESEARCH_HANDOFF.md').write_text(handoff)
    print(json.dumps({'status':'PASS','publication':STAGE,'registry_stages':53,'scientific_runs':0,'article_edited':False,'site_implemented':False}))

if __name__=='__main__':main()
