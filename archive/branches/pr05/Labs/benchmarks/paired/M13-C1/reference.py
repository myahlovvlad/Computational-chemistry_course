from rdkit import Chem
from rdkit.Chem import rdChemReactions
r=rdChemReactions.ReactionFromSmarts('[C:1](=[O:2])[O:3][C:4]>>[C:1](=[O:2])[OH:3].[OH][C:4]');p=r.RunReactants((Chem.MolFromSmiles(case_input['smiles']),));names=[]
for m in p[0]:
 Chem.SanitizeMol(m)
 for a in m.GetAtoms():a.SetAtomMapNum(0)
 names.append(Chem.MolToSmiles(m))
answer={'precursors':sorted(names)}