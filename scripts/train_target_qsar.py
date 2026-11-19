"""Target-specific QSAR: nested scaffold CV, sealed test and grouped calibration.

All endpoints remain separate. Numerical accuracy is reported, never assumed.
"""
import argparse
import csv
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import sys

import joblib
import numpy as np
from rdkit import Chem,DataStructs,rdBase
from rdkit.Chem import Descriptors,Lipinski,rdFingerprintGenerator,rdMolDescriptors
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error,mean_squared_error,r2_score
from sklearn.model_selection import GroupKFold,GroupShuffleSplit,GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT=Path(__file__).resolve().parents[1]
SEED=20261118
DESCRIPTORS=['MolWt','MolLogP','TPSA','HBD','HBA','rotatable_bonds','fraction_CSP3','ring_count','aromatic_rings','formal_charge','heavy_atoms']


def dump(path,value):
    with Path(path).open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)


def scaffold(mol):
    core=MurckoScaffold.GetScaffoldForMol(mol)
    if core.GetNumAtoms():return 'MURCKO:'+Chem.MolToSmiles(core,isomericSmiles=False)
    return 'ACYCLIC_TOPOLOGY:'+Chem.MolToSmiles(MurckoScaffold.MakeScaffoldGeneric(Chem.RemoveHs(mol)),isomericSmiles=False)


def featurize(mol,generator):
    fingerprint=generator.GetFingerprint(mol);bits=np.zeros(2048,dtype=np.uint8)
    DataStructs.ConvertToNumpyArray(fingerprint,bits)
    d=[Descriptors.MolWt(mol),Descriptors.MolLogP(mol),Descriptors.TPSA(mol),Lipinski.NumHDonors(mol),
       Lipinski.NumHAcceptors(mol),Lipinski.NumRotatableBonds(mol),rdMolDescriptors.CalcFractionCSP3(mol),
       rdMolDescriptors.CalcNumRings(mol),rdMolDescriptors.CalcNumAromaticRings(mol),Chem.GetFormalCharge(mol),mol.GetNumHeavyAtoms()]
    return np.r_[d,bits],fingerprint


def estimator():
    descriptor_transform=ColumnTransformer([('descriptors',StandardScaler(),list(range(len(DESCRIPTORS))))])
    fingerprint_transform=ColumnTransformer([('Morgan', 'passthrough',list(range(len(DESCRIPTORS),len(DESCRIPTORS)+2048)))])
    pipeline=Pipeline([('features',descriptor_transform),('model',Ridge(solver='lsqr',tol=1e-8))])
    grid=[{'features':[descriptor_transform],'model':[Ridge(solver='lsqr',tol=1e-8)],'model__alpha':[.01,.1,1.,10.,100.]},
          {'features':[fingerprint_transform],'model':[RandomForestRegressor(n_estimators=1000,max_features=.33,
             min_samples_leaf=2,random_state=SEED,n_jobs=1)]}]
    return GridSearchCV(pipeline,grid,cv=GroupKFold(3),scoring='neg_root_mean_squared_error',
                        n_jobs=2,refit=True,return_train_score=False,error_score='raise')


def metrics(y,pred):
    return {'n':len(y),'RMSE':float(np.sqrt(mean_squared_error(y,pred))),
            'MAE':float(mean_absolute_error(y,pred)),'R2':float(r2_score(y,pred)),
            'bias':float(np.mean(pred-y))}


