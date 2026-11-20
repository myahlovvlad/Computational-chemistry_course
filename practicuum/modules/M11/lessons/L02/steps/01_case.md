# Разбор A. Можно ли доверять первой позе молекулярного докинга?

Представьте следующий этап исследования. Вы хотите рассмотреть, как новая молекула может взаимодействовать с белком, и выбрать геометрию комплекса для дальнейшего анализа. Экспериментальной структуры именно этого комплекса пока нет. Программа докинга предлагает несколько расположений молекулы и упорядочивает их по приближённой оценке. С какого из них начинать?

Первое место выглядит естественным выбором. Однако если эта геометрия неудачна, последующий разбор контактов с остатками белка и выбор стартовой структуры для моделирования будут опираться на неверное расположение молекулы. Поэтому перед таким применением полезно проверить протокол на комплексе с известной структурной моделью. Именно ради этого решения нам нужны сегодняшние расчёты.

Договоримся о словах. **Лиганд** — небольшая молекула, положение которой мы исследуем; здесь это истрадефиллин, наш основной объект A. **Рецептор A2A** — белковая мишень. **Поза** — положение и конформация лиганда относительно рецептора. **Score** — значение функции оценки докинга, по которому программа упорядочивает позы. Для используемого здесь Vina меньший score стоит раньше; это оценка модели, а не измеренная аффинность.

В предыдущем уроке мы проверяли структурный вход. Теперь проверим, что протокол делает с допущенным входом. Будущий пользователь новой молекулы сможет выбрать первую позу по score, но не сможет выбрать позу, наиболее похожую на неизвестный экспериментальный ответ.

## Сначала сформулируем задачу, которую можно проверить

