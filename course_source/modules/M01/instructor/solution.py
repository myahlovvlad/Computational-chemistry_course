"""Instructor reference: actual numbers and artifacts, not automatic essay grading."""
from pathlib import Path
import csv
import json
import math
import statistics
import sys

MODULE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(MODULE))
from m01 import read_rows,prepare_import_case,locate_snapshot,checksum

def metrics(errors):
    return {'MAE_logS':statistics.mean(abs(e) for e in errors),
            'RMSE_logS':math.sqrt(statistics.mean(e*e for e in errors))}

def run(output):
    import matplotlib.pyplot as plt
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    source=locate_snapshot();before=checksum(source)
    rows=[r for r in read_rows(source) if r['row_id']%4==1]
    errors=[r['predicted']-r['measured'] for r in rows]
    result=metrics(errors)
    worst=max(rows,key=lambda r:abs(r['predicted']-r['measured']))
    result.update(rows=len(rows),row_ids=[r['row_id'] for r in rows],largest_row_id=worst['row_id'],
                  largest_record=worst,fold_gap=10**abs(worst['predicted']-worst['measured']))
    with (output/'case1_residuals.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['row_id','name','measured','predicted','residual'])
        writer.writeheader()
        writer.writerows({**{k:r[k] for k in ['row_id','name','measured','predicted']},'residual':e} for r,e in zip(rows,errors))
    fig,ax=plt.subplots(figsize=(7,5));ax.scatter([r['measured'] for r in rows],[r['predicted'] for r in rows],s=18,alpha=.6)
    ax.plot([-10,3],[-10,3],'k--');ax.set(xlabel='Measured log10(S/(mol/L))',ylabel='Archived predicted log10(S/(mol/L))')
    fig.savefig(output/'case1_parity.png',dpi=140);plt.close(fig)
    fault=prepare_import_case(rows)
    wrong=[r['reported_logS']-r['measured'] for r in fault['rows']]
    repaired=[math.log10(r['reported_logS']) for r in fault['rows']]
    after=[pred-r['measured'] for pred,r in zip(repaired,fault['rows'])]
    assert all(math.isclose(p,r['predicted'],abs_tol=1e-12) for p,r in zip(repaired,rows))
    assert math.isclose(metrics(after)['MAE_logS'],result['MAE_logS'],abs_tol=1e-12)
    assert checksum(source)==before
    with (output/'case2_repaired.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(['row_id','reported_linear_mol_L','repaired_logS','measured_logS'])
        writer.writerows([r['row_id'],r['reported_logS'],p,r['measured']] for r,p in zip(fault['rows'],repaired))
    answer={'case1':result,'case2':{'fault_kind':'synthetic import mismatch, not a source error',
             'before_repair':metrics(wrong),'after_repair':metrics(after),'raw_unchanged':True,'source_sha256':before},
            'case3':{'status':'NOT_RUN','reason':'Independent scientific artifact and human assessment required; see RUBRIC.md'},
            'scope':'author numeric reference; no learner completion or independent ESOL test accuracy claimed'}
    (output/'reference_results.json').write_text(json.dumps(answer,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(answer,ensure_ascii=False,indent=2))
    return answer

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args().output)
