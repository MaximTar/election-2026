# election-2026

This repository currently publishes the static data layer of one election research
project. Calculation states are precomputed and frozen; clients select stored states
and do not execute scientific models.

- `publication/sites/v1/` is the canonical static publication contract.
- `publication/sites/v1/runtime/` is the lightweight delivery layer for a future
  reader-facing website / Scenario Explorer.
- Start with `publication/sites/v1/runtime/CONTRACT.md` and its `manifest.json`.
- `src/publication_sites/` contains publication generators and validators;
  accepted engineering evidence is under `outputs/sites_publication_*`.
- GitHub Pages deploys only the contents of `publication/sites/v1/`, with that
  directory as the site root. CI checks integrity and deploys stored bytes only.

This first public commit exposes the static publication/API layer, not yet the
complete research reproducibility repository. Technical provenance can reference
local artifacts that are not included in this commit. Full scientific regeneration
requires those additional frozen inputs; their absence must not be replaced with
new calculations or inferred values.

No article or public user interface is included. The reader-facing site will consume
this static data later. Different result types remain distinct; clients must honor
coverage, availability and interpretation guards.

Version `v1` is immutable. Its deployment fails if either accepted manifest changes.
Future publication changes require a new version directory.

No license is selected in this initial publication; licensing remains unresolved.
