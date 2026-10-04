"""Build an additive routing/transport projection of accepted publication JSON."""
import sys
import zlib
from .runtime_common import *

NUMERIC_POLICY = {
    'exact_integer_strings': 'KEEP_STRINGS_WITHOUT_NUMERIC_COERCION',
    'integer_pool_references': 'LOOK_UP_STRINGS_ONLY',
    'scientific_arithmetic_in_client': False,
    'BigInt_arithmetic_required': False,
    'exact_parseInt_or_float_conversion_allowed': False,
    'chart_values': 'UNCHANGED_PREPARED_CANONICAL_DISPLAY_FIELDS',
    'display_decimal_strings': 'BOUNDED_PRESENTATION_DECIMALS_ONLY_MAY_BE_CONVERTED_FOR_CHART_COORDINATES',
    'exact_resources': 'EXPLICIT_USER_REQUEST_ONLY_NO_BOOTSTRAP_OR_ORDINARY_VIEW_READ',
}

CONTRACT = '''# Additive static delivery contract, runtime 1

This is a delivery projection of the accepted publication view of one research project,
not a second scientific API. The canonical manifest and every canonical file remain
unchanged. All state IDs, values, availability, guards and predeclared defaults are copied.

## Load order and URL bases

1. Load this directory's `manifest.json`, then `methods.json`. No exact-file inventory is
   in the bootstrap. `canonical_publication.root` resolves to the parent publication
   directory relative to the runtime manifest URL. Do not fetch its full manifest merely
   to open the application; the bootstrap binds it by SHA256 for optional full auditing.
2. Each method wrapper has `catalog_entry`, the complete unchanged canonical method
   record, and `delivery`. A CARD_ONLY entry has `delivery=null` and no executable route.
   Paths in `catalog_entry` and inside unchanged state records are relative to the
   CANONICAL publication root. Paths in `delivery`, indexes and runtime manifest entries
   are relative to the RUNTIME manifest URL, never to the nested index or shard URL.
3. For A/B/C load its index and only the selected source + design shard. For D load its
   index and only the selected source + frozen specification shard. `routes` enumerates
   existing keys and state IDs. The chosen shard's `states` enumerate exact availability.
   A/B are aliases/slices of these records, not duplicated scientific states. Default
   pointers are inherited; their presence implies no post-results preference.
4. For the four smaller executable methods, `delivery.resource` points directly to the
   unchanged canonical state file. Do not shard them for symmetry. Its gzip alternative
   is only a transport representation of the same bytes, not another scientific state.
5. `manifest.optional_metadata` supplies canonical sources, baselines and designs, with
   optional gzip transport. A ten-party comparison needs the existing baseline and design
   context; LOO region names are in sources. These are small and need no pipeline access.
6. Marginal controls in catalogs are not a Cartesian product. Never synthesize a missing
   route/state or interpolate a result. Disable unsupported controls with the unchanged
   availability policy. Any reset must be explicit and visible, with no silent fallback.

## Values and lazy exact resources

Ordinary views use already prepared display/chart fields, native/full coverage and support.
Runtime state records are structurally identical to canonical records, including diagnostics
and undefined markers. Nothing is rounded again, calculated or interpreted here.

On explicit exact-data request, resolve `state.result.exact_file` against the CANONICAL
root and verify `exact_file_sha256`. This fetches one existing gzip resource; runtime does
not copy, decompress, re-encode or enumerate the 1,620 exact resources. The full exact
inventory remains in the accepted canonical manifest for optional reproducibility audit.
Pooled numerator/denominator strings stay strings. Integer pool indices can locate strings;
they do not authorize numeric conversion of the strings. No parseInt, Number conversion,
float conversion or BigInt arithmetic is needed for exact values. No browser-side model
reconstruction is required. Only bounded prepared DISPLAY decimals may be converted to
chart coordinates; they remain presentation values, never replacements for exact values.

## Compression and integrity

Every normal JSON delivery resource offers raw and `.json.gz` alternatives. Choose ONE.
Explicit gzip files are reproducible binary transports (mtime=0), to fetch as bytes,
verify the compressed hash when supplied, decompress once and parse JSON. Hosting must
not label these `.gz` URLs with an additional Content-Encoding:gzip layer. If a host serves
ordinary `.json` with automatic compression, that is a separate hosting behavior: the raw
JSON hash still refers to decoded bytes. This repository does not guarantee CDN compression.
Raw sizes and explicit generated-gzip sizes are reported separately, never as assumed wire
savings. `manifest.json.gz` expands exactly to the bootstrap manifest; its integrity hash
is recorded outside the self-referential manifest, in the engineering evidence inventory.

## Semantics and coverage

Always render `catalog_entry.interpretation_guards`, per-state guards and result_type.
Ten-party conditional scenarios, focal-party D, scenario focal-valid share, signed excess /
observed focal, 1D component center and 2D center/membership are distinct. Cedar is not a
party share; 1D is not a national counterfactual share; 2D membership is not honesty/fraud
probability. D undefined is not zero. Reference windows and anchors are specification
sensitivity, not confidence intervals. LOO is influence, not a bad-region label. Sources
are not correctness rankings; native universes differ and must not be silently intersected.
Do not average unlike estimands or display an implied truth scale. All reference/support
counts and reportability diagnostics remain in the unchanged records. Show them alongside
results as required by the canonical contract. Editorial copy remains pending where marked.

## Generation, checking and the accepted older tools

`/usr/bin/python3 -m src.publication_sites.runtime_generate`
`/usr/bin/python3 -m src.publication_sites.runtime_check`
`/usr/bin/python3 -m src.publication_sites.runtime_measure`

The accepted original generator/checker uses a closed recursive inventory and predates this
explicitly authorized additive subtree. Its code/bindings are retained unchanged. Do not
run its generation over the delivery tree. The runtime checker verifies all 1,640 accepted
files by their original hashes, permits only this separately inventoried subtree, then checks
the complete delivery graph. It does not rerun the scientific/publication extraction pipeline.
No framework, backend, scientific dependency change or UI is introduced.
'''

