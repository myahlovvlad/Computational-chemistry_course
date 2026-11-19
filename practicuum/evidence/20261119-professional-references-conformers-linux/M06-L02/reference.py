from pathlib import Path
import json
from scipy import stats
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'programm/course.json').is_file())
D=ROOT/'practicuum/shared/data/conformer_research'
r=json.loads((D/'atorvastatin/result.json').read_text());checked=[h for h in r['hessian_results'] if h['status']=='PASS']
result={'acid_minimum_internal_frequency_cm1':min(h['lowest_frequency_cm1'] for h in checked),'acid_internal_mode_count':checked[0]['internal_mode_count'],'restricted_conformer_count':len(checked),'complete_population_claim_allowed':False}
if __name__=='__main__':print(json.dumps(result,indent=2))
