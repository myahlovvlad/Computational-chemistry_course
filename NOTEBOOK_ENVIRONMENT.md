# Среда парного практикума: uv / WSL / IDE

Актуальный маршрут: **14 модулей, 28 notebooks**. В каждом модуле `labXX.ipynb` содержит разбор с чередованием пояснений и кода, а `labXX_practice.ipynb` — три самостоятельных кейса. DFT включён в модуль 12. Quickstart и отдельное DFT-дополнение сохранены как вспомогательные материалы прежней редакции.

[Полная инструкция установки, выбора ядра и диагностики](Labs/SETUP.md). [Разработка приложений через IDE](Labs/ide/README.md).

В Ubuntu из корня проекта:

```bash
uv sync --frozen
uv run --frozen python tools/register_uv_kernel.py
uv run --frozen python tools/preflight.py
bash tools/start_notebooks.sh
```

Ядро `chemistry-course-uv` использует проектную `.venv` через `uv run --frozen`. Активация в ячейке не требуется. При переносе папки повторите регистрацию; её абсолютный путь должен совпасть с новым checkout. В VS Code открывайте папку через WSL и выбирайте это ядро. Персональный запомненный выбор другого ядра может потребовать однократного переключения.

На этом ПК: `/home/miakhlov/course-notebooks`. Из PowerShell:

```powershell
wsl -d Ubuntu-24.04 -u miakhlov -- bash /home/miakhlov/course-notebooks/tools/start_notebooks.sh
```

Откройте напечатанный localhost URL с токеном JupyterLab. `.venv`, результаты и файлы ученика не входят в Git. Новая редакция имеет [отдельный журнал исполнения](Labs/benchmarks/paired-execution.json); исторические файлы `environment-validation/` относятся к предыдущему маршруту из 16 notebooks и не заменяют эту проверку.
