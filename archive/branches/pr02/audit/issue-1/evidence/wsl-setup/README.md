# Дополнительный WSL/uv прогон 17.11.2026

Установка выполнена по явному запросу владельца ПК. Windows WSL обновлён до 3.0.5, официальный MSI x64:

`https://github.com/microsoft/WSL/releases/download/3.0.5/wsl.3.0.5.0.x64.msi`

SHA256 `2313efc5873e3f8552f42e77f950fabd913c0289078fa89d2100f3421a525eaa`, Authenticode Valid, Microsoft Corporation. Установка `msiexec /i <msi> /qn /norestart /L*v <local-log>` завершилась exit 0. Компоненты Microsoft-Windows-Subsystem-Linux и VirtualMachinePlatform уже были включены; RestartNeeded false. Автоматической перезагрузки не выполнялось. Подробные системные MSI/UAC логи оставлены локально, чтобы не публиковать сведения компьютера.

Дистрибутив: `wsl.exe --install -d Ubuntu-24.04 --no-launch --web-download`. Создан пользователь miakhlov без заданного агентом пароля, Python 3.12 и системные зависимости. Для административной работы пользователь может задать свой Linux-пароль самостоятельно; расчётам он не нужен. Исходный автоматически назначенный WSL DNS не отвечал. Сохранён `/etc/resolv.conf.course-original`, в WSL указан работающий DNS текущего Windows Ethernet; VPN/Windows firewall не отключались. При смене сети эту локальную настройку может потребоваться обновить.

`uv` установлен официальным Linux installer Astral (`https://astral.sh/uv/install.sh`), наблюдаемая версия 0.13.8. В checkout базового commit выполнены `uv lock`, `uv sync --frozen`, регистрация ядра через `uv run --frozen python tools/register_uv_kernel.py`. Проектный pyproject и полный lock сохранены рядом. Внешний Linux Vina 1.2.7 взят из официального релиза; SHA256 и `--version` находятся в `../wsl-linux/vina-version/`.

Первая попытка harness остановилась при сборе freeze: в uv venv нет pip. Не доустанавливался pip ради этой команды; collector исправлен на `uv pip freeze --python <interpreter>`. Исходные stdout/stderr и driver-result сохранены рядом как `first-attempt-*`. Повтор выполнен в новый каталог `/home/miakhlov/course-evidence-linux-02`; `driver-run.json` фиксирует точную команду WSL. `retry-linux.sh` показывает точный запуск uv и Linux runner. Нет подстановки прежних notebook outputs.

В `../wsl-linux/` сохранены новая среда, lock-derived freeze, исходные SHA256, 16 исполненных notebooks, 25 существующих unit tests, неизменённая PySCF-вставка и фактические outputs всех лабораторных. Kernel `chemistry-course-uv` запускается через uv. Основные исходные notebooks на момент полного прогона были из base commit; kernel выбирался runner явно. Отдельная проверка метаданных и автоматического выбора ядра выполнена в companion ветке настройки среды.

После аудита по дополнительному запросу создана самостоятельная учебная копия `/home/miakhlov/course-notebooks` с собственной uv `.venv`. Регистрация именованного ядра перенесена на неё; историческое место исполнения аудита и его логи сохраняются. Для повторения аудита из прежнего checkout сначала заново зарегистрировать ядро для него или использовать отдельное имя.

Официальные инструкции: [Microsoft WSL](https://learn.microsoft.com/en-us/windows/wsl/install), [PySCF](https://pyscf.org/user/install.html), [uv/Jupyter](https://docs.astral.sh/uv/guides/integration/jupyter/).