def group_bootstrap(y,pred,groups,count=2000):
    rng=np.random.default_rng(SEED);unique=np.unique(groups);rmse=[]
    for _ in range(count):
        selected=rng.choice(unique,size=len(unique),replace=True)
        indices=np.concatenate([np.flatnonzero(groups==g) for g in selected])
        rmse.append(float(np.sqrt(np.mean((y[indices]-pred[indices])**2))))
    return np.quantile(rmse,[.025,.975]).tolist()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--dataset',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    card=json.loads((args.dataset/'dataset.json').read_text(encoding='utf-8'))
    source=args.dataset/'curated.csv'
    if hashlib.sha256(source.read_bytes()).hexdigest()!=card['sha256_curated_csv']:raise ValueError('Changed curated input')
    with source.open(encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream))
    molecules=[Chem.MolFromSmiles(r['smiles']) for r in rows]
    if not all(m is not None for m in molecules):raise ValueError('Invalid curated structure')
    generator=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=2048,includeChirality=True)
    features=[featurize(m,generator) for m in molecules];X=np.array([f[0] for f in features]);fps=[f[1] for f in features]
    y=np.array([float(r['y']) for r in rows]);groups=np.array([scaffold(m) for m in molecules])
    if len(y)<80 or len(set(groups))<20:
        dump(out/'result.json',{'status':'BLOCKED','reason':'Insufficient data for the predeclared nested 5x3 / calibration / sealed-test protocol',
          'n_total':len(y),'n_scaffolds':len(set(groups)),'required_compounds':80,'required_scaffolds':20,
          'dataset_sha256':card['sha256_curated_csv'],'endpoint':'p'+card['endpoint'],
          'target_id':card['target']['target_chembl_id'],'model_training':'NOT_RUN',
          'scope':'eligibility assessment, not a fitted QSAR; thresholds were not relaxed to obtain a result'})
        raise SystemExit(2)
    compounds=json.loads((ROOT/'practicuum/shared/data/compounds.json').read_text(encoding='utf-8'))
    query_names=['istradefylline','caffeine'] if card['target']['target_chembl_id']=='CHEMBL251' else ['atorvastatin','atorvastatin_lactone']
    queries=[next(r for r in compounds if r['name']==n) for n in query_names]
    query_mols=[Chem.MolFromSmiles(r['smiles']) for r in queries];query_groups={scaffold(m) for m in query_mols}
    development,test=next(GroupShuffleSplit(n_splits=1,test_size=.2,random_state=SEED).split(X,y,groups))
    # Every named drug scaffold is forced into the sealed test; no target-drug memorization.
    forced=np.flatnonzero(np.isin(groups,list(query_groups)));test=np.unique(np.r_[test,forced])
    development=np.setdiff1d(np.arange(len(y)),test)
    train_local,cal_local=next(GroupShuffleSplit(n_splits=1,test_size=.25,random_state=SEED+1).split(X[development],y[development],groups[development]))
    train=development[train_local];cal=development[cal_local]
    partitions={'training':train,'calibration':cal,'test':test}
    for a,b in [('training','calibration'),('training','test'),('calibration','test')]:
        if set(groups[partitions[a]])&set(groups[partitions[b]]):raise AssertionError('Scaffold leakage')
    if len(set(groups[train]))<10:raise RuntimeError('Too few training scaffolds after drug-scaffold holdout')
    dump(out/'split.json',{k:{'row_ids':indices.tolist(),'scaffolds':sorted(set(groups[indices]))} for k,indices in partitions.items()})
    nested=np.full(len(train),np.nan);outer=[]
    for fold,(tr,va) in enumerate(GroupKFold(5).split(X[train],y[train],groups[train]),1):
        search=estimator();search.fit(X[train[tr]],y[train[tr]],groups=groups[train[tr]])
        pred=search.predict(X[train[va]]);nested[va]=pred
        entry={'fold':fold,'train_row_ids':train[tr].tolist(),'validation_row_ids':train[va].tolist(),
               'metrics':metrics(y[train[va]],pred),'selected_model':str(search.best_estimator_),
               'inner_group_CV_RMSE':float(-search.best_score_)}
        outer.append(entry);dump(out/f'outer-fold-{fold}.json',entry)
        print(card['endpoint'],'outer fold',fold,entry['metrics'],flush=True)
    final=estimator();final.fit(X[train],y[train],groups=groups[train])
    test_prediction=final.predict(X[test]);cal_prediction=final.predict(X[cal])
    baseline=DummyRegressor(strategy='mean').fit(X[train],y[train]).predict(X[test])
    # Calibration units are scaffolds: maxima give group-level simultaneous coverage
    # only if future scaffold groups are exchangeable with calibration groups.
    cal_residual=abs(cal_prediction-y[cal]);cal_groups=np.unique(groups[cal])
    scores=np.array([max(cal_residual[groups[cal]==g]) for g in cal_groups]);alpha=.1
    rank=math.ceil((len(scores)+1)*(1-alpha))
    width=float(np.sort(scores)[rank-1]) if rank<=len(scores) else None
    test_metrics=metrics(y[test],test_prediction)
    test_metrics['scaffold_bootstrap_RMSE_CI95']=group_bootstrap(y[test],test_prediction,groups[test])
    test_metrics['conformal_group_calibration_n']=len(scores)
    test_metrics['coverage_90']=float(np.mean(abs(test_prediction-y[test])<=width)) if width is not None else None
    results=[]
    trainfps=[fps[i] for i in train]
    for record,m in zip(queries,query_mols):
        feature,fp=featurize(m,generator);prediction=float(final.predict(feature.reshape(1,-1))[0])
        nearest=DataStructs.BulkTanimotoSimilarity(fp,trainfps);j=int(np.argmax(nearest))
        results.append({'name':record['name'],'smiles':record['smiles'],'predicted_p'+card['endpoint']:prediction,
            'scaffold_excluded_from_training':scaffold(m) not in set(groups[train]),
            'nearest_train_Tanimoto':nearest[j],'nearest_train_row_id':int(train[j]),
            'conditional_90_interval':[prediction-width,prediction+width] if width is not None else None,
            'decision':'REVIEW: target/endpoint prediction, not experimental affinity, exposure or efficacy',
            'interval_assumption':'exchangeable scaffold groups; no guaranteed coverage under chemical-domain shift'})
    with (out/'heldout_predictions.csv').open('x',encoding='utf-8',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(['row_id','smiles','scaffold','observed','predicted'])
        writer.writerows((int(i),rows[i]['smiles'],groups[i],float(y[i]),float(p)) for i,p in zip(test,test_prediction))
    joblib.dump(final.best_estimator_,out/'fitted_pipeline.joblib',compress=3)
    report={'status':'PASS','created_utc':datetime.now(timezone.utc).isoformat(),'target_id':card['target']['target_chembl_id'],
      'endpoint':'p'+card['endpoint'],'units':'negative log10 molar concentration; assay endpoint retained',
      'dataset_sha256':card['sha256_curated_csv'],'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      'features':{'descriptors':DESCRIPTORS,'Morgan_radius':2,'Morgan_size':2048,'chirality':True},
      'n_total':len(y),'n_scaffolds':len(set(groups)),'partitions':{k:len(v) for k,v in partitions.items()},
      'nested_5x3_training_CV':metrics(y[train],nested),'outer_folds':outer,'sealed_test':test_metrics,
      'sealed_test_mean_baseline':metrics(y[test],baseline),'selected_model':str(final.best_estimator_),
      'query_results':results,'python':sys.version,'rdkit':rdBase.rdkitVersion,
      'versions':{n:importlib.metadata.version(n) for n in ['numpy','scipy','scikit-learn','rdkit']},
      'scientific_review':'NOT_RUN','prospective_assay_validation':'NOT_RUN',
      'limitations':['Pooled exact endpoints remain heterogeneous across assays','Named query drug scaffolds are excluded from all training/calibration',
                     'Source-data holdout is not independent prospective validation','Conformal coverage needs scaffold-group exchangeability',
                     'Bootstrap CI measures test-group sampling variability, not all model uncertainty',
                     'No claim about clinical efficacy, tissue exposure or binding mechanism','Stereochemistry kept in structure and fingerprints; scaffold split groups stereoisomers together']}
    dump(out/'result.json',report);print('QSAR completed',report['target_id'],test_metrics,flush=True)


if __name__=='__main__':main()
