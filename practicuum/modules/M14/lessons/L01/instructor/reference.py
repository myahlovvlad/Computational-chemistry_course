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
OUT=workspace('M14-L01','instructor')

def reference():
    import hashlib,networkx as nx
    digest=hashlib.sha256((DATA/'compounds.json').read_bytes()).hexdigest()
    nodes={'input','method','claim'};edges=[('input','method'),('method','claim')]
    g=nx.DiGraph();g.add_nodes_from(nodes);g.add_edges_from(edges)
    valid=nx.is_directed_acyclic_graph(g);g.add_edge('claim','input')
    result={'valid_DAG':valid,'cycle_detected':not nx.is_directed_acyclic_graph(g),'input_sha256':digest,'kind':'calculated'}
    assert result['valid_DAG'] and result['cycle_detected']
    return result

if __name__=="__main__":
    print(json.dumps(reference(),ensure_ascii=False,indent=2))
