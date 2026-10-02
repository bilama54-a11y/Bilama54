import { DEFAULT_PARAMETERS } from './data.js';

export const number = value => {
  if (typeof value === 'number') return Number.isFinite(value) ? value : NaN;
  if (typeof value !== 'string' || !value.trim()) return NaN;
  const normalized = value.trim().replace(/\s/g, '').replace(',', '.');
  if (!/^\d+(\.\d+)?$/.test(normalized)) return NaN;
  const result = Number(normalized);
  return Number.isFinite(result) ? result : NaN;
};

export function validateMatch(match) {
  const errors = [];
  if (!match || typeof match !== 'object') return ['Données du match absentes.'];
  if (match.modelMode != null && !['xg', 'goals'].includes(match.modelMode)) errors.push('Mode du modèle invalide.');
  if (!['total', 'average'].includes(match.xgUnit)) errors.push('Choisissez l’unité des xG.');
  if (!['home', 'neutral'].includes(match.venue)) errors.push('Lieu du match invalide.');
  for (const side of ['home', 'away']) {
    const team = match[side];
    const label = side === 'home' ? 'Équipe 1' : 'Équipe 2';
    if (!team || typeof team !== 'object') { errors.push(`${label} manquante.`); continue; }
    if (typeof team.name !== 'string' || !team.name.trim() || team.name.length > 70) errors.push(`${label} : nom requis (70 caractères maximum).`);
    const games = number(team.games);
    if (!Number.isInteger(games) || games < 1 || games > 200) errors.push(`${label} : nombre de matchs entier entre 1 et 200 requis.`);
    const fields = match.modelMode === 'goals' ? ['goalsFor', 'goalsAgainst'] : ['goalsFor', 'goalsAgainst', 'xgFor', 'xgAgainst'];
    for (const field of fields) {
      const n = number(team[field]);
      const limit = field.startsWith('xg') && match.xgUnit === 'total' ? 1000 : 15;
      if (!Number.isFinite(n) || n < 0 || n > limit) errors.push(`${team.name || label} : ${field.startsWith('xg') ? 'xG' : 'moyenne de buts'} invalide (0–${limit}).`);
    }
  }
  return errors;
}

export function poisson(lambda, maxGoals = 24) {
  if (!Number.isFinite(lambda) || lambda < 0) throw new Error('Intensité de Poisson invalide.');
  const values = [Math.exp(-lambda)];
  for (let goal = 1; goal <= maxGoals; goal++) values.push(values[goal - 1] * lambda / goal);
  return values;
}

