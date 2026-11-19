from pathlib import Path
import sys,json,csv
import numpy as np
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'programm/course.json').is_file())
with (ROOT/'practicuum/shared/data/atorvastatin_hplc_table1.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
factors=np.array([[float(r[k]) for k in ['acetonitrile_percent','column_temperature_C','flow_mL_min']] for r in rows])
sys.path.insert(0,str(ROOT/'scripts'))
from analyze_hplc_research import fit_response
m=fit_response(factors,np.array([float(r['retention_ATO_lactone_min']) for r in rows]))
result={'rows':m['n'],'columns':m['p'],'rank':m['rank'],'pure_error_df':m['pure_error_df'],'lack_of_fit_df':m['lack_of_fit_df'],'held_condition_RMSE_min':m['held_condition_RMSE'],'lack_of_fit_p':m['lack_of_fit_p'],'adequacy':m['adequacy'],'mean_CI95':m['center_mean_CI95'],'new_observation_PI95':m['center_new_injection_PI95']}
if __name__=='__main__':print(json.dumps(result,indent=2))
