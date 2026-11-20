# Разбор A. Когда ошибка QSAR действительно помогает выбрать следующий эксперимент

Представим практическое решение: модель предлагает кандидата для следующего измерения связывания с человеческим A2A. Прежде чем опираться на её число, я хочу знать, какую задачу она уже выдержала. Хорошее описание обучающих молекул и перенос на новые каркасы — разные требования. В нашем сохранённом исследовании проверяется второе: предсказывает ли модель pKi на отложенных каркасах лучше простого прогноза без структуры?

Я начну с формулировки измеряемой величины. pKi = −log₁₀(Ki / (1 mol/L)); для Ki в nM это 9 − log₁₀(Ki/nM). Поэтому сравнивать прогнозы надо с тем же endpoint. Подмешивание pIC50 изменило бы смысл задачи: общая логарифмическая шкала сама по себе не делает измерения взаимозаменяемыми.

Здесь заново анализируются сохранённые прогнозы выполненного исследования. Полное обучение вынесено в `scripts/train_target_qsar.py`, где видны курация, разделения, признаки, подбор и calibration. Это позволяет обсуждать выбор метода и проверить его результат без имитации нового многочасового обучения в Notebook.

## 1. Восстановлю, откуда появились строки

В закреплённом снимке ChEMBL CHEMBL251 обработаны 8009 activity records. Правила курации сохраняют human/wild type, confidence 9, type B, точные положительные nM и исключают объявленные validity/duplicate flags. Итог — 4546 структур и 1807 каркасов. Многокомпонентные записи не обессоливаются молча; повторные значения одного изомерного графа агрегируются медианой только при разбросе не более 1 log.

Практический смысл этих правил — заранее определить, какие наблюдения сравниваются. Медиана уменьшает влияние отдельных повторов, но не приводит разные assay к одному эксперименту. Поэтому позже я отдельно ограничу смысл тестовой ошибки.

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

## 2. Спрошу, что модель могла видеть до проверки

В исходном протоколе train, calibration и test разделены до подбора. Разные наборы не содержат общих Murcko-каркасов; каркасы истрадефиллина и кофеина исключены из train и calibration. Такой выбор усложняет задачу по сравнению с произвольным перемешиванием близких аналогов и соответствует заявленному вопросу о новых каркасах.

Подбор выполнен внутри nested схемы outer 5 / inner 3: Ridge на 11 дескрипторах с пятью alpha либо RF с 1000 деревьев на Morgan radius 2, 2048 bits, chirality. Нормирование входит в pipeline. В этом разборе я не перенастраиваю модель после просмотра test; проверяю, выполнены ли сохранённые правила разделения.

Вычислительная проверка ниже должна обнаружить потерянные или повторно использованные индексы, общие каркасы и нарушение порядка тестовых прогнозов. Убедительное название split без такой проверки оставляло бы эти ошибки незамеченными.

```python
rows=read_csv('a2a_curated.csv');split=read_json('a2a_split.json');report=read_json('a2a_result.json')
heldout=read_csv('a2a_heldout_predictions.csv')
y=np.array([float(r['y']) for r in rows])
ids={k:np.array(v['row_ids'],dtype=int) for k,v in split.items()}
assert sorted(np.concatenate(list(ids.values())).tolist())==list(range(len(rows)))
for a,b in [('training','calibration'),('training','test'),('calibration','test')]:
    assert not (set(split[a]['scaffolds']) & set(split[b]['scaffolds']))
assert [int(r['row_id']) for r in heldout]==ids['test'].tolist()
```

Зачем отдельно сопоставлять row_id и значения наблюдений? Предсказания и наблюдения могут иметь одинаковую длину, но относиться к разным строкам. Формула RMSE всё равно вернёт число. Поэтому сначала восстанавливаю соответствие записей, затем разрешаю вычисление метрики. Сортировка двух массивов независимо друг от друга здесь разрушила бы проверяемое соответствие.

```python
observed=np.array([float(r['observed']) for r in heldout])
predicted=np.array([float(r['predicted']) for r in heldout])
assert np.array_equal(observed,y[ids['test']])
```

## 3. Сравню с решением, которому структура вообще не нужна

Если модель сложная, это ещё не означает, что её стоит применять. В качестве baseline я предсказываю всем тестовым молекулам одно число — среднее y только обучающей выборки. Среднее минимизирует сумму квадратов отклонений от постоянного прогноза; поэтому это осмысленная отправная точка для RMSE.

Почему не взять среднее test? Тогда в прогноз заранее попадут ответы, доступность которых мы как раз проверяем. Даже настолько простая операция создаёт утечку. Поэтому test участвует только в сравнении уже заданных прогнозов с наблюдениями.

Для каждой молекулы вычисляю остаток «прогноз минус наблюдение». Знак позволяет увидеть направление ошибки; квадрат усиливает вклад крупных отклонений. RMSE возвращает результат в шкалу pKi, а MAE показывает средний модуль ошибки с иным отношением к крупным отклонениям.

```python
residual=predicted-observed
rmse=float(np.sqrt(np.mean(residual**2)));mae=float(np.mean(abs(residual)))
baseline=float(np.sqrt(np.mean((y[ids['training']].mean()-observed)**2)))
assert math.isclose(rmse,report['sealed_test']['RMSE'],rel_tol=1e-12)
```

RMSE модели получается около 0,745 pKi, baseline — около 1,242. Это поддерживает вывод об улучшении над данным постоянным прогнозом на закреплённом test. Теперь нужно понять устойчивость этой оценки к составу тестового набора и посмотреть, где средняя метрика может скрывать проблему.

