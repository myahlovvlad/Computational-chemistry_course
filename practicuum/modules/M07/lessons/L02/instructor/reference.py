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
OUT=workspace('M07-L02','instructor')

def reference():
    import hashlib
    folder=DATA/'quantum'/'atorvastatin';q=json.loads((folder/'result.json').read_text(encoding='utf-8'))
    ok=hashlib.sha256((folder/'geometry.json').read_bytes()).hexdigest()==q['geometry_sha256']
    result={'geometry_hash_matches':ok,'charge':q['charge'],'spin':q['spin'],'transitions':len(q['transitions']),'scf_converged':q['scf_converged']}
    assert ok and q['scf_converged'] and len(q['transitions'])==6
    return result

if __name__=="__main__":
    print(json.dumps(reference(),ensure_ascii=False,indent=2))
