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
OUT=workspace('M02-L01','instructor')

def reference():
    import hashlib
    raw=(DATA/'compounds.json').read_bytes()
    result={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'same_object':json.loads(raw)==json.loads(raw+b' ')}
    assert len(result['sha256'])==64 and result['bytes']>0
    return result

if __name__=="__main__":
    print(json.dumps(reference(),ensure_ascii=False,indent=2))
