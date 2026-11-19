from pathlib import Path
import hashlib,json,sys
import numpy as np
from rdkit import Chem
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'practicuum/shared'))
from conformer_ensemble import aligned_conformer_rmsd
E=R/'practicuum/evidence';D=R/'practicuum/shared/data/conformer_research'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
protocol=read(E/'20261119-GFN2-fixed-geometry-inputs/protocol.json')
win=read(E/'20261119-GFN2-fixed-geometry-windows/result.json');linux=read(E/'20261119-GFN2-fixed-geometry-linux/result.json')
if win['protocol_sha256']!=linux['protocol_sha256']:raise ValueError('Different fixed geometry protocols')
matches=[]
for a,b in zip(win['singlepoints'],linux['singlepoints']):
 if (a['geometry'],a['input_sha256'])!=(b['geometry'],b['input_sha256']):raise ValueError('Different input geometry bytes')
 delta=b['energy_Eh']-a['energy_Eh'];matches.append({'geometry':a['geometry'],'input_sha256':a['input_sha256'],
   'windows_energy_Eh':a['energy_Eh'],'linux_energy_Eh':b['energy_Eh'],'difference_Eh':delta})
maximum=max(abs(r['difference_Eh']) for r in matches)
initial=[]
for platform in ['','-linux']:
 mols=list(Chem.SDMolSupplier(str(E/f'20261119-conformer-GFN2-istradefylline{platform}/initial_ensemble.sdf'),removeHs=False))
 initial.append({int(m.GetProp('id')):m for m in mols})
if initial[0].keys()!=initial[1].keys():raise ValueError('Different initial sample IDs')
rmsd=[aligned_conformer_rmsd(initial[0][i],initial[1][i]) for i in initial[0]]
basins=read(E/'20261119-GFN2-cross-platform-reproduction/result.json')
out=E/'20261119-GFN2-cross-platform-diagnosis';out.mkdir(exist_ok=False)
report={'status':'PASS' if maximum<=protocol['absolute_energy_difference_tolerance_Eh'] else 'FAIL',
 'scope':'Identical-geometry engine comparison; complete stochastic/optimized basin-set reproduction remains REVIEW',
 'fixed_geometry_count':len(matches),'fixed_geometry_results':matches,'fixed_geometry_max_abs_energy_difference_Eh':maximum,
 'fixed_geometry_energy_tolerance_Eh':protocol['absolute_energy_difference_tolerance_Eh'],
 'initial_same_id_geometry_RMSD_A':{'count':len(rmsd),'median':float(np.median(rmsd)),'maximum':float(max(rmsd)),
                                  'count_above_0_01_A':sum(x>.01 for x in rmsd)},
 'basin_comparison':basins,'complete_basin_set_reproduction':'REVIEW',
 'assignment_within_both_tolerances':sum(x['within_comparison_tolerances'] for x in basins['matched_basins']),
 'diagnosis':'Initial MMFF-refined geometries differ across platforms; 0.5-A selection and finite optimization can reach different basins. Fixed-geometry comparisons separate this from executable energy differences. No numerical-error estimate is inferred from energies of geometrically unmatched basins.',
 'observations_not_claimed':'No unique causal attribution among embedding, MMFF, selection and optimization without further controlled experiments; no exhaustive/global-minimum/population claim',
 'source_result_sha256':{str(p.relative_to(R)).replace('\\','/'):sha(p) for p in [E/'20261119-GFN2-fixed-geometry-windows/result.json',E/'20261119-GFN2-fixed-geometry-linux/result.json',E/'20261119-GFN2-cross-platform-reproduction/result.json']}}
(out/'result.json').write_text(json.dumps(report,indent=2)+'\n');(out/'auditor-source.py').write_bytes(Path(__file__).read_bytes())
(D/'cross_platform_reproduction.json').write_text(json.dumps(report,indent=2)+'\n')
p=D/'bundle-manifest.json';b=read(p);b['files_sha256']={str(f.relative_to(D)).replace('\\','/'):sha(f) for f in sorted(D.rglob('*')) if f.is_file() and f!=p};p.write_text(json.dumps(b,indent=2)+'\n')
for l in ['L01','L02']:
 p=R/f'practicuum/modules/M06/lessons/{l}/lesson.json';j=read(p);j['inputs']=['practicuum/shared/data/conformer_research/'+n for n in b['files_sha256']]+['practicuum/shared/data/conformer_research/bundle-manifest.json'];p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=R/'practicuum/modules/M06/lessons/L01/steps/01_case.md';text=p.read_text(encoding='utf-8')
marker="```python\nwrite_json(OUT/'result.json',result)"
extra='''## Независимый запуск под другой ОС

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

'''
if marker not in text:raise ValueError('Canonical insertion marker absent')
p.write_text(text.replace(marker,extra+marker),encoding='utf-8')
p=R/'practicuum/shared/data/sources-v2.json';records=read(p)
for record in records:
 if record['file']=='conformer_research/bundle-manifest.json':record.update(sha256=sha(D/'bundle-manifest.json'),bytes=(D/'bundle-manifest.json').stat().st_size)
p.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(report['status'],'fixed geometry max energy difference',maximum,'initial RMSD',report['initial_same_id_geometry_RMSD_A'],'basins',report['assignment_within_both_tolerances'],'/10; full set REVIEW')
