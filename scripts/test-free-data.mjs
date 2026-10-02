import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
await mkdir('.cache',{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROME_PATH||undefined,args:['--no-sandbox','--disable-dev-shm-usage','--no-zygote'],headless:true});
const context=await browser.newContext({viewport:{width:1460,height:980}});
const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
const year=new Date().getUTCFullYear()-(new Date().getUTCMonth()<6?1:0);
const pastDate=(month,day)=>`${year}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}`;
const upcoming=new Date();upcoming.setUTCDate(upcoming.getUTCDate()+10);const date=upcoming.toISOString().slice(0,10);
const rows=[
  {date:pastDate(8,1),team1:'Équipe Alpha',team2:'Équipe Gamma',score:{ft:[2,0]}},
  {date:pastDate(8,2),team1:'Équipe Gamma',team2:'Équipe Beta',score:{ft:[1,1]}},
  {date:pastDate(8,8),team1:'Équipe Alpha',team2:'Équipe Delta',score:{ft:[1,0]}},
  {date:pastDate(8,9),team1:'Équipe Delta',team2:'Équipe Beta',score:{ft:[2,1]}},
  {date:pastDate(8,15),team1:'Équipe Alpha',team2:'Équipe Beta',score:{ft:[1,1]}},
  {date,team1:'Équipe Alpha',team2:'Équipe Beta'},
];
const content=Buffer.from(JSON.stringify({name:'Calendrier synthétique de test',matches:rows})).toString('base64');let calls=0;
await context.route('https://api.github.com/repos/openfootball/football.json/**',async route=>{calls++;await route.fulfill({status:200,contentType:'application/json',headers:{'Access-Control-Allow-Origin':'*'},body:JSON.stringify(route.request().url().includes('/contents/')?{encoding:'base64',content}:[{commit:{committer:{date:new Date().toISOString()}}}])});});
try{
  await page.goto(process.env.TEST_BASE_URL||'http://127.0.0.1:5173',{waitUntil:'networkidle'});
  await page.locator('.heading-actions .online-open-button').click();
  await page.locator('.free-fixture-row').first().waitFor();
  assert.match(await page.locator('.free-data-metrics').innerText(),/6/);assert.match(await page.locator('.free-source-bottom').innerText(),/Données téléchargées/);
  const initialCalls = calls;
  await page.getByRole('button',{name:'Analyser',exact:true}).click();
  assert.equal(await page.getByRole('combobox',{name:'Mode du modèle',exact:true}).inputValue(),'goals');
  assert.equal(await page.getByRole('textbox',{name:'Équipe Alpha — Buts attendus (xG)',exact:true}).inputValue(),'');
  assert.equal(await page.getByRole('textbox',{name:'Équipe Alpha — Buts attendus (xG)',exact:true}).isDisabled(),true);
  assert.equal(await page.getByRole('textbox',{name:'Matchs utilisés · Équipe Alpha',exact:true}).inputValue(),'3');
  assert.match(await page.locator('.outcome-value').first().innerText(),/%/);console.log('PASS collecte → statistiques antérieures → prévisions sans xG');
  await page.getByRole('button',{name:'Enregistrer l’analyse',exact:true}).click();
  await page.waitForFunction(()=>JSON.parse(localStorage.getItem('matchlab:workspace:v1'))?.match?.modelMode==='goals');
  await page.reload({waitUntil:'networkidle'});assert.equal(await page.getByRole('combobox',{name:'Mode du modèle',exact:true}).inputValue(),'goals');console.log('PASS sauvegarde et restauration du mode gratuit');
  await page.locator('.heading-actions .online-open-button').click();await page.locator('.free-fixture-row').first().waitFor();assert.equal(calls,initialCalls);assert.match(await page.locator('.free-source-bottom').innerText(),/Cache local/);console.log('PASS cache anonyme, pas de requête inutile');
  await context.unrouteAll({behavior:'wait'});await context.route('https://api.github.com/**',route=>route.abort());
  await page.getByRole('button',{name:'Actualiser',exact:true}).click();await page.waitForFunction(()=>document.querySelector('.free-source-bottom').textContent.includes('Ancien cache'));
  assert.match(await page.locator('.main-content').innerText(),/anciennes données/i);console.log('PASS panne réseau : ancien cache explicitement signalé');
  await page.setViewportSize({width:390,height:844});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth),390);await page.screenshot({path:'.cache/free-data-mobile-test.png',fullPage:true});assert.deepEqual(errors,[]);console.log('PASS interface mobile et absence d’erreur JavaScript');
}finally{await browser.close();}
