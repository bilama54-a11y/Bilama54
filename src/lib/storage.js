import { SAMPLE, COUPON_SAMPLE, DEFAULT_PARAMETERS, clone } from './data.js';
import { validateMatch, number } from './model.js';
const KEY = 'matchlab:workspace:v1';

export const defaultWorkspace = () => ({ match: clone(SAMPLE), parameters: { ...DEFAULT_PARAMETERS }, coupon: [], history: [] });

export function validateImport(input) {
  if (!input || typeof input !== 'object' || Array.isArray(input) || input.version !== 1) throw new Error('Format non reconnu. Utilisez un export MatchLab (version 1).');
  const match = input.match || input;
  const errors = validateMatch(match);
  if (errors.length) throw new Error(errors[0]);
  const cleanTeam = team => {
    const clean = {};
    for (const [key, fallback] of Object.entries(SAMPLE.home)) {
      if (key === 'crest') { clean.crest = ['Arsenal', 'Leeds'].includes(team.name) ? `/teams/${team.name.toLowerCase()}.svg` : ''; }
      else if (key === 'color') clean.color = /^#[0-9a-f]{6}$/i.test(team.color || '') ? team.color : '#396958';
      else if (key === 'name') clean.name = team.name.trim();
      else if (key === 'form') clean.form = Array.isArray(team.form) ? team.form.slice(-5).filter(x => ['W', 'D', 'L'].includes(x)) : [];
      else clean[key] = Number.isFinite(number(team[key])) ? String(team[key]).slice(0, 14) : (['games', 'goalsFor', 'goalsAgainst', 'xgFor', 'xgAgainst'].includes(key) ? String(fallback) : '');
    }
    return clean;
  };
  return {
    version: 1, home: cleanTeam(match.home), away: cleanTeam(match.away),
    competition: String(match.competition || 'Football').slice(0, 70), season: String(match.season || '').slice(0, 20),
    source: String(match.source || 'Import JSON').slice(0, 120), captureDate: String(match.captureDate || '').slice(0, 30),
    venue: match.venue, sampleConfirmed: match.sampleConfirmed === true, xgUnit: match.xgUnit,
    h2h: match.h2h && ['home', 'draw', 'away'].every(key => Number.isInteger(match.h2h[key]) && match.h2h[key] >= 0 && match.h2h[key] <= 500) ? { home: match.h2h.home, draw: match.h2h.draw, away: match.h2h.away } : null,
  };
}

export function loadWorkspace() {
  const fallback = defaultWorkspace();
  try {
    const saved = JSON.parse(localStorage.getItem(KEY));
    if (!saved) return fallback;
    const match = validateImport({ version: 1, match: saved.match });
    const parameters = { ...DEFAULT_PARAMETERS };
    for (const key of Object.keys(parameters)) if (typeof saved.parameters?.[key] === 'number' && Number.isFinite(saved.parameters[key])) parameters[key] = saved.parameters[key];
    const coupon = Array.isArray(saved.coupon) ? saved.coupon.slice(0, 8).filter(e => e && typeof e.fixture === 'string' && e.fixture.length < 150).map(e => ({ id: String(e.id).slice(0, 80), fixture: e.fixture, market: String(e.market || '').slice(0, 100), odds: String(e.odds || '').slice(0, 14), probability: String(e.probability ?? '').slice(0, 14), source: String(e.source || '').slice(0, 150), date: String(e.date || '').slice(0, 50) })) : [];
    const history = Array.isArray(saved.history) ? saved.history.slice(0, 20).flatMap(e => { try { return [{ id: String(e.id), createdAt: String(e.createdAt), match: validateImport({ version: 1, match: e.match }), parameters: { ...DEFAULT_PARAMETERS, ...(e.parameters || {}) } }]; } catch { return []; } }) : [];
    return { match, parameters, coupon, history };
  } catch { return fallback; }
}

export function saveWorkspace(workspace) {
  try { localStorage.setItem(KEY, JSON.stringify(workspace)); return true; } catch { return false; }
}
export function downloadAnalysis(match, parameters, result) {
  const data = { version: 1, match, parameters, result: result.valid ? { home: result.home, draw: result.draw, away: result.away, lambdaHome: result.lambdaHome, lambdaAway: result.lambdaAway, scores: result.scores.slice(0, 8), markets: result.markets } : null, disclaimer: 'Modèle exploratoire non calibré. Aucune garantie de gain. Données non connectées à FotMob en direct.' };
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `matchlab-${match.home.name}-${match.away.name}.json`.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-zA-Z0-9._-]/g, '-').toLowerCase();
  document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1500);
}
export const couponExample = () => clone(COUPON_SAMPLE);
