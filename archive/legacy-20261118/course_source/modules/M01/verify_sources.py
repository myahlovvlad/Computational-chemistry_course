"""Verify pinned official source bytes and repository license, without republishing CSV."""
import argparse
import csv
from datetime import datetime,timezone
import hashlib
import io
import json
from pathlib import Path
import platform
import sys
import urllib.request

from m01 import META,MEASURED,PREDICTED

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    records=[]
    sources=[('snapshot',META['url'],META['sha256']),
             ('repository_license',META['url'].replace('datasets/delaney-processed.csv','LICENSE'),
              'e93ec2f869cea11536743939feb7943e195096ea363e16298620d4622046631f')]
    for name,url,expected in sources:
        with urllib.request.urlopen(url,timeout=60) as response:
            content=response.read();http_status=response.status
        actual=hashlib.sha256(content).hexdigest()
        record={'name':name,'url':url,'expected_sha256':expected,'actual_sha256':actual,
                'bytes':len(content),'http_status':http_status,'status':'PASS' if actual==expected else 'FAIL'}
        if name=='snapshot':
            rows=list(csv.DictReader(io.StringIO(content.decode('utf-8'))))
            record.update(rows=len(rows),columns=list(rows[0]),numeric_columns=[MEASURED,PREDICTED])
        records.append(record)
    result={'argv':[sys.executable,*sys.argv],'utc':datetime.now(timezone.utc).isoformat(),
            'python':sys.version,'platform':platform.platform(),'checks':records,
            'scope':'official byte identity and repository license only; not an independent ACS reuse grant',
            'status':'PASS' if all(r['status']=='PASS' for r in records) else 'FAIL'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
    print(json.dumps(result,indent=2))
    if result['status']!='PASS':raise SystemExit(1)

if __name__=='__main__':main()
