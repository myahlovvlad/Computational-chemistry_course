# Разбор A. Поиск нашёл близкую позу — можно ли доверять первой в списке?

Мне нужно решить, пригоден ли протокол докинга для следующей задачи. У нас есть редкая для проверки возможность: для истрадефиллина известна кристаллическая поза в A2A, PDB 8RW0. Значит, можно сопоставить предсказанное положение с экспериментальной структурной моделью и проверить заранее выбранный критерий.

Начну с различия двух решений. Первое — смог ли поиск вообще попасть в область близкой позы. Второе — выбрала ли система оценки эту позу как лучшую. Для нового комплекса правильная поза заранее неизвестна, поэтому в рабочем применении нельзя просмотреть результаты и выбрать тот, который ближе к известному ответу. Именно поэтому меня интересует первая поза по score, а лучший RMSD во всём наборе остаётся отдельной диагностикой поиска.

Мы повторно анализируем сохранённые SDF девяти выполненных Vina-поисков: три независимые стартовые геометрии ETKDG/MMFF (13/37/73) × три search seed (101/202/303). В исходном протоколе exhaustiveness=64, 20 poses, spacing=0,375 Å, rigid receptor. Новый поиск здесь не запускается; его исходник — `scripts/run_target_redocking.py`.

Критерий объявлен до этого анализа: top-1 RMSD < 2 Å минимум в восьми из девяти поисков. Порог — правило приёмки данного протокола, а не универсальная граница качества любой задачи докинга. Сначала проверю входы и измеритель RMSD, затем применю одно и то же правило ко всем девяти результатам.

## 1. Проверю, какие координаты сравниваю

Отпечатки файлов закрепляют версию входа. Это важно: если сравнивать позы одной подготовки с эталоном в другой системе координат, численный RMSD будет отвечать на посторонний вопрос. После проверки manifest я рассматриваю набор как конкретный сохранённый экспериментальный протокол вычисления.

```python
from pathlib import Path
import sys,json,hashlib,math
import numpy as np
from rdkit import Chem
from IPython.display import display
ROOT=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'programm/course.json').is_file())
sys.path.insert(0,str(ROOT/'practicuum/shared'))
from course_support import DATA,workspace,write_json,init_dossier
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=workspace('M11-L02','case');D=DATA/'target_docking'
manifest=json.loads((D/'manifest.json').read_text(encoding='utf-8'))
for name,digest in manifest['files_sha256'].items():
    assert hashlib.sha256((D/name).read_bytes()).hexdigest()==digest,name
def read_json(name):return json.loads((D/name).read_text(encoding='utf-8'))
def publish_plot(fig,name):
    fig.savefig(OUT/name,dpi=150,bbox_inches='tight');display(fig);plt.close(fig)
```

Теперь нужно определить сам измеритель. Для N тяжёлых атомов считаем квадрат расстояния каждой соответствующей пары, усредняем по атомам и извлекаем корень:

\[
\operatorname{RMSD}=\sqrt{\frac{1}{N}\sum_i\lVert\mathbf r_i^{pose}-\mathbf r_i^{ref}\rVert^2}.
\]

Простое сравнение атома с индексом i в двух SDF ненадёжно: индексы могут измениться при записи. Я сначала требую совпадения выбранного графового представления со стереоинформацией, затем перебираю допустимые полные соответствия и беру минимальный RMSD. Так симметрийное перенумерование не создаёт ложную геометрическую ошибку. Ограничение числа соответствий проверяется, чтобы незаметно не принять усечённый перебор.

Почему не совмещаю сам лиганд вращением и переносом? Для этой задачи положение относительно рецептора и есть часть ответа. Две одинаковые конформации в разных местах кармана должны различаться. Совмещение лиганда измеряло бы другой аспект — сходство его собственной геометрии после удаления положения в комплексе.

