# Bounded scenario model zoo — SMZ-2026-v1

Contract freeze date: 2026-09-29. Status at release: FROZEN_CONTRACT_ONLY.
Normative companions: `outputs/scenario_model_zoo/20260929_v1/config.json`,
`model_cards.json`, `abc_designs.csv`, `abc_parameter_grid.csv`, `d_execution_grid.csv`,
`comparison_matrix.csv`, `output_interface.json`, `qualification_registry.json`,
`source_bindings.json`, `decision_ledger.json`, and `manifest.json`.
Text and structured records must agree; disagreement is FREEZE_BLOCKED, never an
invitation for the executor to choose an interpretation. No scenario kernel is supplied.

## 1. Scope, inventory, adaptation and history

ACTIVE_CORE = A, B, C, D. ACTIVE_OPTIONAL is empty. A is
COMPOSITION_ONLY_BENCHMARK_AND_MATCHED_ACCOUNTING_COMPARISON, not the preferred
estimator of a latent result. A/B/C are modes of one matched accounting construction,
not three independent confirmations. D is a separate asymmetric comparator.
DEFERRED, outside this release: smooth comparator, constraint envelope, hierarchical
counterfactual. EXCLUDED_FROM_CURRENT_SCENARIO_RELEASE: KYHT latent-mechanism fitting.
CONTEXT_ONLY, not a scenario estimator: historical baseline. There is no open model slot.

Design was developed after existing descriptive, inferential, temporal, historical and
documentary results had been seen. It is not preregistration or outcome-blind research.
No real A/B/C/D scenario totals or shares had been computed/opened at this freeze.
A/B/C are researcher-defined conditional transformations; D is a documented adaptation.
Any model added after scenario reveal requires a separate disclosed follow-up and may
not silently enter this release. No calibration-until-pass or output-driven rescue.

All predecessor packages, proposals on disk, source data, contracts and archive indices
remain unchanged. Original L FAIL, A association PASS with source-sensitive formal
result, L-B PASS/RETAIN, H computational abort, HC1/HF2 numerical history, H-C FE2
numerical FAIL/scientific NOT_RUN, 2B failures and historical version/abort history persist.
Scenario A is NOT Stage3A association A; use namespace SMZ for every ID.

Counterfactual truth remains NOT_IDENTIFIED. No fraud/violation probability, recovered
true result, honest baseline, causal effect, anomalous/clean precinct label, method
voting, combined p-values, model ranking/average/consensus, or universal corrected-votes
quantity. The whole source frame is the project frame, not automatically the nation.
Existing evidence never defines target/reference membership or party selection.

## 2. Source versions, fields and scope

Current primary: `paper_primary__evidence_20260927`, inherited metadata 87,736 UIKs,
84 regions, 2,818 official TIKs; these counts are NOT recomputed by this contract freeze.
All A/B/C/D grids use primary, S1, S2a, S2b. Source mappings are the unchanged mappings
in `docs/STAGE3A_SENSITIVITY_CONTRACT_20260928.md` and its source manifest.
Primary exact membership/selectors and hierarchy: the universe freeze and
membership_sources/design files under `outputs/stage3a_v2/universe_20260927/`.
S1 removes the registered 88 conflict UUIDs (87,648 rows). S2a retains primary UUIDs
and substitutes whole historical alternative vectors for those 88. S2b retains primary
UUIDs and substitutes whole fresh vectors only for the two registered revisions.
S2a/S2b are competing variants, never stacked. S3 is IDENTITY_WITH_PRIMARY, no rerun.
No new territory, party, source or exclusion; no old 87,734-row universe substitution.

Canonical variables: UUID; resolved source region; official election `tik_uuid`;
n=voters, I=issued, V=valid, C_j for ALL ten parties in `src/data/schema.py`;
J=known invalid under the frozen source-version resolution, otherwise UNKNOWN.
An unavailable alternative or unknown invalid never causes a new exclusion.
Raw source fields and resolved semantics must both remain traceable. Exact source hashes,
full-vector selection and identity joins must pass before future execution. No name-based
TIK proxy. No historical identity bridge. Party order/ER alias comes from the bound schema.

Source integrity requires unique UUID, validated hierarchy/version membership, finite
integer n,I,V,C; n>0, 0<V<=I<=n, C_j>=0, sum_j C_j=V. Where J is known require integer
J>=0 and V+J<=I under inherited primary semantics. Mismatch stops the variant without
row/region exclusion, imputation, clipping or repair. Missing source/design binding stops
execution. Source issues are not model non-applicability. No raw values are changed.

