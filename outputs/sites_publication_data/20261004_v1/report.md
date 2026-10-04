# Static publication-data layer for Sites v1

The static API is ready at `publication/sites/v1/`. This is publication engineering:
stored values and existing metadata were extracted, joined and serialized. No model,
fit, source-row kernel, new estimand, scenario, article change or UI was executed.
Scientific methodological choices: **0**. New source/row/region/TIK exclusions: **0**.

## Authoritative inputs

| Immutable source manifest | SHA256 |
|---|---|
| `outputs/smz_publication_package/20261001_v1/manifest.json` | `9b420792e74466fde297b1c03dc4247e3a4526d19bd836b783112b8723d9b48a` |
| `outputs/smz_run01_reveal/20261001_v1/manifest.json` | `b501f8bdfc6bc7004300a5ad8761d2b82f4b45008e3788da88549820d62c9503` |
| `outputs/smz_v2_external_joint_reveal/20261003_v1/manifest.json` | `5176c9c067aa3f88ebd77e3bf5836aa9233b51ea3664b726e87632a87026ed43` |
| `outputs/smz_v2_external_closure/20261003_v1/manifest.json` | `06cf02d7d8e2c32b89a4af78246a48fd5e692cfe9d2066ab3caf6b78116d86f5` |
| `outputs/smz_run01_interpretation/20261001_v1/manifest.json` | `04aef6f926d9986ee24102d82e514702707f0c6e38b0cfaab646538bfc8e5c45` |
| `outputs/smz_v2_external_freeze/20261002_v2/manifest.json` | `942f34530a5456b2a83048f8c9fa3c4003998941b2da5ebae7b72eafcc0218d5` |

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
contract/readme,and1,620lazy exact JSON.gzip sidecars. Total: **295,868,404bytes**;
state indices: **10,989,574bytes**. Large integer strings are pooled losslessly
inside each exact resource;pool expansion is checked. Do not load all exact resources
initially or convert integer strings through JavaScript Number. Pipeline composition/
intensity/interaction details are intentionally not duplicated;their immutable provenance
remains available. Exact counts,shares,delta and scoped focal accounting are retained.

Regenerate:`/usr/bin/python3 -m src.publication_sites generate`.
Validate:`/usr/bin/python3 -m src.publication_sites check`.
Existing publication environment:{'jsonschema': '4.17.3', 'python': '3.10.12'};scientific dependencies
are not changed. No new framework or dependency installation was introduced.

## Verification and determinism

Checker:**PASS**. Checks:
- authority_manifests_and_all_consumed_dependencies
- manifest_schema
- complete_public_file_inventory_hash_and_size
- method_schema
- source_baseline_design_schemas
- only_frozen_public_axes_no_optimizer_K_scaling_or_accounting_selectors
- all_state_schemas_exact_types_finite_values_and_D_missingness
- 1620_published_scenario_cells_444_additional_public_states_zero_duplicates
- zero_internal_state_in_all_public_files_including_exact_downloads
- OFAT_availability_15_windows_71_anchors_and_own_frame_support
- 2D_threshold_fit_reuse_and_exact_centers
- all_exact_sidecars_and_states_identical_to_authoritative_projection
- documented_client_workflow_and_no_cartesian_inference
- negative_schema_regressions_wrong_estimands_and_card_execution
- protected_science_reveal_committed_article_and_provenance_bytes_unchanged
- no_scientific_kernel_provider_or_optimizer_loaded

Independent comparison with the qualified exact decoder passed for three saved aggregate
records,including a non-identity joint scenario and D. This is a serializer check,not a
scientific execution. Both final generations have identical bytes for all1640
files. Manifest SHA256:`38d8f0eaa79952b4036d7e23c04ff40cca65f51e40f5cbbcddc88efd92fc3d16`.
Whole public inventory SHA256:`64565aa34eed51dd1dd7c18e9d2a900f7868cfbf19fbb5faeb28e559bdf46b62`.
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
