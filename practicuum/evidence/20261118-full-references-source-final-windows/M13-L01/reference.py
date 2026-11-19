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
OUT=workspace('M13-L01','instructor')

def reference():
    source=json.loads((DATA/'atorvastatin_process_source.json').read_text(encoding='utf-8'))
    result={'stage1_yield':source['stage1_isolated_molar_yield'],
            'overall_yield_lower_bound':source['overall_two_stage_molar_yield_lower_bound'],
            'stage2_implied_lower_bound':source['overall_two_stage_molar_yield_lower_bound']/source['stage1_isolated_molar_yield'],
            'route':source['route'],'relation':'>','kind':'calculated'}
    assert result['stage2_implied_lower_bound']==.8125
    return result

if __name__=="__main__":
    print(json.dumps(reference(),ensure_ascii=False,indent=2))
