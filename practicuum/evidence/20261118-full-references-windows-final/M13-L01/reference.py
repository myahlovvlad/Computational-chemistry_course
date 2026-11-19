from pathlib import Path
import sys,json,math
from IPython.display import display
ROOT=next(p for p in [Path(__file__).resolve().parent,*Path(__file__).resolve().parents] if (p/'programm/course.json').is_file())
sys.path.insert(0,str(ROOT/'practicuum/shared'))
from course_support import DATA,compound,esol,workspace,write_json,init_dossier
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
def publish_plot(fig,name):
    fig.savefig(OUT/name,dpi=120,bbox_inches='tight')
    display(fig)
    plt.close(fig)
OUT=workspace('M13-L01','instructor')

def reference():
    import csv
    with (DATA/'xanthine_synthesis_table1.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    result={'rows':len(rows),'reflux_zeros':sum(float(r['reflux_yield_percent'])==0 for r in rows),
            'microwave_zeros':sum(float(r['microwave_yield_percent'])==0 for r in rows),'B_yields':'NOT_AVAILABLE'}
    assert len(rows)==4
    return result

if __name__=="__main__":
    print(json.dumps(reference(),ensure_ascii=False,indent=2))
