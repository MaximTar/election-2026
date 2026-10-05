"""Fail-closed validation of chart bytes, public-state scope and numeric reproduction."""
import ast
import json
import math
from fractions import Fraction
from pathlib import Path
from .presentation_generate import (ROOT, PUBLIC, OUT, REPORT, CANONICAL_SHA, RUNTIME_SHA,
                                    read, sha, need, number, tables, default, packet, component_curves)


def finite(value):
    if isinstance(value, float):
        need(math.isfinite(value), 'nonfinite chart number')
    elif isinstance(value, dict):
        for k, v in value.items():
            need(k not in ['uuid', 'UUID', 'member_indices', '_core_posterior'], 'raw row/membership dump')
            finite(v)
    elif isinstance(value, list):
        for v in value:
            finite(v)


def validate_schema(value, rule, location='$'):
    """Validate the explicit keywords used by chart.schema.json; no new dependency.

    Reject unknown validation keywords so extensions cannot silently go unchecked.
    """
    supported = {'$schema', 'type', 'required', 'properties', 'const', 'enum',
                 'items', 'maxItems', 'minItems', 'uniqueItems', 'minimum'}
    need(set(rule) <= supported, 'unsupported schema keyword ' + location)
    kind = rule.get('type')
    if kind:
        matches = {'object': isinstance(value, dict), 'array': isinstance(value, list),
                   'string': isinstance(value, str), 'integer': type(value) is int}
        need(kind in matches and matches[kind], 'schema type ' + location)
    if 'const' in rule:
        need(value == rule['const'], 'schema const ' + location)
    if 'enum' in rule:
        need(value in rule['enum'], 'schema enum ' + location)
    if isinstance(value, dict):
        need(set(rule.get('required', [])) <= set(value), 'schema required ' + location)
        for key, subrule in rule.get('properties', {}).items():
            if key in value:
                validate_schema(value[key], subrule, location + '.' + key)
    if isinstance(value, list):
        need(len(value) >= rule.get('minItems', 0) and len(value) <= rule.get('maxItems', len(value)), 'schema array size ' + location)
        if rule.get('uniqueItems'):
            need(len({json.dumps(v, sort_keys=True) for v in value}) == len(value), 'schema uniqueItems ' + location)
        if 'items' in rule:
            for j, v in enumerate(value):
                validate_schema(v, rule['items'], location + '[' + str(j) + ']')
    if 'minimum' in rule:
        need(value >= rule['minimum'], 'schema minimum ' + location)


