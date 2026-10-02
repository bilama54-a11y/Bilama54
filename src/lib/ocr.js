const normalize = text => String(text || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[’']/g, ' ').replace(/\s+/g, ' ').trim();
const FIELD_LABELS = [
  ['goalsAgainst', /buts?\s+concedes?\s+par\s+match|goals?\s+conceded\s+per\s+match/],
  ['xgAgainst', /xg\s+concedes?|xg\s+against/],
  ['xgFor', /buts?\s+attendus?|expected\s+goals|xg\s+(?:pour|crees?)/],
  ['goalsFor', /buts?\s+par\s+match|goals?\s+per\s+match/],
  ['shotsOnTarget', /tirs?\s+cadres?|shots?\s+on\s+target/],
  ['possession', /possession\s+moyenne|average\s+possession/],
  ['cleanSheets', /invincibilite|clean\s+sheets?/],
  ['longPasses', /passes?\s+longues?\s+precises?|accurate\s+long\s+balls/],
  ['passes', /passes?\s+precises?\s+par\s+match|accurate\s+passes?/],
  ['interceptions', /interceptions?\s+par\s+match|interceptions?\s+per/],
  ['clearances', /degagements?\s+par\s+match|clearances?\s+per/],
  ['saves', /arrets?\s+par\s+match|saves?\s+per/],
  ['rating', /note\s+fotmob|fotmob\s+rating/],
  ['bigChancesMissed', /grosses?\s+occasions?\s+manquees?|big\s+chances?\s+missed/],
  ['crosses', /centres?\s+reussis?\s+par\s+match|accurate\s+crosses?/],
  ['games', /matchs?\s+joues?|matches?\s+played/],
];
export const FIELD_NAMES = { name: 'Équipe', games: 'Matchs joués', goalsFor: 'Buts / match', goalsAgainst: 'Buts concédés / match', xgFor: 'xG créés', xgAgainst: 'xG concédés', shotsOnTarget: 'Tirs cadrés / match', possession: 'Possession (%)', cleanSheets: 'Clean sheets', passes: 'Passes précises / match', interceptions: 'Interceptions / match', clearances: 'Dégagements / match', saves: 'Arrêts / match', rating: 'Note FotMob', bigChancesMissed: 'Grosses occasions manquées', longPasses: 'Passes longues précises / match', crosses: 'Centres réussis / match' };
const numeric = text => {
  const match = String(text).trim().match(/^(\d+(?:[.,]\d+)?)\s*%?$/);
  return match ? match[1].replace('.', ',') : null;
};

export function tsvWords(tsv) {
  if (typeof tsv !== 'string') return [];
  return tsv.split('\n').slice(1).flatMap(line => {
    const columns = line.split('\t');
    if (columns.length < 12 || Number(columns[0]) !== 5 || !columns[11]?.trim()) return [];
    const [x, y, width, height, confidence] = columns.slice(6, 11).map(Number);
    if (![x, y, width, height, confidence].every(Number.isFinite)) return [];
    return [{ x, y, width, height, confidence, text: columns.slice(11).join('\t').trim(), cy: y + height / 2, cx: x + width / 2 }];
  });
}

export function parseText(text) {
  const fields = [];
  for (const raw of String(text || '').split('\n')) {
    const label = FIELD_LABELS.find(([, regex]) => regex.test(normalize(raw)));
    if (!label) continue;
    const values = raw.match(/\d+(?:[.,]\d+)?\s*%?/g) || [];
    if (values.length !== 2) continue;
    const [home, away] = values.map(x => numeric(x));
    if (home != null && away != null) fields.push({ key: label[0], home, away, confidence: null });
  }
  return fields;
}

export function parseCapture(data, width, height) {
  const text = data.text || '';
  if (/details?\s+du\s+pari|dupliquer\s+le\s+coupon|statut\s*:?\s*accepte|coupon\s+de\s+pari/.test(normalize(text))) {
    return { kind: 'coupon', fields: [], teams: {}, text, warnings: ['Coupon détecté : ses cotes ne sont pas des statistiques FotMob. Il n’est pas utilisé pour prédire le match.'] };
  }
  const words = tsvWords(data.tsv);
  const rows = [];
  for (const word of [...words].sort((a, b) => a.cy - b.cy)) {
    let row = rows.find(r => Math.abs(r.cy - word.cy) <= Math.max(8, height * 0.007));
    if (!row) { row = { cy: word.cy, words: [] }; rows.push(row); }
    row.words.push(word);
    row.cy = row.words.reduce((sum, w) => sum + w.cy, 0) / row.words.length;
  }
  rows.forEach(row => row.words.sort((a, b) => a.x - b.x));
  const fields = [];
  const teams = {};
  for (const row of rows) {
    const labelText = normalize(row.words.map(w => w.text).join(' '));
    const field = FIELD_LABELS.find(([, regex]) => regex.test(labelText));
    if (field) {
      const pick = side => {
        const candidates = row.words.filter(w => side === 'home' ? w.cx < width * 0.23 : w.cx > width * 0.76).map(w => ({ ...w, value: numeric(w.text) })).filter(w => w.value != null);
        return candidates.sort((a, b) => b.confidence - a.confidence)[0];
      };
      const home = pick('home'); const away = pick('away');
      if (home && away) fields.push({ key: field[0], home: home.value, away: away.value, confidence: Math.min(home.confidence, away.confidence) });
    }
    // Noms dans les deux cartes d’équipe, à l’exclusion de l’en-tête et des menus.
    if (row.cy > height * 0.18 && row.cy < height * 0.30 && !field) {
      for (const side of ['home', 'away']) {
        const candidates = row.words.filter(w => side === 'home' ? w.cx < width * 0.48 : w.cx > width * 0.52);
        const name = candidates.map(w => w.text).join(' ').trim();
        if (name && /[a-zA-ZÀ-ÿ]/.test(name) && !/premier|league|champion|football|statistique|victoire|equipe|vs|\d/.test(normalize(name)) && candidates.some(w => w.height > height * 0.012)) teams[side] = name;
      }
    }
  }
  if (!fields.length) fields.push(...parseText(text));
  const unique = [...new Map(fields.map(field => [field.key, field])).values()];
  const warnings = [];
  if (!unique.length) warnings.push('Aucune paire de statistiques reconnue. Essayez une capture nette, non recadrée, ou la saisie manuelle.');
  if (!unique.some(field => field.key === 'games')) warnings.push('Le nombre de matchs n’est pas visible : il doit être renseigné, jamais déduit de la forme sur 5 matchs.');
  if (unique.some(field => field.confidence != null && field.confidence < 65)) warnings.push('Certaines valeurs sont peu lisibles : vérifiez-les avant l’import.');
  return { kind: 'stats', fields: unique, teams, text, warnings };
}

let workerPromise;
let progressListener = () => {};
export async function recognizeCapture(file, onProgress = () => {}) {
  if (!['image/png', 'image/jpeg', 'image/webp', 'image/bmp'].includes(file.type)) throw new Error('Utilisez une image PNG, JPG, WEBP ou BMP.');
  if (file.size > 10 * 1024 * 1024) throw new Error('L’image dépasse 10 Mo.');
  const bitmap = await createImageBitmap(file);
  if (bitmap.width * bitmap.height > 40_000_000) { bitmap.close(); throw new Error('Image trop grande. Réduisez sa résolution.'); }
  const scale = Math.min(Math.max(1, 1400 / bitmap.width), 4096 / bitmap.height);
  const canvas = document.createElement('canvas');
  canvas.width = Math.round(bitmap.width * scale); canvas.height = Math.round(bitmap.height * scale);
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = 'white'; ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.filter = 'grayscale(1) contrast(1.1)';
  ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height); bitmap.close();
  progressListener = onProgress;
  if (!workerPromise) {
    const portable = globalThis.MATCHLAB_PORTABLE;
    workerPromise = import('tesseract.js').then(({ createWorker }) => createWorker('fra', 1, {
      workerPath: portable?.workerPath || '/ocr/worker.min.js',
      corePath: portable?.corePath || '/ocr/tesseract-core-lstm.wasm.js',
      langPath: portable ? 'https://matchlab.invalid/embedded' : '/ocr',
      cacheMethod: portable ? 'none' : 'write',
      workerBlobURL: false, gzip: true,
      logger: message => progressListener({ progress: message.progress || 0, status: message.status }),
    })).then(async worker => { await worker.setParameters({ tessedit_pageseg_mode: '12', preserve_interword_spaces: '1' }); return worker; }).catch(error => { workerPromise = null; throw error; });
  }
  try {
    const worker = await workerPromise;
    const { data } = await worker.recognize(canvas, {}, { text: true, tsv: true });
    return parseCapture(data, canvas.width, canvas.height);
  } catch {
    throw new Error('La lecture OCR a échoué. Rechargez la page, utilisez une capture plus nette ou saisissez les valeurs manuellement.');
  } finally { canvas.width = 0; canvas.height = 0; progressListener = () => {}; }
}

export function cancelRecognition() {
  const pending = workerPromise;
  workerPromise = null;
  progressListener = () => {};
  if (pending) pending.then(worker => worker.terminate()).catch(() => {});
}
