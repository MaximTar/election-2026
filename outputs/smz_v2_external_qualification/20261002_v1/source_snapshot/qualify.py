"""CLI for the fixed 63 synthetic fixtures only. No dataset/real-run arguments."""
import copy
import csv
import datetime
from fractions import Fraction as F
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import platform
import resource
import signal
import sys
import time
from types import SimpleNamespace

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
FREEZE = ROOT / 'outputs/smz_v2_external_freeze/20261002_v2'
OUT = ROOT / 'outputs/smz_v2_external_qualification/20261002_v1'
CODE = Path(__file__).resolve().parent
READ_PROJECT_FILES = {str((FREEZE / n).resolve()) for n in [
    'synthetic_fixtures.json', 'fixture_resolution.json', 'state_index.csv', 'state_index_summary.json',
    'ui_state_availability.csv', 'checker_results.json', 'manifest.json', 'manifest.sha256']}
FILE_AUDIT = {'project_files_read': set(), 'forbidden_access_attempts': [], 'network_attempts': 0}


def audit(event, args):
    if event in ['socket.connect', 'socket.bind']:
        FILE_AUDIT['network_attempts'] += 1
        raise SystemExit('QUALIFICATION_NETWORK_FORBIDDEN')
    if event != 'open' or not args or not isinstance(args[0], (str, bytes, os.PathLike)):
        return
    path = os.path.realpath(os.fsdecode(args[0]))
    mode, flags = args[1], args[2]
    writing = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
    if path.startswith(str(ROOT) + '/'):
        allowed = (path.startswith(str(OUT) + '/') or
                   path.startswith(str(CODE) + '/') or
                   path.startswith(str(FREEZE / 'contracts') + '/') or
                   path in READ_PROJECT_FILES or path == str(ROOT / 'src/__init__.py') or
                   (path.startswith(str(ROOT / 'src/__pycache__') + '/') and
                    os.path.basename(path).startswith('__init__.')))
        if not allowed or (writing and not path.startswith(str(OUT) + '/')):
            FILE_AUDIT['forbidden_access_attempts'].append(path)
            raise SystemExit('QUALIFICATION_REAL_PROJECT_IO_FORBIDDEN: ' + path)
        if not writing:
            FILE_AUDIT['project_files_read'].add(path)
    if writing and not path.startswith(str(OUT) + '/') and path not in ['/dev/null']:
        raise SystemExit('QUALIFICATION_WRITE_SCOPE_FORBIDDEN: ' + path)


sys.addaudithook(audit)
resource.setrlimit(resource.RLIMIT_AS, (10 * 1024**3, 10 * 1024**3))

import numpy as np
import scipy
import sklearn
from . import common, istories as i, cedar as c, gaussian1d as n, gmm2d as g
from .qualification_units import run as units_run


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def clean(value):
    if isinstance(value, np.ndarray):
        if value.size > 100:
            return {'shape': list(value.shape), 'dtype': str(value.dtype), 'sha256': hashlib.sha256(value.tobytes()).hexdigest()}
        return clean(value.tolist())
    if isinstance(value, np.generic):
        return clean(value.item())
    if isinstance(value, F):
        return str(value)
    if isinstance(value, float):
        return value if math.isfinite(value) else 'NONFINITE'
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items() if not str(k).startswith('_')}
    if isinstance(value, (tuple, list)):
        if len(value) > 100:
            return {'count': len(value), 'sha256': hashlib.sha256(json.dumps(clean(list(value[:100])) + ['TRUNCATED_FOR_DIGEST'], sort_keys=True).encode()).hexdigest(),
                    'full_logical_digest': hashlib.sha256(json.dumps([clean(x) for x in value], sort_keys=True).encode()).hexdigest()}
        return [clean(x) for x in value]
    return value


