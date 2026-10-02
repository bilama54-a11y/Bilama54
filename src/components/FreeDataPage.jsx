import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, ArrowRight, CalendarDays, CloudDownload, ExternalLink, Globe, LoaderCircle, RefreshCw, ShieldCheck, WifiOff } from 'lucide-react';
import { Badge, EmptyState, Notice, PanelHeader } from './UI.jsx';
import { LEAGUES, SOURCE, buildFreeAnalysis, currentSeason, loadSeason, sourceAgeDays, todayUTC } from '../lib/openfootball.js';

const dateFormat = value => {
  if (!value || Number.isNaN(Date.parse(value))) return 'Inconnue';
  return new Intl.DateTimeFormat('fr-FR', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'UTC' }).format(new Date(value)) + ' UTC';
};
const addDays = (date, days) => { const d = new Date(`${date}T00:00:00Z`); d.setUTCDate(d.getUTCDate()+days); return d.toISOString().slice(0,10); };
export default function FreeDataPage({ onAnalyze, onImport }) {
  const [league, setLeague] = useState('en.1');
  const [season, setSeason] = useState(currentSeason);
  const [dataset, setDataset] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refresh, setRefresh] = useState(0);
  const [tab, setTab] = useState('upcoming');
  const [from, setFrom] = useState(todayUTC);
  const [to, setTo] = useState(() => addDays(todayUTC(),30));
  const [windowSize, setWindowSize] = useState(10);
  const [search, setSearch] = useState('');
  const [analysisError, setAnalysisError] = useState('');
  const [clock, setClock] = useState(0);
  const [autoRefresh, setAutoRefresh] = useState(true);
  useEffect(() => {
    const controller = new AbortController(); let active = true;
    setLoading(true); setError(''); setDataset(null); setAnalysisError('');
    loadSeason(league,season,{ signal: controller.signal, force: refresh > 0 }).then(data => { if(active) setDataset(data); }).catch(e => { if(active && e.name !== 'AbortError') setError(e.message); }).finally(() => { if(active) setLoading(false); });
    return () => { active = false; controller.abort(); };
  }, [league,season,refresh]);
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => { if(document.visibilityState === 'visible') { setClock(n=>n+1); setRefresh(n=>n+1); } },10*60*1000);
    return () => clearInterval(interval);
  }, [autoRefresh]);
  const today = todayUTC();
  const seasons = Array.from({length:4},(_,i)=>{const year=Number(currentSeason().slice(0,4))-i;return `${year}-${String(year+1).slice(-2)}`;});
  const displayed = useMemo(() => {
    if (!dataset) return [];
    const selected = dataset.fixtures.filter(row => {
      const stateMatch = tab === 'upcoming' ? !row.score && row.date >= today : row.score && row.date <= today;
      const dateMatch = tab === 'upcoming' ? row.date >= from && row.date <= to : true;
      const nameMatch = `${row.home} ${row.away}`.toLowerCase().includes(search.trim().toLowerCase());
      return stateMatch && dateMatch && nameMatch;
    });
    return (tab === 'results' ? [...selected].reverse() : selected).slice(0,60);
  },[dataset,tab,from,to,search,today]);
  const age = sourceAgeDays(dataset);
  const importAnalysis = row => {
    try { const analysis=buildFreeAnalysis(dataset,row.id,{limit:windowSize}); setAnalysisError(''); onAnalyze(analysis); }
    catch(e) { setAnalysisError(e.message); }
  };
  const totals = dataset?.fixtures.filter(row=>row.score && row.date<=today).length || 0;
  const isCurrentSeason = season === currentSeason();
  return <>
    <div className="page-heading"><div><div className="eyebrow">ESSAI GRATUIT · DONNÉES OUVERTES</div><h1>Vos matchs, sans captures<span>.</span></h1><p>Choisissez une rencontre. Les résultats antérieurs deviennent automatiquement des statistiques.</p></div><Badge kind="green" icon={ShieldCheck}>Sans compte · sans clé API</Badge></div>
    <section className="panel free-source-panel"><div className="free-source-heading"><div className="free-source-icon"><Globe size={25} /></div><div><h2>OpenFootball</h2><p>Source communautaire · domaine public · pas un flux temps réel</p></div><a className="text-button" href={SOURCE.url} target="_blank" rel="noreferrer">Voir la source <ExternalLink size={14} /></a></div>
      <div className="free-controls"><label className="field-label">Championnat<select aria-label="Championnat gratuit" value={league} onChange={e=>{setLeague(e.target.value);setRefresh(0);}}>{LEAGUES.map(l=><option value={l.id} key={l.id}>{l.name} · {l.country}</option>)}</select></label><label className="field-label">Saison<select aria-label="Saison des données" value={season} onChange={e=>{setSeason(e.target.value);setRefresh(0);}}>{seasons.map(s=><option key={s} value={s}>{s.replace('-','/20')}</option>)}</select></label><label className="field-label">Échantillon par équipe<select aria-label="Fenêtre statistique" value={windowSize} onChange={e=>setWindowSize(Number(e.target.value))}><option value={5}>5 derniers résultats disponibles</option><option value={10}>10 derniers résultats disponibles</option><option value={200}>Saison, avant la rencontre</option></select></label><button className="button button-primary" disabled={loading} onClick={()=>setRefresh(n=>n+1)}><RefreshCw size={16} className={loading?'spin':''} /> Actualiser</button></div>
      <div className="free-source-bottom"><label className="confirm-checkbox"><input type="checkbox" checked={autoRefresh} onChange={e=>setAutoRefresh(e.target.checked)} /><span>Actualiser toutes les 10 min tant que cet écran est ouvert et visible.</span></label><span>{loading?'Chargement…':dataset?.delivery==='network'?'Données téléchargées':dataset?.delivery==='offline-cache'?'Ancien cache · connexion indisponible':dataset?'Cache local · moins de 10 min':'Source non chargée'}</span></div>
    </section>
    <Notice><strong>Ce mode n’utilise pas les xG.</strong> Il calcule les buts marqués/encaissés et la forme à partir des scores confirmés. Les tirs, la possession, les blessures, les cotes et les xG ne sont pas fournis. Les captures restent disponibles pour une analyse enrichie.</Notice>
    {!isCurrentSeason && <Notice kind="warning"><strong>Saison historique.</strong> Les données {season.replace('-','/20')} ne sont pas les données de la saison en cours. Elles ne seront jamais étiquetées « actuelles ».</Notice>}
    {dataset && <div className="free-data-metrics"><div><span>Matchs répertoriés</span><strong>{dataset.fixtures.length}</strong></div><div><span>Scores confirmés disponibles</span><strong>{totals}</strong></div><div><span>Dernière modification du fichier source</span><strong className="small-date">{dateFormat(dataset.updatedAt)}</strong></div><div><span>Dernière récupération par l’application</span><strong className="small-date">{dateFormat(dataset.retrievedAt)}</strong></div></div>}
    {dataset?.delivery==='offline-cache' && <Notice kind="warning"><WifiOff size={15} /><span>{dataset.networkError} Les anciennes données sont affichées, pas de nouvelles données. Vérifiez leur date avant toute analyse.</span></Notice>}
    {dataset && (age===null || age>=7) && <Notice kind="warning">{age===null?'La date de mise à jour de la source n’a pas pu être vérifiée.':`Le fichier source a été modifié il y a ${age} jours.`} Une récupération aujourd’hui ne signifie pas que le fournisseur vient d’actualiser ses résultats. Les pauses de championnat et les retards de saisie peuvent l’expliquer.</Notice>}
    {analysisError && <Notice kind="warning"><strong>Analyse en pause :</strong> {analysisError}</Notice>}
    <section className="panel free-fixtures-panel"><PanelHeader title="Choisir une rencontre" description="Seuls les résultats strictement antérieurs au jour de calcul sont utilisés."><Badge icon={CloudDownload}>{LEAGUES.find(l=>l.id===league)?.name}</Badge></PanelHeader><div className="free-fixture-toolbar"><div className="segmented" role="tablist" aria-label="Type de rencontres"><button role="tab" aria-selected={tab==='upcoming'} className={tab==='upcoming'?'selected':''} onClick={()=>setTab('upcoming')}>À venir</button><button role="tab" aria-selected={tab==='results'} className={tab==='results'?'selected':''} onClick={()=>setTab('results')}>Résultats disponibles</button></div><input className="free-search" type="search" aria-label="Rechercher une équipe" value={search} placeholder="Rechercher une équipe…" maxLength={70} onChange={e=>setSearch(e.target.value)} /></div>
      {tab==='upcoming' && <div className="free-date-range"><label className="field-label">Du<input type="date" aria-label="Date de début" value={from} onChange={e=>setFrom(e.target.value)} /></label><label className="field-label">Au<input type="date" aria-label="Date de fin" value={to} min={from} onChange={e=>setTo(e.target.value)} /></label><span>Dates du calendrier de la source. Les heures et fuseaux ne sont pas suffisamment garantis pour une conversion automatique.</span></div>}
      {loading ? <div className="free-loading" role="status"><LoaderCircle className="spin" size={28} /><strong>Chargement du calendrier public…</strong><span>Pas de clé à saisir et aucun abonnement.</span></div> : error ? <EmptyState icon={WifiOff} title="La source n’a pas répondu." description={error}><div className="empty-actions"><button className="button button-primary" onClick={()=>setRefresh(n=>n+1)}>Réessayer <RefreshCw size={15} /></button><button className="button button-secondary" onClick={onImport}>Utiliser mes captures</button></div></EmptyState> : !displayed.length ? <EmptyState icon={CalendarDays} title="Aucune rencontre dans cette sélection." description={tab==='upcoming'?'Élargissez les dates ou choisissez une autre saison. Une pause internationale ou un calendrier incomplet peut laisser cette liste vide.':'La source ne fournit pas encore de scores correspondant à votre recherche.'} /> : <div className="free-fixtures-list">{displayed.map(row=><div className="free-fixture-row" key={row.id}><div className="free-fixture-date"><CalendarDays size={15} /><span>{row.date.split('-').reverse().join('.')}<small>{row.round || 'Championnat'}</small></span></div><div className="free-fixture-teams"><strong>{row.home}<span>—</span>{row.away}</strong><small>{row.score?`Score fourni par la source : ${row.score[0]}–${row.score[1]}`:'Avant-match · statistiques calculées sur les résultats disponibles'}</small></div>{row.score?<Badge>Terminé selon la source</Badge>:<button className="button button-secondary" onClick={()=>importAnalysis(row)}>Analyser <ArrowRight size={15} /></button>}</div>)}</div>}
      {dataset && <div className="free-fixtures-footer"><span>Maximum 60 rencontres affichées · cache 10 min · collecte uniquement quand l’écran est utilisé.</span><a href={dataset.sourceUrl} target="_blank" rel="noreferrer">Fichier source <ExternalLink size={12} /></a></div>}
    </section>
    <Notice kind="warning"><strong>Limites de l’essai :</strong> cette source ne couvre pas ici la Ligue des nations ni la NVSL. Les calendriers sont saisis par une communauté, et peuvent être incomplets. Le modèle de buts est non calibré ; aucune rentabilité ni réussite n’est démontrée.</Notice>
  </>;
}
