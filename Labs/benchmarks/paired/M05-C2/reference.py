from rdkit import Chem,DataStructs
from rdkit.Chem import rdFingerprintGenerator
m=[Chem.MolFromSmiles(s) for s in case_input['smiles']]; fs=[]
for chiral in [False,True]:
 g=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=2048,includeChirality=chiral);fs.append([g.GetFingerprint(x) for x in m])
f=DataStructs.TanimotoSimilarity; a,b=fs[1];answer={'achiral_score':f(*fs[0]),'chiral_score_below_one':f(a,b)<1,'symmetric':math.isclose(f(a,b),f(b,a)),'self_score':f(a,a)}