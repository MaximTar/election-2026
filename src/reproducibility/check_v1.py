"""Portable verification of PUBLIC frozen results; no external raw input required.

Never imports a source provider, numerical estimator, or scientific kernel. Does
not mutate results or regenerate files. This is the release verification adapter
for the accepted additive publication/runtime/presentation contracts.
"""
import argparse
import gzip
import hashlib
import json
import sys
import tarfile
from pathlib import Path
from .common import ROOT, RELEASE, BINDINGS, read, sha, need, safe_relative


def archive_check(directory, manifest):
    assets = read(RELEASE / 'assets.json')['assets']
    excluded_paths = {r['original_project_path'] for r in manifest['external_inputs']}
    excluded_hashes = {r['sha256'] for r in manifest['external_inputs']}
    for asset in assets:
        path = directory / asset['name']
        need(path.is_file() and sha(path) == asset['sha256'] and path.stat().st_size == asset['bytes'], 'asset hash/size')
        expected = {n: s for n, s in manifest['files'].items() if s['delivery'] == asset['name']}
        seen = []
        with tarfile.open(path, 'r|gz') as archive:
            for member in archive:
                safe_relative(member.name)
                need(member.isfile() and not member.issym() and member.name in expected, 'unexpected archive member')
                need(member.uid == member.gid == member.mtime == 0 and member.mode == 0o644, 'nondeterministic archive metadata')
                need(member.name not in excluded_paths, 'external raw input in archive')
                h = hashlib.sha256()
                stream = archive.extractfile(member)
                for b in iter(lambda: stream.read(1024 * 1024), b''):
                    h.update(b)
                digest = h.hexdigest(); spec = expected[member.name]
                need(digest == spec['sha256'] and member.size == spec['bytes'], 'member hash/size')
                need(digest not in excluded_hashes, 'raw bytes included under another name')
                seen.append(member.name)
        need(len(seen) == len(set(seen)) == len(expected) and set(seen) == set(expected), 'archive inventory closure')


def manifest_check(manifest):
    for path, digest in BINDINGS.items():
        need(sha(ROOT / path) == digest == manifest['accepted_manifest_hashes'][path], 'accepted manifest changed')
    for key in ['new_scientific_states', 'new_model_calls', 'new_fits']:
        need(manifest['assertions'][key] == 0, key)
    for key in ['canonical_publication_changed', 'runtime_changed', 'presentation_changed']:
        need(manifest['assertions'][key] is False, key)
    external = read(RELEASE / 'external_inputs.json')['inputs']
    need(external == manifest['external_inputs'] and len(external) >= 4, 'external input disappeared')
    for item in external:
        need(len(item['sha256']) == 64 and all(c in '0123456789abcdef' for c in item['sha256']), 'missing external SHA256')
        need(item['bytes'] > 0 and item['source'] and item['source_url'] and item['required_for_full_rerun'], 'external provenance incomplete')
        need(item['included_in_release'] is False and item['redistribution'] == 'not_redistributed'
             and item['EXTERNAL_INPUT'] is True and item['REDISTRIBUTED'] is False, 'external classification')
        need(item['original_project_path'] not in manifest['files'], 'external raw selected for publication')
    need(manifest['self_contained_full_rerun'] is False, 'false self-contained claim')
    for name, spec in manifest['files'].items():
        safe_relative(name)
        path = ROOT / name
        if path.is_symlink():
            need(spec.get('local_alias_target') == path.resolve().relative_to(ROOT).as_posix(), 'unregistered local alias')
        need(path.is_file() and path.stat().st_size == spec['bytes']
             and sha(path) == spec['sha256'], 'release file hash/size: ' + name)
    # Original dependency edges, checked without whole historical governance tree.
    pins = read(ROOT / 'outputs/sites_publication_data/20261004_v1/input_bindings.json')
    membership = {}
    for record in pins['manifests']:
        path = ROOT / record['path']
        need(sha(path) == record['sha256'], 'pinned authority manifest')
        for name, digest in read(path)['files'].items():
            membership.setdefault(name, set()).add(digest)
    for name, digest in pins['files'].items():
        need(digest in membership.get(name, set()) and sha(ROOT / name) == digest, 'consumed frozen dependency')
    for path, expected in BINDINGS.items():
        base = (ROOT / path).parent
        for name, meta in read(ROOT / path)['files'].items():
            need(sha(base / name) == meta['sha256'] and (base / name).stat().st_size == meta['bytes'], 'static tree closure')


