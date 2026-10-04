"""Deterministic static export; no scientific calls, models or real row loader."""
from .data import *

SCHEMA = 'https://json-schema.org/draft/2020-12/schema'

def schemas():
    string={'type':'string'}
    semantics={'type':'object','required':['value_kind','denominator_kind','is_confidence_interval','undefined_is_zero'],
               'properties':{'value_kind':{'enum':list(TYPES.values())},'is_confidence_interval':{'const':False},
                             'is_true_result':{'const':False},'undefined_is_zero':{'const':False},
                             'honesty_or_fraud_probability':{'const':False},'may_average_across_methods':{'const':False}}}
    state={'type':'object','additionalProperties':False,
           'required':['state_id','method_id','source_version','controls','geography','availability','visibility','status','result_type','result','coverage','support','interpretation_guards','warnings','provenance'],
           'properties':{'state_id':string,'method_id':{'enum':list(TYPES)},'source_version':{'enum':['primary','S1','S2a','S2b']},
                         'controls':{'type':'object'}, 'geography':{'type':'object','additionalProperties':False,
                         'required':['mode','excluded_region_id'],'properties':{'mode':{'enum':['DEFAULT','LEAVE_ONE_REGION_OUT']},'excluded_region_id':{'type':['string','null']}}},
                         'availability':{'const':'AVAILABLE'},'visibility':{'const':'PUBLIC'},
                         'status':{'enum':['APPLICABLE','DEFINED','NOT_DEFINED','UNDEFINED','UNDEFINED_SCENARIO_TOTAL','NO_TARGET_SUPPORT','INSUFFICIENT_FIT_SUPPORT']},
                         'result_type':{'enum':list(TYPES.values())},'result':{'type':'object'},'coverage':{'type':'object'},'support':{'type':'object'},
                         'diagnostics':{'type':'object'},'interpretation_guards':semantics,'warnings':{'type':'array','items':string},
                         'aliases':{'type':'array','items':string},'fit_relationship':{'type':'object'},'provenance':{'type':'object','required':['original_state_id']}}}
    state['allOf']=[]
    for method,result_type in TYPES.items():
        state['allOf'].append({'if':{'properties':{'method_id':{'const':method}}},'then':{'properties':{'result_type':{'const':result_type},'interpretation_guards':{'properties':{'value_kind':{'const':result_type},'denominator_kind':{'const':DENOMINATORS[method]}}}}}})
    st={'$schema':SCHEMA,'type':'object','additionalProperties':False,'required':['api_version','method_id','state_count','availability','states'],
        'properties':{'api_version':{'const':'1'},'method_id':{'enum':list(TYPES)},'state_count':{'type':'integer','minimum':1},
                      'availability':{'const':'ONLY_LISTED_STATES_AVAILABLE'},'states':{'type':'array','items':state}}}
    method={'type':'object','required':['method_id','label_ru','execution_status','result_type','available_controls','available_state_count','state_file','interpretation_guards','editorial_copy_status'],
            'properties':{'method_id':{'enum':list(TYPES)+['novaya_conventional','novaya_overlap_core']},'label_ru':string,
                          'execution_status':{'enum':['executable','card_only']},'editorial_copy_status':{'const':'pending'},
                          'available_state_count':{'type':'integer','minimum':0},'available_controls':{'type':'object'},
                          'state_file':{'type':['string','null']},'result_type':{'enum':list(TYPES.values())+['NO_PROJECT_EXECUTION']}},
            'allOf':[{'if':{'properties':{'execution_status':{'const':'card_only'}}},'then':{'properties':{'available_state_count':{'const':0},'state_file':{'type':'null'},'available_controls':{'maxProperties':0},'result_type':{'const':'NO_PROJECT_EXECUTION'}}}}]}
    methods={'$schema':SCHEMA,'type':'object','additionalProperties':False,'required':['api_version','project_id','methods'],
             'properties':{'api_version':{'const':'1'},'project_id':{'const':'election-2026'},'methods':{'type':'array','minItems':8,'maxItems':8,'items':method}}}
    manifest={'$schema':SCHEMA,'type':'object','additionalProperties':False,
              'required':['api_version','project_id','load_first','files','state_counts','primary_universe','chart_readiness','generator','missing_publication_derivatives','provenance'],
              'properties':{'api_version':{'const':'1'},'project_id':{'const':'election-2026'},'load_first':{'type':'array','items':string},
              'files':{'type':'object','additionalProperties':{'type':'object','additionalProperties':False,'required':['sha256','bytes','encoding'],
                       'properties':{'sha256':{'type':'string','pattern':'^[a-f0-9]{64}$'},'bytes':{'type':'integer','minimum':0},'encoding':{'enum':['JSON','GZIP_JSON','UTF8_MARKDOWN']}}}},
              'state_counts':{'type':'object'},'primary_universe':{'type':'object'},'chart_readiness':{'type':'object'},'generator':{'type':'object'},
              'missing_publication_derivatives':{'type':'array'},'provenance':{'type':'object'}}}
    exact={'$schema':SCHEMA,'type':'object','additionalProperties':False,'required':['state_id','method_id','result_type','party_order','scopes','integer_strings'],
           'properties':{'state_id':string,'method_id':{'enum':['abc','d']},'result_type':{'enum':[TYPES['abc'],TYPES['d']]},
                         'party_order':{'type':'array','minItems':10,'maxItems':10,'items':string},
                         'scopes':{'type':'object','required':['full','native'],'additionalProperties':{'type':'object'}},
                         'aggregate_exact':{'type':'object','required':['full','native']},
                         'integer_strings':{'type':'array','items':{'type':'string','pattern':'^-?[0-9]+$'}}}}
    sources={'$schema':SCHEMA,'type':'object','required':['api_version','primary_universe','versions','cedar_primary_coverage'],
             'properties':{'api_version':{'const':'1'},'versions':{'type':'array','minItems':4,'maxItems':4,
                 'items':{'type':'object','required':['id','frame_UIKs','regions','official_TIKs','mapping_sha256','design_sha256'],
                          'properties':{'id':{'enum':['primary','S1','S2a','S2b']},'frame_UIKs':{'type':'integer','minimum':1}}}},
                           'versions_are_correctness_ranking':{'const':False}}}
    baselines={'$schema':SCHEMA,'type':'object','required':['api_version','party_order','sources'],
               'properties':{'api_version':{'const':'1'},'party_order':{'type':'array','minItems':10,'maxItems':10},
                             'sources':{'type':'object','required':['primary','S1','S2a','S2b'],'minProperties':4,'maxProperties':4}}}
    designs={'$schema':SCHEMA,'type':'object','required':['abc','d_specifications','provenance'],
             'properties':{'abc':{'type':'object','required':['components','designs','default']},
                           'd_specifications':{'type':'array','minItems':5,'maxItems':5}}}
    return {'states':st,'methods':methods,'manifest':manifest,'exact':exact,'sources':sources,'baselines':baselines,'designs':designs}

