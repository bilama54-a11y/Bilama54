import { useState } from 'react';
import { ArrowUpRight, ChartNoAxesCombined, ChevronRight, CircleHelp, Goal, Info, Plus, TrendingUp } from 'lucide-react';
import { percent, decimal } from '../lib/data.js';
import { evaluateOdds } from '../lib/model.js';
import { Badge, Notice, PanelHeader } from './UI.jsx';

export function OutcomeCards({ prediction, match }) {
  const items = [
    { label: `Victoire ${match.home.name}`, short: 'ÉQUIPE 1', value: prediction.home, color: 'green', symbol: '1' },
    { label: 'Match nul', short: 'ÉQUILIBRE', value: prediction.draw, color: 'neutral', symbol: 'N' },
    { label: `Victoire ${match.away.name}`, short: 'ÉQUIPE 2', value: prediction.away, color: 'blue', symbol: '2' },
  ];
  const best = Math.max(prediction.home || 0, prediction.draw || 0, prediction.away || 0);
  return <div className="outcome-grid" aria-live="polite">
    {items.map(item => <div key={item.symbol} className={`outcome-card outcome-${item.color} ${prediction.valid && best === item.value ? 'outcome-favorite' : ''}`}><div className="outcome-heading"><span>{item.label}</span><span className="outcome-symbol">{item.symbol}</span></div><div className="outcome-value">{prediction.valid ? percent(item.value, 1) : '—'}<span>{prediction.valid && best === item.value ? <TrendingUp size={18} /> : null}</span></div><div className="mini-track"><span style={{ width: `${(item.value || 0) * 100}%` }} /></div><small>{prediction.valid && best === item.value ? 'Issue la plus probable du modèle' : 'Probabilité estimée · 90 minutes'}</small></div>)}
    <div className="outcome-card outcome-goals"><div className="outcome-heading"><span>Total de buts attendu</span><Goal size={18} /></div><div className="outcome-value">{prediction.valid ? decimal(prediction.totalGoals) : '—'}<span className="unit">buts</span></div><div className="xg-split"><span><i className="legend-dot home-dot" />{match.home.name} <b>{prediction.valid ? decimal(prediction.lambdaHome) : '—'}</b></span><span><i className="legend-dot away-dot" />{match.away.name} <b>{prediction.valid ? decimal(prediction.lambdaAway) : '—'}</b></span></div><small>Intensités du modèle, pas un score annoncé</small></div>
  </div>;
}

export function ScorePanel({ prediction, match }) {
  const [mode, setMode] = useState('scores');
  const [active, setActive] = useState(null);
  const top = prediction.scores?.slice(0, 3) || [];
  const visible = prediction.matrix?.slice(0, 5).reduce((sum, row) => sum + row.slice(0, 5).reduce((a, b) => a + b, 0), 0) || 0;
  const maximum = top[0]?.probability || 1;
  return <section className="panel score-panel"><PanelHeader title="Les scénarios les plus probables" description="Un score possible n’est jamais un score certain."><Badge kind="green" icon={ChartNoAxesCombined}>Poisson</Badge></PanelHeader>
    {!prediction.valid ? <div className="chart-placeholder"><ChartNoAxesCombined size={34} /><p>Complétez les données pour afficher les scénarios.</p></div> : <>
      <div className="top-scores">{top.map((score, index) => <div className={`score-tile ${index === 0 ? 'score-top' : ''}`} key={`${score.home}-${score.away}`}><span className="score-position">{index === 0 ? 'SCÉNARIO PRINCIPAL' : `SCÉNARIO 0${index + 1}`}</span><strong>{score.home}<span>–</span>{score.away}</strong><span className="score-probability">{percent(score.probability)} <small>de probabilité</small></span></div>)}</div>
      <div className="chart-switch"><div className="segmented" role="tablist" aria-label="Type de graphique"><button role="tab" aria-selected={mode === 'scores'} className={mode === 'scores' ? 'selected' : ''} onClick={() => setMode('scores')}>Matrice des scores</button><button role="tab" aria-selected={mode === 'goals'} className={mode === 'goals' ? 'selected' : ''} onClick={() => setMode('goals')}>Buts par équipe</button></div><CircleHelp size={16}><title>Les couleurs les plus foncées correspondent aux scores les plus probables.</title></CircleHelp></div>
      {mode === 'scores' ? <div className="heatmap-wrap"><span className="heatmap-title">Buts de {match.away.name} →</span><div className="heatmap" role="group" aria-label="Probabilités des scores de 0 à 4 buts"><div className="axis-label">{match.home.name} ↓</div>{[0,1,2,3,4].map(a => <span className="axis-number" key={`a${a}`}>{a}</span>)}{[0,1,2,3,4].map(h => <div className="heatmap-row" key={h}><span className="axis-number">{h}</span>{[0,1,2,3,4].map(a => <button key={a} aria-label={`${match.home.name} ${h} — ${match.away.name} ${a} : ${percent(prediction.matrix[h][a])}`} className={`heat-cell ${active?.home === h && active?.away === a ? 'active' : ''}`} style={{ backgroundColor: `rgba(82, 140, 102, ${0.04 + 0.43 * prediction.matrix[h][a] / maximum})`, color: '#294834' }} onClick={() => setActive({ home: h, away: a, probability: prediction.matrix[h][a] })} title={`${h}–${a} : ${percent(prediction.matrix[h][a])}`}>{prediction.matrix[h][a] < 0.01 ? '<1 %' : percent(prediction.matrix[h][a], 0)}</button>)}</div>)}</div><div className="heatmap-legend"><span>{active ? `Score ${active.home}–${active.away} : ${percent(prediction.matrix[active.home][active.away])}` : `Autres scores (5 buts ou plus d’une équipe) : ${percent(1 - visible)}`}</span><div><i />Moins probable <b />Plus probable</div></div></div> : <div className="goal-distribution"><div className="distribution-legend"><span><i className="legend-dot home-dot" />{match.home.name}</span><span><i className="legend-dot away-dot" />{match.away.name}</span></div><div className="distribution-bars">{[0,1,2,3,4,5,6].map(goal => {
        const hp = goal === 6 ? prediction.matrix.slice(6).flat().reduce((s,p)=>s+p,0) : prediction.matrix[goal].reduce((s,p)=>s+p,0);
        const ap = goal === 6 ? prediction.matrix.reduce((s,row)=>s+row.slice(6).reduce((t,p)=>t+p,0),0) : prediction.matrix.reduce((s,row)=>s+row[goal],0);
        return <div className="distribution-column" key={goal}><div className="bar-pair"><div className="distribution-bar home-bar" style={{ height: `${hp*290}%` }} title={`${match.home.name} : ${percent(hp)}`} /><div className="distribution-bar away-bar" style={{ height: `${ap*290}%` }} title={`${match.away.name} : ${percent(ap)}`} /></div><span>{goal === 6 ? '6+' : goal}</span></div>;
      })}</div><p>Nombre de buts · chaque distribution totalise 100 %.</p></div>}
    </>}
  </section>;
}

