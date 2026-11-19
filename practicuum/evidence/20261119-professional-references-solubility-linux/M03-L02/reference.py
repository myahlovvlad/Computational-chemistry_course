"""Расчётный ориентир карты форм; реальная гидратация/чистота не установлены."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[6]
sys.path.insert(0,str(ROOT/'practicuum/shared'))
from course_support import compound
from rdkit import Chem,rdBase
from rdkit.Chem import Descriptors,rdMolDescriptors

def properties(mol):
    return {'formula':rdMolDescriptors.CalcMolFormula(mol),'MW_g_mol':Descriptors.MolWt(mol),
        'charge':Chem.GetFormalCharge(mol),'smiles':Chem.MolToSmiles(mol,isomericSmiles=True)}

def reference():
    rows=[]
    for name in ['atorvastatin','atorvastatin_calcium','atorvastatin_lactone']:
        record=compound(name);mol=Chem.MolFromSmiles(record['smiles'])
        if mol is None:raise ValueError(name)
        fragments=list(Chem.GetMolFrags(mol,asMols=True))
        rows.append({'name':name,'source':record['source_url'],**properties(mol),
                     'fragments':[properties(part) for part in fragments]})
    acid,salt,lactone=rows
    assert [p['charge'] for p in salt['fragments']]==[-1,-1,2]
    assert sum(p['charge'] for p in salt['fragments'])==salt['charge']==0
    assert len(salt['fragments'])==3
    assert abs((acid['MW_g_mol']-lactone['MW_g_mol'])-18.015)<1e-6
    return {'forms':rows,'rdkit':rdBase.rdkitVersion,'organic_equivalents_per_salt_record':2,
        'acid_equivalent_mass_fraction_ideal_anhydrous':2*acid['MW_g_mol']/salt['MW_g_mol'],
        'real_sample_hydration':'NOT_RUN','real_sample_identity':'NOT_RUN','scientific_explanation_review':'NOT_RUN'}

if __name__=='__main__':print(json.dumps(reference(),ensure_ascii=False,indent=2))
