"""Two fully specified predictive count models, not clean-baseline estimators."""
import numpy as np
from scipy import sparse
from scipy.optimize import minimize
from scipy.special import expit, softmax, gammaln, betaln, digamma, logsumexp
from scipy.stats import betabinom
from .spec import CONFIG
from .generators import multinomial_rows


def bb_log(k, n, a, b):
    return gammaln(n+1)-gammaln(k+1)-gammaln(n-k+1)+betaln(k+a, n-k+b)-betaln(a, b)


def dm_log(k, alpha):
    n = k.sum(axis=-1); total = alpha.sum(axis=-1)
    return (gammaln(n+1)-gammaln(k+1).sum(axis=-1)+gammaln(total)-gammaln(n+total)
            +(gammaln(k+alpha)-gammaln(alpha)).sum(axis=-1))


class Basis:
    def __init__(self, d):
        self.regions = {x: i for i, x in enumerate(sorted(d.region.unique()))}
        self.tiks = {x: i for i, x in enumerate(sorted(d.tik_uuid.unique()))}
        self.width = 6+len(self.regions)+len(self.tiks)
        sd = CONFIG['H']['prior_sd']
        self.penalty = 1/np.square([sd[0]]+[sd[1]]*5+[sd[2]]*len(self.regions)+[sd[3]]*len(self.tiks))

    def matrix(self, d):
        z = np.clip(np.log(d.voters.to_numpy()/1000.), -5, 5)
        base = np.column_stack([np.ones(len(d)), z, np.sin(z), np.cos(z), np.sin(2*z), np.cos(2*z)])
        rows=[]; cols=[]
        for i, (r, t) in enumerate(zip(d.region, d.tik_uuid)):
            if r in self.regions: rows.append(i); cols.append(6+self.regions[r])
            if t in self.tiks: rows.append(i); cols.append(6+len(self.regions)+self.tiks[t])
        group = sparse.csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(len(d), self.width))
        return group+sparse.hstack([sparse.csr_matrix(base), sparse.csr_matrix((len(d), self.width-6))], format='csr')


def objective(beta, X, counts, denominators, precision, penalty, composition):
    W = beta.reshape(X.shape[1], 10) if composition else beta
    eta = X@W
    if composition:
        p = softmax(eta, axis=1); a = precision*p
        ll = dm_log(counts, a)
        h = digamma(counts+a)-digamma(a)
        g = precision*p*(h-(p*h).sum(axis=1, keepdims=True))
        grad = -X.T@g+penalty[:, None]*W
        reg = .5*np.sum(penalty[:, None]*W*W)
    else:
        p = expit(eta); q = expit(-eta); a = precision*p; b = precision*q
        ll = bb_log(counts, denominators, a, b)
        h = digamma(counts+a)-digamma(a)-digamma(denominators-counts+b)+digamma(b)
        g = precision*p*q*h
        grad = -X.T@g+penalty*W; reg = .5*np.sum(penalty*W*W)
    # Scale likelihood AND penalty equally: identical MAP, stable numerical tolerance
    # across training sizes. Acceptance is for gradient of this mean objective.
    return float((-ll.sum()+reg)/len(counts)), np.asarray(grad).ravel()/len(counts)


class HCount:
    def fit(self, d, y):
        if not y.get('synthetic', False): raise RuntimeError('Real-response fit prohibited')
        self.basis = Basis(d); X=self.basis.matrix(d); n=d.voters.to_numpy()
        self.parameters=[]; self.diagnostics=[]
        settings=CONFIG['H']
        for j, (counts, den) in enumerate([(y['issued'], n), (y['valid'], y['issued']), (y['votes'], y['valid'])]):
            composition = j == 2; length=X.shape[1]*(10 if composition else 1)
            result=minimize(objective, np.zeros(length), args=(X, counts, den, settings['precision'][j], self.basis.penalty, composition),
                            jac=True, method='L-BFGS-B', bounds=[(-settings['logit_bound'], settings['logit_bound'])]*length,
                            options={k: settings[k] for k in ['maxiter', 'maxls', 'gtol', 'ftol']})
            gradient=np.max(np.abs(result.jac))
            ok=bool(result.success and np.isfinite(result.fun) and np.isfinite(result.x).all()
                    and gradient <= settings['gradient_acceptance'] and np.max(np.abs(result.x)) < settings['logit_bound']-1e-6)
            self.diagnostics.append({'success': ok, 'iterations': int(result.nit), 'gradient': float(gradient), 'message': str(result.message)})
            self.parameters.append(result.x.reshape(X.shape[1], 10) if composition else result.x)
        self.success=all(x['success'] for x in self.diagnostics)
        return self

    def component(self, d, row):
        X=self.basis.matrix(d.iloc[[row]])
        eI=float((X@self.parameters[0])[0]); eV=float((X@self.parameters[1])[0]); pC=softmax(X@self.parameters[2], axis=1)[0]
        kI,kV,kC=CONFIG['H']['precision']
        return np.array([1.]), np.array([[kI*expit(eI),kI*expit(-eI)]]), np.array([[kV*expit(eV),kV*expit(-eV)]]), np.array([kC*pC])


