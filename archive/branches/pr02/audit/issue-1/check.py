"""Audit-only observations. References and course implementation are read-only."""
from __future__ import annotations
import contextlib
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(os.environ.get("PRACTICE_AUDIT_OUTPUT", str(ROOT / "audit/issue-1/evidence"))).resolve()


def write(name: str, data: dict) -> None:
    target = BASE/name/"results.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(data, ensure_ascii=False, indent=2))


def environment() -> None:
    distributions = sorted({item.metadata["Name"]: item.version for item in importlib.metadata.distributions()}.items())
    print(json.dumps({"python": sys.version, "executable": sys.executable, "prefix": sys.prefix,
                      "base_prefix": sys.base_prefix, "isolated": sys.prefix != sys.base_prefix,
                      "platform": platform.platform(), "machine": platform.machine(),
                      "utc": datetime.now(timezone.utc).isoformat(), "packages": dict(distributions)}, indent=2))


def numerics() -> None:
    sys.path.insert(0, str(ROOT/"Stepik_course/practice"))
    import stepik_tasks as tasks
    checks = []
    def record(key, inputs, expected, actual):
        passed = math.isclose(actual, expected, rel_tol=0, abs_tol=1e-5)
        checks.append({"id": key, "input": inputs, "expected": expected, "actual": actual,
                       "status": "PASS" if passed else "FAIL", "absolute_tolerance": 1e-5})
    for i,(value,unit,expected) in enumerate([(100,"nM",7),(0.1,"uM",7),(1,"mM",3),(2,"M",-math.log10(2))],1):
        record(f"P1-{i}",[value,unit],expected,tasks.p_activity(value,unit))
    for i,(a,b,expected) in enumerate([({1,2,3},{2,3,4},.5),({1},{2},0),(set(),set(),1),({2,3,4},{1,2,3},.5)],1):
        record(f"P2-{i}",[sorted(a),sorted(b)],expected,tasks.tanimoto(a,b))
    for i,(inputs,expected) in enumerate([((1000,20,50,5),5),((100,10,10,0),0),((100,10,100,10),1)],1):
        record(f"P3-{i}",inputs,expected,tasks.enrichment(*inputs))
    for i,(inputs,expected) in enumerate([((100,10,5,5),2/3),((10,100,5,5),2/3),((100,10,20,20),-1/3)],1):
        record(f"P4-{i}",inputs,expected,tasks.z_prime(*inputs))
    record("F-energy",[-100.0,-100.01,2625.5],-26.255,(-100.01+100)*2625.5)
    record("G-yield-A",[.8,.7],.56,.8*.7)
    record("G-yield-B",[.95,.9],.855,.95*.9)
    record("G-cost-A",[600,.8,.7],1071.4285714285713,600/(.8*.7))
    record("G-cost-B",[750,.95,.9],877.1929824561404,750/(.95*.9))
    y=[-3,-2,-1]
    record("E-MAE-A",[y,[-2.5,-2.5,-1]],1/3,sum(abs(a-b) for a,b in zip(y,[-2.5,-2.5,-1]))/3)
    record("E-MAE-B",[y,[-2,-2,-2]],2/3,sum(abs(a-b) for a,b in zip(y,[-2,-2,-2]))/3)
    rows=[(-1,-1,43),(1,-1,47),(-1,1,37),(1,1,73)]
    for axis,expected in [("A",20),("B",10),("AB",16)]:
        sign=lambda a,b: a if axis=="A" else b if axis=="B" else a*b
        actual=sum(value*sign(a,b) for a,b,value in rows)/2
        record("H-effect-"+axis,rows,expected,actual)
    result={"status":"PASS" if all(r["status"]=="PASS" for r in checks) else "FAIL",
            "scope":"Audit arithmetic / reference function calls only, not learner interpretation or Stepik grader",
            "checks":checks}
    write("04-audit-numerics",result)


