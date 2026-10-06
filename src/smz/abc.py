"""A and B are exact slices of one C engine. No data loading or D dependency."""
from dataclasses import dataclass
from fractions import Fraction as F
from itertools import product
from .common import (validate, guard, require, level, fingerprint, UNKNOWN, shares, totals, coverage)

DESIGNS = tuple('-'.join(x) for x in product(('R1','R2'), ('T1','T2'), ('D1','D2'), ('M1','M2')))

@dataclass(frozen=True)
class Target:
    uuid: str
    rank: F
    status: str
    donors: tuple
    q: tuple = ()
    tau: F | None = None

@dataclass(frozen=True)
class Design:
    frame: object
    design_id: str
    targets: tuple
    object_id: str


def parameters(design_id):
    require(design_id in DESIGNS, 'unknown ABC design', 'UNKNOWN_PARAMETER')
    r,t,d,m = design_id.split('-')
    return (F(1,4), {'R1':F(1,2),'R2':F(5,8)}[r],
            {'T1':F(3,4),'T2':F(7,8)}[t], {'D1':F(5,4),'D2':F(3,2)}[d], {'M1':3,'M2':5}[m])


def midranks(rows):
    """Complete rational tie groups; sorting UUIDs never splits ties."""
    groups = {}
    for row in rows:
        groups.setdefault(row.tik, {}).setdefault(F(row.issued, row.n), []).append(row)
    result = {}
    for times in groups.values():
        n = sum(map(len, times.values())); lower = 0
        for t in sorted(times):
            tied = times[t]; rank = F(2*lower + len(tied), 2*n)
            result.update((r.uuid, rank) for r in tied)
            lower += len(tied)
    return result


def donor_status(references, donors, minimum):
    """Pure support primitive, including unreachable-on-valid-source zero-valid fixture."""
    if not references: return 'NO_REFERENCE_IN_TIK'
    if not donors: return 'NO_SIZE_LOCAL_DONOR'
    if len(donors) < minimum: return 'INSUFFICIENT_DONORS'
    valid = sum(r.valid for r in donors)
    if valid == 0: return 'ZERO_REFERENCE_VALID'
    if 2*max(r.valid for r in donors) > valid: return 'DONOR_DOMINANCE'
    return 'SUPPORTED'


def local_donors(target, references, ratio):
    return tuple(r for r in references if r.tik == target.tik and 1/ratio <= F(r.n,target.n) <= ratio)


def build(frame, design_id):
    rows = validate(frame)
    lo, hi, cutoff, ratio, minimum = parameters(design_id)
    ranks = midranks(rows)
    refs = {}
    for r in rows:
        if lo <= ranks[r.uuid] <= hi:
            refs.setdefault(r.tik, []).append(r)
    targets = []
    for r in rows:
        rank = ranks[r.uuid]
        if rank < cutoff:
            targets.append(Target(r.uuid,rank,'NOT_SELECTED',())); continue
        references = refs.get(r.tik, ())
        donors = local_donors(r,references,ratio)
        status = donor_status(references,donors,minimum)
        q, tau = (), None
        if status == 'SUPPORTED':
            v = sum(x.valid for x in donors)
            q = tuple(F(sum(x.parties[j] for x in donors),v) for j in range(10))
            tau = F(sum(x.issued for x in donors),sum(x.n for x in donors))
            require(tau <= F(r.issued,r.n), 'reference issuance exceeds target', 'ABC_DESIGN_INVARIANT_FAILURE')
        targets.append(Target(r.uuid,rank,status,tuple(x.uuid for x in donors),q,tau))
    object_id = fingerprint({'source':frame.source_id,'rows':rows,'design':design_id,'targets':targets})
    return Design(frame,design_id,tuple(targets),object_id)