class LPeer:
    def fit(self, d, y):
        if not y.get('synthetic', False): raise RuntimeError('Real-response fit prohibited')
        self.d=d.reset_index(drop=True);self.y=y;self.success=len(d)>=CONFIG['L']['min_pool']
        self.diagnostics=[{'success': self.success, 'algorithm': 'closed_form_mixture'}]
        return self

    def neighbours(self, d, row):
        v=d.iloc[row]; s=CONFIG['L']; pool=np.flatnonzero(self.d.tik_uuid==v.tik_uuid); level='tik'
        if len(pool)<s['min_pool']: pool=np.flatnonzero(self.d.region==v.region);level='region'
        if len(pool)<s['min_pool']: pool=np.arange(len(self.d));level='global'
        if len(pool)<s['min_pool']: raise ValueError('UNSUPPORTED')
        distances=np.abs(np.log(self.d.voters.to_numpy()[pool]/v.voters))
        order=np.lexsort((self.d.uuid.to_numpy()[pool], distances))[:s['k']]
        ix=pool[order];distances=distances[order];h=max(s['min_bandwidth'], float(distances.max()))
        w=np.exp(-.5*(distances/h)**2);w/=w.sum()
        return ix,w,level

    def component(self, d, row):
        ix,w,_=self.neighbours(d,row);v=self.d.voters.to_numpy()[ix];I=self.y['issued'][ix];V=self.y['valid'][ix]
        c=CONFIG['L']['pseudocount']
        return w,np.column_stack([I+c,v-I+c]),np.column_stack([V+c,I-V+c]),self.y['votes'][ix]+c


def predictive(model, d, y, row, random):
    """Conditional factor scores and discrete randomized PIT; no UIK iid SE."""
    w,abI,abV,alpha=model.component(d,row)
    I=int(y['issued'][row]);V=int(y['valid'][row]);C=y['votes'][row];n=int(d.voters.iloc[row])
    fI=bb_log(I,n,abI[:,0],abI[:,1]);fV=bb_log(V,I,abV[:,0],abV[:,1]);fC=dm_log(C,alpha)
    # Same donor defines the joint mixture; posterior donor weights for conditionals.
    logw=np.log(w);lI=logsumexp(logw+fI)
    lIV=logsumexp(logw+fI+fV);joint=logsumexp(logw+fI+fV+fC)
    wI=np.exp(logw+fI-lI);wIV=np.exp(logw+fI+fV-lIV)
    total=alpha.sum(axis=1)
    params=[(w,n,abI[:,0],abI[:,1],I),(wI,I,abV[:,0],abV[:,1],V)]
    params += [(wIV,V,alpha[:,j],total-alpha[:,j],int(C[j])) for j in range(10)]
    mean=[];pit=[];coverage=[];width=[];crps=[]
    B=CONFIG['predictive_draws']
    for weights,den,a,b,obs in params:
        idx=random.choice(len(weights),size=B,p=weights)
        sample=random.binomial(den,random.beta(a[idx],b[idx]))
        lo,hi=np.quantile(sample,[.025,.975],method='inverted_cdf')
        cdf=float(np.dot(weights,betabinom.cdf(obs-1,den,a,b)))
        mass=float(np.dot(weights,np.exp(bb_log(obs,den,a,b))))
        pit.append(cdf+random.random()*mass);coverage.append(bool(lo<=obs<=hi));width.append(float(hi-lo))
        mean.append(float(den*np.dot(weights,a/(a+b))))
        # CRPS Monte Carlo estimate using two independent predictive samples.
        ix2=random.choice(len(weights),size=B,p=weights)
        second=random.binomial(den,random.beta(a[ix2],b[ix2]))
        crps.append(float(np.abs(sample-obs).mean()-.5*np.abs(sample-second).mean()))
    return {'log_score_joint': float(-joint), 'log_scores': [float(-lI),float(lI-lIV),float(lIV-joint)],
            'mean':mean,'pit':pit,'coverage':coverage,'width':width,'crps_marginals':crps,
            'observed':[I,V,*C.tolist()]}


def subset(y, ix):
    return {k: (v[ix] if isinstance(v,np.ndarray) and v.shape[0]==len(y['issued']) else v) for k,v in y.items()}
