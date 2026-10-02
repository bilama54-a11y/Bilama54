import { useEffect, useRef, useState } from 'react';
import { Upload, ScanLine, FileJson, Image, Check, AlertTriangle, LoaderCircle, ShieldCheck, ArrowRight, FileText, X } from 'lucide-react';
import { recognizeCapture, FIELD_NAMES, cancelRecognition } from '../lib/ocr.js';
import { validateImport } from '../lib/storage.js';
import { Badge, Modal, Notice } from './UI.jsx';

function mergeResults(results, match) {
  const fields = new Map();
  let teams = { home: match.home.name, away: match.away.name };
  for (const result of results) {
    for (const field of result.fields || []) fields.set(field.key, { ...field });
    teams = { ...teams, ...result.teams };
  }
  return { fields: [...fields.values()], teams };
}

export default function ImportDialog({ match, onClose, onApply, onJson, onSample, onCompare }) {
  const [results, setResults] = useState([]);
  const [review, setReview] = useState(null);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState({ value: 0, name: '', index: 0, total: 0 });
  const [error, setError] = useState('');
  const [dragging, setDragging] = useState(false);
  const [preserve, setPreserve] = useState(false);
  const imageInput = useRef(null); const jsonInput = useRef(null);
  const active = useRef(true); const urls = useRef([]);
  useEffect(() => { active.current = true; return () => { active.current = false; urls.current.forEach(URL.revokeObjectURL); cancelRecognition(); }; }, []);

  async function processImages(files) {
    const list = [...files];
    if (!list.length || busy) return;
    if (list.length > 6) { setError('Importez au maximum 6 captures à la fois.'); return; }
    if (list.some(file => file.size > 10 * 1024 * 1024)) { setError('Une capture dépasse la limite de 10 Mo.'); return; }
    setError(''); setBusy(true); setResults([]); setReview(null);
    urls.current.forEach(URL.revokeObjectURL); urls.current = [];
    const output = [];
    for (let index = 0; index < list.length; index++) {
      if (!active.current) break;
      const file = list[index]; const preview = URL.createObjectURL(file); urls.current.push(preview);
      setProgress({ value: 0, name: file.name, index: index + 1, total: list.length });
      try {
        const parsed = await recognizeCapture(file, message => { if (active.current) setProgress({ value: Math.round(message.status === 'recognizing text' ? message.progress * 100 : 0), name: file.name, index: index + 1, total: list.length }); });
        output.push({ ...parsed, name: file.name, preview });
      } catch (e) { output.push({ name: file.name, preview, kind: 'error', fields: [], error: e.message }); }
      if (active.current) setResults([...output]);
    }
    if (active.current) { setReview(mergeResults(output, match)); setBusy(false); }
  }

  async function importJson(file) {
    if (!file) return;
    try {
      if (file.size > 200 * 1024) throw new Error('Le fichier JSON dépasse 200 Ko.');
      const data = JSON.parse(await file.text());
      const clean = validateImport(data);
      onJson(clean, data.parameters); onClose();
    } catch (e) { setError(e instanceof SyntaxError ? 'Ce fichier n’est pas un JSON valide.' : e.message); }
  }
  const close = () => { active.current = false; if (busy) cancelRecognition(); onClose(); };
  const updateField = (key, side, value) => setReview(current => ({ ...current, fields: current.fields.map(field => field.key === key ? { ...field, [side]: value } : field) }));
  return <Modal wide title="Vos captures deviennent des données." subtitle="Importez vos comparaisons FotMob, puis vérifiez les valeurs reconnues." onClose={close}>
    <div className="import-content">
      <input ref={imageInput} type="file" multiple accept="image/png,image/jpeg,image/webp,image/bmp" className="sr-only" tabIndex={-1} aria-label="Importer des captures FotMob" onChange={e => { processImages(e.target.files); e.target.value = ''; }} />
      <input ref={jsonInput} type="file" accept=".json,application/json" className="sr-only" tabIndex={-1} aria-label="Importer un export JSON" onChange={e => { importJson(e.target.files[0]); e.target.value = ''; }} />
      <div className={`dropzone ${dragging ? 'dragging' : ''} ${busy ? 'is-busy' : ''}`} onDragOver={e => { e.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={e => { e.preventDefault(); setDragging(false); processImages(e.dataTransfer.files); }}>
        <div className="dropzone-icon">{busy ? <LoaderCircle className="spin" size={29} /> : <ScanLine size={29} />}</div>
        <h3>{busy ? `Lecture de la capture ${progress.index}/${progress.total}` : 'Glissez vos captures ici'}</h3>
        <p>{busy ? progress.name : 'Attaque, défense, contexte : plusieurs captures peuvent être fusionnées.'}</p>
        {busy ? <div className="ocr-progress"><span style={{ width: `${Math.max(5, progress.value)}%` }} /><small>{progress.value > 0 ? `${progress.value} %` : 'Préparation du moteur local…'}</small></div> : <><button className="button button-primary" onClick={() => imageInput.current.click()}><Upload size={16} /> Choisir des images</button><small>PNG, JPG, WEBP · 6 images maximum · 10 Mo par image</small></>}
      </div>
      <div className="import-privacy"><ShieldCheck size={16} /><span>OCR dans votre navigateur. Aucun envoi des images à un serveur. Le moteur français est servi avec l’application.</span></div>
      {error && <Notice kind="warning">{error}</Notice>}
      {!!results.length && <div className="import-files">{results.map((result, index) => <div className="import-file" key={index}><img src={result.preview} alt={`Aperçu de ${result.name}`} /><div><strong>{result.name}</strong><small>{result.kind === 'coupon' ? 'Coupon de pari · pas de statistiques importées' : result.kind === 'error' ? result.error : `${result.fields.length} paires de statistiques reconnues`}</small></div><Badge kind={result.kind === 'stats' && result.fields.length ? 'green' : 'amber'} icon={result.kind === 'stats' && result.fields.length ? Check : AlertTriangle}>{result.kind === 'stats' && result.fields.length ? 'À vérifier' : result.kind === 'coupon' ? 'Coupon' : 'Non reconnu'}</Badge></div>)}</div>}
      {review?.fields.length > 0 && <div className="ocr-review"><h3>Vérifiez avant d’appliquer <span>{review.fields.length} statistiques</span></h3><div className="review-team-names"><label className="field-label">Équipe 1<input value={review.teams.home || ''} maxLength={70} onChange={e => setReview(current => ({ ...current, teams: { ...current.teams, home: e.target.value } }))} /></label><label className="field-label">Équipe 2<input value={review.teams.away || ''} maxLength={70} onChange={e => setReview(current => ({ ...current, teams: { ...current.teams, away: e.target.value } }))} /></label></div><div className="review-stat-list">{review.fields.map(field => <div className="review-stat-row" key={field.key}><span>{FIELD_NAMES[field.key]}{field.confidence != null && field.confidence < 65 && <AlertTriangle size={13} title="Reconnaissance incertaine" />}</span><input aria-label={`${review.teams.home} — import ${FIELD_NAMES[field.key]}`} inputMode="decimal" value={field.home} onChange={e => updateField(field.key, 'home', e.target.value)} /><input aria-label={`${review.teams.away} — import ${FIELD_NAMES[field.key]}`} inputMode="decimal" value={field.away} onChange={e => updateField(field.key, 'away', e.target.value)} /></div>)}</div><label className="confirm-checkbox"><input type="checkbox" checked={preserve} onChange={e => setPreserve(e.target.checked)} /><span>Compléter les données actuelles : mêmes équipes et même période uniquement.</span></label><Notice>Si le nombre de matchs ou une donnée essentielle n’est pas reconnu, le calcul sera mis en pause jusqu’à sa saisie. L’unité des xG doit aussi être vérifiée.</Notice></div>}
      {results.some(result => result.kind === 'coupon') && <Notice kind="warning">Cette image est un <strong>coupon de bookmaker</strong>, pas une comparaison FotMob. Les cotes seules ne permettent pas d’estimer une probabilité de victoire. <button className="inline-link" onClick={() => { onCompare(); close(); }}>Ouvrir le comparateur de cotes <ArrowRight size={13} /></button></Notice>}
      {results.some(result => result.text) && <details className="ocr-text"><summary><FileText size={15} /> Voir le texte reconnu</summary><pre>{results.map(result => result.text || '').join('\n\n')}</pre></details>}
      {!busy && !results.length && <div className="import-alternatives"><button className="button button-secondary" onClick={() => jsonInput.current.click()}><FileJson size={16} /> Importer un export JSON</button><button className="text-button" onClick={() => { onSample(); close(); }}>Utiliser l’exemple fourni <ArrowRight size={15} /></button></div>}
    </div>
    <div className="modal-footer"><span>{busy ? 'Vous pouvez annuler la lecture à tout moment.' : 'Vous gardez le contrôle sur chaque chiffre.'}</span><button className="button button-secondary" onClick={close}>{busy ? 'Annuler la lecture' : 'Fermer'}</button><button className="button button-primary" disabled={busy || !review?.fields.length || !review.teams.home?.trim() || !review.teams.away?.trim()} onClick={() => { onApply(review, preserve); close(); }}>Appliquer les données <ArrowRight size={16} /></button></div>
  </Modal>;
}
