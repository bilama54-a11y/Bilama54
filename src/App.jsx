import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ArrowDown, ArrowRight, ArrowUpRight, BarChart3, BookOpen, Check, ChevronRight, CircleHelp, ClipboardList, CloudDownload, Download, FileImage, FlaskConical, History, Info, LayoutDashboard, Menu, Plus, RefreshCw, ScanLine, Settings2, ShieldCheck, Sparkles, Target, Upload, X } from 'lucide-react';
import { SAMPLE, DEFAULT_PARAMETERS, clone, percent, decimal } from './lib/data.js';
import { predict, number } from './lib/model.js';
import { loadWorkspace, saveWorkspace, downloadAnalysis, couponExample } from './lib/storage.js';
import { Badge, TeamCrest, FormDots, Modal, Notice, Toast } from './components/UI.jsx';
import { OutcomeCards, ScorePanel, MarketsPanel } from './components/Predictions.jsx';
import StatsEditor from './components/StatsEditor.jsx';
import FreeDataPage from './components/FreeDataPage.jsx';
import ImportDialog from './components/ImportDialog.jsx';
import { ComparePage, HistoryPage, MethodPage } from './components/PageViews.jsx';

const NAV = [
  { id: 'analysis', label: 'Analyse du match', icon: LayoutDashboard },
  { id: 'online', label: 'Données gratuites', icon: CloudDownload },
  { id: 'compare', label: 'Comparateur de cotes', icon: BarChart3 },
  { id: 'history', label: 'Mes analyses', icon: History },
  { id: 'method', label: 'Méthode & réglages', icon: BookOpen },
];
const crestFor = name => ({ arsenal: '/teams/arsenal.svg', leeds: '/teams/leeds.svg' }[name.trim().toLowerCase()] || '');
function blankMatch(homeName = 'Équipe 1', awayName = 'Équipe 2', competition = 'Football') {
  const emptyTeam = (name, base) => Object.fromEntries(Object.entries(base).map(([key]) => [key, key === 'name' ? name : key === 'color' ? '#467562' : key === 'crest' ? crestFor(name) : key === 'form' ? [] : '']));
  return { version: 1, modelMode: 'xg', competition, season: '', captureDate: '', source: 'Saisie manuelle', venue: 'home', xgUnit: 'total', sampleConfirmed: false, home: emptyTeam(homeName, SAMPLE.home), away: emptyTeam(awayName, SAMPLE.away), h2h: null };
}

function Sidebar({ page, setPage, mobileOpen, close, historyCount, onImport }) {
  const [narrow, setNarrow] = useState(() => window.matchMedia('(max-width: 820px)').matches);
  useEffect(() => {
    const media = window.matchMedia('(max-width: 820px)');
    const update = () => setNarrow(media.matches);
    media.addEventListener('change', update);
    return () => media.removeEventListener('change', update);
  }, []);
  useEffect(() => {
    const key = event => { if (event.key === 'Escape' && narrow && mobileOpen) close(); };
    document.addEventListener('keydown', key);
    return () => document.removeEventListener('keydown', key);
  }, [narrow, mobileOpen, close]);
  return <>
    {mobileOpen && <div className="sidebar-scrim" onClick={close} />}
    <aside className={`sidebar ${mobileOpen ? 'sidebar-open' : ''}`} aria-hidden={narrow && !mobileOpen} inert={narrow && !mobileOpen}>
      <button className="brand" onClick={() => { setPage('analysis'); close(); }} aria-label="MatchLab — accueil"><img src="/icons/matchlab.svg" alt="" /><span>Match<span>Lab</span><small>FOOTBALL INTELLIGENCE</small></span></button>
      <button className="icon-button sidebar-close" onClick={close} aria-label="Fermer le menu"><X size={20} /></button><span className="sidebar-section">VOTRE ATELIER</span>
      <nav aria-label="Navigation principale">{NAV.map(({ id, label, icon: Icon }) => <button key={id} className={`nav-item ${page === id ? 'nav-active' : ''}`} onClick={() => { setPage(id); close(); }}><Icon size={19} strokeWidth={1.8} /><span>{label}</span>{id === 'history' && historyCount > 0 && <b>{historyCount}</b>}{page === id && <span className="nav-active-dot" />}</button>)}</nav>
      <div className="sidebar-separator" />
      <button className="nav-item import-nav" onClick={() => { onImport(); close(); }}><ScanLine size={19} /><span>Importer des captures</span><Plus size={15} /></button>
      <div className="sidebar-bottom"><div className="private-card"><div className="private-icon"><ShieldCheck size={21} /></div><h3>Vos données.<br />Votre terrain.</h3><p>Images et calculs restent sur votre appareil. Aucun compte requis.</p><span><i /> Analyse locale</span></div><div className="sidebar-footer"><span>MatchLab <b>v1.1</b></span><small>18+ · Aucun gain garanti</small></div></div>
    </aside>
  </>;
}

