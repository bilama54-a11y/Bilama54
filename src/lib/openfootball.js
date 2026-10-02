import { SAMPLE } from './data.js';

// Données publiques CC0 : aucune clé, aucun compte, aucun scraping.
export const SOURCE = { id: 'openfootball', name: 'OpenFootball', url: 'https://github.com/openfootball/football.json', license: 'CC0 / domaine public' };
export const LEAGUES = [
  { id: 'en.1', name: 'Premier League', country: 'Angleterre' },
  { id: 'fr.1', name: 'Ligue 1', country: 'France' },
  { id: 'de.1', name: 'Bundesliga', country: 'Allemagne' },
  { id: 'es.1', name: 'La Liga', country: 'Espagne' },
  { id: 'it.1', name: 'Serie A', country: 'Italie' },
  { id: 'nl.1', name: 'Eredivisie', country: 'Pays-Bas' },
  { id: 'pt.1', name: 'Primeira Liga', country: 'Portugal' },
  { id: 'en.2', name: 'Championship', country: 'Angleterre' },
];
export const CACHE_TTL = 10 * 60 * 1000;
const API = 'https://api.github.com/repos/openfootball/football.json';
const memory = new Map();
const cacheKey = (league, season) => `matchlab:openfootball:v1:${league}:${season}`;
export const todayUTC = (now = new Date()) => now.toISOString().slice(0, 10);
export const currentSeason = (now = new Date()) => { const year = now.getUTCFullYear() - (now.getUTCMonth() < 6 ? 1 : 0); return `${year}-${String(year + 1).slice(-2)}`; };
export function validDate(date) { return typeof date === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(date) && !Number.isNaN(Date.parse(`${date}T00:00:00Z`)) && new Date(`${date}T00:00:00Z`).toISOString().slice(0, 10) === date; }
const formOf = (gf, ga) => gf > ga ? 'W' : gf < ga ? 'L' : 'D';
export const fixtureKey = row => `${row.date}|${row.team1}|${row.team2}`;
function selection(league, season) {
  const selected = LEAGUES.find(item => item.id === league);
  const year = Number(String(season).slice(0, 4));
  if (!selected || !/^20\d{2}-\d{2}$/.test(season) || year < 2010 || year > 2098 || season.slice(-2) !== String(year + 1).slice(-2)) throw new Error('Championnat ou saison non pris en charge.');
  return selected;
}
export function normalizeSeason(payload, league, season) {
  const selected = selection(league, season);
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) throw new Error('Réponse de la source non reconnue.');
  const rows = Array.isArray(payload.matches) ? payload.matches : Array.isArray(payload.rounds) ? payload.rounds.flatMap(round => round.matches || []) : null;
  if (!rows || rows.length > 1500) throw new Error('Le calendrier reçu est absent ou trop volumineux.');
  const seen = new Set(); const fixtures = []; let rejected = 0;
  for (const row of rows) {
    if (!row || !validDate(row.date) || typeof row.team1 !== 'string' || typeof row.team2 !== 'string' || !row.team1.trim() || !row.team2.trim() || row.team1.length > 70 || row.team2.length > 70 || row.team1 === row.team2) { rejected++; continue; }
    const year = Number(row.date.slice(0, 4));
    if (year < Number(season.slice(0,4)) || year > Number(season.slice(0,4)) + 1) { rejected++; continue; }
    const score = Array.isArray(row.score?.ft) && row.score.ft.length === 2 && row.score.ft.every(n => Number.isInteger(n) && n >= 0 && n <= 50) ? [...row.score.ft] : null;
    const fixture = { date: row.date, time: typeof row.time === 'string' && /^\d{2}:\d{2}$/.test(row.time) ? row.time : '', home: row.team1.trim(), away: row.team2.trim(), score, round: String(row.round || '').slice(0,60) };
    fixture.id = fixtureKey({ date: fixture.date, team1: fixture.home, team2: fixture.away });
    if (seen.has(fixture.id)) { rejected++; continue; }
    seen.add(fixture.id); fixtures.push(fixture);
  }
  if (!fixtures.length) throw new Error('Aucun match exploitable pour cette saison. Une autre saison peut être essayée, sans la présenter comme actuelle.');
  fixtures.sort((a,b) => a.date.localeCompare(b.date) || a.time.localeCompare(b.time) || a.home.localeCompare(b.home));
  return { provider: SOURCE.id, league: selected.id, competition: selected.name, season, name: String(payload.name || selected.name).slice(0,100), fixtures, rejected };
}
const decode = text => new TextDecoder('utf-8', { fatal: true }).decode(Uint8Array.from(atob(text.replace(/\s/g, '')), char => char.charCodeAt(0)));
function readCache(league, season) {
  const key = cacheKey(league,season);
  if (memory.has(key)) return memory.get(key);
  try {
    const saved = JSON.parse(localStorage.getItem(key));
    if (saved && saved.league === league && saved.season === season && validDate(saved.fixtures?.[0]?.date) && typeof saved.retrievedAt === 'string' && saved.fixtures.length <= 1500) { memory.set(key, saved); return saved; }
  } catch { /* Le mode privé peut désactiver le stockage. */ }
  return null;
}
function writeCache(data) {
  const key = cacheKey(data.league,data.season); memory.set(key,data);
  try { localStorage.setItem(key, JSON.stringify(data)); } catch { /* Les calculs restent possibles sans persistance. */ }
}
async function getJson(url, signal, fetcher) {
  const response = await fetcher(url, { signal, headers: { Accept: 'application/vnd.github+json' }, credentials: 'omit', cache: 'no-store' });
  if (!response.ok) {
    if (response.status === 403 || response.status === 429) throw new Error('La source gratuite limite les requêtes. Attendez avant d’actualiser : aucune clé payante n’est nécessaire.');
    if (response.status === 404) throw new Error('Cette saison n’est pas encore disponible pour ce championnat.');
    throw new Error(`Source indisponible (HTTP ${response.status}).`);
  }
  return response.json();
}
export async function loadSeason(league, season, { force = false, signal, fetcher = globalThis.fetch, now = new Date() } = {}) {
  selection(league,season);
  const cached = readCache(league,season);
  const cacheAge = cached ? now.getTime() - Date.parse(cached.retrievedAt) : Infinity;
  if (!force && cached && cacheAge >= 0 && cacheAge < CACHE_TTL) return { ...cached, delivery: 'cache' };
  const controller = new AbortController();
  const cancel = () => controller.abort(signal?.reason);
  if (signal?.aborted) { const error = new Error('Chargement annulé.'); error.name = 'AbortError'; throw error; }
  signal?.addEventListener('abort',cancel,{ once: true });
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const path = `${season}/${league}.json`;
    const response = await getJson(`${API}/contents/${path}?ref=master`, controller.signal, fetcher);
    if (response.encoding !== 'base64' || typeof response.content !== 'string' || response.content.length > 500000) throw new Error('Format de fichier non reconnu ou trop volumineux.');
    const data = normalizeSeason(JSON.parse(decode(response.content)), league,season);
    let updatedAt = null;
    try {
      const changes = await getJson(`${API}/commits?path=${encodeURIComponent(path)}&per_page=1`,controller.signal,fetcher);
      const date = changes?.[0]?.commit?.committer?.date;
      if (typeof date === 'string' && !Number.isNaN(Date.parse(date))) updatedAt = date;
    } catch { /* Une date inconnue est affichée comme inconnue, jamais « à jour ». */ }
    if (signal?.aborted) { const error = new Error('Chargement annulé.'); error.name = 'AbortError'; throw error; }
    const result = { ...data, retrievedAt: now.toISOString(), updatedAt, delivery: 'network', sourceUrl: `${SOURCE.url}/blob/master/${path}` };
    writeCache(result); return result;
  } catch (error) {
    if (error.message === 'Failed to fetch' || /NetworkError/.test(error.message || '')) error = new Error('Connexion à la source impossible. Vérifiez Internet ; les captures et le dernier cache restent utilisables.');
    if (signal?.aborted) { const aborted = new Error('Chargement annulé.'); aborted.name = 'AbortError'; throw aborted; }
    if (cached) return { ...cached, delivery: 'offline-cache', networkError: error.name === 'AbortError' ? 'La source a mis trop de temps à répondre.' : error.message };
    throw new Error(error.name === 'AbortError' ? 'La source a mis trop de temps à répondre. Réessayez ou utilisez les captures.' : error.message || 'Connexion impossible. Les données gratuites nécessitent Internet.');
  } finally { clearTimeout(timeout); signal?.removeEventListener('abort',cancel); }
}

