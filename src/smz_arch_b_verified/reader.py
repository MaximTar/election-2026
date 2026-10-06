"""Bounded research queries. No bulk result-loading default."""
from . import codec,basis
from .engine import row_from_record,_access
from .storage import need
from src.smz.common import NOT_DEFINED
class Reader:
    def __init__(self,store,run,token):self.store=store;self.run=run;self.token=token
    def get(self,name):return self.store.read(self.run,self.token,name)
    def cell(self,cell_id):return self.get('cells/'+cell_id)
    def surface(self,source,design):return self.store.read_many(self.run,self.token,tuple(f'cells/ABC:{source}:{design}:L{l}:M{m}' for l in range(5) for m in range(5)))
    def compare(self,ids):
        need(len(ids)<=8,'BOUNDED_COMPARISON');return self.store.read_many(self.run,self.token,tuple('cells/'+i for i in ids))
    def region(self,cell,region):return self.cell(cell)['scopes']['region:'+region]
    def target(self,cell_id,index):
        if cell_id.startswith('D:'):return NOT_DEFINED
        # One authenticated bounded transaction; no repeated whole-package traversal
        # per dependency. Requested chunks are still individually checked and closure
        # is rechecked before returning any reconstructed result.
        p,m,c,ch=self.store.verify(self.run);t=self.store._verify(self.token)
        need(t==dict(purpose='REVEAL',run=self.run,manifest=codec.digest(m),commit=ch,plan=c['plan'],contract=c['contract']),'REVEAL_BINDING')
        key=(self.store.root/'vault'/self.run).read_bytes()
        def get(name):
            need(name in m['artifacts'],'UNREGISTERED_QUERY')
            return self.store._decode(p,name,m['artifacts'][name],key,self.run)
        cell=get('cells/'+cell_id);source=cell['source_id'];design=cell['design_id']
        idx=get('source_frames/'+source+'/table/index');need(0<=index<idx['rows'],'ROW_INDEX')
        block=get(idx['chunks'][index//1024]);row=row_from_record(tuple(codec.records(block))[index%1024])
        root='abc_design/'+source+'/'+design
        statusidx=get(root+'/status/index');sblock=get(statusidx['chunks'][index//1024]);status=tuple(codec.records(sblock))[index%1024][2]
        b=None
        if status=='SUPPORTED':
            bidx=get(root+'/basis/index')
            for chunk in bidx['chunks']:
                for r in codec.records(get(chunk)):
                    if r[0]==index:b=r[1:];break
                if b is not None:break
            need(b is not None,'MISSING_SUPPORTED_BASIS')
        with _access((row,)):
            result=basis.reconstruct(row,status,b,cell['lambda_'],cell['mu'])
        need(self.store.verify(self.run)[3]==ch,'PACKAGE_CHANGED_DURING_QUERY')
        return result