```python
def receptor_frame_rmsd(reference, pose):
    if reference is None or pose is None:
        raise ValueError('Не прочитана молекула из SDF')
    reference = Chem.RemoveHs(reference)
    pose = Chem.RemoveHs(pose)
    # Сначала проверяем сравнимость графов и доступную стереоинформацию.
    assert Chem.MolToSmiles(reference, isomericSmiles=True) == Chem.MolToSmiles(pose, isomericSmiles=True)
    mappings = pose.GetSubstructMatches(reference, uniquify=False, useChirality=True, maxMatches=10000)
    assert mappings and len(mappings) < 10000
    a = np.array(reference.GetConformer().GetPositions())
    b = np.array(pose.GetConformer().GetPositions())
    rmsd_values = []
    for mapping in mappings:
        displacement = b[list(mapping)] - a
        squared_per_atom = np.sum(displacement ** 2, axis=1)
        rmsd_values.append(float(np.sqrt(np.mean(squared_per_atom))))
    return min(rmsd_values)
```

В строке `axis=1` суммируются три координатные компоненты для каждого атома. Затем `mean` усредняет по атомам, а `sqrt` возвращает расстояние в Å. Если забыть последний корень, получится величина в Å²; если усреднить сразу все координатные компоненты, формула будет иметь иной масштаб. Размерности и оси массива помогают проверить алгоритм до просмотра итогового числа.

## 2. Проверю измеритель на известном вмешательстве

Я сдвигаю все атомы эталона на 1 Å по x, сохраняя его внутреннюю геометрию. Такой контроль должен дать RMSD 1 Å в неподвижной системе рецептора. Если получилось около нуля, в процедуре могло появиться совмещение лиганда, которое стирает интересующее нас положение. Прежде чем доверять девяти поискам, проверяю это требование на конструкции с известным ответом.

```python
reference=Chem.SDMolSupplier(str(D/'a2a_crystal_reference.sdf'),removeHs=False)[0]
shifted=Chem.Mol(reference);conf=shifted.GetConformer()
for i in range(shifted.GetNumAtoms()):
    p=conf.GetAtomPosition(i);conf.SetAtomPosition(i,(p.x+1,p.y,p.z))
assert math.isclose(receptor_frame_rmsd(reference,shifted),1.,abs_tol=1e-10)
```

## 3. Сохраню два ответа для каждого поиска

Теперь последовательно читаю поиски и заново вычисляю RMSD каждой позы. Сверка с сохранённым отчётом использует допуск 0,001 Å для координат, сериализованных в SDF. Этот технический допуск отличается от порога приёмки позы 2 Å: они контролируют разные вещи.

Для каждого поиска сохраняю RMSD первой позы, минимальный RMSD среди всех найденных поз и ранг первого близкого результата. Иначе удачная геометрия в конце списка могла бы скрыть неудачу ранжирования. Мне важна судьба каждого поиска, поэтому я сохраняю комбинацию начальной геометрии и search seed вместе с результатом.

```python
report=read_json('a2a_redocking.json');records=[]
for run in report['runs']:
    label=f"start-{run['starting_geometry_seed']}-search-{run['search_seed']}"
    poses=list(Chem.SDMolSupplier(str(D/(label+'.sdf')),removeHs=False))
    values=np.array([receptor_frame_rmsd(reference,p) for p in poses])
    # SDF output rounds coordinates; allow its sub-milliangstrom serialization error.
    assert np.allclose(values,run['all_RMSD_A'],atol=.001,rtol=0)
    native_ranks=np.flatnonzero(values<2)+1
    records.append({'label':label,'top1_RMSD_A':float(values[0]),'best_sampled_RMSD_A':float(values.min()),
                    'first_native_like_rank':None if len(native_ranks)==0 else int(native_ranks[0]),
                    'top1_Vina_score_kcal_mol':run['Vina_energy_columns'][0][0]})
display(records)
```

Когда читаете таблицу, начните с первой строки: совпадают ли top-1 и best sampled? Если близкая поза существует, но находится ниже первой, поиск достиг нужной области, а ранжирование не выбрало её. Если близкой позы нет вовсе, по одному этому результату мы ещё не можем свести проблему к scoring: нужно исследовать и генерацию поз, и подготовку входа.

## 4. Применю критерий ко всему набору

Я не выбираю один удачный seed после просмотра таблицы. Считаю два показателя на одном и том же наборе девяти запусков, после чего проверяю заранее заданные восемь успехов top-1.

