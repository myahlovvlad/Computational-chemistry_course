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
OUT=workspace('M05-L02','instructor')

def reference():
    points={'acid':(.9,.4),'lactone':(.7,.8),'salt':(.5,.3)}
    selected=[n for n,p in points.items() if not any(all(a>=b for a,b in zip(q,p)) and any(a>b for a,b in zip(q,p)) for k,q in points.items() if k!=n)]
    result={'frontier':sorted(selected),'n':len(selected),'kind':'simulation'}
    assert set(selected)=={'acid','lactone'}
    return result

if __name__=="__main__":
    print(json.dumps(reference(),ensure_ascii=False,indent=2))
