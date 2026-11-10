# Ответы к лабораторной работе 11: QSPR растворимости ESOL

## Контрольный результат

Identity:901/227, MAE RF≈0,497; scaffold:1009/119, MAE RF≈0,716 для зафиксированных зависимостей и seed. Эти значения не универсальная точность.

## Ответы на задания

1. Размеры групп различны; ациклические структуры собраны в одну группу.
2. Нужно сохранить ID, measured/predicted и интерпретацию, а не перекраивать test после просмотра.
3. Среднее и разброс нескольких заранее заданных splits лучше описывают устойчивость; настройка остаётся отдельно.

## Как разбирать расхождение

Сначала сравните вход, единицы и режим выполнения. Затем проверьте версии и параметры, после этого — собственную интерпретацию. Для численного расхождения сохраните исходные значения и residual; для структурного — raw/parent и политику. Статус «получен эталонный выход из файла» нельзя подписывать «я выполнил расчёт».

## Готовый скрипт

Тот же скрипт полностью включён в notebook. Общие научные функции находятся в `Labs/chemistry.py`, `Labs/h2_scf.py`, `Labs/docking.py`, `Labs/train_esol.py` и `Labs/pipeline.py` в зависимости от работы.

```python
from train_esol import run
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

```

**Рубеж понимания:** сумейте объяснить хотя бы один отрицательный контроль и одно недопустимое обобщение этого результата. Численный эталон описывает конкретную постановку, не универсальную гарантию.
