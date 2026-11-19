# Разбор A. Профессиональный target-specific QSAR A2A

Вопрос: предсказывает ли модель pKi человеческого A2A для новых молекулярных каркасов лучше среднего обучающей выборки? Здесь используются реальные данные ChEMBL/EMBL-EBI (CC BY-SA 3.0), а не растворимость ESOL. Endpoint сохраняется: pKi=−log₁₀(Ki / mol L⁻¹). Для nM это 9−log₁₀(Ki/nM). pIC50 не подмешивается.

Источник: полная пагинация по CHEMBL251, 8009 activity records; включаются confidence 9, type B, wild type, точные положительные nM, без validity/duplicate flags. Многокомпонентные записи не обессоливаются молча. Одинаковые изомерные графы агрегируются медианой лишь при разбросе ≤1 log. Получены 4546 структур и 1807 каркасов. Неоднородность условий assay остаётся ограничением.

Профессиональное обучение уже выполнено `scripts/train_target_qsar.py`: outer 5 / inner 3 GroupKFold по Murcko-каркасам; во внутренних циклах выбираются Ridge (11 дескрипторов, пять alpha) или RF (1000 деревьев, Morgan radius 2, 2048 bits, chirality). Нормирование обучается внутри pipeline. Train/calibration/test разделены до подбора; каркасы истрадефиллина и кофеина принудительно исключены из train и calibration. Параметры seed=20261118 и все row IDs сохранены.

В этом Notebook **повторно анализируются сохранённые прогнозы**, новое многочасовое обучение не имитируется. Полный перезапуск выполняется из IDE отдельной командой, в новый каталог: `scripts/environment/.venv-chem/Scripts/python.exe scripts/train_target_qsar.py --dataset practicuum/evidence/20261119-research-A2A-dataset --out practicuum/evidence/NEW-A2A-QSAR`. В Linux используйте `.venv-chem/bin/python`. Исходный код содержит все операции split, featurization, inner selection, refit и calibration.

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
OUT=workspace('M12-L01','case')
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

Восстановим численные метрики по отложенным прогнозам, сохраняя соответствие row_id. Средний baseline обучается только на training. Bootstrap здесь выбирает целые тестовые каркасы с возвращением, сохраняя зависимость соединений внутри группы. Он оценивает выборочную изменчивость тестовых групп, не всю неопределённость модели.

```python
residual=predicted-observed
rmse=float(np.sqrt(np.mean(residual**2)));mae=float(np.mean(abs(residual)))
baseline=float(np.sqrt(np.mean((y[ids['training']].mean()-observed)**2)))
assert math.isclose(rmse,report['sealed_test']['RMSE'],rel_tol=1e-12)
groups=np.array([r['scaffold'] for r in heldout]);unique=np.unique(groups)
rng=np.random.default_rng(20261118);bootstrap=[]
for _ in range(2000):
    chosen=rng.choice(unique,size=len(unique),replace=True)
    sample=np.concatenate([np.flatnonzero(groups==g) for g in chosen])
    bootstrap.append(float(np.sqrt(np.mean(residual[sample]**2))))
ci=np.quantile(bootstrap,[.025,.975])
assert np.allclose(ci,report['sealed_test']['scaffold_bootstrap_RMSE_CI95'],atol=1e-12)
print({'n':len(observed),'RMSE_pKi':rmse,'MAE_pKi':mae,'baseline_RMSE':baseline,'conditional_group_bootstrap_CI95':ci.tolist()})
fig,axes=plt.subplots(1,2,figsize=(9,3.5))
axes[0].scatter(observed,predicted,s=7,alpha=.35)
limits=[min(observed.min(),predicted.min()),max(observed.max(),predicted.max())]
axes[0].plot(limits,limits,color='gray');axes[0].set(xlabel='Observed pKi',ylabel='Predicted pKi')
axes[1].axhline(0,color='gray');axes[1].scatter(predicted,residual,s=7,alpha=.35)
axes[1].set(xlabel='Predicted pKi',ylabel='Prediction minus observation')
publish_plot(fig,'sealed_test.png')
result={'kind':'calculated','scope':'reanalysis of saved target-specific QSAR predictions','RMSE_pKi':rmse,'baseline_RMSE_pKi':baseline,'new_training':'NOT_RUN','scientific_review':'NOT_RUN'}
```

RMSE≈0.745 pKi ниже baseline≈1.242, но pooled-assay holdout не является новым независимым assay. Систематический сдвиг лабораторий и временной перенос не оценены. Хорошая средняя ошибка не подтверждает конкретный прогноз на истрадефиллин; в следующем уроке проверим его химическую область.

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
print(append_record(init_dossier(),'M12-L01','A',result,ROOT,inputs=['practicuum/shared/data/target_qsar/a2a_curated.csv', 'practicuum/shared/data/target_qsar/a2a_dataset.json', 'practicuum/shared/data/target_qsar/a2a_result.json', 'practicuum/shared/data/target_qsar/a2a_split.json', 'practicuum/shared/data/target_qsar/a2a_heldout_predictions.csv', 'practicuum/shared/data/target_qsar/a2a_audit.json', 'practicuum/shared/data/target_qsar/hmgcr_curated.csv', 'practicuum/shared/data/target_qsar/hmgcr_dataset.json', 'practicuum/shared/data/target_qsar/hmgcr_result.json', 'practicuum/shared/data/target_qsar/manifest.json']))
```
