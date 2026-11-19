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
OUT=workspace('M11-L02','instructor')

def reference():
    from docking import mapped_rmsd,first_pose
    folder=DATA/'docking'
    rmsd=mapped_rmsd(folder/'1iep_ligand.pdbqt',folder/'1iep_ligand_vina_out.pdbqt')
    atoms,score=first_pose(folder/'1iep_ligand_vina_out.pdbqt')
    result={'control_RMSD_A':rmsd,'heavy_atoms':len(atoms),'shift_RMSD_A':1.0,'HMGCR_execution':'NOT_RUN'}
    assert rmsd>=0 and len(atoms)>0
    return result

if __name__=="__main__":
    print(json.dumps(reference(),ensure_ascii=False,indent=2))
