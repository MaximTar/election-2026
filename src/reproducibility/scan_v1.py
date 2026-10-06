"""Scan the exact allowlisted payload and archive members without disclosing values.

Credential signatures, session/export path categories, private key envelopes,
credential-like assignments and personal absolute paths are checked. Synthetic
code uses of token/key names are not credentials. No scanner proves universal
absence; findings require review before publication.
"""
import argparse
import gzip
import re
import tarfile
import zlib
from pathlib import Path
from .common import ROOT, RELEASE, read, write, need

PATTERNS = {
    'credential_signature': re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|sk-(?:proj-)?[A-Za-z0-9_-]{40,}|AKIA[A-Z0-9]{16})'),
    'private_key': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----'),
    'credential_assignment': re.compile(rb'''(?i)(?:api[_-]?key|access[_-]?token|password|authorization|cookie)\s*[=:]\s*["'](?:Bearer\s+)?[A-Za-z0-9_+/=-]{24,}["']'''),
    'personal_absolute_path': re.compile(rb'(?:/home/(?!runner(?:/|\b))[A-Za-z0-9_.-]+/|[A-Za-z]:[\\/]Users[\\/][A-Za-z0-9_.-]+[\\/])'),
    'unnecessary_local_network_metadata': re.compile(rb'"local_ip"\s*:\s*"[^"n]'),
}
FORBIDDEN_PARTS = {'.env', '.aws', '.ssh', 'vault', 'browser_profile', 'node_modules', '__pycache__', '.idea', '.venv'}


def decoded(name, blob):
    if name.endswith('.gz'):
        return gzip.decompress(blob)
    if '/exact_records/' in name:
        return zlib.decompress(blob)
    return blob


def inspect(name, blob):
    findings = []
    if any(p in FORBIDDEN_PARTS for p in Path(name).parts) or name.endswith(('.har', '.pem', '.key', '.p12')):
        findings.append({'path': name, 'category': 'private_or_local_path_category'})
    data = decoded(name, blob)
    for category, pattern in PATTERNS.items():
        if pattern.search(data):
            findings.append({'path': name, 'category': category})
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    manifest = read(RELEASE / 'manifest.json')
    findings = []
    for name in manifest['files']:
        findings.extend(inspect(name, (ROOT / name).read_bytes()))
    for path in sorted(RELEASE.glob('*')):
        if path.is_file():
            findings.extend(inspect(str(path.relative_to(ROOT)), path.read_bytes()))
    archive_members = 0
    if args.assets:
        for asset in read(RELEASE / 'assets.json')['assets']:
            with tarfile.open(args.assets / asset['name'], 'r|gz') as archive:
                for member in archive:
                    need(member.isfile(), 'unexpected archive member')
                    findings.extend(inspect(member.name, archive.extractfile(member).read()))
                    archive_members += 1
    unique = sorted({(x['path'], x['category']) for x in findings})
    result = {'status': 'PASS' if not unique else 'REVIEW_REQUIRED', 'files_scanned': len(manifest['files']),
              'archive_members_scanned': archive_members, 'decoded_gzip_and_exact_records': True,
              'findings': [{'path': p, 'category': c} for p, c in unique],
              'secret_values_printed': False, 'limitations': 'Signature/path scan plus explicit dependency allowlist; not a universal proof against all forms of private information.'}
    write(args.output, result)
    print(__import__('json').dumps(result, sort_keys=True))
    if unique:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
