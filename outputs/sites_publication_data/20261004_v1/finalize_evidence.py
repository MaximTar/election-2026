"""Seal final engineering evidence after the current-stage checker succeeds."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
P = Path(__file__).resolve().parent
PUBLIC = ROOT / 'publication/sites/v1'


def sha(path):
    with Path(path).open('rb') as stream:
        value = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n')


def main():
    log = (P / 'general_checker.log').read_text().splitlines()
    objects = [json.loads(line) for line in log if line.strip().startswith('{')]
    assert len(objects) == 2, 'History and current publication checks are both required'
    history = next(value for value in objects if 'publications' in value)
    publication = next(value for value in objects if 'public_states' in value)
    assert history['status'] == publication['status'] == 'PASS'
    assert history['publications'] == 53
    assert publication['manifest_sha256'] == sha(PUBLIC / 'manifest.json')
    assert '\tExit status: 0' in (P / 'general_checker_runtime.txt').read_text()
    # Nothing recorded by the stage seal may change during final checking.
    seal = read(P / 'publication_seal.json')
    assert all(sha(ROOT / name) == digest for name, digest in seal['files'].items())
    for name, digest in read(P / 'code_freeze.json')['files'].items():
        assert sha(ROOT / name) == digest
    assert (ROOT / 'docs/RESEARCH_HANDOFF.md').read_bytes() == (P / 'publication/RESEARCH_HANDOFF.md').read_bytes()
    assert (ROOT / 'outputs/metadata/research_state.json').read_bytes() == (P / 'publication/research_state.json').read_bytes()
    assert publication['publication_inventory_sha256'] == read(P / 'determinism.json')['first_inventory_sha256']
    final = {
        'status': 'PASS',
        'general_checker_exit_status': 0,
        'history_check': history,
        'publication_check': publication,
        'sealed_evidence_unchanged': True,
        'live_handoff_state_match_registered_append_only_stage': True,
        'final_public_inventory_matches_both_generations': True,
        'scientific_changes': 0,
        'article_or_site_implementation_changes': 0,
    }
    write(P / 'final_checker_results.json', final)
    modified = []
    for name in ('docs/RESEARCH_HANDOFF.md', 'outputs/metadata/research_state.json',
                 'src/smz_stage_registry.py', 'src/analysis/research_handoff.py'):
        modified.append({'path': name, 'before_sha256': sha(P / 'before' / name),
                         'after_sha256': sha(ROOT / name),
                         'purpose': 'Append-only publication-stage registration and scoped checker dispatch',
                         'historical_bytes_archive': str((P / 'before' / name).relative_to(ROOT))})
    new_code = {str(path.relative_to(ROOT)): sha(path)
                for path in sorted((ROOT / 'src/publication_sites').glob('*.py'))}
    write(P / 'file_changes.json', {
        'modified_existing_files': modified,
        'new_engineering_source_files': new_code,
        'new_public_files_inventory': 'publication/sites/v1/manifest.json',
        'new_public_file_count': publication['files'],
        'new_public_manifest_sha256': sha(PUBLIC / 'manifest.json'),
        'new_evidence_inventory': str((P / 'manifest.json').relative_to(ROOT)),
        'frozen_scientific_or_result_files_modified': 0,
        'article_files_modified': 0, 'site_implementation_files_modified': 0,
    })
    # This terminal manifest is separate from the earlier immutable stage seal.
    files = {str(path.relative_to(ROOT)): sha(path) for path in sorted(P.rglob('*'))
             if path.is_file() and '__pycache__' not in path.parts
             and path.name not in ('manifest.json', 'manifest.sha256')}
    write(P / 'manifest.json', {
        'status': 'PASS', 'stage': 'SITES_PUBLICATION_DATA_V1',
        'files': files, 'new_engineering_sources': new_code,
        'public_manifest': {'path': 'publication/sites/v1/manifest.json', 'sha256': sha(PUBLIC / 'manifest.json')},
        'live_metadata_files': modified,
        'scientific_model_calls': 0, 'new_fits': 0, 'new_scientific_states': 0,
        'public_states': 2064, 'internal_states_exported': 0,
        'separate_publication_stage_seal_sha256': sha(P / 'publication_seal.json'),
    })
    (P / 'manifest.sha256').write_text(sha(P / 'manifest.json') + '  manifest.json\n')
    print(json.dumps({'status': 'PASS', 'evidence_manifest_sha256': sha(P / 'manifest.json'),
                      'public_manifest_sha256': sha(PUBLIC / 'manifest.json'),
                      'public_states': 2064, 'modified_existing_engineering_metadata_files': len(modified)}))


if __name__ == '__main__':
    main()
