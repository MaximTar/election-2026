"""Independent, opt-in recomputation of the EXISTING frozen grids.

This command is never used by release verification. It does not resume historical
transactions, consume their authorizations, or write to their directories. The
scientific functions are imported unchanged only after all input/code/environment
checks and creation of a fresh reproduction commitment. This engineering harness
has not been exercised on election data during release packaging.
"""
import argparse
import csv
import datetime
import importlib.metadata
import json
import os
import platform
import sys
from fractions import Fraction
from pathlib import Path
from .common import ROOT, RELEASE, read, sha, need, external_guard, write


def inputs(root, family):
    need(Path(root).resolve() == ROOT, 'run from the unpacked repository; external paths are fixed')
    external_guard(root, [family])
    manifest = read(RELEASE / 'manifest.json')
    for name, spec in manifest['files'].items():
        need((ROOT / name).is_file() and sha(ROOT / name) == spec['sha256'], 'RELEASE_INPUT_OR_CODE_CHANGED: ' + name)
    return manifest


def environment():
    expected = read(ROOT / 'outputs/smz_v2_external_qualification/20261002_v1/environment.json')
    need(platform.python_version() == expected['python'], 'Python version differs from frozen environment')
    for name, version in expected['versions'].items():
        need(importlib.metadata.version(name) == version, 'dependency version differs: ' + name)
    need(all(os.environ.get(k) == '1' for k in expected['thread_env']), 'single-thread variables required')
    # Versions are enforced. Original binary RECORD hashes remain evidence, not a
    # portable installation lock. Numeric agreement must be checked after a rerun.
    return {'python': platform.python_version(), 'versions': expected['versions'], 'binary_identity_guaranteed': False}


def decode(source, context):
    from src.smz_real_adapter import adapter, plans
    profile_path = ROOT / 'outputs/smz_real_party_adapter/20260929_v1/frozen_source_profile.json'
    profile = profile_path.read_bytes()
    plan = plans.compile_plan(profile, source, lambda p: (ROOT / p).read_bytes(), expected_profile_sha256=sha(profile_path))
    def provider(path, expected):
        need(sha(ROOT / path) == expected, 'source SHA changed before decode')
        return (ROOT / path).open('rb')
    return adapter._decode(plan, source, provider, run_id=context['run_id'], created_at=context['created_at'],
                           bundle_sha=sha(profile_path), origin='INDEPENDENT_REPRODUCTION_REAL_SOURCE')


def abcd(destination, context):
    from src.smz import common
    from src.smz_arch_b_verified import basis, codec, engine, native_d
    inventory = read(ROOT / 'outputs/smz_run01_reveal/20261001_v1/canonical_cell_inventory.json')
    records = []
    for source in ('primary', 'S1', 'S2a', 'S2b'):
        frame = decode(source, context)
        rows = tuple(common.Row(r.uuid, r.region, r.tik_uuid, r.voters, r.issued, r.valid, r.parties, r.known_invalid.value) for r in frame.rows)
        with engine._access(rows):
            for design in sorted({c['parameters']['spec'] for c in inventory['cells'] if c['parameters']['family'] == 'ABC'}):
                b = basis.build(rows, design); aggregates = basis.aggregate_basis(rows, b)
                for cell in inventory['cells']:
                    p = cell['parameters']
                    if p['family'] != 'ABC' or p['source'] != source or p['spec'] != design:
                        continue
                    lam, mu = Fraction(p['lambda_quarters'], 4), Fraction(p['mu_quarters'], 4)
                    result = dict(engine='ABC', source_id=source, design_id=design, lambda_=lam, mu=mu,
                                  status='APPLICABLE' if b['sparse'] else 'NOT_APPLICABLE_ON_THIS_DESIGN',
                                  scopes={k: basis.evaluate(v, lam, mu) for k, v in aggregates.items()})
                    path = destination / (cell['id'] + '.exact')
                    path.write_bytes(codec.pack(result)); records.append({'state_id': cell['id'], 'sha256': sha(path)})
            for cell in inventory['cells']:
                p = cell['parameters']
                if p['family'] != 'D' or p['source'] != source:
                    continue
                strata = destination / ('strata_' + source + '_' + p['spec']); strata.mkdir()
                def emit(name, value):
                    (strata / (name + '.exact')).write_bytes(codec.pack(value))
                result = native_d.run(rows, p['spec'], emit); result['source_id'] = source
                path = destination / (cell['id'] + '.exact')
                path.write_bytes(codec.pack(result)); records.append({'state_id': cell['id'], 'sha256': sha(path)})
    need(len(records) == 1620 and len({x['state_id'] for x in records}) == 1620, 'ABCD grid mismatch')
    return records