I/n is the frozen issuance alias, not automatically ballot-box participation. V is not I.
I-V is not automatically invalid. No paper/DEG inference, urban/rural reconstruction,
new source priority, latest-version substitution or source/outcome selection is allowed.

Each source variant rebuilds scenario ranks, bins, donors, weights and support from its
complete selected frame. Do not reuse Stage3A pairs, folds, L-B neighbours or supports.
These scenario rules require none of those earlier objects. Source sensitivities are
dependent measurement comparisons, not replications or causal source effects.

## 3. A/B/C shared design: exact and original-table only

For every official TIK g, rank ALL its selected-source UIKs before model exclusions.
Compare t_i=I_i/n_i by exact integer cross-products. Let N_g be its row count,
L_i the number with strictly smaller t, E_i the complete equal-t group size including i.
Midrank r_i=(L_i+E_i/2)/N_g. No UUID tie-breaking, percentage rounding or percentile
interpolation. Ties enter/leave together. If every t is equal, every rank is 1/2.

Reference intervals inclusive: R1=[1/4,1/2], R2=[1/4,5/8]. Targets inclusive:
T1=r>=3/4, T2=r>=7/8. References/targets never overlap. These are scenario selections,
not anomaly rules. No outcomes or evidence labels select the ranges.

For target i, D_i contains ALL reference rows k in the SAME official TIK satisfying
1/a<=n_k/n_i<=a; D1:a=5/4, D2:a=3/2. Exact inclusive comparisons. No k-nearest
restriction, smoothing weight, size band, regional/national fallback or expansion.
M1 requires at least 3 donors; M2 at least 5. In both cases, sum_D V>0 and
max_D V_k / sum_D V <= 1/2. This dominance limit is structural, not a confidence bound.
Support does not depend on individual party quantities or the direction/size of a change.

Mutually exclusive target disposition order:
1 NO_REFERENCE_IN_TIK; 2 NO_SIZE_LOCAL_DONOR; 3 INSUFFICIENT_DONORS;
4 ZERO_REFERENCE_VALID; 5 DONOR_DOMINANCE; 6 SUPPORTED.
Source integrity failure takes precedence and stops execution, never becomes disposition.
Non-target rows are NOT_SELECTED; unsupported targets retain original values and are
SCENARIO_NOT_APPLIED, not validated/honest/zero-effect targets. Supplemental flags may
overlap, mutually exclusive accounting reasons may not. No renormalization of coverage.

All 2x2x2x2=16 designs are mandatory. Default: R1-T1-D1-M2. No coverage-based default
promotion. If default has no support it is NOT_APPLICABLE_ON_THIS_DESIGN; no alternative
becomes default. Per-source support IDs: SMZ1:{source}:{R}-{T}-{D}-{M}; register future
membership hashes as analysis views, never change base universes. No membership is
materialized at this freeze.

Shared objects per source/design: exact selected frame, target set, donor sets, support,
n/I/V/J/C original arrays, q and tau. Persist object IDs/hashes before transformations.
Compute q_j=sum_D C_kj / sum_D V_k; tau=sum_D I_k / sum_D n_k from original data ONCE.
q is valid-weighted composition; tau is voters-weighted issuance. Never update ranks,
donors, tau or q after any transformation. No references to another scenario's outputs.

## 4. A/B/C formulas and accounting

Let p_ij=C_ij/V_i, p*_ij=(1-lambda)p_ij+lambda q_ij,
Iref_i=n_i tau_i, s_i(mu)=(1-mu)+mu Iref_i/I_i.
lambda and mu independently belong ONLY to {0,1/4,1/2,3/4,1} in this execution release.
No continuous slider executions; a later display of exact interpolation needs its own
UI authorization and cannot create another scientific parameter search.

For every supported target tau_i<=I_i/n_i MUST hold by the rank/reference ordering.
With positive donor n and disjoint ranks the ordering is strict. Failure is
DESIGN_INTEGRITY_FAILURE/STOP, never a cap. Thus 0<=s<=1. No arbitrary numeric tolerance.

A: I^A=I; V^A=V; C^A_j=V p*_j; n^A=n; known J^A=J.
B: I^B=s I; V^B=s V; C^B_j=s C_j; n^B=n.
C: I^C=s I; V^C=s V; C^C_j=s V p*_j; n^C=n.
For B/C, known J*=s J and known R*=s(I-V-J). R is an arithmetic remainder, not a
diagnosis or behavioral mechanism. If J unknown it remains UNKNOWN, R remains UNKNOWN;
only the combined I*-V*=s(I-V) is defined. No invented invalid or scenario cast.
Where J known, V*+J*+R*=I*; where J unknown no separate J*/R* identity is asserted.
All parties nonnegative; sum_j C*_j=V*; n unchanged; V*<=I*<=n. For A sum_j delta C_j=0.
For B/C sum_j delta C_j=delta V. No vote removal/transfer mechanism is inferred.

