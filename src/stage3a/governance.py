"""Stage-aware publication and verification; no prior publisher is rerun."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import json
import shutil
import sys
import platform
import numpy as np
import scipy
import pandas as pd
from .spec import ROOT,OUT,CONFIG,DESIGN_SOURCE,HIERARCHY_SOURCE,digest,write_json,frozen
from .design import actual,pairs,association_support,folds
from .gates import registry

HISTORY=ROOT/'outputs/metadata/history/before_stage3a_freeze_20260927'
STATE=ROOT/'outputs/metadata/research_state.json'
HANDOFF=ROOT/'docs/RESEARCH_HANDOFF.md'
OLD_MANIFEST=ROOT/'outputs/identity_validation/20260923T110217085076Z/evidence_review/metadata/artifact_manifest.json'


def archive():
    if HISTORY.exists():raise FileExistsError(HISTORY)
    for p in [STATE,HANDOFF,OLD_MANIFEST,ROOT/'AGENTS.md',ROOT/'src/analysis/research_handoff.py']:
        dest=HISTORY/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)


def package():
    if (OUT/'manifest.json').exists():raise FileExistsError('Freeze already exists')
    write_json(OUT/'config.json',CONFIG)
    registry().to_csv(OUT/'binding_gates.csv',index=False)
    write_json(OUT/'software.json',{'python':sys.version,'platform':platform.platform(),
               'numpy':np.__version__,'scipy':scipy.__version__,'pandas':pd.__version__,
               'threads':1,'optimizer':'scipy L-BFGS-B analytic gradient',
               'rng':'numpy PCG64 SHA256 first16bytes big-endian','git_commit':None})
    (OUT/'requirements.freeze.txt').write_text(f'numpy=={np.__version__}\nscipy=={scipy.__version__}\npandas=={pd.__version__}\n')
    paths=sorted(p for p in OUT.rglob('*') if p.is_file())
    paths+=sorted(p for p in (ROOT/'src/stage3a').glob('*.py'))
    paths += [ROOT/'docs/STAGE_3A_FROZEN_PLAN.md',ROOT/'tests/test_stage3a.py',ROOT/'AGENTS.md',ROOT/'src/analysis/research_handoff.py']
    inputs=[ROOT/DESIGN_SOURCE,ROOT/HIERARCHY_SOURCE,OLD_MANIFEST,
            HISTORY/'outputs/metadata/research_state.json',HISTORY/'docs/RESEARCH_HANDOFF.md']
    write_json(OUT/'manifest.json',{'status':'FROZEN_NOT_CALIBRATED','generated_at_utc':datetime.now(timezone.utc).isoformat(),
               'files':{str(p.relative_to(ROOT)):digest(p) for p in paths},
               'inputs':{str(p.relative_to(ROOT)):digest(p) for p in inputs},
               'plan_sha256':digest(ROOT/'docs/STAGE_3A_FROZEN_PLAN.md'),
               'config_sha256':digest(OUT/'config.json'),'git_commit':None})


def publish():
    frozen();old=json.loads((HISTORY/'outputs/metadata/research_state.json').read_text())
    s=json.loads(STATE.read_text())
    if s!=old:raise RuntimeError('Live state changed since archive')
    support=json.loads((OUT/'support_audit.json').read_text());d=actual();p,m=pairs(d)
    now=datetime.now(timezone.utc).isoformat()
    views=[]
    for name,kind in [('paper_primary__3a_exact_size_projection','association'),
                      ('paper_primary__3a_prediction_known_tik','known_tik'),
                      ('paper_primary__3a_prediction_heldout_tik','heldout_tik')]:
        x=support if kind=='association' else support['prediction'][kind]
        mask=m.reason.eq('matched').to_numpy() if kind=='association' else (d.groupby('tik_uuid').uuid.transform('size').to_numpy()>=2 if kind=='known_tik' else np.ones(len(d),bool))
        view={'name':name,'snapshot':CONFIG['snapshot'],'previous_universe':'paper_primary',
              'rows':x['rows'],'regions':x['regions'],'official_tiks':x['tiks'],'voters':x['voters'],
              'inclusion':'Adjacent UUID pairs within exact official TIK and integer voters cell' if kind=='association' else ('original official TIK N>=2' if kind=='known_tik' else 'all paper_primary'),
              'exclusion':'odd/unpaired exact-size cell rows' if kind=='association' else ('singleton official TIK' if kind=='known_tik' else 'none'),
              'purpose':'Prospective synthetic calibration design; no electoral result analysed',
              'issued':None,'valid':None,'party_votes':None,'outcome_aggregate_status':'NOT_READ_INFORMATION_BOUNDARY',
              'excluded_rows':len(d)-int(mask.sum()),'excluded_voters':int(d.loc[~mask,'voters'].sum()),
              'region_names':sorted(d.loc[mask,'region'].unique()),'not_nationally_representative':kind=='association'}
        views.append(view)
        s['available_analysis_universes'].append(view);s['row_counts'][name]=view['rows'];s['region_counts'][name]=view['regions']
    decision={'id':'STAGE3A_V1_FREEZE','stage':'3A preparation/freeze','origin':'researcher/Codex choice',
      'decision':'Separate P/A/C task gates; H/L predictive candidates; exact-size categorical projection association; Holm; Shpilkin/KYHT/standalone robust counterfactual DROP; history EXCLUDED.',
      'rationale':'Executable count predictions and explicit narrow exchangeability hypothesis, with exact size control and denominator-aware coarsening; counterfactual observational equivalence prevents point identification.',
      'quantitative_impact':{'base_rows_delta':0,'primary_rows':87734,'association_rows':3592,'association_excluded':84142,'known_tik_prediction_excluded':7,'promotions':0,'all_base_aggregate_deltas':0},
      'alternatives_considered':'Finite-caliper kernel, raw-share exchangeability, old spline bootstrap, outcome-selected reference core, relaxed identity gate; none adopted.',
      'reversibility':'Frozen artifacts immutable; method/gate changes require separately identified version and new prospective evaluation.',
      'downstream_consequences':'Next task calibration only. No real fits, no enrichment/history, no reconstruction. A support is4.09%, not a national estimand.'}
    s['methodological_decisions'].append(decision)
    for issue in [
      {'id':'stage3a_calibration_pending','status':'BLOCKER','description':'Frozen code/design only; actual-design P/A evaluation NOT RUN. Dry-run is engineering, not calibration.',
       'affected':'New P/A real-data outputs','can_change_quantitative_results':True,'resolution_needed':'Separately authorized frozen evaluation, all binding gates and reproducibility PASS for each released task.'},
      {'id':'stage3a_projection_support','status':'IMPORTANT','description':'A uses3592/87734 UIKs,1796pairs,955TIK,80regions; one-category projection sacrifices power. No generalization to84142unpaired UIKs.',
       'affected':'Association estimand/external validity','can_change_quantitative_results':True,'resolution_needed':'Report power/support; any broader method needs a new design, never support relaxation inside v1.'},
      {'id':'stage3a_counterfactual_nonidentification','status':'BLOCKER','description':'Exact observed-law equivalence permits different latent baseline counts. Shpilkin/KYHT not fitted; agreement of predictors is not identification.',
       'affected':'Counterfactual point totals/mechanism claims','can_change_quantitative_results':True,'resolution_needed':'Independent identifying restrictions/evidence and a separately authorized identification stage.'}]:
        s['open_issues'].append(issue)
        s['open_blockers' if issue['status']=='BLOCKER' else 'open_important_issues'].append(issue['id'])
    s.update(schema_version=12,current_stage='stage3A_v1_FROZEN_CALIBRATION_NOT_RUN',last_updated=now)
    s['stage3a']={'status':'FROZEN_NOT_CALIBRATED','path_c_accepted_by_user':True,
         'plan':'docs/STAGE_3A_FROZEN_PLAN.md','manifest':'outputs/stage3a/freeze/manifest.json',
         'plan_sha256':digest(ROOT/'docs/STAGE_3A_FROZEN_PLAN.md'),'config_sha256':digest(OUT/'config.json'),
         'manifest_sha256':digest(OUT/'manifest.json'),'R':5000,'B':1999,'binding_gates':23336,
         'predictive':'NOT_RUN','association':'NOT_RUN','counterfactual':'NOT_IDENTIFIED',
         'real_models_executed':False,'source_promotions':0,'new_views':views,
         'safe_to_proceed':'YES: calibration execution only under next task',
         'previous_state':str((HISTORY/'outputs/metadata/research_state.json').relative_to(ROOT)),
         'self_review':{'large_support_loss':True,'fully_reconciled_rows_voters':True,'base_changes':False,
             'new_assumptions':True,'narrow_support':True,'outcome_support_totals_withheld':True,
             'all_old_issues_preserved':True,'no_real_response_fit':True}}
    write_json(STATE,s)
    summary='''

### Stage 3A v1 — frozen preparation only (2026-09-27)

Path C accepted by user. Plan `docs/STAGE_3A_FROZEN_PLAN.md`; full executable package
`outputs/stage3a/freeze/`. Actual-design calibration NOT RUN. No real-response fit or
new electoral coefficient/p-value. Source-only design audit, synthetic engineering
tests and deterministic replay are not calibration evidence.

### Analysis universes

Primary87,734→87,734;84regions/2,818officialTIK unchanged;voters99,359,922;
issued55,674,254;valid54,722,540;all party/base deltas0;promotions0.
Three prospective design views registered, never replacements for primary:
* A exact-size projection:3,592UIK/1,796pairs/955TIK/80regions/voters3,013,626.
  87,734=3,592+84,142unpaired;99,359,922=3,013,626+96,346,296voters.
* Known-TIK prediction:87,727UIK/2,811TIK/84regions/voters99,350,362;
  7singleton-TIK rows/9,560voters unsupported; no region excluded.
* Held-out-TIK prediction:all87,734UIK/2,818TIK/84regions/voters99,359,922.
Support-specific issued/valid/party aggregates deliberately NOT_READ under the new
response information boundary, not zero; base preservation established by input hashes.

### Methodological decisions

STAGE3A_V1_FREEZE (`researcher/Codex choice`): H hierarchical count ridge and L local
predictive mixture; new A exact-size one-category projection with parent-joint signs,
Holm and independent calibration. Distinct predictive/association/identification gates.
Shpilkin/KYHT and standalone robust counterfactual DROP; historical EXCLUDED.
Rationale: explicit observable estimands; size/denominator control without failed2%kernel;
ordinary alternative worlds preclude baseline identification. User requirement: Path C,
freeze only, no real runs. Alternative raw-share/finite-caliper/clean-core methods rejected.
Quantitative impact:base0;A excludes84,142for its own estimand;prediction known-TIK7.
Reversible only by a new prospective version. Scientific consequence:narrow A support,
information loss/potential low power, predictive PASS never identifies mechanism.

### Open issues

All old BLOCKER/IMPORTANT retained, especially C_namespace_bridge/history and geographic
coverage/source uncertainty. New BLOCKER:Stage3A actual-design calibration pending;
counterfactual observed-law nonidentification. IMPORTANT:A support4.09% plus randomized
coarsening; no promise of useful power. Temporal3,615 result and old2B failures unchanged.

### Reviewer attention

Large support loss is deliberate and explicit, not a data-quality exclusion. A observed
statistic estimates pair covariance using a noisy categorical projection, not full-data
Pearson. 7prediction singleton exclusions are task-specific. Priors/precisions, fallback,
Holm, R5000/B1999 and23,336simultaneous gates are new frozen researcher choices.
Allowed Type-I ceiling .075 is distinct from nominal .05;coverage floor .92 from .95.
No broad association or counterfactual claim follows from P or narrow A success.
Numerical engineering corrections are logged; they used fake data, not election results.

### Self-review

Large input/output support differences:yes, fully reconciled for rows/voters; outcomes
withheld explicitly. Primary loss/collateral exclusions:no. New named views:yes. New
assumptions/choices:yes, all frozen. Dependence on exact size/support:yes. Inconsistent
base aggregates:no. No source promotion/history attachment. Dry-run/test PASS means
code reproducibility only. Synthetic calibration itself has not been executed.

Safe to proceed:YES only to separately authorized frozen calibration execution. NO
to substantive real models, automatic task-to-task promotion or counterfactual totals.
'''
    HANDOFF.write_text('> Current status: Stage3A v1 FROZEN; actual-design calibration NOT RUN. Next scope is calibration only. Earlier statements below retain their historical scope.\n\n'+HANDOFF.read_text()+summary)
    write_json(ROOT/'outputs/stage3a/governance_manifest.json',{
       'state_sha256':digest(STATE),'handoff_sha256':digest(HANDOFF),'freeze_manifest_sha256':digest(OUT/'manifest.json'),
       'historical_manifest_sha256':digest(OLD_MANIFEST),'updated_at':now})


def check():
    frozen();live=json.loads(STATE.read_text());old=json.loads((HISTORY/'outputs/metadata/research_state.json').read_text())
    binding=json.loads((ROOT/'outputs/stage3a/governance_manifest.json').read_text())
    assert digest(STATE)==binding['state_sha256'] and digest(HANDOFF)==binding['handoff_sha256']
    assert digest(OUT/'manifest.json')==binding['freeze_manifest_sha256']
    oldmf=json.loads(OLD_MANIFEST.read_text())
    assert digest(OLD_MANIFEST)==binding['historical_manifest_sha256']
    for group in ['files','inputs']:
        for p,h in oldmf[group].items():
            target=HISTORY/p if p in ['AGENTS.md','src/analysis/research_handoff.py'] else ROOT/p
            assert digest(target)==h,p
    assert digest(HISTORY/'docs/RESEARCH_HANDOFF.md')==oldmf['handoff_sha256']
    assert digest(HISTORY/'outputs/metadata/research_state.json')==oldmf['state_sha256']
    for key in ['active_snapshot_id','raw_sha256','primary_analysis_universe','primary_universe_definition']:
        assert live[key]==old[key],key
    for key in ['available_analysis_universes','methodological_decisions','open_issues']:
        assert live[key][:len(old[key])]==old[key],key
    for key in ['row_counts','region_counts']:
        for k,v in old[key].items():assert live[key][k]==v,(key,k)
    allowed={'schema_version','current_stage','last_updated','available_analysis_universes','methodological_decisions',
             'open_issues','open_blockers','open_important_issues','row_counts','region_counts'}
    for k,v in old.items():
        if k not in allowed:assert live[k]==v,k
    d=actual();p,m=pairs(d);sup=association_support(d,p)
    assert (sup['rows'],sup['pairs'],sup['tiks'],sup['regions'],sup['voters'])==(3592,1796,955,80,3013626)
    assert p.to_csv(index=False)==(OUT/'association_pairs.csv').read_text()
    assert m.to_csv(index=False)==(OUT/'association_membership.csv').read_text()
    assert d.to_csv(index=False)==(OUT/'design.csv').read_text()
    for task in CONFIG['prediction_tasks']:
        eligible=(d.groupby('tik_uuid').uuid.transform('size').to_numpy()>=2 if task=='known_tik' else np.ones(len(d),bool))
        assert d.assign(fold=folds(d,task),eligible=eligible).to_csv(index=False)==(OUT/f'prediction_{task}_membership.csv').read_text()
    assert registry().to_csv(index=False)==(OUT/'binding_gates.csv').read_text()
    assert live['stage3a']['real_models_executed'] is False
    assert live['stage3a']['counterfactual']=='NOT_IDENTIFIED'
    # Replay earlier evidence without rewriting its state or invoking its old publisher.
    from src.data.identity_validation_evidence import audit,OUT as EVIDENCE
    df,cl,mu,req,resp,su=audit()
    for frame,name in [(df,'row_decisions.csv'),(cl,'class_decisions.csv'),(mu,'multi_candidate_decisions.csv'),(req,'required_class_membership.csv'),(resp,'raw_response_manifest.csv')]:
        assert frame.to_csv(index=False,lineterminator='\n')==(EVIDENCE/name).read_text(),name
    assert json.loads(json.dumps(su))==json.loads((EVIDENCE/'metadata/audit_summary.json').read_text())
    print(json.dumps({'status':'PASS','freeze':'VERIFIED','base_rows':87734,'association_design_rows':3592,
           'predictive_known_tik_rows':87727,'predictive_heldout_tik_rows':87734,
           'binding_gates':23336,'prior_2c1_replay':'PASS','actual_design_calibration':'NOT_RUN',
           'real_models':'NOT_RUN','counterfactual':'NOT_IDENTIFIED'}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['archive','package','publish','check']);args=parser.parse_args()
    globals()[args.command]()
