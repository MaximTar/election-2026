"""L donor mixture only. Same-donor sequential joint count law."""
import numpy as np
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


class LPeer:
    def fit(self, d, y):
        if not y.get('synthetic', False): raise RuntimeError('Real-response fit prohibited')
        self.d=d.reset_index(drop=True);self.y=y;self.success=len(d)>=CONFIG['L']['min_pool']
        self.diagnostics=[{'success': self.success, 'algorithm': 'closed_form_mixture'}]
        return self

    def neighbours(self, d, row):
        cache=getattr(self,'_neighbour_cache',None)
        if cache is not None and row in cache:return cache[row]
        v=d.iloc[row]; s=CONFIG['L']; pool=np.flatnonzero(self.d.tik_uuid==v.tik_uuid); level='tik'
        if len(pool)<s['min_pool']: pool=np.flatnonzero(self.d.region==v.region);level='region'
        if len(pool)<s['min_pool']: pool=np.arange(len(self.d));level='global'
        if len(pool)<s['min_pool']: raise ValueError('UNSUPPORTED')
        distances=np.abs(np.log(self.d.voters.to_numpy()[pool]/v.voters))
        order=np.lexsort((self.d.uuid.to_numpy()[pool], distances))[:s['k']]
        ix=pool[order];distances=distances[order];h=max(s['min_bandwidth'], float(distances.max()))
        w=np.exp(-.5*(distances/h)**2);w/=w.sum()
        result=(ix,w,level)
        if cache is not None:cache[row]=result
        return result

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