export function MarketsPanel({ prediction, selectedId, onSelect, bookOdds, setBookOdds, onAdd }) {
  const [tab, setTab] = useState('goals');
  const ids = ['under-3.5', 'over-1.5', 'over-2.5', 'over-3.5', 'btts-yes'];
  const markets = prediction.markets?.filter(m => tab === 'goals' ? ids.includes(m.id) : m.group === tab) || [];
  const selected = prediction.markets?.find(m => m.id === selectedId);
  const comparison = selected && bookOdds ? evaluateOdds(selected.probability, bookOdds) : null;
  return <section className="panel markets-panel"><PanelHeader title="Explorer les marchés" description="Probabilités et cotes théoriques, sans marge." /><div className="segmented market-tabs" role="tablist" aria-label="Marchés">{[['goals', 'Buts'], ['result', '1 / N / 2'], ['double', 'Double chance']].map(([key,label]) => <button key={key} role="tab" aria-selected={tab === key} className={tab === key ? 'selected' : ''} onClick={() => { setTab(key); const first = prediction.markets?.find(m => key === 'goals' ? m.id === 'under-3.5' : m.group === key); if (first) onSelect(first.id); }}>{label}</button>)}</div>
    <div className="market-table-heading"><span>Sélection</span><span>Probabilité</span><span>Cote neutre</span></div><div className="market-rows">{markets.length ? markets.map(m => <button className={`market-row ${m.id === selectedId ? 'market-selected' : ''}`} key={m.id} onClick={() => onSelect(m.id)}><span><i className="market-radio" />{m.label}</span><b>{percent(m.probability, 0)}</b><span>{decimal(m.fairOdds)}</span></button>) : <p className="muted text-center">En attente de données valides.</p>}</div>
    <div className="odds-workshop"><div className="odds-heading"><span className="odds-icon"><ArrowUpRight size={19} /></span><div><h3>Et votre cote ?</h3><p>Comparez le prix proposé par votre bookmaker.</p></div></div><div className="odds-input-row"><label className="field-label">{selected?.label || 'Sélection'}<input aria-label="Cote du bookmaker" type="text" inputMode="decimal" maxLength={10} placeholder="Ex. : 1,65" value={bookOdds} onChange={e => setBookOdds(e.target.value)} /></label><button className="icon-button add-market-button" aria-label="Ajouter la sélection au comparateur" disabled={!comparison?.valid} onClick={() => onAdd(selected, bookOdds)}><Plus size={22} /></button></div>
      {comparison && (comparison.valid ? <div className="odds-result"><span>Seuil de réussite <b>{percent(comparison.breakEven)}</b></span><span>Écart du modèle <b className={comparison.edge >= 0 ? 'positive' : 'negative'}>{comparison.edge >= 0 ? '+' : ''}{decimal(comparison.edge * 100, 1)} pts</b></span></div> : <p className="field-error">{comparison.error}</p>)}
      <p className="micro-note"><Info size={13} />Un écart positif ne prouve pas la rentabilité : ce modèle n’est pas calibré sur des résultats historiques.</p>
    </div>
  </section>;
}
