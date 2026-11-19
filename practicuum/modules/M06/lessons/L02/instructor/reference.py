from pathlib import Path
import sys,json
import numpy as np
from rdkit import Chem
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'programm/course.json').is_file())
sys.path.insert(0,str(ROOT/'practicuum/shared'))
from conformer_ensemble import projected_frequencies
D=ROOT/'practicuum/shared/data/conformer_research/atorvastatin'
checks=[]
for row in json.loads((D/'result.json').read_text())['hessian_results']:
    i=row['source_id'];mol=Chem.MolFromXYZBlock((D/f'geometry_{i:04}.xyz').read_text());n=mol.GetNumAtoms()
    lines=(D/f'hessian_{i:04}_Eh_bohr2.txt').read_text().splitlines()
    H=np.fromstring(' '.join(line for line in lines if not line.startswith('$')),sep=' ').reshape(3*n,3*n)
    actual=projected_frequencies(H,mol.GetConformer().GetPositions(),[a.GetMass() for a in mol.GetAtoms()])
    if not actual['minimum_verified']:raise ValueError('Negative internal curvature')
    checks.append(actual)
result={'acid_minimum_internal_frequency_cm1':min(c['lowest_frequency_cm1'] for c in checks),
        'acid_internal_mode_count':checks[0]['internal_mode_count'],'restricted_conformer_count':len(checks),
        'complete_population_claim_allowed':False}
if __name__=='__main__':print(json.dumps(result,indent=2))
