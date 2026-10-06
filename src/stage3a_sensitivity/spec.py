import json
from src.stage3a_real.spec import ROOT,sha,write,CFG as REAL,verify as verify_primary
OUT=ROOT/'outputs/stage3a_sensitivity/20260928'
PLAN=ROOT/'docs/STAGE3A_SENSITIVITY_CONTRACT_20260928.md'
PRIMARY=ROOT/'outputs/stage3a_real/20260928_real_stage3a_primary_01'
UF=ROOT/'outputs/stage3a_v2/universe_20260927'
CFG=dict(variants=['S1','S2a','S2b'],identity_variant='S3',namespace='sensitivity-transport-only-20260928-v1',
         scenarios=[f'N{i}' for i in range(1,11)],partial_scenarios=[f'N{i}' for i in range(1,9)],
         replicate=0,fold_rule='(scenario_number-1)%5',targets_per_cell=1,deadline_seconds=3600,
         real_namespace=REAL['namespace'],numeric=REAL['numeric'],real_authorized=False,
         no_retry=True,full_calibration=False)
def read(p):return json.loads(p.read_text())
def verify():
    verify_primary()
    m=read(OUT/'freeze/manifest.json')
    for p,h in m['files'].items():assert sha(ROOT/p)==h,p
    for p,h in read(OUT/'sources/manifest.json')['files'].items():assert sha(ROOT/p)==h,p
    assert sha(PRIMARY/'manifest.json')=='8cb660c19a8774a53cedc10ab034d732383781876fbadb194194ba0ac87fa61a'
    assert read(OUT/'freeze/config.json')==CFG
    return m
