async (page) => {
  // Проверка интерфейса: это не исследование студента и не валидация аналитического метода.
  const failures=[];
  const ensure=(condition,message)=>{if(!condition)failures.push(message);};
  await page.goto('http://127.0.0.1:8875/');
  const start=await page.evaluate(()=>window.courseHplc.getResult());
  ensure(start.domain_status==='WITHIN_FACTOR_BOX','Начальное условие должно входить в диапазон');
  ensure(Math.abs(start.predicted_first_last_Rt_min[0]-2.8410545454545453)<1e-10,'Первый отклик при центре');
  ensure(Math.abs(start.predicted_first_last_Rt_min[1]-7.268463636363636)<1e-10,'Последний отклик при центре');
  const optimum=await page.evaluate(()=>window.courseHplc.predict(61.93,31.44,1.03));
  ensure(Math.abs(optimum[0]-2.7929906681818175)<1e-8,'JS/NumPy: первый отклик');
  ensure(Math.abs(optimum[1]-7.184782540606061)<1e-8,'JS/NumPy: последний отклик');
  await page.getByRole('slider',{name:'Условная ширина у основания, мин:'}).press('End');
  const wider=await page.evaluate(()=>window.courseHplc.getResult());
  ensure(wider.conditional_Rs[1]<start.conditional_Rs[1],'Уширение должно уменьшать условный Rs');
  const blocked=[];
  for(const value of ['3','6']){
    await page.getByLabel('pH',{exact:true}).selectOption(value);
    const result=await page.evaluate(()=>window.courseHplc.getResult());
    ensure(result.domain_status==='OUT_OF_DOMAIN','Нет калибровки для pH '+value);
    ensure(!('predicted_first_last_Rt_min' in result),'Не должно оставаться старого прогноза');
    ensure(await page.locator('#plot').isHidden(),'График должен скрываться вне области');
    blocked.push(result);
  }
  await page.getByLabel('pH',{exact:true}).selectOption('4.6');
  await page.getByLabel('Элюирование',{exact:true}).selectOption('gradient');
  ensure((await page.evaluate(()=>window.courseHplc.getResult())).domain_status==='OUT_OF_DOMAIN','Нет калибровки градиента');
  await page.getByLabel('Элюирование',{exact:true}).selectOption('isocratic');
  await page.getByLabel('Колонка',{exact:true}).selectOption('other');
  ensure((await page.evaluate(()=>window.courseHplc.getResult())).domain_status==='OUT_OF_DOMAIN','Нет калибровки другой колонки');
  await page.reload();
  await page.getByLabel('Какое изменение должно улучшить разделение и почему?').fill('UI SMOKE TEST: not learner research');
  await page.getByLabel('Что поддерживает модель, что неизвестно, какие контроль и критерий вы выберете?').fill('UI SMOKE TEST: interpretation is not scientifically assessed');
  const downloadPromise=page.waitForEvent('download');
  await page.getByRole('button',{name:'Сохранить решение в досье JSON'}).click();
  const download=await downloadPromise;
  await download.saveAs('output/playwright/chromatography_decision-ui-smoke.json');
  await page.screenshot({path:'output/playwright/hplc-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  ensure(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),'Страница не должна прокручиваться по горизонтали на телефоне');
  await page.screenshot({path:'output/playwright/hplc-mobile.png',fullPage:true});
  await page.setViewportSize({width:1280,height:900});
  if(failures.length)throw new Error(JSON.stringify(failures));
  return {status:'PASS',scope:'UI smoke and numeric parity; not scientific validation or student pilot',
      browser:await page.context().browser().version(),start,optimum,wider,blocked,
      export_filename:download.suggestedFilename(),student_work:'NOT_RUN',method_validation:'NOT_RUN'};
}
