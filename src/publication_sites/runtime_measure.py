"""Stored-file delivery measurements only; no result analysis or exact decoding."""
import math
import statistics
from .runtime_common import *


def measure():
    m = read(RUNTIME / 'manifest.json')
    wrappers = read(RUNTIME / 'methods.json')['methods']
    methods = {w['method_id']: w for w in wrappers}

    def resource_size(resource):
        raw, gz = resolve_runtime_reference(resource['path']), resolve_runtime_reference(resource['gzip_path'])
        return {'raw_bytes': raw.stat().st_size, 'generated_gzip_bytes': gz.stat().st_size,
                'raw_path': resource['path'], 'gzip_path': resource['gzip_path']}

    bootstrap = [{'path': 'manifest.json', 'gzip_path': 'manifest.json.gz'}, m['methods_file']]

    def sizes(resources):
        dedup = {r['path']: r for r in resources}
        items = [resource_size(r) for r in dedup.values()]
        return {'raw_bytes': sum(s['raw_bytes'] for s in items),
                'generated_gzip_bytes': sum(s['generated_gzip_bytes'] for s in items),
                'file_count_if_raw_or_gzip_chosen_once': len(items), 'resources': items}

    abc, d = methods['abc']['delivery'], methods['d']['delivery']
    abc_index = read(resolve_runtime_reference(abc['index']['path']))
    d_index = read(resolve_runtime_reference(d['index']['path']))
    abc_default = abc['default_routes']['C']['resource']
    d_default = d['default_routes']['D']['resource']
    external = {name: resource_size(methods[name]['delivery']['resource'])
                for name in COUNTS if name not in ('abc', 'd')}
    cmanifest = read(CANONICAL / 'manifest.json')
    exact_sizes = sorted(item['bytes'] for name, item in cmanifest['files'].items() if name.startswith('exact/'))
    need(len(exact_sizes) == 1620, 'exact sidecar inventory count')
    default_c = next(s for s in read(resolve_runtime_reference(abc_default['path']))['states']
                     if s['state_id'] == abc['default_routes']['C']['state_id'])
    example = canonical_exact_reference(default_c)
    ABC_context = [m['optional_metadata'][name] for name in ('baselines', 'designs')]
    source_context = [m['optional_metadata']['sources']]
    runtime_files = list(p for p in RUNTIME.rglob('*') if p.is_file())
    # Count each logical JSON resource once, not both alternative encodings.
    # The full logical graph also includes the seven canonical-backed resources.
    logical = [{'path': str(p.relative_to(RUNTIME)),
                'gzip_path': str(p.relative_to(RUNTIME)) + '.gz'}
               for p in runtime_files if p.suffix == '.json']
    logical += list(m['optional_metadata'].values())
    logical += [methods[name]['delivery']['resource'] for name in COUNTS if name not in ('abc', 'd')]
    result = {
        'measurement_type': 'STATIC_TRANSPORT_ONLY_NO_RESULT_INTERPRETATION',
        'compression_level': 6, 'gzip_mtime': 0,
        'host_automatic_compression_guaranteed': False,
        'gzip_size_meaning': 'BYTES_OF_GENERATED_EXPLICIT_GZIP_ALTERNATIVE_NOT_CDN_ASSUMPTION',
        'bootstrap_manifest': resource_size(bootstrap[0]), 'bootstrap_catalog': resource_size(m['methods_file']),
        'bootstrap_combined': sizes(bootstrap),
        'default_ABC_shard': resource_size(abc_default),
        'ABC_index': resource_size(abc['index']),
        'all_ABC_index_and_shards': sizes([abc['index']] + [r['resource'] for r in abc_index['routes']]),
        'D_index': resource_size(d['index']), 'default_D_shard': resource_size(d_default),
        'all_D_index_and_shards': sizes([d['index']] + [r['resource'] for r in d_index['routes']]),
        'D_largest_shard': max((resource_size(r['resource']) for r in d_index['routes']), key=lambda x: x['raw_bytes']),
        'external_method_state_files': external,
        'canonical_exact_sidecars': {'files': len(exact_sizes), 'already_compressed': True,
            'median_compressed_bytes': statistics.median(exact_sizes),
            'p95_compressed_bytes': exact_sizes[math.ceil(.95 * len(exact_sizes)) - 1],
            'max_compressed_bytes': max(exact_sizes), 'p95_rule': 'NEAREST_RANK_CEIL_0.95_N'},
        'browser_paths': {
            'A_initial_bootstrap': sizes(bootstrap),
            'B_open_default_ABC_incremental_after_bootstrap': sizes([abc['index'], abc_default] + ABC_context + source_context),
            'B_open_default_ABC_total_cold': sizes(bootstrap + [abc['index'], abc_default] + ABC_context + source_context),
            'C_change_ABC_source_design_if_index_cached': {
                'requested_resources': 1, 'raw_min_bytes': min(resource_size(r['resource'])['raw_bytes'] for r in abc_index['routes']),
                'raw_max_bytes': max(resource_size(r['resource'])['raw_bytes'] for r in abc_index['routes']),
                'gzip_min_bytes': min(resource_size(r['resource'])['generated_gzip_bytes'] for r in abc_index['routes']),
                'gzip_max_bytes': max(resource_size(r['resource'])['generated_gzip_bytes'] for r in abc_index['routes']),
                'no_fetch_if_active_shard_cached': True, 'exact_sidecars_loaded': 0},
            'D_open_default_D_incremental_after_bootstrap': sizes([d['index'], d_default] + ABC_context + source_context),
            'D_open_default_D_total_cold': sizes(bootstrap + [d['index'], d_default] + ABC_context + source_context),
            'E_open_one_small_method_incremental_after_bootstrap': external,
            'F_explicit_exact_request_example': {'state_id': default_c['state_id'],
                'path_relative_to_canonical_root': default_c['result']['exact_file'],
                'compressed_bytes': example.stat().st_size, 'exact_sidecars_loaded': 1,
                'optional_full_integrity_catalog_raw_bytes': (CANONICAL / 'manifest.json').stat().st_size,
                'per_state_hash_already_in_selected_record': True},
        },
        'total_runtime_layer_excluding_exact': {'files': len(runtime_files),
            'all_physical_runtime_bytes_including_raw_and_gzip_alternatives': sum(p.stat().st_size for p in runtime_files),
            'complete_logical_JSON_graph': {k: v for k, v in sizes(logical).items() if k != 'resources'},
            'documentation_bytes_not_needed_for_app_fetch': sum(p.stat().st_size for p in runtime_files if p.suffix == '.md'),
            'canonical_backed_small_methods_not_duplicated_as_raw_runtime_JSON': True,
            'ordinary_view_exact_sidecars_loaded': 0},
        'performance_targets': {
            'bootstrap_raw_below_200000': sizes(bootstrap)['raw_bytes'] < 200000,
            'default_ABC_state_payload_raw_below_500000': resource_size(abc_default)['raw_bytes'] < 500000,
            'no_initial_exact_fetch': True, 'no_ordinary_full_ABC_fetch': True},
    }
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / 'size_report.json').write_bytes(encode(result))
    print(json.dumps({'status': 'MEASURED', 'bootstrap': result['bootstrap_combined'],
                      'default_ABC_shard': result['default_ABC_shard'],
                      'total_runtime': result['total_runtime_layer_excluding_exact'],
                      'targets': result['performance_targets']}))
    return result


if __name__ == '__main__':
    measure()
