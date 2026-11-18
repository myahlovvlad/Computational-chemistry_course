# Ответы к лабораторной работе 2: Проверяемый цифровой верстак

## Контрольный результат

100 nM = 0.1 uM → 7; ноль/неизвестная единица отклоняются; версии и hash сохранены.

## Ответы на задания

1. Коэффициент для uM равен 1e−6; 0,1 uM даёт pIC50=7.
2. Нужно сравнить sys.executable ядра с интерпретатором, которому принадлежит pip.
3. Hash изменится, но это не свидетельство улучшения химического качества.

## Как разбирать расхождение

Сначала сравните вход, единицы и режим выполнения. Затем проверьте версии и параметры, после этого — собственную интерпретацию. Для численного расхождения сохраните исходные значения и residual; для структурного — raw/parent и политику. Статус «получен эталонный выход из файла» нельзя подписывать «я выполнил расчёт».

## Готовый скрипт

Тот же скрипт полностью включён в notebook. Общие научные функции находятся в `Labs/chemistry.py`, `Labs/h2_scf.py`, `Labs/docking.py`, `Labs/train_esol.py` и `Labs/pipeline.py` в зависимости от работы.

```python
from chemistry import p_activity
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

```

**Рубеж понимания:** сумейте объяснить хотя бы один отрицательный контроль и одно недопустимое обобщение этого результата. Численный эталон описывает конкретную постановку, не универсальную гарантию.