def external(destination, context):
    from src.smz_external_real import adapter, coordinator, kernel_loader, transport
    from src.smz_external_plus_a import arithmetic
    # Independent reproduction scope, explicitly separated from historical one-use
    # authorization. Reuse strict REAL input types and qualified numerical ASTs.
    need(transport._ACTIVE is None, 'fresh process required')
    transport._ACTIVE = {**context, 'committed_before_first_fit': True, 'access_log': []}
    modules = {f: kernel_loader.load(n) for f, n in [('ISTORIES', 'istories'), ('CEDAR', 'cedar'), ('NOVAYA_1D', 'gaussian1d'), ('NOVAYA_2D', 'gmm2d')]}
    with (ROOT / 'outputs/smz_v2_external_freeze/20261002_v2/state_index.csv').open(newline='') as f:
        states = list(csv.DictReader(f))
    with (ROOT / 'outputs/smz_v2_external_c_lite_plus_a_freeze/20261003_v1/state_index.csv').open(newline='') as f:
        supplement = list(csv.DictReader(f))
    frames, parents, records = {}, {}, []
    # The original CSV order binds fit reuse. Never sort states across parents.
    for state in states:
        source = state['source']
        if source not in frames:
            frames[source] = adapter.load(source)
        result = coordinator.execute_state(state, frames[source], modules, parents)
        coordinator.state_reconcile(state, frames[source], result, parents, modules)
        parents[state['state_id']] = result
        path = destination / (state['state_id'] + '.json')
        path.write_bytes(transport.canonical(coordinator.compact(result)) + b'\n')
        records.append({'state_id': state['state_id'], 'sha256': sha(path), 'visibility': state['visibility']})
    h = arithmetic.cedar_histogram(modules['CEDAR'], frames['primary'])
    for state in supplement:
        result = arithmetic.execute(state, frames['primary'], modules, h)
        arithmetic.reconcile(state, frames['primary'], result, h)
        path = destination / (state['state_id'] + '.json')
        path.write_bytes(transport.canonical(coordinator.compact(result)) + b'\n')
        records.append({'state_id': state['state_id'], 'sha256': sha(path), 'visibility': state['visibility']})
    need(len(records) == 445 and len({x['state_id'] for x in records}) == 445, 'external grid mismatch')
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--family', choices=['abcd', 'external'], required=True)
    parser.add_argument('--input-root', type=Path, default=ROOT)
    parser.add_argument('--check-inputs-only', action='store_true')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--execute', action='store_true', help='opt in to actual independent recomputation')
    args = parser.parse_args()
    inputs(args.input_root, args.family)  # Always first, before scientific imports.
    if args.check_inputs_only:
        print(json.dumps({'status': 'PASS', 'input_hashes_verified': True, 'model_calls': 0})); return
    need(args.execute and args.output is not None, 'explicit --execute and fresh --output required')
    destination = args.output.resolve()
    need(destination.parent == ROOT / 'reproduction_runs' and not destination.exists(), 'use a fresh reproduction_runs/<name> directory')
    env = environment()
    destination.parent.mkdir(exist_ok=True); destination.mkdir()
    context = {'run_id': 'independent-' + destination.name, 'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'family': args.family, 'release_manifest_sha256': sha(RELEASE / 'manifest.json'), 'environment': env,
               'historical_transactions_resumed': False}
    write(destination / 'reproduction_commitment.json', context)
    records = (abcd if args.family == 'abcd' else external)(destination, context)
    write(destination / 'reproduction_inventory.json', {'records': records, 'historical_outputs_modified': False})
    print(json.dumps({'status': 'RECOMPUTED_IN_SEPARATE_DIRECTORY', 'state_count': len(records),
                      'numeric_comparison_to_frozen_results_required': True}))


if __name__ == '__main__':
    if hasattr(sys, 'set_int_max_str_digits'):
        sys.set_int_max_str_digits(0)
    main()