CONTRACT = '''# Static data contract, version 1

This is the publication view of one election-2026 research project. It contains only
stored, disclosed results. No fitting, runtime calculations or back-end API is needed.
Regenerate with `/usr/bin/python3 -m src.publication_sites generate`; validate with
`/usr/bin/python3 -m src.publication_sites check` from the repository root.

## Client workflow

1. Load `manifest.json`; verify hashes if the client supports integrity checking.
2. Load `methods.json` and `sources.json`. Optional `baselines.json` supplies the
   original ten-party vector for each frozen source; `designs.json` explains controls.
3. An executable method names one state file. A card-only method has no executable
   file, no available states and no project numeric output.
4. Read the selected state file. Its `states` array is the complete availability list.
   Offer a control change only if an actual row exists matching ALL selected controls,
   source and geography. Marginal `available_controls` are NOT a Cartesian product.
   Only keys in the method's `available_controls` may be public selectors. Other fields
   in a state's `controls` are fixed/coupled specification facts, never independent
   optimizer knobs. In particular sigma_min is determined by bin width, and K is fixed.
5. Changing source/geography can make a method control unavailable. Disable it with
   `UNAVAILABLE_NOT_IN_FROZEN_GRID`. Require an explicit reader-visible reset before
   choosing another listed state; never silently coerce to a default.
6. Render that row's already-stored results, result type, native coverage and support.
   `provenance` is technical audit information, never a reader-facing method name.

Stable IDs here are publication aliases with a one-to-one technical provenance mapping.
Aliases A and B are slices of the joint local scenario grid, not duplicate states.
An initial view may use `baselines.json` without inventing a scenario ID. Scopes `full`
and `native` are two stored outputs of one calculation, not separate states.

## Exact values and display values

All integer denominators/numerators are strings when represented as rationals.
Additional result objects preserve stored `{exact: "numerator/denominator"}` or
`{float_hex, decimal17}` exactly. Counts remain stored integers. For large ten-party
vectors, `result.exact_file` is a lazy static gzip-compressed JSON resource. Fetch as
bytes and decompress with `DecompressionStream('gzip')` (or equivalent client library),
then parse JSON. Each rational uses `numerator_ref` / `denominator_ref`, zero-based
indices into that resource's `integer_strings` array. Resolve those two indices to
obtain the exact numerator/denominator strings; never calculate them from rounded data.
This storage-only pool avoids repeating enormous identical integer strings. Hosting
must serve the resource as bytes, not apply another gzip
content encoding. Its manifest/hash covers the compressed bytes. No scientific pipeline
knowledge is required. Never convert large integer strings through JavaScript Number.

The main ten-party `display_vectors` are the unchanged six-decimal stored presentation
arrays. `shares` are fractions, `percentage_points` are already in pp. They are not exact
records; their exact counterparts are in the sidecar. Pipeline decomposition details
are intentionally not duplicated; technical provenance retains their frozen source.
External display percentages use
four decimal places, half-even, derived from exact stored rational/binary64 values.
Display transformations never overwrite exact values. Full/native focal accounting in
`aggregate_exact` inside that sidecar is copied from the disclosed exact inventory.

## Meaning, undefined states and coverage

Do not put different `result_type` values on a common truth scale or average methods.
The local ten-party scenarios and focal-party scenario D are conditional scenarios.
The iStories construction reports a scenario focal-valid share. Cedar reports signed
E / observed focal votes, NOT a party share. The one-dimensional Gaussian result is a
component center, NOT a national counterfactual share. The two-dimensional result is a
component center plus model membership, never an honesty/fraud probability.

Honor original `status`; undefined fields/groups have typed status/reason, never numeric
zero. In D, full-frame identity extension retains observed values outside native support;
it does not assert zero effect there. D is focal-party-specific, not a symmetric ten-party
reconstruction. Do not promote an unavailable group to an available scenario.

Show native vs source/full-frame coverage separately. For Cedar show included 71,438 /
87,736 and outside 16,298 (2,758 registered <=100; 13,540 unknown invalid) on the primary
default view. Anchor support N/L/O belongs next to the fixed-anchor curve and AUTO states.
It is a NON_MODEL reader diagnostic, not an honesty label. iStories reference N belongs
next to each of the 15 windows; distinguish it from the scenario frame. Do not hide small
windows or invent an acceptability cutoff. The predeclared default is not a post-result
scientific preference. Window ranges and anchor curves are specification sensitivity,
NOT confidence/credible intervals. LOO is single-region influence, not a bad-region label.
Source variants are not correctness rankings and must not be silently replaced.
For anchor interpretation, Cedar uses `(valid + known invalid) / registered voters`;
its O includes known invalid ballots. It never substitutes issued for cast. iStories
uses issued ballots / registered voters and O=valid-focal; its predeclared 20–29%
reference is technically [20%,30%). These are prospective project mappings, not
proof of the published authors' exact implementation. The official region names
in `sources.json` resolve LOO IDs without reading the scientific pipeline.

For 1D, K=3 is fixed; bin width also changes sigma_min=h/2, not pure discretization.
For 2D, the exact first coordinate is issued ballots / registered voters. Thresholds
>.5 / >.7 / >.9 reuse the same fit; unchanged centers are mechanical reuse. Diagonal
covariance is a different fitted specification. No arbitrary thresholds or K controls exist.

## Stable versus editorial

`method_id`, `state_id`, controls, hashes, result_type, value_kind, denominator_kind,
availability and interpretation guards are technical. Short neutral Russian labels are
navigation labels; `editorial_copy_status: pending` reserves final prose for later review.
Source fidelity gaps and release-license/repository details remain accepted/pending
metadata, not permissions to modify results. Only files listed by this public manifest
form the client API. Opaque local provenance paths are not additional executable routes.
'''

