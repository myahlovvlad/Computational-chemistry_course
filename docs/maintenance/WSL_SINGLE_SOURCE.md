# Одна папка курса в Windows и WSL

Единственный действующий репозиторий:

```text
C:\Users\Miakhlov\Documents\GitHub\Computational chemistry_course
```

В Ubuntu-24.04 он доступен по двум путям к одним и тем же файлам:

```text
/mnt/c/Users/Miakhlov/Documents/GitHub/Computational chemistry_course
/home/miakhlov/Computational-chemistry_course
```

Второй путь — символическая ссылка. Сохранение файла через любой из этих путей меняет один исходник. Рабочая ветка — `main`.

Откройте терминал WSL и выполните:

```bash
cd ~/Computational-chemistry_course
code .
```

В проводнике VS Code выберите **File → Open Folder** и укажите `/home/miakhlov/Computational-chemistry_course`. Начните с `README.md` и `programm/COURSE_BLUEPRINT.md`; уроки находятся в `theory/modules` и `practicuum/modules`.

Старые папки `course-*`, `M01-*`, `m01-issue4-evidence` и прежний Linux-клон выведены из работы. Их материалы, включая датасеты, журналы, checkpoint и Git-историю Linux-клона, сохранены в одном резервном архиве. Воспроизводимые установленные Python-окружения удалены; их список сохранён рядом с архивом в `omitted-environments.json`.

```text
/var/backups/computational-chemistry/retired-wsl-20261120/retired-wsl.tar.gz
```

Рядом находятся `manifest.json` с SHA-256 файлов и `receipt.json` с результатом проверки. Архив предназначен для восстановления отдельных исторических материалов; действующая программа курса находится в `main`. Не распаковывайте его в домашнюю папку как ещё одну рабочую редакцию.

Настройку Python выполняйте по `scripts/README.md`. Среды Windows и Linux имеют разные исполняемые файлы; общий исходный код курса не делает их взаимозаменяемыми.

Старые записи Jupyter, ссылавшиеся на удалённые рабочие папки, также убраны из списка ядер. Их настройки сохранены в `retired-kernels.json` рядом с резервным архивом. Для работы в WSL зарегистрируйте ядра заново по инструкции настройки среды.
