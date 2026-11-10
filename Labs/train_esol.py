"""Small ESOL audit: fixed baseline/model, identity and scaffold holdouts.

Run with --csv PATH --out PATH. Use --download only to fetch the public example.
This is a teaching benchmark, not a validated solubility service.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

import numpy as np
import sklearn
from rdkit import Chem, DataStructs, rdBase
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline

from chemistry import descriptors, parse

URL = "https://raw.githubusercontent.com/deepchem/deepchem/master/datasets/delaney-processed.csv"
TARGET = "measured log solubility in mols per litre"
FEATURES = ["MolWt", "MolLogP", "TPSA", "HBD", "HBA"]


def load(path: Path) -> list[dict]:
    records = []
    with path.open(encoding="utf-8", newline="") as handle:
        for index, row in enumerate(csv.DictReader(handle)):
            mol = parse(row["smiles"])
            identity = Chem.MolToSmiles(mol, canonical=True, isomericSmiles=True)
            scaffold = MurckoScaffold.MurckoScaffoldSmiles(mol=mol)
            # WHY: all acyclic structures share one explicit conservative group.
            scaffold = scaffold or "ACYCLIC_ALL"
            records.append({"row": index, "name": row["Compound ID"],
                            "smiles": identity, "identity": identity,
                            "scaffold": scaffold, "y": float(row[TARGET]),
                            "x": [descriptors(identity)[key] for key in FEATURES]})
    if not records or not np.isfinite([r["y"] for r in records]).all():
        raise ValueError("Missing or nonfinite target")
    # Identity repeats stay in a single group; no silent averaging of measurements.
    return records


def run(path: Path, out: Path) -> dict:
    records = load(path)
    x = np.array([r["x"] for r in records], dtype=float)
    y = np.array([r["y"] for r in records], dtype=float)
    fpgen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048, includeChirality=True)
    fps = [fpgen.GetFingerprint(parse(r["smiles"])) for r in records]
    summary = {
        "input_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "source_url": URL, "run_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(), "rdkit": rdBase.rdkitVersion,
        "sklearn": sklearn.__version__, "rows": len(records),
        "unique_identity": len({r["identity"] for r in records}),
        "features": FEATURES, "target": TARGET,
        "policy": "sanitized input graph; no salt neutralization or tautomer merging",
        "seed": 42, "test_fraction_groups": 0.2,
        "model": {"n_estimators": 200, "min_samples_leaf": 2},
        "warning": "Single fixed holdout per scenario; no uncertainty calibration or tuning",
        "splits": {},
    }
    out.mkdir(parents=True, exist_ok=True)
    for kind in ("identity", "scaffold"):
        groups = [r[kind] for r in records]
        splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
        train, test = next(splitter.split(x, y, groups))
        if set(groups[i] for i in train) & set(groups[i] for i in test):
            raise RuntimeError("Group leakage")
        if {records[i]["identity"] for i in train} & {records[i]["identity"] for i in test}:
            raise RuntimeError("Identity leakage")
        models = {
            "mean_baseline": make_pipeline(SimpleImputer(strategy="median"), DummyRegressor()),
            "random_forest": make_pipeline(SimpleImputer(strategy="median"), RandomForestRegressor(
                n_estimators=200, min_samples_leaf=2, random_state=42, n_jobs=1)),
        }
        metrics, predictions = {}, {}
        for name, model in models.items():
            model.fit(x[train], y[train])
            predicted = model.predict(x[test])
            predictions[name] = predicted
            metrics[name] = {
                "MAE_logS": float(mean_absolute_error(y[test], predicted)),
                "RMSE_logS": float(np.sqrt(np.mean((y[test] - predicted) ** 2))),
                "R2": float(r2_score(y[test], predicted)),
            }
        nearest = [max(DataStructs.BulkTanimotoSimilarity(fps[i], [fps[j] for j in train])) for i in test]
        with (out / f"{kind}_predictions.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["row", "smiles", "measured_logS", "baseline", "predicted", "nearest_train_T"])
            for k, i in enumerate(test):
                writer.writerow([int(i), records[i]["smiles"], y[i],
                                 predictions["mean_baseline"][k], predictions["random_forest"][k], nearest[k]])
        membership = ["train" if i in set(train) else "test" for i in range(len(records))]
        (out / f"{kind}_split.json").write_text(json.dumps(membership), encoding="utf-8")
        summary["splits"][kind] = {"train_rows": len(train), "test_rows": len(test), "metrics": metrics}
    (out / "report.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    if args.download:
        if args.csv.exists():
            raise FileExistsError("Refusing to replace existing data; omit --download to reuse")
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with urlopen(URL, timeout=60) as response:
            args.csv.write_bytes(response.read())
    print(json.dumps(run(args.csv, args.out), indent=2))


if __name__ == "__main__":
    main()
