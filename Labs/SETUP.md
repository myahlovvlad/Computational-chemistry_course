# Установка и настройка рабочего окружения

Полный практикум рассчитан на **Ubuntu 24.04 в WSL 2, Python 3.12 и uv**. Для каждого из 14 модулей есть два notebook: разобранный пример и самостоятельные кейсы. Приложения разрабатываем в IDE. Ручная установка пакетов из ячеек не нужна.

## 1. На этом ПК: готовая учебная папка

В PowerShell:

```powershell
wsl -d Ubuntu-24.04 -u miakhlov
```

В открывшемся Linux-терминале:

```bash
cd /home/miakhlov/course-notebooks
uv sync --frozen
uv run --frozen python tools/register_uv_kernel.py
uv run --frozen python tools/preflight.py
bash tools/start_notebooks.sh
```

Откройте в Windows-браузере напечатанный JupyterLab адрес `http://localhost:…` с токеном. В каталоге `Labs/notebooks/` выбирайте `labXX.ipynb`, затем `labXX_practice.ipynb`. Ядро **Chemistry course (uv / WSL / Python 3.12)** само запускает проектную `.venv` через uv. Открытие документа выбирает ядро; вычисления начинаются после запуска ячейки. Если редактор запомнил другое ядро, один раз выберите правильное вручную.

Папка в Проводнике: `\\wsl.localhost\Ubuntu-24.04\home\miakhlov\course-notebooks`. Разработка идёт в Linux-среде; открытие UNC-пути обычным Windows Python не заменяет WSL-подключение IDE.

## 2. Установка с нуля на другом ПК

1. Установите WSL/Ubuntu из PowerShell администратора: `wsl --install -d Ubuntu-24.04`. Если Windows запросит перезагрузку, завершите её самостоятельно. Создайте своего Linux-пользователя. [Инструкция Microsoft](https://learn.microsoft.com/en-us/windows/wsl/install).
2. В Ubuntu установите системные зависимости:

```bash
sudo apt-get update
sudo apt-get install -y git curl ca-certificates python3.12-venv libgomp1
curl -LsSf https://astral.sh/uv/install.sh -o /tmp/uv-install.sh
sh /tmp/uv-install.sh
source "$HOME/.local/bin/env"
```

3. Получите проект. До слияния новой редакции используйте ветку `practice/paired-case-notebooks`:

```bash
git clone --branch practice/paired-case-notebooks https://github.com/myahlovvlad/Computational-chemistry_course.git
cd Computational-chemistry_course
uv sync --frozen
uv run --frozen python tools/register_uv_kernel.py
```

`uv.lock` фиксирует зависимости. Не выполняйте `uv lock --upgrade` перед воспроизведением контрольного расчёта: это отдельный эксперимент с другой средой. После переноса папки повторите регистрацию ядра, поскольку его user kernelspec содержит абсолютный путь checkout. [Документация uv/Jupyter](https://docs.astral.sh/uv/guides/integration/jupyter/).

## 3. Vina и PySCF

PySCF входит в uv lock и устанавливается в Linux-среду. [Native Windows не поддерживается PySCF](https://pyscf.org/user/install.html); отдельный Windows pip не решает эту проблему. В модуле 12 уже есть пакетный RHF/PBE, поэтому дополнительный старый DFT notebook не нужен для основного маршрута.

Vina — внешний бинарник, он не входит в Python venv. Для Linux x86_64:

```bash
mkdir -p "$HOME/.local/bin"
curl -fL https://github.com/forlilab/AutoDock-Vina/releases/download/v1.2.7/vina_1.2.7_linux_x86_64 -o "$HOME/.local/bin/vina"
chmod +x "$HOME/.local/bin/vina"
export PATH="$HOME/.local/bin:$PATH"
vina --version
sha256sum "$HOME/.local/bin/vina"
```

Используйте архитектуру своего ПК и [официальный релиз](https://github.com/forlilab/AutoDock-Vina/releases/tag/v1.2.7). Сохраните URL, дату, версию и наблюдаемый SHA256. `tools/preflight.py` проверяет доступность команды. Без Vina полный docking-кейс имеет BLOCKED; анализ готовой позы не считается новым запуском. Для новой подготовки из raw PDB понадобятся дополнительные инструменты и отдельная проверка протокола.

## 4. IDE для приложений

Рекомендуемый маршрут — VS Code с расширениями **WSL**, **Python**, **Jupyter**. Откройте Linux-папку из Ubuntu командой `code .` либо **WSL: Open Folder in WSL**. В левом нижнем углу должно быть подключение к Ubuntu. В **Python: Select Interpreter** выберите `${workspaceFolder}/.venv/bin/python`.

В терминале IDE проверьте:

```bash
uv run --frozen python -c "import sys; print(sys.executable)"
uv run --frozen python -m unittest discover -s Labs -p test_labs.py -v
```

Это должен быть тот же проектный Python, что выводит notebook. [Работа VS Code в WSL](https://code.visualstudio.com/docs/remote/wsl). Можно использовать другую IDE с WSL-интерпретатором; химический код и тесты остаются теми же. [Пошаговое задание для IDE](ide/README.md).

## 5. Проверка готовности и сохранение работы

```bash
uv run --frozen python tools/preflight.py
uv run --frozen python tools/validate_course.py
uv run --frozen python tools/run_labs.py --only 3
```

`run_labs.py` сохраняет исполненные копии в отдельный каталог, а не перезаписывает учебные notebooks. Самостоятельный notebook с `answer=None` исполняется как каркас, но все три задачи остаются NOT_RUN. Для авторской проверки численных эталонов применяется отдельный режим, не подставляющий ответы в студенческие файлы.

Сохраняйте свою копию notebook и артефакты в `student_work/`. Перед полным Restart & Run All убедитесь, что изменяли свою копию, а не стирали исходный разбор. Для сдачи нужны код, входы, параметры, фактический вывод и интерпретация, а для приложения — также файлы проекта и логи IDE/браузерных проверок.

## 6. Частые сбои

| Симптом | Диагностика и действие |
|---|---|
| `uv: command not found` | Откройте новый Linux-терминал или загрузите `$HOME/.local/bin/env`. |
| Пакет есть в терминале, но нет в notebook | Сравните `sys.executable`; переустановите регистрацию ядра через uv и перезапустите ядро. |
| Папка перенесена, ядро смотрит по старому пути | В новой папке выполните `uv sync --frozen` и `tools/register_uv_kernel.py`. |
| `vina` не найден | Проверьте PATH и права выполнения; не заменяйте новый расчёт сохранённым результатом. |
| Не скачиваются пакеты | Проверьте `getent hosts pypi.org`; в WSL возможна проблема DNS. Не отключайте firewall/VPN как универсальное решение; проверяйте настройки текущей сети. |
| Checker показывает NOT_RUN | Решение отсутствует либо требуется рецензия исследовательского/IDE-кейса. Это не ошибка установки. |
| PySCF в Windows не устанавливается | Откройте проект в Ubuntu/WSL и используйте Linux `.venv`. |
