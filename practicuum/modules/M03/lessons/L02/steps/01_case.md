# Разбор A. Почему одинаковая формула не решает вопрос идентичности?

Мы получили две карточки ксантинов. Коллега предлагает оставить одну: формула и молярная масса совпадают. Не будем спорить по названию. Построим проверку, которая показывает, какая информация скрыта за этим совпадением.

```python
from pathlib import Path
import sys,json,math
from IPython.display import display
ROOT=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'programm/course.json').is_file())
sys.path.insert(0,str(ROOT/'practicuum/shared'))
from course_support import compound,workspace,write_json
from rdkit import Chem,rdBase
from rdkit.Chem import Descriptors,rdMolDescriptors,Draw
OUT=workspace('M03-L02','case')
rows=[]
molecules=[]
for name in ['theophylline','theobromine']:
    record=compound(name)
    molecule=Chem.MolFromSmiles(record['smiles'])
    if molecule is None:raise ValueError('Не разобрана запись: '+name)
    molecules.append(molecule)
    rows.append({'name':name,'cid':record['cid'],'source':record['source_url'],
       'formula':rdMolDescriptors.CalcMolFormula(molecule),
       'MW_g_mol':Descriptors.MolWt(molecule),
       'canonical_smiles':Chem.MolToSmiles(molecule,isomericSmiles=True)})
display(rows)
```

Теперь предскажите результат трёх сравнений: формула, масса, каноническая запись. Не подменяем результат вопросом «похожи ли картинки»: выбираем проверяемые свойства графа.

```python
comparison={'same_formula':rows[0]['formula']==rows[1]['formula'],
            'same_mass':math.isclose(rows[0]['MW_g_mol'],rows[1]['MW_g_mol'],abs_tol=1e-9),
            'same_canonical_graph':rows[0]['canonical_smiles']==rows[1]['canonical_smiles']}
display(comparison)
assert comparison=={'same_formula':True,'same_mass':True,'same_canonical_graph':False}
# Визуализация помогает локализовать различие после вычислительной проверки.
display(Draw.MolsToGridImage(molecules,legends=[r['name'] for r in rows],subImgSize=(330,250)))
```

Первые два совпадения верны, но не достаточны для объединения. Посмотрите, где стоят метильные группы относительно атомов азота. Это конституционное различие, а не просто другой порядок символов. Из него ещё нельзя количественно вывести различие активности: для этого понадобятся биологические данные с сопоставимыми условиями.

Запишем политику: сохраняем самостоятельные записи и исходные структуры, разрешаем поиск по общей формуле, но не используем его как дедупликацию по полной идентичности. Подобное правило потребуется при работе с формами B, однако там придётся проверить ещё и компоненты/заряд.

```python
passport={'rows':rows,'comparison':comparison,'rdkit':rdBase.rdkitVersion,
  'decision':'Не объединять конституционные изомеры по формуле или массе.',
  'next_check':'Для физического образца выбрать метод, способный различить предполагаемые изомеры, и сравнить со стандартами.'}
write_json(OUT/'isomer_comparison.json',passport)
print(OUT/'isomer_comparison.json')
```

Проверьте понимание: каноническая строка решает сравнение при выбранной политике графа. Может ли она сама доказать, что содержимое неизвестной пробирки соответствует этой строке? Если нет, назовите недостающее звено.