function MatchHero({ match, prediction, updateMatch, onEdit }) {
  return <section className="panel match-hero"><div className="match-card-top"><span className="league-label"><span className="league-symbol"><Target size={15} /></span>{match.competition} <b>{match.season}</b></span><Badge icon={FlaskConical}>Simulation</Badge></div><div className="fixture"><div className="fixture-team"><TeamCrest team={match.home} /><div><h2>{match.home.name || 'Équipe 1'}</h2><FormDots form={match.home.form} /></div></div><div className="fixture-center"><span>VS</span><small>90 minutes</small></div><div className="fixture-team fixture-away"><div><h2>{match.away.name || 'Équipe 2'}</h2><FormDots form={match.away.form} /></div><TeamCrest team={match.away} /></div></div><div className="fixture-bottom"><div className="venue-toggle"><button className={match.venue === 'home' ? 'active' : ''} onClick={() => updateMatch({ venue: 'home' })} aria-pressed={match.venue === 'home'}>Équipe 1 à domicile</button><button className={match.venue === 'neutral' ? 'active' : ''} onClick={() => updateMatch({ venue: 'neutral' })} aria-pressed={match.venue === 'neutral'}>Terrain neutre</button></div><button className="text-button" onClick={onEdit}>Modifier les données <ArrowDown size={14} /></button></div><div className="fixture-source"><Info size={13} /> Comparaison de statistiques, pas un match en direct. La forme va du plus ancien au plus récent.</div></section>;
}

function QualityCard({ match, onData, onMethod }) {
  const fields = match.modelMode === 'goals' ? ['games', 'goalsFor', 'goalsAgainst'] : ['games', 'goalsFor', 'goalsAgainst', 'xgFor', 'xgAgainst'];
  const coreCount = fields.reduce((count, key) => count + (Number.isFinite(number(match.home[key])) ? 1 : 0) + (Number.isFinite(number(match.away[key])) ? 1 : 0), 0);
  const complete = coreCount === fields.length * 2;
  return <section className="panel quality-card"><div className="quality-header"><span className="eyebrow">QUALITÉ DES DONNÉES</span><ShieldCheck size={17} /></div><div className="quality-main"><span className={`quality-orbit ${match.sampleConfirmed && complete ? 'verified' : ''}`}><span>{complete ? (match.sampleConfirmed ? <Check size={27} /> : <Info size={27} />) : <ClipboardList size={27} />}</span></span><div><h3>{!complete ? 'À compléter' : match.sampleConfirmed ? (match.modelMode === 'goals' ? 'Volume observé' : 'Volume confirmé') : 'Volume à confirmer'}</h3><p>{complete ? `${match.home.games || '—'} + ${match.away.games || '—'} matchs utilisés` : `${coreCount} / ${fields.length * 2} valeurs essentielles`}</p></div></div><div className="quality-items"><span><i className="quality-dot green" /> Calcul automatique <Check size={14} /></span><span><i className={`quality-dot ${match.sampleConfirmed ? 'green' : 'amber'}`} /> Échantillon vérifié {match.sampleConfirmed ? <Check size={14} /> : <b>À vérifier</b>}</span><span><i className="quality-dot gray" /> Modèle calibré <b>Non</b></span></div><button className="quality-link" onClick={match.sampleConfirmed ? onMethod : onData}>{match.sampleConfirmed ? 'Comprendre les limites' : 'Vérifier mes données'} <ArrowRight size={15} /></button></section>;
}

