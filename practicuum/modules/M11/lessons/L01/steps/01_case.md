# Разбор A. Реальная мишень, кристаллический лиганд и допуск рецептора

Объект — 8RW0, A2A в комплексе с истрадефиллином JQ9. Это инженерная кристаллическая конструкция A2A-StaR2-bRIL, не молекула дикого типа в мембране. [RCSB PDB 8RW0](https://www.rcsb.org/structure/8RW0) предоставляет координаты; первичная публикация и конструкция должны сопровождать интерпретацию. Лиганд нейтрален; стереохимический/полный граф сверены при подготовке с PubChem.

Все белковые цепи исходной конструкции сохранены, включая fusion-часть. pH=5.0 взят из кристаллизации, а не измерения протонов и не физиологического предположения. PDB2PQR AMBER/PROPKA подготовка, histidine naming и Meeko charges записаны в manifest. Удаление кристаллических вод, липидов и Na⁺ в текущей модели явно ограничивает выводы и требует sensitivity analysis.

```python
from pathlib import Path
import sys,json,hashlib,math
import numpy as np
from rdkit import Chem
from IPython.display import display
ROOT=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'programm/course.json').is_file())
sys.path.insert(0,str(ROOT/'practicuum/shared'))
from course_support import DATA,workspace,write_json,init_dossier
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=workspace('M11-L01','case');D=DATA/'target_docking'
manifest=json.loads((D/'manifest.json').read_text(encoding='utf-8'))
for name,digest in manifest['files_sha256'].items():
    assert hashlib.sha256((D/name).read_bytes()).hexdigest()==digest,name
def read_json(name):return json.loads((D/name).read_text(encoding='utf-8'))
def publish_plot(fig,name):
    fig.savefig(OUT/name,dpi=150,bbox_inches='tight');display(fig);plt.close(fig)
```

```python
# PDB columns describe original extracted protein coordinates, not a repaired receptor.
def protein_atoms(path):
    atoms=[]
    for line in path.read_text(encoding='utf-8').splitlines():
        if line[:6].strip()!='ATOM':continue
        if line[76:78].strip()=='H':continue
        atoms.append({'chain':line[21:22].strip(),'residue':line[17:20].strip(),
                      'residue_id':line[22:27].strip(),'atom':line[12:16].strip(),
                      'xyz':list(map(float,[line[30:38],line[38:46],line[46:54]]))})
    return atoms
def pocket_table(prefix):
    ligand=Chem.SDMolSupplier(str(D/(prefix+'_crystal_reference.sdf')),removeHs=True)[0]
    assert ligand is not None
    atoms=protein_atoms(D/(prefix+'_protein_crystal.pdb'))
    xyz=np.array([a['xyz'] for a in atoms]);ligand_xyz=np.array(ligand.GetConformer().GetPositions())
    distances=np.sqrt(np.sum((xyz[:,None,:]-ligand_xyz[None,:,:])**2,axis=2)).min(axis=1)
    selected=[{**a,'minimum_ligand_distance_A':float(v)} for a,v in zip(atoms,distances) if v<=6.]
    return ligand,selected
```

Проверим химическую форму и карман геометрически. Расстояние — минимум по тяжёлым атомам лиганда; радиус 6 Å является заранее заданной областью аудита, не доказательством контакта или энергии связывания. Не выравниваем лиганд отдельно от белка.

```python
ligand,selected=pocket_table('a2a')
print('Ligand heavy atoms / charge:',ligand.GetNumHeavyAtoms(),Chem.GetFormalCharge(ligand))
residues={}
for a in selected:
    key=(a['chain'],a['residue_id'],a['residue'])
    residues[key]=min(residues.get(key,float('inf')),a['minimum_ligand_distance_A'])
display(sorted([{'residue':key,'minimum_distance_A':v} for key,v in residues.items()],key=lambda r:r['minimum_distance_A']))
prepared=read_json('a2a_preparation.json')
print('Prepared construct chains:',prepared['protein_chains'],'residues:',prepared['protein_residues'])
print('Backbone gap audit:',prepared['backbone_gap_audit'])
nearest_repair=min(r['nearest_ligand_A'] for r in prepared['heavy_atom_repairs'])
print('Nearest rebuilt heavy atom / A:',nearest_repair)
assert nearest_repair>6
result={'kind':'calculated','scope':'original 8RW0 coordinate and preparation audit','pocket_heavy_atoms':len(selected),
        'pocket_residues':len(residues),'ligand_charge':Chem.GetFormalCharge(ligand),
        'protein_preparation_status':prepared['status'],'pose_validation':'separate M11-L02','affinity_measurement':'NOT_RUN'}
```

Допуск подготовки означает, что заданные проверки входа прошли; он не подтверждает позу, функцию scoring или физиологическую применимость. Требуется проверить отсутствующие концы/остатки, альтернативные протонные состояния и гидратацию. В B реальная подготовка 1HWK остановлена: замена структуры недоказанным исправлением недопустима.

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
print(append_record(init_dossier(),'M11-L01','A',result,ROOT,inputs=['practicuum/shared/data/target_docking/a2a_crystal_reference.sdf', 'practicuum/shared/data/target_docking/a2a_preparation.json', 'practicuum/shared/data/target_docking/a2a_protein_crystal.pdb', 'practicuum/shared/data/target_docking/a2a_protocol.json', 'practicuum/shared/data/target_docking/a2a_redocking.json', 'practicuum/shared/data/target_docking/hmgcr_crystal_reference.sdf', 'practicuum/shared/data/target_docking/hmgcr_failure.json', 'practicuum/shared/data/target_docking/hmgcr_gap_audit.json', 'practicuum/shared/data/target_docking/hmgcr_protein_crystal.pdb', 'practicuum/shared/data/target_docking/hmgcr_repair_audit.json', 'practicuum/shared/data/target_docking/manifest.json', 'practicuum/shared/data/target_docking/start-13-search-101.sdf', 'practicuum/shared/data/target_docking/start-13-search-202.sdf', 'practicuum/shared/data/target_docking/start-13-search-303.sdf', 'practicuum/shared/data/target_docking/start-37-search-101.sdf', 'practicuum/shared/data/target_docking/start-37-search-202.sdf', 'practicuum/shared/data/target_docking/start-37-search-303.sdf', 'practicuum/shared/data/target_docking/start-73-search-101.sdf', 'practicuum/shared/data/target_docking/start-73-search-202.sdf', 'practicuum/shared/data/target_docking/start-73-search-303.sdf']))
```
