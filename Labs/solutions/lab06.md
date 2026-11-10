# Ответы к лабораторной работе 6: Ансамбль конформеров бутана

## Контрольный результат

Есть хотя бы один конформер; все записанные энергии конечны; статус несходимости не скрыт; минимальная энергия бутана около −5,1…−4 ккал/моль при найденном наборе, не жёсткая универсальная константа.

## Ответы на задания

1. Меняется поиск; устойчивость исследуют несколькими стартами, а не обещают одинаковую выборку.
2. С конечным числом стартов поверхность исследована неполно.
3. Торсион измеряется по четырём атомам в координатах; камера координаты не меняет.

## Как разбирать расхождение

Сначала сравните вход, единицы и режим выполнения. Затем проверьте версии и параметры, после этого — собственную интерпретацию. Для численного расхождения сохраните исходные значения и residual; для структурного — raw/parent и политику. Статус «получен эталонный выход из файла» нельзя подписывать «я выполнил расчёт».

## Готовый скрипт

Тот же скрипт полностью включён в notebook. Общие научные функции находятся в `Labs/chemistry.py`, `Labs/h2_scf.py`, `Labs/docking.py`, `Labs/train_esol.py` и `Labs/pipeline.py` в зависимости от работы.

```python
from rdkit import Chem
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

```

**Рубеж понимания:** сумейте объяснить хотя бы один отрицательный контроль и одно недопустимое обобщение этого результата. Численный эталон описывает конкретную постановку, не универсальную гарантию.
