from pathlib import Path
import json,numpy as np
from rdkit import Chem
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'programm/course.json').is_file())
D=ROOT/'practicuum/shared/data/target_docking'
m=Chem.SDMolSupplier(str(D/'hmgcr_crystal_reference.sdf'),removeHs=True)[0]
xyz=m.GetConformer().GetPositions();chains=set();count=0
for line in (D/'hmgcr_protein_crystal.pdb').read_text().splitlines():
    if line[:6].strip()!='ATOM' or line[76:78].strip()=='H':continue
    pos=np.array([float(line[30:38]),float(line[38:46]),float(line[46:54])])
    if np.linalg.norm(xyz-pos,axis=1).min()<=6:chains.add(line[21:22]);count+=1
result={'ligand_heavy_atoms':m.GetNumHeavyAtoms(),'ligand_formal_charge':Chem.GetFormalCharge(m),'pocket_chain_count':len(chains),'original_pocket_heavy_atoms':count}
if __name__=='__main__':print(json.dumps(result,indent=2))
