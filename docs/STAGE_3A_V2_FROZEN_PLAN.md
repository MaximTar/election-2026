# Stage 3A v2 — executable prospective L + A protocol

Version: 20260927. This plan is frozen by the manifest under
`outputs/stage3a_v2/freeze/` before the actual-design timing preflight. Full calibration
requires a separate user authorization. No real-response model loader is provided.
The Python sources in `src/stage3a_v2/`, their immutable v1 dependencies, tests,
software versions, source manifests, design and gate registry form the executable specification.

## 1. Final-universe evidence gate and information boundary

Analysis universe: `paper_primary__evidence_20260927`, defined in the separate dated
universe freeze. It preserves all accepted canonical rows of `paper_primary` and adds
previously absent eligible paper protocols from the supplied 20260927 main-source files.
Existing UUID counts retain accepted source priority; new versions are recorded separately.
This is a versioned extension, never an overwrite of old `paper_primary` or its supports.
Final-design counts/hashes are in `support.json` and `universe_20260927/reconciliation.json`.

Fresh final data add two Bashkortostan UIKs. Both pass the unchanged row-integrity and
regional policy. Bashkortostan registry coverage becomes 3250/3250. Leningrad final
coverage remains 1/1020, below 99%; it remains excluded. The CEC report453 refresh is
temporal, not final federal-party counts. It cannot fill the missing 1019 final protocols.
No inference is made about why public final protocols are unavailable.

Existing rows retain their accepted main canonical versions even where the fresh main
file differs (including two count revisions). This follows `universe_policy_v2.json`:
version evidence is not silently substituted according to outcome convenience.
New-source version differences and opaque row hashes are retained for future measurement
sensitivity. The original 88 alternative-source conflicts remain separate.

Only UUID, official TIK UUID, region and positive integer voters enter synthetic design.
Source counts were accessed only for inclusion and arithmetic reconciliation. No real
turnout/party fit, coefficient, p-value, residual map, ranking or performance criterion is
opened. No history, incidents, observers, directory candidates, geography/type proxies,
temporal labels, numeric UIK number or presumed clean core enters either task.

Incident archive integrity/inventory is audited and quarantined. Its contents do not choose
membership, parameters, seeds, scenarios or models. Region-level historical work is separate;
strict cross-cycle UIK identity remains NOT_IDENTIFIED. Full real execution needs a later task.

## 2. Independent estimands and support

P: evaluate the fixed L sequential count prediction law for issued I given voters n,
valid V given observed I, and party counts C given observed I,V. Conditional-factor
intervals are evaluated for 12 responses; this is not certification of the full joint law.
Known-TIK only. Eligibility: original official TIK N>=2. No outcome selection.

Sort immutable UUIDs by SHA256-derived fold key within each TIK, assign rank modulo5.
For every synthetic dataset independently draw one fold uniformly from five. Fit using
the complement. Define voters quartiles by rank(voters,UUID) on the complete frozen design;
cross four quartiles with original TIK size <10 / >=10. All eight cells must contain
eligible held-out rows in every fold; otherwise STOP before freeze, no post-outcome removal.
Draw one row uniformly within each selected fold/cell. A row in cell c/fold f has
probability 1/(5*N_cf). Save these probabilities. The estimand is fold-balanced and
cell-conditional, not nationally voter-weighted. TIK groups are not iid inferential rows;
independent synthetic datasets are the binomial calibration trials.

A: adjacent UUID pairs within exact official TIK and identical integer voters. Odd rows
remain unmatched; no caliper or region fallback. Minimum design support:2000 rows,
40 TIKs,20 regions,2% of frozen rows. Minimum pairs per TIK=1. Membership is materialized.
The projection-averaged effect for party j is sum(DeltaT*DeltaY_j)/(2M), M pairs;
T=I/n,Y_j=C_j/V. One categorical draw per row generates Z with E[Z|C,V]=Y.
Realized effect is sum(DeltaT*DeltaZ_j)/(2M), not Pearson correlation.

Unsupported rows are not data-quality failures and remain in the main universe. No
automatic generalization to unpaired rows. No empirical support rule is changed after freeze.

## 3. Fixed L algorithm

No nonlinear optimization. Same-TIK training donor pool if size>=8, otherwise same-region
pool if size>=8, otherwise all training rows; if still <8, unavailable. Order by absolute
log(voters_donor/voters_target), then UUID; select at most32 donors. h=max(log(1.10),largest
selected distance). Weights proportional to exp(-0.5*(distance/h)^2), normalized.

