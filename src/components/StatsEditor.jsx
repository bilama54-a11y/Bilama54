import { useState } from 'react';
import { Check, ChevronDown, Pencil, SlidersHorizontal, Info } from 'lucide-react';
import { Badge, PanelHeader, Notice, TeamCrest } from './UI.jsx';
import { number } from '../lib/model.js';

const groups = {
  attack: [['goalsFor', 'Buts par match', 'Moyenne'], ['xgFor', 'Buts attendus (xG)', 'Unité choisie ci-dessus'], ['shotsOnTarget', 'Tirs cadrés par match', 'Contexte, hors calcul'], ['passes', 'Passes précises par match', 'Contexte, hors calcul'], ['bigChancesMissed', 'Grosses occasions manquées', 'Contexte, hors calcul']],
  defense: [['goalsAgainst', 'Buts concédés par match', 'Moyenne'], ['xgAgainst', 'xG concédés', 'Unité choisie ci-dessus'], ['cleanSheets', 'Matchs sans encaisser', '« Invincibilité » sur FotMob'], ['interceptions', 'Interceptions par match', 'Contexte, hors calcul'], ['saves', 'Arrêts par match', 'Contexte, hors calcul']],
  context: [['possession', 'Possession moyenne (%)', 'Contexte, hors calcul'], ['rating', 'Note FotMob', 'Contexte, hors calcul'], ['longPasses', 'Passes longues précises / match', 'Contexte, hors calcul'], ['crosses', 'Centres réussis par match', 'Contexte, hors calcul'], ['clearances', 'Dégagements par match', 'Contexte, hors calcul']],
};
const essential = ['goalsFor', 'xgFor', 'goalsAgainst', 'xgAgainst'];
export default function StatsEditor({ match, updateTeam, updateMatch, onImport }) {
  const [tab, setTab] = useState('attack');
  const [open, setOpen] = useState(true);
  return <section className="panel stats-panel" id="donnees">
    <PanelHeader title="Les données du match" description="Modifiez une valeur. Les scénarios se recalculent automatiquement.">
      <button className="text-button" onClick={() => setOpen(!open)} aria-expanded={open} aria-controls="stats-content"><SlidersHorizontal size={16} />{open ? 'Réduire' : 'Modifier'}<ChevronDown size={16} className={open ? 'rotated' : ''} /></button>
    </PanelHeader>
    {open && <div id="stats-content">
      <div className="data-settings">
        <label className="field-label">Matchs utilisés · {match.home.name}<input type="text" inputMode="numeric" maxLength={3} value={match.home.games} onChange={e => { updateTeam('home', 'games', e.target.value); updateMatch({ sampleConfirmed: false }); }} aria-invalid={!Number.isInteger(number(match.home.games)) || number(match.home.games) < 1} /></label>
        <label className="field-label">Matchs utilisés · {match.away.name}<input type="text" inputMode="numeric" maxLength={3} value={match.away.games} onChange={e => { updateTeam('away', 'games', e.target.value); updateMatch({ sampleConfirmed: false }); }} aria-invalid={!Number.isInteger(number(match.away.games)) || number(match.away.games) < 1} /></label>
        <label className="field-label">Unité des xG<select value={match.xgUnit} onChange={e => updateMatch({ xgUnit: e.target.value })}><option value="total">Totaux sur la période</option><option value="average">Moyennes par match</option></select></label>
      </div>
      {!match.sampleConfirmed && <Notice kind="warning"><strong>Volume à confirmer.</strong> Les captures fournies ne montrent pas le nombre de matchs de saison. Les « 5 derniers matchs » et les 13 confrontations ne permettent pas de le déduire. L’exemple utilise 5 matchs par équipe, uniquement comme hypothèse.</Notice>}
      <label className="confirm-checkbox"><input type="checkbox" checked={match.sampleConfirmed} onChange={e => updateMatch({ sampleConfirmed: e.target.checked })} /><span>J’ai vérifié le nombre de matchs et l’unité des xG.</span></label>
      <div className="stats-toolbar"><div className="segmented" role="tablist" aria-label="Catégories de statistiques">{[['attack', 'Attaque'], ['defense', 'Défense'], ['context', 'Contexte']].map(([key, label]) => <button key={key} role="tab" aria-selected={tab === key} onClick={() => setTab(key)} className={tab === key ? 'selected' : ''}>{label}</button>)}</div><Badge icon={Pencil}>Champs modifiables</Badge></div>
      <div className="stats-team-row"><div><TeamCrest team={match.home} size="tiny" /><input aria-label="Nom de l’équipe 1" value={match.home.name} maxLength={70} onChange={e => updateTeam('home', 'name', e.target.value)} /></div><span>Statistique</span><div><TeamCrest team={match.away} size="tiny" /><input aria-label="Nom de l’équipe 2" value={match.away.name} maxLength={70} onChange={e => updateTeam('away', 'name', e.target.value)} /></div></div>
      <div className="stats-rows" role="tabpanel" aria-label={{ attack: 'Attaque', defense: 'Défense', context: 'Contexte' }[tab]}>
        {groups[tab].map(([key, label, hint]) => <div className="stat-row" key={key}>
          <input className="stat-input home-stat" inputMode="decimal" type="text" maxLength={12} aria-label={`${match.home.name} — ${label}`} aria-invalid={essential.includes(key) && !Number.isFinite(number(match.home[key]))} value={match.home[key]} placeholder="—" onChange={e => updateTeam('home', key, e.target.value)} />
          <div><span>{label}{essential.includes(key) && <span className="model-dot" title="Utilisé par le modèle" />}</span><small>{hint}</small></div>
          <input className="stat-input away-stat" inputMode="decimal" type="text" maxLength={12} aria-label={`${match.away.name} — ${label}`} aria-invalid={essential.includes(key) && !Number.isFinite(number(match.away[key]))} value={match.away[key]} placeholder="—" onChange={e => updateTeam('away', key, e.target.value)} />
        </div>)}
      </div>
      <div className="stats-footer"><span><span className="model-dot" /> Utilisé dans le calcul · les autres chiffres donnent du contexte.</span><button className="text-button" onClick={onImport}>Importer des captures <Pencil size={14} /></button></div>
    </div>}
  </section>;
}
