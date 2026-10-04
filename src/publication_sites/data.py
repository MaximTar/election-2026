"""Pure stored-artifact reader and static serializer. No row providers or estimators."""
import csv
import gzip
import hashlib
import json
import re
import sys
import zlib
from collections import Counter
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'publication/sites/v1'
EVIDENCE = ROOT / 'outputs/sites_publication_data/20261004_v1'
OLD = ROOT / 'outputs/smz_publication_package/20261001_v1'
REVEALED = ROOT / 'outputs/smz_run01_reveal/20261001_v1'
READER = ROOT / 'outputs/smz_v2_external_joint_reveal/20261003_v1'
CLOSURE = ROOT / 'outputs/smz_v2_external_closure/20261003_v1'
INTERNAL = 'ISTORIES__primary__DEFAULT__LS_B_WINDOW'
METHOD_MAP = {'ISTORIES':'vazhnye_istorii', 'CEDAR':'cedar',
              'NOVAYA_1D':'novaya_1d', 'NOVAYA_2D':'novaya_2d',
              'NOVAYA_CONVENTIONAL':'novaya_conventional',
              'NOVAYA_OVERLAP_CORE':'novaya_overlap_core'}
TYPES = {'abc':'TEN_PARTY_CONDITIONAL_SCENARIO', 'd':'FOCAL_PARTY_CONDITIONAL_SCENARIO',
         'cedar':'SIGNED_EXCESS_OVER_OBSERVED_FOCAL',
         'vazhnye_istorii':'SCENARIO_FOCAL_VALID_SHARE',
         'novaya_1d':'FITTED_CORE_CENTER', 'novaya_2d':'FITTED_CORE_CENTER_AND_MEMBERSHIP'}
DENOMINATORS = {'abc':'SCENARIO_VALID_BY_SCOPE', 'd':'SCENARIO_VALID_BY_SCOPE',
                'cedar':'OBSERVED_FOCAL_VOTES_IN_NATIVE_FRAME',
                'vazhnye_istorii':'SCENARIO_VALID_IN_ELIGIBLE_FRAME',
                'novaya_1d':'NOT_A_NATIONAL_SHARE', 'novaya_2d':'NOT_A_NATIONAL_SHARE'}
if hasattr(sys, 'set_int_max_str_digits'):
    sys.set_int_max_str_digits(0)  # Exact stored aggregate integers, never executed arithmetic.

def need(ok, message):
    if not ok:
        raise ValueError('PUBLICATION_BLOCKER: ' + message)

