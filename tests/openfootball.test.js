import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeSeason, buildFreeAnalysis, currentSeason, validDate, loadSeason, sourceAgeDays } from '../src/lib/openfootball.js';
import { predict } from '../src/lib/model.js';
import { validateImport } from '../src/lib/storage.js';
import { DEFAULT_PARAMETERS } from '../src/lib/data.js';
const NOW = new Date('2026-10-02T12:00:00Z');
const fixtures = [
  { date:'2026-08-21',team1:'Arsenal FC',team2:'Chelsea FC',score:{ft:[2,0]} },
  { date:'2026-08-22',team1:'Chelsea FC',team2:'Leeds United FC',score:{ft:[1,1]} },
  { date:'2026-08-28',team1:'Arsenal FC',team2:'Everton FC',score:{ft:[1,0]} },
  { date:'2026-08-29',team1:'Everton FC',team2:'Leeds United FC',score:{ft:[2,1]} },
  { date:'2026-09-05',team1:'Arsenal FC',team2:'Leeds United FC',score:{ft:[1,1]} },
  { date:'2026-10-02',team1:'Arsenal FC',team2:'Chelsea FC',score:{ft:[7,0]} },
  { date:'2026-10-20',team1:'Arsenal FC',team2:'Leeds United FC' },
  { date:'2026-10-25',team1:'Arsenal FC',team2:'Chelsea FC',score:{ft:[15,0]} },
];
const data = () => ({...normalizeSeason({name:'English Premier League 2026/27',matches:fixtures},'en.1','2026-27'),retrievedAt:NOW.toISOString(),updatedAt:'2026-09-22T09:33:49Z',delivery:'network'});
const futureId = () => data().fixtures.find(row=>row.date==='2026-10-20').id;

test('calendrier public : validation, dates réelles et absence de résultat différent de 0–0',()=>{
  assert.equal(validDate('2026-02-30'),false); assert.equal(validDate('2024-02-29'),true);
  assert.equal(data().fixtures.length,8); assert.equal(data().fixtures.find(row=>row.date==='2026-10-20').score,null);
  const n=normalizeSeason({matches:[{date:'2026-08-01',team1:'A',team2:'B',score:{ft:[0,0]}},{date:'invalid',team1:'A',team2:'B'}]},'en.1','2026-27'); assert.deepEqual(n.fixtures[0].score,[0,0]);assert.equal(n.rejected,1);
});
test('une mauvaise saison ou un chemin arbitraire est rejeté',()=>{
  assert.throws(()=>normalizeSeason({matches:fixtures},'../secret','2026-27'));
  assert.throws(()=>normalizeSeason({matches:fixtures},'en.1','2026-28'));
  assert.throws(()=>normalizeSeason({matches:[{date:'2024-01-01',team1:'A',team2:'B'}]},'en.1','2026-27'));
});
test('les doublons ne gonflent pas les échantillons',()=>{
  const n=normalizeSeason({matches:[...fixtures,fixtures[0]]},'en.1','2026-27');assert.equal(n.fixtures.length,8);assert.equal(n.rejected,1);
});
test('pas de fuite du futur ni du jour courant vers les statistiques avant-match',()=>{
  const m=buildFreeAnalysis(data(),futureId(),{now:NOW});
  assert.equal(m.home.games,'3');assert.equal(m.away.games,'3');assert.equal(m.home.goalsFor,'1,3333');assert.equal(m.home.goalsAgainst,'0,3333');
  assert.equal(m.dataSource.cutoffDate,'2026-10-02');assert.equal(m.modelMode,'goals');assert.equal(m.home.xgFor,'');assert.equal(m.away.xgAgainst,'');assert.equal(m.season,'2026/2027');
});
test('pas de prévision fabriquée sur un résultat passé ou un échantillon trop petit',()=>{
  assert.throws(()=>buildFreeAnalysis(data(),data().fixtures[0].id,{now:NOW}),/à venir/);
  const small={...data(),fixtures:data().fixtures.filter(row=>row.date!=='2026-09-05')};assert.throws(()=>buildFreeAnalysis(small,futureId(),{now:NOW}),/Au moins 3/);
});
test('résultat antérieur manquant : analyse suspendue plutôt que source prétendument complète',()=>{
  const g=normalizeSeason({matches:[...fixtures,{date:'2026-09-29',team1:'Arsenal FC',team2:'Chelsea FC'}]},'en.1','2026-27');
  assert.throws(()=>buildFreeAnalysis(g,futureId(),{now:NOW}),/sans résultat confirmé/);
});
test('mode buts réels : valide sans xG, pondération xG ignorée, probabilités cohérentes',()=>{
  const m=buildFreeAnalysis(data(),futureId(),{now:NOW});const r=predict(m,{...DEFAULT_PARAMETERS,xgWeight:1});assert.equal(r.valid,true);assert.equal(r.mode,'goals');assert.equal(r.homeRate.xg,null);assert.equal(r.parameters.xgWeight,0);assert.ok(Math.abs(r.home+r.draw+r.away-1)<1e-9);
});
test('export/import du mode gratuit préserve provenance et absence de xG',()=>{
  const m=buildFreeAnalysis(data(),futureId(),{now:NOW});const clean=validateImport({version:1,match:m});assert.equal(clean.modelMode,'goals');assert.equal(clean.home.xgFor,'');assert.equal(clean.dataSource.provider,'openfootball');assert.equal(clean.dataSource.cutoffDate,'2026-10-02');assert.equal(predict(clean).valid,true);
});
test('la date de téléchargement et la date de mise à jour ne sont pas confondues',()=>{
  assert.equal(sourceAgeDays(data(),NOW),10);assert.equal(sourceAgeDays({updatedAt:null},NOW),null);
  assert.equal(currentSeason(new Date('2026-01-03')),'2025-26');assert.equal(currentSeason(NOW),'2026-27');
});
test('collecte anonyme, cache et repli hors ligne restent explicitement identifiés',async()=>{
  let calls=0;
  const fetcher=async(url,options)=>{calls++;assert.equal(options.credentials,'omit');assert.equal(options.headers.Authorization,undefined);return {ok:true,json:async()=>url.includes('/contents/')?{encoding:'base64',content:Buffer.from(JSON.stringify({matches:fixtures})).toString('base64')}:[{commit:{committer:{date:'2026-09-22T09:33:49Z'}}}]};};
  const loaded=await loadSeason('en.1','2026-27',{force:true,now:NOW,fetcher});assert.equal(calls,2);assert.equal(loaded.delivery,'network');assert.equal(loaded.updatedAt,'2026-09-22T09:33:49Z');
  const cached=await loadSeason('en.1','2026-27',{now:NOW,fetcher});assert.equal(calls,2);assert.equal(cached.delivery,'cache');
  const failed=await loadSeason('en.1','2026-27',{force:true,now:NOW,fetcher:async()=>{throw new Error('Offline');}});assert.equal(failed.delivery,'offline-cache');assert.equal(failed.retrievedAt,loaded.retrievedAt);assert.equal(failed.networkError,'Offline');
});
