export const SAMPLE = {
  version: 1,
  competition: 'Premier League',
  season: '2026/2027',
  source: 'Captures FotMob fournies',
  captureDate: '2026-10-02',
  venue: 'home',
  sampleConfirmed: false,
  xgUnit: 'total',
  home: {
    name: 'Arsenal', crest: '/teams/arsenal.svg', color: '#d9333a', games: '5',
    goalsFor: '1,6', goalsAgainst: '0,8', xgFor: '8,5', xgAgainst: '4,0',
    shotsOnTarget: '4,8', possession: '59,3', cleanSheets: '3', passes: '434,6',
    interceptions: '7,4', clearances: '21,2', saves: '1,8', rating: '7,03',
    bigChancesMissed: '8', longPasses: '19,2', crosses: '3,4',
    form: ['W', 'W', 'W', 'W', 'L'],
  },
  away: {
    name: 'Leeds', crest: '/teams/leeds.svg', color: '#457fa6', games: '5',
    goalsFor: '1,4', goalsAgainst: '0,6', xgFor: '7,7', xgAgainst: '6,5',
    shotsOnTarget: '3,6', possession: '44,8', cleanSheets: '2', passes: '278,6',
    interceptions: '12,0', clearances: '31,6', saves: '4,0', rating: '7,01',
    bigChancesMissed: '7', longPasses: '21,0', crosses: '3,4',
    form: ['D', 'D', 'L', 'W', 'D'],
  },
  h2h: { home: 11, draw: 2, away: 0 },
};

export const COUPON_SAMPLE = [
  { id: 'nvsl-total90', fixture: 'Total 90 — Nova Athletic', market: 'Plus de 3,5 buts', odds: '1,23', probability: '', date: '01.10.2026 · 23:30', source: 'Capture du coupon — aucune statistique fournie' },
  { id: 'nvsl-atlas', fixture: 'Atlas VA — Lumark', market: 'Plus de 3,5 buts', odds: '1,37', probability: '', date: '02.10.2026 · 01:00', source: 'Capture du coupon — aucune statistique fournie' },
  { id: 'nvsl-bench', fixture: 'Benchwarmer — Rampage', market: 'Plus de 3,5 buts', odds: '1,21', probability: '', date: '02.10.2026 · 01:00', source: 'Capture du coupon — aucune statistique fournie' },
];

export const DEFAULT_PARAMETERS = {
  xgWeight: 0.7, priorMatches: 4, baseline: 1.35, homeAdvantage: 0.12, awayPenalty: 0.06,
};

export const clone = value => JSON.parse(JSON.stringify(value));
export const percent = (value, digits = 1) => value == null || !Number.isFinite(value) ? '—' : new Intl.NumberFormat('fr-FR', { style: 'percent', maximumFractionDigits: digits, minimumFractionDigits: digits }).format(value);
export const decimal = (value, digits = 2) => value == null || !Number.isFinite(value) ? '—' : new Intl.NumberFormat('fr-FR', { maximumFractionDigits: digits, minimumFractionDigits: digits }).format(value);
