# Вычислительные протоколы и область допуска

Все исследования сохраняют исходную форму, заряд, source SHA, версии, протокол, точную команду и неизменяемые результаты. Исследовательский расчёт выполняется из IDE/CLI; повторный анализ готового результата в Notebook обозначается отдельно. PASS исполнения, проверка минимума, численная сходимость, научная рецензия и экспериментальная валидация — разные статусы.

`research-quantum*.json` задают полные молекулярные DFT/TDDFT маршруты PySCF, с дисперсией и явно выбранным растворителем. `scripts/run_research_quantum.py` использует density fitting; при закреплённой версии PySCF auxiliary basis выбирается библиотекой для AO basis. Точный выбор и расчётные настройки доступны в логах. Проверка чувствительности auxiliary/AO basis требует отдельного исследования; факт RI/DF не скрывается. [Документация DF](https://pyscf.org/user/df.html).

Legacy-имя `density_tolerance` в этих JSON передаётся в PySCF `conv_tol_grad`: это допуск **SCF orbital gradient**, не норма изменения density matrix. `gradient_rms_hartree_bohr` и `gradient_max_hartree_bohr` относятся к ядерным градиентам и в критерии приёмки используют нормы векторов по атомам. Предварительная callback-колонка `gradient_rms` усредняет декартовы компоненты; её нельзя напрямую сравнивать с vector-RMS критерием. Независимая финальная проверка использует правильные атомные нормы.

SMD и C-PCM сохраняются как разные методы. Неудачные SMD-попытки не превращаются в успешный C-PCM результат под прежним названием. C-PCM не включает все SMD CDS/nonpolar contributions. Геометрическая сходимость не подтверждает минимум: требуются Hessian и все положительные внутренние частоты. Проверяются также сетки DFT и поверхности растворителя. RRHO при 1 atm не объявляется solution free energy без обработки standard state/low modes. Энергии кислоты, аниона и лактона нельзя непосредственно сравнивать без сбалансированной реакции/модели химических потенциалов.

`conformer-gfn2-alpb.json` — отдельный предварительный электронноструктурный маршрут. Три ETKDGv3 seed по 100 целых молекул проходят MMFF94s и 300 GFN2-xTB singlepoints в ALPB-water. После re-ranking выбранные разнообразные структуры оптимизируются; для трёх низкоэнергетических конформеров рассчитываются численные Hessian. Отбор по конечному бюджету/energy window не доказывает полноту поиска или глобальный минимум.

xTB 6.8.0 устанавливается локально `python scripts/setup_xtb.py`; официальный бинарный архив и executable проверяются SHA256. Windows и Linux installer проверены фактически; на Linux независимо выполнен полный поиск истрадефиллина. Остальные маршруты должны подтверждаться собственным запуском. Установка не меняет системный PATH. Основная Python-среда остаётся закреплённой uv chem. [Официальный выпуск](https://github.com/grimme-lab/xtb/releases/tag/v6.8.0), [оптимизация](https://xtb-docs.readthedocs.io/en/latest/optimization.html), [ALPB и reference states](https://xtb-docs.readthedocs.io/en/latest/gbsa.html), [Hessian](https://xtb-docs.readthedocs.io/en/latest/hessian.html).

В ALPB выбран `gsolv` reference state; стандартная смена 1 bar→1 M не подразумевается. В GFN2 считаются valence electrons; это отличается от all-electron счёта PySCF. Проверяются валентный электронный счёт, spin, сумма зарядов и сохранение connectivity/protonation/stereochemistry после оптимизации. Самостоятельный mass-weighted SVD удаляет жёсткие translation/rotation степени свободы из Hessian; отрицательные внутренние частоты не обрезаются. Дополнительная сверка с native frequencies учитывает явно названную mass basis.

GFN2/ALPB minimum не считается DFT minimum. Изменение ранга MMFF→GFN2/ALPB совмещает смену Hamiltonian и среды; чистый solvent effect требует парного сравнения при одном методе и одной геометрии. Electronic/ALPB energy не равна полной conformer free energy. Неполный набор Hessian и неопределённость низких частот не позволяют заявлять измеренные populations. Native thermochemistry сохраняется с её условиями и ограничениями.

Большие PySCF checkpoint и xTB restart-кэши остаются локально; геометрии, логи, параметрические файлы, Hessian и receipts сохраняются как доказательства. Чужие исходные результаты не перезаписываются ради прохождения gates.

## Вертикальный CAM-B3LYP//GFN2

`uv-cam-gfn2-water.json` фиксирует CAM-B3LYP/def2-TZVP, density fitting, grid 4, C-PCM water (eps 78.3553; optical 1.78), 30 полных singlet TDDFT states с неравновесным откликом. Исходная геометрия — Hessian-проверенный минимум GFN2/ALPB, не DFT-минимум. [PySCF solvent documentation](https://pyscf.org/user/solvent.html) и [API optical response](https://pyscf.org/pyscf_api_docs/pyscf.solvent.html) определяют выбранный отклик; параметры заданы явно.

Первый Windows запуск остановлен ENOSPC во временных DF/RSH интегралах при 1012 AO. Его frozen runner и input protocol сохранены отдельно. Новый runner до SCF требует консервативный резерв 50 GiB на scratch volume и допускает `--scratch`; текущий preflight BLOCKED при ≈17 GiB. Этот резерв — operational safeguard, а не выведенная точная оценка памяти. Basis/functional не меняются ради запуска. Завершённый H2O installation check подтверждает работу native API, но не является расчётом или валидацией лекарства.


## Контроль воспроизводимости поиска и движка

Новый Linux search A завершён отдельно от Windows. Исходники/формы/протоколы совпали по SHA, но конечный basin-set audit имеет REVIEW: 7/10 назначений проходят одновременно RMSD ≤0.1 Å и |ΔE| ≤1e-5 Eh. Эти заранее записанные допуски не расширялись. У 20/300 same-ID начальных MMFF-refined структур RMSD >0.01 Å; максимум 1.839 Å. Это свидетельство чувствительности всего вычислительного пути, а не доказательство единственной причины расхождений.

Десять исходных XYZ Windows скопированы побайтово и отдельно рассчитаны обоими бинарниками xTB 6.8.0 (OpenBLAS/MKL), при accuracy 0.01, tight ALPB grid и одном потоке. Max |ΔE| = 1.009e-12 Eh при заранее заданном допуске 1e-6 Eh: fixed-geometry engine check PASS. Энергии геометрически несопоставленных бассейнов не используются как оценка numerical error. Первичный REVIEW, все новые входы/результаты и диагностический исходник сохранены; полнота ансамбля и тонкий порядок остаются непроверенными.


## Проверенный маршрут HDF5 без потери данных

`uv-cam-gfn2-water-lossless.json` сохраняет functional, orbital/auxiliary basis, grid, dielectric response, 30 состояний и convergence thresholds исходного протокола. Изменяется хранение временных интегралов: gzip level 1, shuffle, Fletcher32, float64 без округления. Процессовый context действует только на собственную scratch-папку; после выхода оригинальные функции h5py восстанавливаются. Guard проверяет свободное место перед записью и останавливает попытку при резерве <4 GiB. Начальные 16 GiB — operational entry threshold, не гарантия достаточности места и не смягчение научного допуска.

Контроль `scripts/check_lossless_quantum.py` выполнил настоящие disk-backed H2O CAM-B3LYP/def2-TZVP/C-PCM SCF и три TDDFT состояния в обоих вариантах IO: DF matrices совпали побитово, ΔSCF=0, max Δexcitation=0; файл уменьшился 1715448→922294 bytes. Это контроль хранения, не валидация лекарства. `scripts/check_lossless_guard.py` проверяет отказ при недостатке места, неизменность файлов за пределами заданной папки, bitwise roundtrip и восстановление API после исключения. В обычном chem-профиле эти необязательные проверки не запускаются; нужен quantum-core/quantum.

`scripts/analyze_electronic_checkpoint.py --run <завершённый-run> --out <новый-каталог>` независимо проверяет Tr(DS), C†SC, closed-shell idempotency, геометрию checkpoint и норму TDDFT 2(||X||²−||Y||²)=1; затем восстанавливает length/velocity oscillator strengths. Он сохраняет полные X/Y и MO vectors. X-only SVD character соответствует явно указанной CIS-like интерпретации; это не полный transition-density NTO анализ. Нативный PySCF get_nto игнорирует Y и нормализует X in-place, поэтому наш анализ работает с новой копией X и отдельно сообщает норму Y. Orbital gap не объявляется optical gap; SCF stability и независимая спектральная валидация остаются отдельными задачами.

Контроль анализа выполнен на реальном H2O checkpoint; намеренная подмена числа электронов отвергнута. Для целевого расчёта создан неизменяемый postprocess plan: анализ запускается только при наличии завершённого numerical PASS. Отсутствующий или оборванный спектр не заменяется контрольными значениями. Checkpoint/временные большие тензоры остаются локально; frozen sources, параметры и receipts сохраняются в evidence.
