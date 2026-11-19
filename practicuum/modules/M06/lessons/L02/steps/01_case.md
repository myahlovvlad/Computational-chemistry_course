# Разбор A. Энсамбль, низкие частоты и пределы численного ранга

Один минимум не определяет распределение конформеров. Для трёх Hessian-проверенных структур истрадефиллина сравним restricted weights по electronic+ALPB energies и native model free-energy values. Полная функция распределения по неизвестным состояниям и экспериментальные populations отсюда не следуют.

Термодинамическая формула w_i∝g_i exp(−ΔG_i/RT) требует свободных энергий, degeneracy и полноты состояний. Здесь degeneracy не установлена, набор ограничен тремя конформерами, а native thermochemistry использует собственную coupled RRHO/low-mode модель xTB при 298.15 K. Её значения сохраняются как model-dependent diagnostic, не как проверенная solution free energy.

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
OUT=workspace('M06-L02','case');C_DATA=DATA/'conformer_research'
manifest=json.loads((C_DATA/'bundle-manifest.json').read_text(encoding='utf-8'))
for name,digest in manifest['files_sha256'].items():assert hashlib.sha256((C_DATA/name).read_bytes()).hexdigest()==digest,name
def read(state,name):return json.loads((C_DATA/state/name).read_text(encoding='utf-8'))
def publish_plot(fig,name):
    fig.savefig(OUT/name,dpi=150,bbox_inches='tight');display(fig);plt.close(fig)
```

Из исходных матриц Eh/bohr² заново построим mass-weighted Hessian и удалим переносы/вращения. Функция проекции открыта в shared/conformer_ensemble.py; здесь явно формируются матрица, координаты и массы. Пересчитанные частоты сравниваются со всеми сохранёнными внутренними модами, включая знак.

```python
from conformer_ensemble import projected_frequencies

def reproject_hessian(state,source_id):
    xyz=Chem.MolFromXYZBlock((C_DATA/state/f'geometry_{source_id:04}.xyz').read_text())
    assert xyz is not None
    # В XYZ нет связей; для mass weighting здесь нужны только идентичность атомов и координаты.
    masses=[atom.GetMass() for atom in xyz.GetAtoms()]
    lines=(C_DATA/state/f'hessian_{source_id:04}_Eh_bohr2.txt').read_text().splitlines()
    H=np.fromstring(' '.join(line for line in lines if not line.startswith('$')),sep=' ')
    H=H.reshape(3*xyz.GetNumAtoms(),3*xyz.GetNumAtoms())
    actual=projected_frequencies(H,xyz.GetConformer().GetPositions(),masses)
    saved=read(state,f'hessian_{source_id:04}_projected.json')
    assert np.allclose(actual['frequencies_cm1'],saved['frequencies_cm1'],rtol=1e-10,atol=1e-7)
    return actual

recomputed={h['source_id']:reproject_hessian('istradefylline',h['source_id'])
            for h in read('istradefylline','result.json')['hessian_results']}
assert all(h['minimum_verified'] and h['internal_mode_count']==150 for h in recomputed.values())
display({i:{'lowest_frequency_cm1':h['lowest_frequency_cm1'],'rigid_mode_rank':h['rigid_mode_rank']}
         for i,h in recomputed.items()})
```

```python
state='istradefylline';report=read(state,'result.json');checked=report['hessian_results']
assert all(r['status']=='PASS' and r['minimum_verified'] for r in checked)
ids=[r['source_id'] for r in checked]
native=[read(state,f'hessian_{i:04}_native.json') for i in ids]
E=np.array([r['energy_hartree'] for r in checked]);G=np.array([r['total free energy'] for r in native])
T=298.15;R_kcal=8.31446261815324/4184
def restricted_weights(energy_Eh):
    relative=(energy_Eh-energy_Eh.min())*627.5094740631
    weight=np.exp(-relative/(R_kcal*T))
    return weight/weight.sum()
wE=restricted_weights(E);wG=restricted_weights(G)
display([{'source_id':i,'model_E_relative_kcal_mol':float(e),'model_G_relative_kcal_mol':float(g),
          'restricted_E_weight':float(a),'restricted_native_G_weight':float(b),'lowest_internal_frequency_cm1':r['lowest_frequency_cm1']}
         for i,e,g,a,b,r in zip(ids,(E-E.min())*627.5094740631,(G-G.min())*627.5094740631,wE,wG,checked)])
fig,ax=plt.subplots();x=np.arange(len(ids));ax.bar(x-.18,wE,.36,label='E + ALPB, restricted set');ax.bar(x+.18,wG,.36,label='Native model G, restricted set')
ax.set_xticks(x,[str(i) for i in ids]);ax.set(xlabel='Source conformer ID',ylabel='Restricted model weight');ax.legend(fontsize=8)
publish_plot(fig,'restricted_ensemble_weights.png')
```

Проверим численную устойчивость до физической интерпретации точного порядка. Парные GFN2 calculations при той же геометрии отделяют модельную solvation contribution от gas energy. Более плотная SASA-сетка и вдвое меньший Hessian step проверяют разные численные источники.

```python
audit=read(state,'numerics.json');pairs=audit['paired_fixed_geometry_results']
display(pairs)
order_tight=np.argsort([r['tight_energy_Eh'] for r in pairs]).tolist()
order_dense=np.argsort([r['verytight_energy_Eh'] for r in pairs]).tolist()
print({'grid_order_tight':order_tight,'grid_order_verytight':order_dense,
       'relative_energy_grid_sensitivity_kcal_mol':audit['max_relative_energy_grid_sensitivity_kcal_mol'],
       'Hessian_half_step_max_frequency_change_cm1':audit['Hessian_step_max_frequency_change_cm1'],
       'minimum_sign_stable':audit['minimum_sign_stable']})
result={'kind':'calculated','scope':'restricted saved-ensemble and numerical-sensitivity analysis','conformer_ids':ids,
        'restricted_E_weights':wE.tolist(),'restricted_native_G_weights':wG.tolist(),
        'precise_ordering_accepted':order_tight==order_dense,'complete_population_claim_allowed':False,
        'DFT_validation':'separate and incomplete','new_external_calculation':'NOT_RUN'}
```

Для близкой пары уточнение сетки меняет порядок: точные последние знаки не доказывают предпочтение одного конформера. При этом Hessian frequencies изменились максимум на ≈0.183 cm⁻¹ и положительный знак сохранился. Эти проверки оценивают numerical sensitivity, не все ошибки Hamiltonian/solvent/entropy model. Следующий шаг — дополнительные состояния, low-mode/degeneracy sensitivity, целевые DFT и независимые solution-state данные, например подходящие NMR ограничения.

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
print(append_record(init_dossier(),'M06-L02','A',result,ROOT,inputs=['practicuum/shared/data/conformer_research/'+name for name in manifest['files_sha256']]+['practicuum/shared/data/conformer_research/bundle-manifest.json']))
```
