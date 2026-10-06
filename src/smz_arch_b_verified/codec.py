"""Canonical exact binary records; column blocks; no pickle/float/decimal bigint limit."""
import hashlib,struct,zlib
from fractions import Fraction as F
from src.smz.common import Missing
VERSION='SMZ_EXACT_COLUMNAR_1'
def uint(n):
    assert n>=0
    b=bytearray()
    while n>=128:b.append((n&127)|128);n>>=7
    b.append(n);return bytes(b)
def encode(x):
    if x is None:return b'n'
    if type(x) is bool:return b't' if x else b'f'
    if type(x) is int:
        b=abs(x).to_bytes((abs(x).bit_length()+7)//8,'big');return (b'-' if x<0 else b'+')+uint(len(b))+b
    if isinstance(x,F):return b'r'+encode(x.numerator)+encode(x.denominator)
    if isinstance(x,Missing):return b'm'+encode(x.status)+encode(x.reason)
    if type(x) is str:
        b=x.encode();return b's'+uint(len(b))+b
    if type(x) is bytes:return b'b'+uint(len(x))+x
    if isinstance(x,(tuple,list)):return b'l'+uint(len(x))+b''.join(encode(v) for v in x)
    if type(x) is dict:
        assert all(type(k) is str for k in x)
        return b'd'+uint(len(x))+b''.join(encode(k)+encode(x[k]) for k in sorted(x))
    raise TypeError('UNSUPPORTED_EXACT_TYPE:'+type(x).__name__)
def decode(b):
    pos=0
    def u():
        nonlocal pos
        v=shift=0
        while True:
            c=b[pos];pos+=1;v|=(c&127)<<shift
            if c<128:return v
            shift+=7
    def get():
        nonlocal pos
        t=b[pos:pos+1];pos+=1
        if t==b'n':return None
        if t in (b't',b'f'):return t==b't'
        if t in (b'+',b'-',b's',b'b'):
            n=u();v=b[pos:pos+n];pos+=n
            if t==b's':return v.decode()
            if t==b'b':return v
            return int.from_bytes(v,'big')*(-1 if t==b'-' else 1)
        if t==b'r':return F(get(),get())
        if t==b'm':return Missing(get(),get())
        if t==b'l':return tuple(get() for _ in range(u()))
        if t==b'd':return {get():get() for _ in range(u())}
        raise ValueError('EXACT_CODEC_TAG')
    value=get()
    if pos!=len(b) or encode(value)!=b:raise ValueError('NONCANONICAL_EXACT_STREAM')
    return value
def sha(b):return hashlib.sha256(b).hexdigest()
def digest(x):return sha(encode(x))
def columnar(rows,fields):
    rows=list(rows)
    return dict(schema=VERSION,fields=tuple(fields),rows=len(rows),columns=tuple(tuple(r[j] for r in rows) for j in range(len(fields))))
def records(block):
    assert block['schema']==VERSION and len(block['columns'])==len(block['fields'])
    assert all(len(c)==block['rows'] for c in block['columns'])
    return zip(*block['columns'])
def pack(x):return zlib.compress(encode(x),6)
def unpack(b):return decode(zlib.decompress(b))
