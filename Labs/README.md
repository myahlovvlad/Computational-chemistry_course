# Практикум: два notebook на модуль

[Установка и настройка среды](SETUP.md). [Разработка приложений через IDE](ide/README.md).

Первый notebook сочетает пояснения с исполняемыми короткими шагами. Второй содержит три самостоятельных кейса без подставленных решений. Работа над приложением ведётся в IDE; notebook сохраняет постановку и доказательства.

| Модуль | Разбор | Самостоятельный практикум | Руководство |
|---|---|---|---|
| 1. Паспорт проекта и взаимодействие факторов | [lab01](notebooks/lab01.ipynb) | [lab01_practice](notebooks/lab01_practice.ipynb) | [Guideline](guides/lab01.md) |
| 2. Проверяемый цифровой верстак | [lab02](notebooks/lab02.ipynb) | [lab02_practice](notebooks/lab02_practice.ipynb) | [Guideline](guides/lab02.md) |
| 3. Идентичность, соли и таутомеры | [lab03](notebooks/lab03.ipynb) | [lab03_practice](notebooks/lab03_practice.ipynb) | [Guideline](guides/lab03.md) |
| 4. Осмысленные дескрипторы | [lab04](notebooks/lab04.ipynb) | [lab04_practice](notebooks/lab04_practice.ipynb) | [Guideline](guides/lab04.md) |
| 5. Поиск аналогов и Танимото | [lab05](notebooks/lab05.ipynb) | [lab05_practice](notebooks/lab05_practice.ipynb) | [Guideline](guides/lab05.md) |
| 6. Ансамбль конформеров бутана | [lab06](notebooks/lab06.ipynb) | [lab06_practice](notebooks/lab06_practice.ipynb) | [Guideline](guides/lab06.md) |
| 7. Кураторство активности и происхождение данных | [lab07](notebooks/lab07.ipynb) | [lab07_practice](notebooks/lab07_practice.ipynb) | [Guideline](guides/lab07.md) |
| 8. Скрининг с журналом и контролями | [lab08](notebooks/lab08.ipynb) | [lab08_practice](notebooks/lab08_practice.ipynb) | [Guideline](guides/lab08.md) |
| 9. Отчёт, который можно прочитать без кода | [lab09](notebooks/lab09.ipynb) | [lab09_practice](notebooks/lab09_practice.ipynb) | [Guideline](guides/lab09.md) |
| 10. Реальный redocking 1IEP | [lab10](notebooks/lab10.ipynb) | [lab10_practice](notebooks/lab10_practice.ipynb) | [Guideline](guides/lab10.md) |
| 11. QSPR растворимости ESOL | [lab11](notebooks/lab11.ipynb) | [lab11_practice](notebooks/lab11_practice.ipynb) | [Guideline](guides/lab11.md) |
| 12. Электронная энергия H2: RHF и DFT/PBE | [lab12](notebooks/lab12.ipynb) | [lab12_practice](notebooks/lab12_practice.ipynb) | [Guideline](guides/lab12.md) |
| 13. Шаблонный ретросинтез и выбор маршрута | [lab13](notebooks/lab13.ipynb) | [lab13_practice](notebooks/lab13_practice.ipynb) | [Guideline](guides/lab13.md) |
| 14. Передаваемый лабораторный конвейер | [lab14](notebooks/lab14.ipynb) | [lab14_practice](notebooks/lab14_practice.ipynb) | [Guideline](guides/lab14.md) |

## Проверяемость

[Свежие запуски](benchmarks/paired-execution.json) разделяют исполнение разбора, проверку незаполненного каркаса и авторскую проверку эталонных решений. NOT_RUN у самостоятельного задания означает, что ученик его ещё не решил. PASS численного контракта не оценивает интерпретацию, приложение или защиту. Исторический аудит Issue #1 относится к исходному commit и не сертифицирует эту новую редакцию.

Quickstart в Stepik_course/practice и старое DFT-дополнение — вспомогательные материалы прежней версии; действующий маршрут состоит ровно из 28 notebooks в этой таблице. DFT включён в основной разбор модуля 12.
