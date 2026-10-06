"""Mechanically bind unchanged qualified numerical function AST to real transport.

No new estimator implementation. No module is compiled/imported by the pre-real
metadata checker. All model functions remain byte-for-byte AST-equivalent.
"""
import ast,hashlib,json,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
Q=ROOT/'outputs/smz_v2_external_qualification/20261002_v1'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def transform(name):
    path=Q/'source_snapshot'/f'{name}.py'
    expected=json.loads((Q/'implementation_freeze.json').read_text())['files'][f'src/smz_external_clite/{name}.py']
    if sha(path)!=expected:raise RuntimeError('QUALIFIED_KERNEL_CHANGED')
    original=ast.parse(path.read_text());tree=ast.parse(path.read_text())
    output=[]
    for node in tree.body:
        if isinstance(node,ast.ClassDef) and node.name in ['SyntheticHistogram','SyntheticPoints']:continue
        if name=='gmm2d' and isinstance(node,ast.FunctionDef) and node.name=='budget_gate':
            node=ast.parse('def budget_gate():\n    from .transport import require_active\n    require_active()\n').body[0]
        if isinstance(node,ast.ImportFrom) and node.level==1 and node.module=='common':node.module='transport'
        output.append(node)
    if name=='gaussian1d':output.insert(0,ast.parse('from .transport import InputHistogram as SyntheticHistogram').body[0])
    if name=='gmm2d':output.insert(0,ast.parse('from .transport import InputPoints as SyntheticPoints').body[0])
    tree.body=output;ast.fix_missing_locations(tree)
    a={n.name:ast.dump(n,include_attributes=False) for n in original.body if isinstance(n,ast.FunctionDef) and n.name!='budget_gate'}
    b={n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name!='budget_gate'}
    if a!=b:raise RuntimeError('NUMERICAL_FUNCTION_AST_CHANGED')
    return tree,{'module':name,'qualified_source_sha256':expected,'numerical_function_count':len(a),
                 'all_numerical_function_AST_identical':True,
                 'transport_only_changes':['common import binding','typed input constructors','2D execution budget gate']}
def equivalence_check():
    return {'status':'PASS','modules':[transform(n)[1] for n in ['istories','cedar','gaussian1d','gmm2d']],
            'compiled_or_executed':False,'model_calls':0}
def load(name):
    from .transport import require_active
    require_active();tree,_=transform(name)
    module=types.ModuleType('src.smz_external_real._authorized_'+name)
    module.__package__='src.smz_external_real';module.__file__=str(Q/'source_snapshot'/f'{name}.py')
    exec(compile(tree,module.__file__,'exec'),module.__dict__)
    return module
