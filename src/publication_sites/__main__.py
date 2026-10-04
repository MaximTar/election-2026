import argparse
from .generate import generate

def main():
    parser=argparse.ArgumentParser(description='Static publication export; no scientific execution')
    parser.add_argument('action',choices=['generate','check'])
    args=parser.parse_args()
    if args.action=='generate': generate()
    else:
        from .check import check
        check()

if __name__=='__main__':main()
