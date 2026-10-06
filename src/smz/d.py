"""Independent signed proportional histogram engine. No ABC reference logic."""
from fractions import Fraction as F
from .common import validate, require, SMZError, NOT_DEFINED, shares, totals, coverage

SPECS = {'D0':('region',F(1,5),F(1,200)), 'D1':('region',F(1,10),F(1,200)),
         'D2':('region',F(3,10),F(1,200)), 'D3':('region',F(1,5),F(1,100)),
         'D4':('tik',F(1,5),F(1,200))}
UNDEFINED = ('scenario_issued','scenario_invalid','scenario_cast','issuance_remainder',
             'UIK_scenario_party_counts','UIK_corrections','actually_transformed_UIKs')


def bin_index(issued,n,h):
    require(h in (F(1,200),F(1,100)) and type(h) is F,'unknown exact bin width','UNKNOWN_PARAMETER')
    require(type(issued) is int and type(n) is int and n>0 and 0<=issued<=n,'bin domain','SOURCE_FRAME_UNSUPPORTED')
    return min((F(issued,n)/h).__floor__(),int(1/h)-1)


def stratum(rows,q,h):
    bins=[{'bin':b,'n':0,'valid':0,'UIKs':0,'parties':[0]*10} for b in range(int(1/h))]
    for r in rows:
        b=bins[bin_index(r.issued,r.n,h)]
        b['n']+=r.n; b['valid']+=r.valid; b['UIKs']+=1
        for j,c in enumerate(r.parties): b['parties'][j]+=c
    total_valid=sum(r.valid for r in rows); cumulative=0
    threshold=None
    for b in bins:
        cumulative+=b['valid']
        if cumulative>=q*total_valid:
            threshold=b['bin']; break
    require(threshold is not None,'threshold missing')
    fit=bins[:threshold+1]; tail=bins[threshold+1:]
    fit_rows=sum(b['UIKs'] for b in fit); tail_rows=sum(b['UIKs'] for b in tail)
    g=lambda b: sum(b['parties'])-b['parties'][1]
    den=sum(g(b)**2 for b in fit); num=sum(b['parties'][1]*g(b) for b in fit)
    informative=sum(g(b)>0 for b in fit)
    flags={'NO_TARGET_SUPPORT':tail_rows==0,'FIT_ROWS':fit_rows<5,
           'DEGENERATE_REFERENCE':den==0,'INFORMATIVE_BINS':informative<2}
    reason=''; status='APPLICABLE'
    if flags['NO_TARGET_SUPPORT']: status='NO_TARGET_SUPPORT'
    elif flags['FIT_ROWS']: status='INSUFFICIENT_FIT_SUPPORT'; reason='FIT_ROWS'
    elif flags['DEGENERATE_REFERENCE']: status='DEGENERATE_REFERENCE'
    elif flags['INFORMATIVE_BINS']: status='INSUFFICIENT_FIT_SUPPORT'; reason='INFORMATIVE_BINS'
    alpha=F(num,den) if den else NOT_DEFINED
    scenario=None; residuals=None
    if status=='APPLICABLE':
        residuals=tuple(F(b['parties'][1])-alpha*g(b) if b['bin']>threshold else F(0) for b in bins)
        scenario=[]
        for b,e in zip(bins,residuals):
            parties=list(map(F,b['parties'])); parties[1]-=e
            valid=sum(parties)
            if min(parties)<0 or valid<0 or (b['bin']>threshold and valid>b['n']):
                status='UNDEFINED_SCENARIO_TOTAL'; reason='ELECTORATE_OR_COUNT_COMPATIBILITY'
            scenario.append({'parties':tuple(parties),'valid':valid,'shares':shares(parties,valid)})
        if sum(b['valid'] for b in scenario)<=0:
            status='UNDEFINED_SCENARIO_TOTAL'; reason='STRATUM_ZERO_VALID'
        flags['ELECTORATE_OR_COUNT_COMPATIBILITY']=status=='UNDEFINED_SCENARIO_TOTAL'
    source=totals(rows)
    require(tuple(sum(b['parties'][j] for b in bins) for j in range(10))==source,'histogram-source reconciliation')
    # Invalid candidates remain diagnostics, never an identity-substituted success.
    result_counts=tuple(sum(b['parties'][j] for b in scenario) for j in range(10)) if status=='APPLICABLE' else None
    if result_counts is not None:
        require(all(result_counts[j]==source[j] for j in range(10) if j!=1),'D nonfocal conservation')
        require(sum(result_counts)==total_valid-sum(residuals),'D signed valid identity')
    return {'status':status,'reason':reason,'flags':flags,'threshold_bin':threshold,
            'fit_valid_fraction':F(cumulative,total_valid),'fit_UIKs':fit_rows,'tail_UIKs':tail_rows,
            'informative_fit_bins':informative,'alpha':alpha,'coefficient_numerator':num,'coefficient_denominator':den,
            'bins':tuple(bins),'candidate_bins':tuple(scenario) if scenario is not None else NOT_DEFINED,
            'signed_bin_residual':residuals if residuals is not None else NOT_DEFINED,
            'signed_stratum_residual':sum(residuals) if residuals is not None else NOT_DEFINED,
            'positive_residual_sum':sum(e for e in residuals if e>0) if residuals is not None else NOT_DEFINED,
            'negative_residual_sum':sum(e for e in residuals if e<0) if residuals is not None else NOT_DEFINED,
            'source_parties':source,'source_valid':total_valid,
            'scenario_parties':result_counts if result_counts is not None else NOT_DEFINED,
            'scenario_valid':sum(result_counts) if result_counts is not None else NOT_DEFINED,
            'undefined':{k:NOT_DEFINED for k in UNDEFINED}}


