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

Если отсутствует модуль создания venv, установите пакет `python3-venv` средствами своей Linux-системы. Установщик не запрашивает права администратора и не изменяет системный Python. На Windows профиль `quantum` не предлагается: для PySCF предусмотрен Linux/WSL.

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
