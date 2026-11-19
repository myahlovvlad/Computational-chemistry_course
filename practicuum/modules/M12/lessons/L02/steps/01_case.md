# Разбор A. Неопределённость и отказ от неподтверждённого переноса

Продолжаем сохранённый QSAR A2A. Сначала различите: 90% условный conformal-интервал, наблюдаемое покрытие на тесте и гарантию для нового химического домена. Для calibration использован максимум абсолютного остатка внутри каждого каркаса. Квантиль с конечновыборочным рангом ceil((m+1)·0.9) даёт условие группового покрытия только при обменности новых каркасов с calibration; это не гарантия для произвольного лекарства.

```python
from pathlib import Path
import sys,json,csv,hashlib,math
import numpy as np
from IPython.display import display
ROOT=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'programm/course.json').is_file())
sys.path.insert(0,str(ROOT/'practicuum/shared'))
from course_support import DATA,workspace,write_json,init_dossier,compound
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=workspace('M12-L02','case')
QDATA=DATA/'target_qsar'
manifest=json.loads((QDATA/'manifest.json').read_text(encoding='utf-8'))
for name,digest in manifest['files_sha256'].items():
    assert hashlib.sha256((QDATA/name).read_bytes()).hexdigest()==digest,name
def read_json(name):return json.loads((QDATA/name).read_text(encoding='utf-8'))
def read_csv(name):
    with (QDATA/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def publish_plot(fig,name):
    fig.savefig(OUT/name,dpi=150,bbox_inches='tight');display(fig);plt.close(fig)
```

```python
rows=read_csv('a2a_curated.csv');split=read_json('a2a_split.json');report=read_json('a2a_result.json')
heldout=read_csv('a2a_heldout_predictions.csv')
y=np.array([float(r['y']) for r in rows])
ids={k:np.array(v['row_ids'],dtype=int) for k,v in split.items()}
assert sorted(np.concatenate(list(ids.values())).tolist())==list(range(len(rows)))
for a,b in [('training','calibration'),('training','test'),('calibration','test')]:
    assert not (set(split[a]['scaffolds']) & set(split[b]['scaffolds']))
assert [int(r['row_id']) for r in heldout]==ids['test'].tolist()
observed=np.array([float(r['observed']) for r in heldout])
predicted=np.array([float(r['predicted']) for r in heldout])
assert np.array_equal(observed,y[ids['test']])
```

Проверим покрытие по соединениям и одновременное покрытие всех соединений каждого тестового каркаса. Нельзя объявлять первое вторым.

```python
queries=report['query_results']
width=(queries[0]['conditional_90_interval'][1]-queries[0]['conditional_90_interval'][0])/2
absolute=abs(predicted-observed);groups=np.array([r['scaffold'] for r in heldout])
point_coverage=float(np.mean(absolute<=width))
group_coverage=float(np.mean([np.all(absolute[groups==g]<=width) for g in np.unique(groups)]))
print({'half_width_pKi':width,'point_coverage':point_coverage,'simultaneous_scaffold_coverage':group_coverage})
audit=read_json('a2a_audit.json')
assert math.isclose(group_coverage,audit['observed_test_scaffold_simultaneous_coverage'],abs_tol=1e-12)
```

Рассчитаем Morgan-сходство запросов только с настоящим training. Murcko-ядро группирует стереоизомеры вместе, а fingerprints сохраняют chirality. Идентичный граф или каркас запроса в train/calibration нарушил бы выбранный эксперимент. Для ациклических структур pipeline использует generic full topology вместо единой пустой scaffold-группы.

```python
from rdkit import Chem,DataStructs
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.Scaffolds import MurckoScaffold
def scaffold(m):
    core=MurckoScaffold.GetScaffoldForMol(m)
    if core.GetNumAtoms():return 'MURCKO:'+Chem.MolToSmiles(core,isomericSmiles=False)
    return 'ACYCLIC_TOPOLOGY:'+Chem.MolToSmiles(MurckoScaffold.MakeScaffoldGeneric(Chem.RemoveHs(m)),isomericSmiles=False)
gen=rdFingerprintGenerator.GetMorganGenerator(radius=2,fpSize=2048,includeChirality=True)
fps=[gen.GetFingerprint(Chem.MolFromSmiles(rows[i]['smiles'])) for i in ids['training']]
nearest=[]
for q in queries:
    mol=Chem.MolFromSmiles(q['smiles']);g=scaffold(mol)
    assert g not in set(split['training']['scaffolds'])|set(split['calibration']['scaffolds'])
    similarities=DataStructs.BulkTanimotoSimilarity(gen.GetFingerprint(mol),fps)
    j=int(np.argmax(similarities));value=float(similarities[j])
    assert math.isclose(value,q['nearest_train_Tanimoto'],abs_tol=1e-12)
    nearest.append({'name':q['name'],'nearest_training_row_id':int(ids['training'][j]),'Tanimoto':value,
                    'predicted_pKi':q['predicted_pKi'],'conditional_90_interval':q['conditional_90_interval'],
                    'decision':'REVIEW: external domain evidence required'})
display(nearest)
fig,ax=plt.subplots()
ax.bar([r['name'] for r in nearest],[r['Tanimoto'] for r in nearest]);ax.set(ylim=(0,1),ylabel='Nearest training Morgan Tanimoto')
publish_plot(fig,'chemical_domain.png')
result={'kind':'calculated','scope':'audit of frozen QSAR predictions and chemical domain','nearest':nearest,
        'point_coverage':point_coverage,'simultaneous_scaffold_coverage':group_coverage,'new_training':'NOT_RUN','prospective_validation':'NOT_RUN'}
```

Максимальное сходство истрадефиллина лишь ≈0.373, кофеина ≈0.340. Универсального доказанного порога здесь нет. Интервал истрадефиллина примерно 4.53–7.53 pKi широк; похожесть не доказывает применимость. Предсказанная активность не является измерением, механизмом, экспозицией или клиническим эффектом. Решение — запросить согласованные независимые assay для релевантного химического ряда; не подбирать порог после просмотра запроса.

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
print(append_record(init_dossier(),'M12-L02','A',result,ROOT,inputs=['practicuum/shared/data/target_qsar/a2a_curated.csv', 'practicuum/shared/data/target_qsar/a2a_dataset.json', 'practicuum/shared/data/target_qsar/a2a_result.json', 'practicuum/shared/data/target_qsar/a2a_split.json', 'practicuum/shared/data/target_qsar/a2a_heldout_predictions.csv', 'practicuum/shared/data/target_qsar/a2a_audit.json', 'practicuum/shared/data/target_qsar/hmgcr_curated.csv', 'practicuum/shared/data/target_qsar/hmgcr_dataset.json', 'practicuum/shared/data/target_qsar/hmgcr_result.json', 'practicuum/shared/data/target_qsar/manifest.json']))
```
