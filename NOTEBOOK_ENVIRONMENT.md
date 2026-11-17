# Единая среда практикумов через uv и WSL

Все 16 notebooks используют ядро `chemistry-course-uv`: 14 ЛР, quickstart и DFT-дополнение. Ядро запускает Python через `uv run --frozen --project …`; `.venv` выбирается автоматически, ручная активация и установочные ячейки не нужны. Открытие файла выбирает именованное ядро; вычисления начинаются при запуске ячейки или Run All.

Полный маршрут использует Ubuntu 24.04 / WSL 2 и Python 3.12. PySCF не поддерживает native Windows: [официальная установка](https://pyscf.org/user/install.html). Windows `.venv` и Linux `.venv` — разные окружения; не переносите между ними бинарные пакеты.

В Ubuntu, из корня checkout:

```bash
uv sync --frozen
uv run --frozen python tools/register_uv_kernel.py
uv run --frozen jupyter lab --ip=127.0.0.1 --no-browser
```

Либо выполнить `bash tools/start_notebooks.sh`: скрипт синхронизирует uv-среду, регистрирует ядро и запускает JupyterLab.

Откройте напечатанный localhost URL с токеном в Windows-браузере. Сервер использует обычную аутентификацию Jupyter. Для VS Code сначала открыть папку через **WSL: Open Folder in WSL**, затем notebook; выбранное ядро — **Chemistry course (uv / WSL / Python 3.12)**. Если редактор запомнил старое ядро, один раз выбрать это ядро вручную; метаданные не могут отменить персональное сохранённое предпочтение редактора.

`uv.lock` фиксирует зависимости, а `.python-version` — Python 3.12. Перед запуском каждого ядра `uv` проверяет проект и подготавливает среду из lock. См. [интеграцию uv/Jupyter](https://docs.astral.sh/uv/guides/integration/jupyter/). После переноса/клонирования checkout повторить регистрацию: user kernelspec хранит абсолютный путь проекта. Последняя регистрация этого имени задаёт активный checkout.

Для фактического докинга нужен внешний Linux Vina 1.2.7 в PATH. Без Vina исходная ЛР 10 явно переходит к анализу подготовленного выхода; это не новый docking run. Получение бинарника: [официальный релиз](https://github.com/forlilab/AutoDock-Vina/releases/tag/v1.2.7). Бинарник и `.venv` в Git не входят.

Изменения notebooks ограничены `metadata.kernelspec`; химические входы, код, эталоны и учебный текст сохраняются.

Проверено 17.11.2026 на этом ПК: WSL 3.0.5 / Ubuntu 24.04, uv 0.13.8, Python 3.12.3, PySCF 2.15.1. Полный свежий прогон 16 notebooks и 25 существующих unit tests сохранён в отдельном аудите Issue #1. В самостоятельной копии `/home/miakhlov/course-notebooks` созданы новая `.venv` и регистрация ядра; [контроль автоматического выбора](environment-validation/kernel-smoke.json) проверяет метаданные всех 16 файлов и реально исполняет quickstart и DFT без явного переопределения имени ядра. Семантическое сравнение исходных JSON подтвердило, что в 16 notebooks изменён только kernelspec.

Для этой установленной копии из Windows PowerShell:

```powershell
wsl -d Ubuntu-24.04 -u miakhlov -- bash /home/miakhlov/course-notebooks/tools/start_notebooks.sh
```

Папка доступна в Проводнике: `\\wsl.localhost\Ubuntu-24.04\home\miakhlov\course-notebooks`. Внутри находятся `Labs/notebooks` (14 ЛР), `Labs/extensions/dft_pyscf.ipynb` и `Stepik_course/practice/quickstart.ipynb`; сохранены зависимости по относительным путям. Оригинальный аудиторский checkout не удалялся.
