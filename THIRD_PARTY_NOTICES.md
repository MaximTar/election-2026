# Third-party material

The project licenses cover eligible project-authored contributions only.
Third-party material retains its original copyright, license and terms, including
when quoted, excerpted, embedded in metadata, or archived for provenance. Where
origin or rights are ambiguous, the material is excluded from the project grants.
The project does not assert a source license merely because a source is public.

## Sources and exclusions

| Source / category | Role | Bytes redistributed by this project | Source license / terms |
|---|---|---|---|
| [Zhizhin](https://deg.zhizhin.xyz/) election-data snapshots | Historical party-vote and protocol inputs used to construct frozen research views | Raw snapshots are **not redistributed**. Exact identifiers, hashes, sizes and known dates are in [EXTERNAL_INPUTS.md](reproducibility/v1/EXTERNAL_INPUTS.md). Project-created derived views are supplied separately. | No license or terms are asserted by this project. |
| [Central Election Commission (CIK)](https://apps.cikrf.ru/) and election commissions | Hierarchy, protocols and official source/version verification | The raw report-453 snapshot is **not redistributed**. Decoded source fields and excerpts occur in the public provenance/audit records. Those source-origin portions remain excluded. | No license or terms are asserted by this project. |
| [Cedar-Russia / electoral_statistics](https://github.com/Cedar-Russia/electoral_statistics), commit `30b1b6ae4725e7307f67975bc122f35049864644`; [Cedar methodology](https://www.cedarus.io/research/evolution-of-russian-elections) | Published notebook and methodology used for a project adaptation | Extracted notebook cells are included in the results asset at `outputs/smz_v2_external_freeze/20261002_v2/cedar_selector_source.json`. The full upstream notebook is not included in the reproducibility manifest. See the mixed-origin code exception below. | No upstream reuse license is asserted by this project. Upstream code, notebook cells and article excerpts are excluded from the project grants. |
| [Vazhnye Istorii / iStories](https://istories.media/stories/2026/09/22/bolee-18-iz-30-mln-bumazhnikh-golosov-za-edinuyu-rossiyu-mogli-bit-sfalsifitsirovani/) | Published method description, reconstructed with documented ambiguities | Project reconstruction notes and attributed excerpts are included. No published implementation code is supplied as an exact upstream implementation. | No license or terms are asserted for the publication or its excerpts. |
| [Novaya Gazeta Europe](https://novayagazeta.eu/articles/2026/09/24/nastoiashchii-rezultat-er-dorisovki-za-oppozitsiiu-i-skorostnye-sultanaty) | Source descriptions for conventional, overlap/core, 1D and 2D methods | Project reconstruction/provenance notes and attributed excerpts are included. No separate upstream 1D/2D implementation is supplied. | No license or terms are asserted for the publication or its excerpts. |
| [Historical KSP context / dkobak/elections](https://github.com/dkobak/elections) | Historical method context and references | Project-authored context notes and references are included. The upstream repository is not vendored in the release. | Upstream material retains its own terms. This project does not assign a license to it. |
| [Neshodilina](https://neshodilina.netlify.app/api), Electoral.Graphics, Datawrapper and other cited sources | Alternative source/provenance evidence, dataset references and published figures/tables | Project documentation and derived records may contain attributed excerpts or source-origin fields. Referenced upstream publications, figures, tables and source documents are not made project-owned by inclusion or citation. | No license or terms are asserted unless an existing source notice explicitly supplies them. |

## Mixed-origin Cedar code

The files below implement the project's Cedar adaptation and contain logic
reconstructed from the upstream notebook. The provenance records do not establish
a reusable upstream license or a precise rights boundary for inherited portions.
As a conservative exception, these mixed-origin files are excluded from the
blanket MIT grant. No upstream license is invented and their bytes are unchanged:

- `src/smz_external_clite/cedar.py`
- `outputs/smz_v2_external_qualification/20261002_v1/source_snapshot/cedar.py`

Extracted upstream cells in `cedar_selector_source.json` are likewise excluded.
Project-authored commentary and contracts remain within the content scope, while
their quotations and embedded third-party source text remain excluded.

## Provenance and release history

[The release manifest](reproducibility/v1/manifest.json) identifies included files
and non-redistributed external inputs. The authoritative method/source index is
`outputs/smz_v2_external_closure/20261003_v1/external_methods_source_index.json`,
included in the [Reproducibility materials v1 results asset](https://github.com/MaximTar/election-2026/releases/tag/reproducibility-v1).
Project-created tables and results do not transfer ownership of underlying source
facts or grant rights in third-party material embedded within them.

External software dependencies retain their own licenses and are not relicensed
by these notices. The project licenses also do not cover any other copied upstream
code or source documents, even if not individually listed here.

The policy not to mirror third-party raw snapshots is a publication decision, not
a finding that their redistribution is legally forbidden. Current project grants
may cover eligible earlier project-authored contributions without changing the
original tags, release metadata or assets.