README = '''# Static runtime delivery

Start with manifest.json and methods.json; read CONTRACT.md before implementing a client.
Select only listed routes/states. A/B/C uses source + design shards; D uses source + frozen
specification shards. Four other methods use unchanged canonical files. Exact downloads
are explicit and lazy. No UI, scientific arithmetic or model execution is present here.
'''


def runtime_schema():
    resource = {'type': 'object', 'required': ['path', 'sha256', 'gzip_path'],
                'properties': {'path': {'type': 'string'}, 'sha256': {'type': 'string', 'pattern': '^[a-f0-9]{64}$'},
                               'gzip_path': {'type': 'string'}}, 'additionalProperties': False}
    return {'$schema': 'https://json-schema.org/draft/2020-12/schema',
            '$defs': {'resource': resource}, 'type': 'object',
            'required': ['runtime_version', 'canonical_publication', 'methods_file', 'files', 'state_counts', 'numeric_policy'],
            'properties': {'runtime_version': {'const': '1'},
                'canonical_publication': {'type': 'object', 'required': ['root', 'manifest', 'sha256'],
                    'properties': {'root': {'const': '../'}, 'manifest': {'const': '../manifest.json'}, 'sha256': {'const': CANONICAL_SHA}}},
                'methods_file': {'$ref': '#/$defs/resource'}, 'files': {'type': 'object'},
                'state_counts': {'const': COUNTS}, 'public_state_count': {'const': 2064},
                'internal_state_count': {'const': 0}, 'card_only_count': {'const': 2},
                'numeric_policy': {'const': NUMERIC_POLICY}}}


