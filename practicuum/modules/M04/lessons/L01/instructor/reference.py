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
OUT=workspace('M04-L01','instructor')

def reference():
    from rdkit import Chem
    from rdkit.Chem import Descriptors
    rows=[]
    for name in ['atorvastatin','atorvastatin_lactone']:
        m=Chem.MolFromSmiles(compound(name)['smiles'])
        rows.append({'name':name,'MW':Descriptors.MolWt(m),'TPSA':Descriptors.TPSA(m),'logP':Descriptors.MolLogP(m)})
    result={'forms':rows,'mass_difference':rows[0]['MW']-rows[1]['MW']}
    assert abs(result['mass_difference']-18.015)<1e-6
    return result

if __name__=="__main__":
    print(json.dumps(reference(),ensure_ascii=False,indent=2))