def check():
    checks = {}
    manifest = read(OUT / 'manifest.json')
    for path, expected in manifest['generator_files'].items():
        need(sha(ROOT / path) == expected, 'presentation engineering binding ' + path)
    need(sha(PUBLIC / 'manifest.json') == CANONICAL_SHA, 'canonical manifest')
    need(sha(PUBLIC / 'runtime/manifest.json') == RUNTIME_SHA, 'runtime manifest')
    for base in [PUBLIC, PUBLIC / 'runtime']:
        for name, spec in read(base / 'manifest.json')['files'].items():
            p = base / name
            need(p.is_file() and sha(p) == spec['sha256'] and p.stat().st_size == spec['bytes'], 'accepted closure ' + name)
    checks['accepted_canonical_and_runtime_closure'] = 'PASS'
    names = {p.name for p in OUT.iterdir() if p.is_file()}
    need(names == set(manifest['files']) | {'manifest.json'}, 'presentation file inventory')
    for name, spec in manifest['files'].items():
        p = OUT / name
        need(p.is_file() and sha(p) == spec['sha256'] and p.stat().st_size == spec['bytes'], 'chart file hash ' + name)
    for spec in manifest['charts']:
        need({'sha256': spec['sha256'], 'bytes': spec['bytes']} == manifest['files'][spec['file']], 'chart manifest entry')
    checks['manifest_file_hash_closure'] = 'PASS'
    for key in ['scientific_state_count_added', 'fits_run', 'model_calls', 'optimizer_calls']:
        need(manifest[key] == 0, key)
    groups = tables()
    public_ids = {s['state_id'] for states in groups.values() for s in states}
    need(len(public_ids) == 444, 'public external visibility')
    charts = {c['chart_id']: read(OUT / c['file']) for c in manifest['charts']}
    schema = read(OUT / 'chart.schema.json')
    for spec in manifest['charts']:
        need(set(spec['source_state_ids']) <= public_ids, 'unauthorized state reference')
        need(not any('LS_B_WINDOW' in s for s in spec['source_state_ids']), 'INTERNAL state reference')
        need(spec['method_id'] not in ['novaya_conventional', 'novaya_overlap_core'], 'CARD_ONLY chart')
        chart = charts[spec['chart_id']]
        need(chart['metadata'] == {k: spec[k] for k in chart['metadata']}, 'chart/manifest metadata')
        validate_schema(chart, schema)
        finite(chart)
    checks['json_schema_public_scope_finite_arrays'] = 'PASS'
    context = charts['context_turnout_result_density']['grid']
    for name in ['context_turnout_result_density', 'novaya_2d_default_density']:
        grid = charts[name]['grid']; cells = grid['cells']
        need(len(cells) <= 40000 and len({tuple(c[:2]) for c in cells}) == len(cells), 'grid duplicate/bounds')
        need(all(0 <= c[0] < 200 and 0 <= c[1] < 200 and c[2] > 0 for c in cells), 'cell domain')
        need([sum(c[j] for c in cells) for j in [2, 3, 4]] == [87736, 99360758, 54723201], 'primary grid totals')
    need(charts['novaya_2d_default_density']['grid'] == context, 'same frozen coordinates/frame')
    checks['sparse_density_grid_uniqueness_and_totals'] = 'PASS'
    c = charts['cedar_default_curve']; bins = c['bins']; alpha = number(c['alpha_exact_stored'])
    need(len(bins) == 100 and [b['bin_index'] for b in bins] == list(range(100)), 'Cedar bins')
    for b in bins:
        need(number(b['expected_L']) == alpha * b['observed_O'], 'Cedar frozen alpha evaluation')
        need(number(b['signed_residual']) == b['observed_L'] - number(b['expected_L']), 'Cedar residual')
    E = sum((number(b['signed_residual']) for b in bins), Fraction())
    need(E == number(c['stored_E']) and E / sum(b['observed_L'] for b in bins) == number(c['stored_E_over_L']), 'Cedar aggregate')
    need(sum(b['uik_count'] for b in bins) == 71438, 'Cedar native frame')
    a = default(groups['cedar'])
    need(c['alpha_exact_stored'] == a['result']['exact_stored']['alpha'] and
         c['stored_E'] == a['result']['exact_stored']['E'] and
         c['stored_E_over_L'] == a['result']['exact_stored']['main'], 'Cedar unchanged source result')
    points = charts['cedar_anchor_sensitivity']['points']
    fixed = [p for p in points if p['selection_type'] == 'FIXED']
    need(len(points) == 74 and len(fixed) == 71 and {p['anchor_right_edge_percent'] for p in fixed} == set(range(10, 81)), 'frozen anchor grid')
    index = {s['state_id']: s for s in groups['cedar']}
    for p in points:
        s = index[p['state_id']]
        need(p['result_exact_stored'] == s['result']['exact_stored']['main'], 'anchor stored result')
        for field in ['anchor_UIKs', 'anchor_L', 'anchor_O', 'anchor_bin_index']:
            need(p[field] == s['support'][field], 'anchor support')
    checks['Cedar_exact_rational_reproduction_and_unchanged_support'] = 'PASS'
    i = charts['istories_reference_curve']; ibins = i['bins']
    alpha = number(i['default_alpha_exact_stored'])
    for b in ibins:
        need(number(b['expected_L']) == alpha * b['observed_O'] and
             number(b['signed_residual']) == b['observed_L'] - alpha * b['observed_O'], 'iStories frozen curve')
    a = default(groups['vazhnye_istorii'])
    need(sum((number(b['signed_residual']) for b in ibins), Fraction()) == number(a['result']['exact_stored']['E']), 'iStories aggregate')
    need(len(i['windows']) == 15, 'window grid')
    index = {s['state_id']: s for s in groups['vazhnye_istorii']}
    for w in i['windows']:
        s = index[w['state_id']]; lo, hi = w['window_percent']
        need(w['alpha_exact_stored'] == s['result']['exact_stored']['alpha'] and
             w['scenario_result_exact_stored'] == s['result']['exact_stored']['share'], 'stored window fields')
        need(w['reference_UIKs'] == sum(b['uik_count'] for b in ibins[lo:hi]), 'window support')
    checks['iStories_stored_coefficients_residuals_and_15_windows'] = 'PASS'
    n1 = charts['novaya_1d_default_fit']
    need(n1['selected_component_index'] == 0 and n1['K'] == 3, '1D unchanged selected component')
    need(n1['parameters_display'][0][0] == number(n1['core_center_exact_stored']), '1D stored center')
    for curve in [n1['histogram'], n1['plot']]:
        xs = curve.get('x', curve.get('x_midpoints'))
        components = component_curves(n1['parameters_display'], xs)
        need(components == curve['component_curves'], 'frozen Gaussian evaluation')
        need(all(abs(math.fsum(p[j] for p in components) - y) <= 1e-12
                 for j, y in enumerate(curve['total_fitted_curve'])), '1D component sum')
    h = n1['histogram']
    sse = math.fsum((a-b)**2 for a, b in zip(h['total_fitted_curve'], h['normalized_height']))
    need(abs(sse - number(n1['reproduction']['stored_sse'])) <= 1e-10, 'stored SSE reproduction')
    checks['1D_curve_component_sum_and_stored_SSE'] = 'PASS'
    n2 = charts['novaya_2d_default_density']; a = default(groups['novaya_2d'])
    need(n2['core_center_exact_stored'] == a['result']['exact_stored']['core_center'], '2D stored center')
    need(n2['means_exact_stored'][n2['core_component_index']] == n2['core_center_exact_stored'], '2D core slot')
    need(n2['membership_grid_status'] == 'UNAVAILABLE_NOT_STORED', 'no invented posterior grid')
    need(n2['membership_aggregate_exact_stored'] == a['result']['exact_stored']['threshold_output'], 'stored membership')
    checks['2D_frozen_centers_and_membership_no_inference'] = 'PASS'
    # Source packets are local provenance, intentionally not required in partial public checkout.
    local = all((ROOT / p['path']).exists() for p in manifest['source_bindings'])
    if local:
        for p in manifest['source_bindings']:
            need(sha(ROOT / p['path']) == p['sha256'], 'local provenance hash')
        p1, p2 = packet(default(groups['novaya_1d'])), packet(default(groups['novaya_2d']))
        need(n1['parameters_exact_stored'] == p1['parameters'], 'frozen 1D parameters')
        for field, original in [('means_exact_stored', 'means'), ('covariances_exact_stored', 'covariances'), ('weights_exact_stored', 'weights')]:
            need(n2[field] == p2[original], 'frozen 2D parameters ' + field)
    checks['local_authoritative_parameter_bindings'] = 'PASS' if local else 'NOT_AVAILABLE_IN_PARTIAL_PUBLIC_CHECKOUT'
    before = REPORT / 'protected_before.json'
    if before.exists():
        for path, digest in read(before).items():
            need(sha(ROOT / path) == digest, 'protected bytes changed ' + path)
        checks['frozen_runs_reveal_article_publication_unchanged'] = 'PASS'
    # Only stdlib imports in generator; runtime profile rejects scientific/adapter calls.
    tree = ast.parse((ROOT / 'src/publication_sites/presentation_generate.py').read_text())
    allowed = {'collections', 'csv', 'gzip', 'hashlib', 'json', 'math', 'sys', 'decimal', 'fractions', 'pathlib'}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            need(all(n.name in allowed for n in node.names), 'generator non-stdlib import')
        if isinstance(node, ast.ImportFrom):
            need(node.module in allowed, 'generator non-stdlib import')
    checks['stdlib_only_reader_no_scientific_imports'] = 'PASS'
    size = sum(p.stat().st_size for p in OUT.iterdir() if p.is_file())
    need(size < 5 * 1024 * 1024, 'presentation exceeds hard browser target')
    return {'status': 'PASS', 'checks': checks, 'raw_bytes': size, 'charts': len(charts),
            'scientific_model_runs': 0, 'model_calls': 0, 'fits': 0, 'optimizer_calls': 0,
            'scientific_states_added': 0, 'real_source_rows_passed_through_kernels': 0}


if __name__ == '__main__':
    print(json.dumps(check(), sort_keys=True, indent=2))
