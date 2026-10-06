"""Only common-import transport rebinding; qualified function ASTs unchanged."""
import ast
import json
import types
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[2]
Q = ROOT/'outputs/smz_v2_external_qualification/20261002_v1'


def transform(name):
    if name not in ['istories','cedar']:
        raise ValueError('FAMILY_NOT_AUTHORIZED')
    path = Q/'source_snapshot'/f'{name}.py'
    h = json.loads((Q/'implementation_freeze.json').read_text())['files'][f'src/smz_external_clite/{name}.py']
    if hashlib.sha256(path.read_bytes()).hexdigest() != h:
        raise RuntimeError('QUALIFIED_SOURCE_CHANGED')
    original = ast.parse(path.read_text())
    tree = ast.parse(path.read_text())
    for n in tree.body:
        if isinstance(n,ast.ImportFrom) and n.level==1 and n.module=='common':
            n.module='transport'
    a=[ast.dump(n,include_attributes=False) for n in original.body if isinstance(n,ast.FunctionDef)]
    b=[ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)]
    if a!=b:
        raise RuntimeError('QUALIFIED_FUNCTION_AST_CHANGED')
    return tree, {'name':name,'qualified_source_sha256':h,'all_function_AST_identical':True}


def load(name):
    from .transport import require_active
    require_active()
    tree,_=transform(name)
    m=types.ModuleType('src.smz_external_plus_a._authorized_'+name)
    m.__package__='src.smz_external_plus_a'
    exec(compile(tree,str(Q/'source_snapshot'/f'{name}.py'),'exec'),m.__dict__)
    return m
