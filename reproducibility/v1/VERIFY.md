# Verify frozen published results without external raw inputs

1. Clone the public repository at `reproducibility-v1` and download the release assets.

```sh
git clone --branch reproducibility-v1 https://github.com/MaximTar/election-2026.git
cd election-2026
mkdir -p release-assets
gh release download reproducibility-v1 --repo MaximTar/election-2026 --dir release-assets
```

2. Compare each asset's SHA256/size with `reproducibility/v1/assets.json`. Inspect member paths before extracting, then extract at repository root (the archives contain only relative project paths).

```sh
sha256sum release-assets/*.tar.gz
tar -tzf release-assets/reproducibility-v1-derived-inputs.tar.gz
tar -tzf release-assets/reproducibility-v1-results.tar.gz
tar -xzf release-assets/reproducibility-v1-derived-inputs.tar.gz
tar -xzf release-assets/reproducibility-v1-results.tar.gz
```

3. With Python >=3.10 and `jsonschema` available, run:

```sh
/usr/bin/python3 -B -m src.reproducibility.check_v1 --assets release-assets
```

This verifies assets/members and release file hashes, exact source-result/publication projections, all 1,620 A/B/C/D exact sidecars, 444 public external states, 2,064 unique public IDs, zero INTERNAL export, zero CARD_ONLY results, schema/semantic guards, explicit runtime routing, and the accepted presentation bindings/parameters. It imports no source provider or scientific kernel. It requires none of the external raw snapshots.

For a faster hashes/count-binding check after the full first verification, use `--hashes-only`. It still checks the recorded expected external-input hashes and their explicit non-inclusion, not whether absent files can be recovered from the Internet.

The accepted canonical manifest is `38d8f0eaa79952b4036d7e23c04ff40cca65f51e40f5cbbcddc88efd92fc3d16`, runtime `3998d58ec33c4bb8d28b6a35abdb5d2d2d28772a7aaea20b7fbd61afd598131c`, presentation `beb00a95ad1f1d9edc5e05fff17b033a7f23649ecee9b470520b8838f5f7e771`.

The old `src.publication_sites check` predates the additive runtime subtree and reports its 187 files as extras (zero canonical files missing). Do not edit accepted data to satisfy that obsolete closed inventory. `src.publication_sites.runtime_check` is the authoritative additive closure checker. The release verifier additionally compares the unchanged canonical records/sidecars to their frozen scientific sources, without requiring the complete private historical governance tree. The accepted presentation checker can verify public chart content in a partial checkout; its optional local source/protected-tree branch has external raw dependencies. The release verifier checks chart file hashes, public references and stored fitted parameters without those raw dependencies.

No check is an election-model rerun. Verification of frozen hashes/results does not establish self-contained historical raw-data availability.

The portable adapter also runs the unchanged presentation checker with only its optional whole-local-worktree report lookup directed to the release directory. All chart arithmetic/schema/parameter checks stay active. This avoids requiring unpublished article files and excluded raw snapshots merely for an old local protected-tree audit. The release manifest and archive checks protect the actual public payload instead. Stored parameter comparisons additionally read the original packets from the public results asset.
