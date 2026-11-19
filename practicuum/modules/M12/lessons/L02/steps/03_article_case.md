# M12. Статья, в которой лучший метод зависит от задачи

Модель A2A уже дала прогноз, но её химическая область требует review. Перед решением по лекарству проверим более общее утверждение: достаточно ли назвать модель графовой, чтобы считать её лучше? Читаем **Wu et al., MoleculeNet (2018), DOI 10.1039/C7SC02664A**, разделы о разбиении/метриках и **Table 3**. [Первичная статья](https://doi.org/10.1039/C7SC02664A), [доступный структурированный текст NCBI](https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/PMC5868307/unicode).

Локально сохранены три выбранные фактические строки, не полный текст и не вся таблица. [Паспорт и значения](../../../../../shared/data/article_reading/moleculenet_selected_results.json) содержат источник, Table ID и SHA исходного локального cache. В самой сводной строке нет всех определений target и неопределённости; это нужно проверить в полном тексте. Права статьи не меняются.

```python
import json
from course_support import DATA,workspace,write_json
article=json.loads((DATA/'article_reading/moleculenet_selected_results.json').read_text(encoding='utf-8'))
benchmark_audit=[]
for row in article['rows']:
    # Знак улучшения зависит от метрики: для ошибки меньше лучше, для AUC больше лучше.
    c=row['conventional_value'];g=row['graph_value']
    benefit=(g-c) if row['higher_is_better'] else (c-g)
    benchmark_audit.append({'dataset':row['dataset'],'metric':row['metric'],
        'graph_directional_benefit':benefit,'graph_better_in_this_row':benefit>0,
        'relative_error_reduction':None if row['higher_is_better'] else benefit/c})
display(benchmark_audit)
write_json(workspace('M12-L02','case')/'article_benchmark_audit.json',
           {'kind':'calculated','scope':'three published benchmark summary rows; no new training',
            'doi':article['doi'],'comparisons':benchmark_audit})
```

На выбранных строках один победитель не распространяется на все задачи. Относительное уменьшение RMSE осмысленно внутри одной строки; процентное изменение AUC не выдаём за уменьшение физической ошибки. Три специально выбранных примера не оценивают долю побед во всём benchmark. Сводка лучших моделей также не изолирует причинный эффект архитектуры.

Свяжите это с A2A: значение ошибки другой задачи не является независимой проверкой pKi, а scaffold split не устраняет любой assay/time shift. Перейдите к [мини-рецензии B](03_article_review.md), сохранив различие между опубликованной метрикой, нашим пересчётом и химическим выводом.