A equals C at mu=0; B equals C at lambda=0; source identity at both zero. Exactly:
delta C^C = V(p*-p) + p(V^C-V) + (V^C-V)(p*-p).
The three terms are composition, intensity and arithmetic interaction; they are not
causal effects. Summation preserves this count identity, not a naive share identity.
Native UIK and aggregate counts/shares are defined; aggregate share is ratio of sums,
never mean of shares. If a scenario aggregate valid denominator is zero, share is NULL
with UNDEFINED_ZERO_DENOMINATOR; preserve defined counts and do not impute a share.
Fractional values are vote equivalents, not reconstructed integer ballots.

A has 16x5=80 configurations/source; B likewise. C has 16x25=400/source including the
A/B edges and identity. Canonical combined A/B/C lattice = 400/source, 1,600 for four
sources. A/B aliases are reports of the SAME objects/results, not independent re-runs.
Defaults A lambda=1; B mu=1; C lambda=mu=1, on the unchanged default design.

## 5. D — D_KSP_ISSUANCE_SIGNED_2026_v1

Public name: deterministic regional adaptation of the proportional KSP method to 2026
issued/voters, ER focal party, signed adjustment. NOT exact historical replication, NOT
reproduction of a published approximately 34% result, NOT an estimate of violations.

Methodological reference: Kobak/Shpilkin/Pshenichnikov, arXiv:1205.0741v2,
https://arxiv.org/html/1205.0741 ; supporting author field definitions (a later work,
not proof of 2012 implementation): https://arxiv.org/html/1410.6059 , section 2.2.
These are documentary pointers recorded from the preceding discussion, not newly
downloaded sources or data dependencies of this freeze. The freeze does not assert
bit-exact historical reconstruction. Proportional histograms, lower-range fit and signed
tail residual are retained. Exact historical field mapping for threshold weight, bin
boundary handling, failure rules and jitter's role in numerical estimates are not fully
established. Do not supply missing rules from media summaries or their headline number.

Adaptation choices: current frame; regional geography; no urban/rural classifier or manual
regional exception; valid-weighted threshold; exact bins; no jitter/smoothing; explicit
zero-intercept unweighted LS and support minima; exact signed accounting; scenario-valid
share denominator; electorate gate; explicit statuses. No historic exclusions from other
tests migrate here. Issued/voters is documented author-compatible semantics, not a claim
of full historical source equivalence. Old primary/other-model failures are not repaired.

Focal party = schema alias `er`, prospectively named for the historical comparator and
original comparison question, NOT selected by Stage3A. Others=sum of the nine remaining
parties for fitting only; every non-focal party remains separately conserved. No leader
selection, all-ten-focal grid, or honest-label inference.

Stratum = resolved region, or official tik_uuid ONLY in D4. No national pooling,
reconstructed urban/rural, size matching, manual territory treatment or fallback.
Coordinate t=I/n. Bin width h=1/200 or 1/100; origin 0; [bh,(b+1)h), last includes 1.
Exact rational membership: b=min(floor(I/(n*h)),1/h-1). Empty bins retained. Never
round counts/percentages before binning. Equal ratios remain together. No jitter/RNG,
smoothing or rebinning at scenario values. No alternate origins.

For stratum s: w_b=sum_bin V, f_b=sum_bin C_er, g_b=sum_bin sum_nonfocal C.
For q in {1/10,1/5,3/10}, k=min{k:sum_(b<=k)w_b>=q sum_b w_b}.
Whole threshold bin is FIT; no fractional allocation. Fit bins b<=k, target bins b>k.
Report realized fit-valid fraction (may exceed q). Fit rule never optimized on party
residuals. Structural requirements: >=5 fit UIKs; >=2 informative fit bins with g>0;
>=1 UIK above threshold. These are deterministic floors, not uncertainty guarantees.

alpha=sum_fit(f_b*g_b)/sum_fit(g_b^2). Unweighted bin-level LS through origin, no robust
loss, extra weights, intercept or post-result coefficient bounds. g=f=0 contributes zero;
g=0,f>0 adds constant loss and provides no coefficient information. Zero denominator is
DEGENERATE_REFERENCE. Positive denominator and zero numerator means alpha=0, not failure.

