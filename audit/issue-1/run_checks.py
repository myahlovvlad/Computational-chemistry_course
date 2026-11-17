"""Stage-1 evidence collector. Never changes teaching sources or gold values.

Run with the host Python: python audit/issue-1/run_checks.py --phase core|labs
Every child command uses a new venv; outputs and exact arguments are retained.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "audit/issue-1"
EVIDENCE = Path(os.environ.get("PRACTICE_AUDIT_OUTPUT", str(BASE / "evidence"))).resolve()
ENV = ROOT / ".venv-audit"
PY = ENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def digest(path: Path) -> dict:
    return {"path": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}


def execute(identifier: str, argv: list[str], inputs: list[str] = (), timeout: int = 1200) -> dict:
    directory = EVIDENCE / identifier
    if (directory / "run.json").exists():
        raise FileExistsError(f"Evidence already exists: {identifier}; use a new evidence directory")
    directory.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env.update(PYTHONNOUSERSITE="1", PYTHONIOENCODING="utf-8", PIP_DISABLE_PIP_VERSION_CHECK="1")
    started = datetime.now(timezone.utc).isoformat()
    clock = time.perf_counter()
    with (directory / "stdout.txt").open("w", encoding="utf-8") as stdout, (directory / "stderr.txt").open("w", encoding="utf-8") as stderr:
        try:
            result = subprocess.run(argv, cwd=ROOT, env=env, stdout=stdout, stderr=stderr,
                                    timeout=timeout, check=False)
            code, status, reason = result.returncode, "PASS" if result.returncode == 0 else "FAIL", ""
        except subprocess.TimeoutExpired:
            code, status, reason = None, "BLOCKED", f"Timeout {timeout}s"
    observation = directory / "results.json"
    if observation.exists():
        observed = json.loads(observation.read_text(encoding="utf-8"))
        if observed.get("status") in {"PASS", "FAIL", "BLOCKED", "NOT_RUN"}:
            status = observed["status"]
            reason = observed.get("reason", reason)
    record = {"id": identifier, "argv": argv, "command_windows": subprocess.list2cmdline(argv),
              "cwd": str(ROOT), "started_utc": started, "duration_seconds": time.perf_counter()-clock,
              "exit_code": code, "status": status, "reason": reason,
              "environment": {"PYTHONNOUSERSITE": "1", "PYTHONPATH": "unset",
                              "python": str(PY), "stage_versions": "../core-environment/stdout.txt or ../labs-environment/stdout.txt"},
              "inputs": [digest(ROOT / item) for item in inputs if (ROOT/item).is_file()],
              "stdout": "stdout.txt", "stderr": "stderr.txt"}
    (directory / "run.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"id": identifier, "status": status, "exit_code": code}), flush=True)
    return record


def snapshot() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode("utf-8").split("\0")
    files = [digest(ROOT/name) for name in tracked if name and not name.startswith("audit/")]
    info = {"base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "client_date": "2026-11-17", "host_utc": datetime.now(timezone.utc).isoformat(),
            "os": platform.platform(), "host_python": sys.version, "files": files}
    (EVIDENCE/"source-inventory.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["core", "labs", "supplemental"], required=True)
    parser.add_argument("--vina", type=Path)
    args = parser.parse_args()
    helper = str(BASE / "check.py")
    if args.phase == "core":
        snapshot()
        if ENV.exists():
            raise FileExistsError("Audit venv must start absent")
        execute("00-create-venv", [sys.executable, "-m", "venv", str(ENV)])
        result = execute("01-install-core", [str(PY), "-m", "pip", "install", "-r", "Stepik_course/practice/requirements-ml.txt"],
                         ["Stepik_course/practice/requirements.txt", "Stepik_course/practice/requirements-ml.txt"])
        if result["status"] != "PASS": raise SystemExit("Core dependencies failed; evidence retained")
        execute("core-environment", [str(PY), helper, "environment"])
        execute("02-core-tests", [str(PY), "-m", "unittest", "discover", "-s", "Stepik_course/practice", "-p", "test_practice.py", "-v"],
                ["Stepik_course/practice/test_practice.py", "Stepik_course/practice/molecules.csv", "Stepik_course/practice/activities.csv"])
        execute("03-chemistry", [str(PY), "Stepik_course/practice/chemistry.py"], ["Stepik_course/practice/molecules.csv"])
        execute("04-audit-numerics", [str(PY), helper, "numerics"], ["Stepik_course/03_STEPIK.md", "Stepik_course/04_CASES.md", "Stepik_course/practice/stepik_tasks.py"])
        execute("05-esol", [str(PY), "Stepik_course/practice/train_esol.py", "--csv", "Labs/datasets/esol.csv", "--out", str(EVIDENCE/"05-esol/results")],
                ["Labs/datasets/esol.csv", "Stepik_course/practice/train_esol.py"])
        execute("06-esol-evidence", [str(PY), helper, "esol", "06-esol-evidence"], ["Labs/datasets/esol.csv", "Stepik_course/practice/esol_results/report.json"])
        execute("07-module-examples", [str(PY), helper, "module-examples"], [str(p.relative_to(ROOT)) for p in sorted((ROOT/"Stepik_course/modules").glob("*.md"))])
    elif args.phase == "supplemental":
        execute("17-case-checks", [str(PY), helper, "cases"], ["Stepik_course/practice/activities.csv", "Stepik_course/04_CASES.md"])
        execute("18-gui", [str(PY), helper, "gui"], ["Labs/app.py", "Labs/datasets/molecules.csv", "Stepik_course/modules/14_delivery.md"])
    else:
        result = execute("08-install-labs", [str(PY), "-m", "pip", "install", "-r", "Labs/requirements.txt"], ["Labs/requirements.txt"])
        if result["status"] != "PASS": raise SystemExit("Labs dependencies failed; evidence retained")
        execute("labs-environment", [str(PY), helper, "environment"])
        execute("09-kernel", [str(PY), "-m", "ipykernel", "install", "--prefix", str(ENV), "--name", "practice-audit-issue1", "--display-name", "Issue 1 audit"])
        execute("10-quickstart", [str(PY), helper, "notebook", "Stepik_course/practice/quickstart.ipynb", "10-quickstart"], ["Stepik_course/practice/quickstart.ipynb"])
        execute("11-labs-tests", [str(PY), "-m", "unittest", "discover", "-s", "Labs", "-p", "test_labs.py", "-v"], ["Labs/test_labs.py", "Labs/datasets/manifest.json"])
        if args.vina:
            execute("12-vina-provenance", [str(PY), helper, "vina", str(args.vina.resolve())], ["Labs/datasets/docking/provenance.json"])
        for number in range(1,15):
            name = f"lab-{number:02d}"
            execute(name, [str(PY), helper, "notebook", f"Labs/notebooks/lab{number:02d}.ipynb", name],
                    [f"Labs/notebooks/lab{number:02d}.ipynb", "Labs/datasets/manifest.json"], timeout=1200)
        execute("13-artifacts", [str(PY), helper, "artifacts"], ["Labs/datasets/manifest.json"])
        execute("14-structure", [str(PY), "tools/validate_course.py"], ["course-manifest.json"])
        execute("15-pyscf-probe", [str(PY), helper, "pyscf"], ["Labs/pyscf_dft.py", "Labs/extensions/dft_pyscf.ipynb"])
        execute("16-platform-capstone", [str(PY), helper, "gaps"], ["Stepik_course/12_PRACTICE_FIRST_GATE.md", "Stepik_course/modules/14_delivery.md"])


if __name__ == "__main__":
    main()
