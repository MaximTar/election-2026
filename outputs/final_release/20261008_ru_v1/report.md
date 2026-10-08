# Russian public release v1 — final freeze record

Release ID: `ru-release-v1`. Date: 2026-10-08. Final release gate: **PASS**.

This is a bounded release audit and metadata freeze. No article, site, scientific code, result, license or accepted publication file was changed. The repository was clean before this stage at `c001f2be25d2d1ed96ddb991677935c7a06487ae`. The new annotated tag resolves to the commit containing this record and its manifest. Existing `publication-v1` and `reproducibility-v1` tags remain unchanged.

## Public release

- Website: https://election-2026-explorer.max-tar.chatgpt.site/
- Technical article: https://election-2026-explorer.max-tar.chatgpt.site/article
- Methods: https://election-2026-explorer.max-tar.chatgpt.site/methods
- Sources: https://election-2026-explorer.max-tar.chatgpt.site/sources
- Reproducibility materials: https://github.com/MaximTar/election-2026/releases/tag/reproducibility-v1

All four website routes and the reproducibility release returned HTTP 200. Commit-pinned article sources and the article package manifest returned HTTP 200. Public scientific JSON files returned HTTP 200 with JSON MIME types and matched local bytes. Response fingerprints and exact URLs are recorded in `manifest.json`.

## Frozen bindings

| Artifact | SHA256 |
|---|---|
| `publication/articles/v2/technical_article.md` | `f08eba55efabb86fd996b2c99d81d7c0a75ed064d8229122a4ac16e43767f19f` |
| `publication/articles/v2/narrative.md` | `fdf9226505f85b34e45f0a3831bff8485c8093e25405276fd9748c6287872e0d` |
| `publication/articles/v2/manifest.json` | `7734a9b50f89d60792867174eef2920c28a0f689be1d3cab4169306bcb3c8fb0` |
| `publication/sites/v1/manifest.json` | `38d8f0eaa79952b4036d7e23c04ff40cca65f51e40f5cbbcddc88efd92fc3d16` |
| `publication/sites/v1/runtime/manifest.json` | `3998d58ec33c4bb8d28b6a35abdb5d2d2d28772a7aaea20b7fbd61afd598131c` |
| `publication/sites/presentation/20261005_v1/manifest.json` | `beb00a95ad1f1d9edc5e05fff17b033a7f23649ecee9b470520b8838f5f7e771` |

Authoritative technical source: https://raw.githubusercontent.com/MaximTar/election-2026/c001f2be25d2d1ed96ddb991677935c7a06487ae/publication/articles/v2/technical_article.md

The article package manifest matches both file sizes and hashes. The narrative remains byte-identical to its v1 publication. All accepted hashes above were verified unchanged before and after audit checks.

## Scope and visibility

Primary universe remains `paper_primary`: 87,736 paper UIKs, 84 regions and 2,818 official TIKs. DEG is outside the core scenario universe; overseas voting remains separate. No membership, rows, geography, votes, electorate, denominator or field semantics changed.

| Public family | States |
|---|---:|
| A/B/C | 1,600 |
| D | 20 |
| Vazhnye Istorii reconstruction | 102 |
| Cedar adaptation | 161 |
| Novaya 1D reconstruction | 90 |
| Novaya 2D reconstruction | 91 |
| Total | 2,064 |

The public API/Explorer export contains **0 INTERNAL states**. The research archive separately retains its one explicitly INTERNAL state, which is not promoted to public result data. Both CARD_ONLY methods remain documentation/provenance only, with **0 executable project results**. Frozen research inventories remain 1,620 A/B/C/D cells and 445 external-method states (444 PUBLIC, 1 INTERNAL).

## QA and automated checks

`manual_visual_qa = PASS`, source: **user browser review**. Scope: Article desktop/mobile layout, bullet markers, mobile tables/overflow, generic density and Cedar figures, compact A/B/C figure and mobile readability, figures generally, and Methods/Sources UX. This was not an automated browser test.

Read-only checks completed with PASS:

- `/usr/bin/python3 -B -m src.publication_sites.runtime_check`: accepted canonical bytes, runtime inventory, exact record projections, all default routing, 2,064 public states, semantic guards, zero reachable INTERNAL states and state-less CARD_ONLY methods.
- `/usr/bin/python3 -B -m src.publication_sites.presentation_check`: file/hash closure, stored parameter and curve consistency, public scope and protected artifact bindings. It does not fit models or regenerate outputs.
- Direct HTTP/download audit: article bindings, three accepted manifests, method catalog and all six canonical state files match local bytes; independent public inventory reconciles to 2,064 unique states.
- Separate self-review: publication-critical bindings and visibility reconcile; no universe change, collateral exclusion, new assumption, parameter choice, scientific result alteration or content edit.

No obsolete historical checker was used to demand changes to accepted additive runtime artifacts.

## License

Project-authored code: MIT. Eligible project-authored text, visualizations and project-created derived materials: CC BY 4.0, to the extent the project owns the relevant rights. Third-party material is excluded from blanket grants and retains its own terms. `LICENSE.md`, `LICENSE-CODE.txt`, `LICENSE-CONTENT.md` and `THIRD_PARTY_NOTICES.md` are present and unchanged.

## Known limitations and non-claims

- Third-party raw source snapshots are intentionally not redistributed. Exact full scientific rerun requires independently obtaining matching external input bytes and verifying their recorded SHA256.
- Manual browser QA is user-reported, not an automated cross-browser test. HTTP checks do not prove rendered layout or character-by-character equality between the hosted article and its Markdown source.
- English localization is not part of this release.
- The Git tag freezes this record and repository bindings. The separately hosted live website remains an external deployment; HTTP response fingerprints record the version observed during this audit.
- Historical environment capture and numeric-versus-byte reproduction limitations remain as documented in reproducibility/v1/REPRODUCE.md.

This release does not establish a true election result, prove violations from statistical unusualness, classify precincts as honest/fraudulent, or interpret component-membership probability as honesty probability. Unlike method outputs remain separate estimands. Sensitivity grids are not uncertainty intervals.

## Decisions and closure

- **User requirement:** freeze the current Russian release after user browser QA. Quantitative scientific impact: zero. Existing immutable releases and all scientific bindings are preserved.
- **Engineering choice:** use an annotated final-release tag and this record rather than an additional GitHub Release page. It identifies the repository freeze without relocating the public API or altering the externally hosted site.

`new_scientific_states = 0`, `fits = 0`, `model_calls = 0`, `scientific_data_regenerated = false`. No anomaly branch was reopened. No article or UI work was performed.

### Handoff

- Stage completed: Russian public release v1 final freeze audit
- Primary universe: unchanged `paper_primary`
- Input rows: 87,736 primary UIKs, no scientific execution
- Output/analysed rows: 2,064 stored public states audited, no new row analysis
- Rows excluded: 0 new exclusions
- Regions included/excluded: unchanged 84 primary regions, 0 new regional exclusions
- New methodological choices: 0
- Important unresolved issues: accepted limitations above, no release blocker
- Reviewer attention: manual QA provenance, external raw input requirement, distinct estimands and INTERNAL scope
- Safe to proceed: YES, Russian release closure only. English localization, analytics, PR, maintenance or new scientific work require a new post-release stage
