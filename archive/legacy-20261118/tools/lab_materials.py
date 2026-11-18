"""Per-module laboratory briefs, authored exercises, and executable code cells."""

LABS = {
1: dict(title="Паспорт проекта и взаимодействие факторов", purpose="Отделить исследовательский вопрос от инструмента и увидеть взаимодействие в плане 2×2.",
 data="factorial.csv: четыре искусственных отклика при кодированных A/B; единицы условные.",
 workflow="Вопрос → факторы → модель с взаимодействием → эффекты → ограничение насыщенного плана.",
 steps=["Прочитайте четыре строки и проверьте полный набор сочетаний ±1.","Постройте матрицу [1,A,B,A·B], решите систему и сравните коэффициенты с эффектами.","Покажите две линии отклика и объясните, почему непараллельность означает взаимодействие."],
 tasks=["Восстановите пропущенный столбец AB и вычислите эффект A.","Предложите два повтора и объясните, какую неопределённость они оценят.","Перепишите цель своего проекта как величину, контроль и следующее решение."],
 answers=["β=[50,10,5,8]; эффекты A=20, B=10, AB=16.","Повторы должны оценивать вариабельность при фиксированных условиях; четыре уникальные точки не дают остаточных степеней свободы насыщенной модели.","Допустимая цель содержит условия измерения и критерий решения; «найти хорошую молекулу» недостаточно."],
 benchmark="Численные эффекты 20/10/16; проверка покрытия четырёх комбинаций. Это тест арифметики, не экспериментальный эффект.",
 code='''design = pd.read_csv(DATA / "factorial.csv")
x = np.column_stack([np.ones(len(design)), design.A, design.B, design.A*design.B])
beta = np.linalg.solve(x, design.y)
effects = 2*beta[1:]
print("Коэффициенты:", beta, "Эффекты:", effects)
assert np.allclose(beta, [50,10,5,8])
assert np.allclose(effects, [20,10,16])
assert len(set(zip(design.A, design.B))) == 4
for b, group in design.groupby("B"):
    group = group.sort_values("A")
    plt.plot(group.A, group.y, "o-", label=f"B={b}")
plt.xlabel("A, кодированный уровень"); plt.ylabel("Отклик, условные единицы")
plt.legend(); plt.savefig(OUT / "factorial.png", dpi=150); plt.show()
artifact = {"beta": beta.tolist(), "effects": effects.tolist(), "residual_df": 0}
'''),
2: dict(title="Проверяемый цифровой верстак",purpose="Проверить интерпретатор, зависимость и контракт численного преобразования до химического конвейера.",
 data="molecules.csv; системные версии и контрольные значения концентрации.",
 workflow="Интерпретатор → версии → hash входа → функция с единицами → отрицательные контроли.",
 steps=["Запишите путь Python и версии, отличая среду выполнения от редактора.","Посчитайте SHA256 входа и pIC50 двумя эквивалентными способами.","Проверьте отрицательный/нулевой ввод и неизвестную единицу без молчаливого исправления."],
 tasks=["Допишите перевод uM в M без использования готовой функции.","Объясните ошибку импорта при двух Python.","Измените байт копии CSV и сравните hash."],
 answers=["Коэффициент для uM равен 1e−6; 0,1 uM даёт pIC50=7.","Нужно сравнить sys.executable ядра с интерпретатором, которому принадлежит pip.","Hash изменится, но это не свидетельство улучшения химического качества."],benchmark="100 nM = 0.1 uM → 7; ноль/неизвестная единица отклоняются; версии и hash сохранены.",
 code='''from chemistry import p_activity
import hashlib, platform, rdkit
passport = {"python": platform.python_version(), "executable": sys.executable,
            "rdkit": rdkit.__version__, "sha256": hashlib.sha256((DATA/"molecules.csv").read_bytes()).hexdigest()}
print(passport)
assert math.isclose(p_activity(100,"nM"),7)
assert math.isclose(p_activity(0.1,"uM"),7)
for value,unit in [(0,"nM"),(-1,"M"),(1,"unknown")]:
    try:
        p_activity(value,unit)
    except ValueError:
        continue
    raise AssertionError("Некорректный ввод принят")
artifact = passport
'''),
3: dict(title="Идентичность, соли и таутомеры",purpose="Построить проверяемую таблицу raw→parent и сохранить смысл химических различий.",data="molecules.csv: 12 исходных записей, два ошибочных ввода, соль, ковалентный Cl и стереопара.",workflow="ID/raw → парсинг → явная политика → parent → журнал и контрпримеры.",
 steps=["Спрогнозируйте пары эквивалентных графов до запуска.","Обработайте все строки, включая ошибки, не удаляя ID.","Проверьте отдельно ковалентный Cl, стереопару и объединение таутомеров по переключателю."],
 tasks=["Добавьте в копию датасета бромбензол; сохранится ли Br?","Поменяйте порядок компонентов соли; сравните parent.","Объясните, почему одинаковый parent не разрешает смешать растворимость соли и кислоты."],
 answers=["Ковалентный Br должен сохраниться при parent-политике.","Порядок компонентов не определяет parent; split по точке некорректен.","Измерения относятся к физическим формам и условиям, которые parent-представление теряет."],benchmark="12 строк на выходе; M08/M09 invalid; M01=M02 и M03=M04 по parent; M10≠M11.",
 code='''from chemistry import screen, standardize, parse
raw = pd.read_csv(DATA/"molecules.csv", keep_default_na=False)
records = [{"id": row.id, **screen(row.smiles)} for row in raw.itertuples()]
report = pd.DataFrame(records); display(report)
report.to_csv(OUT/"curated.csv", index=False)
by_id = {row["id"]:row for row in records}
assert len(records)==12 and sum(row["status"]=="invalid" for row in records)==2
assert by_id["M01"]["parent_smiles"]==by_id["M02"]["parent_smiles"]
assert by_id["M03"]["parent_smiles"]==by_id["M04"]["parent_smiles"]
assert "Cl" in by_id["M05"]["parent_smiles"]
assert by_id["M10"]["parent_smiles"]!=by_id["M11"]["parent_smiles"]
pair=["O=c1cccc[nH]1","Oc1ccccn1"]
assert standardize(pair[0]).parent_smiles != standardize(pair[1]).parent_smiles
assert standardize(pair[0],True).parent_smiles == standardize(pair[1],True).parent_smiles
artifact={"rows":len(records),"invalid":2,"policy":by_id["M01"]["policy"]}
'''),
4: dict(title="Осмысленные дескрипторы",purpose="Посчитать признаки и отличить нулевое значение, пропуск и контекстное предупреждение.",data="Те же 12 строк; признаки рассчитываются только для валидного parent.",workflow="Стандартизация → признаки с единицами → четыре условия Ro5 → объяснение.",
 steps=["Сравните этанол и бензол качественно до расчёта.","Выведите MW, MolLogP, TPSA, HBD, HBA и число предупреждений.","Проверьте полиол, для которого важны HBD/HBA, а не только масса и липофильность."],
 tasks=["Восстановите формулу счётчика четырёх нарушений.","Найдите два признака, которые могут быть связаны, и объясните, почему это не две независимые причины активности.","Объясните отличие logP от logD(pH)."],
 answers=["MW>500, MolLogP>5, HBD>5, HBA>10; TPSA отдельно.","Масса и число тяжёлых атомов обычно связаны; причинный вывод из корреляции не следует.","LogD учитывает распределение всех форм при заданном pH; MolLogP не является его прямым измерением."],benchmark="MW этанола 46,069±0,01; TPSA бензола 0; контрольный полиол нарушает HBD/HBA.",
 code='''from chemistry import standardize, descriptors
raw=pd.read_csv(DATA/"molecules.csv",keep_default_na=False)
table=[]
for row in raw.itertuples():
    try:
        parent=standardize(row.smiles).parent_smiles
    except ValueError:
        continue
    table.append({"id":row.id,"parent":parent,**descriptors(parent)})
features=pd.DataFrame(table); display(features)
features.to_csv(OUT/"features.csv",index=False)
assert math.isclose(descriptors("CCO")["MolWt"],46.069,abs_tol=0.01)
assert descriptors("c1ccccc1")["TPSA"]==0
polyol=descriptors("OC(O)C(O)C(O)C(O)C(O)C(O)C(O)C(O)C(O)C(O)CO")
assert polyol["HBD"]>5 and polyol["HBA"]>10 and polyol["ro5_violations"]==2
artifact={"valid_rows":len(features),"ethanol":descriptors("CCO"),"polyol":polyol}
'''),
5: dict(title="Поиск аналогов и Танимото",purpose="Сравнить ручной бинарный расчёт с молекулярным Morgan и зафиксировать параметры.",data="molecules.csv; битовые множества {1,2,3}/{2,3,4} — искусственное упражнение.",workflow="Ручная метрика → Morgan → матрица → ранжирование → ограничение.",
 steps=["Вычислите вручную общие и уникальные биты.","Сформируйте matrix всех валидных parent с одинаковым Morgan-параметрами.","Отранжируйте аналоги этанола; сохраните ID и параметры, не приписывая активность."],
 tasks=["Сравните радиусы 1 и 3 на новой паре с генератором RDKit.","Объясните, почему T=1 не является универсальным доказательством идентичности.","Предложите план выбора разнообразных аналогов вместо пяти почти одинаковых."],
 answers=["Числа зависят от радиуса; сравнивать пороги разных представлений без калибровки нельзя.","Хеширование допускает коллизии и может не кодировать часть стереоинформации.","Возможна группировка по каркасам с последующим выбором представителя при сохранении критериев задачи."],benchmark="T=0,5 на множествах; диагональ Morgan=1; симметрия и диапазон [0,1].",
 code='''from chemistry import standardize, similarity
from metrics import tanimoto
raw=pd.read_csv(DATA/"molecules.csv",keep_default_na=False)
valid=[]
for row in raw.itertuples():
    try: valid.append((row.id,standardize(row.smiles).parent_smiles))
    except ValueError: pass
matrix=np.array([[similarity(a[1],b[1]) for b in valid] for a in valid])
assert tanimoto({1,2,3},{2,3,4})==0.5
assert np.allclose(matrix,matrix.T) and np.allclose(np.diag(matrix),1)
assert matrix.min()>=0 and matrix.max()<=1
ranking=pd.DataFrame({"id":[x[0] for x in valid],"T_to_ethanol":[similarity("CCO",x[1]) for x in valid]})
display(ranking.sort_values("T_to_ethanol",ascending=False))
pd.DataFrame(matrix,index=[x[0] for x in valid],columns=[x[0] for x in valid]).to_csv(OUT/"tanimoto.csv")
plt.imshow(matrix,vmin=0,vmax=1);plt.colorbar(label="Morgan Tanimoto")
plt.savefig(OUT/"similarity.png",dpi=150);plt.show()
artifact={"radius":2,"fpSize":2048,"includeChirality":True,"molecules":len(valid)}
'''),
6: dict(title="Ансамбль конформеров бутана",purpose="Сгенерировать несколько геометрий и проверить покрытие, параметры и сходимость.",data="Бутан CCCC; геометрии создаются ETKDGv3, seed=42, до 20 стартов.",workflow="Граф → H → параметры → embedding → MMFF → статусы → SDF и энергия.",
 steps=["Проверьте наличие MMFF-параметров и задайте seed.","Создайте ансамбль и сохраните статус каждой оптимизации.","Сравните только сошедшиеся энергии одной системы; выгрузите SDF."],
 tasks=["Повторите с seed=7; сравните число геометрий и диапазон энергий.","Объясните, почему лучший найденный минимум не гарантированно глобальный.","Выведите торсионный угол одной конформации и отличите его от поворота камеры."],
 answers=["Меняется поиск; устойчивость исследуют несколькими стартами, а не обещают одинаковую выборку.","С конечным числом стартов поверхность исследована неполно.","Торсион измеряется по четырём атомам в координатах; камера координаты не меняет."],benchmark="Есть хотя бы один конформер; все записанные энергии конечны; статус несходимости не скрыт; минимальная энергия бутана около −5,1…−4 ккал/моль при найденном наборе, не жёсткая универсальная константа.",
 code='''from rdkit import Chem
from rdkit.Chem import AllChem
mol=Chem.AddHs(Chem.MolFromSmiles("CCCC"))
assert AllChem.MMFFHasAllMoleculeParams(mol)
params=AllChem.ETKDGv3();params.randomSeed=42;params.pruneRmsThresh=0.1
ids=list(AllChem.EmbedMultipleConfs(mol,numConfs=20,params=params))
optimization=AllChem.MMFFOptimizeMoleculeConfs(mol,numThreads=1,maxIters=500)
ensemble=pd.DataFrame([{"conf_id":i,"status":status,"energy_kcal_mol":energy} for i,(status,energy) in zip(ids,optimization)])
display(ensemble)
assert len(ids)>0
assert np.isfinite(ensemble.energy_kcal_mol).all()
assert (ensemble.status==0).any()
with Chem.SDWriter(str(OUT/"butane_conformers.sdf")) as writer:
    for row in ensemble.itertuples():
        mol.SetProp("MMFF_status",str(row.status));mol.SetProp("MMFF_energy_kcal_mol",str(row.energy_kcal_mol))
        writer.write(mol,confId=int(row.conf_id))
ensemble.to_csv(OUT/"energies.csv",index=False)
plt.scatter(ensemble.conf_id,ensemble.energy_kcal_mol);plt.xlabel("Conformer ID");plt.ylabel("MMFF kcal/mol")
plt.savefig(OUT/"conformers.png",dpi=150);plt.show()
artifact={"generated":len(ids),"converged":int((ensemble.status==0).sum()),"minimum":float(ensemble.energy_kcal_mol.min()),"seed":42}
'''),
7: dict(title="Кураторство активности и происхождение данных",purpose="Отделить сопоставимые точные наблюдения от других endpoint, границ и неизвестных единиц.",data="activities.csv — восемь искусственных записей; esol.csv — отдельный настоящий открытый корпус.",workflow="Схема → endpoint/мишень/ассей → единицы/отношение → журнал → snapshot hash.",
 steps=["Прочитайте условия консервативной политики T1/A1/IC50/=.","Преобразуйте только положительные концентрации с известными единицами.","Сохраните восемь исходных строк и причины шести исключений, отдельно прочитайте паспорт ESOL."],
 tasks=["Сохраните R03 как границу вместо точного числа.","Добавьте Ki с тем же числом и объясните, почему это не новый IC50.","Спроектируйте pagination/timeout для API, не запрашивая закрытые данные."],
 answers=["Для R03 pIC50<5; точечной регрессии в данном задании строка не подходит.","Разные величины требуют модели связи и условий, не только одинаковых единиц.","Нужны ограниченные повторы, проверка HTTP/schema и сохранение URL, параметров, даты и hash."],benchmark="Включены R01/R02 с pIC50=7; в журнале все 8 строк; остальные причины различимы.",
 code='''from chemistry import curate_activity
import hashlib
with (DATA/"activities.csv").open(encoding="utf-8") as handle:
    records=[curate_activity(row) for row in csv.DictReader(handle)]
table=pd.DataFrame(records);display(table)
included=[r for r in records if r["status"]=="included"]
assert [r["record_id"] for r in included]==["R01","R02"]
assert all(math.isclose(r["pIC50"],7) for r in included)
assert len(records)==8
table.to_csv(OUT/"activity_audit.csv",index=False)
esol=pd.read_csv(DATA/"esol.csv")
print("ESOL отдельно:",len(esol),"строк; measured target присутствует")
assert "measured log solubility in mols per litre" in esol
artifact={"included":2,"excluded":6,"esol_rows":len(esol),"esol_sha256":hashlib.sha256((DATA/"esol.csv").read_bytes()).hexdigest()}
'''),
8: dict(title="Скрининг с журналом и контролями",purpose="Развести качество ассая, структурный риск и ранжирование; не удалять спорные записи молча.",data="molecules.csv плюс заданные учебные контроли μ=100/10, σ=5/5 и библиотека N=1000,A=20,k=50,a=5.",workflow="Структуры → предупреждения → статусы → Z′ → EF → следующий контроль.",
 steps=["Получите все PAINS-предупреждения, не объявляя механизм доказанным.","Посчитайте Z′ и EF на отдельных числах.","Запишите следующий контроль для review и объяснение для eligible."],
 tasks=["Увеличьте σ до 20 и объясните знак Z′.","Почему EF нельзя вычислить, если истинное число активных неизвестно?","Рассчитайте условные затраты контроля с учётом цены ложного отказа."],
 answers=["Z′=−1/3; контрольные распределения плохо разделены в данной оценке.","Прогнозы модели не являются истинной разметкой активности.","Нужны вероятность помехи, чувствительность контроля и цена потерянного полезного кандидата; одних цен закупки недостаточно."],benchmark="Катехол review, пустой ввод invalid; Z′=2/3; EF@50=5; журнал 12 строк.",
 code='''from chemistry import screen
from metrics import z_prime,enrichment
raw=pd.read_csv(DATA/"molecules.csv",keep_default_na=False)
records=[{"id":r.id,**screen(r.smiles)} for r in raw.itertuples()]
table=pd.DataFrame(records);display(table[["id","status","reason"]])
assert screen("Oc1ccccc1O")["status"]=="review"
assert screen("")["status"]=="invalid"
assert math.isclose(z_prime(100,10,5,5),2/3)
assert enrichment(1000,20,50,5)==5
table.to_csv(OUT/"decisions.csv",index=False)
artifact={"Z_prime":z_prime(100,10,5,5),"EF_at_50":enrichment(1000,20,50,5),"statuses":table.status.value_counts().to_dict()}
'''),
9: dict(title="Отчёт, который можно прочитать без кода",purpose="Связать структуры, подписанные числовые признаки и статус решения в автономном отчёте.",data="molecules.csv; признаки и изображения рассчитываются заново.",workflow="ID → 2D-сетка → график MW/TPSA → CSV → HTML с ограничениями.",
 steps=["Соберите структуры с подписями ID.","Постройте MW/TPSA с единицами; не называйте область графика областью эффективности.","Сохраните картинки и автономный HTML с таблицей и текстовым выводом."],
 tasks=["Добавьте к точке ID и предупреждение.","Найдите вводящую в заблуждение подпись «drug-ready» и перепишите её.","Сформулируйте ограничение одной 3D-конформации."],
 answers=["Статус дублируется текстом; цвет не единственный канал.","Корректная подпись: рассчитанные признаки parent при указанной политике.","Один конформер не задаёт ансамбль и не доказывает позу связывания."],benchmark="В отчёте 12 строк включая ошибки, 10 валидных структур; картинки и относительные ссылки существуют.",
 code='''from chemistry import screen,parse
from rdkit.Chem import Draw
raw=pd.read_csv(DATA/"molecules.csv",keep_default_na=False)
table=pd.DataFrame([{"id":r.id,**screen(r.smiles)} for r in raw.itertuples()])
valid=table[table.status!="invalid"]
image=Draw.MolsToGridImage([parse(s) for s in valid.parent_smiles],molsPerRow=3,subImgSize=(260,180),legends=list(valid.id),returnPNG=False)
image.save(str(OUT/"structures.png"))
plt.figure(figsize=(7,4));plt.scatter(valid.MolWt,valid.TPSA)
for row in valid.itertuples(): plt.annotate(row.id,(row.MolWt,row.TPSA))
plt.xlabel("MolWt, g/mol");plt.ylabel("TPSA, square angstrom")
plt.tight_layout();plt.savefig(OUT/"properties.png",dpi=150);plt.show()
html="<meta charset='utf-8'><h1>Отчёт Химера</h1><p>Признаки parent, не доказательство активности.</p><img src='structures.png' width='800'><img src='properties.png' width='700'>"+table.to_html(index=False,escape=True)
(OUT/"report.html").write_text(html,encoding="utf-8")
assert len(table)==12
assert len(valid)==10
assert (OUT/"structures.png").exists() and (OUT/"report.html").exists()
artifact={"report":"report.html","rows":12,"structures":10}
'''),
10: dict(title="Реальный redocking 1IEP",purpose="Выполнить официальный пример Vina и сравнить геометрию с подготовленным лигандом.",data="Открытые 1IEP PDBQT/SDF, box и официальный выход; upstream commit и hash — в docking/provenance.json.",workflow="Проверка данных → box → Vina seed42/cpu1 → mapped RMSD → интерпретация.",
 steps=["Проверьте источник подготовленных файлов и систему координат.","Разберите официальный выход; при установленном Vina выполните собственный запуск.","Сравните score и RMSD по serial тяжёлых атомов, без независимого совмещения лиганда."],
 tasks=["Измените seed и сравните поиск при той же подготовке.","Почему serial-mapped RMSD не равен symmetry-corrected минимуму?","Какие шаги нужно добавить при подготовке нового сырого PDB?"],
 answers=["Числа могут измениться; устойчивость нужно измерять, подготовка остаётся фиксированной.","Эквивалентные атомы могут быть сопоставлены иначе; здесь строгое соответствие serial без перебора симметрии.","Выбор цепи/кофакторов/вод, протонирование, валентности, box и проверка референса; автоматическое удаление всего лишнего недопустимо."],benchmark="Полный запуск отмечен executed-vina. Score сравнивается с официальным примером описательно; RMSD конечен. Если бинарника нет, явно reference-analysis, а не фиктивный выполненный докинг.",
 code='''from docking import run_docking
result=run_docking(ROOT,OUT)
print(json.dumps(result,indent=2))
assert math.isfinite(result["official_reference_rmsd_angstrom"])
assert result["reference_score"]<0
assert "rmsd_definition" in result
if result["mode"]=="executed-vina":
    assert math.isfinite(result["rmsd_angstrom"]) and result["score"]<0
else:
    print("Vina не установлен: выполнен только разбор официального выхода. Это явно ограниченный режим.")
artifact=result
'''),
11: dict(title="QSPR растворимости ESOL",purpose="Сравнить mean-baseline и Random Forest на двух групповых holdout без обучения преобразований на тесте.",data="esol.csv: 1128 строк, измеренный logS; предрассчитанный ESOL-прогноз не используется.",workflow="Паспорт → графовые признаки → identity/scaffold groups → train fit → test metrics → остатки.",
 steps=["Проверьте measured target и не включайте готовый predicted ESOL.","Запустите фиксированные группы и Pipeline с imputer только на train.","Сравните MAE/RMSE/R² и ближайшую train-похожесть; изучите пять крупнейших остатков."],
 tasks=["Почему 20% групп не обязаны давать 20% строк?","Определите, какие записи дали крупнейшие ошибки; не удаляйте их из отчёта.","Добавьте повторный split только как новый заранее определённый эксперимент, без выбора самого красивого теста."],
 answers=["Размеры групп различны; ациклические структуры собраны в одну группу.","Нужно сохранить ID, measured/predicted и интерпретацию, а не перекраивать test после просмотра.","Среднее и разброс нескольких заранее заданных splits лучше описывают устойчивость; настройка остаётся отдельно."],benchmark="Identity:901/227, MAE RF≈0,497; scaffold:1009/119, MAE RF≈0,716 для зафиксированных зависимостей и seed. Эти значения не универсальная точность.",
 code='''from train_esol import run
result=run(DATA/"esol.csv",OUT)
display(pd.json_normalize(result["splits"],sep="."))
assert result["rows"]==1128 and result["unique_identity"]==1117
for split in result["splits"].values():
    assert split["metrics"]["random_forest"]["MAE_logS"] < split["metrics"]["mean_baseline"]["MAE_logS"]
predictions=pd.read_csv(OUT/"scaffold_predictions.csv")
predictions["absolute_error"]=abs(predictions.measured_logS-predictions.predicted)
display(predictions.nlargest(5,"absolute_error"))
plt.scatter(predictions.measured_logS,predictions.predicted,alpha=0.6)
plt.plot([-10,2],[-10,2],"k--");plt.xlabel("Measured logS");plt.ylabel("Predicted logS")
plt.savefig(OUT/"parity.png",dpi=150);plt.show()
artifact=result
'''),
12: dict(title="Электронная энергия H2: исполняемый RHF/STO-3G",purpose="Проследить электронный расчёт от интегралов до сходимости и различить E, G и барьер.",data="Два атома H, расстояние 0,74 Å; стандартные параметры STO-3G заданы явно в h2_scf.py.",workflow="S/H/ERI → F[P] → FC=SCε → плотность → сходимость → кривая энергии.",
 steps=["Прочитайте ограничение реализации: только H2, закрытая оболочка, s-функции.","Посчитайте энергию и проверьте контрольное значение около −1,1167593 Hartree.","Просканируйте расстояние, затем объясните, почему этот расчёт не даёт ΔG и активационный барьер."],
 tasks=["Переведите разность −0,010 Hartree в кДж/моль.","Найдите слагаемое отталкивания ядер и объясните ошибку его пропуска.","Почему растянутая RHF-кривая не даёт корректную диссоциацию?"],
 answers=["При коэффициенте 2625,5: −26,255 кДж/моль.","Enuc=1/R в атомных единицах; без него электронная энергия не равна полной Born–Oppenheimer энергии.","Одна ограниченная детерминанта не описывает статическую корреляцию растянутой связи; хорошая SCF-сходимость не исправляет модель."],benchmark="RHF/STO-3G при 0,74 Å: −1,116759307±5e−5 Hartree. Все точки должны сходиться. Это HF, не выполненный DFT.",
 code='''from h2_scf import rhf_h2
result=rhf_h2(0.74)
print(result)
assert result["converged"]
assert abs(result["energy_hartree"]-(-1.116759307))<5e-5
assert math.isclose(-0.010*2625.5,-26.255,abs_tol=1e-9)
scan=pd.DataFrame([{"R_A":r,"E_hartree":rhf_h2(float(r))["energy_hartree"]} for r in np.linspace(0.5,2.5,11)])
scan.to_csv(OUT/"h2_scan.csv",index=False)
plt.plot(scan.R_A,scan.E_hartree,"o-");plt.xlabel("H-H distance, angstrom");plt.ylabel("RHF/STO-3G energy, Hartree")
plt.savefig(OUT/"h2_energy.png",dpi=150);plt.show()
artifact={"single_point":result,"minimum_of_grid":float(scan.E_hartree.min()),"DFT_executed":False}
'''),
13: dict(title="Шаблонный ретросинтез и выбор маршрута",purpose="Выполнить прозрачное структурное разбиение и проверить упрощённую экономическую модель.",data="Цель — метилацетат COC(C)=O; routes.csv содержит два вымышленных линейных маршрута.",workflow="Эфир → реакционный SMARTS → санитарная проверка продуктов → выходы → сравнение допущений.",
 steps=["Найдите сложноэфирный фрагмент и примените один заданный шаблон.","Проверьте, что получены кислота и спирт; это ещё не препаративный протокол.","Сравните два маршрута по произведению долей и заданным суммарным затратам."],
 tasks=["Примените шаблон к этилацетату; определите второй продукт.","Назовите три причины, по которым реальный выход может отличаться.","Почему SA Score не заменяет маршрут и прайс-лист?"],
 answers=["Кислота остаётся уксусной, спирт — этанол.","Совместимость групп, селективность, выделение/очистка и условия требуют источников и опыта.","SA Score — структурная эвристика без поставщика, даты, масштаба и проверенного синтеза."],benchmark="Продукты метилацетата: уксусная кислота и метанол; выходы A=0,56/B=0,855; приведённые затраты A≈1071,43/B≈877,19 при явно заданной модели.",
 code='''from rdkit import Chem
from rdkit.Chem import rdChemReactions
reaction=rdChemReactions.ReactionFromSmarts("[C:1](=[O:2])[O:3][C:4]>>[C:1](=[O:2])[OH:3].[OH][C:4]")
products=reaction.RunReactants((Chem.MolFromSmiles("COC(C)=O"),))
assert products
names=[]
for mol in products[0]:
    Chem.SanitizeMol(mol)
    for atom in mol.GetAtoms(): atom.SetAtomMapNum(0)
    names.append(Chem.MolToSmiles(mol))
print("Учебные предшественники:",names)
assert set(names)=={"CC(=O)O","CO"}
routes=pd.read_csv(DATA/"routes.csv")
routes["overall_yield"]=routes.yield1*routes.yield2
routes["normalized_cost"]=routes.assumed_cost/routes.overall_yield
display(routes)
assert np.allclose(routes.overall_yield,[0.56,0.855])
assert routes.loc[1,"normalized_cost"]<routes.loc[0,"normalized_cost"]
routes.to_csv(OUT/"route_comparison.csv",index=False)
artifact={"precursors":names,"routes":routes.to_dict(orient="records"),"scope":"one ester template, not general AI retrosynthesis"}
'''),
14: dict(title="Передаваемый лабораторный конвейер",purpose="Проверить работу с чужим CSV, сохранность строк и один вычислительный контракт для CLI и интерфейса.",data="molecules.csv; дополнительный ошибочный CSV без нужного столбца.",workflow="CSV contract → ядро → журнал всех строк → паспорт → CLI → проверка передачи.",
 steps=["Вызовите табличную функцию напрямую и проверьте все статусы.","Запустите тот же конвейер как отдельный CLI-процесс.","Сравните ID и hash отчётов, затем откройте локальный Streamlit при желании."],
 tasks=["Передайте файл с повторным ID; объясните явный отказ.","Перенесите проект в новую папку и повторите запуск по README.","Как добавить другую политику, сохранив проверяемость результатов?"],
 answers=["ID должен быть уникальным: иначе теряется связь строки и результата.","Нужны зависимости, относительные пути, исходные данные и ядро выбранной среды.","Параметр должен присутствовать в контракте и паспорте; результаты старого ввода/политики не смешивают с новыми."],benchmark="CLI и прямой вызов сохраняют 12 строк и hash; отсутствующий столбец/повторный ID отклоняются; Streamlit — тот же pipeline.",
 code='''from pipeline import process_csv
import subprocess
data=(DATA/"molecules.csv").read_bytes()
rows,passport=process_csv(data)
assert len(rows)==12
assert sum(row["status"]=="invalid" for row in rows)==2
for bad in [b"id,wrong\\nX,CCO\\n",b"id,smiles\\nX,CCO\\nX,CCN\\n"]:
    try: process_csv(bad)
    except ValueError: continue
    raise AssertionError("Неверный контракт принят")
process=subprocess.run([sys.executable,str(ROOT/"Labs/pipeline.py"),str(DATA/"molecules.csv"),"--out",str(OUT/"cli")],capture_output=True,text=True,check=True)
loaded=json.loads((OUT/"cli/report.json").read_text(encoding="utf-8"))
assert loaded["passport"]["input_sha256"]==passport["input_sha256"]
assert len(loaded["rows"])==12
display(pd.DataFrame(rows))
print("Интерфейс: python -m streamlit run Labs/app.py")
artifact=passport
'''),
}
