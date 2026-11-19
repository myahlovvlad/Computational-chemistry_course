"""Target-specific, auditable redocking preparation with protonation and cofactors.

Crystal heavy-atom coordinates are retained for reference. Search ligands get
independently embedded/minimized conformations. Missing pocket atoms fail closed.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import traceback

import gemmi
import numpy as np
import requests
from rdkit import Chem
from rdkit.Chem import AllChem
from meeko import MoleculePreparation,PDBQTWriterLegacy

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'practicuum/shared'))
from receptor_inputs import normalize_pqr


def dump(path,value):
    with path.open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2)


def run(command,folder,label):
    process=subprocess.run(command,cwd=folder,capture_output=True,text=True,timeout=1800)
    (folder/(label+'-stdout.txt')).write_text(process.stdout,encoding='utf-8')
    (folder/(label+'-stderr.txt')).write_text(process.stderr,encoding='utf-8')
    dump(folder/(label+'-command.json'),{'argv':[str(v) for v in command],'returncode':process.returncode})
    if process.returncode:raise RuntimeError(label+' failed; no bad-residue bypass applied')


def subset_pdb(chain,residues):
    structure=gemmi.Structure();model=gemmi.Model('1');copy=gemmi.Chain(chain.name)
    for res in residues:copy.add_residue(res.clone())
    model.add_chain(copy);structure.add_model(model)
    return structure.make_pdb_string()


def crystal_molecule(chain,residue,template):
    raw=Chem.MolFromPDBBlock(subset_pdb(chain,[residue]),removeHs=False,sanitize=False,proximityBonding=True)
    if raw is None:raise ValueError('Crystal ligand could not be parsed')
    mol=AllChem.AssignBondOrdersFromTemplate(Chem.RemoveHs(template),Chem.RemoveHs(raw,sanitize=False))
    Chem.SanitizeMol(mol);Chem.AssignStereochemistryFrom3D(mol,replaceExistingTags=True)
    actual=Chem.MolToSmiles(mol,isomericSmiles=True);expected=Chem.MolToSmiles(Chem.RemoveHs(template),isomericSmiles=True)
    if actual!=expected:raise ValueError('Crystal ligand graph/stereochemistry differs from selected template: '+actual+' versus '+expected)
    return Chem.AddHs(mol,addCoords=True)


def pdbqt(molecule):
    setups=MoleculePreparation().prepare(molecule)
    if len(setups)!=1:raise ValueError('Unexpected ligand preparation multiplicity')
    text,ok,error=PDBQTWriterLegacy.write_string(setups[0])
    if not ok:raise ValueError('Meeko ligand preparation failed: '+error)
    return text


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target',choices=['8RW0','1HWK'],required=True)
    parser.add_argument('--structures',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--ligand-form',choices=['source','anion'],default='source')
    args=parser.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    try:
        folder=args.structures.resolve()/args.target;coordinate=folder/'structure.cif'
        entry=json.loads((folder/'entry.json').read_text(encoding='utf-8'))
        if entry['rcsb_id']!=args.target:raise ValueError('Wrong target snapshot')
        pdb=args.target;code='JQ9' if pdb=='8RW0' else '117';name='istradefylline' if pdb=='8RW0' else 'atorvastatin'
        records=json.loads((ROOT/'practicuum/shared/data/compounds.json').read_text(encoding='utf-8'))
        record=next(r for r in records if r['name']==name);template=Chem.MolFromSmiles(record['smiles'])
        if args.ligand_form=='anion':
            if pdb!='1HWK':raise ValueError('Anion protocol only for atorvastatin')
            salt=Chem.MolFromSmiles(next(r for r in records if r['name']=='atorvastatin_calcium')['smiles'])
            template=next(m for m in Chem.GetMolFrags(salt,asMols=True) if Chem.GetFormalCharge(m)==-1)
        structure=gemmi.read_structure(str(coordinate));structure.remove_alternative_conformations()
        chain=structure[0]['A'];ligand_res=next(r for r in chain if r.name==code)
        ligand=crystal_molecule(chain,ligand_res,template)
        with Chem.SDWriter(str(out/'crystal_reference.sdf')) as writer:writer.write(ligand)
        (out/'crystal_reference.pdbqt').write_text(pdbqt(ligand),encoding='utf-8')
        positions=np.asarray(ligand.GetConformer().GetPositions())[[a.GetIdx() for a in ligand.GetAtoms() if a.GetAtomicNum()>1]]
        center=(positions.min(axis=0)+positions.max(axis=0))/2
        size=np.maximum(positions.max(axis=0)-positions.min(axis=0)+16,22)
        # Keep every protein chain: HMGCR's active site involves a subunit interface.
        receptor=gemmi.Structure();model=gemmi.Model('1');protein=[];gaps=[]
        for source_chain in structure[0]:
            copy=gemmi.Chain(source_chain.name);residues=[r for r in source_chain if r.entity_type==gemmi.EntityType.Polymer]
            for i,res in enumerate(residues):
                copy.add_residue(res.clone());protein.append((source_chain.name,str(res.seqid),res.name))
                if i and res.seqid.num-residues[i-1].seqid.num>1:
                    flank=np.array([[a.pos.x,a.pos.y,a.pos.z] for r in [residues[i-1],res] for a in r if a.element.name!='H'])
                    nearest=float(np.sqrt(np.sum((flank[:,None,:]-positions[None,:,:])**2,axis=2)).min())
                    gaps.append({'chain':source_chain.name,'before':str(residues[i-1].seqid),'after':str(res.seqid),'nearest_flank_to_ligand_A':nearest})
            if len(copy):model.add_chain(copy)
        receptor.add_model(model);receptor.write_pdb(str(out/'protein_crystal.pdb'))
        dump(out/'pocket_gap_audit.json',{'gaps':gaps,'criterion':'unresolved backbone gap flank within 6 A requires modelling/review'})
        if any(g['nearest_flank_to_ligand_A']<6 for g in gaps):raise RuntimeError('Unresolved backbone gap near binding site: professional preparation blocked')
        pH=5.0 if pdb=='8RW0' else 7.5
        binary=Path(sys.executable).parent
        run([str(binary/'pdb2pqr30'),'--ff=AMBER','--ffout=AMBER','--keep-chain','--drop-water','--whitespace',
             '--titration-state-method=propka','--with-ph='+str(pH),'--pdb-output='+str(out/'protein_protonated.pdb'),
             str(out/'protein_crystal.pdb'),str(out/'protein_protonated.pqr')],out,'pdb2pqr')
        # PDB2PQR retains fixed-width chain/residue fields even with --whitespace;
        # Meeko's token parser cannot read A1001 as chain A plus residue 1001.
        # Re-serialize fields without changing coordinates, radii or charges.
        # Audit modeled sidechains and preserve the experimental pocket frame.
        protonated=gemmi.read_structure(str(out/'protein_protonated.pdb'));reference_atoms={}
        for c in receptor[0]:
            for r in c:
                for a in r:
                    if a.element.name!='H':reference_atoms[(c.name,str(r.seqid),a.name)]=a.pos
        repairs=[];pocket_movement=[]
        for c in protonated[0]:
            for r in c:
                for a in r:
                    if a.element.name=='H':continue
                    key=(c.name,str(r.seqid),a.name);nearest=float(np.linalg.norm(positions-np.array([a.pos.x,a.pos.y,a.pos.z]),axis=1).min())
                    if key not in reference_atoms:repairs.append({'atom':key,'nearest_ligand_A':nearest})
                    elif nearest<6:pocket_movement.append(a.pos.dist(reference_atoms[key]))
        dump(out/'heavy_atom_repair_audit.json',{'new_heavy_atoms':repairs,'max_original_pocket_heavy_displacement_A':max(pocket_movement,default=0),
            'criterion':'original pocket atoms within 6 A may not move >0.05 A without separate review'})
        if max(pocket_movement,default=0)>.05:raise RuntimeError('Receptor repair moved original binding-pocket atoms; review required')
        if any(r['nearest_ligand_A']<6 for r in repairs):raise RuntimeError('New heavy-atom reconstruction in binding pocket requires review')
        normalized=normalize_pqr((out/'protein_protonated.pqr').read_text(encoding='utf-8'),canonical_resnames=True)
        (out/'protein_protonated_tokens.pqr').write_text(normalized,encoding='utf-8')
        run([str(binary/'mk_prepare_receptor.py'),'--read_pqr',str(out/'protein_protonated_tokens.pqr'),
             '--charge_model','read','-o',str(out/'receptor'),'-p','-j','--default_altloc','A'],out,'meeko-receptor')
        receptor_file=out/'receptor.pdbqt'
        if not receptor_file.is_file():raise FileNotFoundError('Prepared receptor not produced')
        cofactors=[]
        if pdb=='1HWK':
            # Retain experimental ADP geometry, using an explicit dominant phosphate
            # ionization assumption at pH 7.5; this is a protocol, not a pKa measurement.
            url='https://files.rcsb.org/ligands/download/ADP_ideal.sdf'
            response=requests.get(url,timeout=(20,90));response.raise_for_status();(out/'ADP_CCD_ideal.sdf').write_bytes(response.content)
            source=Chem.MolFromMolBlock(response.text,removeHs=False)
            if source is None:raise ValueError('ADP template unreadable')
            source=Chem.RemoveHs(source)
            phosphate_oh=source.GetSubstructMatches(Chem.MolFromSmarts('[OX2H1]-[P]'))
            for oxygen,_ in phosphate_oh:
                atom=source.GetAtomWithIdx(oxygen);atom.SetFormalCharge(-1);atom.SetNumExplicitHs(0);atom.SetNoImplicit(True)
            source=Chem.RemoveHs(source);Chem.SanitizeMol(source)
            if Chem.GetFormalCharge(source)!=-3:raise ValueError('ADP -3 template assumption not achieved')
            fixed=[]
            for source_chain in structure[0]:
                for res in source_chain:
                    if res.name!='ADP':continue
                    molecule=crystal_molecule(source_chain,res,source);text=pdbqt(molecule)
                    fixed += [line for line in text.splitlines() if line.startswith(('ATOM  ','HETATM'))]
                    cofactors.append({'chain':source_chain.name,'residue':str(res.seqid),'form':'ADP3-','atoms':molecule.GetNumHeavyAtoms()})
            combined=receptor_file.read_text(encoding='utf-8').rstrip()+'\n'+'\n'.join(fixed)+'\n'
            (out/'receptor_with_ADP.pdbqt').write_text(combined,encoding='utf-8')
            cofactor_source={'url':url,'sha256':hashlib.sha256(response.content).hexdigest(),'licence':'RCSB CCD CC0'}
        else:cofactor_source=None
        starts=[]
        for seed in [13,37,73]:
            m=Chem.Mol(ligand);m.RemoveAllConformers();params=AllChem.ETKDGv3();params.randomSeed=seed
            if AllChem.EmbedMolecule(m,params)!=0:raise RuntimeError('Independent ligand embedding failed')
            if not AllChem.MMFFHasAllMoleculeParams(m):raise RuntimeError('Ligand MMFF parameters unavailable')
            if AllChem.MMFFOptimizeMolecule(m,mmffVariant='MMFF94s',maxIters=3000)!=0:raise RuntimeError('Ligand geometry did not converge')
            path=out/f'ligand-start-{seed}.pdbqt';path.write_text(pdbqt(m),encoding='utf-8');starts.append({'seed':seed,'file':path.name})
        manifest={'status':'PASS','target':pdb,'ligand_code':code,'ligand_name':name,'ligand_form':args.ligand_form,
          'template_smiles':Chem.MolToSmiles(Chem.RemoveHs(template),isomericSmiles=True),
          'coordinate_sha256':hashlib.sha256(coordinate.read_bytes()).hexdigest(),
          'created_utc':datetime.now(timezone.utc).isoformat(),'source_structure':entry['struct']['title'],
          'pH':pH,'pH_basis':'reported crystallization pH; soaking conditions and physiological transfer require separate review',
          'protein_chains':[c.name for c in receptor[0]],'protein_residues':len(protein),'backbone_gap_audit':gaps,
          'heavy_atom_repairs':repairs,'histidine_alias':'HID/HIE/HIP renamed HIS for terminal template matching; protons and charges unchanged',
          'receptor_variants':['receptor.pdbqt']+(['receptor_with_ADP.pdbqt'] if cofactors else []),
          'cofactors':cofactors,'cofactor_source':cofactor_source,'independent_ligand_starts':starts,
          'box_center_A':center.tolist(),'box_size_A':size.tolist(),'padding_A_each_side':8,
          'reference':'crystal_reference.sdf','reference_frame':'receptor, no independent ligand superposition',
          'versions':{n:importlib.metadata.version(n) for n in ['meeko','vina','gemmi','rdkit','pdb2pqr']},
          'limitations':['Rigid receptor approximation; no affinity/clinical validation',
                         'All crystal waters omitted: hydration sensitivity remains required',
                         'A2A lipids and sodium omitted explicitly; allosteric/membrane effects not represented',
                         'ADP phosphate state is a declared pH assumption, not measured proton positions',
                         'Protein-only HMGCR is a cofactor-sensitivity control, not the primary accepted receptor',
                         'Alternative protein protonation/tautomer assignments require sensitivity analysis'],
          'redocking_execution':'NOT_RUN','scientific_review':'NOT_RUN'}
        dump(out/'manifest.json',manifest);print(pdb,'preparation PASS',flush=True)
    except Exception as error:
        dump(out/'failure.json',{'status':'BLOCKED','error':str(error),'traceback':traceback.format_exc(),'no_bad_residue_bypass':True})
        raise


if __name__=='__main__':main()
