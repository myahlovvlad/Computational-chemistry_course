"""Обработка локальной таблицы: сохраняем каждую строку, статус и причину решения."""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import platform
from rdkit import rdBase
from chemistry import screen


def process_csv(data: bytes, max_rows: int | None = None, canonical_tautomer: bool = False) -> tuple[list[dict],dict]:
    text=data.decode("utf-8-sig")
    reader=csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or not {"id","smiles"}<=set(reader.fieldnames):
        raise ValueError("CSV requires id and smiles columns")
    rows=list(reader)
    if max_rows is not None and len(rows)>max_rows:
        raise ValueError(f"CSV exceeds the configured limit of {max_rows} rows")
    ids=[row["id"] for row in rows]
    if any(not value.strip() for value in ids) or len(ids)!=len(set(ids)):
        raise ValueError("IDs must be nonempty and unique")
    result=[{"id":row["id"],**screen(row.get("smiles"),canonical_tautomer=canonical_tautomer)} for row in rows]
    passport={"input_sha256":hashlib.sha256(data).hexdigest(),"python":platform.python_version(),
              "rdkit":rdBase.rdkitVersion,"rows":len(rows),
              "policy":"teaching-parent-v1;neutralize;tautomer="+str(canonical_tautomer)}
    return result,passport


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("input",type=Path)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    rows,passport=process_csv(args.input.read_bytes())
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"report.json").write_text(json.dumps({"passport":passport,"rows":rows},indent=2),encoding="utf-8")
    keys=list(dict.fromkeys(key for row in rows for key in row))
    with (args.out/"report.csv").open("w",encoding="utf-8-sig",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(passport))


if __name__=="__main__":
    main()
