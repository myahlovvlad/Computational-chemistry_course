# Разбор A. Целая молекула: независимые seed и электронноструктурное ранжирование

Для истрадефиллина реально выполнен маршрут: три ETKDGv3 seed × 100 структур → MMFF94s → 300 GFN2-xTB singlepoints в ALPB-water → выбор разнообразных кандидатов → оптимизация и Hessian. Число оптимизируемых кандидатов ограничено 24, окно singlepoint energy 15 kcal/mol, heavy-atom RMSD 0.5 Å. Это конечный поиск, не доказательство глобального минимума.

Полный новый запуск из IDE: `python scripts/setup_xtb.py`, затем `python scripts/run_conformer_research.py --name istradefylline --out practicuum/evidence/MY-new-run`. Используется uv chem; официальный xTB 6.8.0 скачивается с проверкой SHA. Метод/solvent state/точность/ресурсы раскрыты в `practicuum/protocols/conformer-gfn2-alpb.json`. Ниже **повторно анализируем сохранённые результаты**, не имитируя запуск внешней программы.

```python
from pathlib import Path
import sys,json,hashlib,math
import numpy as np
from scipy import stats
from rdkit import Chem
from rdkit.Chem import rdMolAlign
from IPython.display import display
ROOT=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'programm/course.json').is_file())
sys.path.insert(0,str(ROOT/'practicuum/shared'))
from course_support import DATA,workspace,write_json,init_dossier
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=workspace('M06-L01','case');C_DATA=DATA/'conformer_research'
manifest=json.loads((C_DATA/'bundle-manifest.json').read_text(encoding='utf-8'))
for name,digest in manifest['files_sha256'].items():assert hashlib.sha256((C_DATA/name).read_bytes()).hexdigest()==digest,name
def read(state,name):return json.loads((C_DATA/state/name).read_text(encoding='utf-8'))
def publish_plot(fig,name):
    fig.savefig(OUT/name,dpi=150,bbox_inches='tight');display(fig);plt.close(fig)
```

Я хочу выяснить, насколько выбранная геометрия представляет доступные конформации, а не просто получить один красивый рисунок. Для этого важен путь отбора: какие исходные геометрии сгенерированы, какие вычисления сошлись, какие кандидаты оптимизированы и какие структуры остались различными. Счётчики этих этапов помогают заметить, где именно сузился поиск.

При сравнении MMFF и GFN2/ALPB я не сопоставляю абсолютные энергетические нули. Внутри каждого метода вычитаю его собственный минимум, а затем исследую относительные значения и ранги на тех же геометриях. Spearman показывает согласованность порядка в выбранном наборе; это не независимая проверка физических энергий и не основание отказаться от оптимизации на нужном уровне.

```python
state='istradefylline';report=read(state,'result.json');points=read(state,'singlepoint_results.json')
valid=[r for r in points if r['status']=='PASS' and r['MMFF_status']==0]
mmff=np.array([r['MMFF_energy_kcal_mol'] for r in valid]);gfn=np.array([r['energy_hartree'] for r in valid])
# Каждый метод имеет собственный энергетический ноль; сравниваем относительные энергии.
relative_mmff=mmff-mmff.min();relative_gfn=(gfn-gfn.min())*627.5094740631
rho=float(stats.spearmanr(mmff,gfn).statistic)
print({'whole_molecule_singlepoints':report['singlepoints_converged'],'optimization_candidates':report['optimization_candidates'],
       'optimization_converged':report['optimization_converged'],'distinct_optimized_conformers':report['distinct_optimized_conformers'],
       'descriptive_rank_correlation_MMFF_GFN2_ALPB':rho})
fig,ax=plt.subplots()
for seed in sorted({r['seed'] for r in valid}):
    take=np.array([r['seed']==seed for r in valid]);ax.scatter(relative_mmff[take],relative_gfn[take],s=10,alpha=.5,label=str(seed))
ax.set(xlabel='Relative MMFF94s energy / kcal mol^-1',ylabel='Relative GFN2/ALPB singlepoint energy / kcal mol^-1');ax.legend()
publish_plot(fig,'ranking_methods.png')
```

Корреляция описывает два вычислительных ранга. 300 конформеров — не 300 независимых экспериментальных проверок; p-value корреляции не используем как валидацию. MMFF→GFN2/ALPB одновременно меняет Hamiltonian и среду. Чистый solvent effect требует того же электронного метода и той же геометрии в парном gas/solution сравнении.

