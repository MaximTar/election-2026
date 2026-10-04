# Additive static publication delivery, runtime v1

The runtime projection is ready at `publication/sites/v1/runtime/`. The accepted
publication-data contract remains the authority. This pass copies existing records,
partitions them by existing keys, creates deterministic gzip transports and measures
stored file sizes. It performs no result analysis, scientific calculation, model call,
fit, source-row loading, new scenario/estimand/control or article/UI work.

## Authority and immutability

Accepted manifest SHA256 before and after:
`38d8f0eaa79952b4036d7e23c04ff40cca65f51e40f5cbbcddc88efd92fc3d16`.
All **1,640 canonical files** are byte-identical, as recorded in `canonical_before.json`
and checked against the accepted manifest. The accepted five generator/checker code
files remain unchanged. Acceptance/report evidence remains in
`outputs/sites_publication_data/20261004_v1/`; its terminal manifest
`008f9ce56b985af4d80492a14721f410938cc4a685f5ae200de9811aae075c21`
and sealed evidence were verified before implementation. No article draft supplied values.

## Architecture and accounting

Bootstrap: runtime manifest + full unchanged method entries inside a delivery wrapper.
No 1,620-sidecar inventory is copied into the bootstrap. Method metadata points to explicit
routing indexes. ABC has **64 source/design shards**, each with **25 complete states**.
D has **20 source/frozen-specification shards**, one state each: this prevents D4's large
group diagnostics being downloaded when opening D0. The four smaller executable methods
retain their unchanged canonical raw files, with runtime gzip transport alternatives.

Logical graph: **1,600 ABC + 20 D + 161 Cedar + 102 iStories + 90 1D + 91 2D = 2,064**
PUBLIC states. INTERNAL reachability: **0**. CARD_ONLY: **2**, project states/results: **0**.
Each scientific state appears once in the logical graph; raw/gzip copies are alternative
encodings, not added calculations. A/B aliases remain slices of ABC. Default pointers are
unchanged. A missing route/state is unavailable, never synthesized, interpolated or silently
reset. Complete records reconstruct identically, including exact references, coverage,
support, source/geography controls, diagnostics and D undefined markers.

All runtime URLs resolve against the runtime manifest. Paths inside unchanged canonical
records/catalog entries resolve against the canonical publication root. Opaque scientific
provenance paths are not additional client execution/data endpoints.

## Measured resource sizes

Sizes are bytes. Gzip columns are actual generated level-6, mtime-0 binary transports;
they are not an assumption about CDN compression. Choose raw OR gzip for each resource.

| Resource | Raw bytes | Generated gzip bytes |
|---|---:|---:|
| Bootstrap manifest | 33,681 | 11,030 |
| Bootstrap catalog | 51,626 | 7,357 |
| Bootstrap combined | 85,307 | 18,387 |
| Default ABC shard (25 states) | 110,036 | 14,923 |
| ABC routing index | 69,769 | 8,597 |
| Complete ABC index + 64 shards | 7,089,784 | 964,657 |
| Default D shard (D0) | 22,941 | 4,013 |
| D routing index | 5,269 | 1,417 |
| Complete D index + 20 shards | 2,697,729 | 410,478 |
| Largest D shard (D4) | 582,107 | 86,223 |
| State file: cedar | 386,208 | 27,670 |
| State file: novaya_1d | 220,674 | 17,750 |
| State file: novaya_2d | 447,533 | 45,599 |
| State file: vazhnye_istorii | 235,800 | 22,554 |

### Actual browser fetch paths

A. Initial bootstrap: **85,307 raw /
18,387 gzip**, two resources.

B. Opening default ABC after bootstrap: index + selected 25-state shard + existing
baseline/design/source context, **215,577 raw /
30,559 gzip**.
Total cold ABC view, including bootstrap: **300,884 raw /
48,946 gzip**. No full ABC list/exact sidecar.

C. Changing source/design with index cached: one shard, **109,216–
110,393 raw /
14,797–
15,097 gzip**; zero transfer if that shard is cached.
Lambda/mu or A/B/C slice changes within the active shard require no additional fetch.

D. Opening default D after bootstrap with baseline/design/source context:
**63,982 raw /
12,469 gzip**.
Cold total: **149,289 raw /
30,856 gzip**.
Selecting D4 deliberately loads its larger diagnostics, never as a hidden initial dependency.

E. Opening one other method: only its state file, using the table above. Source metadata
is optional when region names/provenance are needed; it does not load other method states.

F. Requesting exact data: one existing canonical sidecar. For the default C example it is
**206,728 compressed bytes**; its SHA is
already in the selected record. The full 268,237-byte canonical manifest is optional for
complete integrity inventory inspection, not required for ordinary charts or one-file verification.
No exact file is decoded/re-encoded/copied by generation or normal client rendering.

