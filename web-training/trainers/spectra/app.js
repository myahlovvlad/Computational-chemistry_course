'use strict';
const ids=['energy','sigma','concentration','length','stray'];
function model(p){
  for(const id of ids)if(!Number.isFinite(p[id]))throw Error('Неконечный параметр '+id);
  if(p.energy<2||p.energy>6||p.sigma<.03||p.sigma>.5||p.concentration<0||p.concentration>400||p.length<.1||p.length>2||p.stray<0||p.stray>.02)throw Error('Параметры вне области учебной модели');
  const ideal=10000*p.concentration*1e-6*p.length;
  return {kind:'simulation',parameters:p,wavelength_nm:1239.8419843320026/p.energy,
    FWHM_eV:2*Math.sqrt(2*Math.log(2))*p.sigma,ideal_A:ideal,
    observed_A:-Math.log10((10**(-ideal)+p.stray)/(1+p.stray)),
    limitations:'Independent Gaussian and concentration controls; no measured drug spectrum or calibrated epsilon'};
}
function current(){return model(Object.fromEntries(ids.map(id=>[id,Number(document.getElementById(id).value)])));}
function render(){
  const result=current(),p=result.parameters,max=1/(p.sigma*Math.sqrt(2*Math.PI));
  const points=Array.from({length:501},(_,i)=>{
    const e=i*8/500,y=Math.exp(-.5*((e-p.energy)/p.sigma)**2)/(p.sigma*Math.sqrt(2*Math.PI));
    return `${50+e*90},${250-y/max*210}`;
  }).join(' ');
  // Numeric model values only enter SVG; learner prose is always textContent.
  document.getElementById('plot').innerHTML=`<path d="M50 20V250H780" stroke="#687777" fill="none"/><polyline points="${points}" fill="none" stroke="#087d78" stroke-width="3"/><text x="350" y="290">Energy / eV (0–8)</text><text x="60" y="25">Relative Gaussian density; peak ${max.toFixed(3)} eV⁻¹</text>`;
  document.getElementById('result').textContent=`E₀ ${p.energy.toFixed(2)} eV · λ₀ ${result.wavelength_nm.toFixed(2)} nm · FWHM ${result.FWHM_eV.toFixed(3)} eV · c ${p.concentration} μmol/L · l ${p.length} cm · s ${p.stray} · A ideal ${result.ideal_A.toFixed(3)} · A observed ${result.observed_A.toFixed(3)}`;
}
ids.forEach(id=>document.getElementById(id).addEventListener('input',render));
document.getElementById('export').addEventListener('click',()=>{
  const record={schema_version:1,id:crypto.randomUUID(),created_utc:new Date().toISOString(),lesson_id:'M08-L02',...current(),
    hypothesis:document.getElementById('hypothesis').value,decision:document.getElementById('decision').value,scientific_review:'NOT_RUN'};
  const url=URL.createObjectURL(new Blob([JSON.stringify(record,null,2)],{type:'application/json'}));
  const a=document.createElement('a');a.href=url;a.download=`spectral-evidence-${record.id}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  document.getElementById('message').textContent='Создана новая версия. Сохраните файл в своём досье; аргумент требует оценки преподавателя.';
});
window.spectralModel={model,current};render();
