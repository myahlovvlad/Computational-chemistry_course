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
OUT=workspace('M13-L02','instructor')

def reference():
    result={'A_yield':.8*.7,'B_yield':.95*.9,'A_cost':600/(.8*.7),'B_cost':750/(.95*.9),
            'A_lower_yield':.75*.65,'B_lower_yield':.9*.85,'kind':'simulation'}
    assert result['B_yield']>result['A_yield'] and result['B_cost']<result['A_cost']
    return result

if __name__=="__main__":
    print(json.dumps(reference(),ensure_ascii=False,indent=2))