```python
top1=np.array([r['top1_RMSD_A'] for r in records]);best=np.array([r['best_sampled_RMSD_A'] for r in records])
recovery=int(np.sum(top1<2));sampling=int(np.sum(best<2))
print({'top1_recovery':f'{recovery}/9','sampled_native_like':f'{sampling}/9','ranking_criterion_met':recovery>=8})
```

Фактический результат — top-1 recovery 0/9 и наличие хотя бы одной позы с RMSD < 2 Å в 9/9 поисков. Следовательно, критерий ранжирования на этом наборе не пройден. Увеличить только число поисков теперь не является достаточным обоснованием исправления: в текущих результатах близкие позы уже присутствуют, но первая позиция выбирается иначе.

На графике ниже я разделяю две серии и оставляю видимой линию 2 Å. Смотрите не только на среднее: каждая точка относится к определённому поиску. Среднее top-1 около 9,559 Å не должно скрывать сам факт отсутствия успешного top-1 во всех девяти результатах.

```python
fig,ax=plt.subplots(figsize=(9,4));ax.plot(top1,'o',label='Top-ranked pose');ax.plot(best,'s',label='Best sampled crystal RMSD')
ax.axhline(2,color='gray',linestyle='--');ax.set(xlabel='Independent starting-geometry / search-seed combination',ylabel='Receptor-frame heavy-atom RMSD / A');ax.legend()
publish_plot(fig,'sampling_vs_ranking.png')
result={'kind':'calculated','scope':'saved SDF pose audit, no new docking','top1_within_2A':recovery,
        'best_sampled_within_2A':sampling,'ranking_status':'PASS' if recovery>=8 else 'FAIL',
        'mean_top1_RMSD_A':float(top1.mean()),'binding_affinity':'NOT_MEASURED','prospective_validation':'NOT_RUN'}
```

## 5. Приму решение о следующем исследовании

Рабочее решение: этот протокол ещё не принимается для выбора позы истрадефиллина по первому score. Сохранённые координаты остаются полезными для диагностики. Я бы заранее оформил следующий набор сравнений подготовки: протонирование, гидратация и модель рецептора, затем проверил выбранный вариант на отдельном структурном комплексе. Подбирать настройки до красивого RMSD на единственном известном ответе недостаточно для независимой проверки.

Перенос на аторвастатин/HMGCR начинается ещё раньше — с допуска подготовленного входа. Если подготовка меняет карман за пределами объявленных gates, следующий обоснованный шаг — разбор этой причины. Получение score на неподходящем входе не решит задачу выбора позы.

В досье сохраняю значения обоих показателей, критерий отказа и план следующей проверки. Девять поисков этого набора не устанавливают универсальную частоту успеха протокола; Vina score также не становится измеренной аффинностью.

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
print(append_record(init_dossier(),'M11-L02','A',result,ROOT,inputs=['practicuum/shared/data/target_docking/a2a_crystal_reference.sdf', 'practicuum/shared/data/target_docking/a2a_preparation.json', 'practicuum/shared/data/target_docking/a2a_protein_crystal.pdb', 'practicuum/shared/data/target_docking/a2a_protocol.json', 'practicuum/shared/data/target_docking/a2a_redocking.json', 'practicuum/shared/data/target_docking/hmgcr_crystal_reference.sdf', 'practicuum/shared/data/target_docking/hmgcr_failure.json', 'practicuum/shared/data/target_docking/hmgcr_gap_audit.json', 'practicuum/shared/data/target_docking/hmgcr_protein_crystal.pdb', 'practicuum/shared/data/target_docking/hmgcr_repair_audit.json', 'practicuum/shared/data/target_docking/manifest.json', 'practicuum/shared/data/target_docking/start-13-search-101.sdf', 'practicuum/shared/data/target_docking/start-13-search-202.sdf', 'practicuum/shared/data/target_docking/start-13-search-303.sdf', 'practicuum/shared/data/target_docking/start-37-search-101.sdf', 'practicuum/shared/data/target_docking/start-37-search-202.sdf', 'practicuum/shared/data/target_docking/start-37-search-303.sdf', 'practicuum/shared/data/target_docking/start-73-search-101.sdf', 'practicuum/shared/data/target_docking/start-73-search-202.sdf', 'practicuum/shared/data/target_docking/start-73-search-303.sdf']))
```
