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
OUT=workspace('M09-L02','instructor')

def reference():
    import numpy as np
    t=np.array([0,10,20,40.]);y=np.exp(-.03*t)
    k=-float(np.polyfit(t,np.log(y),1)[0])
    result={'k_min_inverse':k,'half_life_min':math.log(2)/k,'kind':'simulation'}
    assert math.isclose(k,.03,rel_tol=1e-10)
    return result

if __name__=="__main__":
    print(json.dumps(reference(),ensure_ascii=False,indent=2))
