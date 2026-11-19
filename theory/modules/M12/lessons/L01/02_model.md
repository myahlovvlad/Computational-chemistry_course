# Модель, курация и выбор без утечки

pKi=−log₁₀(Ki / mol L⁻¹)=9−log₁₀(Ki/nM). pIC50 не равен pKi без дополнительной физической модели и условий assay. Куратор исключает censored relation, validity/duplicate flags, мутантные мишени и многокомпонентные графы. Повторные точные изомерные графы агрегируются медианой только при разбросе ≤1 log. Смешение assay остаётся источником систематического смещения.

4546 структур A2A разделены на train 2848, calibration 844 и test 854 с непересекающимися Murcko-каркасами. Каркасы истрадефиллина/кофеина принудительно отнесены в test. Внутри training: outer 5-fold оценивает процедуру выбора, inner 3-fold выбирает Ridge или RF. Ridge использует 11 нормированных дескрипторов и alpha∈{0.01,0.1,1,10,100}; RF — Morgan radius 2, 2048 bits, chirality, 1000 деревьев, max_features=.33, min_samples_leaf=2. Нормирование не видит validation/test.

RMSE=√mean((ŷ−y)²), MAE=mean|ŷ−y|. Baseline использует только среднее training. Тест открывается после выбора модели. Групповой bootstrap выбирает целые тестовые каркасы с возвращением; интервалы отражают изменчивость по этим каркасам, но не устраняют assay bias, ошибки курации и временной сдвиг.

Источники методов и данных: [ChEMBL API](https://www.ebi.ac.uk/chembl/api/data/docs), [GroupKFold](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html). Код `scripts/fetch_target_qsar.py` и `scripts/train_target_qsar.py` фиксирует точные версии и операции; первичные HTTP-ответы и SHA сохраняются в evidence.
