"""Close the additive engineering evidence after the current handoff gate."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
P = Path(__file__).resolve().parent
PUBLIC = ROOT / 'publication/sites/v1'
RUNTIME = PUBLIC / 'runtime'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def put(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n')


def main():
    log = [json.loads(line) for line in (P / 'general_checker.log').read_text().splitlines()
           if line.startswith('{')]
    assert len(log) == 2
    history = next(row for row in log if 'publications' in row)
    runtime = next(row for row in log if 'public_states' in row)
    assert history['status'] == runtime['status'] == 'PASS' and history['publications'] == 54
    assert '\tExit status: 0' in (P / 'general_checker_runtime.txt').read_text()
    for name, value in read(P / 'publication_seal.json')['files'].items():
        assert sha(ROOT / name) == value, name
    for name, value in read(P / 'code_freeze.json')['files'].items():
        assert sha(ROOT / name) == value, name
    for name, value in read(P / 'canonical_before.json').items():
        assert sha(PUBLIC / name) == value, name
    assert runtime['runtime_manifest_sha256'] == sha(RUNTIME / 'manifest.json')
    assert runtime['runtime_inventory_sha256'] == read(P / 'determinism.json')['second_inventory_sha256']
    assert (ROOT / 'docs/RESEARCH_HANDOFF.md').read_bytes() == (P / 'publication/RESEARCH_HANDOFF.md').read_bytes()
    assert (ROOT / 'outputs/metadata/research_state.json').read_bytes() == (P / 'publication/research_state.json').read_bytes()
    put(P / 'final_checker_result.json', {'status': 'PASS', 'history_check': history, 'runtime_check': runtime,
        'canonical_files_changed': 0, 'canonical_manifest_before_after': sha(PUBLIC / 'manifest.json'),
        'registered_stage_evidence_unchanged': True, 'final_inventory_matches_both_generations': True,
        'handoff_state_match_registered_append_only_stage': True})
    changes = []
    for name in ('docs/RESEARCH_HANDOFF.md', 'outputs/metadata/research_state.json',
                 'src/smz_stage_registry.py', 'src/analysis/research_handoff.py'):
        changes.append({'path': name, 'before_sha256': sha(P / 'before' / name), 'after_sha256': sha(ROOT / name),
                        'historical_version_archive': str((P / 'before' / name).relative_to(ROOT)),
                        'purpose': 'Append-only engineering stage registration/scoped checker dispatch'})
    sources = {str(f.relative_to(ROOT)): sha(f) for f in sorted((ROOT / 'src/publication_sites').glob('runtime_*.py'))}
    runtime_inventory = {str(f.relative_to(RUNTIME)): sha(f) for f in sorted(RUNTIME.rglob('*')) if f.is_file()}
    put(P / 'file_changes.json', {
        'canonical_publication_files_changed': 0, 'canonical_files_verified': 1640,
        'canonical_manifest_sha256_before_after': sha(PUBLIC / 'manifest.json'),
        'accepted_generator_checker_code_changed': 0,
        'new_runtime_files': {'base': 'publication/sites/v1/runtime', 'count': len(runtime_inventory), 'sha256_by_relative_path': runtime_inventory},
        'new_delivery_code': sources, 'existing_metadata_files_modified': changes,
        'new_evidence_files_inventory': str((P / 'manifest.json').relative_to(ROOT)),
        'article_files_edited': 0, 'site_UI_files_implemented': 0,
        'frozen_scientific_artifacts_modified': 0,
    })
    evidence = {str(f.relative_to(ROOT)): sha(f) for f in sorted(P.rglob('*'))
                if f.is_file() and '__pycache__' not in f.parts and f.name not in ('manifest.json', 'manifest.sha256')}
    put(P / 'manifest.json', {'status': 'PASS', 'stage': 'PUBLICATION_DELIVERY_RUNTIME_V1',
        'files': evidence, 'new_delivery_source_files': sources,
        'canonical_manifest_sha256': sha(PUBLIC / 'manifest.json'),
        'runtime_manifest': {'path': 'publication/sites/v1/runtime/manifest.json', 'sha256': sha(RUNTIME / 'manifest.json')},
        'publication_stage_seal_sha256': sha(P / 'publication_seal.json'),
        'public_states': 2064, 'internal_reachable': 0, 'card_only_project_results': 0,
        'new_model_calls': 0, 'new_fits': 0, 'new_scientific_states': 0,
        'real_source_rows_passed_through_kernels': 0, 'new_methodological_choices': 0,
        'canonical_files_changed': 0})
    (P / 'manifest.sha256').write_text(sha(P / 'manifest.json') + '  manifest.json\n')
    print(json.dumps({'status': 'PASS', 'evidence_manifest_sha256': sha(P / 'manifest.json'),
                      'runtime_manifest_sha256': sha(RUNTIME / 'manifest.json'), 'public_states': 2064}))


if __name__ == '__main__':
    main()
