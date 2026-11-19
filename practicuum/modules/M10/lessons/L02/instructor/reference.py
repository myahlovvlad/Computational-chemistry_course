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
OUT=workspace('M10-L02','instructor')

def reference():
    import numpy as np,csv
    with (DATA/'atorvastatin_hplc_table1.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    x=np.array([[(float(r['acetonitrile_percent'])-65)/5,(float(r['column_temperature_C'])-35)/5,(float(r['flow_mL_min'])-1)/.2] for r in rows])
    X=np.column_stack([np.ones(len(x)),x,x*x,x[:,0]*x[:,1],x[:,0]*x[:,2],x[:,1]*x[:,2]])
    y=np.array([float(r['retention_ATO_lactone_min']) for r in rows]);beta=np.linalg.lstsq(X,y,rcond=None)[0]
    result={'rows':len(rows),'columns':X.shape[1],'rank':int(np.linalg.matrix_rank(X)),'train_RMSE_min':float(np.sqrt(np.mean((X@beta-y)**2)))}
    assert X.shape==(20,10)
    return result

if __name__=="__main__":
    print(json.dumps(reference(),ensure_ascii=False,indent=2))