For donor k: I~beta-binomial(n,I_k+.5,n_k-I_k+.5);
V|I~beta-binomial(I,V_k+.5,I_k-V_k+.5);
C|V~Dirichlet-multinomial(V,C_k+.5). Same donor indexes the sequential joint mixture.
Conditional donor weights for V and C are updated using held-out I and I,V respectively;
this is ordinary conditioning, not leakage of a response into its own training.
Party marginals use beta-binomial(alpha_j,sum_other_alpha). Small and zero party counts
are legal; pseudocount .5 is fixed. No clipping of observed responses.

For each response generate1999 predictive draws. Interval endpoints: empirical .025/.975
quantiles, NumPy `inverted_cdf`. These finite-draw intervals themselves are calibrated.
Randomized PIT uses exact mixture CDF at observed-1 plus independent U times observed mass.
Record joint/conditional negative log scores, means, errors, squared errors, coverage,
width, PIT and CRPS using two independent1999-draw samples. Scores do not choose a winner.
Cache only immutable fold memberships, training frames and outcome-independent neighbours.
All response-dependent quantities are recomputed per dataset. No H optimizer is imported.

## 4. Fixed A randomization

For each TIK sum pair products into a ten-coordinate score S_t. Standardize each total
by sqrt(sum_t S_tj^2). Any zero scale makes this joint task unidentified, not a zero effect.
B=1999 independent random sign orientations across TIKs; all pairs and all ten parties
within a TIK share one orientation. Include observed orientation with add-one formula:
p_j=(1+#abs(reference_j)>=abs(observed_j))/(B+1), ties included.
Primary: two-sided Holm across ten parties. maxT is diagnostic only.
One predetermined projection stream; no alternate-seed selection.

H0 is orientation exchangeability of projected party vectors relative to turnout under
the specified exact-size/local design. Exact reported size does not ensure equivalent
latent electorate or precinct type. Strong Holm control needs valid marginal null tests;
the partial-null battery below checks specified alternatives, not every conceivable one.

## 5. Synthetic equations and constants

All design quantities are frozen; no real response informs parameters. For row i let
z_i=clip(log(n_i/1000),-5,5), phi_j=2*pi*j/10. All named RNG streams below are independent
unless sharing is explicitly specified. Region and TIK vectors are indexed by sorted IDs.
aT=.25*Normal_region+.35*Normal_TIK;
aY_j=.25*Normal_region,j+.35*Normal_TIK,j, independent of aT.
Base fT=.45*sin(z)+.2*tanh(z);
base fY_j=.35*sin(z+phi_j)+.15*cos(2z)*cos(phi_j).
Base eT~N(0,1), eY_j~N(0,1), sT=.2,sY=.25, effective n*=n.
etaT=.2+aT+fT+sT*eT; etaY_j=aY_j+fY_j+sY*eY_j.
pT=logistic(etaT),pY=softmax(etaY),q=.98-.03*logistic(z).

| Scenario | Exact modification to the base equations | P | A |
|---|---|---|---|
| N1 | Base unchanged | binding | complete/partial binding |
| N2 | fT=2*tanh(80*sin(z)); fY_j=1.5*tanh(80*sin(z))*cos(phi_j) | binding | complete/partial binding |
| N3 | Add .45*independentNormal_TIK*sin(3z)+.2*independentNormal_TIK*z separately to fT and each fY_j | binding | complete/partial binding |
| N4 | sT=.1+.5*logistic(z);sY=.1+.7*logistic(-z) | binding | complete/partial binding |
| N5 | eT,eY independently Exp(1)-1; after softmax draw independent Gamma(12*pY_j) and normalize | binding | complete/partial binding |
| N6 | Add1.3*(2*Bernoulli(.5)-1) to fT; independent row type adds1.6*(2*Bernoulli(.5)-1)*cos(phi_j) to fY | binding | complete/partial binding |
| N7 | Independent T/Y family cluster shocks: add .6*Normal_region+.5*Normal_TIK, coordinate-specific for Y | binding | complete/partial binding |
| N8 | fT=.8*sin(2z)+.3*z;fY_j=.7*cos(3z+phi_j)-.25*z*sin(phi_j) | binding | complete/partial binding |
| N9 | m~Bernoulli(.1); n*=max(1,floor(.8*n)) when m=1; add .8*m*cos(phi_j) to fY | binding recorded counts | specificity only |
| N10 | shared type h~Bernoulli(logistic(.5z));add1.2*(h-.5) to fT and1.4*(h-.5)*cos(phi_j) to fY | binding | specificity only |

Draw I~Binomial(n*,pT),V~Binomial(I,q). Rejection-resample I,V for rows with V=0, keeping
the latent parameters fixed, up to100000 attempts; failure is explicit. This is a
positive-valid conditional synthetic population, not zero imputation. Draw C~Multinomial(V,pY)
by sequential binomials. Assert integer,0<V<=I<=n,C>=0,sum(C)=V. Tiny probability arithmetic
is clipped to [0,1] only inside sequential multinomial implementation, never observed counts.

Partial-null experiments for each N1-N8: j drawn iid uniformly from0..9 by the independent `partial_target` stream; k=(j+1)%10.
After all scenario-specific probability construction preserve mass m=pY_j+pY_k;
w=logistic(log(pY_j/pY_k)+1.0*eT);set pY_j=m*w,pY_k=m*(1-w).
All eight other probabilities remain exactly unchanged. Both pair coordinates are non-null;
FWER counts any Holm rejection among the other eight. Complete-null uses all ten.
This is a randomized cyclic target, balanced in expectation rather than forced equal
counts. The iid target mixture is necessary for exact binomial calibration trials; cycling
deterministically over parties with different rejection probabilities would instead yield
nonidentically distributed events. This detail is fixed before timing/calibration; no party
is selected from real results. Positive-control rotation remains balanced/descriptive.

Positive controls use N1: before softmax add sign*strength*eT*contrast_j, contrast=1 for
target and -1/9 otherwise. Strength=.10,.30,.60, both signs,200datasets each; target=replicate%10.
These are logit loadings, not predetermined correlations. Power is descriptive and cannot
rescue invalidity. N9/N10 A specificity:200each; genuine association is not Type-I error.

Observational-equivalence witness uses one synthetic N10 dataset: ordinary observed counts
versus latent party relabelling or latent added-count construction, same observables and
different hypothetical baselines. Only identity/difference checks and NOT_IDENTIFIED are
reported; no real counterfactual calculation. Model agreement cannot identify a mechanism.

## 6. RNG policy and task inventory

PCG64; seed = first16bytes(big endian) of SHA256(UTF8 compact JSON array of
["stage3a-v2-independent-20260927-final-design",*semantic_keys]). Full keys in code.
Generator keys include stream,scenario,replicate,strength,sign,target,experiment plus a
distinct named innovation stream. Projection,orientations,fold,probe and prediction draws
have separate keys. Timing/unit/evaluation namespaces never overlap. Chunk order does not
affect any scientific result. No imported aborted-v1/preflight result enters calibration.

Prediction:10*2500=25000tasks. Association nulls:8*2*2500=40000tasks.
Positives:3*2*200=1200tasks. Specificity:2*200=400tasks. Equivalence:1task.
Total66601 logical tasks, unique deterministic IDs. All must complete before final release.

## 7. Exact task-clearance rules

P has970requirements:10success floors .99 plus10*8*12coverage floors .92 for nominal.95
conditional-factor intervals. A has32requirements:8*2success floors .99 and8*2FWER ceilings
.075 at nominal test alpha .05. Total1002. Every requirement hasR=2500 independent datasets.
No sequential extension. Reference B=1999; neither R nor B adapts to outcomes or runtime.

Each task receives Monte Carlo false-clearance budget delta=.025. For k events out of R,
lower=BetaQuantile(.025;k,R-k+1),upper=BetaQuantile(.975;k+1,R-k), with exact0/1 boundaries.
Missing event counts widen bounds over all possible missing outcomes. Failed predictions
count uncovered and unsuccessful; undefined A contributes unsuccessful and unknown FWER.
Never shrink the denominator. PASS requires the relevant bound inside the allowed range;
FAIL means the opposite bound excludes it; otherwise INDETERMINATE. Both non-PASS statuses
block that task. INCOMPLETE execution is not scientific FAIL. One binding failure blocks
the whole task; no promotion of passing parties/scenarios/sensitivity variants.

AtR2500:success PASS>=2485,coverage PASS>=2327,FWER PASS<=161 absent missing events.
All requirements must PASS to release a task. If one requirement is false, probability
all pass <= probability that false requirement passes <=.025. Union bound over two tasks
gives<=.05 false clearance. This is NOT simultaneous confidence coverage of every table row,
nor a guarantee outside the fixed DGP class. No candidate selection across multiple predictors.
Calibration's .075 ceiling must never be described as proof that empirical FWER<=.05.

## 8. Diagnostics, numerical checks and outputs

Keep all replicate-level events and raw predictive scores/PIT/width/CRPS/means/observed
synthetic counts. Record support, fallback level, selected fold/row probabilities, failures,
raw/Holm/maxT p-values, effect/score, identification rates and power by sign/target.
PIT/CDF grids and proper scores are mandatory diagnostics, not release gates. No per-UIK
anomaly p-values, joint-density guarantee or anomaly rankings follow from interval coverage.
Wide intervals can be uninformative and must be shown. No overall model winner score.

Toy tests cover integer/simplex invariants, null stream separation, partial-null invariance,
all-party positive controls, exact disjoint pairs, folds, joint signs, Holm, old/new L
equivalence, cache equivalence, exact CP thresholds, missing-event handling, task inventory,
atomic idempotency/crash residue and observational equivalence. Actual timing replay compares
all34logical scientific task outputs serial versus two parallel runs. Numerical tolerance
rtol1e-10/atol1e-12; replay here requires exact serialized scientific equality. No plots need
byte identity. Nonfinite scores/PIT outside numerical tolerance => explicit failure.

Worker results are independent; only one coordinator writes atomic scientific artifacts.
Duplicate identical task commits are idempotent, conflicting duplicates STOP. Deterministic
resume validates task/freeze metadata. A coordinator lock prevents multiple writers.
No real-data execution command exists. Raw result artifacts are the authoritative ledger;
completion logs and gate tables reconcile from them. Preserve engineering failures separately.

## 9. Bounded preflight and launch gate

Exactly34tasks:10L(N1-N10,rep0),16A(N1-N8 complete/partial,rep0),6positive(strength/sign,rep0),
2specificity(N9/N10,rep0). Stream is `timing-preflight-never-calibration`.
Serial once, then twice in fresh8-worker spawn pools, BLAS/OMP/MKL threads1. Total102
executions,68serial-parallel equality comparisons. Budget1800wallseconds. No calibration
PASS/FAIL is inferred from these tasks. New scientific choices cannot follow their outputs.

Record design/startup,generation,procedure,CPU/wall and process/commit overhead. Per scenario/
type use maximum observed steady task wall (generation+procedure), weighted by full task
inventory, divided by8; add measured startup/IPC allowance. Conservative projection is1.5
times that cost plus900seconds for final audit. Report raw and conservative estimates.
Target<=8h; allowable<=10h. If conservative estimate>10h, SAFE_TO_LAUNCH=NO; no full run.
At most two bounded exact-equivalent optimization proposals may be returned, not executed.
No automatic R/scenario/gate changes, rented compute or H project.

## 10. Release and interpretation

Separate authorization after preflight is mandatory even if runtime passes. Full synthetic
completion, exact gates, required diagnostics, consistency and replay precede any separately
authorized real output. P does not release A; A does not validate P. Neither licenses
mechanism, fraud, causal effect, honest precincts or quantitative counterfactual reconstruction.
Shared ordinary type and measurement uncertainty can explain genuine association.

After task PASS, source-conflict/alternative-version/complete-region sensitivities require
named current-version universes, rebuilt support, and a prospective transport justification
or separately budgeted calibration before inferential claims. Old complete-region membership
must NOT silently substitute for the new frame: Bashkortostan now has100% registry coverage.
No full Cartesian product and no rescue of failed primary by sensitivity.

## 11. Preserve H's history

H was seriously attempted in v1. Initial fits exposed numerical and computational issues.
HC1 showed1000iterations were not uniformly adequate; HF2 full-design whitening passed its
tested synthetic numerical criteria without changing the objective/penalties. H was not
scientifically rejected. It is prospectively absent from the binding v2 set because its
distinctive partial-pooling/structured-extrapolation capability is unnecessary for the
primary claims and disproportionately expensive relative to L's overlapping predictive role.
V1 remains ABORTED_COMPUTATIONAL_INFEASIBILITY, not a scientific calibration failure.