def module_examples(name="07-module-examples") -> None:
    results=[]
    folder=BASE/name
    folder.mkdir(parents=True,exist_ok=True)
    for path in sorted((ROOT/"Stepik_course/modules").glob("*.md")):
        number=int(path.name[:2])
        text=path.read_text(encoding="utf-8")
        for index,match in enumerate(re.finditer(r"```python\s*\n(.*?)\n```",text,re.S),1):
            code=match.group(1)
            script=folder/f"module-{number:02d}-{index}.py"
            script.write_text(code,encoding="utf-8")
            # Import only the audited Stepik implementation, not the Labs copy.
            wrapper="import sys; sys.path.insert(0,"+repr(str(ROOT/"Stepik_course/practice"))+"); exec(compile("+repr(code)+","+repr(str(path))+",'exec'))"
            argv=[sys.executable,"-c",wrapper]
            process=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True,encoding="utf-8",errors="replace")
            (folder/f"module-{number:02d}-{index}-stdout.txt").write_text(process.stdout,encoding="utf-8")
            (folder/f"module-{number:02d}-{index}-stderr.txt").write_text(process.stderr,encoding="utf-8")
            status="PASS" if process.returncode==0 else "BLOCKED" if "No module named 'pyscf'" in process.stderr else "FAIL"
            results.append({"module":number,"index":index,"source":path.relative_to(ROOT).as_posix(),
                            "source_line":text[:match.start()].count("\n")+1,"argv":argv,
                            "exit_code":process.returncode,"status":status,
                            "reason":"PySCF not installed in native Windows environment" if status=="BLOCKED" else "",
                            "stdout":process.stdout,"stderr_file":f"module-{number:02d}-{index}-stderr.txt"})
    write(name,{"status":"BLOCKED" if any(r["status"]=="BLOCKED" for r in results) else "FAIL" if any(r["status"]=="FAIL" for r in results) else "PASS",
                                "reason":"Mixed results; see per-example status", "checks":results})


def esol(name="06-esol-evidence-retry") -> None:
    from rdkit import Chem
    from rdkit.Chem.Scaffolds import MurckoScaffold
    checks=[]
    def check(key, expected, actual, passed):
        checks.append({"id":key,"expected":expected,"actual":actual,"status":"PASS" if passed else "FAIL"})
    data=ROOT/"Labs/datasets/esol.csv"
    rows=list(csv.DictReader(data.open(encoding="utf-8")))
    report=json.loads((BASE/"05-esol/results/report.json").read_text(encoding="utf-8"))
    checksum=hashlib.sha256(data.read_bytes()).hexdigest()
    check("data-hash",report["input_sha256"],checksum,checksum==report["input_sha256"])
    check("data-rows",1128,len(rows),len(rows)==1128)
    old=json.loads((ROOT/"Stepik_course/practice/esol_results/report.json").read_text(encoding="utf-8"))
    identities=[]
    scaffolds=[]
    for row in rows:
        mol=Chem.MolFromSmiles(row["smiles"])
        identities.append(Chem.MolToSmiles(mol,canonical=True,isomericSmiles=True))
        scaffolds.append(MurckoScaffold.MurckoScaffoldSmiles(mol=mol) or "ACYCLIC_ALL")
    for kind in ["identity","scaffold"]:
        membership=json.loads((BASE/f"05-esol/results/{kind}_split.json").read_text(encoding="utf-8"))
        predictions=list(csv.DictReader((BASE/f"05-esol/results/{kind}_predictions.csv").open(encoding="utf-8")))
        train=[i for i,m in enumerate(membership) if m=="train"]
        test=[i for i,m in enumerate(membership) if m=="test"]
        overlaps=set(identities[i] for i in train)&set(identities[i] for i in test)
        check(kind+"-identity-overlap",0,len(overlaps),not overlaps)
        if kind=="scaffold":
            overlap=set(scaffolds[i] for i in train)&set(scaffolds[i] for i in test)
            check("scaffold-overlap",0,len(overlap),not overlap)
        check(kind+"-test-membership",test,[int(r["row"]) for r in predictions],test==[int(r["row"]) for r in predictions])
        actual=[float(rows[int(r["row"])]["measured log solubility in mols per litre"]) for r in predictions]
        check(kind+"-target-provenance",True,all(abs(y-float(r["measured_logS"]))<1e-12 for y,r in zip(actual,predictions)),all(abs(y-float(r["measured_logS"]))<1e-12 for y,r in zip(actual,predictions)))
        mae=sum(abs(y-float(r["predicted"])) for y,r in zip(actual,predictions))/len(predictions)
        saved=report["splits"][kind]["metrics"]["random_forest"]["MAE_logS"]
        check(kind+"-MAE-recomputed",saved,mae,abs(saved-mae)<1e-12)
        check(kind+"-historical-MAE",old["splits"][kind]["metrics"]["random_forest"]["MAE_logS"],mae,abs(mae-old["splits"][kind]["metrics"]["random_forest"]["MAE_logS"])<1e-9)
        mean_train=sum(float(rows[i]["measured log solubility in mols per litre"]) for i in train)/len(train)
        check(kind+"-baseline-is-train-mean",mean_train,float(predictions[0]["baseline"]),all(abs(float(r["baseline"])-mean_train)<1e-10 for r in predictions))
    try:
        from urllib.request import urlopen
        with urlopen(report["source_url"],timeout=45) as response:
            content=response.read()
        (BASE/name/"upstream-esol.csv").write_bytes(content)
        upstream_hash=hashlib.sha256(content).hexdigest()
        check("upstream-live-hash",checksum,upstream_hash,upstream_hash==checksum)
    except Exception as error:
        checks.append({"id":"upstream-live-hash","status":"BLOCKED","actual":repr(error),"expected":checksum})
    write(name,{"status":"FAIL" if any(c["status"]=="FAIL" for c in checks) else "BLOCKED" if any(c["status"]=="BLOCKED" for c in checks) else "PASS", "checks":checks})


