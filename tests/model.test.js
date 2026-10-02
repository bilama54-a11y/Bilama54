import test from 'node:test';
import assert from 'node:assert/strict';
import { SAMPLE, DEFAULT_PARAMETERS, clone, COUPON_SAMPLE } from '../src/lib/data.js';
import { predict, poisson, number, evaluateOdds, couponTotals, validateMatch } from '../src/lib/model.js';
import { validateImport } from '../src/lib/storage.js';
const close = (actual, expected, tolerance = 1e-9) => assert.ok(Math.abs(actual - expected) < tolerance, `${actual} ≠ ${expected}`);

test('les valeurs préremplies correspondent aux captures FotMob', () => {
  assert.equal(SAMPLE.home.xgFor, '8,5'); assert.equal(SAMPLE.away.xgAgainst, '6,5');
  assert.equal(SAMPLE.sampleConfirmed, false); assert.equal(SAMPLE.h2h.home, 11);
});
test('lecture des décimales françaises et rejet des données ambiguës', () => {
  close(number('1,122'), 1.122); close(number(' 4.8 '), 4.8); close(number('0'), 0);
  for (const v of ['', null, undefined, '-2', '1abc', '1e8', '1,2,3', Infinity]) assert.ok(Number.isNaN(number(v)));
});
test('une loi de Poisson de zéro but est une masse ponctuelle', () => {
  assert.deepEqual(poisson(0, 3), [1, 0, 0, 0]);
  close(poisson(1.7, 30).reduce((s,p)=>s+p,0), 1);
});
test('victoires, nuls et scores sont des partitions à 100 %', () => {
  const result = predict(clone(SAMPLE)); assert.ok(result.valid);
  close(result.home + result.draw + result.away, 1);
  close(result.matrix.flat().reduce((s,p)=>s+p,0), 1);
  close(result.scores.reduce((s,score)=>s+score.probability,0), 1);
  for (const market of result.markets) { assert.ok(market.probability >= 0 && market.probability <= 1); close(market.fairOdds * market.probability, 1); }
  assert.ok(result.truncatedMass < 1e-8);
});
test('les xG totaux sont divisés par le bon nombre de matchs de chaque équipe', () => {
  const sample = clone(SAMPLE); sample.away.games = '10';
  const result = predict(sample); close(result.homeRate.xg, 1.7); close(result.awayRate.xg, 0.77);
});
test('les modes totaux et moyennes produisent le même résultat à données équivalentes', () => {
  const averages = clone(SAMPLE); averages.xgUnit = 'average';
  for (const side of ['home','away']) for (const key of ['xgFor','xgAgainst']) averages[side][key] = String(number(averages[side][key]) / number(averages[side].games));
  const total = predict(SAMPLE); const average = predict(averages);
  close(total.lambdaHome, average.lambdaHome); close(total.home, average.home);
});
test('le changement d’échantillon recalcule les prédictions', () => {
  const other = clone(SAMPLE); other.home.games = '12';
  assert.notEqual(predict(other).home, predict(SAMPLE).home);
});
test('les totaux, BTTS et doubles chances sont cohérents', () => {
  const result = predict(SAMPLE); const p = id => result.markets.find(m=>m.id===id).probability;
  close(p('1x'), result.home + result.draw); close(p('x2'), result.away + result.draw);
  close(p('over-2.5') + p('under-2.5'), 1); close(p('btts-yes') + p('btts-no'), 1);
  assert.ok(p('over-1.5') > p('over-2.5')); assert.ok(p('over-2.5') > p('over-3.5'));
});
test('sur terrain neutre, l’échange des équipes échange les probabilités de victoire', () => {
  const original = clone(SAMPLE); original.venue = 'neutral';
  const reversed = { ...original, home: clone(original.away), away: clone(original.home) };
  close(predict(original).home, predict(reversed).away); close(predict(original).draw, predict(reversed).draw);
});
test('les paramètres influencent le modèle mais les tirs et H2H ne le doublonnent pas', () => {
  const sample = clone(SAMPLE); sample.h2h = { home: 0, draw: 0, away: 100 }; sample.home.shotsOnTarget = '100';
  close(predict(sample).home, predict(SAMPLE).home);
  assert.notEqual(predict(sample, { ...DEFAULT_PARAMETERS, xgWeight: 0 }).home, predict(sample).home);
});
test('données manquantes ou nombres de matchs fractionnaires : calcul en pause', () => {
  for (const [key,value] of [['games','0'],['games','3,5'],['xgFor',''],['goalsFor','-1']]) {
    const sample = clone(SAMPLE); sample.home[key] = value; const result = predict(sample);
    assert.equal(result.valid, false); assert.ok(result.errors.length);
  }
  assert.ok(validateMatch(null).length);
});
test('même des intensités élevées ne produisent pas de probabilité incohérente', () => {
  const sample = clone(SAMPLE); sample.xgUnit = 'average';
  for (const side of ['home','away']) { sample[side].xgFor='15'; sample[side].xgAgainst='15'; }
  const result = predict(sample, { ...DEFAULT_PARAMETERS, priorMatches: 0 });
  close(result.home + result.draw + result.away, 1); assert.ok(result.lambdaHome <= 8);
});
test('seuil de rentabilité et espérance ne sont pas confondus', () => {
  const result = evaluateOdds(.7, '1,25'); close(result.breakEven, .8); close(result.edge, -.1); close(result.expectedReturn, -.125);
  assert.equal(evaluateOdds(null, '1,25').probability, null); assert.equal(evaluateOdds(null, '1,25').expectedReturn, null);
  for (const invalid of ['1','0','abc','']) assert.equal(evaluateOdds(.7, invalid).valid, false);
});
test('le coupon NVSL reste sans probabilité inventée', () => {
  const result = couponTotals(clone(COUPON_SAMPLE)); assert.equal(result.complete, false);
  close(result.combinedOdds, 2.038971); close(result.breakEven, 1/2.038971);
  assert.equal(result.jointProbability, null); assert.equal(result.expectedReturn, null);
});
test('la multiplication des probabilités est conditionnelle à des matchs différents', () => {
  const items = [{ fixture: 'A — B', odds: '1.25', probability: '80' }, { fixture: 'C — D', odds: '1.5', probability: '70' }];
  close(couponTotals(items).jointProbability, .56);
  items[1].fixture = 'A — B'; assert.equal(couponTotals(items).correlated, true); assert.equal(couponTotals(items).jointProbability, null);
});
test('coupon vide et entrées invalides ne produisent pas NaN ni un conseil', () => {
  assert.equal(couponTotals([]).valid, false);
  assert.equal(couponTotals([{ fixture:'A', odds:'', probability:'80' }]).valid, false);
  const invalid = couponTotals([{ fixture:'A', odds:'1.5', probability:'150' }]); assert.equal(invalid.complete, false); assert.equal(invalid.invalidProbability, true);
});
test('les exports sont réimportables, les champs inattendus et URL de crest sont éliminés', () => {
  const exported = { version: 1, match: clone(SAMPLE), parameters: DEFAULT_PARAMETERS };
  exported.match.home.crest = 'javascript:evil()'; exported.match.home.secret = 'not imported';
  const imported = validateImport(exported); assert.equal(imported.home.crest, '/teams/arsenal.svg'); assert.equal(imported.home.secret, undefined);
  close(predict(imported).home, predict(SAMPLE).home);
});
test('les fichiers JSON mal formés ou de version inconnue sont rejetés', () => {
  for (const file of [null, [], { version:2, match:SAMPLE }, { version:1, match:{home:{}} }]) assert.throws(()=>validateImport(file));
});
