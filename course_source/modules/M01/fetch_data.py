"""Download a checked public snapshot once, or verify/copy existing local bytes."""
import argparse
import json
from m01 import acquire,checksum,META

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--from-file')
    args=parser.parse_args()
    path=acquire(args.from_file)
    print(json.dumps({'file':str(path),'sha256':checksum(path),'source':META['url'],'rows':META['rows']},indent=2))
