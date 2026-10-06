# Stage 3A v1 — core-only applicability, calibration and identification audit

Freeze date: 2026-09-27. Authority: user accepted Path C and authorized specification,
implementation and synthetic engineering dry-run ONLY. Evaluation calibration has NOT
run. Real-response execution is absent from the CLI and prohibited. Manifest under
`outputs/stage3a/freeze/` binds this document, executable code, config, gate registry,
support, dependency versions, engineering corrections and test/replay records.

The executable specification is `src/stage3a/{spec,design,generators,models,association,gates,runner}.py`.
Both document and code are binding. A discrepancy is an implementation STOP, not
permission to choose the convenient interpretation. No parameters change after freeze.
No dropped family returns within v1. Future substantive execution requires a new task
and the separate task-specific release gate below.

## 1. Reconciliation and independent task gates

Primary frame: `paper_primary`, snapshot `20260923T110217085076Z`, 87,734 UIK,
84 regions, 2,818 official TIK; voters99,359,922. No base exclusions or promotions.
Identity whitelist: UUID, resolved region, exact official tik_uuid, integer voters n.
Source flags remain audit metadata, not explanatory regressors or selection variables.
Neither directory, geography/type guesses, history, temporal outcomes, past anomaly
scores nor UIK number enters any predictor, matching rule, generator or party selection.
Published n is conditioned upon, not declared exogenous or a pre-process population.

Let I=issued, V=valid, C=(C_0,...,C_9), T=I/n, Y=C/V.
V is composition exposure. I−V is NOT labelled invalid. Unknown invalid is not zero.
All party labels are handled identically; no party selected using old findings.
Future real-vector order, if separately released: rodina, er, kprf, pensioners,
new_people, direct_democracy, greens, communists_russia, ldpr, sr. Future A seed key
is [real-release,snapshot_id,exact_registered_universe_name], with projection and
orientations suffixes from the frozen kernel. No real seed search is permitted.

| Task | Estimand and unit | Conditioning | Allowed output after separate release | Gate |
|---|---|---|---|---|
| P, prediction | Predictive joint mass of I,V,C for a held-out UIK | published n, region, official TIK and training responses only | proper scores, conditional-factor predictive intervals/calibration, support | PASS independently per family AND prediction target only if every binding scenario/check passes; FAIL on any binding FAIL; otherwise INDETERMINATE/STOP |
| A, association | Pair-support mean covariance functional theta_j=(1/(2M)) sum_pairs E[(T_l−T_r)(Y_lj−Y_rj)]; no causal effect | exact n and same official TIK, fixed UUID pairs | randomized unbiased estimator using categorical projection, cluster scores, raw/Holm p under declared null, MC limitations | sole A family must pass every N1–N8 binding gate, fit/support requirements and implementation review; failure does not erase P results |
| C, identification | Counterfactual count vector under a specified absent/alternative mechanism | same available observables; no privileged core | analytical nonidentification witness and synthetic known-baseline artifacts only | NOT_IDENTIFIED now: exact observational equivalence with different baselines. Neither P nor A PASS releases reconstruction |

Prediction targets are separate: within-known-TIK UIK holdout and held-out-TIK
prediction. They are not two estimates of the same generalization task. Stage output is
a vector of task statuses, never an all-purpose PASS. For each prediction target, at
least one of two predeclared co-primary families must PASS for predictive applicability;
both FAIL means FAIL; no PASS with an incomplete/indeterminate family means STOP.
No model is promoted from sensitivity. Counterfactuals remain closed even if all P/A pass.

## 2. Family dispositions BEFORE evaluation

* **H_count_ridge retained for prediction only.** Penalized hierarchical beta-binomial /
  Dirichlet-multinomial factorization, defined below. It estimates observed-count laws,
  not a no-intervention baseline. No p-values derived from its Hessian.
* **L_peer_mixture retained for prediction only.** Local continuous-size empirical
  predictive mixture, defined below. It is not a geographic-neighbour model and is not
  an exchangeability/permutation kernel.
