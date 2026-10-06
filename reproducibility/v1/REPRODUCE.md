# Reproduce or verify

## A. Verify published results

Follow [VERIFY.md](VERIFY.md). This workflow is fully possible using public repository files and GitHub Release assets. No third-party raw snapshot is needed. It verifies already computed results, not a re-estimation.

Assets preserve original relative paths: `reproducibility-v1-derived-inputs.tar.gz` contains project-derived input views/selectors/eligibility metadata. `reproducibility-v1-results.tar.gz` contains frozen exact result records, original state packets, relevant source/qualification/provenance records and environment evidence. Scientific code and compact contracts are in Git. `manifest.json` binds every included path/hash/size and external input. `assets.json` binds archive hashes/contents via the manifest.

## B. Independently recompute scientific results

This requires independently obtaining exact external snapshots listed in [EXTERNAL_INPUTS.md](EXTERNAL_INPUTS.md). The current live source is not a substitute unless its SHA256 matches. Downloaded bytes are not supplied by this release. Never substitute new official data or choose a source because its result looks preferable.

First unpack assets, establish the compatible environment in [ENVIRONMENT.md](ENVIRONMENT.md), and place external files at their recorded project paths. Run the guards before calculation:

```sh
python3 -B -m src.reproducibility.rerun --family abcd --check-inputs-only
python3 -B -m src.reproducibility.rerun --family external --check-inputs-only
```

Missing inputs or mismatched SHA256 stop before scientific imports, data decoding, commitment creation, or any model call. The publication-derived primary and alternative views, source maps and native eligibility are already supplied with exact frozen hashes. The source universe construction and source-variant preparation code is included for inspection (`src/stage3a_v2/audit.py`, `src/stage3a_sensitivity/prepare.py`), together with their frozen membership/configuration artifacts. Their original entry points are prospective stage publishers and must not be executed over already frozen outputs. Older raw snapshots/CEC hierarchy evidence are identified for upstream construction provenance; the instructions above rerun the published calculations from the supplied frozen views, not the entire earlier collector/forensic research history.

Only after successful guards, use a NEW separate output directory:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python3 -B -m src.reproducibility.rerun --family abcd --execute --output reproduction_runs/abcd_independent_01
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python3 -B -m src.reproducibility.rerun --family external --execute --output reproduction_runs/external_independent_01
```

These commands are an independent reproduction harness, not a resumption of the consumed historical authorizations. They verify included input/code hashes and exact dependency versions, create a fresh reproduction commitment, and call unchanged historical scientific functions. ABC uses the frozen design/basis engine and exact rational evaluation. D uses the frozen native-stratum implementation. External methods load the archived qualified numerical functions through the original AST-equivalence loader, with the same inputs/ordering/controls, original fit-reuse policy, and 83-state arithmetic supplement. The only new mechanism is release-specific independent output/commitment transport. It does not alter original files or method semantics. This packaging task did NOT execute these scientific commands, so successful end-to-end independent refitting is not claimed as newly tested.

ABCD writes exact `.exact` records in the historical columnar codec and separate D strata. Compare their physical/semantic hashes to `outputs/smz_run01_reveal/20261001_v1/canonical_cell_inventory.json` / `exact_records`; floating-point external results need numeric/diagnostic comparison to the original JSON packets and `stored_results.json`, not matching run IDs or transaction timestamps. Original stored source/coverage counts and terminal statuses remain the comparison targets. Differences must be reported, never repaired by tuning. Expected topology is 1,620 ABCD cells and 445 external research states (444 public, one INTERNAL, not a publication result).

Historical external compute was approximately 4,453.255 s with peak RSS 971,304,960 bytes for 362 states, then 90.959947 s / 441,528,320 bytes for the 83 arithmetic states. ABCD historical resource records and preflight limits are retained in release provenance; the independent harness does not guarantee the same runtime or enforce old calendar deadlines. Exact rational verification can take minutes and considerable RAM. Plan adequate disk space for the approximately 1.63 GB compressed exact source records plus the public tree/assets. Gaussian/GMM numerical identity can depend on system binaries. K=3, starts, tolerances and all frozen sensitivities are unchanged.

## Publication rebuilding

The ordinary verifier compares projections in memory and writes nothing. Runtime delivery can be regenerated in a disposable copy using `/usr/bin/python3 -B -m src.publication_sites.runtime_generate`; compare every byte to the accepted runtime inventory. The original canonical/presentation generation entry points also have local historical governance/raw-input requirements. Their code and consumed source bindings are published, but do not invoke them over this immutable v1 tree or claim they work without independently supplied external inputs. This release verifies the existing canonical/runtime/presentation bytes and scientific mapping rather than silently regenerating them.

No project-wide reuse license has yet been selected. See source attribution and limitations in [SCOPE.md](SCOPE.md).
