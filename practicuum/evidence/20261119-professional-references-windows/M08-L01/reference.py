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
OUT=workspace('M08-L01','instructor')

def reference():
    import numpy as np
    q=json.loads((DATA/'quantum/atorvastatin/result.json').read_text(encoding='utf-8'));t=q['transitions']
    x=np.linspace(.1,max(r['energy_eV'] for r in t)+2,3000);sigma=.1
    y=sum(r['oscillator_strength']*np.exp(-.5*((x-r['energy_eV'])/sigma)**2)/(sigma*np.sqrt(2*np.pi)) for r in t)
    area=float(np.trapezoid(y,x));total=sum(r['oscillator_strength'] for r in t)
    result={'area':area,'sum_f':total,'relative_error':abs(area-total)/total,'kind':'simulation'}
    assert result['relative_error']<1e-4
    return result

if __name__=="__main__":
    print(json.dumps(reference(),ensure_ascii=False,indent=2))
