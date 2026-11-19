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
OUT=workspace('M05-L01','instructor')

def reference():
    from rdkit import Chem,DataStructs
    from rdkit.Chem import rdFingerprintGenerator
    m=[Chem.MolFromSmiles(compound(n)['smiles']) for n in ['atorvastatin','atorvastatin_lactone']]
    values={}
    for radius in [2,3]:
        g=rdFingerprintGenerator.GetMorganGenerator(radius=radius,fpSize=2048,includeChirality=True)
        values[str(radius)]=DataStructs.TanimotoSimilarity(*[g.GetFingerprint(v) for v in m])
    result={'similarities':values,'manual_T':.4}
    assert all(0<v<1 for v in values.values())
    return result

if __name__=="__main__":
    print(json.dumps(reference(),ensure_ascii=False,indent=2))
