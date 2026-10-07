# election-2026

One research project with frozen, precomputed conditional calculation outputs.
Different method outputs have different meanings and are not estimates that can be
averaged into one election result.

- [Public static data endpoint](https://maximtar.github.io/election-2026/).
- Canonical publication contract: `publication/sites/v1/`.
- Lightweight client delivery: `publication/sites/v1/runtime/`.
- [Chart presentation data](https://maximtar.github.io/election-2026/presentation/20261005_v1/manifest.json).
- [Reproducibility materials v1](reproducibility/v1/REPRODUCE.md).
- [Fast frozen-result verification](reproducibility/v1/VERIFY.md).
- [GitHub Release and large frozen assets](https://github.com/MaximTar/election-2026/releases/tag/reproducibility-v1).
- [External-input identifiers and hashes](reproducibility/v1/EXTERNAL_INPUTS.md).

Scientific code and compact release documentation are in the repository. Larger
project-derived inputs, exact frozen results and provenance are supplied as Release
assets. Source-origin raw snapshots, including Zhizhin snapshots, are intentionally
not redistributed. Exact independent scientific recomputation requires obtaining
inputs whose SHA256 matches the recorded historical snapshot. A different current
source response is not an interchangeable input.

Verification of frozen results works without these external raw snapshots. The
release covers 1,620 A/B/C/D cells and 445 external-method research states, with
2,064 PUBLIC states in the static API and no INTERNAL state exported. Two CARD_ONLY
methods have descriptions/provenance and no project execution. The anomaly-aware
branch has bounded requirements/mathematical NO-GO evidence, not model fits.

Start client integration with `publication/sites/v1/runtime/CONTRACT.md`. The
reader-facing website/Scenario Explorer consumes these static files. Its UI and
article drafts are not part of this repository release. CI deploys accepted data
bytes only and does not run or regenerate scientific calculations.

`publication-v1` and the accepted v1 manifests remain immutable. Scientific reruns
must use separate output directories and must not overwrite frozen results. See
release documentation for environment capture and historical-pipeline limitations.

## License

Project-authored code is licensed under MIT. Eligible project-authored text,
documentation, visualizations and project-created derived materials are licensed
under CC BY 4.0. Third-party source material is excluded and retains its own terms.
See the [license scope](LICENSE.md), [MIT notice](LICENSE-CODE.txt),
[content license](LICENSE-CONTENT.md) and
[third-party notices](THIRD_PARTY_NOTICES.md). The current grants also apply to
eligible earlier project-authored tagged/released versions; historical release
records remain unchanged.