## 4. Выберу единицу повторной выборки

Если я буду независимо выбирать молекулы, то могу рассматривать очень близкие аналоги как полностью независимые сведения. В принятой проверке единица bootstrap — целый тестовый каркас. Выбираем столько каркасов, сколько их в test, с возвращением; для каждого выбранного каркаса включаем все его строки. Повторно выбранный каркас входит повторно. Число молекул в отдельной bootstrap-выборке может меняться, поскольку размеры групп различны.

После сборки вычисляется общая RMSE по вошедшим молекулам. Это отличается от среднего отдельных RMSE каркасов: большие группы дают больше строк. Так определяется именно тот оцениваемый показатель, с которым мы работаем. Seed фиксирует псевдослучайную процедуру; 2000 повторов — число расчётных выборок, а не новых независимых экспериментов.

```python
groups=np.array([r['scaffold'] for r in heldout]);unique=np.unique(groups)
rng=np.random.default_rng(20261118);bootstrap=[]
for _ in range(2000):
    chosen=rng.choice(unique,size=len(unique),replace=True)
    sample=np.concatenate([np.flatnonzero(groups==g) for g in chosen])
    bootstrap.append(float(np.sqrt(np.mean(residual[sample]**2))))
ci=np.quantile(bootstrap,[.025,.975])
assert np.allclose(ci,report['sealed_test']['scaffold_bootstrap_RMSE_CI95'],atol=1e-12)
print({'n':len(observed),'RMSE_pKi':rmse,'MAE_pKi':mae,'baseline_RMSE':baseline,'conditional_group_bootstrap_CI95':ci.tolist()})
```

Полученный условный 95%-интервал RMSE около [0,687; 0,804] описывает изменчивость оценки при таком переотборе тестовых каркасов и фиксированных прогнозах. Модель в bootstrap заново не обучается. Интервал не включает всю неопределённость подбора, сдвиг условий assay или перенос во времени и не является интервалом отдельного прогноза для новой молекулы.

Поэтому я не перевожу 0,745 автоматически в гарантированную кратность ошибки Ki конкретного кандидата. Ошибка в логарифмической шкале и распределение ошибок отдельных прогнозов связаны, но одна средняя квадратическая величина не задаёт персональный интервал.

## 5. Посмотрю, какое решение скрывается за метрикой

На левой панели проверяю отклонения от диагонали: есть ли области, где модель систематически недооценивает или переоценивает наблюдения? На правой панели читаю знак и разброс остатка относительно прогноза. Скопление ошибок с одной стороны нуля или изменение разброса заставило бы ограничить область использования и исследовать причину, даже при приемлемой общей RMSE.

Это диагностические вопросы к фактическому графику. Их нельзя заменить фразой «точки расположены достаточно близко», не указав, в какой области и относительно какого критерия. Если график вызывает новое решение о модели, его нужно проверить на данных, которые не использовались для этого решения.

```python
fig,axes=plt.subplots(1,2,figsize=(9,3.5))
axes[0].scatter(observed,predicted,s=7,alpha=.35)
limits=[min(observed.min(),predicted.min()),max(observed.max(),predicted.max())]
axes[0].plot(limits,limits,color='gray');axes[0].set(xlabel='Observed pKi',ylabel='Predicted pKi')
axes[1].axhline(0,color='gray');axes[1].scatter(predicted,residual,s=7,alpha=.35)
axes[1].set(xlabel='Predicted pKi',ylabel='Prediction minus observation')
publish_plot(fig,'sealed_test.png')
result={'kind':'calculated','scope':'reanalysis of saved target-specific QSAR predictions','RMSE_pKi':rmse,'baseline_RMSE_pKi':baseline,'new_training':'NOT_RUN','scientific_review':'NOT_RUN'}
```

Рабочий вывод таков: сохранённая модель улучшает среднюю ошибку на выбранном отложенном наборе, но этого ещё мало для выбора эксперимента по истрадефиллину. Теперь я проверю химическую область применимости и неопределённость именно интересующего кандидата. Новый независимый assay понадобился бы для проверки переноса измеряемого endpoint в новые условия.

Для аторвастатина/HMGCR сначала проверяется другая развилка — хватает ли однородных данных для заранее заданного протокола. Копировать A2A split и объявлять аналогичное качество без этой проверки было бы необоснованно. В B вы сформулируете, когда следует отказаться от обучения и какое расширение данных изменит решение.

В досье сохраняю метрики, происхождение прогнозов и область допустимого вывода. Новое обучение и независимая научная рецензия в этом Notebook остаются NOT_RUN.

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
print(append_record(init_dossier(),'M12-L01','A',result,ROOT,inputs=['practicuum/shared/data/target_qsar/a2a_curated.csv', 'practicuum/shared/data/target_qsar/a2a_dataset.json', 'practicuum/shared/data/target_qsar/a2a_result.json', 'practicuum/shared/data/target_qsar/a2a_split.json', 'practicuum/shared/data/target_qsar/a2a_heldout_predictions.csv', 'practicuum/shared/data/target_qsar/a2a_audit.json', 'practicuum/shared/data/target_qsar/hmgcr_curated.csv', 'practicuum/shared/data/target_qsar/hmgcr_dataset.json', 'practicuum/shared/data/target_qsar/hmgcr_result.json', 'practicuum/shared/data/target_qsar/manifest.json']))
```
