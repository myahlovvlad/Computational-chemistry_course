"""Independently audit saved partitions, predictions and target-drug exclusion."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator
from train_target_qsar import scaffold, metrics

ROOT=Path(__file__).resolve().parents[1]


def validate_partitions(groups, partitions):
    n=len(groups);seen=set()
    for name,part in partitions.items():
        ids=part['row_ids']
        if len(ids)!=len(set(ids)) or any(type(i) is not int or not 0<=i<n for i in ids):
            raise ValueError('Invalid or duplicate row ID in '+name)
        if seen.intersection(ids):raise ValueError('Overlapping rows')
        seen.update(ids)
        if set(part['scaffolds'])!={groups[i] for i in ids}:raise ValueError('Scaffold ledger mismatch')
    if seen!=set(range(n)):raise ValueError('Partitions do not cover the dataset')
    names=list(partitions)
    for j,a in enumerate(names):
        for b in names[j+1:]:
            if set(partitions[a]['scaffolds']) & set(partitions[b]['scaffolds']):
                raise ValueError('Scaffold leakage')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',type=Path,required=True)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    report=json.loads((args.run/'result.json').read_text(encoding='utf-8'))
    if hashlib.sha256((ROOT/'scripts/train_target_qsar.py').read_bytes()).hexdigest()!=report['script_sha256']:
        raise ValueError('Training source changed; use the exact recorded source before freezing it')
    raw=(args.dataset/'curated.csv').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=report['dataset_sha256']:raise ValueError('Dataset changed')
    with (args.dataset/'curated.csv').open(encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream))
    mols=[Chem.MolFromSmiles(r['smiles']) for r in rows]
    groups=[scaffold(m) for m in mols]
    split=json.loads((args.run/'split.json').read_text(encoding='utf-8'))
    validate_partitions(groups,split)
    train=set(split['training']['row_ids']);outer_seen=set()
    for path in sorted(args.run.glob('outer-fold-*.json')):
        fold=json.loads(path.read_text(encoding='utf-8'))
        tr=set(fold['train_row_ids']);va=set(fold['validation_row_ids'])
        if tr & va or tr|va!=train:raise ValueError('Outer fold row leakage or coverage')
        if {groups[i] for i in tr}&{groups[i] for i in va}:raise ValueError('Outer fold scaffold leakage')
        if outer_seen&va:raise ValueError('Repeated outer validation row')
        outer_seen.update(va)
    if outer_seen!=train:raise ValueError('Outer CV does not validate every training row')
    with (args.run/'heldout_predictions.csv').open(encoding='utf-8',newline='') as stream:heldout=list(csv.DictReader(stream))
    if [int(r['row_id']) for r in heldout]!=split['test']['row_ids']:raise ValueError('Heldout row order mismatch')
    y=[];p=[]
    for r in heldout:
        i=int(r['row_id'])
        if r['smiles']!=rows[i]['smiles'] or r['scaffold']!=groups[i] or float(r['observed'])!=float(rows[i]['y']):
            raise ValueError('Heldout identity or observation mismatch')
        y.append(float(r['observed']));p.append(float(r['predicted']))
    y=np.asarray(y);p=np.asarray(p)
    m=metrics(y,p)
    for key in ['RMSE','MAE','R2','bias']:
        if not np.isclose(m[key],report['sealed_test'][key],rtol=1e-12,atol=1e-12):raise ValueError('Metric mismatch '+key)
    width=(report['query_results'][0]['conditional_90_interval'][1]-report['query_results'][0]['conditional_90_interval'][0])/2
    residual=abs(np.array(y)-p)
    testgroups=np.array([r['scaffold'] for r in heldout])
    group_coverage=float(np.mean([np.all(residual[testgroups==g]<=width) for g in np.unique(testgroups)]))
    gen=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=2048,includeChirality=True)
    train_ids=split['training']['row_ids'];fps=[gen.GetFingerprint(mols[i]) for i in train_ids]
    queries=[]
    for q in report['query_results']:
        mol=Chem.MolFromSmiles(q['smiles']);g=scaffold(mol)
        if g in set(split['training']['scaffolds'])|set(split['calibration']['scaffolds']):raise ValueError('Named query scaffold leakage')
        similarity=DataStructs.BulkTanimotoSimilarity(gen.GetFingerprint(mol),fps)
        if not np.isclose(max(similarity),q['nearest_train_Tanimoto'],atol=1e-12):raise ValueError('Nearest similarity mismatch')
        observed=[float(rows[i]['y']) for i in split['test']['row_ids'] if rows[i]['smiles']==q['smiles']]
        queries.append({'name':q['name'],'nearest_train_Tanimoto':max(similarity),
                        'exact_graph_observations_in_sealed_test':observed,
                        'prediction_minus_observation':None if not observed else q['predicted_pKi']-observed[0],
                        'decision':'Domain review required; low nearest similarity and pooled-assay heterogeneity limit transfer'})
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    files={}
    for path in sorted(args.run.iterdir()):
        if path.is_file():files[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
    result={'status':'PASS','scope':'independent deterministic audit, not prospective experimental validation',
            'dataset_sha256':report['dataset_sha256'],'artifacts_sha256':files,
            'partitions_cover_unique_rows':True,'scaffold_leakage':False,'named_query_training_calibration_leakage':False,
            'outer_validation_covers_training_once':True,'recomputed_sealed_test':m,
            'observed_test_scaffold_simultaneous_coverage':group_coverage,
            'test_scaffold_n':len(np.unique(testgroups)),'query_audit':queries,'scientific_review':'NOT_RUN'}
    (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    (out/'training-source.py').write_bytes((ROOT/'scripts/train_target_qsar.py').read_bytes())
    (out/'auditor-source.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
