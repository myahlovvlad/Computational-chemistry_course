"""Download RCSB coordinate/metadata snapshots for target-specific redocking preparation."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import requests


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False);records=[]
    for pdb,compound in [('8RW0','istradefylline'),('1HWK','atorvastatin')]:
        folder=out/pdb;folder.mkdir()
        urls={'structure.cif':f'https://files.rcsb.org/download/{pdb}.cif',
              'entry.json':f'https://data.rcsb.org/rest/v1/core/entry/{pdb}'}
        for name,url in urls.items():
            response=requests.get(url,timeout=(20,120));response.raise_for_status();path=folder/name;path.write_bytes(response.content)
            records.append({'pdb':pdb,'compound':compound,'url':url,'file':path.relative_to(out).as_posix(),
                            'sha256':hashlib.sha256(response.content).hexdigest(),'bytes':len(response.content),
                            'created_utc':datetime.now(timezone.utc).isoformat(),'http_status':response.status_code,'licence':'wwPDB/RCSB CC0'})
        entry=json.loads((folder/'entry.json').read_text(encoding='utf-8'))
        if entry['rcsb_id']!=pdb:raise ValueError('PDB identity mismatch')
        entities=entry['rcsb_entry_container_identifiers']['non_polymer_entity_ids']
        for entity in entities:
            url=f'https://data.rcsb.org/rest/v1/core/nonpolymer_entity/{pdb}/{entity}'
            response=requests.get(url,timeout=(20,120));response.raise_for_status()
            path=folder/f'nonpolymer-{entity}.json';path.write_bytes(response.content)
            record={'pdb':pdb,'file':path.relative_to(out).as_posix(),'url':url,'sha256':hashlib.sha256(response.content).hexdigest(),
                    'licence':'wwPDB/RCSB CC0','created_utc':datetime.now(timezone.utc).isoformat()};records.append(record)
        print(pdb,compound,'coordinates and',len(entities),'ligand entity passports saved',flush=True)
    (out/'sources.json').write_text(json.dumps({'status':'PASS','sources':records,'scope':'coordinate/metadata acquisition, not prepared receptor or docking result'},indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
