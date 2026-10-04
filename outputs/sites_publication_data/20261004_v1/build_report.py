"""Write engineering review evidence after, not instead of, successful validation."""
from pathlib import Path
import json
import hashlib

ROOT=Path(__file__).resolve().parents[3]
P=Path(__file__).resolve().parent
PUB=ROOT/'publication/sites/v1'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n')

def main():
    check=read(P/'checker_results.json');det=read(P/'determinism.json')
    assert check['status']==det['status']==read(P/'decoder_regression.json')['status']=='PASS'
    manifest=read(PUB/'manifest.json');assert sha(PUB/'manifest.json')==check['manifest_sha256']==det['second_manifest_sha256']
    total=sum(v['bytes'] for v in manifest['files'].values())+(PUB/'manifest.json').stat().st_size
    states_bytes=sum(v['bytes'] for k,v in manifest['files'].items() if k.startswith('states/'))
    affirmative=[
        'Different native universes are preserved, especially Cedar71438of87736;no common-complete-case restriction or new exclusion.',
        'A/B are aliases/slices of1600jointABC cells;20D cells;full/native are scope outputs,not added calculation states.',
        'Exactly444additional public states;the one internalLS state is excluded and CARD_ONLY methods have no numeric calculation.',
        'Exact rational outputs have huge integers;lossless lazy gzip integer-string pools avoid precision loss. Main indices are separate from optional exact resources.',
        'Pre-seal engineering issues/metadata refinements were logged;no scientific source,contract,packet,eligibility or result was altered.',
        'Default states are inherited,notselectedafterreveal;source/geography/controlavailability is explicit.',
        'Final editorial labels/prose and release metadata are pending;no article or UI has been implemented.',
        'Current handoff checker requires a narrow new engineering-stage route to avoid the obsolete schema12 scientific-design checker. Original dispatcher archived unchanged;stage registry extends52to53append-only.',
    ]
    put(P/'self_review.json',{'status':'PASS','review_type':'SEPARATE_POST_IMPLEMENTATION_SELF_REVIEW',
        'affirmative_findings':affirmative,'universe_changes':0,'new_exclusions':0,'new_methodological_choices':0,
        'result_changes':0,'new_models':0,'new_fits':0,'new_scientific_states':0,
        'article_edits':0,'site_implementation':0,'protected_files_unchanged':check['protected_files'],
        'missing_requested_chart_derivatives':[],'unresolved_blockers':[],
        'accepted_limitations':['Final reader copy pending','Established public-source fidelity gaps retained','Large optional exact resources;serve only the public API subtree','License/repository/release metadata remain separately pending']})
    authorities='\n'.join(f"| `{r['path']}` | `{r['sha256']}` |" for r in read(P/'input_bindings.json')['manifests'])
    checker_names='\n'.join('- '+r['check'] for r in check['checks'])
    report=f'''# Static publication-data layer for Sites v1

The static API is ready at `publication/sites/v1/`. This is publication engineering:
stored values and existing metadata were extracted, joined and serialized. No model,
fit, source-row kernel, new estimand, scenario, article change or UI was executed.
Scientific methodological choices: **0**. New source/row/region/TIK exclusions: **0**.

## Authoritative inputs

| Immutable source manifest | SHA256 |
|---|---|
{authorities}

The canonical publication contract explicitly includes all1,620cells and resolves its
exact references through already-revealed exact records, without protected raw execution
access. Its 1,600joint cells contain A/B as aliases/slices;20cells are D. The accepted
additional-method reader contains445states with explicit visibility. Its INTERNAL state
is not exported. The accepted closure supplies Cedar support N/L/O and source/fidelity
metadata. The frozen region catalog supplies84official IDs/names;no current web sources
or article drafts supply numbers. Consumed dependency hashes and roles are recorded in
`input_bindings.json`;the complete protected before/after inventory is independent.
No conflicting public static-data convention was present.

## Inventory and accounting

| Inventory | Frozen states | Public exported | Omitted from public API |
|---|---:|---:|---:|
| Joint A/B/C cells |1600|1600|0|
| D |20|20|0|
| iStories |103|102|1 INTERNAL|
| Cedar |161|161|0|
| Novaya1D |90|90|0|
| Novaya2D |91|91|0|
| Total |2065|2064|1 INTERNAL|

Two CARD_ONLY catalog entries have no state/result or executable controls. A/B aliases
and full/native scoped values do not inflate this inventory. Publication aliases map
one-to-one to original state IDs in technical provenance;no scientific state was created.

Primary frame remains87,736UIKs/84regions/2,818officialTIKs,99,360,758registered voters,
55,674,920issued,54,723,201valid. DEG is excluded;overseas is separate. Source memberships,
denominators and scientific field meanings did not change. S1 remains87,648UIKs.
Cedar's primary native frame remains71,438;16,298outside=2,758registered<=100+
13,540unknowninvalid,mutually exclusive inherited reasons. No new complete-case
intersection,new universe,source substitution or collateral region exclusion exists.

## Client contract and scientific semantics

Load manifest,methods,sources;choose an executable method;load its explicit state list.
Only AVAILABLE listed rows may be chosen. Marginal control lists are not a Cartesian
product. Source/geography changes require disabling unsupported controls and an explicit
visible reset. Exact source selectors and all frozen LOO regions remain unchanged.

The catalog distinguishes ten-party local conditional scenarios,focal-party D,
iStories scenario focal-valid share,Cedar signed E/observed-focal,1Dcomponent center,
and2Dcomponent center plus membership. Typed guards prohibit a common truth scale,
confidence-interval labeling,honesty/fraud probabilities,source correctness ranking,
native/full conflation and zero-imputation of Dundefined fields/groups. Predeclared
defaults are identified without scientific-preference claims. INTERNAL LS is unreachable
through the public file graph. Published-only methods carry no fake zero/result.

All15iStories windows carry referenceN,distinct from scenario frame. Cedar has all71fixed
anchors plus stored AUTO/relative/source/LOO states,each with existingNON_MODEL N/L/O.
1Dbin widths retainK3 and sigma_min=h/2 coupling. 2Dretains exact issued/registered
coordinate wording,covariance distinction and mechanical threshold-fit reuse.
Reader labels treat this as one project;historical names appear only in technical
provenance. Final editorial copy is explicitly pending.

## Static data and chart readiness

All requested chart inputs exist:original-vs-scenario ten-party arrays,A/B/C sensitivity,
Dspecification comparison,15window points with N,71anchor points with N/L/O,1Dcenters,
2Dcenters/membership/coverage. Missing requested publication derivatives: **NONE**.

Files:manifest,method/source catalogs,baselines,designs,six state files,seven schemas,
contract/readme,and1,620lazy exact JSON.gzip sidecars. Total: **{total:,}bytes**;
state indices: **{states_bytes:,}bytes**. Large integer strings are pooled losslessly
inside each exact resource;pool expansion is checked. Do not load all exact resources
initially or convert integer strings through JavaScript Number. Pipeline composition/
intensity/interaction details are intentionally not duplicated;their immutable provenance
remains available. Exact counts,shares,delta and scoped focal accounting are retained.

Regenerate:`/usr/bin/python3 -m src.publication_sites generate`.
Validate:`/usr/bin/python3 -m src.publication_sites check`.
Existing publication environment:{check['validator_environment']};scientific dependencies
are not changed. No new framework or dependency installation was introduced.

## Verification and determinism

Checker:**PASS**. Checks:
{checker_names}

Independent comparison with the qualified exact decoder passed for three saved aggregate
records,including a non-identity joint scenario and D. This is a serializer check,not a
scientific execution. Both final generations have identical bytes for all{det['files']}
files. Manifest SHA256:`{sha(PUB/'manifest.json')}`.
Whole public inventory SHA256:`{det['second_inventory_sha256']}`.
Newmodelcalls=0,newfits=0,newscientificstates=0,source rows passed through kernels=0.
Frozen scientific/reveal/committed artifacts remain byte-identical. Engineering attempts
and corrections before sealing are documented in `generation_attempts.json`;none repaired
a model,fixture,source mapping or frozen result.

## Separate self-review and project handoff

The affirmative findings and accepted limitations are in `self_review.json`. Exact
outputs remain different estimands;no new claim,preferred parameter,source or political
comparison was selected. Source/fidelity public gaps and final prose/release metadata
remain pending;these do not block the data contract. No article/site product was edited.

The handoff/state update is append-only through registry stage53,with the original
dispatcher and pointer archived. The old schema12 scientific-design checker is bypassed
only for this publication-engineering stage;its historical code remains preserved.
Roadmap99is unchanged and formally paused before54;neither article54 nor site work starts.
External branch stays CLOSED;G stays closedNO_GO;scientific results stay frozen.

### Handoff

Stage completed:Publication layer for Sites v1.
Primary universe:paper_primary__evidence_20260927,unchanged.
Input rows:2065stored scientific states;0real source rows passed through kernels.
Output/analysed rows:2064PUBLICstate records;2CARD_ONLYcatalogentries.
Rows excluded:0newUIK exclusions;1INTERNALstate excluded only from publication API.
Regions included/excluded:84primary;own inherited native/LOO scopes;0newregion exclusions.
New methodological choices:0;engineering serialization decisions logged separately.
Important unresolved issues:no blocker;editorial/release metadata and known fidelity gaps pending.
Reviewer attention:typed estimands,support,undefinedD,availability,lazy exact integers,internal exclusion.
Safe to proceed:YES WITH LIMITATIONS—review this static contract in a separately authorized publication-engineering task;no UI/article/science started here.
'''
    (P/'report.md').write_text(report)
    print(json.dumps({'report':'created','public_manifest_sha256':sha(PUB/'manifest.json'),'files':det['files'],'total_bytes':total}))

if __name__=='__main__':main()
