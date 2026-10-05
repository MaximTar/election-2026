# Presentation chart data — 20261005_v1

Status: LOCAL_VALIDATION_PASS; public deployment/HTTP verification pending.

## Extracted frozen values
Six chart files derive from existing PUBLIC default states and public window/anchor states. Coefficients, 1D Gaussian parameters and 2D means/covariances/weights were extracted from immutable hash-bound packets. Exact rational/binary64 representations are preserved separately from rendering numbers.

## Presentation-only derivations
Primary coordinates: issued ballots / registered voters and focal valid votes / valid votes. Sparse 200×200 grid (0.5 pp), equal UIK counts and separate registered/valid sums. Exact endpoint bin policy is documented; no row identifiers are published. Primary totals remain 87,736 UIKs, 84 regions, 2,818 official TIKs, 99,360,758 voters, 54,723,201 valid votes.
iStories: 100 1-pp observed L/O/support bins; all 15 stored ROS coefficients/window results, expected/residual curves and reference support. No coefficient estimation.
Cedar: native cast/registered coordinate, 100 right-closed bins; frozen alpha and stored (43%,44%] anchor; 71 fixed anchors plus AUTO/±5 stored results/support. Native 71,438 UIKs; 16,298 inherited exclusions (2,758 registered≤100; 13,540 unknown invalid), no new exclusions. Expected and residual curves reproduce stored E and E/L exactly.
1D: focal-vote histogram mass, 1-pp bins, common max normalization. Three stored (mean,sigma,amplitude) components evaluated at midpoints and a deterministic 0.2-pp plot grid; their sum is the fitted total. Stored SSE matched within prospectively declared presentation verification tolerance 1e-10; component sums within 1e-12. No fitting/optimization.
2D: same primary grid, raw coordinate parameters and complete stored mixture means/covariances/weights. Existing core slot and membership aggregate copied without inference. A/B/C and D retain existing runtime data; no new heavy dataset.

## Unavailable fields
Per-UIK 2D posteriors/member indices were stripped by committed compaction. Therefore per-cell membership counts/weights are unavailable; no predict_proba call or responsibility reconstruction was performed. Missing membership is not zero. 1D pre-evaluated fitted-total curves were not persisted: evaluation from stored parameters is validated against the independently stored SSE.

## Integrity and deterministic validation
Canonical SHA: 38d8f0eaa79952b4036d7e23c04ff40cca65f51e40f5cbbcddc88efd92fc3d16
Runtime SHA: 3998d58ec33c4bb8d28b6a35abdb5d2d2d28772a7aaea20b7fbd61afd598131c
Protected before/after inventory includes 2,373 files across publication/runtime, both committed runs, reveal, successor freeze and article checkpoints. No accepted scientific/publication bytes are changed. Deterministic regeneration and fail-closed schema/numeric/public-scope checks are recorded separately. Generator imports only stdlib and installs a call guard rejecting scientific/adapter modules. Scientific states added=0, model calls=0, fits=0, optimizer calls=0; real source rows through kernels=0.

## Delivery
Total raw bytes: 924959
Presentation manifest SHA: beb00a95ad1f1d9edc5e05fff17b033a7f23649ecee9b470520b8838f5f7e771
Workflow copies unchanged publication/sites/v1 to temporary staging and adds presentation/20261005_v1 there; accepted API roots do not move. No generation in CI. publication-v1 tag remains pinned to 197ac6a27739a9a2b33df4c5c817ece3edde5073. Local provenance inputs intentionally remain outside the partial public reproducibility repository.

## Decisions / reviewer attention
User requirement: additive deterministic chart data only; no scientific changes or UI/article work. Researcher/Codex engineering choices: sparse columnar density, shared coordinate policy, 501 plotting points, stdlib schema-subset checker that rejects unsupported validation keywords. Source constraint: absent per-UIK posterior history prevents membership heatmap. No new methodological choice, universe or preferred parameter.
All charts inherit method-specific estimands, native coverage and non-CI/non-honesty guards. Context geometry is descriptive, not historical KSP replication or fraud classification. No unlike outputs are averaged.

## Handoff
Stage completed: additive static chart presentation data; public delivery pending.
Primary universe: unchanged paper_primary__evidence_20260927.
Input rows: 87,736 selected frozen primary rows (presentation aggregation only); inherited PUBLIC states/parameters.
Output/analysed rows: aggregated sparse cells and 100-bin/curve tables; no raw UIK publication.
Rows excluded: 0 new; Cedar retains inherited 16,298 native-scope exclusions.
Regions included/excluded: 84 primary; no new exclusions.
New methodological choices: 0.
Important unresolved issues: no scientific blocker; per-cell membership unavailable, public full reproducibility/licensing pending.
Reviewer attention: bin endpoint policy, distinct cast/issued coordinates, exact frozen coefficients, common normalization, absent membership is not zero.
Safe to proceed: only after deployment/HTTP/CORS PASS, give the presentation manifest to Sites for a separately authorized second UI pass.
