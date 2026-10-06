"""Release-only constants; no outcome access on import/freeze/check."""
from pathlib import Path
import hashlib,json
import numpy as np
from src.stage3a_qualification.spec import ROOT,sha,write,plain
from src.stage3a_v2.spec import CONFIG as V2
OUT=ROOT/'outputs/stage3a_real_release/20260928'
PLAN=ROOT/'docs/REAL_STAGE3A_RELEASE_CONTRACT_20260928.md'
UNIVERSE=ROOT/'outputs/stage3a_v2/universe_20260927'
CFG=dict(namespace='real-stage3a-release-20260928-v1',universe=V2['universe'],
         party_order=V2['party_order'],responses=['issued','valid_given_issued',*V2['party_order']],
         B=1999,alpha=.05,calibration_cap=99,workers=1,numeric=dict(rtol=1e-10,atol=1e-12),
         preopen_namespace='preopen-equivalence-never-real-20260928-v1',
         L_B_usefulness='RETAIN_USER_ACCEPTED',real_execution_authorized=False)
def rng(*parts,namespace=None):
    raw=json.dumps([namespace or CFG['namespace'],*parts],ensure_ascii=False,separators=(',',':')).encode()
    return np.random.Generator(np.random.PCG64(int.from_bytes(hashlib.sha256(raw).digest()[:16],'big')))
def verify():
    from src.stage3a_qualification.spec import verify as older
    older();m=json.loads((OUT/'freeze/manifest.json').read_text())
    for p,h in m['files'].items():assert sha(ROOT/p)==h,p
    assert json.loads((OUT/'freeze/config.json').read_text())==CFG
    return m

