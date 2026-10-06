"""Publish preparation/qualification facts only; preserve all real-primary results."""
import argparse,json,shutil
from datetime import datetime,timezone
from .spec import ROOT,OUT,PLAN,PRIMARY,CFG,verify,read,write,sha
STATE=ROOT/'outputs/metadata/research_state.json';HAND=ROOT/'docs/RESEARCH_HANDOFF.md';GOV=ROOT/'outputs/stage3a/governance_manifest.json'
REPORT=ROOT/'outputs/reports/20260928_stage3a_sensitivity_transport_qualification.md'

def command(v):return f'OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python3 -m src.stage3a_sensitivity.execution run --variant {v} --run-id 20260928_{v.lower()}_sensitivity_01 --authorized-sensitivity-execution'

def publish():
    verify();q=read(OUT/'qualification/summary.json');r=read(OUT/'reconciliation.json')
    pub=OUT/'publication';pub.mkdir(exist_ok=False);before=pub/'before';before.mkdir()
    for p in [STATE,HAND,GOV]:shutil.copy2(p,before/p.name)
    ready=dict(STAGE3A_SENSITIVITY_CONTRACT_FROZEN=True,variants=q['variants'],S3_STATUS=r['S3']['status'],
      SAFE_TO_OPEN_STAGE3A_SENSITIVITIES=all(v=='PASS' for v in q['variants'].values()) and r['S3']['status']=='IDENTITY_WITH_PRIMARY',
      plan_sha256=sha(PLAN),source_manifest_sha256=sha(OUT/'sources/manifest.json'),freeze_manifest_sha256=sha(OUT/'freeze/manifest.json'),qualification_manifest_sha256=sha(OUT/'qualification/manifest.json'),
      sensitivity_response_reads=0,execution_authorized=False,commands={v:command(v) for v in CFG['variants'] if q['variants'][v]=='PASS'})
    write(OUT/'readiness.json',ready)
    write(pub/'self_review.json',dict(status='PASS',separate_review=True,new_primary_exclusions=0,base_changes=0,
      counts_changed_in_sensitivity_versions='Bound to source selectors; issued/valid/party values not read',
      design_deltas=r,overlap='S2b two UUIDs both in S2a88; no hybrid',S3='Canonical source/UUID/design identity, no stochastic rerun',
      selection='Source-based, not ignored by assumption: conditional exchangeability only',
      uncertainty='No new empirical calibration or pointwise LB guarantee; no across-variant FWER',
      history='Original LFAIL/APASS/LBPASS/RETAIN/H computational abort/HC final numericalFAIL preserved'))
    lines=['| Variant | Rows | Regions | TIKs | Voters | A rows/pairs/TIK/regions | LB rows/TIK | LB excluded rows/voters | Voters delta |','|---|---:|---:|---:|---:|---|---|---|---:|']
    for v,s in r.items():
        a=s['A'];b=s['LB'];lines.append(f"| {v} | {s['rows']} | {s['regions']} | {s['tiks']} | {s['voters']} | {a['rows']}/{a['pairs']}/{a['tiks']}/{a['regions']} | {b['rows']}/{b['tiks']} | {b['excluded_rows']}/{b['excluded_voters']} | {s['voters_delta']} |")
    text=f'''# Stage3A sensitivity source/design freeze and transport qualification

Preparation/qualification only. Sensitivity election responses NOT_READ; no real models.
Plan SHA256:{ready['plan_sha256']}
Source mapping manifest SHA256:{ready['source_manifest_sha256']}
Freeze manifest SHA256:{ready['freeze_manifest_sha256']}
Qualification manifest SHA256:{ready['qualification_manifest_sha256']}

## Source/design reconciliation

{chr(10).join(lines)}

Primary87736/84/2818 immutable. S1 removes only original88conflicts, keeps two new rows.
S2a full historical alternatives at88UUIDs; S2b full fresh vectors at2overlappingUUIDs;
no hybrid. Count-vector bindings use exact file hash+uniqueUUID+full ordered columns,
not a claimed hash of decoded numerical values. Only voters read as design covariate.
Source provenance and byte hashes retained; no new source searches/choices.
S3={r['S3']['status']}; exact current primary canonical source selectors and design,
not old84486/83universe. Registry completeness precedes row integrity and does not resolve
Primorye/source-frame caveats. No S3model/stochastic execution command.

## Qualification

Statuses:{json.dumps(q['variants'])}. Fixtures PASS={q['fixtures_PASS']}.
Unique synthetic datasets:{q['synthetic_datasets']}; A comparisons:{q['A_comparisons']};
LB targets:{q['LB_target_comparisons']}. Elapsed:{q['elapsed_seconds']:.3f}s.
N1replays are additional same-seed computations, not additional independent datasets.
Original numerical tolerance unchanged. All outcomes in qualification are synthetic.
No rejection-rate/coverage empirical calibration claim. Any failure stops that variant;
no repair/retry. Full ledger,raw comparison artifacts,fixtures and hashes retained.

A transport: conditional validity under same joint TIK orientation-exchangeability null
on selected source version/design. Measurement selection is not proven ignorable.
Holm within10parties only, no jointFWER acrossprimary/variants. LB finite-population expected
cell-average rank coverage only, not realised/local/pointwise/density or usefulness PASS.
Changed folds/order/pools can change projection/calibration randomness; deltas not causal.
Primary results never replaced; no new discovery by convenient variant.

## Future commands — NOT EXECUTED

{chr(10).join('```sh'+chr(10)+x+chr(10)+'```' for x in ready['commands'].values())}

Separate user authorization still required. Guarded loading first verifies source/qualification
hashes/count integrity,atomic immutable package before interpretation. Only frozen response/
cell/region/TIK summaries/comparator and primary-metric deltas; no maps/toplists/localtests.
Failure =>ABORTED/STOP,no silent exclusion/rerun. No H-C,newmodel,integration/counterfactual.
After promised sensitivities Stage3A closes; integration requires separate task.

## Governance / self-review

User requirement: exact variants,one bounded qualification,no real response loading. Source
constraint: overlapping version evidence,current completeness. Researcher implementation:
immutable locator commitments,unchanged cached neighbours,proof/reference checks and guarded
future adapter. No scientific algorithm/threshold change. Design quantities reconciled above;
issued/valid/party deltas intentionally NOT_READ,not zero. Alternative hybrids,newseeds and
calibration-until-PASS prohibited. Previous universe definitions/results preserved.
Separate self-review in publication/self_review.json. Current scoped checker:
python3 -m src.stage3a_sensitivity.governance check. General checker retains historicalv1 scope.
SAFE_TO_OPEN_STAGE3A_SENSITIVITIES={ready['SAFE_TO_OPEN_STAGE3A_SENSITIVITIES']}, subject to
separate explicit authorization; no automatic execution.
'''
    REPORT.write_text(text)
    state=read(STATE);now=datetime.now(timezone.utc).isoformat()
    state['stage3a_sensitivity_freeze_qualification']=dict(readiness=ready,qualification=q,reconciliation=r,report=str(REPORT.relative_to(ROOT)))
    for v,s in r.items():
        name='paper_primary__evidence_20260927__'+v
        state['available_analysis_universes'].append(dict(name=name,rows=s['rows'],regions=s['regions'],official_tiks=s['tiks'],voters=s['voters'],parent='paper_primary__evidence_20260927',purpose='Frozen source/coverage sensitivity; no electoral responses opened',issued=None,valid=None,party_votes=None,outcome_aggregate_status='NOT_READ',source_mapping=str((OUT/f'sources/{v}_source_mapping.csv').relative_to(ROOT)),status=s['status']))
        state['row_counts'][name]=s['rows'];state['region_counts'][name]=s['regions']
    state['methodological_decisions'].append(dict(id='STAGE3A_SENSITIVITY_FREEZE_20260928',origin='user requirement',decision='Exact S1/S2a/S2b source variants; S3 identity; bounded synthetic transport qualification only',rationale='Previously promised robustness after primary, no result-driven versions',quantitative_impact={'primary_delta':0,'S1_removed':88,'S2a_replaced':88,'S2b_replaced':2,'S2_overlap':2,'sensitivity_response_reads':0},alternatives='No hybrid/new seed/model/full calibration adopted',reversibility='Frozen files immutable; no retry after qualification failure',downstream_consequences='Separate sensitivity execution authorization required; conditional transport only'))
    state['open_issues'].append(dict(id='STAGE3A_SENSITIVITY_EXECUTION_AUTHORIZATION',status='BLOCKER',origin='user requirement',description='Freeze/qualification complete as reported; no sensitivity response execution until separately authorized. Failed variants cannot execute.'))
    state['current_stage']='stage3A_SENSITIVITY_FROZEN_QUALIFIED_AWAITING_AUTHORIZATION' if ready['SAFE_TO_OPEN_STAGE3A_SENSITIVITIES'] else 'stage3A_SENSITIVITY_TRANSPORT_FAIL_STOP'
    state['last_updated']=now;write(STATE,state)
    HAND.write_text('> Latest: sensitivity source/design contract frozen; bounded synthetic transport qualification '+str(q['variants'])+'. S3 identity, no run. No sensitivity election responses read; separate authorization required. Primary remains immutable.\n\n'+HAND.read_text()+f'''

### Stage3A sensitivity freeze/qualification — 2026-09-28

### Analysis universes
Primary87736/84/2818 unchanged; source versions/counts untouched. New named sensitivity
universes (no primary substitution): S1 87648; S2a/S2b/S3 87736. Full design reconciliation:
{OUT.relative_to(ROOT)}/reconciliation.json. S2b2UUIDs overlap S2a88; no hybrid. S3 identity.
Task supports rebuilt from whole chosen universes; source/issued/valid/party deltas NOT_READ.
S1 LB exclusions={r['S1']['LB']['excluded_rows']}rows/{r['S1']['LB']['excluded_voters']}voters
versus primary7/9560; this is rebuilt singleton eligibility,not a new primary exclusion.
S1 fold/cell reassignment counts={r['S1']['fold_changed_common_rows']}/{r['S1']['cell_changed_common_rows']}.
S2a changed voters at{r['S2a']['voters_changed_rows']}UUIDs,net voters delta{r['S2a']['voters_delta']};
A pair additions/removals={r['S2a']['new_A_pairs']}/{r['S2a']['removed_A_pairs']}. Counts of
rows alone therefore do not prove support identity. All changes retained in design ledgers.

### Methodological decisions
User requirement: exact source choices and one bounded synthetic-only qualification.
Researcher implementation: source-hash/UUID/whole-vector selectors; original fold/RNG/kernel
mechanics; officialTIK only. No new method/gate. Qualification:{q['variants']},
{q['synthetic_datasets']}datasets/{q['A_comparisons']}A comparisons/{q['LB_target_comparisons']}LB targets.
Original scientific calibration evidence remains design-specific,not transferred empiricalPASS.

### Open issues
BLOCKER: separate real sensitivity authorization; variants withFAIL cannot execute.
IMPORTANT: measurement-selection conditional A null; LB expectation not pointwise/local;
cell/order changes affect metric deltas; no across-variantFWER or independent replication.
Source/geographic/enrichment/history limitations unchanged. No primary rescue.

### Reviewer attention
Source mappings and all designs/caches hashed before qualification. Sensitivity response
reads0; no outcome summaries. S3 identical sources/hierarchy/voters/design, no stochastic
rerun. Prior LFAIL/APASS/LBPASS/H/H-C histories unchanged. No H-C/newmodel reopening.

### Self-review
Primary/collateral exclusions0. S1 exactly88source exclusions; other versions sameUUIDframe.
Overlap and voter/design deltas explicit. Separate self-review/publication ledger saved.
Current checker:python3 -m src.stage3a_sensitivity.governance check. General historicalv1
checker retained. Report:{REPORT.relative_to(ROOT)}. Safe to request execution authorization:
{ready['SAFE_TO_OPEN_STAGE3A_SENSITIVITIES']}; no execution automatically.
''')
    g=read(GOV);g.update(state_sha256=sha(STATE),handoff_sha256=sha(HAND),updated_at=now);write(GOV,g)
    files=[p for p in pub.rglob('*') if p.is_file()]+[STATE,HAND,GOV,REPORT,OUT/'readiness.json']
    write(pub/'manifest.json',dict(files={str(p.relative_to(ROOT)):sha(p) for p in files}))
    print(json.dumps(ready))

def check():
    verify()
    for mf in [OUT/'qualification/manifest.json',OUT/'publication/manifest.json']:
        for p,h in read(mf)['files'].items():assert sha(ROOT/p)==h,p
    for p,h in read(PRIMARY/'manifest.json')['files'].items():assert sha(PRIMARY/p)==h,p
    old=read(OUT/'publication/before/research_state.json');s=read(STATE)
    allowed={'available_analysis_universes','row_counts','region_counts','methodological_decisions','open_issues','current_stage','last_updated'}
    for k,v in old.items():
        if k not in allowed:assert s[k]==v,k
    for k in ['available_analysis_universes','methodological_decisions','open_issues']:assert s[k][:len(old[k])]==old[k]
    for k in ['row_counts','region_counts']:
        for n,v in old[k].items():assert s[k][n]==v
    q=read(OUT/'qualification/summary.json');r=read(OUT/'readiness.json')
    assert r['variants']==q['variants'] and q['sensitivity_response_reads']==0
    print(json.dumps(dict(status='PASS',primary_immutable=True,sensitivity_response_reads=0,qualification=q['variants'],S3=r['S3_STATUS'])))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['publish','check']);a=p.parse_args();globals()[a.command]()
