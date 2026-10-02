import test from 'node:test';
import assert from 'node:assert/strict';
import { parseText, parseCapture, tsvWords } from '../src/lib/ocr.js';
const tsv = rows => 'level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n' + rows.map((r,i)=>`5\t1\t1\t1\t${i+1}\t1\t${r[0]}\t${r[1]}\t${r[2]}\t${r[3]}\t95\t${r[4]}`).join('\n');

test('les décimales françaises sont reconnues sans confondre xG pour et contre', () => {
  const data = parseText('1,6 Buts par match 1,4\n8,5 Buts attendus (xG) 7,7\n0,8 Buts concédés par match 0,6\n4,0 xG concédés 6,5');
  assert.equal(data.find(f=>f.key==='xgFor').home, '8,5'); assert.equal(data.find(f=>f.key==='xgAgainst').away, '6,5');
  assert.equal(data.find(f=>f.key==='goalsAgainst').home, '0,8');
});
test('la géométrie préserve équipe de gauche et équipe de droite', () => {
  const data = { text:'Arsenal Leeds\nAttaque\n1,6 Buts par match 1,4', tsv:tsv([[130,370,140,30,'Arsenal'],[525,370,115,30,'Leeds'],[60,780,45,30,'1,6'],[265,779,195,30,'Buts par match'],[613,782,45,30,'1,4']]) };
  const parsed = parseCapture(data,706,1568);
  assert.equal(parsed.teams.home,'Arsenal'); assert.equal(parsed.teams.away,'Leeds'); assert.equal(parsed.fields[0].home,'1,6'); assert.equal(parsed.fields[0].away,'1,4');
});
test('13 confrontations et cinq derniers résultats ne sont pas un nombre de matchs de saison', () => {
  const data=parseCapture({text:'Matchs précédents (13)\n11 Victoires 0\n5 derniers matchs',tsv:''},706,1568);
  assert.equal(data.fields.some(f=>f.key==='games'),false);
});
test('un coupon de pari n’est pas interprété comme des statistiques', () => {
  const data=parseCapture({text:'Détails du pari\nTotal 90 VS Nova Athletic\nTotal. (3.5) Plus de 1.23\nStatut : Accepté',tsv:''},706,1568);
  assert.equal(data.kind,'coupon'); assert.deepEqual(data.fields,[]);
});
test('texte incomplet : pas de valeurs inventées', () => {
  assert.deepEqual(parseText('Buts attendus (xG) 8,5'),[]);
  assert.equal(parseCapture({text:'Image illisible'},706,1568).fields.length,0);
});
test('colonnes TSV invalides et niveaux non mots sont ignorés', () => {
  assert.deepEqual(tsvWords('broken'),[]);
  assert.equal(tsvWords(tsv([[1,1,10,10,'hello']])).length,1);
});
