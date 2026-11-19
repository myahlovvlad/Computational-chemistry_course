from pathlib import Path
import json
from scipy import stats
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'programm/course.json').is_file())
D=ROOT/'practicuum/shared/data/conformer_research'
result={}
for state in ['atorvastatin','atorvastatin_anion','atorvastatin_lactone']:
    rows=json.loads((D/state/'singlepoint_results.json').read_text())
    valid=[r for r in rows if r['status']=='PASS' and r['MMFF_status']==0]
    result[state+'_descriptive_rank_correlation']=float(stats.spearmanr([r['MMFF_energy_kcal_mol'] for r in valid],[r['energy_hartree'] for r in valid]).statistic)
if __name__=='__main__':print(json.dumps(result,indent=2))
