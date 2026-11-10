# Ответы к лабораторной работе 5: Поиск аналогов и Танимото

## Контрольный результат

T=0,5 на множествах; диагональ Morgan=1; симметрия и диапазон [0,1].

## Ответы на задания

1. Числа зависят от радиуса; сравнивать пороги разных представлений без калибровки нельзя.
2. Хеширование допускает коллизии и может не кодировать часть стереоинформации.
3. Возможна группировка по каркасам с последующим выбором представителя при сохранении критериев задачи.

## Как разбирать расхождение

Сначала сравните вход, единицы и режим выполнения. Затем проверьте версии и параметры, после этого — собственную интерпретацию. Для численного расхождения сохраните исходные значения и residual; для структурного — raw/parent и политику. Статус «получен эталонный выход из файла» нельзя подписывать «я выполнил расчёт».

## Готовый скрипт

Тот же скрипт полностью включён в notebook. Общие научные функции находятся в `Labs/chemistry.py`, `Labs/h2_scf.py`, `Labs/docking.py`, `Labs/train_esol.py` и `Labs/pipeline.py` в зависимости от работы.

```python
from chemistry import standardize, similarity
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

```

**Рубеж понимания:** сумейте объяснить хотя бы один отрицательный контроль и одно недопустимое обобщение этого результата. Численный эталон описывает конкретную постановку, не универсальную гарантию.