README = '''# election-2026 static publication data

Load `manifest.json`, then `methods.json`. Read `CONTRACT.md` before building a client.
This directory is data and metadata only; no article, charts or user interface.

Generation: `/usr/bin/python3 -m src.publication_sites generate`
Validation: `/usr/bin/python3 -m src.publication_sites check`

There are 2,064 stored public calculation states across six executable catalog entries;
two further catalog entries are source-only cards. Exact ten-party aggregates are lazy
gzip JSON sidecars. Source/coverage and result semantics are mandatory display context.
Final editorial copy and release metadata remain pending. Scientific inputs are read-only.
'''

def generate():
    files,groups=construct()
    for key,value in schemas().items():files['schemas/'+key+'.schema.json']=encode(value)
    files['CONTRACT.md']=CONTRACT.encode();files['README.md']=README.encode()
    manifest={'api_version':'1','project_id':'election-2026','load_first':['methods.json','sources.json'],
              'files':{k:{'sha256':hashlib.sha256(v).hexdigest(),'bytes':len(v),'encoding':'GZIP_JSON' if k.endswith('.gz') else 'JSON' if k.endswith('.json') else 'UTF8_MARKDOWN'} for k,v in sorted(files.items())},
              'state_counts':{k:len(v) for k,v in sorted(groups.items())},
              'primary_universe':build_sources()['primary_universe'],
              'chart_readiness':{'original_vs_ten_party':'baselines.json + states/abc.json + lazy exact sidecars',
                                'local_sensitivity':'abc explicit stored control rows and native/full scopes',
                                'focal_scenario_variants':'d stored scopes, five specifications and typed group statuses',
                                'reference_windows':'vazhnye_istorii 15 windows with reference_UIKs',
                                'anchor_curve':'cedar 71 fixed anchors with NON_MODEL N/L/O, AUTO retained separately',
                                'one_dimensional_center':'novaya_1d explicit source, geography and bin-width states',
                                'two_dimensional_center_membership':'novaya_2d centers, threshold_output and fit_relationship'},
              'missing_publication_derivatives':[],
              'generator':{'command':'/usr/bin/python3 -m src.publication_sites generate',
                           'source_files':{str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'src/publication_sites').glob('*.py'))},
                           'deterministic':True, 'new_model_calls':0,'new_fits':0,'new_scientific_states':0},
              'provenance':{'technical_only':True,'input_bindings':ref(EVIDENCE/'input_bindings.json'),
                            'authority_manifests':read(EVIDENCE/'input_bindings.json')['manifests']}}
    files['manifest.json']=encode(manifest)
    # Fail on unknown stale public files, do not silently keep another API generation.
    existing={str(p.relative_to(OUT)) for p in OUT.rglob('*') if p.is_file()} if OUT.exists() else set()
    need(existing<=set(files),'unexpected existing public files '+str(existing-set(files)))
    for name,blob in sorted(files.items()):
        target=OUT/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(blob)
    print(json.dumps({'status':'GENERATED','public_states':sum(len(v) for v in groups.values()),'files':len(files),'bytes':sum(map(len,files.values())),
                      'manifest_sha256':sha(OUT/'manifest.json')},sort_keys=True))