Проверим разнообразие после оптимизации. Для свободной молекулы допускается оптимальное жёсткое совмещение; полный граф и chirality сохраняются. Рецептор при этом отсутствует. В docking M11 лиганд отдельно от рецептора не выравнивается.

```python
molecules=list(Chem.SDMolSupplier(str(C_DATA/state/'optimized_conformers.sdf'),removeHs=True))
assert all(m is not None for m in molecules)
def conformer_rmsd(reference,pose):
    assert Chem.MolToSmiles(reference,isomericSmiles=True)==Chem.MolToSmiles(pose,isomericSmiles=True)
    maps=pose.GetSubstructMatches(reference,uniquify=False,useChirality=True,maxMatches=10000)
    assert maps and len(maps)<10000
    return min(rdMolAlign.GetAlignmentTransform(pose,reference,atomMap=[(pi,ri) for ri,pi in enumerate(mapping)],reflect=False)[0] for mapping in maps)
matrix=np.array([[conformer_rmsd(a,b) for b in molecules] for a in molecules])
assert np.allclose(matrix,matrix.T,atol=1e-6) and np.max(abs(np.diag(matrix)))<1e-6
fig,ax=plt.subplots();plot=ax.imshow(matrix,cmap='viridis');fig.colorbar(plot,ax=ax,label='Aligned heavy-atom RMSD / A')
ax.set(xlabel='Optimized conformer',ylabel='Optimized conformer');publish_plot(fig,'conformer_diversity.png')
result={'kind':'calculated','scope':'saved whole-molecule seeded conformer reanalysis','singlepoints':len(valid),
        'rank_correlation':rho,'distinct_optimized':len(molecules),'global_minimum_proven':False,
        'experimental_population':'NOT_MEASURED','new_external_calculation':'NOT_RUN'}
```

После оптимизации 19 выбранных структур осталось 10 различных по заданному RMSD. Три низкоэнергетические структуры имеют положительные внутренние частоты в GFN2/ALPB. Это подтверждение в названной модели; DFT имеет отдельные convergence/minimum gates. Для B формы кислота/анион/лактон анализируются раздельно: изменение заряда или состава не является конформацией той же молекулы.

## Независимый запуск под другой ОС

Под Linux выполнен новый полный поиск с теми же исходниками, seed и протоколом: 300 singlepoints, 19 оптимизаций и три гессиана. Одинаковые seed не гарантировали одинаковые MMFF-refined координаты. Полные наборы бассейнов различаются: аудит REVIEW. Поэтому отдельно рассчитаны десять идентичных XYZ-файлов на Windows OpenBLAS и Linux MKL — без новой оптимизации.

```python
reproduction=json.loads((C_DATA/'cross_platform_reproduction.json').read_text())
assert reproduction['fixed_geometry_count']==10
assert reproduction['fixed_geometry_max_abs_energy_difference_Eh']<=reproduction['fixed_geometry_energy_tolerance_Eh']
display({key:reproduction[key] for key in ['fixed_geometry_max_abs_energy_difference_Eh',
        'initial_same_id_geometry_RMSD_A','assignment_within_both_tolerances','complete_basin_set_reproduction']})
result['cross_platform_fixed_geometry_status']=reproduction['status']
result['complete_basin_set_reproduction']=reproduction['complete_basin_set_reproduction']
```

Сравнение энергии одной геометрии проверяет воспроизводимость движка при заданных настройках. Разность энергий несопоставленных бассейнов не является численной ошибкой. Расхождение стартов, отбора и траекторий требует дальнейших раздельных контролей; границы допуска не расширены для получения PASS.

Для сравнения свободных конформаций ориентация и перенос молекулы не должны создавать различие, поэтому RMSD здесь включает совмещение и симметрийные соответствия без отражения. В докинге M11 мы, напротив, сохраним положение относительно рецептора. Сам выбор измерителя зависит от исследовательского вопроса. После кластеризации я проверяю минимумы, а вопрос полноты поиска оставляю отдельным: ещё один seed может открыть состояние, отсутствующее в текущем наборе.

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
print(append_record(init_dossier(),'M06-L01','A',result,ROOT,inputs=['practicuum/shared/data/conformer_research/'+name for name in manifest['files_sha256']]+['practicuum/shared/data/conformer_research/bundle-manifest.json']))
```
