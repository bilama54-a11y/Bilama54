import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

// Navigateur Playwright normal, ou binaire fourni par l’environnement de CI.
const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || undefined, args: ['--no-sandbox', '--disable-dev-shm-usage', '--no-zygote'], headless: true });
const context = await browser.newContext({ viewport: { width: 1460, height: 1050 }, acceptDownloads: true });
const page = await context.newPage();
const failures = []; const errors = [];
page.on('pageerror', error => errors.push(error.message));
page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
const base = process.env.TEST_BASE_URL || 'http://127.0.0.1:5173';
await fs.mkdir('.cache', { recursive: true });
async function check(name, action) { try { await action(); console.log(`PASS ${name}`); } catch (e) { failures.push(name); console.error(`FAIL ${name}: ${e.message}`); } }
try {
  await page.goto(base, { waitUntil: 'networkidle' });
  await check('tableau de bord et prédictions', async () => { assert.ok(await page.getByRole('heading', { name: 'Le match, sous un autre angle.' }).isVisible()); assert.equal(await page.locator('.outcome-value').count(), 4); assert.match(await page.locator('.outcome-value').first().innerText(), /%/); });
  await check('recalcul automatique avec décimales françaises', async () => { const before = await page.locator('.outcome-value').first().innerText(); await page.getByRole('textbox', { name: 'Arsenal — Buts attendus (xG)', exact: true }).fill('10,5'); await page.waitForFunction(old => document.querySelector('.outcome-value').textContent !== old, before); await page.getByRole('textbox', { name: 'Arsenal — Buts attendus (xG)', exact: true }).fill('8,5'); });
  await check('données manquantes : calcul en pause', async () => { const input = page.getByRole('textbox', { name: 'Arsenal — Buts attendus (xG)', exact: true }); await input.fill(''); assert.ok(await page.getByText('Calcul en pause.', { exact: true }).isVisible()); await input.fill('8,5'); });
  await check('confirmation du volume et historique persistant', async () => { await page.getByRole('checkbox', { name: 'J’ai vérifié le nombre de matchs et l’unité des xG.' }).check(); await page.getByRole('button', { name: 'Enregistrer l’analyse', exact: true }).click(); await page.waitForFunction(() => JSON.parse(localStorage.getItem('matchlab:workspace:v1')).history.length === 1); await page.getByRole('button', { name: /Mes analyses/ }).click(); assert.equal(await page.locator('.history-card').count(), 1); await page.getByRole('button', { name: 'Reprendre', exact: true }).click(); });
  let exported;
  await check('export JSON', async () => { const event = page.waitForEvent('download'); await page.getByRole('button', { name: 'Exporter', exact: true }).click(); const download = await event; await download.saveAs('.cache/analysis.json'); exported = JSON.parse(await fs.readFile('.cache/analysis.json', 'utf8')); assert.equal(exported.version, 1); assert.equal(exported.match.home.name, 'Arsenal'); });
  await check('comparateur NVSL sans probabilités inventées', async () => { await page.getByRole('button', { name: 'Comparateur de cotes', exact: true }).click(); await page.getByRole('button', { name: /Charger le coupon de la capture/ }).click(); assert.equal(await page.locator('.coupon-row').count(), 3); assert.match(await page.locator('.coupon-price').innerText(), /2,039/); assert.equal(await page.getByRole('textbox', { name: 'Probabilité — Total 90 — Nova Athletic', exact: true }).inputValue(), ''); assert.ok(await page.getByRole('heading', { name: 'Sans statistiques, pas de prédiction fiable.' }).isVisible()); });
  await check('paramètres du modèle et retour à l’analyse', async () => { await page.getByRole('button', { name: 'Méthode & réglages', exact: true }).click(); assert.ok(await page.getByRole('slider', { name: 'Poids des xG', exact: true }).isVisible()); await page.getByRole('button', { name: 'Analyse du match', exact: true }).click(); });
  await check('réimport JSON', async () => { await page.locator('.heading-actions').getByRole('button', { name: 'Importer des captures', exact: true }).click(); await page.getByLabel('Importer un export JSON', { exact: true }).setInputFiles({ name: 'analysis.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(exported)) }); await page.waitForFunction(() => !document.querySelector('[role=dialog]')); assert.equal(await page.getByRole('textbox', { name: 'Arsenal — Buts attendus (xG)', exact: true }).inputValue(), '8,5'); });
  await check('OCR réel sur une capture de comparaison synthétique', async () => {
    const capture = await context.newPage(); await capture.setViewportSize({ width: 706, height: 1568 }); await capture.goto(base);
    const rows = [['1,6','Buts par match','1,4'],['8,5','Buts attendus (xG)','7,7'],['0,8','Buts concédés par match','0,6'],['4,0','xG concédés','6,5'],['4,8','Tirs cadrés par match','3,6'],['59,3','Possession moyenne','44,8'],['3','Invincibilité','2']];
    await capture.setContent(`<html><head><style>@font-face{font-family:DM;src:url('${base}/fonts/dm-sans.woff2')}*{box-sizing:border-box}body{margin:0;background:#fff;width:706px;height:1568px;font-family:DM,Arial,sans-serif;color:#222}.team{position:absolute;top:370px;width:250px;text-align:center;font-size:34px}.row{position:absolute;left:0;width:706px;display:grid;grid-template-columns:155px 396px 155px;align-items:center;font-size:28px;text-align:center}.row span:nth-child(2){font-size:25px}</style></head><body><div class="team" style="left:40px">Arsenal</div><div class="team" style="right:40px">Leeds</div>${rows.map(([h,label,a],i)=>`<div class="row" style="top:${650+i*90}px"><span>${h}</span><span>${label}</span><span>${a}</span></div>`).join('')}</body></html>`);
    await capture.evaluate(() => document.fonts.ready); await capture.screenshot({ path: '.cache/ocr-fixture.png' }); await capture.close();
    await page.locator('.heading-actions').getByRole('button', { name: 'Importer des captures', exact: true }).click(); await page.getByLabel('Importer des captures FotMob', { exact: true }).setInputFiles('.cache/ocr-fixture.png');
    await page.waitForFunction(() => document.querySelector('.ocr-review') || document.querySelector('.import-file small')?.textContent.includes('échoué'), null, { timeout: 90000 });
    console.log('OCR:', await page.locator('.import-files').innerText());
    assert.ok(await page.locator('.ocr-review').isVisible()); assert.equal(await page.getByRole('textbox', { name: 'Arsenal — import Buts / match', exact: true }).inputValue(), '1,6');
    assert.equal(await page.getByRole('textbox', { name: 'Leeds — import xG concédés', exact: true }).inputValue(), '6,5');
    await page.getByRole('button', { name: 'Appliquer les données', exact: true }).click(); assert.ok(await page.getByText('Calcul en pause.', { exact: true }).isVisible());
    await page.getByRole('textbox', { name: 'Matchs utilisés · Arsenal', exact: true }).fill('5'); await page.getByRole('textbox', { name: 'Matchs utilisés · Leeds', exact: true }).fill('5');
    assert.match(await page.locator('.outcome-value').first().innerText(), /%/);
  });
  await check('mobile : navigation et absence de débordement horizontal', async () => { await page.setViewportSize({ width: 390, height: 844 }); assert.equal(await page.evaluate(() => document.documentElement.scrollWidth), 390); await page.getByRole('button', { name: 'Ouvrir le menu', exact: true }).click(); await page.getByRole('button', { name: 'Comparateur de cotes', exact: true }).click(); assert.equal(await page.evaluate(() => document.documentElement.scrollWidth), 390); await page.screenshot({ path: '.cache/mobile-compare.png', fullPage: true }); });
  await check('aucune erreur JavaScript navigateur', async () => assert.deepEqual(errors, []));
} finally { await browser.close(); }
if (failures.length) process.exitCode = 1;
