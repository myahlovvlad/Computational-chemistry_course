from pathlib import Path
import sys,json,csv
from rdkit import Chem,DataStructs
from rdkit.Chem import rdFingerprintGenerator
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'programm/course.json').is_file())
sys.path.insert(0,str(ROOT/'scripts'))
from train_target_qsar import scaffold
with (ROOT/'practicuum/shared/data/target_qsar/hmgcr_curated.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
mols=[Chem.MolFromSmiles(r['smiles']) for r in rows]
n=len(mols);g=len({scaffold(m) for m in mols})
result={'curated_HMGCR_n':n,'HMGCR_scaffolds':g,'training_eligible':n>=80 and g>=20,'model_training':'NOT_RUN'}
if __name__=='__main__':print(json.dumps(result,indent=2))
