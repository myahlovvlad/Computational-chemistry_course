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
OUT=workspace('M13-L02','instructor')

def reference():
    source=json.loads((DATA/'atorvastatin_process_source.json').read_text(encoding='utf-8'))
    mass=source['advanced_input_mass_kg']
    result={'isopropanol_L_per_kg_input':source['stage1_isopropanol_volume_L']/mass,
            'water_L_per_kg_input':source['stage1_water_volume_L']/mass,
            'PMI':'NOT_CALCULABLE: missing full mass balance','kind':'calculated'}
    assert result['isopropanol_L_per_kg_input']==10
    return result

if __name__=="__main__":
    print(json.dumps(reference(),ensure_ascii=False,indent=2))
