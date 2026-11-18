# Воспроизведение аудита Issue #1

Исходный commit: `75e9e8606972f49f9a380588ee9c1db1c10d90fa`. [Основной отчёт](../../PRACTICE_AUDIT_REPORT.md). Команды выполняются из корня репозитория, Windows PowerShell, Python 3.12.

## Сохранённый прогон

`evidence/*/run.json` — точные argv, cwd, время, exit/status и входные SHA256. stdout/stderr лежат рядом. `results.json` содержит более узкие проверки; статус оболочки 0 не заменяет контрактный статус. Например, `18-gui` имеет exit code 0 и FAIL наблюдения. Перед новым notebook execution старые outputs очищены; исполненные копии сохранены в `evidence/lab-XX/executed.ipynb` и `10-quickstart`.

`source-inventory.json` сохраняет хеши исходного checkout. `file-manifest.json` фиксирует хеши файлов аудита (кроме самого manifest и результата его валидации). В `13-artifacts/labs-results/` сохранены свежие CSV/JSON/SDF/рисунки/HTML, Vina позы и полный лог. Это outputs reference, не ответы учащихся.

Ошибочные попытки harness `06-esol-evidence` и `07-module-snippets` сохранены неизменно. Исправленные повторы: `06-esol-evidence-retry`, `07-module-examples`. При новом прогоне исправленный collector использует `06-esol-evidence` в новом output root.

## Новый прогон без перезаписи доказательств

Создать отдельный checkout этой ветки. `.venv-audit` должна отсутствовать. Задать новый каталог результатов; не удалять исходные evidence:

```powershell
$env:PRACTICE_AUDIT_OUTPUT = Join-Path (Get-Location) 'tmp/audit-replay-01'
python audit/issue-1/run_checks.py --phase core
python audit/issue-1/run_checks.py --phase labs --vina 'C:\absolute\path\vina_1.2.7_win.exe'
python audit/issue-1/run_checks.py --phase supplemental
```

Бинарник Vina не включён в Git. Проверенный Windows v1.2.7 SHA256: `e0c4b2715e0c1a74f6e92d0f3be0328ac97542eafbc111e6b1efad897a73cce5`. Без `--vina` анализ подготовленного выхода не считается исполнением Vina; проверка режима в artifacts это обнаружит. Источник бинарника и его версия сохранены в `12-vina-provenance`.

Все child commands используют новую `.venv-audit`. Versions фиксируются отдельно до/после установки Labs. Датасеты берутся из репозитория; ESOL provenance дополнительно сверяется с upstream, поэтому нужна сеть. Результаты Labs пишутся в игнорируемый `Labs/results/`, затем копируются в выбранный evidence root.

Collector отказывается перезаписывать `run.json`. Для новых попыток использовать другой output root и чистую venv/checkout. На Linux путь Python в collector поддерживается, но Windows Vina provenance helper рассчитан на `.exe`; Linux/WSL запуск должен использовать отдельный Linux runner и `vina` в PATH.

## Реестр и целостность

Генератор читает сохранённые evidence исходного аудита. Новый replay не подменяет их автоматически:

```powershell
Remove-Item Env:PRACTICE_AUDIT_OUTPUT -ErrorAction SilentlyContinue
python audit/issue-1/build_registry.py
python audit/issue-1/validate_audit.py
```

`build_registry.py` не выполняет задания. Он извлекает явные действия и связывает их с конкретным запуском/подпроверкой. При изменении учебных текстов требуется ручная проверка полноты extractor и новый snapshot. PASS ограничен `status_scope`; перенос/объяснение/рубрика не наследуют PASS reference. Изменения collector после исходных запусков касаются повторяемости и не означают нового исполнения сохранённых результатов.

Для запуска notebook вручную в VS Code выбрать интерпретатор `.venv-audit/Scripts/python.exe`. Полный дополнительный Linux/uv прогон, включая PySCF, находится в `evidence/wsl-linux`; установка и команды — в [wsl-setup](evidence/wsl-setup/README.md). Установка редактора или пакета не является выполнением задания.
