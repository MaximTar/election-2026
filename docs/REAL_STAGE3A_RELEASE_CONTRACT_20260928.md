# Real Stage 3A — prospective reporting and release contract

Preparation only. The user explicitly RETAINS L-B for the main study after its completed
usefulness review. A calibration PASS; L-B calibration PASS and usefulness RETAIN;
original L permanent FAIL; H-C FE2 numerical FAIL, scientific calibration NOT_RUN,
closed for the main study. No model selection or outcome tuning remains authorized.
No real responses may be opened in preparation, freeze or synthetic equivalence checks.
Actual execution requires a separate explicit user authorization and guarded command.

## Frozen inputs and procedural boundary

Universe `paper_primary__evidence_20260927`: 87,736 UIKs,84regions,2,818officialTIK,
99,360,758voters. Use immutable universe freeze and `membership_sources.csv`: existing
87,734 canonical rows retain accepted old source versions, two additions use the specified
fresh source. No newest-version substitution. Official `tik_uuid` only. No historical,
directory, temporal, incidents or observer information enters either procedure.
Verify source SHA256 on opaque bytes before guarded loading. Exact UUID/region/TIK/voters
design, positive integer counts,0<V<=I<=n, nonnegative integer parties summing to V required.
Primary policy already has positive V. Mismatch => STOP, never trimming or renormalizing.
Region identity is anchored to frozen design plus exact official hierarchy; raw alternative
region labels cannot silently replace accepted canonical labels. No source collection.

## A primary

Unchanged 3,592UIKs/1,796pairs/955TIK/80regions/3,013,626voters. Adjacent UUID exact-size
pairs, one categorical projection, TIK-joint full-vector orientations,B1999,add-one >= ties,
two-sided Holm10 at.05. Frozen standardized statistic and realised effect unchanged.
One table for all ten parties in original frozen order: party, realised projection effect,
standardized score, raw p, Holm p/decision, projection-averaged descriptive effect
sum(DeltaT*DeltaY)/(2M), support and identification status. No new effect CI or test.
maxT remains diagnostic artifact, not alternate decision. Zero scale for any party =>
STOP joint A, not removal of that party. Min raw p=.0005, never zero. No extra B or seeds.
Real RNG key prefix `[real-stage3a-release-20260928-v1,A]` passed to unchanged v2 RNG;
its existing projection/orientations role keys remain distinct. Fresh synthetic pre-open
keys NEVER become real keys. Record projection and reference reproducibility metadata.

## L-B all-target transport, without changing its kernel

87,729supported UIKs/84regions/2,811TIK; seven prior singleton exclusions/9,560voters;
zero new exclusions. All five frozen folds, other-four-fold training. Same donor/locality
kernel, base weights for party composition, rank rule, integer boundary correction,
zero-variance treatment and cell-only comparator as qualified. I conditioned on n;
V conditioned on observed I; party counts conditioned on observed V. Using these
conditioning inputs is allowed; target response itself must not determine its calibration
membership or own quantile. No PIT/density/anomaly probability is released as calibrated.

For EACH target UUID i in fold f/cell c, sample m=min(99,M_fc-1) rows uniformly without
replacement from that frozen pool excluding i. PCG64 first128bits big-endian SHA256 of
compact UTF8 JSON `[real-stage3a-release-20260928-v1,LB,calibration,f,c,uuid]`.
The same ordered sample is used for all12responses and comparator. Save its entire integer
index matrix, index->UUID map and a SHA256 per target sample; not just an opaque confidence
score. Model/moment caching may depend only on fixed fold/training inputs and is equivalent
to computing each target/calibration row separately; no target-dependent refit.

Proof of transport: conditional on a uniform target i, the old ordered uniform sample's
remaining members are exactly a uniform sample without replacement from pool minus i.
The new table enumerates all targets with that conditional law. For fixed training data
and finite score vector, uniform rank gives average coverage >=ceil(.95*(m+1))/(m+1)
with conservative ties/full-support small-m behavior. By linearity this bounds expected
average coverage of the all-target table over calibration RNG. No independence assumption
across UIKs is needed for that expectation. This is not guaranteed realised coverage,
pointwise/TIK/region coverage, simultaneous12response coverage or future-election validity.
All-target transport is a reporting extension, not a new anomaly test/calibration battery.

Primary all-target outputs for LB AND comparator: UUID,region,officialTIK,fold,cell,response,
observed count,denominator,integer endpoints,position,normalized width,interval score,
normalized interval score,empty/near-trivial flags,fallback/training/donor metadata,
sample identifier. Near-trivial=width/max(den,1)>=.9. Empty interval has position `empty`
(fourth mutually exclusive category), coverage false and score +infinity. No forced
widening or dropping; below+inside+above+empty=N. Store numeric score NULL plus explicit
score_infinite flag for CSV/raw interoperability. Summary unconditional score is infinity
if any member score is infinite; finite contribution is separately labelled, never a
silently filtered mean. Integer bounds and comparator exact floating predicates unchanged.

## Primary summaries, weights, figures

