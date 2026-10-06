"""Publish prepared real-release contract; never opens electoral responses."""
import argparse,json,shutil
from pathlib import Path
from datetime import datetime,timezone
import pandas as pd
from .spec import ROOT,OUT,PLAN,CFG,sha,write,verify
STATE=ROOT/'outputs/metadata/research_state.json';HANDOFF=ROOT/'docs/RESEARCH_HANDOFF.md'
GOV=ROOT/'outputs/stage3a/governance_manifest.json'
REPORT=ROOT/'outputs/reports/20260928_real_stage3a_release_preparation.md'
COMMAND='OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python3 -m src.stage3a_real.execution run --run-id 20260928_real_stage3a_primary_01 --authorized-real-stage3a'

def read(p):return json.loads(p.read_text())
def readiness():
    verify();checks=read(OUT/'checks/summary.json');assert checks['status']=='PASS' and checks['real_response_reads']==0
    for p,h in read(OUT/'checks/manifest.json')['files'].items():assert sha(ROOT/p)==h,p
    a=pd.read_csv(ROOT/'outputs/stage3a_v2/calibration/20260927_v2_clean_01/gate_decisions.csv');a=a[a.gate_id.str.startswith('A/')]
    assert len(a)==32 and a.status.eq('PASS').all()
    lb=pd.read_csv(ROOT/'outputs/stage3a_qualification/20260928/future_calibration/20260928_lb_fresh_01/gates.csv')
    assert len(lb)==970 and lb.status.eq('PASS').all()
    hc=read(ROOT/'outputs/stage3a_hc_final_gate/20260928_FE2/summary.json');assert hc['H_C_MAIN_STUDY_STOP']
    d=pd.read_csv(OUT/'freeze/reporting_design.csv')
    assert d.uuid.is_unique and len(d)==87736 and d.eligible.sum()==87729 and d.region.nunique()==84 and d.tik_uuid.nunique()==2818
    assert len(d[~d.eligible])==7 and d.loc[~d.eligible,'voters'].sum()==9560
    support=read(ROOT/'outputs/stage3a_v2/freeze/support.json');assert support['A']['rows']==3592
    return dict(REAL_STAGE3A_CONTRACT_FROZEN=True,REAL_ADAPTERS_EQUIVALENCE='PASS',SAFE_TO_OPEN_REAL_STAGE3A=True,
        separate_user_execution_authorization_required=True,real_execution_started=False,real_response_reads=0,
        L_B_usefulness='RETAIN_USER_ACCEPTED',A_gate_PASS=32,LB_gate_PASS=970,H_C_closed=True,
        checks=checks,plan_sha256=sha(PLAN),freeze_manifest_sha256=sha(OUT/'freeze/manifest.json'),
        support=support,command=COMMAND)