def notebook(source: str, name: str) -> None:
    import nbformat
    from nbclient import NotebookClient
    os.environ["JUPYTER_PATH"] = str(Path(sys.prefix)/"share/jupyter")
    path = ROOT/source
    book = nbformat.read(path, as_version=4)
    # Strip all historical outputs before running; never retain a stale PASS.
    for cell in book.cells:
        if cell.cell_type == "code":
            cell.outputs=[]
            cell.execution_count=None
    target = BASE/name/"executed.ipynb"
    try:
        client = NotebookClient(book,timeout=900,kernel_name="practice-audit-issue1",
                                resources={"metadata":{"path":str(ROOT)}})
        client.execute()
    finally:
        nbformat.write(book,target)
    write(name,{"status":"PASS","source":source,"source_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                "kernel":"practice-audit-issue1", "code_cells_executed":sum(cell.cell_type=="code" for cell in book.cells),
                "output":"executed.ipynb","scope":"Reference notebook execution and its assertions; no learner/Stepik verification"})


def vina(source: str) -> None:
    path=Path(source)
    checksum=hashlib.sha256(path.read_bytes()).hexdigest()
    expected="e0c4b2715e0c1a74f6e92d0f3be0328ac97542eafbc111e6b1efad897a73cce5"
    if checksum!=expected:
        write("12-vina-provenance",{"status":"BLOCKED","reason":"Local binary differs from recorded v1.2.7 checksum","sha256":checksum})
        return
    version=subprocess.run([str(path),"--version"],capture_output=True,text=True,check=True)
    target=ROOT/"tools/bin/vina_1.2.7_win.exe"
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(path,target)
    write("12-vina-provenance",{"status":"PASS","source":str(path),"target":str(target),"sha256":checksum,
                                 "version_command":[str(path),"--version"],"version_stdout":version.stdout,
                                 "origin":"Previously downloaded official v1.2.7 binary, explicitly hashed external dependency"})