def mappings_check():
    from src.publication_sites import data
    from src.publication_sites.check import schema_validate, valid_numbers
    from src.publication_sites.runtime_check import check as runtime_check
    from src.publication_sites.presentation_check import finite, validate_schema
    files = {}
    groups, order = data.build_abc_d(files)
    groups.update(data.build_external())
    all_ids = []
    canonical = ROOT / 'publication/sites/v1'
    for method, records in groups.items():
        records.sort(key=lambda r: r['state_id'])
        stored = read(canonical / 'states' / (method + '.json'))
        need(stored['states'] == records, 'scientific/publication projection: ' + method)
        schema_validate(stored, read(canonical / 'schemas/states.schema.json'))
        for state in records:
            need(state['visibility'] == 'PUBLIC' and 'LS_B_WINDOW' not in state['state_id'], 'INTERNAL export')
            valid_numbers(state['result'])
            all_ids.append(state['state_id'])
    need(len(all_ids) == len(set(all_ids)) == 2064, 'public inventory')
    need({k: len(v) for k, v in groups.items()} == {'abc': 1600, 'd': 20, 'cedar': 161, 'vazhnye_istorii': 102, 'novaya_1d': 90, 'novaya_2d': 91}, 'family counts')
    for name, blob in files.items():
        # Hash closure above proves stored gzip bytes. Decode equality is portable
        # across Python gzip header versions, preserving exact integer strings.
        need(json.loads(gzip.decompress(blob)) == json.loads(gzip.decompress((canonical / name).read_bytes())), 'exact sidecar scientific mapping')
    catalog = read(canonical / 'methods.json')
    need(catalog == data.catalog(groups), 'method guards/catalog')
    card_only = [r for r in catalog['methods'] if r['execution_status'] == 'card_only']
    need(len(card_only) == 2 and all(r['available_state_count'] == 0 and r['state_file'] is None for r in card_only), 'CARD_ONLY result')
    runtime = runtime_check()
    from src.publication_sites import presentation_check
    # The original checker has an optional WHOLE LOCAL WORKTREE inventory, which
    # intentionally includes non-redistributed raw inputs and article drafts. The
    # portable release has its own explicit inventory above. Redirect only that
    # optional local-report lookup, never data paths or scientific bindings, and
    # retain every chart schema/arithmetic/parameter validation. This adaptation
    # is disclosed in VERIFY.md; the accepted checker file is unchanged.
    original_report = presentation_check.REPORT
    try:
        presentation_check.REPORT = RELEASE
        chart_checks = presentation_check.check()
    finally:
        presentation_check.REPORT = original_report
    presentation = ROOT / 'publication/sites/presentation/20261005_v1'
    pm = read(presentation / 'manifest.json')
    schema = read(presentation / 'chart.schema.json')
    for chart in pm['charts']:
        content = read(presentation / chart['file'])
        validate_schema(content, schema); finite(content)
        need(set(chart['source_state_ids']) <= set(all_ids), 'chart references non-public state')
    # Compare chart fitted parameters directly to original stored packets. This
    # path never needs precinct rows, histogram reconstruction, or model inference.
    for method, chart_name, fields in [
        ('novaya_1d', 'novaya_1d_default_fit.json', {'parameters_exact_stored': 'parameters'}),
        ('novaya_2d', 'novaya_2d_default_density.json', {'means_exact_stored': 'means', 'covariances_exact_stored': 'covariances', 'weights_exact_stored': 'weights'}),
    ]:
        state = next(s for s in groups[method] if s['source_version'] == 'primary' and s['provenance']['original_state_id'].endswith('__DEFAULT__B'))
        result = state['result']['exact_stored']
        content = read(presentation / chart_name)
        packet = read(ROOT / state['provenance']['stored_packet']['path'])
        original = packet.get('result', packet.get('stored_result', packet))
        for field, key in fields.items():
            need(content[field] == original[key], 'frozen chart parameters')
    need(not any(k.startswith(('src.smz', 'scipy', 'sklearn')) for k in sys.modules), 'scientific import during VERIFY')
    return {'public_states': 2064, 'ABCD': 1620, 'external_research': 445,
            'external_public': 444, 'internal_exported': 0, 'card_only_project_results': 0,
            'runtime_check': runtime['status'], 'presentation_frozen_bindings': 'PASS',
            'presentation_public_checks': chart_checks['status'],
            'presentation_local_optional_provenance': chart_checks['checks']['local_authoritative_parameter_bindings'],
            'exact_result_mapping': 'PASS'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', type=Path)
    parser.add_argument('--hashes-only', action='store_true')
    args = parser.parse_args()
    manifest = read(RELEASE / 'manifest.json')
    manifest_check(manifest)
    if args.assets:
        archive_check(args.assets, manifest)
    result = {'status': 'PASS', 'release_files_verified': len(manifest['files']),
              'external_raw_files_required_for_verification': 0, 'model_calls': 0,
              'new_fits': 0, 'new_scientific_states': 0,
              'accepted_manifest_hashes': BINDINGS}
    if not args.hashes_only:
        result.update(mappings_check())
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    if hasattr(sys, 'set_int_max_str_digits'):
        sys.set_int_max_str_digits(0)
    main()
