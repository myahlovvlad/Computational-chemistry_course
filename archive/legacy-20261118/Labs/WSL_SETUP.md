# WSL 2: воспроизводимое окружение для всего практикума

Эта инструкция предназначена для локального прогона курса под Windows через WSL 2. Основные 14 лабораторных работ используют базовую среду Python 3.12 из `Labs/requirements.txt`. AutoDock Vina устанавливается как отдельный Linux-бинарник. Дополнительный PySCF/DFT-практикум разворачивается в отдельной среде, чтобы не смешивать тяжёлые научные зависимости с базовым контуром курса.

## 1. Установить WSL 2 и Ubuntu

Откройте PowerShell от имени администратора:

```powershell
wsl --update
wsl --list --online
wsl --install -d Ubuntu-24.04
```

После перезагрузки откройте Ubuntu и создайте Linux-пользователя. Проверьте из PowerShell:

```powershell
wsl --list --verbose
```

Для Ubuntu должен быть указан WSL version 2. Если имя `Ubuntu-24.04` отсутствует в списке доступных дистрибутивов, выберите актуальное имя Ubuntu из `wsl --list --online`.

## 2. Держать репозиторий в файловой системе Linux

Для Linux-инструментов не размещайте рабочую копию курса в `/mnt/c/...`. Создайте её в домашнем каталоге WSL:

```bash
sudo apt-get update
sudo apt-get install -y git curl ca-certificates

mkdir -p ~/src
cd ~/src
git clone https://github.com/myahlovvlad/Computational-chemistry_course.git
cd Computational-chemistry_course
```

Так Python, Git, Jupyter и научные библиотеки работают с Linux-файлами напрямую.

## 3. Автоматическая установка базового контура

Из корня репозитория:

```bash
bash tools/setup_wsl.sh
```

Скрипт:

1. устанавливает системные зависимости;
2. устанавливает `uv`;
3. устанавливает управляемый Python 3.12;
4. пересоздаёт `.venv-course`;
5. устанавливает строго закреплённые зависимости из `Labs/requirements.txt`;
6. регистрирует Jupyter kernel `course-chemistry`;
7. устанавливает AutoDock Vina 1.2.7 в `~/.local/bin/vina` для x86-64 или ARM64;
8. выполняет regression tests и `tools/validate_course.py`;
9. выполняет smoke-run ЛР 1.

После установки откройте новый терминал или выполните:

```bash
source ~/.bashrc
source .venv-course/bin/activate

python --version
which python
vina --version
```

Ожидается Python 3.12.x, Python из `.venv-course` и AutoDock Vina 1.2.7.

## 4. Проверить докинг и затем весь практикум

Сначала отдельно проверьте ЛР 10, чтобы убедиться, что notebook использует настоящий Linux-бинарник Vina, а не только сохранённый reference output:

```bash
.venv-course/bin/python tools/run_labs.py --only 10
cat Labs/results/lab10/docking.json
```

В `docking.json` поле `mode` должно быть `executed-vina`.

Затем выполните полный прогон:

```bash
.venv-course/bin/python -m unittest discover -s Labs -p test_labs.py -v
.venv-course/bin/python tools/validate_course.py
.venv-course/bin/python tools/run_labs.py
```

Или выполните установку и полный прогон одной командой:

```bash
bash tools/setup_wsl.sh --run-all
```

`tools/run_labs.py` запускает каждую лабораторную работу в новом Jupyter kernel и записывает фактические результаты в `Labs/benchmarks/execution.json`.

## 5. Дополнительный PySCF/DFT-контур

Основная ЛР 12 не требует PySCF: в ней исполняется собственный RHF/STO-3G расчёт H2. Для дополнительного notebook `Labs/extensions/dft_pyscf.ipynb` создайте отдельную среду:

```bash
bash tools/setup_wsl.sh --with-pyscf
```

Будет создана `.venv-pyscf`, зарегистрирован kernel `course-pyscf` и выполнен `Labs/pyscf_dft.py`. Результат сохраняется в `Labs/results/dft/pyscf_dft.json`.

Разделение сред намеренное: базовый практикум остаётся воспроизводимым, а PySCF и будущие тяжёлые движки можно обновлять независимо.

## 6. VS Code и Jupyter

VS Code устанавливайте в Windows, а не внутрь WSL. Установите расширение WSL, затем из каталога курса в Ubuntu выполните:

```bash
code .
```

Для основных notebooks выбирайте интерпретатор `.venv-course/bin/python` или kernel `Chemistry course (WSL)`. Для PySCF-extension выбирайте `.venv-pyscf/bin/python` / `Chemistry course PySCF (WSL)`.

Отдельный JupyterLab для автоматического прогона не нужен: курс использует `nbclient`. Если нужен браузерный JupyterLab:

```bash
uv pip install --python .venv-course/bin/python jupyterlab
.venv-course/bin/python -m jupyter lab
```

## 7. Streamlit-финал

ЛР 14 и итоговый интерфейс:

```bash
.venv-course/bin/python -m streamlit run Labs/app.py
```

WSL обычно пробрасывает localhost в Windows, поэтому адрес, напечатанный Streamlit, открывается в Windows-браузере.

## 8. Почему не одна среда для всех будущих расширений

Текущие 14 основных ЛР должны воспроизводиться из одного `.venv-course`. Но дополнительные научные движки лучше изолировать. В частности, реальный AI-ретросинтез на AiZynthFinder следует добавлять отдельным environment: его зависимости не должны заставлять менять закреплённые версии NumPy/RDKit основного практикума. Текущая ЛР 13 использует прозрачный шаблонный ретросинтез и AiZynthFinder для неё не требуется.

## Диагностика

Если Vina не находится:

```bash
source ~/.bashrc
which vina
vina --version
```

Если runner не видит kernel:

```bash
.venv-course/bin/python -m ipykernel install \
  --prefix .venv-course \
  --name course-chemistry \
  --display-name "Chemistry course (WSL)"
```

Если базовая среда повреждена, не лечите её случайными `pip install -U`. Пересоздайте её из закреплённого файла:

```bash
rm -rf .venv-course
bash tools/setup_wsl.sh
```

## Контрольная точка готовности

Окружение считается готовым к системному тесту, если одновременно выполняются условия:

- regression tests проходят;
- `tools/validate_course.py` проходит;
- ЛР 10 пишет `mode: executed-vina`;
- `tools/run_labs.py` завершает все 14 notebooks без статуса `failed`;
- для PySCF-extension, если он входит в проверку, `Labs/results/dft/pyscf_dft.json` содержит `HF_converged: true` и `DFT_converged: true`.

Официальные справки: Microsoft WSL — https://learn.microsoft.com/windows/wsl/install; uv — https://docs.astral.sh/uv/getting-started/installation/; PySCF — https://pyscf.org/user/install.html; AutoDock Vina — https://github.com/forlilab/AutoDock-Vina/releases/tag/v1.2.7.
