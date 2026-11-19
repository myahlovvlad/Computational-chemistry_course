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
OUT=workspace('M11-L01','instructor')

def reference():
    records=json.loads((DATA/'atorvastatin_activities.json').read_text(encoding='utf-8'))['records']
    selected=[]
    for r in records:
        if r['target_chembl_id']=='CHEMBL402' and r['target_organism']=='Homo sapiens' and r['standard_type']=='IC50' and r['standard_relation']=='=' and r['standard_units']=='nM':
            v=float(r['standard_value'])
            if v>0:selected.append({'pIC50':-math.log10(v*1e-9),'assay':r['assay_chembl_id'],'document':r['document_chembl_id']})
    result={'records':selected,'n':len(selected),'pIC50_6nM':-math.log10(6e-9)}
    assert selected and math.isclose(result['pIC50_6nM'],8.2218487496,abs_tol=1e-9)
    return result

if __name__=="__main__":
    print(json.dumps(reference(),ensure_ascii=False,indent=2))
