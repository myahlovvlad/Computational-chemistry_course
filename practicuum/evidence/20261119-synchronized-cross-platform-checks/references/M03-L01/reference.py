"""Вычислительная часть ответа B; не оценивает объяснение студента."""
from pathlib import Path
import sys,json

ROOT=Path(__file__).resolve().parents[6]
sys.path.insert(0,str(ROOT/'practicuum/shared'))
from course_support import compound
from rdkit import Chem,rdBase
from rdkit.Chem import Descriptors,rdMolDescriptors

def reference():
    record=compound('atorvastatin')
    mol=Chem.MolFromSmiles(record['smiles'])
    if mol is None:raise ValueError('Не разобрана исходная запись')
    stereo=Chem.MolToSmiles(mol,isomericSmiles=True)
    no_stereo=Chem.MolToSmiles(mol,isomericSmiles=False)
    simplified=Chem.MolFromSmiles(no_stereo)
    assert rdMolDescriptors.CalcMolFormula(mol)==rdMolDescriptors.CalcMolFormula(simplified)
    assert abs(Descriptors.MolWt(mol)-Descriptors.MolWt(simplified))<1e-9
    assert stereo!=Chem.MolToSmiles(simplified,isomericSmiles=True)
    centers=Chem.FindMolChiralCenters(mol,includeUnassigned=True)
    return {'source':record,'rdkit':rdBase.rdkitVersion,
        'formula':rdMolDescriptors.CalcMolFormula(mol),'MW_g_mol':Descriptors.MolWt(mol),
        'chiral_centers_graph_indices':centers,'canonical_isomeric':stereo,
        'connectivity_only':no_stereo,'explanation_review':'NOT_RUN',
        'sample_identity_experiment':'NOT_RUN'}

if __name__=='__main__':print(json.dumps(reference(),ensure_ascii=False,indent=2))
