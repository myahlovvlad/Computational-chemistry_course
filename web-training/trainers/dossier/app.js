'use strict';
const KEY='chemistry-research-dossier-v1';
const kinds=new Set(['measured','literature','calculated','simulation','hypothesis']);
let state={schema_version:1,versions:[]};
let unreadable=null;
function validateMap(map){
  if(!map||!Array.isArray(map.nodes)||!Array.isArray(map.edges))throw Error('Нужны nodes и edges');
  const ids=map.nodes.map(n=>n.id);
  if(ids.some(id=>typeof id!=='string'||!id.trim())||new Set(ids).size!==ids.length)throw Error('ID узлов должны быть непустыми и уникальными');
  const known=new Set(ids);
  for(const e of map.edges){
    if(!known.has(e.source)||!known.has(e.target))throw Error('Ребро ссылается на неизвестный узел');
    for(const key of ['explanation','source_reference','limitation'])if(typeof e[key]!=='string'||!e[key].trim())throw Error('Для ребра нужно поле '+key);
  }
  return map;
}
function validateVersion(v){
  if(!v||typeof v.id!=='string'||!v.id.trim()||!kinds.has(v.kind)||typeof v.created_utc!=='string'||!Number.isFinite(Date.parse(v.created_utc)))throw Error('Неверный паспорт версии');
  for(const key of ['question','form','source','decision'])if(typeof v[key]!=='string'||!v[key].trim())throw Error('Заполните '+key);
  validateMap(v.concept_map);return v;
}
function load(value){
  if(!value||value.schema_version!==1||!Array.isArray(value.versions))throw Error('Неверная схема досье');
  value.versions.forEach(validateVersion);
  if(new Set(value.versions.map(v=>v.id)).size!==value.versions.length)throw Error('Повтор ID версии в импорте');
  return value;
}
function render(){
  const list=document.getElementById('history');list.replaceChildren();
  for(const v of state.versions){const li=document.createElement('li');li.textContent=`${v.created_utc} · ${v.kind} · ${v.question} · ${v.decision}`;list.append(li);}
}
try{const saved=localStorage.getItem(KEY);if(saved)state=load(JSON.parse(saved));}
catch(error){unreadable=localStorage.getItem(KEY);document.getElementById('status').textContent='Сохранённые данные не перезаписаны. Экспортируйте оригинал перед восстановлением: '+error.message;}
document.getElementById('save').addEventListener('click',()=>{
  try{
    if(unreadable!==null)throw Error('Хранилище повреждено; экспортируйте оригинал. Запись заблокирована для сохранения данных.');
    const v={id:crypto.randomUUID(),created_utc:new Date().toISOString(),scientific_review:'NOT_RUN',
      ...Object.fromEntries(['question','form','kind','source','decision'].map(id=>[id,document.getElementById(id).value])),concept_map:JSON.parse(document.getElementById('map').value)};
    validateVersion(v);const next={schema_version:1,versions:[...state.versions,v]};
    localStorage.setItem(KEY,JSON.stringify(next));state=next;render();document.getElementById('status').textContent='Добавлена версия '+v.id+'. Научное обоснование требует ручной оценки.';
  }catch(error){document.getElementById('status').textContent=error.message;}
});
document.getElementById('validate').addEventListener('click',()=>{
  const list=document.getElementById('edges');list.replaceChildren();
  try{
    const map=validateMap(JSON.parse(document.getElementById('map').value));
    for(const e of map.edges){const li=document.createElement('li');li.textContent=`${e.source} → ${e.target}: ${e.explanation}. Источник: ${e.source_reference}. Ограничение: ${e.limitation}`;list.append(li);}
    document.getElementById('map-status').textContent='Структура корректна. Смысл связей не оценён автоматически.';
  }catch(error){document.getElementById('map-status').textContent=error.message;}
});
document.getElementById('export').addEventListener('click',()=>{
  const url=URL.createObjectURL(new Blob([unreadable!==null?unreadable:JSON.stringify(state,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=(unreadable!==null?'original-damaged-dossier-':'research-dossier-')+crypto.randomUUID()+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
document.getElementById('import').addEventListener('change',async event=>{
  try{
    if(unreadable!==null)throw Error('Импорт заблокирован: сохранён повреждённый оригинал; сначала экспортируйте его.');
    const file=event.target.files[0];if(!file)return;
    const imported=load(JSON.parse(await file.text())),known=new Map(state.versions.map(v=>[v.id,v]));
    for(const v of imported.versions){
      if(known.has(v.id)&&JSON.stringify(known.get(v.id))!==JSON.stringify(v))throw Error('Конфликт существующей версии '+v.id+'; данные сохранены');
      known.set(v.id,v);
    }
    const next={schema_version:1,versions:[...known.values()]};localStorage.setItem(KEY,JSON.stringify(next));state=next;render();
    document.getElementById('import-status').textContent='Импорт добавлен; предыдущие версии сохранены.';
  }catch(error){document.getElementById('import-status').textContent='Импорт отклонён: '+error.message;}
});
window.dossierTools={validateMap,validateVersion,load,getState:()=>structuredClone(state)};render();
