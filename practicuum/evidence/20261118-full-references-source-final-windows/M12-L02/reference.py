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
OUT=workspace('M12-L02','instructor')

def reference():
    from rdkit import Chem,DataStructs
    from rdkit.Chem import rdFingerprintGenerator
    from sklearn.model_selection import GroupShuffleSplit
    import numpy as np
    rows=esol();m=[Chem.MolFromSmiles(r['smiles']) for r in rows];g=[Chem.MolToSmiles(v,isomericSmiles=True) for v in m]
    tr,te=next(GroupShuffleSplit(n_splits=1,test_size=.2,random_state=42).split(rows,groups=g))
    gen=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=2048,includeChirality=True);fps=[gen.GetFingerprint(m[i]) for i in tr]
    values={n:max(DataStructs.BulkTanimotoSimilarity(gen.GetFingerprint(Chem.MolFromSmiles(compound(n)['smiles'])),fps)) for n in ['atorvastatin','atorvastatin_lactone']}
    result={'similarities':values,'queries':len(values)}
    assert all(0<=v<=1 for v in values.values())
    return result

if __name__=="__main__":
    print(json.dumps(reference(),ensure_ascii=False,indent=2))
