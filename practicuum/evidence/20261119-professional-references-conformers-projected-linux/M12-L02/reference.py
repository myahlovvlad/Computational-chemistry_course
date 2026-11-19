from pathlib import Path
import sys,json,csv
from rdkit import Chem,DataStructs
from rdkit.Chem import rdFingerprintGenerator
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'programm/course.json').is_file())
sys.path.insert(0,str(ROOT/'scripts'))
from train_target_qsar import scaffold
with (ROOT/'practicuum/shared/data/target_qsar/hmgcr_curated.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
mols=[Chem.MolFromSmiles(r['smiles']) for r in rows]
compounds=json.loads((ROOT/'practicuum/shared/data/compounds.json').read_text(encoding='utf-8'))
queries=[Chem.MolFromSmiles(next(r for r in compounds if r['name']==name)['smiles']) for name in ['atorvastatin','atorvastatin_lactone']]
excluded={scaffold(m) for m in queries};reference=[m for m in mols if scaffold(m) not in excluded]
gen=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=2048,includeChirality=True)
fps=[gen.GetFingerprint(m) for m in reference]
nearest=[max(DataStructs.BulkTanimotoSimilarity(gen.GetFingerprint(m),fps)) for m in queries]
result={'reference_n_after_query_scaffold_exclusion':len(reference),'acid_nearest_reference_Tanimoto':nearest[0],'lactone_nearest_reference_Tanimoto':nearest[1],'model_training':'NOT_RUN'}
if __name__=='__main__':print(json.dumps(result,indent=2))