def execute(frame,spec_id):
    rows=validate(frame)
    require(spec_id in SPECS,'unknown D specification','UNKNOWN_PARAMETER')
    geography,q,h=SPECS[spec_id]
    groups={}
    for r in rows: groups.setdefault(getattr(r,geography),[]).append(r)
    results={}; applicable_rows=[]; target_rows=[]
    for name in sorted(groups):
        try:
            result=stratum(groups[name],q,h)
        except SMZError: raise
        except Exception as exc:
            raise SMZError('NUMERICAL_OR_IMPLEMENTATION_FAILURE',type(exc).__name__) from exc
        results[name]=result
        if result['status']=='APPLICABLE': applicable_rows.extend(groups[name])
        target_rows.extend(r for r in groups[name] if bin_index(r.issued,r.n,h)>result['threshold_bin'])
    native_counts=tuple(sum((r['scenario_parties'][j] for r in results.values() if r['status']=='APPLICABLE'),F(0)) for j in range(10))
    extended=tuple(sum((r['scenario_parties'][j] if r['status']=='APPLICABLE' else r['source_parties'][j] for r in results.values()),F(0)) for j in range(10))
    source=totals(rows); native_source=totals(applicable_rows)
    require(all(extended[j]==source[j] for j in range(10) if j!=1),'D frame nonfocal identity')
    return {'engine':'D','spec_id':spec_id,'source_id':frame.source_id,'strata':results,
            'status':'APPLICABLE' if applicable_rows else 'NOT_APPLICABLE_ON_THIS_DESIGN',
            'source_parties':source,'source_valid':sum(source),
            'native':{'source_parties':native_source,'scenario_parties':native_counts,'source_valid':sum(native_source),
                      'scenario_valid':sum(native_counts),'shares':shares(native_counts,sum(native_counts))},
            'extended':{'scenario_parties':extended,'scenario_valid':sum(extended),'shares':shares(extended,sum(extended)),
                        'identity_extended_status':{k:('APPLIED' if v['status']=='APPLICABLE' else 'SCENARIO_NOT_APPLIED') for k,v in results.items()}},
            'selected_targets':len(target_rows),
            'supported_targets':sum(v['tail_UIKs'] for v in results.values() if v['status']=='APPLICABLE'),
            'coverage':coverage(applicable_rows,rows),'target_coverage':coverage(target_rows,rows),
            'undefined':{k:NOT_DEFINED for k in UNDEFINED}}
