# Ответы к лабораторной работе 12: Электронная энергия H2: исполняемый RHF/STO-3G

## Контрольный результат

RHF/STO-3G при 0,74 Å: −1,116759307±5e−5 Hartree. Все точки должны сходиться. Это HF, не выполненный DFT.

## Ответы на задания

1. При коэффициенте 2625,5: −26,255 кДж/моль.
2. Enuc=1/R в атомных единицах; без него электронная энергия не равна полной Born–Oppenheimer энергии.
3. Одна ограниченная детерминанта не описывает статическую корреляцию растянутой связи; хорошая SCF-сходимость не исправляет модель.

## Как разбирать расхождение

Сначала сравните вход, единицы и режим выполнения. Затем проверьте версии и параметры, после этого — собственную интерпретацию. Для численного расхождения сохраните исходные значения и residual; для структурного — raw/parent и политику. Статус «получен эталонный выход из файла» нельзя подписывать «я выполнил расчёт».

## Готовый скрипт

Тот же скрипт полностью включён в notebook. Общие научные функции находятся в `Labs/chemistry.py`, `Labs/h2_scf.py`, `Labs/docking.py`, `Labs/train_esol.py` и `Labs/pipeline.py` в зависимости от работы.

```python
from h2_scf import rhf_h2
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

```

**Рубеж понимания:** сумейте объяснить хотя бы один отрицательный контроль и одно недопустимое обобщение этого результата. Численный эталон описывает конкретную постановку, не универсальную гарантию.
