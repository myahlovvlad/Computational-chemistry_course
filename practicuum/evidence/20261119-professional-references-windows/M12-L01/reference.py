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
OUT=workspace('M12-L01','instructor')

def reference():
    import numpy as np
    from rdkit import Chem
    from rdkit.Chem import Descriptors,Lipinski
    from sklearn.model_selection import GroupShuffleSplit
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import Ridge
    rows=esol();m=[Chem.MolFromSmiles(r['smiles']) for r in rows]
    X=np.array([[Descriptors.MolWt(v),Descriptors.MolLogP(v),Descriptors.TPSA(v),Lipinski.NumHDonors(v),Lipinski.NumHAcceptors(v)] for v in m]);y=np.array([r['measured'] for r in rows])
    g=np.array([Chem.MolToSmiles(v,isomericSmiles=True) for v in m]);tr,te=next(GroupShuffleSplit(n_splits=1,test_size=.2,random_state=7).split(X,y,g))
    p=make_pipeline(StandardScaler(),Ridge(alpha=1)).fit(X[tr],y[tr]).predict(X[te])
    result={'overlap':len(set(g[tr])&set(g[te])),'RMSE':float(np.sqrt(np.mean((p-y[te])**2))),'baseline_RMSE':float(np.sqrt(np.mean((y[tr].mean()-y[te])**2))),'rows':len(y)}
    assert result['overlap']==0 and math.isfinite(result['RMSE'])
    return result

if __name__=="__main__":
    print(json.dumps(reference(),ensure_ascii=False,indent=2))
