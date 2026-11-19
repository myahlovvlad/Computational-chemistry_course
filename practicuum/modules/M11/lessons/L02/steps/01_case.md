# Разбор A. Redocking истрадефиллина: sampling и ранжирование

Выполнены девять реальных Vina-поисков в 8RW0: три независимые ETKDG/MMFF стартовые геометрии (13/37/73) × три search seed (101/202/303), exhaustiveness=64, 20 poses, grid spacing .375 Å, rigid receptor. Полный Linux-расчёт и версии сохранены в evidence; здесь заново вычисляем RMSD сохранённых SDF, **не объявляя это новым docking**. [AutoDock Vina](https://vina.scripps.edu/) и исходный `scripts/run_target_redocking.py` раскрывают ресурсный маршрут.

Предобъявленный критерий: top-1 RMSD<2 Å минимум в 8/9 поисков. Отдельно измеряется, найдена ли хотя бы одна поза <2 Å. Выбор лучшей по кристаллическому RMSD после поиска оценивает sampling, а не scoring ranking.

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

RMSD считаем в неподвижной системе рецептора, минимизируя по допустимым полным графовым соответствиям с chirality. Канонический изомерный SMILES защищает от сравнения иной формы; атомное перенумерование не должно менять результат. Координатное выравнивание самого лиганда уничтожило бы информацию о его положении в кармане.

```python
def receptor_frame_rmsd(reference,pose):
    reference=Chem.RemoveHs(reference);pose=Chem.RemoveHs(pose)
    assert Chem.MolToSmiles(reference,isomericSmiles=True)==Chem.MolToSmiles(pose,isomericSmiles=True)
    mappings=pose.GetSubstructMatches(reference,uniquify=False,useChirality=True,maxMatches=10000)
    assert mappings and len(mappings)<10000
    a=np.array(reference.GetConformer().GetPositions());b=np.array(pose.GetConformer().GetPositions())
    return min(float(np.sqrt(np.mean(np.sum((b[list(mapping)]-a)**2,axis=1)))) for mapping in mappings)
reference=Chem.SDMolSupplier(str(D/'a2a_crystal_reference.sdf'),removeHs=False)[0]
shifted=Chem.Mol(reference);conf=shifted.GetConformer()
for i in range(shifted.GetNumAtoms()):
    p=conf.GetAtomPosition(i);conf.SetAtomPosition(i,(p.x+1,p.y,p.z))
assert math.isclose(receptor_frame_rmsd(reference,shifted),1.,abs_tol=1e-10)
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
top1=np.array([r['top1_RMSD_A'] for r in records]);best=np.array([r['best_sampled_RMSD_A'] for r in records])
recovery=int(np.sum(top1<2));sampling=int(np.sum(best<2))
print({'top1_recovery':f'{recovery}/9','sampled_native_like':f'{sampling}/9','ranking_criterion_met':recovery>=8})
fig,ax=plt.subplots(figsize=(9,4));ax.plot(top1,'o',label='Top-ranked pose');ax.plot(best,'s',label='Best sampled crystal RMSD')
ax.axhline(2,color='gray',linestyle='--');ax.set(xlabel='Independent starting-geometry / search-seed combination',ylabel='Receptor-frame heavy-atom RMSD / A');ax.legend()
publish_plot(fig,'sampling_vs_ranking.png')
result={'kind':'calculated','scope':'saved SDF pose audit, no new docking','top1_within_2A':recovery,
        'best_sampled_within_2A':sampling,'ranking_status':'PASS' if recovery>=8 else 'FAIL',
        'mean_top1_RMSD_A':float(top1.mean()),'binding_affinity':'NOT_MEASURED','prospective_validation':'NOT_RUN'}
```

Результат: top-1 recovery 0/9, native-like sampling 9/9, средний top-1 RMSD≈9.559 Å. Это провал ранжирования при успешном достижении части правильных поз. Статус исполнения PASS в исходном отчёте не означает научный PASS протокола. Vina score не является измеренной свободной энергией связывания.

Следующий протокол должен заранее определить сравнение гидратации/протонирования, модели рецептора и независимый структурный контроль (например, другой кристаллический комплекс ксантина). Нельзя подбирать ограничения по единственной известной native-позе и считать её же независимой проверкой. До этого прогноз аффинности истрадефиллина по этому scoring не принимается.

```python
write_json(OUT/'result.json',result)
from dossier_records import append_record
print(append_record(init_dossier(),'M11-L02','A',result,ROOT,inputs=['practicuum/shared/data/target_docking/a2a_crystal_reference.sdf', 'practicuum/shared/data/target_docking/a2a_preparation.json', 'practicuum/shared/data/target_docking/a2a_protein_crystal.pdb', 'practicuum/shared/data/target_docking/a2a_protocol.json', 'practicuum/shared/data/target_docking/a2a_redocking.json', 'practicuum/shared/data/target_docking/hmgcr_crystal_reference.sdf', 'practicuum/shared/data/target_docking/hmgcr_failure.json', 'practicuum/shared/data/target_docking/hmgcr_gap_audit.json', 'practicuum/shared/data/target_docking/hmgcr_protein_crystal.pdb', 'practicuum/shared/data/target_docking/hmgcr_repair_audit.json', 'practicuum/shared/data/target_docking/manifest.json', 'practicuum/shared/data/target_docking/start-13-search-101.sdf', 'practicuum/shared/data/target_docking/start-13-search-202.sdf', 'practicuum/shared/data/target_docking/start-13-search-303.sdf', 'practicuum/shared/data/target_docking/start-37-search-101.sdf', 'practicuum/shared/data/target_docking/start-37-search-202.sdf', 'practicuum/shared/data/target_docking/start-37-search-303.sdf', 'practicuum/shared/data/target_docking/start-73-search-101.sdf', 'practicuum/shared/data/target_docking/start-73-search-202.sdf', 'practicuum/shared/data/target_docking/start-73-search-303.sdf']))
```
