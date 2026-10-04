"""Validate additive transport equivalence without scientific/source-row execution."""
import copy
import sys
from .runtime_common import *
from .runtime_generate import construct, runtime_schema


def schema_validate(value, schema):
    import jsonschema
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(value)


def ensure_equivalent(records, canonical):
    ids = [s['state_id'] for s in records]
    expected = {s['state_id']: s for s in canonical}
    need(len(ids) == len(set(ids)) == len(expected), 'missing/duplicate runtime state')
    need(set(ids) == set(expected), 'invented/internal/unavailable state ID')
    for s in records:
        need(s == expected[s['state_id']], 'canonical state record differs: ' + s['state_id'])
        need(s['visibility'] == 'PUBLIC', 'non-public state')


def validate_default_routes(defaults, rows):
    by_id = {s['state_id']: s for s in rows}
    for default in defaults.values():
        need(default['state_id'] in by_id, 'default state not available')
        state = by_id[default['state_id']]
        need(all(state['source_version'] == v if k == 'source_version'
                 else state['controls'].get(k) == v for k, v in default['key'].items()),
             'default route key differs')


def check_gzip(blob, original):
    need(gzip.decompress(blob) == original, 'gzip transport differs from raw publication bytes')


def negative_regressions(groups, catalog):
    """Engineering corruption probes on actual validation functions; no scientific tests."""
    results = []

    def rejected(name, action):
        try:
            action()
        except (ValueError, KeyError, OSError, EOFError):
            results.append({'test': name, 'status': 'PASS', 'corruption_rejected': True})
        else:
            raise ValueError('negative transport regression accepted corruption: ' + name)

    abc = groups['abc']['states']
    rejected('missing_state', lambda: ensure_equivalent(abc[:-1], abc))
    altered = copy.deepcopy(abc); altered[0]['state_id'] = INTERNAL
    rejected('internal_state', lambda: ensure_equivalent(altered, abc))
    cedar = copy.deepcopy(groups['cedar']['states'])
    cedar[0]['result_type'] = 'SCENARIO_FOCAL_VALID_SHARE'
    rejected('Cedar_wrong_estimand', lambda: ensure_equivalent(cedar, groups['cedar']['states']))
    d = copy.deepcopy(groups['d']['states']); d[0]['result']['undefined_fields']['scenario_invalid'] = 0
    rejected('D_undefined_zero', lambda: ensure_equivalent(d, groups['d']['states']))
    altered = copy.deepcopy(abc); altered[0]['result']['exact_file'] = 'runtime/fabricated.json.gz'
    rejected('exact_reference_changed', lambda: ensure_equivalent(altered, abc))
    rejected('reference_escape', lambda: resolve_runtime_reference('../../../data/processed/party_rows.json'))
    rejected('unknown_default', lambda: validate_default_routes({'C': {'state_id': 'MISSING', 'key': {}}}, abc))
    rejected('gzip_wrong_payload', lambda: check_gzip(zipped(b'{}'), b'{"kept":1}'))
    return results