Для комплекса истрадефиллин–A2A доступна [PDB 8RW0](https://www.rcsb.org/structure/8RW0): рентгеноструктурная модель с разрешением 1,94 Å. Это экспериментально обоснованная модель для сравнения, с собственной неопределённостью. Её разрешение не является порогом RMSD и не задаёт автоматически допуск нашего протокола.

Мы используем известную позу как контрольный ответ при redocking — повторном поиске положения того же лиганда. Практический вопрос становится конкретным: **воспроизводит ли первая поза достаточно близкое положение, чтобы принять этот протокол для выбора top-1 в данной системе?** Это ещё не проверка способности предсказывать все новые комплексы.

Разобьём вопрос на две проверяемые части:

| Вопрос | Что сравниваем | Зачем это нужно |
|---|---|---|
| Поиск вообще достиг близкой геометрии? | Лучшую по сходству с эталоном позу среди сохранённых | Отличить отсутствие близких вариантов от их неудачного выбора |
| Программа поставила близкий вариант первым? | Первую позу по score | Проверить правило, доступное без знания экспериментального ответа |

Я не объединяю эти вопросы заранее. Ответы определят разные следующие действия: исследовать генерацию поз, подготовку системы или механизм выбора среди уже найденных вариантов.

## Как получим измеримые показатели

Пусть j нумерует сохранённые позы одного поиска в порядке score, а d_j — их отклонения от эталона. Тогда:

$$
d_{\mathrm{top1}}=d_1,\qquad
d_{\mathrm{best}}=\min_{1\le j\le K}d_j.
$$

**Top-1 RMSD** измеряет отклонение первой позы по score. **Best sampled RMSD** измеряет минимальное отклонение среди K сохранённых поз. Best sampled использует известный ответ и служит диагностикой поиска; заменить им top-1 при оценке рабочего выбора нельзя.

До анализа принято правило этого протокола: top-1 RMSD строго меньше δ=2 Å минимум в восьми из девяти поисков. Если d=2 Å, строгий порог не пройден. Для каждого поиска i введём индикатор I_i и наблюдаемую долю R_top1:

$$
I_i=\mathbf{1}(d_{\mathrm{top1},i}<\delta),\qquad
R_{\mathrm{top1}}=\frac{1}{9}\sum_{i=1}^{9}I_i,\qquad
\mathrm{accept}\ \Longleftrightarrow\ \sum_{i=1}^{9}I_i\ge8.
$$

Аналогично R_sampled считаем по d_best. Эти доли описывают девять вычислительных поисков одного комплекса; они не являются вероятностями успеха на произвольной новой мишени.

Мы заново анализируем девять сохранённых Vina-поисков: три стартовые геометрии ETKDG/MMFF (13, 37, 73) × три search seed (101, 202, 303). Запрошены до 20 поз; фактическое число читается из каждого SDF и может быть меньше. Остальные условия исходного запуска: exhaustiveness=64, spacing=0,375 Å, неподвижный рецептор. Полный новый Vina-поиск в этом Notebook не запускается.

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

## Проверим, можно ли доверять самому сравнению

Хеши закрепляют версии файлов, но не доказывают, что координаты принадлежат общей системе. Поэтому отдельно сопоставим исходные атомы кармана и подготовленный receptor.pdbqt по цепи, номеру остатка и имени атома. Проверим отсутствие пропавших атомов, их смещения и совпадение файла рецептора с SHA, указанным во всех поисках.

Радиус кармана 6 Å и допуск смещения исходных атомов 0,05 Å относятся к данному аудиту подготовки. Они отличаются от порога 2 Å для позы. Эта проверка подтверждает сохранение исходных координат кармана; она не удостоверяет все предположения подготовки, например выбор протонных состояний или исключение вод.

```python
# Проверяем координаты оригинального кармана и файл рецептора, реально указанный в запусках.
receptor_path=ROOT/'practicuum/evidence/20261118-A2A-target-preparation-repair-audited/receptor.pdbqt'
def atom_coordinates(path):
    atoms={}
    for line in path.read_text().splitlines():
        if not line.startswith(('ATOM  ','HETATM')):continue
        key=(line[21:22].strip(),line[22:27].strip(),line[12:16].strip())
        assert key not in atoms, 'Неоднозначный ключ атома'
        atoms[key]=np.array([float(line[30:38]),float(line[38:46]),float(line[46:54])])
    return atoms
original=atom_coordinates(D/'a2a_protein_crystal.pdb')
prepared=atom_coordinates(receptor_path)
ligand_xyz=Chem.RemoveHs(Chem.SDMolSupplier(str(D/'a2a_crystal_reference.sdf'),removeHs=False)[0]).GetConformer().GetPositions()
pocket={k:v for k,v in original.items() if np.min(np.linalg.norm(ligand_xyz-v,axis=1))<=6.0}
assert pocket and set(pocket)<=set(prepared)
max_shift=max(float(np.linalg.norm(v-prepared[k])) for k,v in pocket.items())
assert max_shift<=0.05
receptor_sha=hashlib.sha256(receptor_path.read_bytes()).hexdigest()
source_report=read_json('a2a_redocking.json')
assert all(run['receptor_sha256']==receptor_sha for run in source_report['runs'])
display({'original_pocket_atoms_checked':len(pocket),'max_shift_A':max_shift,
         'same_saved_receptor_for_all_runs':True})
```

### Переведём пространственное отклонение в формулу

Сначала проверим сопоставимость молекулярных графов, затем установим соответствия тяжёлых атомов. При N атомах и допустимом соответствии π:

$$
d(\pi)=\sqrt{\frac{1}{N}\sum_{a=1}^{N}
\left\|\mathbf r_{\pi(a)}^{\mathrm{pose}}-\mathbf r_a^{\mathrm{ref}}\right\|^2},
\qquad d_{\mathrm{RMSD}}=\min_{\pi\in\mathcal M}d(\pi).
$$

Множество M содержит допустимые полные графовые соответствия с сохранением доступной стереоинформации. Это защищает сравнение от перестановки симметрийно эквивалентных атомов. Дополнительное вращение и перенос самого лиганда не выполняются: нам нужно сохранить его положение относительно белка.

В NumPy каждая строка разности координат относится к одному атому. `sum(..., axis=1)` даёт квадрат расстояния по трём координатам, `mean` усредняет по атомам, `sqrt` возвращает Å. Без корня получились бы Å² — другая величина.

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

Проверим измеритель вмешательством с известным ответом: сдвинем весь эталон на 1 Å вдоль x. Ожидаем ровно 1 Å. Значение около нуля означало бы, что сравнение устраняет интересующее нас положение лиганда. Только после этого контроля продолжим анализ поисков.

```python
reference=Chem.SDMolSupplier(str(D/'a2a_crystal_reference.sdf'),removeHs=False)[0]
shifted=Chem.Mol(reference);conf=shifted.GetConformer()
for i in range(shifted.GetNumAtoms()):
    p=conf.GetAtomPosition(i);conf.SetAtomPosition(i,(p.x+1,p.y,p.z))
assert math.isclose(receptor_frame_rmsd(reference,shifted),1.,abs_tol=1e-10)
```

### Подтвердим, какая поза действительно стоит первой

Название `poses[0]` не доказывает порядок по score. Прочитаем свойство `Vina_score_kcal_mol` каждого SDF, сопоставим его с сохранённым в отчёте вектором энергий и проверим неубывание. Так мы проверяем сохранность заявленного порядка при экспорте. Равные score могут оставлять неоднозначность порядка внутри группы; наш критерий относится к фактически первой сохранённой позе.

Затем вычислим RMSD всех поз. Допуск 0,001 Å при сверке с исходным отчётом учитывает запись координат в SDF. Мы не используем этот технический допуск, чтобы расширить геометрический порог 2 Å.

```python
report=read_json('a2a_redocking.json');records=[]
for run in report['runs']:
    label=f"start-{run['starting_geometry_seed']}-search-{run['search_seed']}"
    poses=list(Chem.SDMolSupplier(str(D/(label+'.sdf')),removeHs=False))
    assert poses and all(p is not None for p in poses)
    scores=np.array([float(p.GetProp('Vina_score_kcal_mol')) for p in poses])
    stored_scores=np.array(run['Vina_energy_columns'])[:,0]
    assert len(scores)==len(stored_scores)
    assert np.allclose(scores,stored_scores,atol=1e-9,rtol=0)
    assert np.all(np.diff(scores)>=-1e-9), 'Порядок SDF не соответствует возрастанию Vina score'
    values=np.array([receptor_frame_rmsd(reference,p) for p in poses])
    # SDF output rounds coordinates; allow its sub-milliangstrom serialization error.
    assert np.allclose(values,run['all_RMSD_A'],atol=.001,rtol=0)
    native_ranks=np.flatnonzero(values<2)+1
    records.append({'label':label,'top1_RMSD_A':float(values[0]),'best_sampled_RMSD_A':float(values.min()),
                    'first_native_like_rank':None if len(native_ranks)==0 else int(native_ranks[0]),
                    'top1_Vina_score_kcal_mol':run['Vina_energy_columns'][0][0]})
```

## Сначала посмотрим, чего достиг поиск

Матрица 3×3 сохраняет устройство опыта: строки — стартовые геометрии, столбцы — search seed. Сначала покажем только best sampled RMSD. Перед следующим выводом сформулируйте, можно ли по этой матрице уже принять правило выбора первой позы, и объясните ответ.

```python
starts=sorted({r['starting_geometry_seed'] for r in report['runs']})
seeds=sorted({r['search_seed'] for r in report['runs']})
assert len(starts)==len(seeds)==3 and len(records)==9
by_label={r['label']:r for r in records}
assert len(by_label)==9
def rmsd_grid(field):
    return np.array([[by_label[f'start-{a}-search-{b}'][field] for b in seeds] for a in starts])
def show_grid(field,title,name):
    values=rmsd_grid(field)
    fig,ax=plt.subplots(figsize=(6,4))
    image=ax.imshow(values,vmin=0,vmax=max(r['top1_RMSD_A'] for r in records),cmap='viridis')
    ax.set_xticks(range(3),seeds);ax.set_yticks(range(3),starts)
    ax.set(xlabel='Vina search seed',ylabel='Starting-geometry seed',title=title)
    for i in range(3):
        for j in range(3):ax.text(j,i,f'{values[i,j]:.2f} Å',ha='center',va='center',color='white' if values[i,j]<5 else 'black')
    fig.colorbar(image,ax=ax,label='Heavy-atom receptor-frame RMSD / Å')
    publish_plot(fig,name)
show_grid('best_sampled_RMSD_A','Поиск: ближайшая к эталону сохранённая поза','sampling_matrix.png')
```

Теперь откроем top-1. Сравнивать нужно те же комбинации начальных условий. Если близкий вариант есть, но первая поза далека, этот поиск даёт свидетельство разрыва между обнаружением варианта и его выбором.

```python
show_grid('top1_RMSD_A','Ранжирование: первая поза по score','top1_matrix.png')
```

Сосчитайте успехи самостоятельно по обеим матрицам, затем сверьте с программой:

```python
top1=np.array([r['top1_RMSD_A'] for r in records]);best=np.array([r['best_sampled_RMSD_A'] for r in records])
recovery=int(np.sum(top1<2));sampling=int(np.sum(best<2))
print({'top1_recovery':f'{recovery}/9','sampled_native_like':f'{sampling}/9','ranking_criterion_met':recovery>=8})
```

Фактические результаты — R_sampled=9/9 и R_top1=0/9. Следовательно, для сохранённых поз всех девяти поисков близкий вариант найден, но первая поза не проходит порог ни разу. Критерий приёмки ≥8/9 не выполнен.

Это наблюдение пока не выделяет единственную причину. Scoring, подготовка системы, протонные состояния и приближения рецептора действовали совместно; их причинное влияние надо проверять контролируемым сравнением вариантов. Следующий график сохраняет результаты отдельных поисков и объявленный порог, чтобы среднее не скрывало структуру наблюдений.

```python
fig,ax=plt.subplots(figsize=(9,4));ax.plot(top1,'o',label='Top-ranked pose');ax.plot(best,'s',label='Best sampled crystal RMSD')
ax.axhline(2,color='gray',linestyle='--');ax.set(xlabel='Independent starting-geometry / search-seed combination',ylabel='Receptor-frame heavy-atom RMSD / A');ax.legend()
publish_plot(fig,'sampling_vs_ranking.png')
result={'kind':'calculated','scope':'saved SDF pose audit, no new docking','top1_within_2A':recovery,
        'best_sampled_within_2A':sampling,'ranking_status':'PASS' if recovery>=8 else 'FAIL',
        'mean_top1_RMSD_A':float(top1.mean()),'binding_affinity':'NOT_MEASURED','prospective_validation':'NOT_RUN'}
```

## Переведём результат в исследовательское решение

| Наблюдение после проверок входа и измерителя | Допустимая интерпретация | Следующее действие |
|---|---|---|
| Сопоставимость координат или порядок поз не подтверждены | Показатели ещё нельзя интерпретировать как проверку данного правила выбора | Исправить вход/экспорт и повторить проверку |
| Best sampled ≥2 Å | В сохранённом наборе нет близкой позы | Исследовать поиск, подготовку и ограничения сохранения поз |
| Best sampled <2 Å, top-1 ≥2 Å | Близкая поза есть, первая её не воспроизводит | Диагностировать ранжирование в условиях данной подготовки |
| Top-1 <2 Å | Этот поиск прошёл порог | Проверить общий критерий всех поисков и независимую переносимость |

В нашем наборе обоснованное решение — **не принимать данный протокол для автоматического выбора top-1 в системе истрадефиллин–A2A**. Это решение относится к конкретной подготовке и критерию; оно не утверждает, что докинг вообще бесполезен.

Сделаем решение машиночитаемым и сохраним основание, а не только итоговое слово FAIL:

```python
def interpret_run(top1_rmsd,best_rmsd,delta=2.0):
    assert math.isfinite(top1_rmsd) and math.isfinite(best_rmsd)
    assert 0<=best_rmsd<=top1_rmsd+1e-9
    if best_rmsd>=delta:
        return 'Близкая поза в сохранённом наборе не найдена; проверить поиск и подготовку'
    if top1_rmsd>=delta:
        return 'Близкая поза найдена, но top-1 её не выбрал; протокол требует диагностики'
    return 'Top-1 прошёл геометрический порог в этом поиске; проверить общий критерий'
decisions=[{**r,'interpretation':interpret_run(r['top1_RMSD_A'],r['best_sampled_RMSD_A'])} for r in records]
display(decisions)
result['input_checks']={'pocket_atoms':len(pocket),'max_original_pocket_shift_A':max_shift,
                        'receptor_hashes_match':True,'SDF_score_order_checked':True}
result['decision']='Не принимать данный протокол для автоматического выбора top-1 в этой системе'
result['causal_attribution']='NOT_ISOLATED: scoring, preparation and export assumptions require controlled comparisons'
```

Прежде чем обсуждать улучшение, предложите одно контролируемое изменение и наблюдение, которое позволит оценить его эффект. Зафиксируйте критерий до нового поиска. После выбора варианта потребуется другой структурный комплекс: тот же известный ответ, использованный для настройки, не станет независимой проверкой.

В линии B — аторвастатин/HMGCR — первая развилка возникает ещё до поиска: пригоден ли подготовленный карман? Переносим порядок проверки и принятия решения. Успешный контроль A2A не удостоверил бы HMGCR, а получение score на неподходящем входе не устранило бы его проблему.

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
print(append_record(init_dossier(),'M11-L02','A',result,ROOT,inputs=['practicuum/shared/data/target_docking/a2a_crystal_reference.sdf', 'practicuum/shared/data/target_docking/a2a_preparation.json', 'practicuum/shared/data/target_docking/a2a_protein_crystal.pdb', 'practicuum/shared/data/target_docking/a2a_protocol.json', 'practicuum/shared/data/target_docking/a2a_redocking.json', 'practicuum/shared/data/target_docking/hmgcr_crystal_reference.sdf', 'practicuum/shared/data/target_docking/hmgcr_failure.json', 'practicuum/shared/data/target_docking/hmgcr_gap_audit.json', 'practicuum/shared/data/target_docking/hmgcr_protein_crystal.pdb', 'practicuum/shared/data/target_docking/hmgcr_repair_audit.json', 'practicuum/shared/data/target_docking/manifest.json', 'practicuum/shared/data/target_docking/start-13-search-101.sdf', 'practicuum/shared/data/target_docking/start-13-search-202.sdf', 'practicuum/shared/data/target_docking/start-13-search-303.sdf', 'practicuum/shared/data/target_docking/start-37-search-101.sdf', 'practicuum/shared/data/target_docking/start-37-search-202.sdf', 'practicuum/shared/data/target_docking/start-37-search-303.sdf', 'practicuum/shared/data/target_docking/start-73-search-101.sdf', 'practicuum/shared/data/target_docking/start-73-search-202.sdf', 'practicuum/shared/data/target_docking/start-73-search-303.sdf']))
```