def artifacts() -> None:
    import numpy as np
    import pandas as pd
    from rdkit import Chem
    tests=[]
    def checked(key, condition, actual):
        tests.append({"id":key,"status":"PASS" if bool(condition) else "FAIL","actual":actual})
    core=json.loads((BASE/"03-chemistry/stdout.txt").read_text(encoding="utf-8"))
    checked("chemistry-row-preservation",len(core["results"])==12,len(core["results"]))
    invalid=[r["id"] for r in core["results"] if r["status"]=="invalid"]
    checked("chemistry-invalid-rows",invalid==["M08","M09"],invalid)
    for directory in [BASE/"05-esol/results",ROOT/"Labs/results/lab11"]:
        report=json.loads((directory/"report.json").read_text(encoding="utf-8"))
        actual_hash=hashlib.sha256((ROOT/"Labs/datasets/esol.csv").read_bytes()).hexdigest()
        checked(str(directory.relative_to(ROOT))+"-source-hash",report["input_sha256"]==actual_hash,actual_hash)
        for kind in ["identity","scaffold"]:
            membership=json.loads((directory/f"{kind}_split.json").read_text(encoding="utf-8"))
            predictions=pd.read_csv(directory/f"{kind}_predictions.csv")
            measured=pd.read_csv(ROOT/"Labs/datasets/esol.csv")
            test_indices=[i for i,item in enumerate(membership) if item=="test"]
            checked(f"{directory.relative_to(ROOT)}-{kind}-rows",len(membership)==1128 and list(predictions.row)==test_indices,len(test_indices))
            target=measured.loc[predictions.row,"measured log solubility in mols per litre"].to_numpy()
            checked(f"{directory.relative_to(ROOT)}-{kind}-measured",np.allclose(target,predictions.measured_logS),float(np.max(abs(target-predictions.measured_logS))))
            mae=float(np.mean(abs(target-predictions.predicted.to_numpy())))
            expected=report["splits"][kind]["metrics"]["random_forest"]["MAE_logS"]
            checked(f"{directory.relative_to(ROOT)}-{kind}-MAE-recomputed",abs(mae-expected)<1e-12,mae)
    energy=pd.read_csv(ROOT/"Labs/results/lab06/energies.csv")
    conformers=list(Chem.SDMolSupplier(str(ROOT/"Labs/results/lab06/butane_conformers.sdf"),removeHs=False))
    checked("SDF-record-count",len(conformers)==len(energy) and all(m is not None for m in conformers),len(conformers))
    checked("SDF-status-energy-properties",all(m.HasProp("MMFF_status") and m.HasProp("MMFF_energy_kcal_mol") for m in conformers),[m.GetProp("MMFF_status") for m in conformers])
    for relative in ["lab09/structures.png","lab09/properties.png","lab09/report.html","lab14/cli/report.csv","lab14/cli/report.json"]:
        file=ROOT/"Labs/results"/relative
        checked("output-"+relative,file.exists() and file.stat().st_size>0,file.stat().st_size if file.exists() else 0)
    docking=json.loads((ROOT/"Labs/results/lab10/docking.json").read_text(encoding="utf-8"))
    checked("Vina-executed-mode",docking["mode"]=="executed-vina",docking)
    write("13-artifacts",{"status":"PASS" if all(t["status"]=="PASS" for t in tests) else "FAIL","checks":tests})
    # Preserve the actual reference outputs, not only an assertion summary.
    shutil.copytree(ROOT/"Labs/results",BASE/"13-artifacts/labs-results",dirs_exist_ok=True)


def pyscf() -> None:
    installed=importlib.util.find_spec("pyscf") is not None
    write("15-pyscf-probe",{"status":"BLOCKED" if not installed else "NOT_RUN",
                           "reason":"PySCF absent from the isolated Windows environment; no supported Linux/WSL kernel provisioned" if not installed else "Found package but no QM execution in this probe",
                           "pyscf_importable":installed,"platform":platform.platform(),
                           "executed_DFT":False,"RHF_H2_is_not_PySCF_or_DFT":True})


def gaps() -> None:
    write("16-platform-capstone",{"status":"BLOCKED","reason":"No Stepik test-course/grader execution evidence, learner dossier/defense or implemented concept-map editor/export tests supplied",
        "checks":[{"id":"stepik-grader","status":"BLOCKED","actual":"Local reference functions only; no target course ID, grader submission or grade trace"},
                  {"id":"learner-final-project","status":"NOT_RUN","actual":"Reference CLI/application execution is separate from learner work, independent transfer, dossier and defense"},
                  {"id":"concept-map","status":"BLOCKED","actual":"Specification in 09_EVOLVING_CONCEPT_MAP.md; no implemented editor/JSON export acceptance scenario"}]})