_HASH_CACHE = {}
def sha(path):
    path=Path(path)
    s=path.stat()
    key=(str(path.absolute()),s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    if key in _HASH_CACHE:return _HASH_CACHE[key]
    with path.open('rb') as f:
        value=hashlib.file_digest(f, 'sha256').hexdigest() if hasattr(hashlib, 'file_digest') else hashlib.sha256(f.read()).hexdigest()
    after=path.stat()
    need((s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'file changed during hashing')
    _HASH_CACHE[key]=value
    return value

def read(path):
    return json.loads(Path(path).read_text())

def rows(path):
    with Path(path).open(newline='') as f:
        return list(csv.DictReader(f))

def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()

def ref(path, pointer=None):
    value = {'path':str(Path(path).relative_to(ROOT)), 'sha256':sha(path), 'technical_only':True}
    if pointer is not None:
        value['pointer'] = pointer
    return value

def verify_inputs():
    # Archive-aware resolution is ONLY for sealed historical governance pointers.
    pointer = (ROOT/'src/smz_stage_registry.py').read_text()
    package = re.search(r"PACKAGE=ROOT/'([^']+)'",pointer).group(1)
    registry_path = ROOT/package/'stage_registry.json'
    registry_hash = re.search(r"REGISTRY_SHA='([a-f0-9]+)'",pointer).group(1)
    need(sha(registry_path)==registry_hash,'current governance registry hash')
    reg = read(registry_path)
    current = reg
    while current.get('previous_registry'):
        old = ROOT/current['previous_registry']
        need(sha(old)==current['previous_registry_sha256'],'registry predecessor hash')
        previous = read(old)
        need(current['stages'][:len(previous['stages'])]==previous['stages'],'registry append-only prefix')
        current = previous
    pins = read(EVIDENCE/'input_bindings.json')
    membership = {}
    for item in pins['manifests']:
        manifest_path=ROOT/item['path']
        need(sha(manifest_path)==item['sha256'],'authoritative manifest hash')
        for path,expected in read(manifest_path)['files'].items():
            membership.setdefault(path,set()).add(expected)
    # All consumed sources must belong to a pinned manifest. Unconsumed regional
    # detail sidecars are not rebuilt/read by the client export. The complete before/
    # after protected inventory independently verifies immutability at final check.
    for path, expected in pins['files'].items():
        need(expected in membership.get(path,set()),'consumed dependency absent from authoritative manifest '+path)
        need(sha(ROOT/path) == expected, 'frozen input hash ' + path)
    return pins

def exact_decode(blob, projection=None):
    """Decode already-revealed canonical bytes to JSON-safe exact values, no kernel import.

    Fraction tags are copied directly; there is no gcd, arithmetic or reconstruction.
    This is the qualified codec's documented wire format (n/t/f/+/-/s/b/r/m/l/d).
    """
    b = zlib.decompress(blob)
    pos = 0
    def u():
        nonlocal pos
        value = shift = 0
        while True:
            c = b[pos]; pos += 1
            value |= (c & 127) << shift
            if c < 128:
                return value
            shift += 7
    def skip():
        nonlocal pos
        tag=b[pos:pos+1];pos+=1
        if tag in (b'n',b't',b'f'):return
        if tag in (b'+',b'-',b's',b'b'):
            length=u();pos+=length;return
        if tag in (b'r',b'm'):
            skip();skip();return
        if tag in (b'l',b'd'):
            length=u()
            for _ in range(length*(2 if tag==b'd' else 1)):skip()
            return
        raise ValueError('Invalid exact codec tag while skipping')
    def get(wanted=None):
        nonlocal pos
        tag = b[pos:pos+1]; pos += 1
        if tag == b'n': return None
        if tag in (b't', b'f'): return tag == b't'
        if tag in (b'+', b'-', b's', b'b'):
            n = u(); v = b[pos:pos+n]; pos += n
            if tag == b's': return v.decode()
            if tag == b'b': return {'bytes_hex':v.hex()}
            return int.from_bytes(v, 'big') * (-1 if tag == b'-' else 1)
        if tag == b'r':
            return {'numerator':str(get()), 'denominator':str(get())}
        if tag == b'm': return {'status':get(), 'reason':get()}
        if tag == b'l': return [get() for _ in range(u())]
        if tag == b'd':
            result={}
            for _ in range(u()):
                key=get()
                if wanted is None:result[key]=get()
                elif key in wanted:result[key]=get(wanted[key])
                else:skip()
            return result
        raise ValueError('Invalid exact codec tag')
    result = get(projection)
    need(pos == len(b), 'exact codec trailing bytes')
    return result

def guards(method):
    return {'value_kind':TYPES[method], 'denominator_kind':DENOMINATORS[method],
            'is_counterfactual_national_share':method in ('abc','d','vazhnye_istorii'),
            'national_share_scope':'FULL_FRAME_IDENTITY_EXTENSION_ONLY' if method in ('abc','d') else 'ELIGIBLE_SCENARIO_FRAME' if method=='vazhnye_istorii' else 'NOT_APPLICABLE',
            'is_confidence_interval':False, 'is_true_result':False,
            'may_average_across_methods':False, 'source_correctness_ranking_allowed':False,
            'loo_interpretation':'SINGLE_REGION_INFLUENCE_ONLY',
            'outside_support_identity_means_zero_effect':False,
            'membership_probability_semantics':'MODEL_COMPONENT_ONLY' if method=='novaya_2d' else 'NOT_APPLICABLE',
            'honesty_or_fraud_probability':False,
            'undefined_is_zero':False,
            'sensitivity_kind':'REFERENCE_SPECIFICATION' if method=='vazhnye_istorii' else 'ANCHOR_SPECIFICATION_STRESS_TEST' if method=='cedar' else 'FROZEN_SPECIFICATION_GRID',
            'common_complete_case_frame':False}

def display_number(v, percent=False):
    # Display transformation only. Exact binary64/rational is never replaced.
    if isinstance(v, dict) and 'exact' in v:
        f = Fraction(v['exact']); n, d = f.numerator, f.denominator
    elif isinstance(v, dict) and 'numerator' in v:
        n, d = int(v['numerator']), int(v['denominator'])
    elif isinstance(v, dict) and 'float_hex' in v:
        n, d = float.fromhex(v['float_hex']).as_integer_ratio()
    else:
        n, d = v, 1
    with localcontext() as c:
        c.prec = 50
        dec = Decimal(n) / Decimal(d)
        if percent: dec *= 100
        return format(dec.quantize(Decimal('0.0001'), rounding=ROUND_HALF_EVEN), 'f')

def pack_exact(value):
    """Lossless storage-only interning of repeated huge integer strings."""
    pool=[];index={}
    def intern(text):
        if text not in index:index[text]=len(pool);pool.append(text)
        return index[text]
    def visit(x):
        if isinstance(x,dict):
            if set(x)=={'numerator','denominator'}:
                return {'numerator_ref':intern(x['numerator']),'denominator_ref':intern(x['denominator'])}
            return {k:visit(v) for k,v in sorted(x.items())}
        if isinstance(x,list):return [visit(v) for v in x]
        return x
    result=visit(value)
    result['integer_strings']=pool
    return result

def unpack_exact(value):
    pool=value['integer_strings']
    def visit(x):
        if isinstance(x,dict):
            if set(x)=={'numerator_ref','denominator_ref'}:
                return {'numerator':pool[x['numerator_ref']],'denominator':pool[x['denominator_ref']]}
            return {k:visit(v) for k,v in x.items() if k!='integer_strings'}
        if isinstance(x,list):return [visit(v) for v in x]
        return x
    return visit(value)

def baseline():
    registry = {r['number_id']:r for r in read(OLD/'numbers_registry.json')['records']}
    b = read(OLD/'canonical_data/baselines.json')
    result = {}
    for source, record in b.items():
        if source not in ('primary','S1','S2a','S2b'): continue
        def resolve(identifier):
            number = registry[identifier]
            need(number['exact_value']['kind'] in ('INTEGER','RATIONAL'), 'non-inline baseline exact value')
            return {'exact':{k:number['exact_value'][k] for k in ['numerator','denominator']},
                    'display':number['display_numeric'], 'display_format':number['format_id']}
        result[source] = {'mode':'REPORTED_BASELINE', 'numbers':{k:resolve(v) for k,v in record['numbers'].items()},
                          'parties':[{'party_id':r['party'],'count':resolve(r['count']), 'share':resolve(r['share'])} for r in record['all_parties']]}
    return result

def build_abc_d(files):
    inventory = read(REVEALED/'canonical_cell_inventory.json')
    contract = read(OLD/'canonical_data/contract.json')
    need(contract['cell_count']==1620 and contract['runtime_requires_Layer_R'] is False, 'canonical publication eligibility')
    canonical = json.loads(gzip.decompress((OLD/'canonical_data/cells.json.gz').read_bytes()))
    parents = {c['id']:c for c in canonical['cells']}
    strata = rows(ROOT/'outputs/smz_run01_interpretation/20261001_v1/D_stratum_diagnostics.csv')
    out = {'abc':[], 'd':[]}
    for number,c in enumerate(inventory['cells']):
        method = 'abc' if c['parameters']['family']=='ABC' else 'd'
        parent = parents[c['id']]
        params = c['parameters']
        controls = {'design_id':params['spec'], 'lambda_quarters':params['lambda_quarters'], 'mu_quarters':params['mu_quarters']} if method=='abc' else {'specification':params['spec']}
        suffix = f"{params['spec']}__l{params['lambda_quarters']}__m{params['mu_quarters']}" if method=='abc' else params['spec']
        state_id = f"{method}__{c['source']}__{suffix}"
        entry = c['exact_result']; path = REVEALED/entry['path']
        need(sha(path)==entry['physical_sha256'], 'exact record bytes ' + c['id'])
        fields = ['scenario_parties','scenario_valid','shares','source_parties','source_shares','source_valid','scenario_issued','delta']
        wanted={k:None for k in fields}
        projection={'scopes':{'full':wanted,'native':wanted}} if method=='abc' else {'extended':wanted,'native':wanted}
        z = exact_decode(path.read_bytes(),projection)
        scoped = {}
        for scope in ('full','native'):
            original = z['scopes'][scope] if method=='abc' else z['extended' if scope=='full' else 'native']
            scoped[scope] = {k:original[k] for k in fields if k in original}
        exact = {'state_id':state_id, 'method_id':method, 'result_type':TYPES[method], 'party_order':inventory['party_order'], 'scopes':scoped,
                 'aggregate_exact':{'full':c['full'],'native':c['native']}}
        exact_path = 'exact/'+state_id+'.json.gz'
        compact=pack_exact(exact)
        need(unpack_exact(compact)==exact,'exact integer-string pool roundtrip')
        files[exact_path] = gzip.compress(encode(compact), compresslevel=6, mtime=0)
        stratum_statuses = []
        if method=='d':
            stratum_statuses = [{'group_id':r['stratum'], 'status':r['status'], 'reason':r['reason'],
                                'fit_UIKs':int(r['fit_UIKs']), 'tail_UIKs':int(r['tail_UIKs']),
                                'informative_fit_bins':int(r['informative_fit_bins']),
                                'candidate_defined':r['candidate_defined']=='True', 'included_in_native':r['included_in_native']=='True'}
                               for r in strata if r['source']==c['source'] and r['spec']==params['spec']]
        result = {'exact_file':exact_path, 'exact_file_sha256':hashlib.sha256(files[exact_path]).hexdigest(),
                  'exact_encoding':'GZIP_JSON_RATIONAL_INTEGER_STRING_POOL_V1',
                  'display_vectors':{scope:{k:v for k,v in vector.items() if k!='exact_values'} for scope,vector in parent['party_vectors_P_display'].items()},
                  'undefined_fields':parent['undefined']}
        state = {'state_id':state_id, 'method_id':method, 'source_version':c['source'],
                 'controls':controls, 'geography':{'mode':'DEFAULT','excluded_region_id':None},
                 'availability':'AVAILABLE', 'visibility':'PUBLIC', 'status':c['status'],
                 'result_type':TYPES[method], 'result':result,
                 'coverage':{'coverage_type':'NATIVE_SUPPORT_AND_FULL_FRAME_IDENTITY_EXTENSION', 'native':parent['support'],
                             'selected_targets':c['selected_targets'],'supported_targets':c['supported_targets']},
                 'support':{'group_statuses':stratum_statuses} if method=='d' else {},
                 'interpretation_guards':guards(method), 'warnings':[],
                 'provenance':{'original_state_id':c['id'],'exact_record':ref(path),
                               'omitted_pipeline_detail_fields':['composition','intensity','interaction'],
                               'inventory':ref(REVEALED/'canonical_cell_inventory.json'),
                               'publication_contract':ref(OLD/'canonical_data/contract.json')}}
        if method=='abc': state['aliases']=c['aliases']
        out[method].append(state)
        if (number+1)%200==0:print('Stored scenario records projected: '+str(number+1)+'/1620',file=sys.stderr,flush=True)
    need(len(out['abc'])==1600 and len(out['d'])==20, 'ABC/D exact inventory')
    return out, inventory['party_order']

def external_controls(state):
    method = METHOD_MAP[state['family']]
    ctl = json.loads(state['method_control_values'])
    if method=='vazhnye_istorii':
        window = ctl.get('window_percent')
        if window is None: window = [int(Fraction(t)*100) for t in ctl.get('window',['1/5','3/10'])]
        return {'reference_window_percent':window,'boundary':'LEFT_CLOSED_RIGHT_OPEN', 'coefficient':'RATIO_OF_SUMS','residual':'SIGNED'}
    if method=='cedar':
        if 'fixed_anchor_right_edge_percent' in ctl: return {'anchor_mode':'FIXED','anchor_right_edge_percent':ctl['fixed_anchor_right_edge_percent']}
        # Gate's exact fixed grid may store bin index directly.
        if 'fixed_anchor' in ctl: return {'anchor_mode':'FIXED','anchor_right_edge_percent':ctl['fixed_anchor']+1}
        if 'anchor_bin' in ctl: return {'anchor_mode':'FIXED','anchor_right_edge_percent':ctl['anchor_bin']+1}
        return {'anchor_mode':'AUTO','auto_offset_bins':ctl.get('auto_offset_bins',0)}
    if method=='novaya_1d':
        h = ctl.get('bin_width','1/100')
        return {'K':3, 'bin_width':h, 'sigma_min':str(Fraction(h)/2), 'histogram_mass':'FOCAL_PARTY_VOTES','objective':'UNWEIGHTED_MIDPOINT_OLS'}
    return {'K':3,'covariance':ctl.get('covariance','full'),'membership_threshold':ctl.get('threshold','1/2'),
            'membership_operator':'>','coordinate_scaling':'RAW','observation_weight':'EQUAL_UIK'}

def build_external():
    records = read(READER/'stored_results.json')['records']
    need(len(records)==445, 'external frozen count')
    public = [r for r in records if r['state']['visibility']=='public']
    need(len(public)==444 and {r['state']['state_id'] for r in records if r not in public}=={INTERNAL}, 'visibility inventory')
    support_rows = {r['state_id']:r for r in rows(CLOSURE/'cedar_anchor_support.csv')}
    out = {k:[] for k in ('cedar','vazhnye_istorii','novaya_1d','novaya_2d')}
    for r in public:
        s = r['state']; z = r['stored_result']; method = METHOD_MAP[s['family']]
        old_id = s['state_id']; suffix = old_id.split('__DEFAULT__')[-1] if '__DEFAULT__' in old_id else old_id.split('__')[-1]
        excluded = s.get('excluded_region_id') or None
        state_id = f"{method}__{s['source']}__{'LOO_'+excluded if excluded else 'DEFAULT'}__{suffix}"
        controls = external_controls(s)
        keys = {'vazhnye_istorii':['share','E','L_star','V_star','alpha','scenario_party_totals'],
                'cedar':['main','E','alpha','anchor'],
                'novaya_1d':['core_center'],
                'novaya_2d':['core_center','threshold_output','fit_blob_sha256']}[method]
        result = {'exact_stored':{k:z[k] for k in keys if k in z}, 'display':{}}
        if method in ('vazhnye_istorii','cedar','novaya_1d'):
            metric = {'vazhnye_istorii':'share','cedar':'main','novaya_1d':'core_center'}[method]
            if metric in z:result['display'][metric+'_percent']=display_number(z[metric],True)
        else:
            if 'core_center' in z:
                result['display']['issued_over_registered_center_percent']=display_number(z['core_center'][0],True)
                result['display']['focal_center_percent']=display_number(z['core_center'][1],True)
        diagnostics = {k:z[k] for k in ['flags','sigma_min','normalized_curve_RMSE','selected_sse','bounded_global_optimum_claimed','REGULARIZATION_DOMINATED_CORE','diagnostics','warning_types'] if k in z}
        support = {}
        if method=='vazhnye_istorii':support={'reference_UIKs':z.get('reference_count'),'scenario_frame_UIKs':z['input_coverage']['eligible_UIKs']}
        if method=='cedar':
            a = support_rows[old_id]
            need(a['diagnostic_status']=='AVAILABLE', 'Cedar support unavailable')
            support = {'anchor_bin_index':int(a['anchor_bin_index']), 'anchor_right_edge_percent':int(a['anchor_right_edge_percent']),
                       'anchor_interval':a['anchor_interval'], 'anchor_selection_type':a['anchor_selection_type'],
                       'anchor_UIKs':int(a['anchor_UIKs']), 'anchor_L':int(a['anchor_L']),
                       'anchor_O':int(a['anchor_O']), 'anchor_cast':int(a['anchor_cast']),
                       'diagnostic_type':'NON_MODEL_READER_DERIVED', 'diagnostic_provenance':ref(CLOSURE/'cedar_anchor_support.csv')}
        geography={'mode':'LEAVE_ONE_REGION_OUT' if excluded else 'DEFAULT','excluded_region_id':excluded}
        state = {'state_id':state_id,'method_id':method,'source_version':s['source'],'controls':controls,
                 'geography':geography, 'availability':'AVAILABLE','visibility':'PUBLIC','status':z['status'],
                 'result_type':TYPES[method],'result':result,'coverage':{'coverage_type':'FAMILY_SPECIFIC_NATIVE_ELIGIBILITY', **z['input_coverage']},
                 'support':support,'diagnostics':diagnostics,'interpretation_guards':guards(method),'warnings':[],
                 'provenance':{'original_state_id':old_id, 'stored_packet':{'path':r['packet_path'],'sha256':r['packet_sha256'],'technical_only':True},
                               'reader':ref(READER/'stored_results.json'), 'frozen_specification_id':s['family_spec_id']}}
        if method=='novaya_2d':
            state['fit_relationship']={'reuse':ctl_threshold_only(s),'fit_id':z.get('fit_blob_sha256'),
                                       'threshold_changes':'MEMBERSHIP_AND_COVERAGE_ONLY',
                                       'center_invariance_is_independent_robustness':False}
        out[method].append(state)
    need({k:len(v) for k,v in out.items()}=={'cedar':161,'vazhnye_istorii':102,'novaya_1d':90,'novaya_2d':91},'public family counts')
    return out

def ctl_threshold_only(s):
    return '__THRESHOLD_0P' in s['state_id']

def catalog(groups):
    labels = {'abc':'Локальные сценарии A/B/C','d':'Сценарий D','cedar':'Cedar: пропорциональный остаток',
              'vazhnye_istorii':'«Важные истории»: сценарная доля','novaya_1d':'«Новая газета»: одномерный центр компоненты',
              'novaya_2d':'«Новая газета»: двумерный центр и принадлежность',
              'novaya_conventional':'«Новая газета»: обычная конструкция Шпилькина',
              'novaya_overlap_core':'«Новая газета»: пересечение распределений / ядро'}
    source_index = read(CLOSURE/'external_methods_source_index.json')
    entries = {METHOD_MAP.get(e['method'],e['method']):e for e in source_index['entries']}
    # Preserve exact local method names if the index uses longer card identifiers.
    for e in source_index['entries']:
        if e['method'].startswith('NOVAYA_CONVENTIONAL'):entries['novaya_conventional']=e
        if e['method'].startswith('NOVAYA_OVERLAP'):entries['novaya_overlap_core']=e
    methods=[]
    public_axes={'abc':{'design_id','lambda_quarters','mu_quarters'},'d':{'specification'},
                 'cedar':{'anchor_mode','auto_offset_bins','anchor_right_edge_percent'},
                 'vazhnye_istorii':{'reference_window_percent'},'novaya_1d':{'bin_width'},
                 'novaya_2d':{'covariance','membership_threshold'}}
    for method in labels:
        states=groups.get(method,[]); card=method not in groups
        e=entries.get(method)
        need(method in ('abc','d') or e is not None,'source index method '+method)
        controls={}
        for s in states:
            for k,v in s['controls'].items():
                if k in public_axes[method]:controls.setdefault(k,{})[json.dumps(v,sort_keys=True)]=v
        m={'method_id':method,'label_ru':labels[method],'editorial_copy_status':'pending',
           'execution_status':'card_only' if card else 'executable',
           'result_type':'NO_PROJECT_EXECUTION' if card else TYPES[method],
           'result_semantics':'PUBLISHED_APPROACH_ONLY_NO_PROJECT_NUMERIC_RESULT' if card else TYPES[method],
           'focal_party_behavior':'SYMMETRIC_TEN_PARTY' if method=='abc' else 'FOCAL_PARTY_ONLY',
           'focal_party_id':None if method=='abc' else 'er',
           'available_controls':{k:[v for _,v in sorted(values.items())] for k,values in sorted(controls.items())},
           'availability_model':'EXPLICIT_STATE_LIST_ONLY', 'state_file':None if card else 'states/'+method+'.json',
           'available_state_count':len(states), 'coverage_semantics':'NO_EXECUTION' if card else 'NATIVE_SUPPORT_AND_SOURCE_FRAME_ARE_DISTINCT',
           'available_source_versions':sorted({s['source_version'] for s in states}),
           'available_geographies':[json.loads(k) for k in sorted({json.dumps(s['geography'],sort_keys=True) for s in states})],
           'available_scope_outputs':[] if card else ['full','native'] if method in ('abc','d') else ['native'],
           'availability_policy':{'unsupported_combination':'UNAVAILABLE_NOT_IN_FROZEN_GRID','silent_fallback':False,'reset_requires_visible_action':True},
           'interpretation_guards':{'project_result_available':False} if card else guards(method),
           'source_references':[] if e is None else [e['public_source_url']] if e.get('public_source_url') else [],
           'fidelity_status':e['fidelity_status'] if e else 'PROJECT_SCENARIO',
           'known_source_gaps':e['known_unresolved_public_source_gaps'] if e else [],
           'provenance':[] if e is None else [{'path':e['reconstruction_path'],'sha256':e['reconstruction_sha256'],'technical_only':True}]}
        if method=='novaya_2d':m['coordinate_labels']=['issued ballots / registered voters','focal party votes / valid votes']
        if method=='novaya_1d':m['bin_width_test']='HISTOGRAM_DISCRETIZATION_AND_SIGMA_LOWER_BOUND_H_OVER_2'
        if method=='cedar':
            m['input_coordinate_semantics']={'coordinate':'(valid votes + known invalid ballots) / registered voters',
                'cast':'valid + known_invalid','anchor_O':'cast - focal_party_votes; includes known invalid ballots',
                'registered_minimum':'STRICTLY_GREATER_THAN_100','unknown_invalid':'EXCLUDED_FROM_NATIVE_FRAME'}
        if method=='vazhnye_istorii':
            m['input_coordinate_semantics']={'coordinate':'issued ballots / registered voters','O':'valid_votes - focal_party_votes',
                'coefficient':'RATIO_OF_SUMS','default_window_percent':[20,30],'window_boundary':'LEFT_CLOSED_RIGHT_OPEN'}
        if method=='novaya_1d':
            m['input_coordinate_semantics']={'coordinate':'focal party votes / valid votes','histogram_mass':'FOCAL_PARTY_VOTE_MASS',
                'fit':'SUM_OF_THREE_UNNORMALIZED_GAUSSIANS_UNWEIGHTED_MIDPOINT_OLS','is_likelihood_gmm':False}
        if method=='abc':m['family_slices']={'A':'mu_quarters=0','B':'lambda_quarters=0','C':'full stored lambda/mu grid'}
        if method=='d':m['symmetric_ten_party_reconstruction']=False
        if method in ('abc','d'):
            frozen=read(OLD/'model_metadata.json')
            m['provenance']=[ref(OLD/'model_metadata.json'),ref(OLD/'canonical_data/contract.json')]
            if method=='abc':
                defaults=next(x['defaults'] for x in frozen['models'] if x['id']=='C')
                design=defaults['design_id']
                m['predeclared_default_states']={'A':f'abc__primary__{design}__l4__m0','B':f'abc__primary__{design}__l0__m4','C':f'abc__primary__{design}__l4__m4'}
            else:
                default_spec=next(x['defaults']['spec'] for x in frozen['models'] if x['id']=='D')
                m['predeclared_default_states']={'D':f'd__primary__{default_spec}'}
        elif not card:m['predeclared_default_states']={'default':f'{method}__primary__DEFAULT__B'}
        m['default_implies_scientific_preference']=False
        if card:m['notice_ru']='Опубликованный подход описан; расчёт в проекте не выполнялся.'
        methods.append(m)
    return {'api_version':'1','project_id':'election-2026','methods':methods}

def build_sources():
    meta=read(OLD/'source_metadata.json')
    region_path=ROOT/'outputs/smz_v2_external_freeze/20261002_v2/region_index.json'
    regions=read(region_path)['regions']
    need(len(regions)==84 and len({r['official_region_id'] for r in regions})==84,'official region catalog')
    return {'api_version':'1','primary_universe':{'id':'paper_primary__evidence_20260927','UIKs':87736,'regions':84,'official_TIKs':2818,
                                               'registered_voters':99360758,'valid_votes':54723201,'DEG_included':False,'overseas':'SEPARATE'},
            'versions':[{k:r[k] for k in ['id','label','frame_UIKs','regions','official_TIKs','mapping_sha256','design_sha256','membership_changed_from_primary']} for r in meta['sources']],
            'versions_are_correctness_ranking':False,'unknown_invalid_policy':'UNKNOWN_RETAINED_NO_ZERO_IMPUTATION',
            'official_regions':regions,
            'cedar_primary_coverage':{'included_UIKs':71438,'source_frame_UIKs':87736,'outside_native_frame_UIKs':16298,
                                      'exclusive_reasons':{'REGISTERED_LE_100':2758,'INVALID_UNKNOWN':13540},'coverage_type':'MODEL_APPLICABILITY_NOT_HONESTY'},
            'post_commit_provenance_updates_may_mutate_results':False,
            'provenance':{'source_conflicts':ref(CLOSURE/'provenance_links.json'),'region_catalog':ref(region_path)}}

def construct():
    verify_inputs()
    files={}
    groups,party_order=build_abc_d(files)
    groups.update(build_external())
    for method,states in groups.items():
        states.sort(key=lambda s:s['state_id'])
        files['states/'+method+'.json']=encode({'api_version':'1','method_id':method,'state_count':len(states),
                                               'availability':'ONLY_LISTED_STATES_AVAILABLE','states':states})
    files['methods.json']=encode(catalog(groups))
    files['sources.json']=encode(build_sources())
    files['baselines.json']=encode({'api_version':'1','party_order':party_order,'sources':baseline()})
    # Explicit frozen controls; no execution logic or chronology in reader metadata.
    design=read(OLD/'design_metadata.json')
    design_refs=design.pop('references',None)
    specs=[{k:v for k,v in s.items() if k!='claim_ids'} for s in read(OLD/'model_metadata.json')['D_specifications']]
    files['designs.json']=encode({'abc':design,'d_specifications':specs,
                                  'provenance':{'technical_only':True,'design_references':design_refs}})
    return files,groups
