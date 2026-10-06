"""Closed synthetic execution/serialization. No real mode or real authorization token exists."""
from .common import guard, require, canonical, SOURCES, NOT_DEFINED, fingerprint, shares, Missing, PARTIES, VERSION, level
from . import abc, d


def source_alias(source_id):
    if source_id=='S3': return {'status':'IDENTITY_WITH_PRIMARY','execute':False,'alias':'primary'}
    require(source_id in SOURCES,'unknown source','SOURCE_FRAME_UNSUPPORTED')
    return {'status':'EXECUTABLE_SYNTHETIC_ONLY','execute':True}


def execute(frame,family,design_id,*,lam=0,mu=0,mode='synthetic_qualification'):
    guard(frame,mode)
    require(family in ('A','B','C','D'),'unknown/deferred family','UNKNOWN_MODEL')
    lam,mu=level(lam),level(mu)
    if family=='D':
        require(lam==0 and mu==0,'D has no ABC intensity parameters','UNKNOWN_PARAMETER')
        return d.execute(frame,design_id)
    if family=='A': require(mu==0,'A is C at mu=0','UNKNOWN_PARAMETER')
    if family=='B': require(lam==0,'B is C at lambda=0','UNKNOWN_PARAMETER')
    return abc.C(abc.build(frame,design_id),lam,mu)


def serialize(frame,result,mode='synthetic_qualification'):
    guard(frame,mode)
    require(result.get('source_id')==frame.source_id,'output source mismatch')
    return canonical({'mode':mode,'origin':frame.origin,'input_sha256':fingerprint(frame),'result':result})


def common_records(frame,result,family):
    """Full-frame common comparison records; detailed native output stays in engine result."""
    guard(frame)
    require(family in ('A','B','C','D'),'unknown output model','UNKNOWN_MODEL')
    is_d=family=='D'
    require(result['engine']==('D' if is_d else 'ABC'),'cross-engine output mismatch')
    if family=='A': require(result['mu']==0,'cannot label a joint result as A')
    if family=='B': require(result['lambda']==0,'cannot label a joint result as B')
    src=result['source_parties']; sv=sum(src)
    scen=result['extended']['scenario_parties'] if is_d else result['aggregate']['parties']
    vv=sum(scen); sshare=shares(src,sv); vshare=shares(scen,vv)
    model_id=result['spec_id'] if is_d else result['design_id']
    cov=result['coverage']
    records=[]
    for j,party in enumerate(PARTIES):
        row={'family_id':family,'model_version':VERSION,'design_id':model_id,'source_id':frame.source_id,
             'source_manifest_sha256':fingerprint(frame),'source_frame':frame.fixture_id,
             'native_output_unit':'stratum_x_bin' if is_d else 'UIK','scope':'FULL_FRAME_IDENTITY_EXTENSION',
             'unit_id':frame.fixture_id,'party_id':party,'source_party_count':src[j],'scenario_party_count':scen[j],
             'source_party_share':sshare[j],'scenario_party_share':vshare[j],
             'source_share_denominator':sv,'scenario_share_denominator':vv,
             'signed_count_difference':scen[j]-src[j],
             'percentage_point_difference':100*(vshare[j]-sshare[j]) if vv else Missing('NULL','UNDEFINED_ZERO_DENOMINATOR'),
             'source_valid':sv,'scenario_valid':vv,'net_valid_change':vv-sv,
             'selected_targets':result['selected_targets'],'supported_targets':result['supported_targets'],
             'actually_transformed_units':NOT_DEFINED if is_d else result['actually_transformed_units'],
             'coverage_UIKs':cov['UIKs'],'coverage_voters':cov['voters'],'coverage_source_valid':cov['source_valid'],
             'coverage_denominator_frame':cov['denominator'],'coverage_TIKs':cov['TIKs'],'coverage_regions':cov['regions'],
             'changed_quantities':['focal_party','valid','composition'] if is_d else ({'A':['composition'],'B':['issued','valid','counts'],'C':['issued','valid','composition','counts']}[family]),
             'conserved_quantities':['voters','nonfocal_counts'] if is_d else (['voters','issued','valid','known_invalid'] if family=='A' else ['voters']),
             'undefined_quantities':list(d.UNDEFINED) if is_d else ['scenario_cast_when_invalid_unknown'],
             'applicability_status':result['status'],'failure_reason':NOT_DEFINED,
             'native_support_result_id':fingerprint(result['native']),
             'assumption_parameter_id':model_id if is_d else f"{model_id}:lambda={result['lambda']}:mu={result['mu']}",
             'limitations':['synthetic-only qualification; not scientific calibration','conditional transformation; no identified latent truth']}
        if is_d:
            for field in ('alpha','fit_valid_fraction','fit_UIKs','informative_fit_bins','tail_UIKs','signed_bin_residual',
                          'signed_stratum_residual','positive_residual_sum','negative_residual_sum'):
                row[field]={s:v[field] for s,v in result['strata'].items()}
            row['identity_extended_status']=result['extended']['identity_extended_status']
        records.append(row)
    return records