def case_checks() -> None:
    sys.path.insert(0,str(ROOT/"Stepik_course/practice"))
    from chemistry import curate_activity
    rows=list(csv.DictReader((ROOT/"Stepik_course/practice/activities.csv").open(encoding="utf-8")))
    expectations={"R01":("included",7.0,"teaching rules satisfied"),"R02":("included",7.0,"teaching rules satisfied"),
                  "R03":("excluded",None,"relation"),"R04":("excluded",None,"endpoint"),
                  "R05":("excluded",None,"target_id"),"R06":("excluded",None,"assay_id"),
                  "R07":("excluded",None,"value_or_unit"),"R08":("excluded",None,"value_or_unit")}
    checks=[]
    for row in rows:
        actual=curate_activity(row);expected=expectations[row['record_id']]
        observed=(actual['status'],actual.get('pIC50'),actual['reason'])
        checks.append({"id":"B-"+row['record_id'],"input":row,"expected":expected,"actual":observed,
                       "status":"PASS" if observed==expected else "FAIL"})
    checks.append({"id":"C-nominal-cost","input":[5,20000],"expected":100000,"actual":5*20000,"status":"PASS","scope":"nominal arithmetic only, no net economic benefit proven"})
    write("17-case-checks",{"status":"PASS" if all(c['status']=='PASS' for c in checks) else "FAIL","checks":checks})


def gui() -> None:
    from unittest.mock import patch
    from streamlit.testing.v1 import AppTest
    sys.path.insert(0,str(ROOT/'Labs'))
    checks=[]
    data=(ROOT/'Labs/datasets/molecules.csv').read_bytes()
    app=AppTest.from_file(str(ROOT/'Labs/app.py'))
    with patch('streamlit.file_uploader',return_value=io.BytesIO(data)):
        app.run()
    checks.append({"id":"gui-reference-csv","status":"PASS" if not app.exception and len(app.dataframe)==1 and len(app.dataframe[0].value)==12 else "FAIL",
                   "expected":"12 reference rows without an unhandled exception","actual":{"exceptions":len(app.exception),"dataframes":len(app.dataframe),"rows":len(app.dataframe[0].value) if app.dataframe else 0}})
    controls={name:len(getattr(app,name)) for name in ['checkbox','toggle','selectbox','radio']}
    checks.append({"id":"gui-tautomer-switch","status":"PASS" if controls['checkbox']+controls['toggle']>0 else "FAIL",
                   "expected":"User-operable tautomer-processing switch required by Stepik_course/modules/14_delivery.md section 14.2",
                   "actual":controls,"interpretation":"Contract mismatch with this source, not a chemical failure; current app displays a fixed policy"})
    bad=b'id,smiles\nX,CCO\nX,CCN\n'
    app=AppTest.from_file(str(ROOT/'Labs/app.py'))
    with patch('streamlit.file_uploader',return_value=io.BytesIO(bad)):
        app.run()
    checks.append({"id":"gui-duplicate-id","status":"PASS" if not app.exception and len(app.error)>0 else "FAIL",
                   "input":bad.decode(),"expected":"Visible validation error, no unhandled exception",
                   "actual":{"exceptions":len(app.exception),"errors":[item.value for item in app.error]}})
    write('18-gui',{'status':'FAIL' if any(c['status']=='FAIL' for c in checks) else 'PASS','scope':'Streamlit AppTest with mocked file uploader, not live browser/Stepik or learner grading','checks':checks})


if __name__=="__main__":
    command,*args=sys.argv[1:]
    {"environment":environment,"numerics":numerics,"module-examples":module_examples,"snippets":module_examples,"esol":esol,"notebook":notebook,"vina":vina,
     "artifacts":artifacts,"pyscf":pyscf,"gaps":gaps,"cases":case_checks,"gui":gui}[command](*args)