Above fit: e_b=f_b-alpha*g_b, f*_b=alpha*g_b. Fit bins remain f*_b=f_b.
E_s=sum_tail e_b is SIGNED. No positive-part clipping, aggregate clipping, capping or
redistribution. Non-focal C*_bj=C_bj. F*_s=F_s-E_s; V*_s=V_s-E_s=sum_all C*_sj.
Negative E can increase focal counts/valid. Individual bin residual signs and signed
sum must be retained; cancellation is not hidden. Share denominator is scenario valid
on the same summation frame; original share denominator is original valid.

Electorate gate per transformed bin: 0<=V*_b<=sum_bin n. No cap if violated. Source
voters/membership and nine party counts conserved; focal counts, valid and composition
change. Scenario issued, invalid, cast, issuance remainder and UIK-level counts/corrections
are NOT_DEFINED. Original source issued/invalid remain provenance, not scenario constants.
No row allocation may be fabricated to make a map or common-support comparison possible.

## 6. D statuses, precedence, reporting extension

SOURCE_FRAME_UNSUPPORTED (source/hash/identity/schema/count failures) stops the source
variant before fitting. NUMERICAL_OR_IMPLEMENTATION_FAILURE stops its execution cell;
common kernel/integrity defect stops all affected cells. Neither may be hidden by identity
extension. No silent retry, exclusion, repair or specification switch.

Among structurally valid strata, mutually exclusive first-match precedence is:
1 NO_TARGET_SUPPORT (no UIK above threshold);
2 INSUFFICIENT_FIT_SUPPORT (fit UIKs<5; reason FIT_ROWS);
3 DEGENERATE_REFERENCE (sum_fit g^2=0);
4 INSUFFICIENT_FIT_SUPPORT (informative bins<2; reason INFORMATIVE_BINS);
5 UNDEFINED_SCENARIO_TOTAL (any impossible/negative bin/stratum count, electorate ceiling
  violation, or stratum scenario-valid<=0; preserve specific reason);
6 APPLICABLE.
Zero scenario-valid in one emptied bin permits NULL bin share, not failure if the stratum
denominator remains positive and other identities hold. Nonfinite computed quantities
are numerical failure, not ordinary undefined support. All diagnostic flags retained.

Zero adjustment is a result ONLY for APPLICABLE strata. Non-applicability is not zero,
no effect, clean, honest or evidence of absence. No threshold/bin/geography fallback.
Native result aggregates applicable strata, with corresponding source baseline. Full-frame
identity extension keeps each non-applicable stratum's source counts exactly, explicitly
SCENARIO_NOT_APPLIED; do not remove it from denominator. Publish both native and extended
scopes with UIK/voters/source-valid coverage and reasons. If none applicable, full-frame
identity is bookkeeping only, status NOT_APPLICABLE_ON_THIS_DESIGN, not a substantive zero.
Do not report a complete extended result after a source/numerical/integrity abort.

D0 region,q=.20,h=.005; D1 region,q=.10,h=.005; D2 region,q=.30,h=.005;
D3 region,q=.20,h=.010; D4 official TIK,q=.20,h=.005. Exactly 5, not factorial.
All four source variants =>20 cells. S3 identity only. Rebuild histograms/support for each
source; don't inherit primary bins even for same-UUID count versions. Different versions
are dependent measurement scenarios; no source variant rescues the default.

## 7. Common interface and comparisons

Required fields listed in output_interface.json apply to all outputs. Keep selected targets,
supported targets and units actually transformed separate. Coverage denominators are
UIKs/voters/source-valid in the explicitly named frame; TIK/region counts distinct.
No mixed-unit coverage. Source/result shares require explicit denominators. NOT_DEFINED
means unavailable by construction; UNKNOWN means missing source quantity; NULL with reason
means undefined arithmetic ratio. Never replace any with zero or imputation.

A/B/C native unit is UIK, with all-party aggregates. D native unit is stratum x bin with
stratum/frame aggregates. D target-bin UIK membership may be counted, but actual transformed
UIKs and per-UIK corrections are NOT_DEFINED. Each non-focal count stays separate.
Use source/scenario valid and signed delta valid when defined. No universal adjusted-votes
metric. Rounding for display never feeds accounting; unrounded values remain auditable.

A-B, A-C, B-C = MATCHED_ACCOUNTING_DECOMPOSITION only for identical source/design/reference
objects and corresponding parameters. A/B/C-D = DIFFERENT_QUESTION_JUXTAPOSITION.
Within A/B/C changed reference parameters = SAME_QUESTION_DIFFERENT_REFERENCE, with support
changes disclosed. Different-support restricted comparisons = COMMON_SUPPORT_DIAGNOSTIC_ONLY
when defined; keep original reference objects, do not refit on intersections. UIK A/B/C vs
bin-only D corrections = NOT_DIRECTLY_COMPARABLE. No forced row allocation.
Optional common-support output is restricted to A/B/C for this release; D has no such
row-level diagnostic. Native and full-frame results never silently change denominators.