def construct():
    m, _ = canonical_inventory()
    catalog, tables = canonical_tables()
    files, gzip_origins = {}, {}

    def add_json(name, value):
        blob = encode(value)
        files[name] = blob
        files[name + '.gz'] = zipped(blob)
        gzip_origins[name + '.gz'] = name
        return {'path': name, 'sha256': digest(blob), 'gzip_path': name + '.gz'}

    def canonical_resource(name):
        blob = (CANONICAL / name).read_bytes()
        compressed = 'compressed/' + name + '.gz'
        files[compressed] = zipped(blob)
        gzip_origins[compressed] = '../' + name
        return {'path': '../' + name, 'sha256': m['files'][name]['sha256'], 'gzip_path': compressed}

    methods = []
    for method in catalog['methods']:
        name = method['method_id']
        wrapper = {'method_id': name, 'catalog_entry': method, 'delivery': None}
        if method['execution_status'] == 'executable':
            default_ids = method['predeclared_default_states']
            if name in ('abc', 'd'):
                groups = {}
                for state in tables[name]['states']:
                    axis = 'design_id' if name == 'abc' else 'specification'
                    key = (state['source_version'], state['controls'][axis])
                    groups.setdefault(key, []).append(state)
                routes, default_routes = [], {}
                for (source, choice), states in sorted(groups.items()):
                    need(all(s['geography']['mode'] == 'DEFAULT' for s in states), 'unexpected shard geography')
                    states = sorted(states, key=lambda s: s['state_id'])
                    resource = add_json(f'states/{name}/{source}/{choice}.json', {
                        'runtime_version': '1', 'method_id': name, 'canonical_state_file': '../' + method['state_file'],
                        'availability': 'ONLY_LISTED_STATES_AVAILABLE', 'state_count': len(states), 'states': states})
                    route = {'key': {'source_version': source, axis: choice},
                             'state_ids': [s['state_id'] for s in states], 'resource': resource}
                    routes.append(route)
                    for label, state_id in default_ids.items():
                        if state_id in route['state_ids']:
                            default_routes[label] = {'state_id': state_id, 'key': route['key'], 'resource': resource}
                index = add_json(f'states/{name}/index.json', {
                    'runtime_version': '1', 'method_id': name, 'state_count': COUNTS[name],
                    'routing_axes': ['source_version', axis], 'routes': routes,
                    'default_routes': default_routes, 'availability': 'ONLY_LISTED_ROUTES_AND_STATES_AVAILABLE'})
                wrapper['delivery'] = {'mode': 'EXPLICIT_SHARDS', 'index': index, 'default_routes': default_routes,
                                       'canonical_state_file': '../' + method['state_file']}
            else:
                wrapper['delivery'] = {'mode': 'CANONICAL_FILE', 'resource': canonical_resource(method['state_file']),
                                       'default_states': default_ids}
        methods.append(wrapper)
    methods_file = add_json('methods.json', {
        'runtime_version': '1', 'project_id': catalog['project_id'],
        'catalog_entry_paths_base': 'CANONICAL_PUBLICATION_ROOT', 'methods': methods})
    optional = {name[:-5]: canonical_resource(name)
                for name in ('sources.json', 'baselines.json', 'designs.json')}
    add_json('schemas/runtime.schema.json', runtime_schema())
    files['README.md'] = README.encode()
    files['CONTRACT.md'] = CONTRACT.encode()
    manifest = {
        'runtime_version': '1', 'api_role': 'ADDITIVE_DELIVERY_PROJECTION', 'project_id': 'election-2026',
        'canonical_publication': {'root': '../', 'manifest': '../manifest.json', 'sha256': CANONICAL_SHA},
        'methods_file': methods_file, 'optional_metadata': optional,
        'load_first': ['methods.json'], 'state_counts': COUNTS, 'public_state_count': 2064,
        'internal_state_count': 0, 'card_only_count': 2, 'numeric_policy': NUMERIC_POLICY,
        'availability': 'EXPLICIT_ROUTES_THEN_EXPLICIT_STATES_NO_CARTESIAN_INFERENCE',
        'lazy_exact': {'enumerated_in_bootstrap': False, 'copied_into_runtime': False,
                       'reference': 'SELECTED_STATE.result.exact_file_RELATIVE_TO_CANONICAL_ROOT',
                       'full_integrity_catalog': '../manifest.json'},
        'compression_policy': {'gzip_files': 'EXPLICIT_BINARY_ALTERNATIVES_DECOMPRESS_ONCE',
                               'host_automatic_compression_guaranteed': False,
                               'bootstrap_gzip': 'manifest.json.gz', 'gzip_level': 6, 'gzip_mtime': 0},
        'generator': {'command': '/usr/bin/python3 -m src.publication_sites.runtime_generate',
                      'source_files': {path: sha(ROOT / path) for path in CODE_FILES},
                      'environment': {'python': sys.version.split()[0], 'zlib': zlib.ZLIB_RUNTIME_VERSION},
                      'new_model_calls': 0, 'new_fits': 0, 'new_scientific_states': 0},
        'files': {name: {'sha256': digest(blob), 'bytes': len(blob),
                         'encoding': 'GZIP_BYTES' if name.endswith('.gz') else 'UTF8',
                         **({'gzip_of': gzip_origins[name]} if name in gzip_origins else {})}
                  for name, blob in sorted(files.items())},
    }
    files['manifest.json'] = encode(manifest)
    files['manifest.json.gz'] = zipped(files['manifest.json'])
    return files


def generate():
    files = construct()
    existing = set(inventory()) if RUNTIME.exists() else set()
    need(existing <= set(files), 'unexpected existing runtime file; no silent deletion')
    for name, blob in sorted(files.items()):
        path = RUNTIME / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)
    print(json.dumps({'status': 'GENERATED', 'files': len(files),
                      'runtime_manifest_sha256': digest(files['manifest.json']),
                      'canonical_manifest_sha256': CANONICAL_SHA,
                      'public_states': 2064, 'new_model_calls': 0, 'new_fits': 0}))


if __name__ == '__main__':
    generate()