* **A_exact_size_categorical_projection retained for association only.** New independent
  justification/calibration, not old 2% matching or transfer of temporal validity.
* **Standalone robust/smooth counterfactual comparator DROP.** No independent justified
  counterfactual reference; no residual trimming, robustness-as-honesty assumption or
  revival of failed spline/bootstrap. H already provides one precisely specified smooth
  predictor; no extra smoothing zoo.
* **Proportional/Shpilkin: D — DROP from fitted candidates, including real descriptive
  fits.** Stable comparable reference core and invariance of relative preferences across
  turnout are not established. Ordinary preference/type mixtures can generate the same
  turnout–share structure. Reference selection on observed outcomes would decide the
  answer. No estimator is specified or run for this family. A shared identification
  witness is retained, not relabelled as a fitted Shpilkin challenge.
* **KYHT: D — DROP from fitted candidates, including real descriptive fits.** The
  target mechanism fraction/counterfactual depends on baseline distribution and allowed
  alternatives. Ordinary multimodality, correlated mobilization/preferences and the
  exact equivalence construction below prevent identification on this broad core-only
  problem. A restricted toy parametric mechanism would change the question. No fitter,
  mixture-component search or mechanism parameter output. This is a scope/identification
  decision, not an empirical calibration failure attributed to an unrun model.
* **Historical panel EXCLUDED.** 2C.1 remains NOT_IDENTIFIED; all field/continuity gates
  remain unchanged.