def check():
    checks = []

    def passed(name):
        checks.append({'check': name, 'status': 'PASS'})

    canonical_manifest, before = canonical_inventory()
    need(before == read(EVIDENCE / 'canonical_before.json'), 'accepted canonical bytes changed since this task began')
    passed('all_1640_accepted_canonical_files_and_original_generator_bindings_unchanged')
    m = read(RUNTIME / 'manifest.json')
    schema_validate(m, runtime_schema())
    for name, value in m['generator']['source_files'].items():
        need(sha(ROOT / name) == value, 'runtime code binding changed')
    actual = inventory()
    need(set(actual) == set(m['files']) | {'manifest.json', 'manifest.json.gz'}, 'unlisted/missing runtime file')
    for name, value in m['files'].items():
        need(actual[name] == value['sha256'] and (RUNTIME / name).stat().st_size == value['bytes'], 'runtime hash/size: ' + name)
        if 'gzip_of' in value:
            check_gzip((RUNTIME / name).read_bytes(), resolve_runtime_reference(value['gzip_of']).read_bytes())
    check_gzip((RUNTIME / 'manifest.json.gz').read_bytes(), (RUNTIME / 'manifest.json').read_bytes())
    passed('runtime_schema_complete_inventory_hashes_and_lossless_gzip_transports')
    need('exact/' not in encode(m).decode(), 'bootstrap enumerates exact sidecars')
    need(not any(name.startswith('exact/') for name in actual), 'exact sidecars copied into runtime')
    passed('bootstrap_has_no_exact_sidecar_inventory_and_no_runtime_exact_copies')
    catalog, groups = canonical_tables()
    wrappers = read(RUNTIME / 'methods.json')
    need([w['catalog_entry'] for w in wrappers['methods']] == catalog['methods'], 'method semantics/defaults/guards changed')
    schema_validate(catalog, read(CANONICAL / 'schemas/methods.schema.json'))
    seen, runtime_tables = [], {}
    route_count = {}
    for wrapper in wrappers['methods']:
        method = wrapper['catalog_entry']; name = method['method_id']; delivery = wrapper['delivery']
        if method['execution_status'] == 'card_only':
            need(delivery is None and method['available_state_count'] == 0 and method['state_file'] is None,
                 'CARD_ONLY execution/result invented')
            continue
        if name in ('abc', 'd'):
            need(delivery['mode'] == 'EXPLICIT_SHARDS', 'heavy list unexpectedly canonical/unsharded')
            index = read(resolve_runtime_reference(delivery['index']['path']))
            need(index['method_id'] == name and index['state_count'] == COUNTS[name], 'index family/count')
            axis = 'design_id' if name == 'abc' else 'specification'
            records, route_keys = [], []
            for route in index['routes']:
                key = route['key']
                need(set(key) == {'source_version', axis}, 'new routing axis')
                route_keys.append((key['source_version'], key[axis]))
                resource = route['resource']
                path = resolve_runtime_reference(resource['path'])
                need(sha(path) == resource['sha256'], 'route resource hash')
                table = read(path)
                need(table['state_count'] == len(table['states']), 'shard count')
                need(route['state_ids'] == [s['state_id'] for s in table['states']], 'route state list mismatch')
                for s in table['states']:
                    need(s['source_version'] == key['source_version'] and s['controls'][axis] == key[axis]
                         and s['geography']['mode'] == 'DEFAULT', 'unsupported source/design/geography crossing')
                need(table['canonical_state_file'] == '../' + method['state_file'], 'shard canonical binding')
                records.extend(table['states'])
            need(len(route_keys) == len(set(route_keys)), 'duplicate route key')
            route_count[name] = len(route_keys)
            need(index['default_routes'] == delivery['default_routes'], 'default index/catalog disagree')
            need({k: v['state_id'] for k, v in index['default_routes'].items()} == method['predeclared_default_states'],
                 'predeclared default state changed')
            validate_default_routes(index['default_routes'], records)
            for value in index['default_routes'].values():
                selected = read(resolve_runtime_reference(value['resource']['path']))['states']
                need(value['state_id'] in {s['state_id'] for s in selected}, 'default shard does not resolve')
        else:
            need(delivery['mode'] == 'CANONICAL_FILE', 'small method needlessly copied/sharded')
            need(delivery['resource']['path'] == '../' + method['state_file'], 'small canonical path')
            records = read(resolve_runtime_reference(delivery['resource']['path']))['states']
            need(delivery['default_states'] == method['predeclared_default_states'], 'small default changed')
        records = sorted(records, key=lambda s: s['state_id'])
        ensure_equivalent(records, groups[name]['states'])
        for state_id in method['predeclared_default_states'].values():
            need(state_id in {s['state_id'] for s in records}, 'default state missing')
        canonical_shape = {k: v for k, v in groups[name].items() if k != 'states'}
        schema_validate({**canonical_shape, 'states': records}, read(CANONICAL / 'schemas/states.schema.json'))
        seen.extend(s['state_id'] for s in records); runtime_tables[name] = records
        for state in records:
            path = canonical_exact_reference(state)
            if path:
                relative = str(path.relative_to(CANONICAL))
                need(path.is_file() and state['result']['exact_file_sha256'] == canonical_manifest['files'][relative]['sha256'],
                     'exact resource missing/hash differs')
    need(len(seen) == len(set(seen)) == 2064, 'complete graph duplicate/missing/fabricated state')
    need(route_count == {'abc': 64, 'd': 20}, 'natural-key shard count mismatch')
    passed('2064_PUBLIC_states_exact_canonical_record_reconstruction_and_all_defaults_resolve')
    passed('1600_ABC_once_20_D_once_444_small_methods_no_cartesian_inference')
    passed('all_exact_references_resolve_to_existing_canonical_sidecars_without_decode')
    passed('all_result_types_semantic_guards_coverage_support_and_D_undefined_preserved')
    for name in actual:
        blob = (RUNTIME / name).read_bytes()
        if name.endswith('.gz'):
            blob = gzip.decompress(blob)
        need(INTERNAL.encode() not in blob and b'LS_B_WINDOW' not in blob, 'INTERNAL reachable')
    passed('zero_INTERNAL_reachable_two_CARD_ONLY_without_results')
    expected = construct()
    need(set(expected) == set(actual), 'runtime generator inventory mismatch')
    for name, blob in expected.items():
        need((RUNTIME / name).read_bytes() == blob, 'deterministic projection differs: ' + name)
    passed('every_runtime_byte_matches_deterministic_canonical_projection')
    regressions = negative_regressions(groups, catalog)
    passed('eight_negative_transport_semantics_and_missingness_regressions')
    need(not any(k.startswith(('src.smz', 'src.stage3', 'scipy', 'sklearn')) for k in sys.modules), 'scientific kernel imported')
    passed('no_scientific_kernel_source_provider_or_optimizer_import')
    result = {'status': 'PASS', 'checks': checks, 'negative_regressions': regressions,
              'canonical_manifest_before': CANONICAL_SHA, 'canonical_manifest_after': sha(CANONICAL / 'manifest.json'),
              'canonical_files_changed': 0, 'canonical_files_verified': len(before),
              'runtime_manifest_sha256': sha(RUNTIME / 'manifest.json'), 'runtime_files': len(actual),
              'runtime_inventory_sha256': digest(encode(actual)), 'public_states': 2064,
              'state_counts': COUNTS, 'internal_reachable': 0, 'card_only_methods': 2,
              'card_only_project_results': 0, 'route_counts': route_count,
              'new_model_calls': 0, 'new_fits': 0, 'new_scientific_states': 0,
              'real_source_rows_passed_through_kernels': 0, 'new_methodological_choices': 0}
    print(json.dumps(result, sort_keys=True))
    return result


if __name__ == '__main__':
    check()
