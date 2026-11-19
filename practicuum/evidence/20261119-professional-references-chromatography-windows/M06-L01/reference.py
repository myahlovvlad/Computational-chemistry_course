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
OUT=workspace('M06-L01','instructor')

def reference():
    from rdkit import Chem
    from rdkit.Chem import AllChem
    m=Chem.AddHs(Chem.MolFromSmiles(compound('atorvastatin')['smiles']))
    p=AllChem.ETKDGv3();p.randomSeed=42;p.numThreads=1
    ids=list(AllChem.EmbedMultipleConfs(m,numConfs=6,params=p))
    values=AllChem.MMFFOptimizeMoleculeConfs(m,numThreads=1,maxIters=1000)
    result={'generated':len(ids),'converged':sum(s==0 for s,e in values),'energies_kcal_mol':[e for s,e in values],'statuses':[s for s,e in values]}
    assert len(ids)==6 and all(math.isfinite(e) for s,e in values)
    return result

if __name__=="__main__":
    print(json.dumps(reference(),ensure_ascii=False,indent=2))
