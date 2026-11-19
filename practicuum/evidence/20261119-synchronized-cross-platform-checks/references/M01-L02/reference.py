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
OUT=workspace('M01-L02','instructor')

def reference():
    rows=[r for r in esol() if r['row_id']%5==0]
    e=[r['predicted']-r['measured'] for r in rows]
    result={'n':len(rows),'mae':sum(abs(v) for v in e)/len(e),'rmse':math.sqrt(sum(v*v for v in e)/len(e))}
    assert result['rmse'] >= result['mae'] > 0
    return result

if __name__=="__main__":
    print(json.dumps(reference(),ensure_ascii=False,indent=2))