function ContextPanel({ match, prediction, onMethod }) {
  const h2h = match.h2h;
  const total = h2h ? h2h.home + h2h.draw + h2h.away : 0;
  const moreShots = number(match.home.shotsOnTarget) >= number(match.away.shotsOnTarget) ? match.home : match.away;
  return <section className="panel context-panel"><div className="eyebrow">POUR PRENDRE DU RECUL</div><h2>Au-delà du score.</h2><p className="muted">Du contexte, pas des garanties.</p>{h2h && <div className="h2h-block"><div className="h2h-title"><span>Confrontations affichées</span><Badge>{total} matchs</Badge></div><div className="h2h-numbers"><span><b>{h2h.home}</b>{match.home.name}</span><span><b>{h2h.draw}</b>Nuls</span><span><b>{h2h.away}</b>{match.away.name}</span></div><div className="h2h-track"><span style={{ width: `${h2h.home / total * 100}%` }} /><span style={{ width: `${h2h.draw / total * 100}%` }} /><span style={{ width: `${h2h.away / total * 100}%` }} /></div><small>Historique hors modèle : les fréquences de confrontations ne sont pas des probabilités pour le prochain match.</small></div>}
    <div className="context-insight"><div><Target size={17} /></div><span><strong>{match.modelMode === 'goals' ? 'Des résultats observés, pas des xG.' : 'Les occasions, avant le résultat.'}</strong>{match.modelMode === 'goals' ? 'Les buts marqués et encaissés sont calculés sur les matchs antérieurs confirmés. Les tirs et xG ne sont pas disponibles dans cette source gratuite.' : Number.isFinite(number(moreShots.shotsOnTarget)) ? `${moreShots.name} affiche le plus de tirs cadrés : ${moreShots.shotsOnTarget} par match. Les tirs ne sont pas ajoutés aux xG dans le calcul.` : 'Les tirs cadrés apportent du contexte mais ne sont pas ajoutés aux xG dans le calcul.'}</span></div>
    <div className="context-insight"><div><FlaskConical size={17} /></div><span><strong>L’échantillon compte.</strong>{prediction.valid ? `Avec le lissage actuel, les données de ${match.home.name} ont un poids de ${percent(prediction.homeRate.weight, 0)} %. Le reste vient de la référence générique.` : 'Complétez les données requises par le mode choisi pour calculer les intensités.'}</span></div>
    <div className="source-caption"><FileImage size={16} /><div><span>{match.source}</span><small>{match.dataSource?.retrievedAt ? `Récupérées le ${new Intl.DateTimeFormat('fr-FR', {dateStyle:'short', timeStyle:'short', timeZone:'UTC'}).format(new Date(match.dataSource.retrievedAt))} UTC` : match.captureDate ? `Captures du ${match.captureDate.split('-').reverse().join('.')}` : 'Données saisies sur cet appareil'}</small></div></div><button className="text-button" onClick={onMethod}>Découvrir la méthode <ArrowUpRight size={15} /></button>
  </section>;
}