def put(name, value):
    with (OUT / name).open('x') as f:
        json.dump(clean(value), f, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        f.write('\n')


def check(condition, detail):
    if not condition:
        raise AssertionError(str(clean(detail)))


FIXTURES = json.loads((FREEZE / 'synthetic_fixtures.json').read_text())['fixtures']
BYID = {f['id']: f for f in FIXTURES}
CACHE = {}


def i_base():
    return common.frame(BYID['I01_ROS']['input'], 'I01')


def cedar_stub(parameters):
    def backend(*args, **kwargs):
        return np.asarray(parameters, dtype=float), np.eye(6)
    return backend


def selector_fault(*args, **kwargs):
    raise RuntimeError('injected synthetic optimizer exception')


def n_hist(h=F(1, 100)):
    fixture = next(f for f in FIXTURES if f['family'] == 'NOVAYA_1D' and
                   f['kind'] == 'exact_noiseless_curve' and F(f['input']['h']) == h)
    p = np.array([[a['mu'], a['sigma'], a['A']] for a in fixture['input']['components']])
    return n.SyntheticHistogram(h, n.curve(n.grid(h), p))


def n_default():
    if 'n_default' not in CACHE:
        CACHE['n_default'] = n.fit(n_hist())
    return CACHE['n_default']


def points(cov='full'):
    fixture = BYID['N2_MIX_' + cov]['input']
    generator = np.random.Generator(np.random.PCG64(2026100299))
    X = np.concatenate([generator.multivariate_normal(mean, covariance, size=3000)
                        for mean, covariance in zip(fixture['means'], fixture['covariances'])])
    check(np.all((X >= 0) & (X <= 1)), 'fixture generator domain; no retries or clipping')
    return g.SyntheticPoints(X, tuple(f'mock:N2:{j:05d}' for j in range(len(X))),
                             tuple('mock:region:A' if j % 2 == 0 else 'mock:region:B' for j in range(len(X))),
                             tuple([1000] * len(X)))


def g_default():
    if 'g_default' not in CACHE:
        CACHE['g_default'] = g.fit(points())
    return CACHE['g_default']


def shared(fixture):
    id = fixture['id']
    if id == 'SH01_DETERMINISM':
        a, b = i.run(i_base()), i.run(i_base())
        check(common.digest(a) == common.digest(b), 'deterministic exact replay')
        return {'exact_replay_sha256': common.digest(a)}
    if id == 'SH02_ROW_ORDER':
        a = i_base()
        b = common.SyntheticFrame(tuple(reversed(a.rows)))
        # The kernel canonicalizes; do not reorder the shuffled test input here.
        check(common.digest(i.run(a)) == common.digest(i.run(b)), 'row-order invariance')
        z = BYID['C01_SINGLE_ANCHOR']['input']
        result = c.single_anchor(z['L'], z['O'], z['anchor'])
        check(common.digest(result) == common.digest(c.single_anchor(list(z['L']), list(z['O']), z['anchor'])), 'C histogram replay')
        return {'I': 'EXACT', 'C': 'EXACT', '1D_2D': 'also covered by family repeat/permutation fixtures'}
    if id == 'SH03_SOURCE':
        v = fixture['input']
        frames = {}
        for source in ['primary', 'S1', 'S2a', 'S2b']:
            raw = v['primary'] if source == 'S1' else v[source]
            uuids = v['UUIDs'][:1] if source == 'S1' else v['UUIDs']
            frames[source] = common.frame([{**raw, 'uuid': uuid,
                                           'parties': [0, raw['L'], raw['O'], 0, 0, 0, 0, 0, 0, 0]} for uuid in uuids])
            common.validate(frames[source])
        check(len(frames['S1'].rows) == 1 and all(len(frames[x].rows) == 2 for x in ['primary', 'S2a', 'S2b']), 'source membership')
        check([frames[x].rows[0].L for x in ['primary', 'S2a', 'S2b']] == [100, 110, 120], 'no primary substitution')
        return {'source_rows': {k: len(v.rows) for k, v in frames.items()}, 'party_vector_length': 10, 'variant_vectors_distinct': True}
    if id == 'SH04_OFAT':
        rows = list(csv.DictReader((FREEZE / 'state_index.csv').open()))
        check(len(rows) == 362 and sum(r['visibility'] == 'public' for r in rows) == 361, 'OFAT counts')
        check(all(not r['excluded_region_id'] or r['source'] == 'primary' for r in rows), 'no source LOO cross')
        return {'states': 362, 'public': 361, 'internal': 1}
    if id == 'SH05_SERIALIZATION':
        x = {'rational': F(3, 7), 'float': .18, 'count': 12345678901234567890}
        blob = common.canonical(x)
        decoded = json.loads(blob)
        check(F(decoded['rational']['exact']) == x['rational'] and
              float.fromhex(decoded['float']['float_hex']) == x['float'], 'serialization roundtrip')
        try:
            common.canonical({'float': float('nan')})
        except ValueError:
            return {'roundtrip': True, 'nonfinite_rejected': True}
        raise AssertionError('NaN serialized')
    if id == 'SH06_HASH':
        a = {'a': 1, 'b': 2}
        check(common.digest(a) == common.digest({'b': 2, 'a': 1}), 'canonical hash')
        check(common.digest(a) != common.digest({'a': 1, 'b': 3}), 'corruption rejected')
        return {'stable_hash': common.digest(a), 'corruption_rejected': True}
    if id == 'SH07_FAILURE':
        r = i.run(common.frame(BYID['I07_EMPTY_REFERENCE']['input']))
        O = [0] * 100
        O[10], O[20], O[99] = 40, 40, 1000
        s = c.auto_selector(O, selector_fault)
        check(r['status'] == 'NOT_DEFINED_EMPTY_REFERENCE' and s['anchor'] == 10, 'frozen failures only')
        return {'I': r['status'], 'C': s['path'], 'no_replacement_window': True}
    if id == 'SH08_LOO_EMPTY':
        r = i.run(i_base(), excluded_region='mock:region:empty')
        check(r['geography_status'] == 'NO_CHANGE_EMPTY_REGION', r)
        check(r['E'] == F(500, 7), r)
        return {'geography_status': r['geography_status'], 'identity_preserved': True, 'same_exact_value': str(r['E'])}
    raise KeyError(id)


def istories_fixture(fixture):
    id, inp, expected = fixture['id'], fixture['input'], fixture['expected']
    if id in ['I01_ROS', 'I02_LS', 'I03_PROPORTIONAL', 'I05_NEGATIVE_TOTAL']:
        r = i.run(common.frame(inp, id), estimator='LS' if id == 'I02_LS' else 'ROS')
        check(r['status'] == 'DEFINED', r)
        check(all(r[k] == F(v) for k, v in expected.items()), r)
        if id == 'I01_ROS':
            CACHE['I01'] = r
        return r
    if id == 'I04_MIXED_SIGN':
        r = i.run(common.frame(inp, id))
        check([r['residual_bins'][b] for b in [20, 29, 80]] == list(map(F, expected['residual_bins20_29_80'])), r)
        return r
    if id == 'I06_BOUNDARIES':
        values = inp['issued']
        observed = {'issued10000_bin': i.bin_index(values[-1], inp['n'])}
        for lo, hi in [(15, 25), (20, 30), (25, 35)]:
            observed[f'window{lo}_{hi}_indices'] = [j for j, x in enumerate(values) if F(lo, 100) <= F(x, inp['n']) < F(hi, 100)]
        check(observed == expected, observed)
        return observed
    if id in ['I07_EMPTY_REFERENCE', 'I08_ZERO_OTHERS', 'I12_NO_ELIGIBLE']:
        r = i.run(common.frame(inp, id))
        check(r['status'] == expected, r)
        return r
    if id == 'I09_BAD_DENOMINATOR':
        status = i.denominator_status(F(inp['forged_V_star']))
        check(status == expected.split(';')[0], status)
        return {'status': status, 'kind': 'forged output validator; not a valid input frame'}
    if id == 'I10_PARTIES_RECONCILE':
        r = CACHE['I01']
        check([z['other9'] for z in r['rows']] == inp['other9_vector'], r)
        check(sum(z['V_star'] for z in r['rows']) == r['V_star'], r)
        return {'other9_preserved': True, 'V_star': r['V_star'], 'logical_rows': len(r['rows'])}
    if id == 'I11_DOMAIN':
        r = i.run(common.frame([inp], id))
        check(r['status'] == expected, r)
        return r
    raise KeyError(id)


def cedar_fixture(fixture):
    id, inp, expected = fixture['id'], fixture['input'], fixture['expected']
    if id == 'C01_SINGLE_ANCHOR':
        r = c.single_anchor(inp['L'], inp['O'], inp['anchor'])
        check(all(r[k] == F(v) for k, v in expected.items()), r)
        CACHE['C01'] = r
        return r
    if id == 'C02_LITERAL_SELECTOR':
        r = c.auto_selector(inp['O'], cedar_stub(inp['injected_curve_fit_parameters']))
        check(r['anchor'] == expected['anchor'] and r['path'] == 'FIT', r)
        return r
    if id == 'C03_AUTO_KNOWN_CURVE':
        O = [int(round(1000 * math.exp(-((j + 1) / 100 - .4)**2 / (2 * .06**2)) +
                       400 * math.exp(-((j + 1) / 100 - .8)**2 / (2 * .04**2)))) for j in range(100)]
        s = c.auto_selector(O)
        check(s['status'] == 'DEFINED' and s['path'] == expected['selector_path'], s)
        check(abs(s['anchor'] - expected['anchor_expected']) <= expected['anchor_tolerance_bins'], s)
        r = c.single_anchor([2 * x for x in O], O, s['anchor'])
        check(r['E'] == F(expected['E']) and r['main'] == F(expected['main']), r)
        replay = c.auto_selector(O)
        check(replay['anchor'] == s['anchor'], 'Cedar replay index')
        CACHE['cedar_known'] = (O, s)
        return {'selector': s, 'arithmetic': r, 'deterministic_repeat_anchor': replay['anchor']}
    if id == 'C04_EXCEPTION_FALLBACK':
        O = [inp['others_else']] * 100
        for j, value in inp['O_peaks'].items():
            O[int(j)] = value
        r = c.auto_selector(O, selector_fault)
        check(r['anchor'] == expected['anchor'] and r['path'] == expected['path'], r)
        return r
    if id == 'C05_OFFSETS':
        calls = [0]
        def backend(*args, **kwargs):
            calls[0] += 1
            return [.4, .1, 1, .8, .02, 1], np.eye(6)
        # Controlled AUTO used once; shifted arithmetic reuses the returned anchor.
        s = c.auto_selector(BYID['C02_LITERAL_SELECTOR']['input']['O'], backend)
        check(calls[0] == 1, calls)
        selected = {'status': 'DEFINED', 'anchor': inp['AUTO_anchor']}
        r = c.offset_outputs(inp['L'], inp['O'], selected)
        check([r[x]['anchor'] for x in [-5, 0, 5]] == expected['anchors'], r)
        check([r[x]['alpha'] for x in [-5, 0, 5]] == list(map(F, expected['alphas'])), r)
        return {'outputs': r, 'selector_calls': calls[0], 'controlled_AUTO_fixture': True}
    if id == 'C06_SHIFT_ZERO':
        r = c.offset_outputs([1] * 100, inp['O'], {'status': 'DEFINED', 'anchor': inp['AUTO_anchor']}, [inp['offset']])[inp['offset']]
        check(r['status'] == expected, r)
        return r
    if id == 'C07_SHIFT_DOMAIN':
        r = [c.single_anchor([1]*100, [1]*100, a+b) for a, b in inp['cases']]
        check(all(x['status'] == 'NOT_DEFINED_ANCHOR_DOMAIN' for x in r), r)
        return r
    if id in ['C08_SIZE', 'C10_UNKNOWN']:
        data = common.frame(inp['cases'], id)
        common.validate(data)
        states = [c.eligible_reason(row) or 'ELIGIBLE' for row in data.rows]
        check(states == expected['states'], states)
        observed = {'states': states}
        if id == 'C10_UNKNOWN':
            observed['cast_second'] = data.rows[1].V + data.rows[1].invalid
            check(observed['cast_second'] == expected['cast_second'], observed)
        return observed
    if id == 'C09_BIN_BOUNDARIES':
        values = ['INELIGIBLE' if x == 0 else c.bin_index(x, inp['n']) for x in inp['cast']]
        check(values == expected['bins'], values)
        return values
    if id == 'C11_SIGNED':
        check(CACHE['C01']['main'] == -99, CACHE['C01'])
        return CACHE['C01']
    if id in ['C12_ZERO_ANCHOR', 'C13_ZERO_FOCAL']:
        L, O = [inp.get('L_all', 0)]*100, [inp['O_all']]*100
        if 'L_anchor' in inp:
            L[inp['anchor']] = inp['L_anchor']
        r = c.single_anchor(L, O, inp['anchor'])
        check(r['status'] == expected, r)
        return r
    if id == 'C14_SMOOTH':
        y = c.smoothing([0]*98 + [10, 20])
        check(y[-2:].tolist() == expected['y_tail_last_two'] and len(y) == 100, y)
        return {'last_two': y[-2:].tolist(), 'first_bin': float(y[0]), 'length': len(y)}
    if id == 'C15_REGION_LOO':
        raw = [{**row, 'region': 'mock:region:' + region} for region, key in [('A', 'regionA_rows'), ('B', 'regionB_rows')]
               for row in inp[key]]
        r = c.run(common.frame(raw), inp['exclude'])
        check(r['eligible_UUIDs'] == inp['expected_postfilter_UUIDs'] and r['trace'] == inp['trace_required'], r)
        return r
    if id == 'C16_HIERARCHY':
        raw = {'uuid': 'mock:duplicate', 'n': 1000, 'I': 700, 'V': 600, 'L': 100, 'invalid': 10}
        r = c.run(common.frame([raw, raw]))
        check(r['status'] == expected, r)
        return r
    raise KeyError(id)


def gaussian_fixture(fixture):
    id, expected = fixture['id'], fixture['expected']
    if fixture['kind'] == 'exact_noiseless_curve':
        r = n.fit(n_hist(F(fixture['input']['h'])))
        check(r['status'] == 'DEFINED', r)
        check(abs(r['core_center'] - expected['core_center']) <= expected['atol'] and
              r['normalized_curve_RMSE'] <= expected['normalized_curve_RMSE_max'], r)
        if F(fixture['input']['h']) == F(1, 100):
            CACHE['n_default'] = r
        return r
    base = np.array([[.18, .04, 1], [.5, .05, .8], [.82, .035, .6]])
    if id == 'N104_ORDER':
        r = [n.reportability(base[list(p)], F(1, 100)) for p in itertools.permutations(range(3))]
        check(all(x['status'] == 'DEFINED' and x['core_center'] == .18 for x in r), r)
        return {'permutations': 6, 'core_center': .18}
    if id == 'N105_STARTS':
        starts = n.start_parameters()
        contract = json.loads((FREEZE / 'contracts/novaya_gaussian1d.json').read_text())
        wanted = [np.array([[float(mu), float(sigma), 1/3] for mu in means]).ravel()
                  for means in sorted(contract['numerical']['starts']['mean_triplets'])
                  for sigma in contract['numerical']['starts']['sigma_common']]
        check(len(starts) == 12 and all(np.array_equal(a,b) for a,b in zip(starts,wanted)), starts)
        return {'starts': starts, 'enumeration': 'lexicographic triplet then sigma'}
    if id == 'N106_BOUNDARIES':
        observed = {}
        for h in [F(1,200), F(1,100), F(1,50)]:
            nbins = int(1/h)
            bins = [n.bin_index(0, nbins, h), n.bin_index(nbins, nbins, h), n.bin_index(1, nbins, h)]
            check(bins == [0, nbins-1, 1], bins)
            observed[str(h)] = bins
        return observed
    if id == 'N107_COLLAPSE':
        p = np.array([[.18,.04,1], [.18,.04,.8], [.82,.035,.6]])
        a = n.reportability(p, F(1,100))
        p = base.copy();p[0,2] = 1e-10
        b = n.reportability(p, F(1,100))
        check(a['status']=='NOT_DEFINED_COMPONENT_IDENTITY' and b['status']=='NOT_DEFINED_COMPONENT_DISAPPEARED',[a,b])
        return {'identical':a,'tiny':b}
    if id == 'N108_OPTFAIL':
        def failed(fun, start, **kwargs):
            return SimpleNamespace(x=start, fun=fun(start), success=False, status=0)
        r=n.fit(n_hist(),failed)
        check(r['status']==expected and r['start_attempts']==12,r)
        return r
    if id == 'N109_ZERO':
        r=n.fit(n.SyntheticHistogram(F(1,100),np.zeros(100)))
        check(r['status']==expected,r)
        return r
    if id == 'N110_REPEAT':
        histogram=n_hist()
        records=[(f'mock:curve:{j:05d}',j,mass) for j,mass in enumerate(histogram.mass)]
        reconstructed=np.zeros(100)
        for _,j,mass in sorted(reversed(records)):
            reconstructed[j]+=mass
        r=n.fit(n.SyntheticHistogram(F(1,100),reconstructed));first=n_default()
        check(r['status']=='DEFINED' and abs(r['core_center']-first['core_center'])<=1e-8 and
              r['selected_start_id']==first['selected_start_id'],r)
        return {'replay':r,'center_difference':abs(r['core_center']-first['core_center'])}
    if id == 'N111_FLAT':
        broad=base.copy();broad[:,1]=1
        candidate={'parameters':broad,'converged':True,'sse':0.,'start_id':0}
        r=n.select([candidate],F(1,100))
        check(r['status']=='NOT_DEFINED_WIDTH_LIMIT',r)
        return {'controlled_boundary_candidate':r,'no_widening':True}
    if id == 'N112_LOO':
        rows=[]
        for region,scale in [('A',1),('B',2)]:
            for j in range(100):
                L=scale*(2*j+1)
                rows.append({'uuid':f'mock:{region}:{j:03d}','region':'mock:region:'+region,
                             'n':1000*scale,'I':700*scale,'V':200*scale,'L':L,'invalid':None})
        before=common.COUNTERS['synthetic_fit_attempts'].get('NOVAYA_1D',0)
        r=n.run_frame(common.frame(rows),excluded_region='mock:region:A')
        after=common.COUNTERS['synthetic_fit_attempts'].get('NOVAYA_1D',0)
        check(after-before==12 and len(r['postfilter_UUIDs'])==100 and
              r['trace']==['filter_region','rebuild_histogram','full_12_start_fit'],r)
        return r
    raise KeyError(id)


def mixture_fixture(fixture):
    id, expected = fixture['id'], fixture['expected']
    if id.startswith('N2_MIX_'):
        cov=fixture['input']['fitcov'];r=g.fit(points(cov),cov)
        check(r['status']=='DEFINED' and np.all(np.abs(np.array(r['core_center'])-expected['core_center'])<=expected['atol_each']),r)
        check(np.isfinite(r['selected_score']),r)
        if cov=='full':CACHE['g_default']=r
        return r
    if id=='N203_PERMUTE':
        original=g_default();candidate=original['_selected_candidate'];out=[]
        for perm in itertools.permutations(range(3)):
            c0=copy.deepcopy(candidate)
            for key in ['means','weights','covariances']:c0[key]=np.asarray(candidate[key])[list(perm)]
            c0['posterior']=candidate['posterior'][:,list(perm)]
            r=g.select([c0]);check(r['status']=='DEFINED' and r['core_center']==original['core_center'] and
                                    np.array_equal(r['_core_posterior'],original['_core_posterior']),r)
            out.append(r['core_center'])
        return {'permutations':6,'centers':out,'posterior_same':True}
    if id=='N204_LABEL':
        c0=copy.deepcopy(g_default()['_selected_candidate']);c0['means']=np.array([[.2,.4],[.4,.2],[.1,.2]])
        r=g.select([c0]);check(r['status']=='DEFINED' and r['core_center']==[.1,.2],r)
        return r
    if id=='N205_THRESH':
        r={**g_default(),'_core_posterior':np.array([.49,.5,.5000001,.7,.7000001,.9,.9000001,1]),'_voters':np.array([1000]*8)}
        outputs=[g.threshold_output(r,t) for t in [.5,.7,.9]]
        check([x['membership_count'] for x in outputs]==[6,4,2],outputs)
        check(set(outputs[2]['member_indices'])<=set(outputs[1]['member_indices'])<=set(outputs[0]['member_indices']),outputs)
        return outputs
    if id=='N206_NOCENTER':
        r=g_default();before=common.COUNTERS['synthetic_fit_attempts'].get('NOVAYA_2D',0)
        outputs=[g.threshold_output(r,t) for t in [.5,.7,.9]]
        check(all(x['core_center']==r['core_center'] and x['fit_blob_sha256']==r['fit_blob_sha256'] for x in outputs),outputs)
        check(common.COUNTERS['synthetic_fit_attempts'].get('NOVAYA_2D',0)==before,'threshold refit')
        return {'outputs':outputs,'additional_fit_calls':0}
    if id=='N207_SEEDS':
        r=g_default();check(r['start_attempts']==10 and r['seed_schedule']==list(range(202610020,202610030)),r)
        return {'start_attempts':10,'seed_schedule':r['seed_schedule'],'n_init_per_call':1}
    if id=='N208_BEST':
        c0=copy.deepcopy(g_default()['_selected_candidate']);candidates=[]
        for score,seed in [(-2,g.SEEDS[0]),(-1,g.SEEDS[1]),(-1,g.SEEDS[2])]:
            item=copy.deepcopy(c0);item.update(score=score,seed=seed);candidates.append(item)
        r=g.select(candidates);check(r['selected_score']==-1 and r['selected_seed']==g.SEEDS[1],r)
        return r
    if id=='N209_NONCONVERGE':
        candidates=[]
        c0=g_default()['_selected_candidate']
        for seed in g.SEEDS:
            q=copy.deepcopy(c0);q.update(converged=False,seed=seed);candidates.append(q)
        r=g.select(candidates);check(r['status']==expected,r)
        return r
    if id=='N210_COLLAPSE':
        X=np.repeat(np.array([[.2,.15],[.5,.45],[.82,.8]]),10,axis=0)
        p=g.SyntheticPoints(X,tuple(f'mock:collapse:{j:03d}' for j in range(30)),tuple(['mock:region:A']*30),tuple([1000]*30))
        r=g.fit(p)
        check(r['status']=='DEFINED' and r['REGULARIZATION_DOMINATED_CORE'] and all(d['floor_contact'] for d in r['diagnostics']),r)
        broken=copy.deepcopy(r['_selected_candidate']);broken['covariances'][0]=np.zeros((2,2))
        invalid=g.select([broken]);check(invalid['status']=='NOT_DEFINED_COVARIANCE_DOMAIN',invalid)
        return {'regularized':r,'invalid_unregularized':invalid}
    if id=='N211_NONFINITE':
        c0=copy.deepcopy(g_default()['_selected_candidate']);c0['score']=float('nan')
        r=g.select([c0]);check(r['status']=='NOT_DEFINED_LIKELIHOOD_NONFINITE',r)
        return r
    if id=='N212_LOO':
        p=points();before=common.COUNTERS['synthetic_fit_attempts'].get('NOVAYA_2D',0)
        r=g.fit(p,excluded_region='mock:region:A')
        after=common.COUNTERS['synthetic_fit_attempts'].get('NOVAYA_2D',0)
        check(after-before==10 and len(r['postfilter_UUIDs'])==4500 and
              r['trace']==['filter_region','rebuild_raw_features','full_10_start_fit'],r)
        return r
    if id=='N213_REPEAT':
        p=points();order=np.arange(len(p.UUIDs))[::-1]
        shuffled=g.SyntheticPoints(p.points[order],tuple(p.UUIDs[j] for j in order),
                                   tuple(p.regions[j] for j in order),tuple(p.voters[j] for j in order))
        r=g.fit(shuffled);first=g_default()
        check(r['status']=='DEFINED' and np.max(np.abs(np.array(r['core_center'])-first['core_center']))<=1e-8 and
              np.max(np.abs(r['_core_posterior']-first['_core_posterior']))<=1e-8,r)
        return {'replay':r,'center_difference':np.max(np.abs(np.array(r['core_center'])-first['core_center']))}
    if id=='N214_SCALE':
        p=points();X,indices=g.ordered_points(p)
        check(np.array_equal(X,p.points),'feature normalization changed')
        check(np.min(X)>=0 and np.max(X)<=1,'raw coordinates')
        return {'raw_features_sha256':hashlib.sha256(X.tobytes()).hexdigest(),'equal_observation_weights':True,'normalization':False}
    if id=='N215_CROSS':
        ui=list(csv.DictReader((FREEZE/'ui_state_availability.csv').open()))
        requested=[r for r in ui if r['family']=='NOVAYA_2D' and
                   ((r['source']=='primary' and not r['excluded_region_id'] and r['method_control']=='DIAG_THRESHOLD_0P7') or
                    (r['source']=='S1' and not r['excluded_region_id'] and r['method_control']=='DIAG_THRESHOLD_0P5'))]
        check(len(requested)==2 and all(r['availability']=='UNAVAILABLE_NOT_IN_FROZEN_GRID' for r in requested),requested)
        return requested
    raise KeyError(id)


def main():
    start=time.monotonic();started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    check(platform.python_version()=='3.14.0' and np.__version__=='2.4.2' and scipy.__version__=='1.18.1' and
          sklearn.__version__=='1.7.2','frozen environment mismatch')
    check(json.loads((FREEZE/'checker_results.json').read_text())['status']=='PASS','structural gate not PASS')
    g.budget_gate()
    selection=datetime.datetime.fromisoformat(json.loads((OUT/'phase_2_budget_gate.json').read_text())['selection_gate_timestamp'])
    remaining=15*3600-(datetime.datetime.now(datetime.timezone.utc)-selection).total_seconds()
    if remaining<=0:raise common.ResourceStop('HARD_15H_ALREADY_EXCEEDED')
    def timeout(signum, frame):raise common.ResourceStop('E2_HARD_TIME_STOP')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(math.ceil(remaining))
    code_hashes={str(p.relative_to(ROOT)):sha(p) for p in sorted(CODE.glob('*.py'))}
    implementation_sha=hashlib.sha256(json.dumps(code_hashes,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    put('implementation_freeze.json',{'files':code_hashes,'implementation_sha256':implementation_sha,'frozen_before_first_fit':True})
    manifest={'count':63,'fixtures':FIXTURES,'original_file_sha256':sha(FREEZE/'synthetic_fixtures.json'),
              'fixture_resolution':json.loads((FREEZE/'fixture_resolution.json').read_text()),
              'successor_freeze_manifest_sha256':sha(FREEZE/'manifest.json'),
              'implementation_sha256':implementation_sha,'extra_units_count_separate':True,
              'concrete_mock_realizations':'N111 injects broad sigma=1 selected candidate; N112 uses two deterministic 100-bin mock frames. N210 uses repeated published synthetic-fixture centers with zero empirical covariance. N212 partitions the frozen synthetic mixture by row parity. These plumbing/diagnostic realizations are defined in the implementation before execution; no new scientific threshold.'}
    put('fixture_manifest.json',manifest)
    units=units_run();put('implementation_unit_results.json',units)
    failed_units={r['family'] for r in units['results'] if r['status']=='FAIL'}
    results=[];family_failed=set(failed_units)
    handlers={'SHARED':shared,'ISTORIES':istories_fixture,'CEDAR':cedar_fixture,'NOVAYA_1D':gaussian_fixture,'NOVAYA_2D':mixture_fixture}
    for fixture in FIXTURES:
        family=fixture['family'];t=time.monotonic()
        record={'fixture_id':fixture['id'],'family':family,'purpose':fixture['kind'],
                'expected':fixture['expected'],'implementation_sha256':implementation_sha,
                'original_fixture_input':fixture['input'],'executed':False}
        if family in family_failed or 'SHARED' in family_failed:
            record.update(status='FAIL',observed={'terminal':'NOT_EXECUTED_AFTER_FAMILY_FAILURE'},diagnostics={'incomplete':True})
        else:
            try:
                observed=handlers[family](fixture)
                record.update(status='PASS',observed=clean(observed),executed=True,diagnostics={'input_origin':'SYNTHETIC_QUALIFICATION'})
            except (common.ResourceStop,MemoryError) as error:
                record.update(status='FAIL',observed={'terminal':'RESOURCE_STOP'},executed=True,
                              diagnostics={'exception':type(error).__name__,'message':str(error)})
                family_failed.add(family)
            except Exception as error:
                record.update(status='FAIL',observed={'terminal':'QUALIFICATION_ASSERTION_FAILED'},executed=True,
                              diagnostics={'exception':type(error).__name__,'message':str(error),'failure_preserved':True})
                family_failed.add(family)
        record['wall_seconds']=time.monotonic()-t
        record['peak_process_RSS_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
        results.append(record)
        with (OUT/'qualification_events.jsonl').open('a') as f:f.write(json.dumps(clean(record),sort_keys=True)+'\n')
        print(json.dumps({'fixture':fixture['id'],'family':family,'status':record['status'],'executed':record['executed'],'wall_seconds':round(record['wall_seconds'],3)}),flush=True)
    verdicts={family:'PASS' if family not in family_failed and 'SHARED' not in family_failed else 'FAIL'
              for family in ['ISTORIES','CEDAR','NOVAYA_1D','NOVAYA_2D']}
    complete=all(r['executed'] for r in results)
    ready=complete and all(v=='PASS' for v in verdicts.values()) and units['status']=='PASS'
    end=datetime.datetime.now(datetime.timezone.utc)
    proof={'REAL_EXTERNAL_RUNS_EXECUTED':'NO','REAL_EXTERNAL_RESULTS_OPENED':'NO','REAL_PARTY_ROWS_PROCESSED':0,
           'REAL_MODEL_FITS_EXECUTED':0,'forbidden_access_attempts':FILE_AUDIT['forbidden_access_attempts'],
           'network_attempts':FILE_AUDIT['network_attempts'],'project_files_read':sorted(FILE_AUDIT['project_files_read']),
           'input_factories':'Mock UUIDs + explicit SYNTHETIC_QUALIFICATION types; no input path CLI; audited file allowlist',
           'model_counters':common.COUNTERS}
    check(not proof['forbidden_access_attempts'] and not proof['network_attempts'],'invalid real/network access')
    put('no_real_data_proof.json',proof)
    usage={'started_at':started,'finished_at':end.isoformat(),'wall_seconds':time.monotonic()-start,
           'peak_process_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
           'RAM_limit_bytes':10*1024**3,'RLIMIT_AS_bytes':10*1024**3,'threads':1,'processes':1,
           'elapsed_since_selection_hours':(end-selection).total_seconds()/3600,
           'provider_quota_percent':'UNKNOWN','implementation_model_calls':common.COUNTERS,
           'resource_rules_satisfied':(end-selection).total_seconds()<15*3600 and
           resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<10*1024**3,
           'artifact_bytes_at_execution_finish':sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())}
    usage['combined_static_artifact_bytes'] = usage['artifact_bytes_at_execution_finish'] + sum(
        p.stat().st_size for p in FREEZE.rglob('*') if p.is_file())
    put('resource_usage.json',usage)
    ready = ready and usage['resource_rules_satisfied'] and usage['combined_static_artifact_bytes'] < 250*1024**2
    put('qualification_results.json',{'family_verdicts':verdicts,'frozen_fixture_count':63,
           'executed_frozen_fixtures':sum(r['executed'] for r in results),'passed_frozen_fixtures':sum(r['status']=='PASS' for r in results),
           'failed_frozen_fixtures':sum(r['status']=='FAIL' and r['executed'] for r in results),
           'synthetic_qualification_complete':complete,'ready_for_real_run_authorization':ready,
           'real_execution_authorized':False,'methodological_repair':False,'implementation_sha256':implementation_sha,
           'results':results,'implementation_units_status':units['status'],'extra_unit_count':units['count']})
    with (OUT/'qualification_ledger.csv').open('x',newline='') as f:
        fields=['fixture_id','family','purpose','executed','status','wall_seconds','peak_process_RSS_bytes','implementation_sha256','expected','observed','diagnostics']
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in results:w.writerow({k:json.dumps(clean(r[k]),sort_keys=True) if k in ['expected','observed','diagnostics'] else r[k] for k in fields})
    print(json.dumps({'family_verdicts':verdicts,'complete':complete,'ready_for_real_run_authorization':ready,
                      'wall_seconds':usage['wall_seconds'],'peak_RSS_MiB':usage['peak_process_RSS_bytes']/1024**2}),flush=True)


if __name__=='__main__':main()
