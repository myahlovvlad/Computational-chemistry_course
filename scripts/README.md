# Рабочее окружение курса

Из корня новой рабочей копии выполните установщик. Требуется Python 3.12 x64 и доступ к источникам пакетов при первой установке. `uv` устанавливается локально, если ещё недоступен; зависимости закреплены в `environment/uv.lock`. Активация терминала перед каждым Notebook не нужна: его `kernelspec` указывает определённый профиль uv.

Windows PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/setup-windows.ps1 -Profile base
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/setup-windows.ps1 -Profile chem
```

Параметр `Bypass` действует только для этого процесса запуска сценария; постоянную политику выполнения менять не требуется.

Linux / Ubuntu в WSL:

```bash
bash scripts/setup-linux.sh base
bash scripts/setup-linux.sh chem
# Необязательный профиль для повторения тяжёлых квантовых расчётов:
bash scripts/setup-linux.sh quantum
```

Если отсутствует модуль создания venv, установите пакет `python3-venv` средствами своей Linux-системы. Установщик не запрашивает права администратора и не изменяет системный Python. На Windows доступен `powershell -File scripts/setup-windows.ps1 quantum-core`: закреплённый PySCF 2.15.1 использует официальный win_amd64 wheel. Профиль `quantum-core` включает SCF/TDDFT, но не dispersion и geometry optimizer; полный `quantum` и docking остаются Linux/WSL. Установка quantum-core и контрольный SCF/TDDFT выполнены под Windows. Дополнительная Linux-установка quantum-core отдельно NOT_RUN; полный Linux quantum уже используется в DFT-исследовании.

После установки откройте нужный Notebook в JupyterLab или VS Code. Указанное в нём ядро называется «Курс химии v2 · base · uv» для M01/M02 и «… chem …» для химических уроков. При первом открытии IDE может попросить выбрать уже зарегистрированное ядро; дальнейший запуск использует его. Ни один Notebook не устанавливает зависимости скрыто в середине расчёта.

Запуск JupyterLab из корня (Windows):

```powershell
./scripts/environment/.venv-base/Scripts/python.exe -m jupyterlab
```

Linux:

```bash
scripts/environment/.venv-base/bin/python -m jupyterlab
```

Вводный профиль не содержит RDKit. Химический профиль расширяет среду. Это отдельные окружения, а не обновление глобальных пакетов пользователя. При переносе репозитория в другую папку повторите установщик: абсолютные пути `kernelspec` должны соответствовать этой копии.

Результаты ученика сохраняются в `practicuum/workspace/`, общее досье — в `practicuum/workspace/my_research/`. Эти файлы исключены из Git; сохраните свою резервную копию. Автопрогон задаёт отдельный `COURSE_WORK_DIR` и не перезаписывает личную работу. Повторный запуск `init_dossier()` дописывает только отсутствующие разделы.

Программы и интерфейсы создаём в IDE: например, `web-training/projects/screening`. Notebook объясняет исследование и анализирует результаты, исходный код приложения остаётся обычными файлами проекта.

Служебные команды: `build_notebooks.py --only <ID>` собирает пару из явно названных MD; `run_course.py --only <ID> --out <новая-папка>` запускает её в отдельных ядрах и пишет доказательства. Успешный запуск пустой лабораторной не подтверждает решение её кейсов.


## Реальные конформеры и отдельный UV-протокол

`scripts/setup_xtb.py` устанавливает SHA-проверенный xTB 6.8.0 в локальный ignored bin. `run_conformer_research.py --name istradefylline --out <новый каталог>` выполняет полный новый поиск; `audit_conformer_numerics.py --run <run> --out <новый каталог>` проверяет solvent grid и Hessian step. Методика и ограничения — [протоколы](../practicuum/protocols/README.md). Локальные xTB-бинарники/restart cache не входят в пакет.

`run_vertical_tddft.py --out <новый каталог>` в quantum-core выполняет настоящий CAM-B3LYP/def2-TZVP//GFN2 вертикальный расчёт целой молекулы, C-PCM water с неравновесным откликом. Это отдельный составной протокол; статус DFT-оптимизации не заимствуется. До появления result.json завершение численных gates не подтверждено.


## Проверенный маршрут HDF5 без потери данных

`uv-cam-gfn2-water-lossless.json` сохраняет functional, orbital/auxiliary basis, grid, dielectric response, 30 состояний и convergence thresholds исходного протокола. Изменяется хранение временных интегралов: gzip level 1, shuffle, Fletcher32, float64 без округления. Процессовый context действует только на собственную scratch-папку; после выхода оригинальные функции h5py восстанавливаются. Guard проверяет свободное место перед записью и останавливает попытку при резерве <4 GiB. Начальные 16 GiB — operational entry threshold, не гарантия достаточности места и не смягчение научного допуска.

Контроль `scripts/check_lossless_quantum.py` выполнил настоящие disk-backed H2O CAM-B3LYP/def2-TZVP/C-PCM SCF и три TDDFT состояния в обоих вариантах IO: DF matrices совпали побитово, ΔSCF=0, max Δexcitation=0; файл уменьшился 1715448→922294 bytes. Это контроль хранения, не валидация лекарства. `scripts/check_lossless_guard.py` проверяет отказ при недостатке места, неизменность файлов за пределами заданной папки, bitwise roundtrip и восстановление API после исключения. В обычном chem-профиле эти необязательные проверки не запускаются; нужен quantum-core/quantum.

`scripts/analyze_electronic_checkpoint.py --run <завершённый-run> --out <новый-каталог>` независимо проверяет Tr(DS), C†SC, closed-shell idempotency, геометрию checkpoint и норму TDDFT 2(||X||²−||Y||²)=1; затем восстанавливает length/velocity oscillator strengths. Он сохраняет полные X/Y и MO vectors. X-only SVD character соответствует явно указанной CIS-like интерпретации; это не полный transition-density NTO анализ. Нативный PySCF get_nto игнорирует Y и нормализует X in-place, поэтому наш анализ работает с новой копией X и отдельно сообщает норму Y. Orbital gap не объявляется optical gap; SCF stability и независимая спектральная валидация остаются отдельными задачами.

Контроль анализа выполнен на реальном H2O checkpoint; намеренная подмена числа электронов отвергнута. Для целевого расчёта создан неизменяемый postprocess plan: анализ запускается только при наличии завершённого numerical PASS. Отсутствующий или оборванный спектр не заменяется контрольными значениями. Checkpoint/временные большие тензоры остаются локально; frozen sources, параметры и receipts сохраняются в evidence.
