"""Narrow formative feedback; never grades the scientific case or free explanation."""

ITEMS={
 'P04':{
  'correct':'B',
  'branches':{
   'A':'Проверьте знак: 10^-2 больше 10^-3. Вернитесь от logS к концентрациям и повторите сравнение.',
   'B':'Знак и кратность согласованы: прогноз выше в 10 раз. Теперь объясните, почему отрицательная logS не означает отрицательную концентрацию.',
   'C':'Нельзя трактовать разность logS как процент: сначала восстановите отношение 10^(predicted-measured).'}},
 'P06':{
  'correct':'C',
  'branches':{
   'A':'Среднее по пяти наблюдениям не ограничивает каждое. Проверьте отдельно остаток 5.',
   'B':'MAE не является вероятностью. Посчитайте долю удовлетворяющих условию отдельно от среднего.',
   'C':'Контрпример замечен. Объясните теперь, какое свойство выборки потерялось при усреднении.'}},
 'P09':{
  'correct':'A',
  'branches':{
   'A':'Граница данных сохранена: 25 °C можно задать для будущего опыта, но нельзя приписать архиву. Назовите ещё одну неизвестную переменную.',
   'B':'Обычное лабораторное условие не становится фактом о чужом измерении. Найдите в CSV поле температуры; если его нет, сохраните неизвестность.',
   'C':'Численное расхождение архивных столбцов остаётся вычислимым; неизвестная температура ограничивает причинное толкование, а не арифметику.'}}
}

def feedback(prompt_id,choice):
    item=ITEMS[prompt_id]
    if choice is None:return {'status':'NOT_RUN','scope':'one conceptual choice','message':'Сначала сформулируйте объяснение и выберите вариант.'}
    key=choice.strip().upper() if isinstance(choice,str) else ''
    if key not in item['branches']:
        return {'status':'RETRY','scope':'one conceptual choice','message':'Допустимы A, B или C; выбор не оценивает всю исследовательскую работу.'}
    return {'status':'COMPONENT_CORRECT' if key==item['correct'] else 'RECONSIDER',
            'scope':'one conceptual choice; free explanation and transfer not assessed',
            'message':item['branches'][key]}