const bound = (value, min, max) => Math.max(min, Math.min(max, value));
export function predict(match, inputParameters = DEFAULT_PARAMETERS) {
  const errors = validateMatch(match);
  if (errors.length) return { valid: false, errors };
  const parameters = { ...DEFAULT_PARAMETERS, ...inputParameters };
  for (const key of Object.keys(DEFAULT_PARAMETERS)) {
    if (typeof parameters[key] !== 'number' || !Number.isFinite(parameters[key])) return { valid: false, errors: ['Paramètres du modèle invalides.'] };
  }
  parameters.xgWeight = bound(parameters.xgWeight, 0, 1);
  parameters.priorMatches = bound(parameters.priorMatches, 0, 20);
  parameters.baseline = bound(parameters.baseline, 0.1, 4);
  parameters.homeAdvantage = bound(parameters.homeAdvantage, 0, 0.4);
  parameters.awayPenalty = bound(parameters.awayPenalty, 0, 0.4);

  const mode = match.modelMode || 'xg';
  if (mode === 'goals') parameters.xgWeight = 0;
  const rate = team => {
    const games = number(team.games);
    const divisor = match.xgUnit === 'total' ? games : 1;
    const xg = mode === 'xg' ? number(team.xgFor) / divisor : null;
    const xga = mode === 'xg' ? number(team.xgAgainst) / divisor : null;
    const attackRaw = mode === 'xg' ? parameters.xgWeight * xg + (1 - parameters.xgWeight) * number(team.goalsFor) : number(team.goalsFor);
    const defenseRaw = mode === 'xg' ? parameters.xgWeight * xga + (1 - parameters.xgWeight) * number(team.goalsAgainst) : number(team.goalsAgainst);
    const weight = games / (games + parameters.priorMatches);
    return {
      attack: weight * attackRaw + (1 - weight) * parameters.baseline,
      defense: weight * defenseRaw + (1 - weight) * parameters.baseline,
      attackRaw, defenseRaw, xg, xga, weight,
    };
  };
  const homeRate = rate(match.home);
  const awayRate = rate(match.away);
  const atHome = match.venue === 'home';
  const lambdaHome = bound(Math.sqrt(homeRate.attack * awayRate.defense) * (atHome ? 1 + parameters.homeAdvantage : 1), 0.02, 8);
  const lambdaAway = bound(Math.sqrt(awayRate.attack * homeRate.defense) * (atHome ? 1 - parameters.awayPenalty : 1), 0.02, 8);
  const maxGoals = Math.max(14, Math.ceil(Math.max(lambdaHome, lambdaAway) + 8 * Math.sqrt(Math.max(lambdaHome, lambdaAway))));
  const homePoisson = poisson(lambdaHome, maxGoals);
  const awayPoisson = poisson(lambdaAway, maxGoals);
  const matrix = homePoisson.map(h => awayPoisson.map(a => h * a));
  const mass = matrix.flat().reduce((sum, p) => sum + p, 0);
  // Une troncature suffisamment large, normalisée, conserve les partitions à 100 %.
  let home = 0, draw = 0, away = 0, btts = 0;
  const over = { '0.5': 0, '1.5': 0, '2.5': 0, '3.5': 0, '4.5': 0 };
  const scores = [];
  matrix.forEach((row, h) => row.forEach((_, a) => {
    const p = matrix[h][a] / mass;
    matrix[h][a] = p;
    if (h > a) home += p; else if (h === a) draw += p; else away += p;
    if (h > 0 && a > 0) btts += p;
    for (const threshold of Object.keys(over)) if (h + a > Number(threshold)) over[threshold] += p;
    scores.push({ home: h, away: a, probability: p });
  }));
  scores.sort((a, b) => b.probability - a.probability || a.home - b.home || a.away - b.away);
  const market = (id, label, probability, group) => ({ id, label, probability, group, fairOdds: probability > 0 ? 1 / probability : null });
  const markets = [
    market('home', `Victoire ${match.home.name}`, home, 'result'),
    market('draw', 'Match nul', draw, 'result'),
    market('away', `Victoire ${match.away.name}`, away, 'result'),
    market('1x', `${match.home.name} ou nul (1X)`, home + draw, 'double'),
    market('x2', `${match.away.name} ou nul (X2)`, away + draw, 'double'),
    market('12', 'Pas de match nul (12)', home + away, 'double'),
    ...Object.entries(over).map(([threshold, p]) => market(`over-${threshold}`, `Plus de ${threshold.replace('.', ',')} buts`, p, 'goals')),
    market('under-2.5', 'Moins de 2,5 buts', 1 - over['2.5'], 'goals'),
    market('under-3.5', 'Moins de 3,5 buts', 1 - over['3.5'], 'goals'),
    market('under-4.5', 'Moins de 4,5 buts', 1 - over['4.5'], 'goals'),
    market('btts-yes', 'Les deux équipes marquent', btts, 'btts'),
    market('btts-no', 'Au moins une équipe ne marque pas', 1 - btts, 'btts'),
  ];
  return { valid: true, mode, errors: [], parameters, lambdaHome, lambdaAway, totalGoals: lambdaHome + lambdaAway, home, draw, away, btts, over, markets, scores, matrix, maxGoals, truncatedMass: 1 - mass, homeRate, awayRate };
}

export function evaluateOdds(probability, decimalOdds) {
  const odds = number(decimalOdds);
  if (!Number.isFinite(odds) || odds <= 1 || odds > 10000) return { valid: false, error: 'Saisissez une cote décimale supérieure à 1.' };
  const p = probability == null ? null : number(probability);
  if (p != null && (!Number.isFinite(p) || p < 0 || p > 1)) return { valid: false, error: 'Probabilité invalide.' };
  return { valid: true, odds, breakEven: 1 / odds, probability: p, edge: p == null ? null : p - 1 / odds, expectedReturn: p == null ? null : p * odds - 1 };
}

export function couponTotals(entries) {
  if (!Array.isArray(entries) || entries.length === 0) return { valid: false, empty: true };
  const invalid = entries.some(entry => !evaluateOdds(null, entry.odds).valid);
  if (invalid) return { valid: false, error: 'Une cote du coupon est manquante ou invalide.' };
  const names = entries.map(entry => String(entry.fixture).trim().toLowerCase().replace(/\s+/g, ' '));
  const correlated = new Set(names).size !== names.length;
  const combinedOdds = entries.reduce((product, entry) => product * number(entry.odds), 1);
  const probabilities = entries.map(entry => entry.probability === '' || entry.probability == null ? null : number(entry.probability) / 100);
  const invalidProbability = probabilities.some(p => p != null && (!Number.isFinite(p) || p < 0 || p > 1));
  const complete = !correlated && !invalidProbability && probabilities.every(p => p != null);
  const jointProbability = complete ? probabilities.reduce((product, p) => product * p, 1) : null;
  return { valid: true, combinedOdds, breakEven: 1 / combinedOdds, jointProbability, correlated, invalidProbability, complete, expectedReturn: jointProbability == null ? null : jointProbability * combinedOdds - 1 };
}
