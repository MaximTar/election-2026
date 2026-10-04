"""Delivery-only access to the sealed publication view; no pipeline imports."""
import gzip
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / 'publication/sites/v1'
RUNTIME = CANONICAL / 'runtime'
EVIDENCE = ROOT / 'outputs/sites_publication_delivery/20261004_v1'
CANONICAL_SHA = '38d8f0eaa79952b4036d7e23c04ff40cca65f51e40f5cbbcddc88efd92fc3d16'
COUNTS = {'abc': 1600, 'd': 20, 'cedar': 161, 'vazhnye_istorii': 102,
          'novaya_1d': 90, 'novaya_2d': 91}
INTERNAL = 'ISTORIES__primary__DEFAULT__LS_B_WINDOW'
CODE_FILES = ['src/publication_sites/runtime_' + n + '.py'
              for n in ('common', 'generate', 'check', 'measure')]


def need(condition, message):
    if not condition:
        raise ValueError('PUBLICATION_RUNTIME: ' + message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(',', ':'), allow_nan=False) + '\n').encode()


def read(path):
    return json.loads(Path(path).read_bytes())


def zipped(blob):
    output = io.BytesIO()
    with gzip.GzipFile(filename='', mode='wb', fileobj=output,
                       mtime=0, compresslevel=6) as f:
        f.write(blob)
    return output.getvalue()


def canonical_inventory():
    need(sha(CANONICAL / 'manifest.json') == CANONICAL_SHA, 'accepted manifest changed')
    m = read(CANONICAL / 'manifest.json')
    inventory = {'manifest.json': CANONICAL_SHA}
    for name, item in m['files'].items():
        path = CANONICAL / name
        need(path.is_file() and sha(path) == item['sha256']
             and path.stat().st_size == item['bytes'], 'canonical hash/size: ' + name)
        inventory[name] = item['sha256']
    present = {str(p.relative_to(CANONICAL)) for p in CANONICAL.rglob('*')
               if p.is_file() and not p.is_relative_to(RUNTIME)}
    need(present == set(inventory), 'unlisted canonical file outside additive runtime')
    need(len(inventory) == 1640, 'accepted canonical inventory count')
    for name, value in m['generator']['source_files'].items():
        need(sha(ROOT / name) == value, 'accepted generator/checker changed: ' + name)
    return m, inventory


def canonical_tables():
    catalog = read(CANONICAL / 'methods.json')
    groups = {name: read(CANONICAL / f'states/{name}.json') for name in COUNTS}
    for name, table in groups.items():
        need(table['state_count'] == len(table['states']) == COUNTS[name], 'canonical count ' + name)
        need(all(s['visibility'] == 'PUBLIC' for s in table['states']), 'non-public canonical state')
    return catalog, groups


def inventory(path=RUNTIME):
    return {str(p.relative_to(path)): sha(p) for p in sorted(path.rglob('*')) if p.is_file()}


def resolve_runtime_reference(name):
    """All delivery URLs are relative to the runtime manifest, not the shard."""
    path = (RUNTIME / name).resolve()
    need(path.is_relative_to(CANONICAL.resolve()), 'reference escapes publication tree')
    return path


def canonical_exact_reference(state):
    name = state['result'].get('exact_file')
    if name is None:
        return None
    path = (CANONICAL / name).resolve()
    need(path.is_relative_to((CANONICAL / 'exact').resolve()), 'exact path outside canonical exact directory')
    return path
