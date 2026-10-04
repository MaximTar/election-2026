# Static data contract, version 1

This is the publication view of one election-2026 research project. It contains only
stored, disclosed results. No fitting, runtime calculations or back-end API is needed.
Regenerate with `/usr/bin/python3 -m src.publication_sites generate`; validate with
`/usr/bin/python3 -m src.publication_sites check` from the repository root.

## Client workflow

1. Load `manifest.json`; verify hashes if the client supports integrity checking.
2. Load `methods.json` and `sources.json`. Optional `baselines.json` supplies the
   original ten-party vector for each frozen source; `designs.json` explains controls.
3. An executable method names one state file. A card-only method has no executable
   file, no available states and no project numeric output.
4. Read the selected state file. Its `states` array is the complete availability list.
   Offer a control change only if an actual row exists matching ALL selected controls,
   source and geography. Marginal `available_controls` are NOT a Cartesian product.
   Only keys in the method's `available_controls` may be public selectors. Other fields
   in a state's `controls` are fixed/coupled specification facts, never independent
   optimizer knobs. In particular sigma_min is determined by bin width, and K is fixed.
5. Changing source/geography can make a method control unavailable. Disable it with
   `UNAVAILABLE_NOT_IN_FROZEN_GRID`. Require an explicit reader-visible reset before
   choosing another listed state; never silently coerce to a default.
6. Render that row's already-stored results, result type, native coverage and support.
   `provenance` is technical audit information, never a reader-facing method name.

Stable IDs here are publication aliases with a one-to-one technical provenance mapping.
Aliases A and B are slices of the joint local scenario grid, not duplicate states.
An initial view may use `baselines.json` without inventing a scenario ID. Scopes `full`
and `native` are two stored outputs of one calculation, not separate states.

## Exact values and display values

All integer denominators/numerators are strings when represented as rationals.
Additional result objects preserve stored `{exact: "numerator/denominator"}` or
`{float_hex, decimal17}` exactly. Counts remain stored integers. For large ten-party
vectors, `result.exact_file` is a lazy static gzip-compressed JSON resource. Fetch as
bytes and decompress with `DecompressionStream('gzip')` (or equivalent client library),
then parse JSON. Each rational uses `numerator_ref` / `denominator_ref`, zero-based
indices into that resource's `integer_strings` array. Resolve those two indices to
obtain the exact numerator/denominator strings; never calculate them from rounded data.
This storage-only pool avoids repeating enormous identical integer strings. Hosting
must serve the resource as bytes, not apply another gzip
content encoding. Its manifest/hash covers the compressed bytes. No scientific pipeline
knowledge is required. Never convert large integer strings through JavaScript Number.

The main ten-party `display_vectors` are the unchanged six-decimal stored presentation
arrays. `shares` are fractions, `percentage_points` are already in pp. They are not exact
records; their exact counterparts are in the sidecar. Pipeline decomposition details
are intentionally not duplicated; technical provenance retains their frozen source.
External display percentages use
four decimal places, half-even, derived from exact stored rational/binary64 values.
Display transformations never overwrite exact values. Full/native focal accounting in
`aggregate_exact` inside that sidecar is copied from the disclosed exact inventory.

## Meaning, undefined states and coverage

Do not put different `result_type` values on a common truth scale or average methods.
The local ten-party scenarios and focal-party scenario D are conditional scenarios.
The iStories construction reports a scenario focal-valid share. Cedar reports signed
E / observed focal votes, NOT a party share. The one-dimensional Gaussian result is a
component center, NOT a national counterfactual share. The two-dimensional result is a
component center plus model membership, never an honesty/fraud probability.

Honor original `status`; undefined fields/groups have typed status/reason, never numeric
zero. In D, full-frame identity extension retains observed values outside native support;
it does not assert zero effect there. D is focal-party-specific, not a symmetric ten-party
reconstruction. Do not promote an unavailable group to an available scenario.

Show native vs source/full-frame coverage separately. For Cedar show included 71,438 /
87,736 and outside 16,298 (2,758 registered <=100; 13,540 unknown invalid) on the primary
default view. Anchor support N/L/O belongs next to the fixed-anchor curve and AUTO states.
It is a NON_MODEL reader diagnostic, not an honesty label. iStories reference N belongs
next to each of the 15 windows; distinguish it from the scenario frame. Do not hide small
windows or invent an acceptability cutoff. The predeclared default is not a post-result
scientific preference. Window ranges and anchor curves are specification sensitivity,
NOT confidence/credible intervals. LOO is single-region influence, not a bad-region label.
Source variants are not correctness rankings and must not be silently replaced.
For anchor interpretation, Cedar uses `(valid + known invalid) / registered voters`;
its O includes known invalid ballots. It never substitutes issued for cast. iStories
uses issued ballots / registered voters and O=valid-focal; its predeclared 20–29%
reference is technically [20%,30%). These are prospective project mappings, not
proof of the published authors' exact implementation. The official region names
in `sources.json` resolve LOO IDs without reading the scientific pipeline.

For 1D, K=3 is fixed; bin width also changes sigma_min=h/2, not pure discretization.
For 2D, the exact first coordinate is issued ballots / registered voters. Thresholds
>.5 / >.7 / >.9 reuse the same fit; unchanged centers are mechanical reuse. Diagonal
covariance is a different fitted specification. No arbitrary thresholds or K controls exist.

## Stable versus editorial

`method_id`, `state_id`, controls, hashes, result_type, value_kind, denominator_kind,
availability and interpretation guards are technical. Short neutral Russian labels are
navigation labels; `editorial_copy_status: pending` reserves final prose for later review.
Source fidelity gaps and release-license/repository details remain accepted/pending
metadata, not permissions to modify results. Only files listed by this public manifest
form the client API. Opaque local provenance paths are not additional executable routes.
