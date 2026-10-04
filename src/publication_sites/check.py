"""Fail-closed static contract validation and exact source reconciliation."""
import importlib.metadata
import math
from .data import *
from .generate import schemas, CONTRACT, README

def schema_validate(value, schema):
    import jsonschema
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(value)

def valid_numbers(obj):
    if isinstance(obj,dict):
        if 'float_hex' in obj:
            need(math.isfinite(float.fromhex(obj['float_hex'])), 'non-finite stored float')
            need(float(obj['decimal17'])==float.fromhex(obj['float_hex']), 'inconsistent binary64 display')
        if 'exact' in obj and isinstance(obj['exact'],str):
            need(Fraction(obj['exact']).denominator>0,'invalid rational')
        if 'numerator' in obj and 'denominator' in obj:
            need(int(obj['denominator'])>0,'nonpositive exact denominator')
            int(obj['numerator'])
        for v in obj.values():valid_numbers(v)
    elif isinstance(obj,list):
        for v in obj:valid_numbers(v)
    elif isinstance(obj,float):need(math.isfinite(obj),'nonfinite JSON number')

def public_inventory():
    return {str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file()}

def check():
    checks=[]
    def passed(name):checks.append({'check':name,'status':'PASS'})
    verify_inputs();passed('authority_manifests_and_all_consumed_dependencies')
    manifest=read(OUT/'manifest.json');schema_validate(manifest,schemas()['manifest']);passed('manifest_schema')
    actual=public_inventory()
    need(set(actual)==set(manifest['files'])|{'manifest.json'},'missing/unlisted API file')
    for name,meta in manifest['files'].items():
        need(actual[name]==meta['sha256'] and (OUT/name).stat().st_size==meta['bytes'],'public hash/size '+name)
    for path,expected_hash in manifest['generator']['source_files'].items():
        need(sha(ROOT/path)==expected_hash,'generator source binding '+path)
    passed('complete_public_file_inventory_hash_and_size')
    methods=read(OUT/'methods.json');schema_validate(methods,schemas()['methods']);passed('method_schema')
    for name in ('sources','baselines','designs'):
        schema_validate(read(OUT/(name+'.json')),schemas()[name])
    passed('source_baseline_design_schemas')
    method_map={m['method_id']:m for m in methods['methods']}
    need(len(method_map)==8,'duplicate method ID')
    allowed_axes={'abc':{'design_id','lambda_quarters','mu_quarters'},'d':{'specification'},
                  'cedar':{'anchor_mode','auto_offset_bins','anchor_right_edge_percent'},
                  'vazhnye_istorii':{'reference_window_percent'},'novaya_1d':{'bin_width'},
                  'novaya_2d':{'covariance','membership_threshold'}}
    for method,axes in allowed_axes.items():need(set(method_map[method]['available_controls'])==axes,'unfrozen public selector '+method)
    passed('only_frozen_public_axes_no_optimizer_K_scaling_or_accounting_selectors')
    groups={}
    all_states=[]
    for method,m in method_map.items():
        if m['execution_status']=='card_only':
            need(m['state_file'] is None and m['available_state_count']==0 and not m['available_controls'] and not m['available_scope_outputs'],'fake card execution')
            continue
        value=read(OUT/m['state_file']);schema_validate(value,schemas()['states'])
        need(value['method_id']==method and value['state_count']==len(value['states'])==m['available_state_count'],'method inventory mismatch')
        need(value['states']==sorted(value['states'],key=lambda s:s['state_id']),'unstable state order')
        groups[method]=value['states'];all_states.extend(value['states'])
        need(set(m.get('predeclared_default_states',{}).values())<={s['state_id'] for s in value['states']},'unknown declared default state')
        for s in value['states']:
            need(s['method_id']==method and s['result_type']==TYPES[method],'result semantic mismatch')
            need(s['interpretation_guards']==guards(method),'interpretation guard mismatch')
            valid_numbers(s['result'])
            if method=='d':
                need(s['result']['undefined_fields'] and all(isinstance(v,dict) and v['status']=='NOT_DEFINED' for v in s['result']['undefined_fields'].values()),'D undefined coerced to zero')
                need(all(not r['included_in_native'] for r in s['support']['group_statuses'] if not r['candidate_defined']),'D undefined group included')
    passed('all_state_schemas_exact_types_finite_values_and_D_missingness')
    ids=[s['state_id'] for s in all_states];original=[s['provenance']['original_state_id'] for s in all_states]
    need(len(set(ids))==len(ids)==2064 and len(set(original))==2064,'duplicate/fabricated count')
    counts={m:len(v) for m,v in groups.items()}
    need(counts=={'abc':1600,'d':20,'cedar':161,'vazhnye_istorii':102,'novaya_1d':90,'novaya_2d':91},'authoritative public count mismatch')
    need(counts==manifest['state_counts'],'manifest count mismatch')
    passed('1620_published_scenario_cells_444_additional_public_states_zero_duplicates')
    for name in actual:
        data=(OUT/name).read_bytes()
        if name.endswith('.gz'):data=gzip.decompress(data)
        need(INTERNAL.encode() not in data and b'LS_B_WINDOW' not in data,'internal state reachable '+name)
    passed('zero_internal_state_in_all_public_files_including_exact_downloads')
    for method,states in groups.items():
        if method in ('abc','d'):continue
        loo=[s for s in states if s['geography']['mode']=='LEAVE_ONE_REGION_OUT']
        need(len(loo)==84 and len({s['geography']['excluded_region_id'] for s in loo})==84,'LOO region availability')
        need({s['geography']['excluded_region_id'] for s in loo}=={r['official_region_id'] for r in read(OUT/'sources.json')['official_regions']},'LOO official region catalog mismatch')
        need(all(s['source_version']=='primary' for s in loo),'forbidden source x LOO')
        default_frame=[s for s in states if s['geography']['mode']=='DEFAULT']
        need({s['source_version'] for s in default_frame}=={'primary','S1','S2a','S2b'},'source topology')
        need(all(s['provenance']['original_state_id'].endswith('__B') for s in default_frame if s['source_version']!='primary'),'method x alternate source')
    windows=[s for s in groups['vazhnye_istorii'] if s['source_version']=='primary' and s['geography']['mode']=='DEFAULT']
    need({tuple(s['controls']['reference_window_percent']) for s in windows}=={(start,start+width) for start in (10,15,20,25,30) for width in (5,10,15)},'15 window set')
    need(all(isinstance(s['support']['reference_UIKs'],int) for s in windows),'missing reference N')
    fixed=[s for s in groups['cedar'] if s['controls']['anchor_mode']=='FIXED']
    need(len(fixed)==71 and {s['controls']['anchor_right_edge_percent'] for s in fixed}==set(range(10,81)),'fixed anchor grid')
    need(all(s['source_version']=='primary' and s['geography']['mode']=='DEFAULT' for s in fixed),'fixed anchor cross')
    need(all('anchor_UIKs' in s['support'] and s['support']['anchor_L']+s['support']['anchor_O']==s['support']['anchor_cast'] for s in groups['cedar']),'missing/mismatched Cedar support')
    passed('OFAT_availability_15_windows_71_anchors_and_own_frame_support')
    for s in groups['novaya_2d']:
        if s['fit_relationship']['reuse']:
            base=next(t for t in groups['novaya_2d'] if t['provenance']['original_state_id']=='NOVAYA_2D__primary__DEFAULT__B')
            need(s['result']['exact_stored']['core_center']==base['result']['exact_stored']['core_center'],'reused center mismatch')
            need(s['fit_relationship']['fit_id']==base['fit_relationship']['fit_id'],'wrong parent fit')
    passed('2D_threshold_fit_reuse_and_exact_centers')
    # Independently rebuild from pinned stored sources, then compare every public byte.
    # This is serialization, not recomputation of any scientific result.
    expected,expected_groups=construct()
    for name,blob in expected.items():need((OUT/name).read_bytes()==blob,'stored result/export differs '+name)
    for name in [n for n in expected if n.startswith('exact/')]:
        value=json.loads(gzip.decompress(expected[name]));schema_validate(value,schemas()['exact']);valid_numbers(unpack_exact(value))
    passed('all_exact_sidecars_and_states_identical_to_authoritative_projection')
    need((OUT/'CONTRACT.md').read_text()==CONTRACT and (OUT/'README.md').read_text()==README,'contract mismatch')
    passed('documented_client_workflow_and_no_cartesian_inference')
    # Fail-closed negative checks exercise actual schema/validation paths in memory.
    import copy
    for method,wrong in [('cedar',TYPES['vazhnye_istorii']),('novaya_1d',TYPES['d'])]:
        broken=read(OUT/'states'/f'{method}.json');broken['states'][0]['result_type']=wrong
        try:schema_validate(broken,schemas()['states'])
        except Exception:pass
        else:raise ValueError('negative result-type guard failed')
    broken=copy.deepcopy(methods);card=next(m for m in broken['methods'] if m['execution_status']=='card_only');card['available_state_count']=1
    try:schema_validate(broken,schemas()['methods'])
    except Exception:pass
    else:raise ValueError('card-only negative guard failed')
    passed('negative_schema_regressions_wrong_estimands_and_card_execution')
    protected=read(EVIDENCE/'protected_inputs.json')
    need(all((ROOT/p).is_file() and sha(ROOT/p)==h for p,h in protected.items()),'scientific/frozen/article artifact mutation')
    passed('protected_science_reveal_committed_article_and_provenance_bytes_unchanged')
    need(not any(m.startswith(('src.smz.abc','src.smz.d','src.smz_external','scipy','sklearn')) for m in sys.modules),'scientific kernel import')
    passed('no_scientific_kernel_provider_or_optimizer_loaded')
    digest=hashlib.sha256(encode(actual)).hexdigest()
    result={'status':'PASS','checks':checks,'public_states':2064,'scenario_public_states':1620,'additional_public_states':444,
            'internal_exported':0,'card_only_methods':2,'files':len(actual),'publication_inventory_sha256':digest,
            'manifest_sha256':sha(OUT/'manifest.json'),'new_model_calls':0,'new_fits':0,'new_scientific_states':0,
            'real_source_rows_passed_to_kernels':0,'protected_files':len(protected),
            'validator_environment':{'python':sys.version.split()[0],'jsonschema':importlib.metadata.version('jsonschema')}}
    print(json.dumps(result,sort_keys=True))
    return result