export function teamHistory(dataset, team, cutoff, limit = 10) {
  return dataset.fixtures.filter(row => row.score && row.date < cutoff && (row.home === team || row.away === team)).sort((a,b) => a.date.localeCompare(b.date) || a.id.localeCompare(b.id)).slice(-limit);
}
export function buildFreeAnalysis(dataset, fixtureId, { limit = 10, now = new Date(), allowHistorical = false } = {}) {
  if (![5,10,200].includes(limit)) throw new Error('Fenêtre statistique non reconnue.');
  const fixture = dataset.fixtures.find(row => row.id === fixtureId);
  if (!fixture) throw new Error('Rencontre introuvable.');
  const today = todayUTC(now);
  if (!allowHistorical && (fixture.score || fixture.date < today)) throw new Error('Choisissez une rencontre à venir. Un résultat passé n’est pas une prédiction.');
  const cutoff = fixture.date < today ? fixture.date : today;
  const gaps = dataset.fixtures.filter(row => !row.score && row.date < cutoff && (row.home === fixture.home || row.away === fixture.home || row.home === fixture.away || row.away === fixture.away));
  if (gaps.length) throw new Error(`${gaps.length} rencontre(s) antérieure(s) sans résultat confirmé pour ces équipes. Analyse suspendue : match reporté ou source incomplète à vérifier.`);
  const teams = {};
  for (const [side, name] of [['home',fixture.home],['away',fixture.away]]) {
    const games = teamHistory(dataset,name,cutoff,limit);
    if (games.length < 3) throw new Error(`${name} : seulement ${games.length} résultat(s) antérieur(s). Au moins 3 sont nécessaires pour l’essai.`);
    const scored = games.map(row => row.score[row.home === name ? 0 : 1]);
    const conceded = games.map(row => row.score[row.home === name ? 1 : 0]);
    const mean = nums => String(Number((nums.reduce((sum,n)=>sum+n,0) / nums.length).toFixed(4))).replace('.',',');
    const empty = Object.fromEntries(Object.keys(SAMPLE.home).map(key=>[key,'']));
    teams[side] = { ...empty, name, color: side === 'home' ? '#4c805e' : '#5284a8', crest: '', games: String(games.length), goalsFor: mean(scored), goalsAgainst: mean(conceded), xgFor: '', xgAgainst: '', cleanSheets: String(conceded.filter(n=>n===0).length), form: games.slice(-5).map(row => formOf(row.score[row.home === name ? 0 : 1],row.score[row.home === name ? 1 : 0])) };
  }
  return {
    version: 1, competition: dataset.competition, season: dataset.season.replace('-', '/20'), modelMode: 'goals', venue: 'home', xgUnit: 'average', sampleConfirmed: true,
    source: 'OpenFootball · résultats communautaires', captureDate: '', home: teams.home, away: teams.away, h2h: null,
    dataSource: { provider: SOURCE.id, league: dataset.league, season: dataset.season, fixtureId, fixtureDate: fixture.date, cutoffDate: cutoff, retrievedAt: dataset.retrievedAt, updatedAt: dataset.updatedAt, delivery: dataset.delivery, window: limit, sourceUrl: dataset.sourceUrl },
  };
}
export function sourceAgeDays(data, now = new Date()) { const at = Date.parse(data?.updatedAt); return Number.isFinite(at) ? Math.max(0, Math.floor((now.getTime() - at)/86400000)) : null; }
