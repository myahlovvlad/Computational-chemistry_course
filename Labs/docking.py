"""Official Vina tutorial execution and mapped heavy-atom pose comparison."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import numpy as np


def first_pose(path: Path) -> tuple[dict[int, np.ndarray], float | None]:
    atoms,score = {},None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("ENDMDL"):
            break
        if line.startswith("REMARK VINA RESULT:"):
            score=float(line.split()[3])
        if line.startswith(("ATOM  ","HETATM")):
            atom_type=line.split()[-1]
            if atom_type in {"H","HD","HS"}:
                continue
            serial=int(line[6:11])
            atoms[serial]=np.array([float(line[30:38]),float(line[38:46]),float(line[46:54])])
    if not atoms:
        raise ValueError("No heavy atoms")
    return atoms,score


def mapped_rmsd(reference: Path, pose: Path) -> float:
    a,_=first_pose(reference)
    b,_=first_pose(pose)
    if a.keys()!=b.keys():
        raise ValueError("Atom serials differ: explicit remapping is needed")
    # WHY: keep the receptor coordinate frame; do not align ligand independently.
    return float(np.sqrt(np.mean([np.sum((a[key]-b[key])**2) for key in sorted(a)])))


def run_docking(root: Path, output: Path) -> dict:
    data=root/"Labs/datasets/docking"
    output.mkdir(parents=True,exist_ok=True)
    reference=data/"1iep_ligand.pdbqt"
    official=data/"1iep_ligand_vina_out.pdbqt"
    result={"official_reference_rmsd_angstrom":mapped_rmsd(reference,official),
            "rmsd_definition":"mapped heavy atom serials, receptor frame, no symmetry optimization",
            "reference_score":first_pose(official)[1]}
    bundled=root/"tools/bin/vina_1.2.7_win.exe"
    binary=str(bundled) if bundled.exists() else shutil.which("vina")
    if binary is None:
        result["mode"]="official-reference-analysis; Vina executable not installed"
    else:
        target=output/"redocked.pdbqt"
        command=[binary,"--receptor",str(data/"1iep_receptor.pdbqt"),"--ligand",str(reference),
                 "--config",str(data/"1iep_receptor.box.txt"),"--seed","42","--cpu","1",
                 "--exhaustiveness","8","--num_modes","9","--out",str(target)]
        start=time.perf_counter()
        process=subprocess.run(command,capture_output=True,text=True,timeout=600,check=True)
        (output/"vina.log").write_text(process.stdout+process.stderr,encoding="utf-8")
        result.update({"mode":"executed-vina","wall_seconds":time.perf_counter()-start,
                       "score":first_pose(target)[1],"rmsd_angstrom":mapped_rmsd(reference,target),
                       "command":command,"binary_sha256":hashlib.sha256(Path(binary).read_bytes()).hexdigest()})
    (output/"docking.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    return result
