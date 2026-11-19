"""Actual Vina redocking across independent starts/seeds, symmetry-aware receptor-frame RMSD."""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time
import sys

import numpy as np
from rdkit import Chem
from meeko import PDBQTMolecule,RDKitMolCreate
from vina import Vina

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'practicuum/shared'))
from pose_geometry import rmsd_without_alignment


def save(path,value):
    with path.open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepared',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    prepared=args.prepared.resolve();manifest=json.loads((prepared/'manifest.json').read_text(encoding='utf-8'))
    if manifest['status']!='PASS':raise ValueError('Validated preparation required')
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    reference=Chem.SDMolSupplier(str(prepared/manifest['reference']),removeHs=False)[0]
    if reference is None:raise ValueError('Crystal reference unavailable')
    # Negative control: a global ligand translation stays visible in receptor coordinates.
    shifted=Chem.Mol(reference);coords=shifted.GetConformer()
    for i in range(shifted.GetNumAtoms()):
        p=coords.GetAtomPosition(i);coords.SetAtomPosition(i,(p.x+1,p.y,p.z))
    if not np.isclose(rmsd_without_alignment(reference,shifted),1,atol=1e-10):raise AssertionError('RMSD frame-control regression')
    settings={'scoring':'vina','exhaustiveness':64,'n_poses':20,'energy_range_kcal_mol':8.,
              'cpu_per_run':2,'search_seeds':[101,202,303],'receptor_rigid':True,'grid_spacing_A':.375,
              'top1_RMSD_heuristic_A':2.0,'minimum_top1_recovery_fraction':8/9}
    save(out/'protocol.json',settings);(out/'preparation-manifest.json').write_bytes((prepared/'manifest.json').read_bytes())
    records=[]
    for receptor in manifest['receptor_variants']:
        for start in manifest['independent_ligand_starts']:
            for seed in settings['search_seeds']:
                label=Path(receptor).stem+f"-start-{start['seed']}-search-{seed}";folder=out/label;folder.mkdir()
                print(manifest['target'],label,'START',flush=True);clock=time.perf_counter()
                engine=Vina(sf_name='vina',cpu=settings['cpu_per_run'],seed=seed,verbosity=0)
                engine.set_receptor(str(prepared/receptor));engine.set_ligand_from_file(str(prepared/start['file']))
                engine.compute_vina_maps(center=manifest['box_center_A'],box_size=manifest['box_size_A'],spacing=settings['grid_spacing_A'])
                engine.dock(exhaustiveness=settings['exhaustiveness'],n_poses=settings['n_poses'])
                text=engine.poses(n_poses=settings['n_poses'],energy_range=settings['energy_range_kcal_mol'])
                (folder/'poses.pdbqt').write_text(text,encoding='utf-8')
                energies=engine.energies(n_poses=settings['n_poses'],energy_range=settings['energy_range_kcal_mol'])
                molecule_list=RDKitMolCreate.from_pdbqt_mol(PDBQTMolecule(text,skip_typing=True))
                if len(molecule_list)!=1 or molecule_list[0] is None:raise ValueError('Unambiguous pose reconstruction required')
                molecule=molecule_list[0]
                values=[rmsd_without_alignment(reference,molecule,conf_id=i) for i in range(molecule.GetNumConformers())]
                if len(values)!=len(energies):raise ValueError('Pose/score count mismatch')
                with Chem.SDWriter(str(folder/'poses.sdf')) as writer:
                    for i,value in enumerate(values):
                        molecule.SetProp('Vina_score_kcal_mol',str(float(energies[i][0])));molecule.SetProp('crystal_RMSD_A',str(value));writer.write(molecule,confId=i)
                record={'receptor_variant':receptor,'starting_geometry_seed':start['seed'],'search_seed':seed,
                    'seconds':time.perf_counter()-clock,'top1_RMSD_A':values[0],'best_sampled_RMSD_A':min(values),
                    'all_RMSD_A':values,'Vina_energy_columns':energies.tolist(),'score_units':'kcal/mol scoring function, not measured binding free energy',
                    'receptor_sha256':hashlib.sha256((prepared/receptor).read_bytes()).hexdigest(),
                    'ligand_input_sha256':hashlib.sha256((prepared/start['file']).read_bytes()).hexdigest(),
                    'poses_sha256':hashlib.sha256(text.encode()).hexdigest(),'status':'PASS'}
                save(folder/'result.json',record);records.append(record)
                print(manifest['target'],label,'top1 RMSD / A',values[0],'best sampled',min(values),flush=True)
    variants={}
    for receptor in manifest['receptor_variants']:
        group=[r for r in records if r['receptor_variant']==receptor]
        success=sum(r['top1_RMSD_A']<settings['top1_RMSD_heuristic_A'] for r in group)
        variants[receptor]={'runs':len(group),'top1_within_2A':success,'recovery_fraction':success/len(group),
           'geometric_recovery_criterion_met':success/len(group)>=settings['minimum_top1_recovery_fraction'],
           'mean_top1_RMSD_A':float(np.mean([r['top1_RMSD_A'] for r in group]))}
    result={'status':'PASS','scope':'actual target-specific redocking; scoring and sampling validation, not affinity or efficacy',
       'target':manifest['target'],'ligand_form':manifest['ligand_form'],'created_utc':datetime.now(timezone.utc).isoformat(),
       'runs':records,'receptor_variants':variants,'reference_frame':'fixed receptor, graph-symmetry minimized heavy-atom RMSD, no ligand alignment',
       'negative_translation_control_A':1.,'settings':settings,
       'versions':{n:importlib.metadata.version(n) for n in ['vina','meeko','rdkit','numpy']},
       'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'limitations':manifest['limitations'],'scientific_review':'NOT_RUN','prospective_binding_assay':'NOT_RUN'}
    save(out/'result.json',result)


if __name__=='__main__':main()
