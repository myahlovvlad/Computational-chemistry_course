"""Compare independently executed Windows/Linux GFN2 searches by matched basins."""
import argparse,hashlib,json,shutil,sys
from pathlib import Path
import numpy as np
from rdkit import Chem
from scipy.optimize import linear_sum_assignment
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'practicuum/shared'))
from conformer_ensemble import aligned_conformer_rmsd


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):
    with Path(path).open('x',encoding='utf-8') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--windows',type=Path,required=True);parser.add_argument('--linux',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();out=args.out;out.mkdir(parents=True,exist_ok=False)
    protocol={'comparison':'one-to-one basin assignment minimizing heavy-atom aligned symmetry RMSD',
      'RMSD_tolerance_A':0.1,'paired_absolute_energy_tolerance_Eh':1e-5,
      'scope':'numerical/finite-search reproduction, not physical error or a proof of complete sampling',
      'notes':['Different compilers and libraries need not preserve starting IDs or fine energy order',
               'Thresholds recorded before matching; no empirical tolerance adjustment']}
    save(out/'protocol.json',protocol);shutil.copyfile(__file__,out/'auditor-source.py')
    manifests=[read(folder/'manifest.json') for folder in [args.windows,args.linux]]
    results=[read(folder/'result.json') for folder in [args.windows,args.linux]]
    fields=['name','canonical_state_smiles','charge','protocol_sha256','script_sha256','structure_helper_sha256','geometry_helper_sha256','compound_source_sha256']
    comparison={key:{'windows':manifests[0][key],'linux':manifests[1][key],
                     'equal':manifests[0][key]==manifests[1][key]} for key in fields}
    compatible=all(v['equal'] for v in comparison.values())
    molecules=[list(Chem.SDMolSupplier(str(folder/'optimized_conformers.sdf'),removeHs=False)) for folder in [args.windows,args.linux]]
    if not all(molecules) or any(m is None for values in molecules for m in values):raise ValueError('Invalid conformer bundle')
    M=np.array([[aligned_conformer_rmsd(a,b) for b in molecules[1]] for a in molecules[0]])
    left,right=linear_sum_assignment(M);rows=[]
    for i,j in zip(left,right):
        a,b=molecules[0][i],molecules[1][j]
        delta=float(b.GetProp('GFN2_ALPB_energy_hartree'))-float(a.GetProp('GFN2_ALPB_energy_hartree'))
        rows.append({'windows_source_id':int(a.GetProp('source_id')),'linux_source_id':int(b.GetProp('source_id')),
          'RMSD_A':float(M[i,j]),'linux_minus_windows_energy_Eh':delta,
          'within_comparison_tolerances':bool(M[i,j]<=.1 and abs(delta)<=1e-5)})
    accepted=compatible and all(r['status']=='PASS' for r in results) and len(molecules[0])==len(molecules[1]) and all(r['within_comparison_tolerances'] for r in rows)
    report={'status':'PASS' if accepted else 'REVIEW','scope':protocol['scope'],'source_comparison':comparison,
      'input_result_sha256':[sha(folder/'result.json') for folder in [args.windows,args.linux]],
      'conformer_counts':list(map(len,molecules)),'matched_basins':rows,'max_matched_RMSD_A':float(max(r['RMSD_A'] for r in rows)),
      'max_matched_energy_difference_Eh':float(max(abs(r['linux_minus_windows_energy_Eh']) for r in rows)),
      'minimum_energy_difference_Eh':results[1]['lowest_energy_hartree']-results[0]['lowest_energy_hartree'],
      'executable_sha256':[m['executable_sha256'] for m in manifests],
      'platforms':[m['platform'] for m in manifests],'source_id_identity_required':False,
      'fine_ordering_validation':'NOT_ESTABLISHED by this basin comparison','global_minimum':'NOT_PROVEN'}
    save(out/'result.json',report)
    print(report['status'],'max matched RMSD',report['max_matched_RMSD_A'],'energy delta',report['max_matched_energy_difference_Eh'])


if __name__=='__main__':main()