## 8. Qualification and reveal boundary

Freeze only now. Future stages require separate authorization. Order:
1 contract freeze; 2 implementation; 3 synthetic/accounting qualification;
4 design/support audits without substantive party-result review where applicable;
5 pre-release review of ALL four cards; 6 real scenario execution;
7 preserve complete immutable results; 8 substantive cross-model comparison.

A/B/C future design audit may read only UUID, region, official TIK, n,I,V and source integrity
metadata. Numeric V is needed for dominance and valid coverage; not just availability.
It may calculate ranks/donors/support/overlaps/distances/reasons/counts and coverage. No party
columns, q, scenario totals, earlier evidence labels or direction of adjustment. D source/
bin/threshold structure can be checked using n,I,V; informative-g and coefficient/total
applicability necessarily require parties and occur only in separately authorized sealed
real execution. Do not mislabel this as party-blind design qualification. Prior to opening
real totals D requires fixtures PASS and structural audit PASS; all real applicability and
accounting statuses are validated before its committed outputs are interpreted.

All four core cards must have passed pre-specified pre-execution qualification or reached
a documented frozen STOP before any real party scenario totals are substantively reviewed.
Synthetic qualification is NOT empirical scientific calibration. Underlying raw party
counts may be processed by an authorized executor, not displayed to tune the method.
Execute accepted cells sequentially if desired, but keep party totals sealed until every
core family is complete or STOP, and packages/statuses committed. One valid STOP does not
hold other families indefinitely. No replacement model or output-driven parameter choice.

All required checks in qualification_registry.json must PASS. Incomplete required check,
substantive mismatch or exception => QUALIFICATION_STOP for affected family; common shared
object/kernel failure blocks A/B/C together. No retry/repair-until-pass within the qualified
run. An implementation defect may be documented, but changes need separate review and a
new execution freeze, never reinterpretation of a STOP. No Type-I calibration, p-values,
bootstrap uncertainty or model-based credibility interval for these transformations.

Exact rational algebra is normative: integer input sums, rational memberships/coefficients/
transformations, exact conservation checks; decimal displays rounded only at export with
unrounded rational values retained. No output-dependent tolerance or optimizer. Synthetic
heterogeneity may create nonzero adjustment without violation: expected limitation, not a
criterion to tune until adjustment vanishes. No election outcome is a ground-truth test.

## 9. Resource ceilings and bounded execution

User requirement for D: one CPU process maximum, 8 GiB peak aggregate RSS, 3,600 seconds
wall for all20cells INCLUDING startup/source verification/I/O/reconciliation/serialization.
No per-cell reset. A source-local STOP does not reset budget. D qualification fixture stage
also has a separate 3,600-second/8-GiB/one-process ceiling.

Researcher/Codex operational choice authorized by freeze task: A/B/C complete design/support
audit across16designs x4sources: <=7,200seconds, <=16GiB aggregate RSS, <=4CPU processes.
A/B/C complete canonical scenario lattice across all sources: <=14,400seconds, <=16GiB
aggregate RSS, <=4CPU processes. Shared A/B edges not duplicated for resource accounting.
A/B/C synthetic/accounting qualification: <=3,600seconds, <=8GiB, <=4CPU processes.
BLAS/OMP/MKL threads=1 per process. Memory is coordinator+workers total, not per-worker.
Limits include preparation and I/O. These are generous operational caps, not measured ETAs
or scientific thresholds. RESOURCE_STOP preserves partial artifacts but releases no complete
result. No renting compute, narrower grid, dropped strata, altered formula or automatic
extension/retry to fit a budget. Future user operational amendment must be explicit.

## 10. Governance, preservation and next gate

Current operation consumes contracts/manifests/schema metadata only. No real response table
is parsed, no support computed, no scenario engine implemented. Hashing source selectors
does not read their electoral values semantically. Updated live handoff/state reference
this contract; predecessor versions remain in before/ and their manifests remain untouched.
Scoped governance checker is `python3 -m src.scenario_zoo_governance check`; the frozen
legacy research_handoff dispatcher is not edited or used to republish old stage narratives.
Snapshot-aware predecessor checks resolve old mutable handoff/state entries to before/.

Freeze PASS establishes specification consistency ONLY. It does not establish support,
usefulness, numerical qualification, scientific adequacy or authorization to execute.
Exactly one recommended next task: separately authorize implementation and synthetic-only
accounting qualification of the four frozen cards, without real support/scenario runs.
