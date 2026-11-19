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
OUT=workspace('M04-L02','instructor')

def reference():
    ratio=10**(5.5-4.5)
    result={'neutral_at_pKa':.5,'S_at_pKa':2e-5,'neutral_at_5_5':1/(1+ratio),'S_at_5_5':1e-5*(1+ratio)}
    assert math.isclose(result['neutral_at_5_5'],1/11)
    return result

if __name__=="__main__":
    print(json.dumps(reference(),ensure_ascii=False,indent=2))
