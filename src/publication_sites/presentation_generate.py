"""Presentation only: frozen counts/parameters, stdlib; never imports an estimator."""
import collections
import csv
import gzip
import hashlib
import json
import math
import sys
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / 'publication/sites/v1'
OUT = ROOT / 'publication/sites/presentation/20261005_v1'
REPORT = ROOT / 'outputs/sites_presentation_data/20261005_v1'
PROFILE = ROOT / 'outputs/smz_real_party_adapter/20260929_v1/frozen_source_profile.json'
META = ROOT / 'outputs/smz_v2_external_freeze/20261002_v2/membership_metadata.csv.gz'
CANONICAL_SHA = '38d8f0eaa79952b4036d7e23c04ff40cca65f51e40f5cbbcddc88efd92fc3d16'
RUNTIME_SHA = '3998d58ec33c4bb8d28b6a35abdb5d2d2d28772a7aaea20b7fbd61afd598131c'
PROFILE_SHA = '78385131591910684ebfa3115f27159d4e78be76b5690fdcebc7c72500a84aa3'
META_SHA = '975c3075c40e83f5eedb133529c15ec2ece324d027d2fabc3d0d4b35859e7665'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(',', ':'), allow_nan=False) + '\n').encode()


def need(ok, why):
    if not ok:
        raise ValueError('PRESENTATION_BLOCKER: ' + why)


def pin(path, expected=None):
    path = Path(path)
    actual = sha(path)
    need(expected is None or actual == expected, 'hash ' + str(path))
    return {'path': str(path.relative_to(ROOT)), 'sha256': actual}


def number(value):
    if isinstance(value, dict):
        if 'float_hex' in value:
            return float.fromhex(value['float_hex'])
        if 'exact' in value:
            return Fraction(value['exact'])
    return value


def rational(value):
    q = Fraction(value)
    return {'exact': str(q), 'display_number': float(q)}


def guard(frame, event, arg):
    if event == 'call':
        module = frame.f_globals.get('__name__', '')
        need(not module.startswith(('scipy', 'sklearn', 'numpy', 'src.smz', 'src.analysis', 'src.data')),
             'scientific/adapter call forbidden: ' + module)


