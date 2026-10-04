# Additive static delivery contract, runtime 1

This is a delivery projection of the accepted publication view of one research project,
not a second scientific API. The canonical manifest and every canonical file remain
unchanged. All state IDs, values, availability, guards and predeclared defaults are copied.

## Load order and URL bases

1. Load this directory's `manifest.json`, then `methods.json`. No exact-file inventory is
   in the bootstrap. `canonical_publication.root` resolves to the parent publication
   directory relative to the runtime manifest URL. Do not fetch its full manifest merely
   to open the application; the bootstrap binds it by SHA256 for optional full auditing.
2. Each method wrapper has `catalog_entry`, the complete unchanged canonical method
   record, and `delivery`. A CARD_ONLY entry has `delivery=null` and no executable route.
   Paths in `catalog_entry` and inside unchanged state records are relative to the
   CANONICAL publication root. Paths in `delivery`, indexes and runtime manifest entries
   are relative to the RUNTIME manifest URL, never to the nested index or shard URL.
3. For A/B/C load its index and only the selected source + design shard. For D load its
   index and only the selected source + frozen specification shard. `routes` enumerates
   existing keys and state IDs. The chosen shard's `states` enumerate exact availability.
   A/B are aliases/slices of these records, not duplicated scientific states. Default
   pointers are inherited; their presence implies no post-results preference.
4. For the four smaller executable methods, `delivery.resource` points directly to the
   unchanged canonical state file. Do not shard them for symmetry. Its gzip alternative
   is only a transport representation of the same bytes, not another scientific state.
5. `manifest.optional_metadata` supplies canonical sources, baselines and designs, with
   optional gzip transport. A ten-party comparison needs the existing baseline and design
   context; LOO region names are in sources. These are small and need no pipeline access.
6. Marginal controls in catalogs are not a Cartesian product. Never synthesize a missing
   route/state or interpolate a result. Disable unsupported controls with the unchanged
   availability policy. Any reset must be explicit and visible, with no silent fallback.

## Values and lazy exact resources

Ordinary views use already prepared display/chart fields, native/full coverage and support.
Runtime state records are structurally identical to canonical records, including diagnostics
and undefined markers. Nothing is rounded again, calculated or interpreted here.

On explicit exact-data request, resolve `state.result.exact_file` against the CANONICAL
root and verify `exact_file_sha256`. This fetches one existing gzip resource; runtime does
not copy, decompress, re-encode or enumerate the 1,620 exact resources. The full exact
inventory remains in the accepted canonical manifest for optional reproducibility audit.
Pooled numerator/denominator strings stay strings. Integer pool indices can locate strings;
they do not authorize numeric conversion of the strings. No parseInt, Number conversion,
float conversion or BigInt arithmetic is needed for exact values. No browser-side model
reconstruction is required. Only bounded prepared DISPLAY decimals may be converted to
chart coordinates; they remain presentation values, never replacements for exact values.

## Compression and integrity

Every normal JSON delivery resource offers raw and `.json.gz` alternatives. Choose ONE.
Explicit gzip files are reproducible binary transports (mtime=0), to fetch as bytes,
verify the compressed hash when supplied, decompress once and parse JSON. Hosting must
not label these `.gz` URLs with an additional Content-Encoding:gzip layer. If a host serves
ordinary `.json` with automatic compression, that is a separate hosting behavior: the raw
JSON hash still refers to decoded bytes. This repository does not guarantee CDN compression.
Raw sizes and explicit generated-gzip sizes are reported separately, never as assumed wire
savings. `manifest.json.gz` expands exactly to the bootstrap manifest; its integrity hash
is recorded outside the self-referential manifest, in the engineering evidence inventory.

## Semantics and coverage

Always render `catalog_entry.interpretation_guards`, per-state guards and result_type.
Ten-party conditional scenarios, focal-party D, scenario focal-valid share, signed excess /
observed focal, 1D component center and 2D center/membership are distinct. Cedar is not a
party share; 1D is not a national counterfactual share; 2D membership is not honesty/fraud
probability. D undefined is not zero. Reference windows and anchors are specification
sensitivity, not confidence intervals. LOO is influence, not a bad-region label. Sources
are not correctness rankings; native universes differ and must not be silently intersected.
Do not average unlike estimands or display an implied truth scale. All reference/support
counts and reportability diagnostics remain in the unchanged records. Show them alongside
results as required by the canonical contract. Editorial copy remains pending where marked.

## Generation, checking and the accepted older tools

`/usr/bin/python3 -m src.publication_sites.runtime_generate`
`/usr/bin/python3 -m src.publication_sites.runtime_check`
`/usr/bin/python3 -m src.publication_sites.runtime_measure`

The accepted original generator/checker uses a closed recursive inventory and predates this
explicitly authorized additive subtree. Its code/bindings are retained unchanged. Do not
run its generation over the delivery tree. The runtime checker verifies all 1,640 accepted
files by their original hashes, permits only this separately inventoried subtree, then checks
the complete delivery graph. It does not rerun the scientific/publication extraction pipeline.
No framework, backend, scientific dependency change or UI is introduced.
