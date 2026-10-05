# Static chart presentation data

Load manifest.json, then only the selected chart file. Coordinates are ratios; bin indices
refer to documented origin/step. Sparse grid rows follow the columns array, never raw UIK rows.
Counts/volume channels are separate; vote/voter sums do not redefine model fit weights.
Exact rationals stay strings and frozen binary64 values retain float_hex. Prepared display
numbers and curves are for rendering; no browser model reconstruction is required.
Source state IDs use public publication aliases; opaque local paths are technical provenance.
The public repository does not yet include all frozen input files needed for regeneration.

All charts are deterministic presentation projections, not new states or inference. No
fraud classification, truth interval or averaging across unlike result types is allowed.
1D fitted curves are evaluated from stored parameters; stored SSE provides an independent
reproduction check because a pre-evaluated total curve was not persisted. 2D per-cell membership
is unavailable: neither posteriors nor member indices survived immutable export. The stored
aggregate membership is retained; a missing cell field must never be rendered as zero.

A/B/C and D use existing ../../v1/runtime data; no new chart results are introduced here.
Generate locally: python3 -m src.publication_sites.presentation_generate
Validate locally or in public checkout: python3 -m src.publication_sites.presentation_check
Do not run generation in deployment CI. Deploy accepted static bytes only.
