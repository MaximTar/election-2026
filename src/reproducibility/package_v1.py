"""Build deterministic assets from an explicit, hash-bound dependency allowlist.

No discovery, input substitution, estimator invocation, or scientific serialization.
"""
import argparse
import gzip
import tarfile
from .common import ROOT, RELEASE, read, sha, need, safe_relative, write


def package(destination):
    destination.mkdir(parents=True, exist_ok=True)
    manifest = read(RELEASE / 'manifest.json')
    excluded = {x['original_project_path'] for x in manifest['external_inputs']}
    excluded_hashes = {x['sha256'] for x in manifest['external_inputs']}
    assets = []
    for spec in manifest['asset_definitions']:
        selected = sorted(x for x in manifest['files'] if manifest['files'][x]['delivery'] == spec['name'])
        need(bool(selected), 'empty asset')
        target = destination / spec['name']
        with target.open('wb') as output:
            with gzip.GzipFile(filename='', fileobj=output, mode='wb', mtime=0, compresslevel=6) as compressed:
                with tarfile.open(fileobj=compressed, mode='w', format=tarfile.PAX_FORMAT) as archive:
                    for name in selected:
                        safe_relative(name)
                        record = manifest['files'][name]
                        need(name not in excluded and record['sha256'] not in excluded_hashes, 'excluded raw input')
                        source = ROOT / name
                        need(source.is_file(), 'file policy')
                        if source.is_symlink():
                            need(record.get('local_alias_target') == source.resolve().relative_to(ROOT).as_posix(), 'unregistered local alias')
                            need(sha(source.resolve()) == record['sha256'], 'alias target bytes changed')
                        need(source.stat().st_size == record['bytes'] and sha(source) == record['sha256'], 'packaging source changed: ' + name)
                        info = tarfile.TarInfo(name)
                        info.size = record['bytes']; info.mode = 0o644; info.mtime = 0
                        info.uid = info.gid = 0; info.uname = info.gname = ''
                        with source.open('rb') as stream:
                            archive.addfile(info, stream)
        assets.append({'name': target.name, 'bytes': target.stat().st_size, 'sha256': sha(target), 'file_count': len(selected)})
    write(destination / 'assets.json', {'assets': assets})
    return assets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=__import__('pathlib').Path, required=True)
    args = parser.parse_args()
    print(__import__('json').dumps(package(args.destination), sort_keys=True))


if __name__ == '__main__':
    main()
