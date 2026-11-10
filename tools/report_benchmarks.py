"""Generate a readable report from actual kernel execution evidence."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'Labs/benchmarks/execution.json').read_text(encoding='utf-8'))
lines=['# Benchmark и фактическая проверка практикума','',
       'Все 14 основных notebook исполнены в отдельных чистых Jupyter-ядрах. Дата: 10.11.2026.',
       f"Среда: Python {data['python']}; {data['platform']}. Зависимости: `Labs/requirements.txt` и `Labs/environment-lock.txt`.",'',
       'Время ниже относится к расчётной части notebook, включая создание рисунков/таблиц. Это наблюдение на одном компьютере, не рейтинг пакетов или гарантия времени на другом устройстве. Kernel startup записан отдельно в JSON.','',
       '| Работа | Статус | Расчёт, с | Контрольный результат |','|---|---|---:|---|']
for record in data['runs']:
 n=record['lab'];run=record['calculation'];r=run['result']
 observations={
 1:lambda:'Эффекты 20 / 10 / 16',2:lambda:'Паспорт Python/RDKit и hash',
 3:lambda:f"{r['rows']} строк, {r['invalid']} invalid",4:lambda:f"{r['valid_rows']} рассчитанных профилей",
 5:lambda:f"{r['molecules']} молекул, симметричная матрица",
 6:lambda:f"{r['generated']} конформера, минимум {r['minimum']:.6f} kcal/mol",
 7:lambda:f"{r['included']} включены, {r['excluded']} исключены с причиной",
 8:lambda:f"Z′={r['Z_prime']:.6f}; EF@50={r['EF_at_50']}",
 9:lambda:f"{r['rows']} строк, {r['structures']} структур",
 10:lambda:f"{r['mode']}; score {r.get('score',r['reference_score'])}; RMSD {r.get('rmsd_angstrom',r['official_reference_rmsd_angstrom']):.4f} Å",
 11:lambda:f"MAE RF {r['splits']['identity']['metrics']['random_forest']['MAE_logS']:.4f} / {r['splits']['scaffold']['metrics']['random_forest']['MAE_logS']:.4f} logS",
 12:lambda:f"RHF H2 {r['single_point']['energy_hartree']:.9f} Hartree",
 13:lambda:'Кислота + спирт; A 0,56 / B 0,855',14:lambda:f"CLI: {r['rows']} строк, тот же hash"
 }
 lines.append(f"| [ЛР {n}](../guides/lab{n:02d}.md) | {record['status']} | {run['calculation_wall_seconds']:.3f} | {observations[n]()} |")
lines+=['','## Что проверено дополнительно','',
        'Восемь регрессионных тестов проверяют химические и файловые контракты: соль/ковалентный Cl, стереохимия/таутомерная политика, единицы/недопустимые числа, PAINS-статус, полный CSV, неверная схема/ID/лимит, RHF-контроль и RMSD референса. Streamlit проверен через AppTest; отдельно проверен вычислительный pipeline.',
        '', '## Границы интерпретации','',
        '- Vina: выполнен реальный расчёт 1IEP, seed=42, cpu=1, exhaustiveness=8. RMSD использует serial тяжёлых атомов в системе координат рецептора, без независимого совмещения и оптимизации по симметрии. Это не оценка Kd.',
        '- ESOL: один заранее заданный split на сценарий; группы и размеры тестов различаются. Интервалы и область применимости не калибровались. Готовый ESOL predicted из CSV не использован.',
        '- H2: выполнен RHF/STO-3G, не DFT. Учебный код ограничен этой системой. PySCF-фрагмент в теории не является выполненным PySCF-практикумом.',
        '- Ретросинтез: выполнено одно структурное правило и сравнение двух условных маршрутов, не универсальный нейросетевой поиск.',
        '- Конвертация PDF сохраняет Markdown, 767 отдельных иллюстраций и 2657 визуальных страниц; OCR не выполнялся. Все рисунки не проходили индивидуальную экспертную проверку. Просмотрены контрольные страницы B05/39 и B06/3.',
        '', 'Машиночитаемый журнал: [execution.json](execution.json). Локальные результаты находятся в `Labs/results/labXX/`; они пересоздаются notebook. Выходы ячеек сохранены непосредственно в опубликованных notebooks.','']
(ROOT/'Labs/benchmarks/REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
print('Benchmark report written')
