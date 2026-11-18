# Ответы к лабораторной работе 9: Отчёт, который можно прочитать без кода

## Контрольный результат

В отчёте 12 строк включая ошибки, 10 валидных структур; картинки и относительные ссылки существуют.

## Ответы на задания

1. Статус дублируется текстом; цвет не единственный канал.
2. Корректная подпись: рассчитанные признаки parent при указанной политике.
3. Один конформер не задаёт ансамбль и не доказывает позу связывания.

## Как разбирать расхождение

Сначала сравните вход, единицы и режим выполнения. Затем проверьте версии и параметры, после этого — собственную интерпретацию. Для численного расхождения сохраните исходные значения и residual; для структурного — raw/parent и политику. Статус «получен эталонный выход из файла» нельзя подписывать «я выполнил расчёт».

## Готовый скрипт

Тот же скрипт полностью включён в notebook. Общие научные функции находятся в `Labs/chemistry.py`, `Labs/h2_scf.py`, `Labs/docking.py`, `Labs/train_esol.py` и `Labs/pipeline.py` в зависимости от работы.

```python
from chemistry import screen,parse
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

```

**Рубеж понимания:** сумейте объяснить хотя бы один отрицательный контроль и одно недопустимое обобщение этого результата. Численный эталон описывает конкретную постановку, не универсальную гарантию.