def primary_counts():
    """Read exactly pinned primary selectors, no scientific provider/kernel."""
    pins = [pin(PROFILE, PROFILE_SHA), pin(META, META_SHA)]
    profile = read(PROFILE)
    variant = profile['variants']['primary']
    mapping = ROOT / variant['mapping_path']
    pins.append(pin(mapping, variant['mapping_sha256']))
    with mapping.open(encoding='utf-8-sig', newline='') as f:
        selectors = {z['uuid']: z[variant['mapping_source_column']] for z in csv.DictReader(f)}
    need(len(selectors) == variant['expected_rows'] == 87736, 'primary membership')
    with gzip.open(META, 'rt', newline='') as f:
        metadata = {z['uuid']: z for z in csv.DictReader(f) if z['source'] == 'primary'}
    need(set(metadata) == set(selectors), 'primary metadata membership')
    by_path = collections.defaultdict(set)
    for uid, path in selectors.items():
        by_path[path].add(uid)
    counts = {}
    scanned = []
    def integer(s):
        n = Decimal(s)
        need(n.is_finite() and n == n.to_integral_value() and n >= 0, 'integer count')
        return int(n)
    for name in sorted(by_path):
        path = ROOT / name
        pins.append(pin(path, profile['source_files'][name]['sha256']))
        raw_rows = 0
        with gzip.open(path, 'rt', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            need(reader.fieldnames == profile['source_files'][name]['header'], 'source header')
            for z in reader:
                raw_rows += 1
                uid = z['uuid']
                if uid not in by_path[name]:
                    continue
                need(uid not in counts, 'duplicate selected UUID')
                n, issued, valid = [integer(z[k]) for k in ['voters', 'issued', 'valid']]
                parties = [integer(z[k]) for k in profile['party_source_columns']]
                invalid = None if z['invalid'] in profile['invalid_missing_tokens'] else integer(z['invalid'])
                need(sum(parties) == valid and 0 < valid <= issued <= n, 'complete frozen vector')
                m = metadata[uid]
                need([n, issued, valid] == [int(m[k]) for k in ['voters', 'issued', 'valid']], 'metadata counts')
                need((invalid is None) == (m['invalid_status'] == 'UNKNOWN'), 'invalid status')
                need(invalid is None or invalid == int(m['known_invalid']), 'known invalid count')
                counts[uid] = (n, issued, valid, invalid, parties[1], m['eligible_CEDAR'] == '1')
        scanned.append({'path': name, 'rows_scanned': raw_rows, 'selected_rows': len(by_path[name]),
                        'unselected_superset_rows': raw_rows - len(by_path[name])})
    need(set(counts) == set(selectors), 'missing primary source row')
    rows = [counts[u] for u in sorted(counts)]
    need(sum(z[0] for z in rows) == 99360758 and sum(z[2] for z in rows) == 54723201, 'primary totals')
    return rows, pins, scanned


def tables():
    return {name: read(PUBLIC / ('states/' + name + '.json'))['states']
            for name in ['vazhnye_istorii', 'cedar', 'novaya_1d', 'novaya_2d']}


def default(states):
    return next(s for s in states if s['state_id'].endswith('__primary__DEFAULT__B'))


def packet(state):
    p = state['provenance']['stored_packet']
    path = ROOT / p['path']
    pin(path, p['sha256'])
    return read(path)['result']


def metadata(chart_id, method, state_ids, purpose, coordinate, resolution, weighting):
    return {'chart_id': chart_id, 'method_id': method, 'source_state_ids': state_ids,
            'source_version': 'primary', 'geography': 'DEFAULT',
            'purpose': purpose, 'coordinate_definitions': coordinate, 'resolution': resolution,
            'weighting_semantics': weighting, 'presentation_only': True,
            'allowed_interpretation': 'DESCRIPTIVE_VISUALIZATION_OF_FROZEN_DATA_AND_SPECIFICATIONS',
            'prohibited_interpretation': ['FRAUD_CLASSIFIER', 'HONESTY_PROBABILITY', 'TRUE_RESULT',
                                         'COMMON_TRUTH_SCALE', 'CONFIDENCE_INTERVAL'],
            'is_exact_historical_KSP_replication': False}


def component_curves(parameters, xs):
    return [[a * math.exp(-(x - mu) ** 2 / (2 * sigma ** 2)) for x in xs]
            for mu, sigma, a in parameters]


def construct():
    pin(PUBLIC / 'manifest.json', CANONICAL_SHA)
    pin(PUBLIC / 'runtime/manifest.json', RUNTIME_SHA)
    rows, pins, scanned = primary_counts()
    groups = tables()
    for name in groups:
        pins.append(pin(PUBLIC / ('states/' + name + '.json')))
    defaults = {name: default(states) for name, states in groups.items()}
    packets = {name: packet(s) for name, s in defaults.items()}
    for s in defaults.values():
        pins.append(dict(s['provenance']['stored_packet']))
    pins = [{k: p[k] for k in ('path', 'sha256')} for p in pins]
    bins_i = [[0, 0, 0] for _ in range(100)]
    bins_c = [[0, 0, 0] for _ in range(100)]
    mass = [0] * 100
    grid = collections.defaultdict(lambda: [0, 0, 0])
    for n, issued, valid, invalid, L, cedar_eligible in rows:
        bx, by = min(199, 200 * issued // n), min(199, 200 * L // valid)
        cell = grid[bx, by]
        cell[0] += 1; cell[1] += n; cell[2] += valid
        b = min(99, 100 * issued // n)
        bins_i[b][0] += 1; bins_i[b][1] += L; bins_i[b][2] += valid - L
        mass[min(99, 100 * L // valid)] += L
        if cedar_eligible:
            need(n > 100 and invalid is not None and 0 < valid + invalid <= n, 'Cedar native scope')
            b = (100 * (valid + invalid) - 1) // n
            bins_c[b][0] += 1; bins_c[b][1] += L; bins_c[b][2] += valid + invalid - L
    cells = [[x, y, *values] for (x, y), values in sorted(grid.items())]
    coords = {'x': 'issued ballots / registered voters', 'y': 'focal-party votes / valid votes'}
    resolution = {'step_ratio': '1/200', 'step_percentage_points': 0.5,
                  'bin_rule': 'LEFT_CLOSED_RIGHT_OPEN; endpoint 1 included in final bin',
                  'bins_per_axis': 200, 'origin': 0}
    density = {'columns': ['x_bin', 'y_bin', 'uik_count', 'registered_voters_sum', 'valid_votes_sum'],
               'cells': cells, 'totals': {'uik_count': len(rows), 'registered_voters_sum': sum(z[0] for z in rows),
                                         'valid_votes_sum': sum(z[2] for z in rows)}}
    artifacts = {}
    def add(filename, meta, data):
        artifacts[filename] = {'metadata': meta, **data}
    add('context_turnout_result_density.json', metadata('context_turnout_result_density', 'context', [],
        'Primary paper coordinate geometry; equal UIK count with separate volume sums', coords, resolution,
        'UIK_COUNT; REGISTERED_AND_VALID_SUMS_ARE_SEPARATE_CHANNELS'),
        {'universe': 'paper_primary__evidence_20260927', 'grid': density})

    ist = packets['vazhnye_istorii']
    alpha = number(ist['alpha'])
    ibins = []
    for b, (N, L, O) in enumerate(bins_i):
        expected = alpha * O; residual = L - expected
        need(residual == number(ist['residual_bins'].get(str(b), {'exact': '0'})), 'stored iStories residual bin')
        ibins.append({'bin_index': b, 'lower_percent': b, 'upper_percent': b + 1,
                      'uik_count': N, 'observed_L': L, 'observed_O': O,
                      'expected_L': rational(expected), 'signed_residual': rational(residual),
                      'in_default_reference': 20 <= b < 30})
    windows = [s for s in groups['vazhnye_istorii'] if s['source_version'] == 'primary'
               and s['geography']['mode'] == 'DEFAULT']
    need(len(windows) == 15, '15 public reference windows')
    window_series = []
    for s in sorted(windows, key=lambda s: tuple(s['controls']['reference_window_percent'])):
        lo, hi = s['controls']['reference_window_percent']
        window_series.append({'state_id': s['state_id'], 'window_percent': [lo, hi],
            'alpha_exact_stored': s['result']['exact_stored']['alpha'],
            'reference_UIKs': s['support']['reference_UIKs'],
            'expected_L_display': [float(number(s['result']['exact_stored']['alpha']) * O) for _, _, O in bins_i],
            'scenario_result_exact_stored': s['result']['exact_stored']['share']})
        need(sum(bins_i[b][0] for b in range(lo, hi)) == s['support']['reference_UIKs'], 'reference support')
    need(sum((number(b['signed_residual']) for b in ibins), Fraction()) == number(ist['E']), 'iStories E equality')
    add('istories_reference_curve.json', metadata('istories_reference_curve', 'vazhnye_istorii',
        [s['state_id'] for s in windows], 'Stored proportionality coefficient evaluated on frozen vote bins',
        {'x': coords['x'], 'L': 'focal valid votes', 'O': 'other nine valid party votes'},
        {'step_percentage_points': 1, 'bin_rule': 'LEFT_CLOSED_RIGHT_OPEN; 100% in last bin'}, 'PARTY_VOTE_MASS'),
        {'default_state_id': defaults['vazhnye_istorii']['state_id'], 'default_window_percent': [20, 30],
         'default_alpha_exact_stored': ist['alpha'], 'scenario_frame_UIKs': len(rows),
         'bins': ibins, 'windows': window_series, 'range_is_confidence_interval': False})

    c = packets['cedar']; ca = number(c['alpha']); cbins = []
    for b, (N, L, O) in enumerate(bins_c):
        cbins.append({'bin_index': b, 'interval': f'({b}%,{b+1}%]', 'right_edge_percent': b+1,
                      'uik_count': N, 'observed_L': L, 'observed_O': O,
                      'expected_L': rational(ca * O), 'signed_residual': rational(L - ca * O),
                      'selected_anchor': b == c['anchor']})
    E = sum((number(b['signed_residual']) for b in cbins), Fraction())
    total_L = sum(b[1] for b in bins_c)
    need(E == number(c['E']) and E / total_L == number(c['main']), 'Cedar exact aggregate reproduction')
    need(sum(b[0] for b in bins_c) == c['input_coverage']['eligible_UIKs'] == 71438, 'Cedar native total')
    support = defaults['cedar']['support']; anchor = bins_c[c['anchor']]
    need(anchor == [support['anchor_UIKs'], support['anchor_L'], support['anchor_O']], 'Cedar anchor support')
    add('cedar_default_curve.json', metadata('cedar_default_curve', 'cedar', [defaults['cedar']['state_id']],
        'Frozen selected anchor coefficient on native observed bins; signed residual, not party share',
        {'x': '(valid + known invalid) / registered voters', 'L': 'focal valid votes',
         'O': 'cast minus focal, includes known invalid'}, {'step_percentage_points': 1,
         'bin_rule': 'RIGHT_CLOSED; (j%,(j+1)%]'}, 'CAST_AND_FOCAL_VOLUME'),
        {'bins': cbins, 'alpha_exact_stored': c['alpha'], 'anchor_bin_index': c['anchor'],
         'anchor_interval': support['anchor_interval'], 'eligible_UIKs': 71438,
         'outside_native_scope_UIKs': 16298, 'stored_E': c['E'], 'stored_E_over_L': c['main'],
         'aggregate_reproduction': {'status': 'PASS', 'arithmetic': 'EXACT_RATIONAL', 'tolerance': 0}})
    anchors = [s for s in groups['cedar'] if s['source_version'] == 'primary' and s['geography']['mode'] == 'DEFAULT']
    need(len(anchors) == 74, '71 fixed plus 3 AUTO/relative states')
    add('cedar_anchor_sensitivity.json', metadata('cedar_anchor_sensitivity', 'cedar',
        [s['state_id'] for s in anchors], 'Frozen fixed-anchor stress test with stored support',
        {'x': 'anchor bin right edge percent', 'y': 'SIGNED_EXCESS_OVER_OBSERVED_FOCAL'},
        {'fixed_right_edges_percent': list(range(10, 81))}, 'NATIVE_CEDAR_FRAME'),
        {'points': [{'state_id': s['state_id'], 'selection_type': s['support']['anchor_selection_type'],
                     'anchor_bin_index': s['support']['anchor_bin_index'],
                     'anchor_right_edge_percent': s['support']['anchor_right_edge_percent'],
                     'anchor_interval': s['support']['anchor_interval'],
                     'anchor_UIKs': s['support']['anchor_UIKs'], 'anchor_L': s['support']['anchor_L'],
                     'anchor_O': s['support']['anchor_O'],
                     'result_exact_stored': s['result']['exact_stored']['main'],
                     'display_percent': s['result']['display']['main_percent']} for s in
                    sorted(anchors, key=lambda s: (s['support']['anchor_right_edge_percent'], s['state_id']))],
         'is_confidence_interval': False})

    p1 = packets['novaya_1d']; parameters = [[number(x) for x in row] for row in p1['parameters']]
    xs = [(b + .5) / 100 for b in range(100)]
    normalized = [m / max(mass) for m in mass]
    components = component_curves(parameters, xs)
    total = [math.fsum(row[j] for row in components) for j in range(100)]
    sse = math.fsum((a-b)**2 for a, b in zip(total, normalized))
    need(abs(sse - number(p1['selected_sse'])) <= 1e-10, 'frozen 1D SSE reproduction')
    plot_x = [j / 500 for j in range(501)]
    plot_components = component_curves(parameters, plot_x)
    add('novaya_1d_default_fit.json', metadata('novaya_1d_default_fit', 'novaya_1d',
        [defaults['novaya_1d']['state_id']], 'Evaluate three stored positive Gaussian curves, without fitting',
        {'x': 'focal-party votes / valid votes', 'y': 'FOCAL_PARTY_VOTE_MASS / common max histogram height'},
        {'histogram_step_percentage_points': 1, 'plot_step_percentage_points': 0.2,
         'histogram_bin_rule': 'LEFT_CLOSED_RIGHT_OPEN; x=1 in final bin'}, 'FOCAL_PARTY_VOTE_MASS'),
        {'parameter_order': ['mean', 'sigma', 'amplitude_normalized'], 'parameters_exact_stored': p1['parameters'],
         'parameters_display': parameters, 'selected_component_index': 0, 'selection_rule': 'FROZEN_ASCENDING_MEAN',
         'core_center_exact_stored': p1['core_center'], 'mass_scale': max(mass),
         'histogram': {'x_midpoints': xs, 'mass': mass, 'normalized_height': normalized,
                       'component_curves': components, 'total_fitted_curve': total},
         'plot': {'x': plot_x, 'component_curves': plot_components,
                  'total_fitted_curve': [math.fsum(row[j] for row in plot_components) for j in range(501)]},
         'reproduction': {'status': 'PASS', 'component_sum_absolute_tolerance': 1e-12,
                          'stored_total_curve_available': False, 'stored_sse': p1['selected_sse'],
                          'derived_sse': sse, 'sse_absolute_tolerance': 1e-10},
         'K': 3, 'sigma_min': 0.005, 'is_national_counterfactual_share': False})

    p2 = packets['novaya_2d']
    add('novaya_2d_default_density.json', metadata('novaya_2d_default_density', 'novaya_2d',
        [defaults['novaya_2d']['state_id']], 'Frozen feature geometry and stored mixture parameters',
        coords, resolution, 'ONE_UIK_ONE_OBSERVATION; VOTER_SUM_SEPARATE_FROM_FIT_WEIGHT'),
        {'grid': density, 'means_exact_stored': p2['means'], 'covariances_exact_stored': p2['covariances'],
         'weights_exact_stored': p2['weights'], 'means_display': [[number(x) for x in r] for r in p2['means']],
         'covariances_display': [[[number(x) for x in r] for r in c] for c in p2['covariances']],
         'weights_display': [number(x) for x in p2['weights']], 'core_component_index': p2['core_index'],
         'core_center_exact_stored': p2['core_center'], 'covariance_type': p2['covariance_type'],
         'reg_covar': 1e-6, 'membership_aggregate_exact_stored': p2['threshold_output'],
         'membership_grid_status': 'UNAVAILABLE_NOT_STORED',
         'membership_grid_reason': 'Per-UIK posterior and member indices removed by committed export compaction; no predict_proba/inference rerun permitted.',
         'membership_probability_semantics': 'MODEL_COMPONENT_MEMBERSHIP_NOT_HONESTY_OR_FRAUD'})
    return artifacts, pins, scanned


def schema():
    return {'$schema': 'https://json-schema.org/draft/2020-12/schema', 'type': 'object',
            'required': ['metadata'], 'properties': {'metadata': {'type': 'object',
            'required': ['chart_id', 'method_id', 'source_state_ids', 'source_version', 'coordinate_definitions',
                         'weighting_semantics', 'resolution', 'presentation_only', 'prohibited_interpretation'],
            'properties': {'source_version': {'const': 'primary'}, 'geography': {'const': 'DEFAULT'},
                           'presentation_only': {'const': True},
                           'method_id': {'enum': ['context', 'cedar', 'vazhnye_istorii', 'novaya_1d', 'novaya_2d']},
                           'source_state_ids': {'type': 'array', 'uniqueItems': True, 'items': {'type': 'string'}}}},
            'grid': {'type': 'object', 'required': ['columns', 'cells', 'totals'], 'properties': {
                'cells': {'type': 'array', 'maxItems': 40000, 'items': {'type': 'array', 'minItems': 5,
                    'maxItems': 5, 'items': {'type': 'integer', 'minimum': 0}}}}}}}


def generate():
    sys.setprofile(guard)
    try:
        artifacts, pins, scanned = construct()
        OUT.mkdir(parents=True, exist_ok=True)
        for name, value in artifacts.items():
            (OUT / name).write_bytes(encode(value))
        (OUT / 'chart.schema.json').write_bytes(encode(schema()))
        (OUT / 'README.md').write_text('''# Static chart presentation data

Load manifest.json, then only the selected chart file. Coordinates are ratios; bin indices
refer to documented origin/step. Sparse grid rows follow the columns array, never raw UIK rows.
Counts/volume channels are separate; vote/voter sums do not redefine model fit weights.
Exact rationals stay strings and frozen binary64 values retain float_hex. Prepared display
numbers and curves are for rendering; no browser model reconstruction is required.
Source state IDs use public publication aliases; opaque local paths are technical provenance.
The public repository does not yet include all frozen input files needed for regeneration.

All charts are deterministic presentation projections, not new states or inference. No
fraud classification, truth interval or averaging across unlike result types is allowed.
1D fitted curves are evaluated from stored parameters; stored SSE provides an independent
reproduction check because a pre-evaluated total curve was not persisted. 2D per-cell membership
is unavailable: neither posteriors nor member indices survived immutable export. The stored
aggregate membership is retained; a missing cell field must never be rendered as zero.

A/B/C and D use existing ../../v1/runtime data; no new chart results are introduced here.
Generate locally: python3 -m src.publication_sites.presentation_generate
Validate locally or in public checkout: python3 -m src.publication_sites.presentation_check
Do not run generation in deployment CI. Deploy accepted static bytes only.
''')
        files = {p.name: {'sha256': sha(p), 'bytes': p.stat().st_size} for p in sorted(OUT.iterdir())
                 if p.is_file() and p.name != 'manifest.json'}
        manifest = {'presentation_schema_version': '1', 'project_id': 'election-2026',
                    'canonical_manifest': {'path': '../../v1/manifest.json', 'sha256': CANONICAL_SHA},
                    'runtime_manifest': {'path': '../../v1/runtime/manifest.json', 'sha256': RUNTIME_SHA},
                    'files': files, 'charts': [{**value['metadata'], 'file': name, **files[name],
                        'source_artifacts': pins} for name, value in sorted(artifacts.items())],
                    'scientific_state_count_added': 0, 'fits_run': 0, 'model_calls': 0, 'optimizer_calls': 0,
                    'source_bindings': pins, 'primary_source_scan_accounting': scanned,
                    'existing_runtime_charts': {'abc': {'runtime_index': '../../v1/runtime/states/abc/index.json',
                        'display_delta': 'existing scenario share minus existing observed share'},
                        'd': {'runtime_index': '../../v1/runtime/states/d/index.json', 'new_dataset': False}},
                    'unavailable_fields': ['Novaya 2D per-cell membership/posterior; not persisted',
                                           'Novaya 1D pre-evaluated stored total curve; evaluated from frozen parameters'],
                    'generator_files': {str(p.relative_to(ROOT)): sha(p) for p in
                        [ROOT / 'src/publication_sites/presentation_generate.py', ROOT / 'src/publication_sites/presentation_check.py']}}
        (OUT / 'manifest.json').write_bytes(encode(manifest))
        print(json.dumps({'status': 'GENERATED', 'chart_files': len(artifacts),
                          'bytes': sum(p.stat().st_size for p in OUT.iterdir() if p.is_file()),
                          'model_calls': 0, 'fits': 0}))
    finally:
        sys.setprofile(None)


if __name__ == '__main__':
    generate()
