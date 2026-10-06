"""Portable, standard-library release inventory utilities."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / 'reproducibility/v1'
BINDINGS = {
    'publication/sites/v1/manifest.json': '38d8f0eaa79952b4036d7e23c04ff40cca65f51e40f5cbbcddc88efd92fc3d16',
    'publication/sites/v1/runtime/manifest.json': '3998d58ec33c4bb8d28b6a35abdb5d2d2d28772a7aaea20b7fbd61afd598131c',
    'publication/sites/presentation/20261005_v1/manifest.json': 'beb00a95ad1f1d9edc5e05fff17b033a7f23649ecee9b470520b8838f5f7e771',
}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n')


def need(condition, message):
    if not condition:
        raise ValueError('REPRODUCIBILITY: ' + message)


def safe_relative(name):
    p = Path(name)
    need(not p.is_absolute() and '..' not in p.parts and name == p.as_posix(), 'unsafe archive path')
    return p


def external_guard(root, families=None):
    """Check bytes before importing any scientific code or creating an output."""
    root = Path(root).resolve()
    inputs = read(RELEASE / 'external_inputs.json')['inputs']
    selected = [x for x in inputs if families is None or set(families) & set(x['required_for'])]
    need(bool(selected), 'no registered external dependencies selected')
    for entry in selected:
        path = root / safe_relative(entry['original_project_path'])
        need(path.is_file(), 'MISSING_EXTERNAL_INPUT: ' + entry['original_project_path'])
        need(sha(path) == entry['sha256'], 'EXTERNAL_INPUT_HASH_MISMATCH: ' + entry['original_project_path'])
    return {'status': 'PASS', 'external_inputs_verified': len(selected), 'model_calls': 0}