def publish():
    s=readiness();pub=OUT/'publication';pub.mkdir(exist_ok=False);before=pub/'before';before.mkdir()
    for p in [STATE,HANDOFF,GOV]:shutil.copy2(p,before/p.name)
    write(OUT/'readiness.json',s)
    (OUT/'launch_command.sh').write_text('# NOT EXECUTED. Separate explicit user authorization required.\n'+COMMAND+'\n')
    write(OUT/'self_review.json',dict(status='PASS',separate_review=True,
        material_correction='Empty integer intervals explicitly classified empty, score +infinity; no loss or widening',
        source_or_row_changes=0,new_exclusions=0,collateral_region_exclusions=0,real_response_reads=0,
        kernel_preservation='Frozen bytes intact; AST strips only first synthetic guard; synthetic=False adapter tested',
        scientific_scope='Cell-average expectation, not realised/pointwise/region coverage; A null restricted to support',
        risks=['Human usefulness RETAIN is explicit user decision','Source sensitivities need later route before their outputs',
               'Legacy general checker retains v1 scope; current new checker verifies 87736-row release'],
        no_new_CI_B_or_tests=True,no_real_execution=True,no_new_calibration=True))
    REPORT.write_text(f'''# Real Stage 3A release preparation — 2026-09-28

REAL_STAGE3A_CONTRACT_FROZEN=YES. REAL_ADAPTERS_EQUIVALENCE=PASS.
SAFE_TO_OPEN_REAL_STAGE3A=YES, **subject to separate explicit execution authorization**.
No real responses opened; no execution launched; no new scientific calibration.

User usefulness decision: L-B RETAIN. Previous PENDING_USER_REVIEW entries describe their
historical publication times; a separate current decision supersedes that pending status.
Original L FAIL, A PASS, L-B calibration PASS, H-C final numerical FAIL/scientific NOT_RUN
remain unchanged. H-C remains closed; no future sensitivity rescues a primary result.

## Frozen package
Plan `{PLAN.relative_to(ROOT)}` SHA256 `{s['plan_sha256']}`.
Manifest SHA256 `{s['freeze_manifest_sha256']}`.
All input/source references, kernel hashes, software versions and reporting design included.
No change to frozen scientific kernels. The synthetic-only entry guards remain in original
files; adapters AST-extract unchanged bodies and validate provenance separately. Real data
are never labelled synthetic. Loading requires explicit CLI authorization first.

## Minimal contract correction
Four mutually exclusive interval positions: below/inside/above/empty. Empty intervals already
occurred in synthetic comparator outputs; score remains infinity with explicit flag. No
discarding or widening. Observed I for V|I and V for C|V remain conditioning inputs;
target response does not choose own calibration sample/quantile. Scores on other heldout
rows legitimately use their observed responses. This is not an ordinary-election null test.

## Scope and outputs
Universe87736/84regions/2818TIK,99360758voters unchanged. A3592rows/1796pairs/955TIK/80regions/
3013626voters;84144rows unsupported for A. LB87729/84/2811,99351198voters;seven old singleton
exclusions/9560voters. New exclusions0. All-target LB and comparator with per-target uniform
calibration sample, frozen equal-fold/equal-cell summaries plus separate row-weighted and
full region/TIK descriptive appendices. One all-party A table, no new CI/B/test.
Two fixed figures. Calibration memberships and index map saved. No maps/top lists/local
p-values in primary package. Sensitivities separate, after immutable primary and route review.

## Pre-open validation
{s['checks']['unit_tests']} unit/integration tests;10 fresh actual-design synthetic datasets,
one per N1–N10,all5folds;10 complete A reference comparisons;80 LB/reference target comparisons.
All PASS at existing tolerance1e-10/1e-12; decisions identical. Toy all-target census tested
serial/reverse-chunk/two-worker equivalence,uniform conditional sample law,own-response
exclusion,shared samples,score/empty boundaries,weights,count reconciliation,guarded loading,
undefined A scale STOP,complete tables/two figures and immutable atomic commit.
No synthetic p-values/coverage performance displayed or used for model selection.
One pre-freeze ResourceWarning in gzip writer was corrected by explicitly closing its
underlying handle. No frozen scientific source or numerical behavior changed; all checks
subsequently repeated before final release freeze. Prior scientific artifacts unchanged.

## Proposed authorized command — NOT EXECUTED
```sh
{COMMAND}
```
Output: `outputs/stage3a_real/20260928_real_stage3a_primary_01/` only after complete atomic
commit. `.building` retained on failure, no partial release/retry/overwrite. STOP on source/
identity/count/kernel mismatch or undefined joint A. Real outputs not printed before commit.

## Governance and self-review
User requirement: RETAIN L-B, contract and adapters only; authorization pending. Researcher
choices: deterministic real namespaces, output ordering, guarded AST adapters,empty category;
source constraint: frozen canonical design/versions. Alternative: keep random single-target
output; rejected because all-target conditional sampling preserves average estimand and
gives useful descriptive coverage. Quantitative source/universe/count changes zero.
No further cross-sectional development automatically: after separately authorized primary
and promised robustness, proceed to evidence integration. No counterfactual authorization.
Separate self-review PASS; current checker `python3 -m src.stage3a_real.governance check`.
General historical checker still reports old v1 support; does not substitute for this check.
''')
    state=read(STATE);state['stage3a_real_release']=s
    state['stage3a_LB_usefulness_decision']=dict(status='RETAIN',origin='user requirement',
        supersedes='Historical PENDING_USER_REVIEW in completed review; calibration artifacts unchanged',
        scope='Main-study design-cell-averaged interval benchmark, no conditional density/anomaly claim')
    state['current_stage']='stage3A_REAL_CONTRACT_FROZEN_AWAITING_AUTHORIZATION';state['last_updated']=datetime.now(timezone.utc).isoformat()
    state['methodological_decisions'].append(dict(id='REAL_STAGE3A_RELEASE_CONTRACT_20260928',origin='user requirement',
        decision='RETAIN L-B; freeze A+LB real reporting contract and adapters, no real execution yet',
        rationale='Preserve prospective reporting and calibrated scopes before opening outcomes',
        quantitative_impact=dict(base_delta=0,new_exclusions=0,real_response_reads=0,preopen_synthetic_datasets=10),
        alternatives='Random single-target real output; not selected',reversibility='Future prospective documentation only; no post-result selection',
        downstream_consequences='Separate user command authorization; immutable primary before sensitivities/integration'))
    state['open_issues'].append(dict(id='REAL_STAGE3A_EXECUTION_AUTHORIZATION',status='BLOCKER',origin='user requirement',
        description='Prepared and equivalent adapters; real execution requires separate explicit user authorization. No real responses opened.'))
    write(STATE,state)
    HANDOFF.write_text('> Latest: real Stage3A contract frozen, adapters equivalence PASS, L-B usefulness RETAIN by user. Await separate real-execution authorization; no real outcomes opened.\n\n'+HANDOFF.read_text()+f'''

### Real Stage3A reporting/release preparation — 2026-09-28

### Analysis universes
87736UIKs/84regions/2818officialTIK unchanged. A3592/1796pairs/955TIK/80regions;
LB87729/84/2811;seven prior singleton exclusions/9560voters. New exclusions0.
Voters99360758=99351198+9560. Real responses read0;real fits0.

### Methodological decisions
User requirement: L-B RETAIN; freeze A+LB contract and adapters; no real execution yet.
Researcher choices: per-target real RNG namespace, fixed summaries/figures,AST guard adapter,
explicit empty interval state with infinity score. Source constraint: canonical frozen versions.
No scientific kernel/gate/support change. Old LFAIL,APASS,LBPASS,HC numericalFAIL preserved.
Human PENDING status in earlier review is superseded only by new RETAIN decision above.

### Open issues
BLOCKER: separate user real-execution authorization. Sensitivity route not yet frozen;
no inferential sensitivity until support rebuild and transport/calibration justification.
No calibrated region/TIK/pointwise LB coverage or anomaly probabilities.

### Reviewer attention
Pre-open equivalence PASS:{s['checks']['unit_tests']} tests,10actual-design synthetic datasets,
10A comparisons,80LB targets. No real response access. Empty comparator intervals never
dropped. All-target output preserves conditional sampling law and expected average coverage,
not realised or simultaneous coverage. No additional cross-sectional models after opening.

### Self-review
No base/source/denominator changes,0collateral exclusions. Full output/replay/guard/atomic
commit checks PASS. Current checker:python3 -m src.stage3a_real.governance check.
Report:{REPORT.relative_to(ROOT)}. Safe:YES to request authorization;NO automatic execution.
''')
    gov=read(GOV);gov.update(state_sha256=sha(STATE),handoff_sha256=sha(HANDOFF),updated_at=state['last_updated']);write(GOV,gov)
    files=[p for p in OUT.rglob('*') if p.is_file() and p.name!='publication_manifest.json']+[STATE,HANDOFF,GOV,REPORT]
    write(pub/'publication_manifest.json',dict(files={str(p.relative_to(ROOT)):sha(p) for p in files}))
    print(json.dumps({k:s[k] for k in ['REAL_STAGE3A_CONTRACT_FROZEN','REAL_ADAPTERS_EQUIVALENCE','SAFE_TO_OPEN_REAL_STAGE3A','plan_sha256','freeze_manifest_sha256']}))

def check():
    s=readiness()
    for p,h in read(OUT/'publication/publication_manifest.json')['files'].items():assert sha(ROOT/p)==h,p
    current=read(STATE);old=read(OUT/'publication/before/research_state.json')
    for key in ['row_counts','region_counts','available_analysis_universes','stage3a_HC_FE2_final_gate','stage3a_v2_execution','stage3a_LB_calibration_review']:
        assert current[key]==old[key],key
    assert current['stage3a_real_release']==s and current['stage3a_LB_usefulness_decision']['status']=='RETAIN'
    print(json.dumps(dict(status='PASS',base_rows=87736,A_rows=3592,LB_rows=87729,real_response_reads=0,real_execution=False)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['publish','check']);a=p.parse_args();globals()[a.command]()
