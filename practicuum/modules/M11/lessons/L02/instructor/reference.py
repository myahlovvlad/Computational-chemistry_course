from pathlib import Path
import json,numpy as np
from rdkit import Chem
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'programm/course.json').is_file())
D=ROOT/'practicuum/shared/data/target_docking'
audit=json.loads((D/'hmgcr_repair_audit.json').read_text())
displacement=audit['max_original_pocket_heavy_displacement_A'];nearest=min(r['nearest_ligand_A'] for r in audit['new_heavy_atoms'])
result={'max_original_pocket_displacement_A':displacement,'nearest_new_heavy_atom_A':nearest,'preparation_accepted':displacement<=.05 and nearest>6,'docking':'NOT_RUN'}
if __name__=='__main__':print(json.dumps(result,indent=2))