P-family uncertainty is predictive, not uncertainty for a causal mechanism. Agreement
between fitted models would be robustness conditional on assumptions, never proof of
identification. Original literature is context, not imported validity: [KYHT author
version](https://arxiv.org/html/1201.3087).

## 3. H: complete mathematical specification

z=clip(log(n/1000),−5,5), b(z)=(1,z,sin z,cos z,sin2z,cos2z).
For each response block, eta_i=b(z_i) beta + a_region(i)+b_TIK(i).
No TIK/region size slopes, knots, tuning, cross-products or response-derived features.
TIK effects are distinct UUID parameters nested in region, not names.

I~BetaBinomial(n,80 pI,80(1−pI)); pI=logistic(etaI).
V|I~BetaBinomial(I,200 pV,200(1−pV)); pV=logistic(etaV).
C|V~DirichletMultinomial(V,60 pC); pC=softmax(etaC_0,...,etaC_9).
The three blocks share covariates but have separate coefficients. Within this plug-in
predictive law, rows are conditionally independent given fitted effects. This modelling
assumption is tested against cluster-dependent DGPs; it is not used as an iid UIK SE.

Minimize −sum log mass + .5 sum(beta_k/sd_k)^2. sd: intercept10,
five global size terms1.5, every region effect.75, every TIK effect.75, every party
identically. All ten logits have the penalty, fixing the softmax common-shift redundancy.
This is penalized MAP/plug-in prediction, NOT integrated Bayesian posterior prediction.
Fixed precision parameters are not estimated. Multiply the WHOLE objective and gradient
by 1/Ntrain for numerical scale only; same minimizer and prior penalty.

Algorithm SciPy L-BFGS-B with analytic gradients; all coefficients initialize0;
coefficient bounds[−15,15]; maxiter1000,maxls40,gtol1e−6,ftol1e−12. No restarts or
initialization search. Success requires optimizer success, finite objective/coefficients,
max absolute gradient of mean objective<=1e−4 and no coefficient within1e−6 of a bound.
Any block failure fails the entire replicate/family/task. Stable logistic complements
use logistic(−eta), not numerical subtraction1−logistic(eta). New/unseen TIK/region
effect is0, explicitly prior-centre prediction without extra parameter-uncertainty draw;
held-out-TIK undercoverage will fail the relevant gate, not trigger automatic widening.
Zero party counts enter full DM mass; zero binomial exposures have mass1 at zero.
No pseudocount is added to training observations.

## 4. L: complete mathematical specification

For target i, eligible donors are training rows only. Pool = same official TIK if>=8
training donors; else same region if>=8; else all training if>=8; otherwise UNSUPPORTED.
This prediction-only fallback is always logged; it grants no local-association validity.
Select min(32,pool size) nearest |log n_k−log n_i|, ties by UUID.
h=max(log1.10,largest selected distance), w_k proportional exp(−.5(distance/h)^2).
No caliper exclusion, fitted bandwidth or outcome-dependent donor choice.

Component k has I~BB(n_i,I_k+.5,n_k−I_k+.5), V|I~BB(I,V_k+.5,I_k−V_k+.5),
C|V~DM(V,C_k+.5). The SAME donor indexes all three factors. Joint predictive mass
is sum_k w_k fI_k fV_k fC_k. Conditional V|I uses donor weights proportional w fI;
C|I,V uses w fI fV. This conditioning is part of a joint response law, not a baseline
confounder adjustment. Predictive component probabilities remain on the simplex.
Fit is closed form; no optimization, initialization, convergence tuning or overdispersion
fit. No observation is edited by the .5 distribution parameter. Training pool<8,
nonfinite probabilities or scoring failure fails support/replicate as applicable.

Both P models score three conditional factors and twelve scalar conditional margins
(I, V|I, C_j|I,V). Joint log score is the FULL joint mass, not a sum of ten marginal
party masses. Predictive intervals use1,999 independent draws per scalar margin,
equal-tail .025/.975 quantiles with NumPy method=inverted_cdf. Report interval width,
randomized discrete PIT=F(k−1)+U*Pr(k), conditional mean prediction error and squared
error, marginal CRPS estimate E|X−y|−.5E|X−X'| from two independent1,999 draw streams.
Exact mixture means/CDFs/masses used for PIT. No fitted-parameter interval is claimed.

## 5. A: exact-size randomized coarsening, estimand and null

Inside each (official TIK, exact integer n) cell sort UUID, pair adjacent records
without reuse; final odd row is unsupported. No TIK original-N threshold; >=1pair/TIK.
Do not use any outcome in pairing, support or ordering. Materialized support:
**3,592 UIK /1,796pairs /955TIK /80regions /3,013,626voters (4.0941938% of primary)**.
87,734=3,592matched+84,142odd-cell/unpaired rows; excluded voters96,346,296.
Predeclared minimum:2,000rows,40TIK,20regions,2%primary rows, all must hold.
No fallback to region, relaxed size equality or old2% pairs.

For each retained UIK independently draw one Z_i in ten-category one-hot form with
Pr(Z_ij=1|C,V)=C_ij/V. Exactly ONE projection stream, fixed before results; no repeated
seed search or favourable averaging. This Rao-information-losing projection has
E[Z|C,V]=Y, so sum ΔTΔZ/(2M) is an unbiased randomized estimator of the pair covariance
functional above. It is NOT the full-data Pearson correlation. It sacrifices power to
remove dependence of categorical response noise on differing valid denominators in the
synthetic multinomial/mixture laws. It does not make unobserved types exchangeable.

H0: conditional on exact design, turnout and unordered projected compositions, the
required within-pair outcome orientations are jointly invariant under simultaneously
swapping ALL accepted pairs within each official TIK, independently between TIKs.
For individual party claims the corresponding marginal orientation invariance is
required. This is stronger than an arbitrary zero conditional covariance. No general
validity against all zero-covariance dependent processes is claimed. Shared region/TIK
levels are not shuffled. Region-dependent violation of orientation invariance is a
limitation; it is tested in N7 but cannot be ruled out by finite simulations.

S_gj=sum_pairs_in_TIK ΔTΔZ_j. Statistic z_j=sum_g S_gj/sqrt(sum_g S_gj²).
Randomization:1,999 independent joint Rademacher signs per TIK; each sign applies to
every pair AND all ten party components in that parent. No party-independent shuffling.
Two-sided raw p=(1+#|z*_j|>=|z_j|)/2000. Zero scale for any party means the entire
ten-party replicate NOT_IDENTIFIED, never silently dropping that party.

**Primary correction Holm across ten raw p**, fixed before evaluation. This avoids
claiming maxT strong control from unverified subset pivotality. Same draws preserve
composition. Joint maxT adjusted values are stored as diagnostics only and cannot
replace Holm after results. No local p-values or UIK classifications. Parent-level
score law provides uncertainty; no iid-UIK asymptotic p-value or SE. Coarsening seed
randomness is included in every independent calibration replicate.

## 6. Frozen support/folds/targets

Training/test splits never use outcomes. K=5. Within known TIK, sort UUIDs by
SHA-derived fold key and assign round-robin0..4 inside each TIK. Evaluate only TIKs
with original N>=2:87,727UIK/2,811TIK/84regions/99,350,362voters;7singleton rows and
9,560voters are unsupported for that estimand. Held-out-TIK: order TIKs by SHA key
within region, assign round-robin0..4; all87,734UIK eligible, all2,818TIK/84regions.
An unseen region in training gets the explicit zero/global predictive fallback; no
held-out-region generalization claim. Evaluation fits all5folds per replicate.

Actual strata, fixed before responses: all; four rank quartiles of voters (ties UUID);
original TIK N<10,10–29,>=30. They are diagnostic partitions, not coarse conditioning.
All eight strata are nonempty in both actual prediction designs. Minimum aggregate
support40TIK/20regions;100% of the task-specific design must remain evaluable. Empty
required stratum/support change is structural STOP, not a post-hoc omitted gate.

Per independent dataset/task/stratum, draw ONE uniformly selected eligible held-out
probe using a design-only stream shared by H/L. Coverage/PIT indicators across datasets
are independent Bernoulli trials; no pooling87k correlated UIKs into binomial precision.
All5training folds must converge, not merely the probe folds. Probe scores estimate
stratified prediction performance. Electorate-weighted scores multiply by n_probe /
mean(n_stratum); do not renormalize a single probe to1. Report both weightings and MC SE.
Complete underlying probe IDs/weights/scores preserved. These are calibration scoring
samples, not a change to the base universe or an electoral analysis subset.

Future change of source/support requires a new named view and its OWN actual-design
calibration, not automatic transfer. The three design views are registered in state;
new support issued/valid/party totals are intentionally NOT_READ before information
release, not reported as zero. Whole primary unchanged verified by source hashes.

## 7. Executable synthetic DGPs

Each replicate uses all actual n and nesting, but no real I,V,C/T/Y, party totals,
previous coefficients, temporal labels or directory data. Symmetric indices j=0..9,
phi_j=2pi*j/10. z=clip(log(n/1000),−5,5).
Independent normal region/TIK intercepts have SD .25/.35 separately for T and ten Y
logits. Common base fT=.45sin z+.2tanh z;
fY_j=.35sin(z+phi_j)+.15cos(2z)cos(phi_j).
Independent row eT~N(0,1), eY_j~N(0,1); sigmaT=.2,sigmaY=.25.
etaT=.2+aT+fT+sigmaT eT; etaY_j=aY_j+fY_j+sigmaY eY_j.
pT=logistic(etaT), pY=softmax(etaY); q=.98−.03logistic(z).

I~Binomial(n_true,pT), V~Binomial(I,q). Redraw BOTH I,V for a row with V=0 using
the same pT/q until V>0; maximum100,000 loops then generator STOP. No clamping/zero
imputation. Thus the generator is explicitly conditioned on positive valid, matching
the base frame; fitted H/L do NOT automatically inherit this truncated law. Party
counts C~Multinomial(V,pY) via exact sequential binomial sampling. Integers,
0<V<=I<=n, C_j>=0, sum C=V checked every replicate.

| Scenario | Changes to base law | Binding purpose |
|---|---|---|
| N1 | none | P and A smooth nonlinear null |
| N2 | fT=2tanh(80sin z); fY_j=1.5tanh(80sin z)cos phi_j | P and A steep-gradient stress; arbitrary close but unequal n can differ |
| N3 | add .45 bT_TIK sin3z+.2 cT_TIK z to fT; analogous independent ten-party bY,cY standard-normal TIK coefficients to fY | P and A local nonlinear curves |
| N4 | sigmaT=.1+.5logistic(z); sigmaY=.1+.7logistic(−z) | P and A heteroskedastic noise |
| N5 | independent eT,eY~Exp(1)−1; additionally pY~Dirichlet(12 softmax etaY) | P and A skew/overdispersion |
| N6 | independent Bernoulli(.5) types uT,uY: add1.3(2uT−1) to fT,1.6(2uY−1)cos phi to fY | P and A ordinary independent multimodality |
| N7 | add independent T-region/TIK normal shocks SD.6/.5, and separate Y-region/TIK ten-vector shocks SD.6/.5 | P and A clustered dependence; no permutation of regions |
| N8 | fT=.8sin2z+.3z; fY=.7cos(3z+phi)−.25z sin phi | P and A differing size functions |
| N9 | independent measurement flag m~Bern(.1); n_true=max(1,floor(.8n)) if m; add .8m cos phi to fY; otherwise n_true=n | P binding ordinary measurement uncertainty; NOT A Type-I null |
| N10 | shared u~Bern(logistic(.5z)); add1.2(u−.5) to fT and1.4(u−.5)cos phi to fY | P binding ordinary latent-type heterogeneity; identification stress, NOT A Type-I null |

All unlisted parameters remain base values. N9 is a prospective uncertainty stress,
not an estimate of measurement-error frequency in the election. N10 contains real
conditional association from omitted ordinary type; its rejection would not be Type-I
error. No substantive N9/N10 election-mechanism claim. No election mechanism exists in
any of these ten ordinary DGPs.

Seed derivation: PCG64 seeded by first16SHA256bytes, unsigned big-endian, of UTF-8 JSON
array [namespace,*parts], ensure_ascii=False,separators=(comma,colon). Namespace
`stage3a-prospective-20260927-v1`. Parts for generator:
[stream,scenario,replicate,strength,sign,target,label]. Evaluation strength0/sign1/target0;
labels T_region,T_tik,Y_region,Y_tik,T_row,Y_row,T_curve,Y_curve,T_slope,Y_slope,
T_skew,Y_skew,T_type,Y_type,T_region_shock,T_tik_shock,Y_region_shock,Y_tik_shock,
measurement,shared_type,Y_dirichlet,turnout_valid_counts,party_counts are separate.
Design ordering is sorted UUID. Other streams are literal argument lists in code;
independent projection, reference signs, probes and predictive draws. Dry-run namespace
never shares evaluation streams. No synthetic generator is fitted to real responses.

## 8. Positives and exact observational equivalence

Positive A worlds use N1 with etaY += sign*lambda*eT*v_target;
v_target=1 for selected party, −1/9 for all others. lambda=.10/.30/.60; sign±1.
These are EXACT logit loadings, not claimed correlations .02/.05/.10 from draft.
1,000independent datasets per strength/sign; target=replicate mod10 gives100per party.
All ten tested every time, no privileged party. Monotone shared innovation sets target
association direction; actual count-level effect need not equal lambda. Report target
Holm power, family rejection, effect distribution, identification and exact binomial
95% intervals overall and per label. Power reporting is mandatory; there is no minimum
small-effect power gate and power never repairs a Type-I failure. All6,000 results
required before any A real release, including failed/zero-scale cases (count as no
discovery and show missing identification separately). No conditional power after
dropping failures. Positive draws may run after null assessment even if FAIL, but may
not unlock inference.

Identification witness: draw ANY synthetic observed law O=(n,I,V,C). World A:
baseline=O, no intervention. Let m=floor(C_0/5). World B: baseline C'_0=C_0−m,
C'_1=C_1+m, others unchanged; mechanism transfers m back1→0. World C: baseline
I'=I−m,V'=V−m,C'_0=C_0−m, others unchanged; mechanism adds those m ballots back.
All worlds yield EXACTLY the same observed O with different counterfactuals; counts
remain valid. Party0/1 are arbitrary synthetic coordinates, not selected real parties.
This establishes nonidentification over the allowed ordinary/alternative mechanism
class, without a fitted model or p-value. A fit agreeing across models cannot distinguish
these worlds. To identify a point would require independently justified restrictions
excluding alternatives (reference baseline invariance, intervention law, stable
population/measurement, or external identifying information). Core data do not supply
them. Outcome agreement does not add them. Counterfactual gate stays NOT_IDENTIFIED.

## 9. Exact binding gates, simultaneous uncertainty and STOP

Evaluation R=**5,000 per binding scenario**, fixed once, no sequential extension.
A B=1,999; add-one p-resolution=.0005; Holm10 smallest threshold=.005 has ten lattice
steps, rather than a single possible tail event. Predictive draws1,999 are not reference
p-values. R=500 rejected as too imprecise for the many simultaneous probability bounds;
5,000 permits nontrivial certification near nominal rates without relying on observed
fraction alone. R5,000 still may yield INDETERMINATE; no increase chosen after seeing
direction. A future precision protocol would be a new version.

`binding_gates.csv` exhaustively enumerates **K=23,336** binomial gates:
P:2models×2tasks×10scenarios×[1fit+8strata×12responses×(1coverage+5PIT)] =23,080.
A:8scenarios×[1identification+1FWER+10parties×3raw-CDF] =256.
Family/party/scenario/statistic multiplicity is included in this SINGLE registry.
No implicit extra gate omitted from K; deterministic support/integrity checks have no
Monte Carlo uncertainty and are separate hard requirements.

For s successful events in R trials, lower=BetaQuantile(delta;s,R−s+1),
upper=BetaQuantile(1−delta;s+1,R−s), with0/1 endpoints; delta=.05/(2K).
These are simultaneous two-sided Clopper–Pearson bounds by Bonferroni, regardless of
correlations between gates. With m missing event outcomes, lower uses s and upper uses
s+m out of original R. No denominator reduction. Coverage treats failed fits as uncovered;
PIT/p-value events on failed fits remain missing/adversarially bounded.

Acceptable probability intervals:
* fit/identified: [.99,1]; all5predictive folds must succeed; numerical failure rate<=1%
  must be CERTIFIED, not just observed. A zero scale for any party fails identification.
* predictive95%coverage: [.92,1] per response/stratum/scenario/task/model.
* predictive randomized PIT at u=.01,.05,.10,.50,.90:
  [max(0,u−.05),min(1,u+.05)]. Two-sided gate rejects systematic miscalibration,
  including excessively diffuse predictions; width/proper score also reported.
* A Holm family rejection at alpha=.05: [0,.075].
* A each raw p CDF: at u=.01,.05,.10 upper limits .025,.075,.13 respectively.
  These certify bounded anti-conservatism, NOT uniform p-values; conservative tests are
  allowed and labelled through their power/CDF. Exact nominal .05 is not promised.

**PASS** iff confidence interval is contained in acceptable interval.
**FAIL** iff intervals are disjoint.
**INDETERMINATE** otherwise. Missing replicate IDs/incomplete R are NOT_RUN_INCOMPLETE,
which stops release. One binding FAIL fails that family/task; no failed scenario dropped.
Any unresolved required check stops that family/task. Source/model implementation
failure stops affected runs; no parameter repair. Early termination may occur only
AFTER a whole predeclared R-sized binding scenario fails; unrun checks stay NOT_RUN,
no overall PASS. No optional stopping inside R, no post-hoc tolerance widening.

Binding operational tolerance .075 vs nominal .05, coverage .92 vs nominal .95, PIT
margin .05 are explicit researcher choices frozen now. They do not certify exact
calibration. Conditioning/size misfit is checked through all size/parent strata in every
generator; no visual reviewer override. Finite battery does not prove validity for
every unmeasured heterogeneity. Support hard gate:100% of declared task support retained,
min20regions/40TIK; A additionally min2,000rows/2%base. Base always unchanged.

Numerics: same pinned software/threads/seeds, exact integer replay, float rtol1e−10,
atol1e−12 for representative deterministic replay. Gate counts/classifications must be
EXACT identical. Different software needs engineering reproduction before evaluation,
not automatic tolerance loosening. Implementation corrections discovered before real
outcomes are logged and affected evaluation invalidated/restarted; scientific changes
require new freeze. No real election result has been produced in this package.

## 10. Comparison and allowed post-PASS work

Order: validity → identification for claimed estimand → support → proper predictive
scores → uncertainty quality → robustness. Failed models excluded from substantive
comparison but preserved in calibration tables. Scores stratified by task/scenario and
same probes/support; conditional bias=mean(predicted−observed), predictive RMSE=sqrt
mean squared error (not error against an unknown real latent mean), coverage, width,
PIT, CRPS, joint log score and MC SE. No scalar winner across different estimands.

Disagreement categories: assumptions, support, denominator/version, specification.
Unresolved observational disagreement is specification dependence/NOT_IDENTIFIED for a
shared counterfactual, never an averaged reconstructed total. No local anomaly ranking.

After appropriate calibration PASS and a SEPARATE real-release task: no-source-conflict,
alternate-version, complete-regions,95/99.9coverage sensitivities and leave-one-region-out
are predeclared. Same code/parameters; re-materialize design/pairs/folds. Changed design
needs its own entire applicable calibration registry, including probes/support thresholds;
equivalence of identical designs can be proved by hashes instead of duplicate execution.
No prior/bandwidth/threshold alternatives retained in v1; introducing them needs new
prospective version. No sensitivity rescues FAIL; no extrapolation to missing geography.

## 11. Information boundary, reproduction and governance

Prior2A/2T results are known; this is prospective specification, not retroactively blinded
research. Actual reader requests only uuid,resolved_region,voters and official hierarchy.
No real I,V,C reader, no hidden real fits for testing. Code checks synthetic flag and CLI
has no real mode. Flag is an engineering guard, not cryptographic proof; source reader
and tests are the auditable boundary. Forbidden outputs include new real coefficients,
p-values, residual maps, latent classes/reference cores, mechanism/excess-vote quantities,
rankings and all counterfactual totals. No historical or directory promotion.

Only commands executed during freeze: identity/design audit, synthetic unit tests,
synthetic engineering dry-run and replay, governance consistency checks. None is an
actual-design calibration replicate. Tests do not manufacture a scientific PASS.

Reproduction now: `python3 -m unittest tests.test_stage3a -v`;
`python3 -m src.stage3a.runner dry-run`; `python3 -m src.analysis.research_handoff --check`.
Future calibration (NOT executed, separate authorization):
`python3 -m src.stage3a.runner calibrate --scenario N1 --replicate 0 --task known_tik --family H_count_ridge`;
analogous frozen scenarios0..4999, tasks/families; association with family
A_exact_size_categorical_projection. Positive command specifies frozen strength/sign
and replicate0..999. `aggregate` validates complete IDs and yields gate tables; it never
authorizes real execution. Existing output files cannot be overwritten by these commands.

Model/software versions and full source/input hashes are in freeze metadata. Python,
NumPy,SciPy,pandas versions pinned to the actual dry-run environment. No additional source
collection. User requirement: Path C, scope separation/no real runs. Researcher choices:
family drops, H/L parameters, stochastic coarsening, narrow support, Holm, precision and
gates. Quantitative impact: base0; A support3,592 excludes84,142 for that estimand only;
known-TIK prediction excludes7 for that estimand only. Current source/calibration blockers
and narrow temporal validity remain. No collateral regional exclusion from primary.

SAFE TO PROCEED after engineering checks: calibration execution ONLY under a next task.
Predictive/association calibration NOT RUN; counterfactual NOT_IDENTIFIED. Neither this
freeze nor future statistical PASS permits reconstruction without new identifying evidence
and an explicitly authorized separate stage.