Canonical exact sidecars: 1,620 already-compressed files; median **179,225.5**,
p95 **296,765**, max **323,767** bytes.
The even-sample median averages the two middle sizes; p95 uses ceil(0.95 N) nearest rank.

Total additive runtime on disk: **11,395,608 bytes /
187 files**, including both encodings and docs, excluding exact sidecars.
The complete logical JSON delivery graph, counted once per resource and including
canonical-backed small files/metadata, is **11,200,310 raw /
1,514,912 gzip** bytes.
This full graph is reachable but never an initial fetch requirement. Performance targets PASS.

## Numerical and semantic preservation

Use prepared display/chart values. Exact pooled numerator/denominator strings remain
strings; no parseInt/Number/float conversion or BigInt arithmetic is required. Exact
resources support explicit inspection/reproducibility, not browser-side scientific
recalculation. The source comparison can use the already prepared source vectors in the
selected record; no reconstruction from exact baseline rational values is required.

Method/state guards are unchanged: ten-party local conditional scenarios; focal-party D;
scenario focal-valid share; Cedar signed excess/observed focal (not party share); 1D fitted
component center (not national counterfactual share); 2D center and model membership
(not honesty/fraud probability). Undefined is not zero. Specification windows/anchors are
not confidence intervals. LOO is influence, not region diagnosis. Sources are not correctness
rankings, native universes differ and unlike estimands cannot be averaged onto a truth scale.
Support/coverage remains complete in the runtime records, not discarded to reduce size.

## Qualification, determinism and tooling

Runtime checker: **PASS**. Full normalized record equality, accepted byte hashes, all
2,064 state IDs, default resolution, exact references, explicit routing, semantic guards,
visibility and two state-less cards were verified. Eight negative corruption regressions
exercise missing/internal states, Cedar wrong semantics, D undefined-to-zero, changed/escaped
references, unknown default and damaged gzip payload. All PASS. No old scientific battery
was rerun; scientific extraction/estimator dependencies are not imported.

Two final generations produce identical bytes for all **187 runtime files**.
Runtime manifest SHA256: `3998d58ec33c4bb8d28b6a35abdb5d2d2d28772a7aaea20b7fbd61afd598131c`.
Both complete runtime inventories SHA256: `6fcb1bec0332ff83cc6153fc5bcda9cb17ed30a19a7830cfbd4a08193e5579ef`.
No timestamp enters generated runtime bytes. Environment is recorded in its manifest;
publication commands use existing /usr/bin/python3 and existing jsonschema, without installs.

Commands:
`/usr/bin/python3 -m src.publication_sites.runtime_generate`
`/usr/bin/python3 -m src.publication_sites.runtime_check`
`/usr/bin/python3 -m src.publication_sites.runtime_measure`

The accepted original generator/checker predates this additive subtree and uses a closed
recursive inventory. Its byte-bound code is preserved; do not run its generation over the
runtime tree. This is an explicit tooling limitation, not a mutation of the accepted layer.
Use the new checker, which verifies every accepted hash and only permits the separately
inventoried runtime files. The current handoff dispatcher adds this engineering stage only;
prior dispatcher/pointer bytes are archived and the stage registry extends 53 to 54 unchanged-prefix.

## Separate self-review and limits

`self_review.json` records affirmative findings and accepted limitations. Native support,
electoral counts, region/TIK membership, source choices, controls and result meanings did
not change. No new exclusion/collateral gate, preferred source, parameter or result was
selected. Primary remains 87,736 UIKs / 84 regions / 2,818 official TIKs; 99,360,758 voters,
55,674,920 issued and 54,723,201 valid. DEG remains outside core and overseas separate.

Host Content-Encoding still needs a later deployment/client verification: gzip alternatives
must be served as bytes and decoded once, or raw JSON may be selected. Large D4 diagnostics
remain an explicit on-demand resource. Final reader copy and known external public-source
fidelity limitations remain inherited/pending. No local publication-data blocker.

### Handoff

Stage completed: additive publication delivery/runtime optimization.
Primary universe: paper_primary__evidence_20260927, unchanged.
Input/output state records: 2,064 PUBLIC, identical; no scientific source rows through kernels.
Rows excluded: 0 new; INTERNAL remains excluded; CARD_ONLY has no project result.
Regions included/excluded: existing 84 primary / frozen native and LOO scopes; 0 new exclusions.
New methodological choices: 0; delivery-only choices in decision_ledger.json.
Important unresolved issues: no blocker; hosting compression and editorial/release metadata pending.
Reviewer attention: URL bases, lazy exact strings, explicit availability, D4 size and typed semantics.
Safe to proceed: YES WITH LIMITATIONS — separately authorized Sites client preparation/implementation
against runtime contract. Roadmap-99 is unchanged; no UI/article implementation starts here.
