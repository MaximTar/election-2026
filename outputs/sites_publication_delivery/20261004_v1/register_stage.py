"""Register the engineering successor only after the runtime gate succeeds."""
import copy
import datetime
import importlib.util
import json
import re
from pathlib import Path
from src import smz_stage_registry as registry

ROOT = Path(__file__).resolve().parents[3]
P = Path(__file__).resolve().parent
STAGE = 'SITES_PUBLICATION_RUNTIME_V1_READY'


def put(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n')


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return registry.sha(path)


def rel(path):
    return str(Path(path).relative_to(ROOT))


def main():
    check, deterministic = read(P / 'checker_result.json'), read(P / 'determinism.json')
    assert check['status'] == deterministic['status'] == 'PASS'
    assert (P / 'report.md').is_file() and read(P / 'self_review.json')['status'] == 'PASS'
    for name in ('docs/RESEARCH_HANDOFF.md', 'outputs/metadata/research_state.json',
                 'src/smz_stage_registry.py', 'src/analysis/research_handoff.py'):
        assert (ROOT / name).read_bytes() == (P / 'before' / name).read_bytes()
    before = read(P / 'before/outputs/metadata/research_state.json')
    assert before['current_stage'] == 'SMZ_SITES_PUBLICATION_DATA_V1_READY'
    reg = registry.load_registry(); assert len(reg['stages']) == 53
    original_pointer = (ROOT / 'src/smz_stage_registry.py').read_text()
    old_package = re.search(r"PACKAGE=ROOT/'([^']+)'", original_pointer).group(1)
    public = ROOT / 'publication/sites/v1'
    decision = {
        'publication_id': STAGE, 'predecessor': before['current_stage'],
        'published_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'state_field': 'sites_publication_runtime_v1', 'decision': 'PASS',
        'scope': 'A separately authorized Sites client preparation/implementation task against the runtime contract. No article or UI work was performed here.',
        'canonical_manifest_sha256': check['canonical_manifest_after'],
        'runtime_manifest_sha256': sha(public / 'runtime/manifest.json'),
        'public_states': 2064, 'internal_reachable': 0, 'card_only_methods': 2,
        'ABC_shards': 64, 'D_shards': 20, 'runtime_files': check['runtime_files'],
        'scientific_calls': 0, 'new_fits': 0, 'new_scientific_states': 0,
        'new_methodological_choices': 0, 'new_exclusions': 0,
        'canonical_files_changed': 0, 'article_edited': False, 'site_UI_implemented': False,
        'roadmap_99_changed': False, 'item54_started': False,
        'formal_roadmap_position': 'PAUSED_BEFORE_54_FINALIZE_ARTICLE_STRUCTURE',
        'checker_sha256': sha(P / 'checker_result.json'), 'determinism_sha256': sha(P / 'determinism.json'),
    }
    put(P / 'decision.json', decision)
    (P / 'publication.py').write_text('''import copy,json
from pathlib import Path
P=Path(__file__).resolve().parent
def build_state(before):
 d=json.loads((P/'decision.json').read_text());assert before['current_stage']==d['predecessor']
 after=copy.deepcopy(before)
 after.update(current_stage=d['publication_id'],last_updated=d['published_at'],safe_to_proceed='YES WITH LIMITATIONS',proceed_scope=d['scope'])
 after[d['state_field']]=d
 after['methodological_decisions'].extend(json.loads((P/'decision_ledger.json').read_text())['decisions'])
 after['open_issues'].append({'id':'RUNTIME_HOST_GZIP_HANDLING','status':'ACCEPTED LIMITATION','issue':'Explicit gzip alternatives are measured, not a CDN guarantee. Validate hosting byte serving and one-time decompression before client release. Older canonical checker has a closed recursive inventory; use runtime checker for the additive subtree.','artifact':'publication/sites/v1/runtime/CONTRACT.md'})
 return after
''')
    spec = importlib.util.spec_from_file_location('_runtime_publication', P / 'publication.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    after = module.build_state(before)
    put(P / 'publication/research_state.json', after)
    appendix = '''

## SITES_PUBLICATION_RUNTIME_V1_READY — additive publication delivery

### Analysis universes
Primary paper_primary__evidence_20260927 remains 87,736 UIKs / 84 regions / 2,818 official TIKs;
99,360,758 registered voters, 55,674,920 issued ballots and 54,723,201 valid votes. DEG outside
core; overseas separate. No source rows, membership, region/TIK, electorate/denominator,
issued, valid, party votes, coverage, field semantics or scientific result changed. All native
and full/LOO frames are preserved. Cedar remains 71,438 included / 16,298 outside native
scope (2,758 registered <=100 and 13,540 unknown invalid, inherited exclusive reasons).

### Methodological decisions
New scientific choices: 0. User requirement: additive runtime delivery at publication/sites/v1/runtime;
1,640 accepted canonical files stay byte-identical. Source constraint: exactly 2,064 PUBLIC
states (1,600 ABC + 20 D + 444 other executable states), zero INTERNAL, two CARD_ONLY methods
with no project results. Researcher/Codex engineering choices: 64 source/design ABC shards,
20 source/specification D shards, unchanged small canonical files, deterministic explicit gzip
alternatives and lazy existing exact resources. Routing keys and predeclared defaults did not
change; A/B aliases remain slices. No new control, interpolation or Cartesian-product state.

### Open issues
RESOLVED: exact full-record reconstruction from shards, all defaults, hash closure, semantic guards,
explicit availability, deterministic regeneration and delivery measurements. ACCEPTED LIMITATION:
host Content-Encoding behavior must be verified later; select raw OR gzip transport and decompress
only once. Old accepted generator/checker remains unchanged and has a closed recursive inventory;
the new runtime checker validates the additive subtree without rerunning scientific extraction.
D4 group diagnostics remain comparatively large and load only on explicit selection. Final reader
copy and established source-fidelity gaps remain as previously accepted. External branch CLOSED;
G NO_GO; roadmap-99 unchanged and formally paused before 54. No article/site work started.

### Reviewer attention
All state records, values, guards, support/coverage, D undefined markers, output semantics and
source choices match canonical records structurally. No pooled truth scale, confidence-interval
interpretation, honesty/fraud probability or source correctness ranking. Exact pooled strings stay
strings; ordinary chart rendering never requests or decodes exact sidecars. Runtime URLs resolve
against runtime manifest; unchanged state/catalog paths resolve against canonical root. Gzip aliases
are alternate transports, not duplicated scientific states. Separate self-review completed.

### Handoff
Stage completed: additive runtime/delivery optimization for Sites.
Primary universe: paper_primary__evidence_20260927, unchanged.
Input rows: 2,064 accepted PUBLIC state records; no real source rows through kernels.
Output/analysed rows: the same 2,064 records in 64 ABC + 20 D shards and four canonical-backed method files.
Rows excluded: 0 new source exclusions; the previously INTERNAL state remains non-public.
Regions included/excluded: 84 primary; existing LOO/native frames retained; 0 new exclusions.
New methodological choices: 0; delivery-only decisions documented separately.
Important unresolved issues: no blocker; hosting gzip behavior, final copy/release metadata pending.
Reviewer attention: unchanged canonical manifest, exact lazy downloads, explicit routes and URL bases.
Safe to proceed: YES WITH LIMITATIONS — separately authorized Sites client preparation/implementation only.
'''
    (P / 'handoff_append.md').write_text(appendix)
    handoff = (P / 'before/docs/RESEARCH_HANDOFF.md').read_text() + appendix
    (P / 'publication/RESEARCH_HANDOFF.md').write_text(handoff)
    dispatcher = (P / 'before/src/analysis/research_handoff.py').read_text()
    anchor = "    if STATE.exists() and json.loads(STATE.read_text()).get('current_stage')=='SMZ_SITES_PUBLICATION_DATA_V1_READY':\n"
    assert dispatcher.count(anchor) == 1
    route = """    if STATE.exists() and json.loads(STATE.read_text()).get('current_stage')=='SITES_PUBLICATION_RUNTIME_V1_READY':
        if not args.check:
            raise SystemExit('Runtime publication stage is read-only here; use its explicit runtime generator.')
        from src.smz_stage_registry import verify_history
        print(json.dumps(verify_history('SITES_PUBLICATION_RUNTIME_V1_READY')),flush=True)
        import subprocess
        subprocess.run(['/usr/bin/python3','-m','src.publication_sites.runtime_check'],check=True)
        return
"""
    (ROOT / 'src/analysis/research_handoff.py').write_text(dispatcher.replace(anchor, route + anchor))
    code_files = sorted((ROOT / 'src/publication_sites').glob('runtime_*.py')) + [ROOT / 'src/analysis/research_handoff.py']
    put(P / 'code_freeze.json', {'files': {rel(f): sha(f) for f in code_files}})
    put(P / 'publication_seal.json', {'status': 'PASS', 'files': {
        rel(f): sha(f) for f in sorted(P.rglob('*')) if f.is_file() and '__pycache__' not in f.parts
        and f.name not in ('manifest.json', 'publication_seal.json')}})
    reg = copy.deepcopy(reg)
    reg.update(version='SMZ_IMMUTABLE_STAGE_REGISTRY_54', previous_registry=old_package + '/stage_registry.json',
               previous_registry_sha256=sha(ROOT / old_package / 'stage_registry.json'))
    for name in ('src/smz_stage_registry.py', 'src/analysis/research_handoff.py'):
        reg['engineering_resolutions'].append({'path': name, 'sha256': sha(P / 'before' / name), 'archive': rel(P / 'before' / name)})
    reg['stages'].append({
        'id': STAGE, 'previous_id': before['current_stage'], 'package': rel(P),
        'manifest': rel(P / 'publication_seal.json'), 'manifest_sha256': sha(P / 'publication_seal.json'),
        'contract_sha256': reg['stages'][-1]['contract_sha256'],
        'before_state': rel(P / 'before/outputs/metadata/research_state.json'), 'after_state': rel(P / 'publication/research_state.json'),
        'before_handoff': rel(P / 'before/docs/RESEARCH_HANDOFF.md'), 'after_handoff': rel(P / 'publication/RESEARCH_HANDOFF.md'),
        'builder': {'path': rel(P / 'publication.py'), 'sha256': sha(P / 'publication.py'), 'function': 'build_state', 'arguments': []},
        'outcome': 'PASS', 'outcome_path': ['sites_publication_runtime_v1', 'decision'],
        'evidence_hashes': {rel(P / n): sha(P / n) for n in ('decision.json', 'decision_ledger.json', 'report.md', 'self_review.json', 'determinism.json', 'checker_result.json')},
    })
    put(P / 'stage_registry.json', reg)
    pointer = original_pointer.replace("PACKAGE=ROOT/'" + old_package + "'", "PACKAGE=ROOT/'" + rel(P) + "'")
    pointer = re.sub(r"REGISTRY_SHA='[a-f0-9]+'", "REGISTRY_SHA='" + sha(P / 'stage_registry.json') + "'", pointer, count=1)
    (ROOT / 'src/smz_stage_registry.py').write_text(pointer)
    (ROOT / 'outputs/metadata/research_state.json').write_bytes((P / 'publication/research_state.json').read_bytes())
    (ROOT / 'docs/RESEARCH_HANDOFF.md').write_text(handoff)
    print(json.dumps({'status': 'PASS', 'stage': STAGE, 'registered_stages': 54, 'science_changed': False}))


if __name__ == '__main__':
    main()