def transform(design, lam, mu):
    guard(design.frame)
    lam,mu = level(lam),level(mu)
    rows = validate(design.frame); by_id = {r.uuid:r for r in rows}
    expected_id = fingerprint({'source':design.frame.source_id,'rows':rows,'design':design.design_id,'targets':design.targets})
    require(design.object_id == expected_id, 'reference object mutation', 'ABC_DESIGN_INVARIANT_FAILURE')
    output=[]
    for t in design.targets:
        r = by_id[t.uuid]; p=tuple(F(c,r.valid) for c in r.parties)
        s=F(1); pstar=p
        if t.status == 'SUPPORTED':
            require(t.tau <= F(r.issued,r.n), 'reference issuance exceeds target; never clipped', 'ABC_DESIGN_INVARIANT_FAILURE')
            s=(1-mu)+mu*r.n*t.tau/r.issued
            pstar=tuple((1-lam)*a+lam*b for a,b in zip(p,t.q))
        issued=s*r.issued; valid=s*r.valid
        counts=tuple(valid*x for x in pstar)
        j=UNKNOWN if r.invalid is None else s*r.invalid
        remainder=UNKNOWN if r.invalid is None else s*(r.issued-r.valid-r.invalid)
        comp=tuple(r.valid*(b-a) for a,b in zip(p,pstar))
        intensity=tuple(a*(valid-r.valid) for a in p)
        interaction=tuple((valid-r.valid)*(b-a) for a,b in zip(p,pstar))
        delta=tuple(c-a for c,a in zip(counts,r.parties))
        require(sum(counts)==valid and min(counts)>=0 and 0<=valid<=issued<=r.n,'ABC accounting')
        require(all(d==a+b+c for d,a,b,c in zip(delta,comp,intensity,interaction)),'ABC decomposition')
        if r.invalid is not None: require(valid+j+remainder==issued,'ABC known remainder identity')
        output.append({'uuid':r.uuid,'status':t.status,'scenario_applied':t.status=='SUPPORTED',
                       'actually_transformed':counts!=r.parties or issued!=r.issued,
                       'n':r.n,'issued':issued,'valid':valid,'parties':counts,'invalid':j,
                       'remainder':remainder,'combined_issued_minus_valid':issued-valid,'scale':s,
                       'source_parties':r.parties,'source_valid':r.valid,'delta':delta,
                       'composition':comp,'intensity':intensity,'interaction':interaction})
    agg={key:tuple(sum((r[key][j] for r in output),F(0)) for j in range(10))
         for key in ('parties','delta','composition','intensity','interaction')}
    require(all(d==a+b+c for d,a,b,c in zip(agg['delta'],agg['composition'],agg['intensity'],agg['interaction'])),'aggregate decomposition')
    sv=sum(x['valid'] for x in output)
    supported={t.uuid for t in design.targets if t.status=='SUPPORTED'}
    selected={t.uuid for t in design.targets if t.status!='NOT_SELECTED'}
    native=[x for x in output if x['uuid'] in supported]
    native_counts=tuple(sum((x['parties'][j] for x in native),F(0)) for j in range(10))
    native_source=totals([r for r in rows if r.uuid in supported])
    return {'engine':'ABC','design_id':design.design_id,'source_id':design.frame.source_id,
            'reference_object_id':design.object_id,'lambda':lam,'mu':mu,'rows':tuple(output),
            'aggregate':agg,'source_parties':totals(rows),'source_valid':sum(r.valid for r in rows),
            'scenario_valid':sv,'scenario_shares':shares(agg['parties'],sv),
            'selected_targets':len(selected),'supported_targets':len(supported),
            'actually_transformed_units':sum(r['actually_transformed'] for r in output),
            'coverage':coverage([r for r in rows if r.uuid in supported], rows),
            'native':{'source_parties':native_source,'scenario_parties':native_counts,'scenario_valid':sum(native_counts)},
            'status':'APPLICABLE' if supported else 'NOT_APPLICABLE_ON_THIS_DESIGN'}


def A(design, lam): return transform(design,lam,0)
def B(design, mu): return transform(design,0,mu)
C=transform


def canonical_cells():
    from .common import SOURCES, LEVELS
    return tuple(product(SOURCES,DESIGNS,LEVELS,LEVELS))