export default function App() {
  const [workspace] = useState(loadWorkspace);
  const [match, setMatch] = useState(workspace.match);
  const [parameters, setParameters] = useState(workspace.parameters);
  const [coupon, setCoupon] = useState(workspace.coupon);
  const [history, setHistory] = useState(workspace.history);
  const [page, setPage] = useState('analysis');
  const [mobileOpen, setMobileOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [newOpen, setNewOpen] = useState(false);
  const [manualOpen, setManualOpen] = useState(false);
  const [privacyOpen, setPrivacyOpen] = useState(false);
  const [toast, setToast] = useState('');
  const [selectedMarket, setSelectedMarket] = useState('under-3.5');
  const [bookOdds, setBookOdds] = useState('');
  const [newNames, setNewNames] = useState({ home: '', away: '', competition: 'Football' });
  const [manual, setManual] = useState({ fixture: '', market: 'Plus de 3,5 buts', odds: '', probability: '' });
  const prediction = useMemo(() => predict(match, parameters), [match, parameters]);
  const previousValid = useRef(workspace.match);
  const clearToast = useCallback(() => setToast(''), []);
  useEffect(() => { if (prediction.valid) previousValid.current = match; const timer = setTimeout(() => saveWorkspace({ match: previousValid.current, parameters, coupon, history }), 350); return () => clearTimeout(timer); }, [match, parameters, coupon, history, prediction.valid]);
  useEffect(() => { window.scrollTo({ top: 0, behavior: 'instant' }); }, [page]);
  const updateMatch = patch => setMatch(current => ({ ...current, ...patch }));
  const updateTeam = (side, key, value) => setMatch(current => ({ ...current, ...(current.dataSource ? { source: 'OpenFootball · données modifiées manuellement', sampleConfirmed: false } : {}), [side]: { ...current[side], [key]: value, ...(key === 'name' ? { crest: crestFor(value) } : {}) } }));
  const goData = () => { setPage('analysis'); setTimeout(() => document.getElementById('donnees')?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 80); };
  const resetExample = () => { setMatch(clone(SAMPLE)); setParameters({ ...DEFAULT_PARAMETERS }); setBookOdds(''); setPage('analysis'); setToast('Exemple FotMob rechargé. Le volume de 5 matchs reste à confirmer.'); };
  const importValues = (review, preserve) => {
    const next = preserve ? clone(match) : blankMatch(review.teams.home || match.home.name, review.teams.away || match.away.name, match.competition);
    for (const side of ['home', 'away']) { next[side].name = review.teams[side] || next[side].name; next[side].crest = crestFor(next[side].name); }
    for (const field of review.fields) for (const side of ['home', 'away']) if (Object.hasOwn(next[side], field.key)) next[side][field.key] = field[side];
    next.modelMode = 'xg'; next.dataSource = null; next.sampleConfirmed = false; next.source = `Import OCR · ${review.fields.length} statistiques reconnues`; next.captureDate = ''; next.h2h = preserve ? next.h2h : null;
    setMatch(next); setPage('analysis'); setBookOdds(''); setToast(`${review.fields.length} statistiques appliquées. Vérifiez le nombre de matchs et l’unité des xG.`);
  };
  const importJson = (newMatch, newParameters) => { setMatch(newMatch); if (newParameters && typeof newParameters === 'object') { const values = { ...DEFAULT_PARAMETERS }; for (const key of Object.keys(values)) if (typeof newParameters[key] === 'number' && Number.isFinite(newParameters[key])) values[key] = newParameters[key]; setParameters(values); } setPage('analysis'); setToast('Analyse JSON importée.'); };
  const saveAnalysis = () => { if (!prediction.valid) return; setHistory(current => [{ id: crypto.randomUUID(), createdAt: new Date().toISOString(), match: clone(match), parameters: { ...parameters } }, ...current].slice(0,20)); setToast('Analyse enregistrée sur cet appareil.'); };
  const addMarket = (market, odds) => {
    const fixture = `${match.home.name} — ${match.away.name}`;
    if (coupon.length >= 8) { setToast('Maximum 8 sélections.'); return; }
    if (coupon.some(entry => entry.fixture.toLowerCase() === fixture.toLowerCase())) { setToast('Une sélection de ce match existe déjà. Les corrélations ne sont pas modélisées.'); setPage('compare'); return; }
    setCoupon(current => [...current, { id: crypto.randomUUID(), fixture, market: market.label, odds, probability: decimal(market.probability * 100, 2), source: 'Estimation du modèle exploratoire MatchLab', date: '' }]); setToast('Sélection ajoutée au comparateur, pas à un bookmaker.');
  };
  const loadCoupon = () => { setCoupon(couponExample()); setPage('compare'); setToast('Coupon de la capture chargé. Les probabilités restent à renseigner.'); };
  const createNew = event => { event.preventDefault(); setMatch(blankMatch(newNames.home.trim(), newNames.away.trim(), newNames.competition.trim() || 'Football')); setNewOpen(false); setPage('analysis'); setBookOdds(''); setSelectedMarket('under-3.5'); setToast('Nouvelle analyse créée. Renseignez les statistiques essentielles.'); setTimeout(() => document.getElementById('donnees')?.scrollIntoView({ behavior: 'smooth' }), 120); };
  const addManual = event => { event.preventDefault(); if (coupon.length >= 8) return; setCoupon(current => [...current, { ...manual, id: crypto.randomUUID(), source: 'Saisie manuelle', date: '' }]); setManualOpen(false); setManual({ fixture: '', market: 'Plus de 3,5 buts', odds: '', probability: '' }); setToast('Sélection ajoutée. Vérifiez vos estimations et votre cote.'); };

  return <div className="app-shell">
    <Sidebar page={page} setPage={setPage} mobileOpen={mobileOpen} close={() => setMobileOpen(false)} historyCount={history.length} onImport={() => setImportOpen(true)} />
    <div className="workspace"><header className="topbar"><div className="topbar-left"><button className="icon-button menu-button" onClick={() => setMobileOpen(!mobileOpen)} aria-label="Ouvrir le menu" aria-expanded={mobileOpen}><Menu size={22} /></button><span className="breadcrumb">Votre espace <ChevronRight size={14} /><b>{NAV.find(item => item.id === page)?.label}</b></span><span className="mobile-brand">Match<span>Lab</span></span></div><div className="topbar-right"><span className="engine-status"><i /> Calcul local</span><span className="topbar-divider" /><button className="icon-button" aria-label="Aide et méthode" onClick={() => setPage('method')}><CircleHelp size={20} /></button><button className="profile-button" onClick={() => setPrivacyOpen(true)} aria-label="Stockage et confidentialité">B</button></div></header>
    <main className="main-content" id="main-content">
      {page === 'analysis' && <>
        <div className="page-heading"><div><div className="eyebrow">VOTRE ATELIER DE PRÉDICTION</div><h1>Le match, sous un autre angle<span>.</span></h1><p>Transformez vos statistiques en scénarios. Gardez le contrôle sur vos décisions.</p></div><div className="heading-actions"><button className="button button-primary online-open-button" onClick={() => setPage('online')}><CloudDownload size={17} /> Données gratuites</button><button className="button button-secondary new-analysis-button" onClick={() => { setNewNames({ home: '', away: '', competition: 'Football' }); setNewOpen(true); }}><Plus size={17} /> Nouvelle analyse</button><button className="button button-primary" onClick={() => setImportOpen(true)}><ScanLine size={18} /> Importer des captures</button></div></div>
        <div className="analysis-context"><span><i className="live-dot" /> Calcul automatique</span><span>·</span><span>{match.source === SAMPLE.source ? 'Exemple extrait de vos captures FotMob' : match.source}</span><button onClick={() => setPage('method')} className="text-button"><Info size={14} /> Comment ça fonctionne ?</button></div>
        <div className="intro-grid"><MatchHero match={match} prediction={prediction} updateMatch={updateMatch} onEdit={goData} /><QualityCard match={match} onData={goData} onMethod={() => setPage('method')} /></div>
        {match.modelMode === 'goals' && <Notice kind="warning"><strong>Essai gratuit : buts réels, sans xG.</strong> Les statistiques portent sur les résultats confirmés antérieurs au {match.dataSource?.cutoffDate?.split('-').reverse().join('.') || 'jour choisi'}. {match.dataSource?.updatedAt ? `Dernière modification de la source : ${new Intl.DateTimeFormat('fr-FR', {dateStyle:'short',timeZone:'UTC'}).format(new Date(match.dataSource.updatedAt))}.` : 'Date de mise à jour de la source inconnue.'} La récupération de données ne prouve pas qu’elles sont fraîches. Aucun flux temps réel ou modèle calibré.</Notice>}
        {!prediction.valid && <Notice kind="warning"><strong>Calcul en pause.</strong> {prediction.errors[0]} <button className="inline-link" onClick={goData}>Compléter les données <ArrowRight size={13} /></button></Notice>}
        <div className="section-heading"><h2>Ce que disent les chiffres</h2><span><span className="tiny-dot" /> {match.modelMode === 'goals' ? 'Buts réels · sans xG' : 'Modèle avec xG'} · temps réglementaire</span></div>
        <OutcomeCards prediction={prediction} match={match} />
        <div className="prediction-grid"><ScorePanel prediction={prediction} match={match} /><MarketsPanel prediction={prediction} selectedId={selectedMarket} onSelect={id => { setSelectedMarket(id); setBookOdds(''); }} bookOdds={bookOdds} setBookOdds={setBookOdds} onAdd={addMarket} /></div>
        <div className="bottom-grid"><StatsEditor match={match} updateTeam={updateTeam} updateMatch={updateMatch} onImport={() => setImportOpen(true)} /><ContextPanel match={match} prediction={prediction} onMethod={() => setPage('method')} /></div>
        <div className="analysis-footer"><div><ShieldCheck size={20} /><span><strong>Une analyse, pas une promesse.</strong><small>Probabilités non calibrées. Aucun résultat ni gain garanti. {match.modelMode === 'goals' ? 'Résultats communautaires, pas un flux temps réel.' : 'Données saisies ou importées.'}</small></span></div><div><button className="button button-secondary" disabled={!prediction.valid} onClick={() => { downloadAnalysis(match, parameters, prediction); setToast('Export JSON téléchargé.'); }}><Download size={16} /> Exporter</button><button className="button button-primary" disabled={!prediction.valid} onClick={saveAnalysis}><Plus size={16} /> Enregistrer l’analyse</button></div></div>
      </>}
      {page === 'online' && <FreeDataPage onImport={() => setImportOpen(true)} onAnalyze={analysis => { setMatch(analysis); setPage('analysis'); setBookOdds(''); setToast('Statistiques calculées sur les résultats antérieurs. Mode gratuit sans xG.'); }} />}
      {page === 'compare' && <ComparePage coupon={coupon} onUpdate={(id,key,value) => setCoupon(current => current.map(entry => entry.id === id ? { ...entry, [key]: value } : entry))} onRemove={id => setCoupon(current => current.filter(entry => entry.id !== id))} onLoadExample={loadCoupon} onAddManual={() => setManualOpen(true)} onGoAnalysis={() => setPage('analysis')} />}
      {page === 'history' && <HistoryPage history={history} onLoad={entry => { setMatch(clone(entry.match)); setParameters({ ...entry.parameters }); setPage('analysis'); setBookOdds(''); setToast('Analyse restaurée avec ses paramètres.'); }} onDelete={id => { setHistory(current => current.filter(entry => entry.id !== id)); setToast('Analyse supprimée de cet appareil.'); }} onGoAnalysis={() => setPage('analysis')} />}
      {page === 'method' && <MethodPage parameters={parameters} setParameters={setParameters} onResetExample={resetExample} />}
      <footer className="page-footer"><span><img src="/icons/matchlab.svg" alt="" /> MatchLab <b>·</b> La donnée, pas le hasard.</span><button onClick={() => setPrivacyOpen(true)}>Confidentialité & stockage <ArrowUpRight size={13} /></button><small>18+ · Jouez de manière responsable.</small></footer>
    </main></div>
    <Toast message={toast} onClose={clearToast} />
    {importOpen && <ImportDialog match={match} onClose={() => setImportOpen(false)} onApply={importValues} onJson={importJson} onSample={resetExample} onCompare={() => setPage('compare')} />}
    {newOpen && <Modal title="Un nouveau match à explorer." subtitle="Commencez par les équipes. Vous pourrez ensuite saisir ou importer leurs statistiques." onClose={() => setNewOpen(false)}><form onSubmit={createNew}><div className="modal-form"><label className="field-label">Équipe 1 · domicile par défaut<input autoComplete="off" required maxLength={70} value={newNames.home} placeholder="Ex. : Arsenal" onChange={e => setNewNames(current => ({ ...current, home: e.target.value }))} /></label><label className="field-label">Équipe 2<input autoComplete="off" required maxLength={70} value={newNames.away} placeholder="Ex. : Leeds" onChange={e => setNewNames(current => ({ ...current, away: e.target.value }))} /></label><label className="field-label">Compétition<input maxLength={70} value={newNames.competition} onChange={e => setNewNames(current => ({ ...current, competition: e.target.value }))} /></label><Notice>Aucun calendrier n’est automatiquement importé. Vous pouvez aussi sélectionner une rencontre réelle depuis « Données gratuites ».</Notice></div><div className="modal-footer"><button className="button button-secondary" type="button" onClick={() => setNewOpen(false)}>Annuler</button><button className="button button-primary" type="submit">Créer l’analyse <ArrowRight size={16} /></button></div></form></Modal>}
    {manualOpen && <Modal title="Comparer une sélection." subtitle="Indiquez une cote actuelle et, si vous en avez une, votre estimation indépendante." onClose={() => setManualOpen(false)}><form onSubmit={addManual}><div className="modal-form"><label className="field-label">Match<input required maxLength={120} value={manual.fixture} placeholder="Équipe 1 — Équipe 2" onChange={e => setManual(current => ({ ...current, fixture: e.target.value }))} /></label><label className="field-label">Marché<input required maxLength={100} value={manual.market} onChange={e => setManual(current => ({ ...current, market: e.target.value }))} /></label><div className="data-settings two-columns"><label className="field-label">Cote proposée<input inputMode="decimal" required value={manual.odds} placeholder="1,65" maxLength={10} onChange={e => setManual(current => ({ ...current, odds: e.target.value }))} /></label><label className="field-label">Probabilité estimée (%) · facultatif<input inputMode="decimal" value={manual.probability} placeholder="À renseigner" maxLength={7} onChange={e => setManual(current => ({ ...current, probability: e.target.value }))} /></label></div><Notice>Sans estimation indépendante, seule la probabilité nécessaire à l’équilibre peut être calculée. La cote ne donne pas la probabilité réelle.</Notice></div><div className="modal-footer"><button className="button button-secondary" type="button" onClick={() => setManualOpen(false)}>Annuler</button><button className="button button-primary" type="submit">Ajouter au comparateur <Plus size={16} /></button></div></form></Modal>}
    {privacyOpen && <Modal title="Un espace vraiment local." subtitle="Pas de compte. Pas de tracking. Pas d’envoi des images." onClose={() => setPrivacyOpen(false)}><div className="modal-form privacy-body"><div className="privacy-illustration"><ShieldCheck size={46} /></div><p>Les statistiques, les paramètres, le comparateur et vos analyses enregistrées sont sauvegardés dans le stockage local de ce navigateur. Les images servent uniquement à la lecture OCR et ne sont pas conservées dans votre bibliothèque.</p><p>Les calculs et l’OCR s’exécutent sur votre appareil. Aucun service FotMob ni bookmaker n’est connecté. Le mode gratuit contacte GitHub pour charger le calendrier public OpenFootball ; ces requêtes transmettent votre adresse IP et le championnat choisi au fournisseur. Les images restent sur votre appareil. Les ressources nécessaires sont fournies avec l’application ; la version HTML autonome les embarque directement.</p><Notice>Un navigateur privé ou un stockage saturé peut empêcher la sauvegarde. Exportez les analyses importantes en JSON. Une fois l’application chargée en version de production, elle peut fonctionner hors connexion.</Notice></div><div className="modal-footer"><button className="button button-primary" onClick={() => setPrivacyOpen(false)}>Compris <Check size={16} /></button></div></Modal>}
  </div>;
}
