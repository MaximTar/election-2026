"""Read-only translation checks. No models, generation, network, or file writes.
Run: python3 -B publication/i18n/en/v1/validate_translation.py
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parent
TAG = 'ru-release-v1'
COMMIT = '20bacb4c343e952062599889ea4a4938fb258b98'
NOTE = '**Translation note.** This English version was translated from the original Russian with OpenAI models and checked for semantic consistency. The Russian release remains the authoritative version. Translation errors are still possible.'
NOTICE = 'Machine-translated from Russian with OpenAI models. The Russian release is the authoritative version.'
SOURCES = {
    'technical_article.md': 'f08eba55efabb86fd996b2c99d81d7c0a75ed064d8229122a4ac16e43767f19f',
    'narrative.md': 'fdf9226505f85b34e45f0a3831bff8485c8093e25405276fd9748c6287872e0d',
}
BINDINGS = {
    'publication/sites/v1/manifest.json': '38d8f0eaa79952b4036d7e23c04ff40cca65f51e40f5cbbcddc88efd92fc3d16',
    'publication/sites/v1/runtime/manifest.json': '3998d58ec33c4bb8d28b6a35abdb5d2d2d28772a7aaea20b7fbd61afd598131c',
    'publication/sites/presentation/20261005_v1/manifest.json': 'beb00a95ad1f1d9edc5e05fff17b033a7f23649ecee9b470520b8838f5f7e771',
}
# These are labels inside inline coordinate formulas, not changed mathematics.
INLINE_TRANSLATIONS = {
    '(действительные + известные недействительные бюллетени) / зарегистрированные избиратели': '(valid + known invalid ballots) / registered voters',
    'выдано бюллетеней / зарегистрировано избирателей': 'ballots issued / registered voters',
}
FORMULA_IDENTIFIER = 'Q(λ,μ) = Qисх + λKсостав + μKобъём + λμKвзаимодействие'

def digest(b):
    return hashlib.sha256(b).hexdigest()

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

def links(s):
    return re.findall(r'https?://[^\s)<>]+', s)

def numbers(s):
    s = re.sub(r'https?://[^\s)<>]+', '', s)
    # Preserve precision, sign, order and all digit tokens. Ignore only grouping spaces.
    return [re.sub(r'[ \u00a0\u202f]', '', x) for x in re.findall(r'[−]?\d+(?:[ \u00a0\u202f]\d{3}(?!\d))*(?:\.\d+)?', s)]

def kind(line):
    if not line.strip(): return 'blank'
    if line.startswith('#'): return 'heading:' + str(len(line) - len(line.lstrip('#')))
    if line.startswith('|'): return 'table:' + str(line.count('|'))
    if line.startswith(('Место для графика:', 'Figure placeholder:')): return 'figure'
    if line.startswith('<'): return 'html:' + re.sub(r'>.*', '>', line)
    if line.startswith('>'): return 'blockquote'
    if line.startswith('- '): return 'unordered_item'
    return 'text'

def articles():
    result = {}
    for name, expected in SOURCES.items():
        path = 'publication/articles/v2/' + name
        raw = git('show', TAG + ':' + path)
        assert digest(raw) == expected, path
        assert (ROOT / path).read_bytes() == raw, 'Local Russian source changed: ' + path
        ru = raw.decode().replace('\r\n', '\n')
        out = (PACKAGE / name).read_bytes()
        en_full = out.decode()
        assert en_full.count(NOTE) == 1, name + ': translation note'
        note_line = 4 if name == 'technical_article.md' else 2
        assert en_full.splitlines()[note_line] == NOTE, name + ': note position'
        en = en_full.replace(NOTE + '\n\n', '')
        assert numbers(ru) == numbers(en), name + ': numeric token sequence/precision'
        assert links(ru) == links(en), name + ': link order/bytes'
        rlines, elines = ru.splitlines(), en.splitlines()
        assert [kind(x) for x in rlines] == [kind(x) for x in elines], name + ': complete line/block structure'
        assert [re.findall(r'`([^`]+)`', x) for x in elines] == [[INLINE_TRANSLATIONS.get(v, v) for v in re.findall(r'`([^`]+)`', x)] for x in rlines], name + ': inline code/formulas'
        # Per-line numeric checks catch value movement into a different paragraph or cell.
        for i, (r, e) in enumerate(zip(rlines, elines), 1):
            assert numbers(r) == numbers(e), f'{name}:{i}: numeric location'
            if r.startswith('|'):
                assert [numbers(c) for c in r.split('|')] == [numbers(c) for c in e.split('|')], f'{name}:{i}: table cell'
                if re.fullmatch(r'[| :\-]+', r):
                    align = lambda s: [(c.strip().startswith(':'), c.strip().endswith(':')) for c in s.split('|')[1:-1]]
                    assert align(r) == align(e), f'{name}:{i}: table alignment'
        assert ru.count('**') == en.count('**'), name + ': bold markup'
        stripped = re.sub(r'https?://[^\s)<>]+', '', en).replace(FORMULA_IDENTIFIER, '')
        assert not re.search('[А-Яа-яЁё]', stripped), name + ': untranslated Cyrillic prose'
        assert not re.search(r'\d,\d', en), name + ': decimal comma'
        figure_count = sum(x.startswith('Figure placeholder:') for x in elines)
        assert figure_count == (8 if name == 'technical_article.md' else 0)
        result[name] = {
            'russian_sha256': expected, 'english_sha256': digest(out),
            'heading_count': sum(x.startswith('#') for x in rlines),
            'table_count': sum(x.startswith('|') and (i == 0 or not rlines[i-1].startswith('|')) for i,x in enumerate(rlines)),
            'table_lines': sum(x.startswith('|') for x in rlines),
            'details_count': ru.count('<details>'), 'blockquote_lines': sum(x.startswith('>') for x in rlines),
            'unordered_items': sum(x.startswith('- ') for x in rlines),
            'links': len(links(ru)), 'numeric_tokens': len(numbers(ru)),
            'figure_anchors': figure_count, 'line_structure_matches': True,
            'numbers_links_formulas_tables_emphasis_match': True,
            'untranslated_prose_occurrences': 0,
        }
    return result

def check(pre_freeze=False):
    assert git('rev-parse', TAG + '^{commit}').decode().strip() == COMMIT
    result = {'articles': articles()}
    for path, expected in BINDINGS.items():
        assert digest(git('show', TAG + ':' + path)) == expected, path
        assert digest((ROOT / path).read_bytes()) == expected, 'Current frozen binding: ' + path
    c = json.loads((PACKAGE / 'site_strings.json').read_text())
    assert c['translation.notice'] == NOTICE
    assert c['translation.russian_link'] == 'Russian version'
    assert all(isinstance(v, str) and v for v in c.values())
    assert not any(re.search('[А-Яа-яЁё]', v) for v in c.values())
    inv = json.loads((PACKAGE / 'site_copy_inventory.json').read_text())
    assert inv['catalog_count'] == len(c)
    assert all(x['key'] in c for x in inv['literal_mappings'])
    for path in inv['repository_sources']:
        assert digest(git('show', TAG + ':' + path['path'])) == path['sha256']
    sources = json.loads(git('show', TAG + ':publication/sites/v1/sources.json'))
    assert {k[7:] for k in c if k.startswith('region.') and k != 'region.name_unavailable'} == {x['official_region_id'] for x in sources['official_regions']}
    party_ids = json.loads(git('show', TAG + ':publication/sites/v1/baselines.json'))['party_order']
    assert {k[6:] for k in c if k.startswith('party.')} == set(party_ids)
    designs = json.loads(git('show', TAG + ':publication/sites/v1/designs.json'))['abc']['designs']
    assert {k[7:] for k in c if k.startswith('design.')} == {x['id'] for x in designs}
    result['site_catalog'] = {'strings': len(c), 'source_mappings': len(inv['literal_mappings']), 'regions': 84, 'parties': 10, 'designs': 16, 'untranslated_reader_strings': 0}
    if not pre_freeze:
        m = json.loads((PACKAGE / 'manifest.json').read_text())
        assert m['source_freeze_commit'] == COMMIT and m['source_russian_release'] == TAG
        assert m['semantic_equivalence_review'] == 'PASS'
        assert m['authoritative_language'] == 'ru' and m['language'] == 'en'
        assert all(m[x] == 0 for x in ['new_scientific_states', 'fits', 'model_calls_for_science'])
        assert m['scientific_state_changed'] is False
        actual = {p.name for p in PACKAGE.iterdir() if p.is_file()}
        assert actual == {x['path'] for x in m['files']} | {'manifest.json'}
        for f in m['files']:
            b = (PACKAGE / f['path']).read_bytes()
            assert digest(b) == f['sha256'] and len(b) == f['bytes'], f['path']
        qa = json.loads((PACKAGE / 'semantic_review.json').read_text())
        assert qa['status'] == 'PASS'
        assert all(v == 'PASS' for v in m['translation_gates'].values())
        for name in SOURCES:
            assert qa['translation_hashes'][name] == digest((PACKAGE / name).read_bytes())
    result.update({'status': 'PASS', 'scientific_bindings_unchanged': True, 'science_calls': 0, 'writes': 0})
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pre-freeze', action='store_true', help='Check completed translations before creating the freeze manifest.')
    args = parser.parse_args()
    print(json.dumps(check(args.pre_freeze), ensure_ascii=False, indent=2, sort_keys=True))
