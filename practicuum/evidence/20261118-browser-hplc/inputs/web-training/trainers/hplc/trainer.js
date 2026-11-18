/* Математика прозрачна: два эмпирических отклика и отдельная учебная форма сигнала. */
const model=window.HPLC_MODEL;
const byId=id=>document.getElementById(id);
const numeric=id=>Number(byId(id).value);
let lastResult=null;
function predict(acn,temperature,flow){
  const [a,b,c]=[acn,temperature,flow].map((value,i)=>(value-model.center[i])/model.scale[i]);
  const terms=[1,a,b,c,a*b,a*c,b*c,a*a,b*b,c*c];
  return [0,1].map(j=>terms.reduce((sum,value,i)=>sum+value*model.coefficients[i][j],0));
}
function line(points,color){
  return `<polyline points="${points}" fill="none" stroke="${color}" stroke-width="2.5"/>`;
}
function update(){
  for(const id of ['acn','temperature','flow','width'])byId(id+'-value').textContent=byId(id).value;
  const conditions={acn_percent:numeric('acn'),temperature_C:numeric('temperature'),flow_mL_min:numeric('flow'),
     pH:numeric('ph'),elution:byId('elution').value,column:byId('column').value};
  const inBox=conditions.acn_percent>=60&&conditions.acn_percent<=70&&conditions.temperature_C>=30&&conditions.temperature_C<=40&&conditions.flow_mL_min>=.8&&conditions.flow_mL_min<=1.2;
  const supported=inBox&&conditions.pH===4.6&&conditions.elution==='isocratic'&&conditions.column==='source';
  byId('status-panel').classList.toggle('blocked',!supported);
  byId('domain').textContent=supported?'В пределах диапазонов опубликованного плана; это ещё не независимая проверка прогноза.':'OUT_OF_DOMAIN — для выбранного pH, колонки, режима или диапазона нет калибровочных данных. Нужен новый эксперимент; числа и график не выдаются.';
  lastResult={conditions,domain_status:supported?'WITHIN_FACTOR_BOX':'OUT_OF_DOMAIN',
    source_doi:model.source_doi,input_sha256:model.input_sha256,kind:'teaching model',
    learner_review:'NOT_RUN',real_experiment:'NOT_RUN'};
  byId('plot').hidden=!supported;
  if(!supported){byId('prediction').textContent='Прогноз недоступен.';byId('resolution').textContent='Rs не вычисляется.';return;}
  const [first,last]=predict(conditions.acn_percent,conditions.temperature_C,conditions.flow_mL_min);
  const annotations=Object.values(model.figure5_annotated_Rt_min);
  const fractions=annotations.map(t=>(t-annotations[0])/(annotations[3]-annotations[0]));
  const peaks=fractions.map(f=>first+f*(last-first));
  const width=numeric('width'),sigma=width/4;
  const rs=peaks.slice(1).map((t,i)=>2*(t-peaks[i])/(2*width));
  Object.assign(lastResult,{predicted_first_last_Rt_min:[first,last],conditional_peak_times_min:peaks,
    assumed_equal_baseline_width_min:width,conditional_Rs:rs,
    limitations:model.limitations,method_validated:false});
  byId('prediction').textContent=`Наша регрессия: p-ATO ${first.toFixed(3)} мин; лактон ${last.toFixed(3)} мин.`;
  byId('resolution').textContent=`Условные Rs соседей: ${rs.map(x=>x.toFixed(2)).join('; ')}. Это расчёт для заданных учебных ширин и допущений, не измеренные Rs.`;
  const maxT=Math.max(last+1.5,10),colors=['#22676f','#a36514','#6f458d','#b33e46'];
  let drawing='<path d="M60 20V280H980" fill="none" stroke="#687980"/>';
  for(let tick=0;tick<=maxT;tick+=2){const x=60+920*tick/maxT;drawing+=`<text x="${x}" y="307" text-anchor="middle" font-size="16">${tick}</text>`;}
  drawing+='<text x="510" y="327" text-anchor="middle" font-size="16">Время, мин</text><text x="65" y="17" font-size="15">Отклик, условные единицы</text>';
  peaks.forEach((mean,j)=>{
    const points=Array.from({length:1001},(_,i)=>{const t=maxT*i/1000,y=Math.exp(-.5*((t-mean)/sigma)**2);return `${60+920*t/maxT},${280-235*y}`;}).join(' ');
    drawing+=line(points,colors[j]);
  });
  byId('drawing').innerHTML=drawing;
}
document.querySelectorAll('input,select').forEach(element=>element.addEventListener('input',update));
byId('export').addEventListener('click',()=>{
  const result={...lastResult,hypothesis:byId('hypothesis').value,interpretation:byId('interpretation').value,
    exported_at:new Date().toISOString()};
  const url=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:'application/json'}));
  const anchor=document.createElement('a');anchor.href=url;anchor.download='chromatography_decision.json';anchor.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
  byId('save-status').textContent='Файл подготовлен; качество интерпретации требует обсуждения с преподавателем.';
});
byId('model-info').textContent=`20 строк, ранг ${model.rank}/10. Ошибка подгонки (RMSE): ${model.training_RMSE_min.map(x=>x.toFixed(3)).join(' и ')} мин. Это ошибка на обучающих данных, не независимая точность.`;
byId('observations').innerHTML=model.observations.map((r,i)=>`<tr><td>${i+1}</td><td>${r.acetonitrile_percent}</td><td>${r.column_temperature_C}</td><td>${r.flow_mL_min}</td><td>${r.retention_p_ATO_min}</td><td>${r.retention_ATO_lactone_min}</td></tr>`).join('');
window.courseHplc={predict,getResult:()=>lastResult};
update();
