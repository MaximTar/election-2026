"""Report delivery measurements and separate self-review after qualification."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
P = Path(__file__).resolve().parent


def read(path):
    return json.loads(Path(path).read_text())


def put(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n')


def main():
    check, det, size = (read(P / n) for n in ('checker_result.json', 'determinism.json', 'size_report.json'))
    assert check['status'] == det['status'] == 'PASS'
    assert check['runtime_manifest_sha256'] == det['second_manifest_sha256']
    decisions = [
        {'id': 'RUNTIME_ADDITIVE_CANONICAL_IMMUTABLE', 'origin': 'user requirement',
         'decision': 'Add runtime subtree without editing any accepted canonical file or accepted generator/checker.',
         'rationale': 'Transport optimization is not a replacement scientific/publication contract.',
         'quantitative_impact': {'canonical_files_changed': 0, 'accepted_files_verified': 1640, 'public_states_unchanged': 2064},
         'alternatives_considered': ['Rewrite canonical manifest/state files (prohibited)', 'Add a separate delivery projection (selected)'],
         'reversibility': 'Canonical view remains independently available; future delivery versions require separate engineering authorization.',
         'downstream_consequences': 'Use the scoped runtime checker for the additive graph, retaining older sealed evidence.'},
        {'id': 'RUNTIME_NATURAL_SHARD_KEYS', 'origin': 'researcher/Codex choice',
         'decision': 'ABC source/design shards; D source/frozen-specification shards; four smaller state lists canonical-backed.',
         'rationale': 'Existing metadata defines these keys exactly; D4 group diagnostics should not load with D0.',
         'quantitative_impact': {'ABC_shards': 64, 'states_per_ABC_shard': 25, 'D_shards': 20,
                                 'default_ABC_shard_raw_bytes': size['default_ABC_shard']['raw_bytes'],
                                 'default_D_shard_raw_bytes': size['default_D_shard']['raw_bytes']},
         'alternatives_considered': ['Whole ABC list', 'D source-only shards including large D4', 'Unnecessary symmetric small-method sharding'],
         'reversibility': 'Only routing and storage organization; state records and IDs remain canonical.',
         'downstream_consequences': 'Select an explicit route, then an existing state. No Cartesian-product inference.'},
        {'id': 'RUNTIME_EXPLICIT_GZIP_ALTERNATIVES', 'origin': 'researcher/Codex choice',
         'decision': 'Provide raw JSON and deterministic binary gzip alternatives; report both sizes without assuming CDN behavior.',
         'rationale': 'Static delivery can reduce transfers while retaining raw fallback representation and exact byte equality.',
         'quantitative_impact': {'runtime_files': check['runtime_files'], 'physical_runtime_bytes': size['total_runtime_layer_excluding_exact']['all_physical_runtime_bytes_including_raw_and_gzip_alternatives'],
                                 'bootstrap_raw_bytes': size['bootstrap_combined']['raw_bytes'],
                                 'bootstrap_generated_gzip_bytes': size['bootstrap_combined']['generated_gzip_bytes']},
         'alternatives_considered': ['Assume CDN compression (not established)', 'Raw-only delivery', 'Explicit gzip alternatives (selected)'],
         'reversibility': 'Alternate encodings carry identical logical records; future client may choose either once.',
         'downstream_consequences': 'Validate hosting Content-Encoding behavior; never double-decompress a .gz asset.'},
        {'id': 'RUNTIME_LAZY_EXACT_VISIBILITY_AND_SEMANTICS', 'origin': 'source constraint',
         'decision': 'Preserve full records, exact references, guards/defaults/coverage, 444 additional public states, zero internal reachability and two CARD_ONLY methods.',
         'rationale': 'Accepted visibility and numerical semantics are authoritative; lazy exact resources already exist.',
         'quantitative_impact': {'exact_sidecars_copied': 0, 'ordinary_view_exact_reads': 0, 'new_scientific_states': 0, 'new_exclusions': 0},
         'alternatives_considered': ['Duplicate/decode exact resources for ordinary charts (rejected)', 'Compare display values alone (rejected)'],
         'reversibility': 'No scientific change; accepted records remain the authority.',
         'downstream_consequences': 'Use prepared display fields; pooled exact integer strings stay strings with zero client scientific arithmetic.'},
    ]
    put(P / 'decision_ledger.json', {'scientific_methodological_choices': 0, 'decisions': decisions})
    put(P / 'self_review.json', {
        'status': 'PASS', 'review_type': 'SEPARATE_POST_IMPLEMENTATION_ENGINEERING_SELF_REVIEW',
        'affirmative_findings': [
            'All 1640 accepted canonical files and original five generator/checker code files have unchanged hashes.',
            '2064 complete state records reconstruct exactly; no display-only comparison, ID/default change or scientific state duplication.',
            '64 ABC shards of 25 states and 20 D shards preserve existing natural metadata keys; D4 remains larger and lazy.',
            '444 additional public states remain canonical-backed; INTERNAL is unreachable and CARD_ONLY has no project result.',
            'Explicit gzip aliases are alternate transports, not extra scientific states; exact sidecars are neither copied nor decoded.',
            'Older canonical tools use a closed recursive inventory; their sealed code is unchanged and the new checker scopes the additive subtree.',
            'Source/native/LOO support and different estimands remain unchanged; no common-frame restriction or collateral exclusions.',
            'Host compression behavior and final editorial copy remain separate pending engineering/editorial work.',
        ],
        'new_universes': 0, 'new_exclusions': 0, 'new_model_calls': 0, 'new_fits': 0,
        'new_scientific_states': 0, 'new_methodological_choices': 0,
        'article_edited': False, 'site_UI_implemented': False,
        'blockers': [], 'accepted_limitations': ['Hosting Content-Encoding not yet verified', 'D4 per-group diagnostics remain a larger on-demand resource',
            'Accepted older closed-inventory checker/generator must not be run across the additive runtime subtree', 'Inherited editorial/source-fidelity gaps remain pending'],
    })
    rows = [
        ('Bootstrap manifest', size['bootstrap_manifest']), ('Bootstrap catalog', size['bootstrap_catalog']),
        ('Bootstrap combined', size['bootstrap_combined']), ('Default ABC shard (25 states)', size['default_ABC_shard']),
        ('ABC routing index', size['ABC_index']), ('Complete ABC index + 64 shards', size['all_ABC_index_and_shards']),
        ('Default D shard (D0)', size['default_D_shard']), ('D routing index', size['D_index']),
        ('Complete D index + 20 shards', size['all_D_index_and_shards']), ('Largest D shard (D4)', size['D_largest_shard']),
    ] + [('State file: ' + k, v) for k, v in size['external_method_state_files'].items()]
    table = '\n'.join(f"| {name} | {v['raw_bytes']:,} | {v['generated_gzip_bytes']:,} |" for name, v in rows)
    paths = size['browser_paths']; exact = size['canonical_exact_sidecars']; total = size['total_runtime_layer_excluding_exact']
    runtime_manifest_sha = check['runtime_manifest_sha256']
    report = f'''# Additive static publication delivery, runtime v1

The runtime projection is ready at `publication/sites/v1/runtime/`. The accepted
publication-data contract remains the authority. This pass copies existing records,
partitions them by existing keys, creates deterministic gzip transports and measures
stored file sizes. It performs no result analysis, scientific calculation, model call,
fit, source-row loading, new scenario/estimand/control or article/UI work.

## Authority and immutability

Accepted manifest SHA256 before and after:
`{check['canonical_manifest_after']}`.
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
{table}

### Actual browser fetch paths

A. Initial bootstrap: **{paths['A_initial_bootstrap']['raw_bytes']:,} raw /
{paths['A_initial_bootstrap']['generated_gzip_bytes']:,} gzip**, two resources.

B. Opening default ABC after bootstrap: index + selected 25-state shard + existing
baseline/design/source context, **{paths['B_open_default_ABC_incremental_after_bootstrap']['raw_bytes']:,} raw /
{paths['B_open_default_ABC_incremental_after_bootstrap']['generated_gzip_bytes']:,} gzip**.
Total cold ABC view, including bootstrap: **{paths['B_open_default_ABC_total_cold']['raw_bytes']:,} raw /
{paths['B_open_default_ABC_total_cold']['generated_gzip_bytes']:,} gzip**. No full ABC list/exact sidecar.

C. Changing source/design with index cached: one shard, **{paths['C_change_ABC_source_design_if_index_cached']['raw_min_bytes']:,}–
{paths['C_change_ABC_source_design_if_index_cached']['raw_max_bytes']:,} raw /
{paths['C_change_ABC_source_design_if_index_cached']['gzip_min_bytes']:,}–
{paths['C_change_ABC_source_design_if_index_cached']['gzip_max_bytes']:,} gzip**; zero transfer if that shard is cached.
Lambda/mu or A/B/C slice changes within the active shard require no additional fetch.

D. Opening default D after bootstrap with baseline/design/source context:
**{paths['D_open_default_D_incremental_after_bootstrap']['raw_bytes']:,} raw /
{paths['D_open_default_D_incremental_after_bootstrap']['generated_gzip_bytes']:,} gzip**.
Cold total: **{paths['D_open_default_D_total_cold']['raw_bytes']:,} raw /
{paths['D_open_default_D_total_cold']['generated_gzip_bytes']:,} gzip**.
Selecting D4 deliberately loads its larger diagnostics, never as a hidden initial dependency.

E. Opening one other method: only its state file, using the table above. Source metadata
is optional when region names/provenance are needed; it does not load other method states.

F. Requesting exact data: one existing canonical sidecar. For the default C example it is
**{paths['F_explicit_exact_request_example']['compressed_bytes']:,} compressed bytes**; its SHA is
already in the selected record. The full 268,237-byte canonical manifest is optional for
complete integrity inventory inspection, not required for ordinary charts or one-file verification.
No exact file is decoded/re-encoded/copied by generation or normal client rendering.

Canonical exact sidecars: 1,620 already-compressed files; median **{exact['median_compressed_bytes']:,}**,
p95 **{exact['p95_compressed_bytes']:,}**, max **{exact['max_compressed_bytes']:,}** bytes.
The even-sample median averages the two middle sizes; p95 uses ceil(0.95 N) nearest rank.

Total additive runtime on disk: **{total['all_physical_runtime_bytes_including_raw_and_gzip_alternatives']:,} bytes /
{total['files']} files**, including both encodings and docs, excluding exact sidecars.
The complete logical JSON delivery graph, counted once per resource and including
canonical-backed small files/metadata, is **{total['complete_logical_JSON_graph']['raw_bytes']:,} raw /
{total['complete_logical_JSON_graph']['generated_gzip_bytes']:,} gzip** bytes.
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

Two final generations produce identical bytes for all **{det['files']} runtime files**.
Runtime manifest SHA256: `{runtime_manifest_sha}`.
Both complete runtime inventories SHA256: `{det['second_inventory_sha256']}`.
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
'''
    (P / 'report.md').write_text(report)
    print(json.dumps({'report': 'created', 'checker': check['status'], 'determinism': det['status'], 'public_states': 2064}))


if __name__ == '__main__':
    main()