Support table: full frame, A, L-B with UIKs/voters/regions/TIK and mutually exclusive losses.
1. All12responses (I,V|I,ten parties) for LB and comparator: position fractions,mean
normalized width,mean normalized interval score,empty/near-trivial fractions.
2. Eight frozen cells (voters-rank quartile x original TIK N<10/>=10),same metrics.
Within fold/cell equal UIK weight; within each cell average five folds equally. Overall
standardized summary averages eight cells equally: row weight1/(40*M_fc). Each cell's
five-fold summary weight1/(5*M_fc). All weights fixed from design before responses.
3. Separate row-weighted counts/fractions and metrics across full support; never called
the frozen equal-cell estimand. No electorate-weighted primary summary.
4. Full region and official-TIK appendices for12responses and both methods, fixed lexical
region/TIK/response/method order. Report numerator/denominator,support/voters,interval
widths. No local p-values,binomial CI,calibrated regional coverage or threshold-versus5%.
No disappearance of small groups; retain their denominators explicitly.
5. Comparator uses identical targets/calibration rows; comparisons descriptive, not model
selection. Width advantage is not efficiency at equal achieved coverage by itself.

Two primary figures only: response-level normalized width/miss fraction (both methods),
and eight-cell width/miss summary with all12responses visible. PNG+SVG+underlying CSV.
Figure axes/order/layout fixed; no outcome-based top selection. No 5% critical reference
line or significant color coding. Underlying primary tables remain authoritative.

## Interpretation and exploratory boundary

L-B miss: observed count outside this frozen interval. NOT a p-value, anomaly probability,
rejection of ordinary-election null, violation/mechanism evidence. Calibration can adapt
to shared structure also present in calibration rows. Low misses do not vindicate data.
A Holm rejection: incompatibility with the frozen orientation-exchangeability null on
exact-size support. NOT causality/fraud/additional-vote composition or national effect.
Nominal alpha.05 is distinct from synthetic FWER acceptance ceiling.075; do not claim
the latter empirically proves FWER<=.05 in all DGPs. Projection is noisy; signs of realised
and projection-averaged descriptive effects are both retained, not reconciled by new seeds.
A and LB share counts/support and are not independent evidence. No combined p/score.

Maps, top/bottom lists, individual cases, extra geography/rankings, future incident overlap
and any post-result chosen strata are secondary/exploratory. No new local significance
tests. A stored outside-interval indicator is not a precinct anomaly classification.
No fraudulent/honest labels, counterfactual totals, mechanism parameters or clean baseline.

## Sensitivity sequence and project exit

First commit immutable complete PRIMARY package, then review and separately authorize the
three promised sensitivity families: no-source-conflicts,alternative-conflict versions
(with separately identified fresh-main revisions if specified later),current complete-regions.
Their exact named source mapping/support and transport/calibration route must be frozen
before their outputs are inspected. No old complete-region universe substitution; rebuild
support/pairs/neighbours from the selected named design. No inferential sensitivity p-values
without transport justification/calibration. All promised variants reported regardless of
primary direction/significance. No rescue/new discovery based only on favorable variant.
Sensitivity execution is NOT included in this release command. New ideas are exploratory.
After primary technical checks and scoped robustness, proceed to evidence integration;
no automatic reopening of cross-sectional model development. Scenario layer separate.

## Adapters, pre-open checks, package and STOP

Frozen source files remain byte-identical. A numerical function and LPeer.fit are extracted
by AST from their frozen definitions: remove ONLY the explicit synthetic-only entry guard;
assert its exact shape, hash the remaining AST, compile with original globals. All numeric
statements and low-level kernels unchanged. New entry validates data provenance/counts;
real payload carries synthetic=False and origin=authorized_real_loader. Never pretend real
data are synthetic. CLI authorization is checked BEFORE opening a response file.

Pre-open tests: synthetic N1–N10,one fresh dataset per scenario on actual design; assigned
fold=(s-1)%5. Compare A complete outputs with frozen reference under identical RNG;
compare all eight L-B targets/intervals/comparator/moments against frozen reference using
identical calibration membership. These are equivalence checks, not empirical scientific
calibration or tests of PASS rates. Do not surface synthetic p-values/scores in review.
Toy full-census test:all target sampler disjointness/uniform conditional sample enumeration,
fixed seed/chunk-order and serial/two-worker equality,multi-response/comparator shared
membership,training-only target mutation,integer/ties/zeroSD/smallpool/empty boundaries,
weight sums,summary count reconciliation,source-origin guards,denominator/UUID violations,
undefined A scale STOP,atomic package/replay protection. No actual response loader invoked.
Frozen numeric equivalence rtol1e-10/atol1e-12; boolean/identity decisions exact.

Archive contract/config/kernels/source hashes/software versions,source metadata and pre-open
checks. Verify A and LB completed clearance and explicit user usefulness RETAIN.
Real execution writes a new `.building` directory, never overwrites/resumes a finished run;
only after all tables,figures,integrity checks and hashes succeed atomically rename to
the requested run_id and mark COMPLETE_FOR_REVIEW. On error preserve ABORTED artifacts,
no substantive interpretation/partial release; never silently rerun or exclude rows.
No figures/results printed during construction. Reviewer interpretation only after commit.

Governance: user requirements above; researcher choices are deterministic RNG/output ordering,
AST guard adapter and exact engineering checks; source constraint is frozen canonical frame.
Quantitative universe/denominator changes zero; alternatives rejected: random single-target
real report,common calibration sample silently changing law,new CI/local tests. Reversibility:
new prospective contract only; never post-result editing. No scientific gates/seeds of prior
calibrations changed. This preparation authorizes no real execution.
