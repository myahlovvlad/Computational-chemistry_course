"""Учебные операции со структурами; вычислительная пригодность не означает биоактивность."""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import math
import platform
from dataclasses import asdict, dataclass
from pathlib import Path

from rdkit import Chem, rdBase
from rdkit.Chem import AllChem, Descriptors, Lipinski, rdFingerprintGenerator
from rdkit.Chem.FilterCatalog import FilterCatalog, FilterCatalogParams
from rdkit.Chem.MolStandardize import rdMolStandardize

LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class Structure:
    raw_smiles: str
    parent_smiles: str
    policy: str


def parse(smiles: str) -> Chem.Mol:
    if not isinstance(smiles, str) or not smiles.strip():
        raise ValueError("SMILES must be a nonempty string")
    mol = Chem.MolFromSmiles(smiles.strip())
    if mol is None or mol.GetNumAtoms() == 0:
        raise ValueError("Invalid SMILES")
    return mol


def standardize(smiles: str, canonical_tautomer: bool = False) -> Structure:
    """Teaching policy for simple organic compounds, not arbitrary mixtures."""
    mol = rdMolStandardize.Cleanup(parse(smiles))
    # Дескрипторы родительской формы не включают противоион; исходная запись сохраняется отдельно.
    parent = rdMolStandardize.FragmentParent(mol)
    # Правило нейтрализации не рассчитывает распределение форм при заданном pH.
    parent = rdMolStandardize.Uncharger().uncharge(parent)
    if canonical_tautomer:
        # Каноническая строка SMILES сама по себе не выбирает общий таутомер.
        parent = rdMolStandardize.TautomerEnumerator().Canonicalize(parent)
    Chem.SanitizeMol(parent)
    policy = "teaching-parent-v1;neutralize;tautomer=" + str(canonical_tautomer)
    result = Chem.MolToSmiles(parent, canonical=True, isomericSmiles=True)
    LOG.info("standardized with %s", policy)
    return Structure(smiles, result, policy)


def descriptors(smiles: str) -> dict[str, float | int]:
    mol = parse(smiles)
    result = {
        "MolWt": Descriptors.MolWt(mol),
        "MolLogP": Descriptors.MolLogP(mol),
        "TPSA": Descriptors.TPSA(mol),
        "HBD": Lipinski.NumHDonors(mol),
        "HBA": Lipinski.NumHAcceptors(mol),
    }
    result["ro5_violations"] = sum((
        result["MolWt"] > 500,
        result["MolLogP"] > 5,
        result["HBD"] > 5,
        result["HBA"] > 10,
    ))
    return result


def pains_alerts(smiles: str) -> list[str]:
    params = FilterCatalogParams()
    params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS)
    catalog = FilterCatalog(params)
    return sorted({match.GetDescription() for match in catalog.GetMatches(parse(smiles))})


def screen(smiles: str, canonical_tautomer: bool = False) -> dict:
    # Только ошибка входной структуры получает invalid; ошибки программы не скрываем.
    try:
        parse(smiles)
    except ValueError as error:
        return {"raw_smiles": smiles, "status": "invalid", "reason": str(error)}
    record = standardize(smiles,canonical_tautomer=canonical_tautomer)
    props = descriptors(record.parent_smiles)
    alerts = pains_alerts(record.parent_smiles)
    reasons = ["PAINS:" + alert for alert in alerts]
    if props["ro5_violations"]:
        reasons.append("Ro5 warning: contextual review required")
    return {
        **asdict(record), **props, "alerts": alerts,
        "status": "review" if reasons else "eligible",
        "reason": "; ".join(reasons) or "No listed alert; activity remains unknown",
    }


def similarity(first: str, second: str) -> float:
    from rdkit import DataStructs

    generator = rdFingerprintGenerator.GetMorganGenerator(
        radius=2, fpSize=2048, includeChirality=True
    )
    a = generator.GetFingerprint(parse(first))
    b = generator.GetFingerprint(parse(second))
    return float(DataStructs.TanimotoSimilarity(a, b))


def optimize_conformer(smiles: str, seed: int = 42) -> dict:
    mol = Chem.AddHs(parse(smiles))
    params = AllChem.ETKDGv3()
    params.randomSeed = seed
    if AllChem.EmbedMolecule(mol, params) != 0:
        raise RuntimeError("Embedding failed")
    if not AllChem.MMFFHasAllMoleculeParams(mol):
        raise ValueError("MMFF parameters unavailable")
    # Одна минимизация не доказывает нахождение глобального минимума.
    status = AllChem.MMFFOptimizeMolecule(mol, maxIters=500)
    field = AllChem.MMFFGetMoleculeForceField(
        mol, AllChem.MMFFGetMoleculeProperties(mol)
    )
    energy = field.CalcEnergy()
    if not math.isfinite(energy):
        raise RuntimeError("Nonfinite energy")
    return {"converged": status == 0, "status_code": status,
            "energy_kcal_mol": energy, "seed": seed,
            "n_conformers": mol.GetNumConformers()}


def p_activity(value: float, unit: str) -> float:
    scales = {"M": 1.0, "mM": 1e-3, "uM": 1e-6, "nM": 1e-9}
    if unit not in scales or not math.isfinite(value) or value <= 0:
        raise ValueError("A positive finite concentration and a known unit are required")
    return -math.log10(value * scales[unit])


def curate_activity(row: dict[str, str]) -> dict:
    """Conservative rules for the artificial A1 / T1 / IC50 exercise."""
    required = {"target_id": "T1", "assay_id": "A1", "endpoint": "IC50", "relation": "="}
    for key, expected in required.items():
        if row.get(key) != expected:
            return {**row, "status": "excluded", "reason": key}
    try:
        p_value = p_activity(float(row["value"]), row["unit"])
    except (ValueError, KeyError):
        return {**row, "status": "excluded", "reason": "value_or_unit"}
    return {**row, "status": "included", "pIC50": p_value, "reason": "teaching rules satisfied"}


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")
    source = Path(__file__).with_name("data")/"molecules.csv"
    with source.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    output = [{"id": row["id"], **screen(row["smiles"])} for row in rows]
    passport = {
        "python": platform.python_version(), "rdkit": rdBase.rdkitVersion,
        "input_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "rows": len(rows), "results": output,
    }
    print(json.dumps(passport, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
