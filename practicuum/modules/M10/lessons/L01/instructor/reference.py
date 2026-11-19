from pathlib import Path
import sys,json,csv
import numpy as np
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'programm/course.json').is_file())
with (ROOT/'practicuum/shared/data/atorvastatin_hplc_table1.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
factors=np.array([[float(r[k]) for k in ['acetonitrile_percent','column_temperature_C','flow_mL_min']] for r in rows])
gaps=[float(r['retention_ATO_lactone_min'])-float(r['retention_p_ATO_min']) for r in rows]
result={'unique_conditions':len(np.unique(factors,axis=0)),'minimum_retention_gap_min':min(gaps),'maximum_retention_gap_min':max(gaps),'measured_Rs':'NOT_CALCULABLE'}
if __name__=='__main__':print(json.dumps(result,indent=2))
