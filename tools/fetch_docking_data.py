"""Fetch official Vina teaching data at a pinned upstream commit."""
import hashlib
import json
from pathlib import Path
import urllib.request

REPO = "forlilab/AutoDock-Vina"
headers = {"User-Agent":"computational-chemistry-course"}
request = urllib.request.Request(f"https://api.github.com/repos/{REPO}/commits/develop",headers=headers)
with urllib.request.urlopen(request,timeout=60) as response:
    commit = json.load(response)['sha']
destination = Path('Labs/datasets/docking')
destination.mkdir(parents=True,exist_ok=True)
names=['1iep_receptor.pdbqt','1iep_ligand.pdbqt','1iep_ligand.sdf',
       '1iep_ligand_vina_out.pdbqt','1iep_receptor.box.txt']
manifest=[]
for name in names:
    url=f'https://raw.githubusercontent.com/{REPO}/{commit}/example/basic_docking/solution/{name}'
    with urllib.request.urlopen(url,timeout=60) as response:
        data=response.read()
    (destination/name).write_bytes(data)
    manifest.append({'file':name,'source':url,'sha256':hashlib.sha256(data).hexdigest()})
for remote,local in [('LICENSE','UPSTREAM_LICENSE.txt')]:
    url=f'https://raw.githubusercontent.com/{REPO}/{commit}/{remote}'
    with urllib.request.urlopen(url,timeout=60) as response:
        (destination/local).write_bytes(response.read())
(destination/'provenance.json').write_text(json.dumps({'repository':REPO,'commit':commit,'files':manifest},indent=2),encoding='utf-8')
print('Fetched',len(names),'files at',commit)
