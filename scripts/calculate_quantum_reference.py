"""Воспроизводимый учебный расчёт вертикальных переходов: не экспериментальный UV-спектр."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys

def calculate(record,out):
    import numpy as np
    from rdkit import Chem,rdBase
    from rdkit.Chem import AllChem
    import pyscf
    from pyscf import dft,gto,lib
    from scipy.constants import physical_constants

    out.mkdir(parents=True,exist_ok=False)
    mol=Chem.AddHs(Chem.MolFromSmiles(record['smiles']))
    params=AllChem.ETKDGv3();params.randomSeed=20261118
    if AllChem.EmbedMolecule(mol,params)!=0:raise RuntimeError('Не получена исходная геометрия')
    if not AllChem.MMFFHasAllMoleculeParams(mol):raise RuntimeError('Нет параметров MMFF для заданной формы')
    geometry_status=AllChem.MMFFOptimizeMolecule(mol,maxIters=1000)
    if geometry_status!=0:raise RuntimeError('Исходная MMFF-геометрия не сошлась')
    # Геометрия MMFF не объявляется стационарной точкой поверхности DFT.
    atoms=[]
    for atom in mol.GetAtoms():
        p=mol.GetConformer().GetAtomPosition(atom.GetIdx())
        atoms.append((atom.GetSymbol(),(float(p.x),float(p.y),float(p.z))))
    geometry=json.dumps(atoms)
    (out/'geometry.json').write_text(geometry,encoding='utf-8')
    lib.num_threads(2)
    system=gto.M(atom=atoms,basis='sto-3g',unit='Angstrom',charge=Chem.GetFormalCharge(mol),spin=0,
                 max_memory=3000,verbose=4,output=str(out/'pyscf.log'))
    meanfield=dft.RKS(system).density_fit()
    meanfield.xc='b3lyp';meanfield.grids.level=1;meanfield.conv_tol=1e-8;meanfield.max_cycle=100
    energy=meanfield.kernel()
    if not meanfield.converged:raise RuntimeError('SCF не сошёлся; результат не принимается')
    excited=meanfield.TDDFT();excited.nstates=6;excited.conv_tol=1e-6;excited.max_cycle=100
    transition_hartree,_=excited.kernel()
    if not all(excited.converged):raise RuntimeError('Не все состояния TDDFT сошлись')
    strength=excited.oscillator_strength(gauge='length')
    hartree_eV=physical_constants['Hartree energy in eV'][0]
    rows=[]
    for index,(transition,f) in enumerate(zip(transition_hartree,strength),1):
        eV=float(transition*hartree_eV)
        if not np.isfinite(eV) or eV<=0 or not np.isfinite(f):raise RuntimeError('Некорректный переход')
        rows.append({'state':index,'energy_eV':eV,'wavelength_nm':1239.8419843320026/eV,'oscillator_strength':float(f)})
    result={'status':'PASS','scope':'computed gas-phase vertical transitions; not measured absorbance',
     'compound':record['name'],'cid':record['cid'],'smiles':record['smiles'],'source_url':record['source_url'],
     'method':'B3LYP/STO-3G, density fitting, grids level 1, gas phase; TDDFT singlets, length gauge',
     'geometry_method':'ETKDGv3 seed 20261118 + MMFF; not DFT optimized',
     'geometry_sha256':hashlib.sha256(geometry.encode()).hexdigest(),'charge':system.charge,'spin':system.spin,
     'scf_converged':bool(meanfield.converged),'energy_hartree':float(energy),'transitions':rows,
     'limitations':['minimal basis and coarse grid','no solvent','no vibrational/thermal broadening',
       'MMFF geometry, not DFT stationary point','no absolute measured extinction coefficient',
       'not a reproduction of the literature aqueous-xanthine protocol'],
     'versions':{'python':sys.version,'pyscf':pyscf.__version__,'rdkit':rdBase.rdkitVersion,'numpy':np.__version__},
     'utc':datetime.now(timezone.utc).isoformat()}
    (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compounds',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--names',nargs='+',default=['caffeine','istradefylline','atorvastatin'])
    args=parser.parse_args();records=json.loads(args.compounds.read_text(encoding='utf-8'));summary=[]
    args.out.mkdir(parents=True,exist_ok=True)
    for name in args.names:
        record=next(r for r in records if r['name']==name)
        print(name,'START',flush=True)
        result=calculate(record,args.out/name);summary.append({'name':name,'status':result['status']})
        print(name,'PASS',result['energy_hartree'],flush=True)
        (args.out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')

if __name__=='__main__':main()
