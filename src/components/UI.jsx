import { useEffect, useRef, useState } from 'react';
import { X, CheckCircle2, AlertCircle, Info, ArrowUpRight } from 'lucide-react';

export function Badge({ children, kind = 'muted', icon: Icon }) { return <span className={`badge badge-${kind}`}>{Icon && <Icon size={13} />}{children}</span>; }
export function TeamCrest({ team, size = 'normal' }) {
  const [failed, setFailed] = useState(false);
  const source = globalThis.MATCHLAB_PORTABLE?.assets?.[team.crest] || team.crest;
  useEffect(() => setFailed(false), [source]);
  return <div className={`team-crest crest-${size}`} style={{ '--team-color': team.color || '#46775f' }}>{source && !failed ? <img src={source} alt={`Repère de ${team.name}`} onError={() => setFailed(true)} /> : <span aria-hidden="true">{(team.name || '?').slice(0, 2).toUpperCase()}</span>}</div>;
}
export function FormDots({ form = [] }) {
  return <div className="form-dots" aria-label="Résultats du plus ancien au plus récent">{form.map((value, index) => <span key={index} className={`form-dot form-${value.toLowerCase()} ${index === form.length - 1 ? 'latest' : ''}`} title={{ W: 'Victoire', D: 'Match nul', L: 'Défaite' }[value]} aria-label={{ W: 'Victoire', D: 'Match nul', L: 'Défaite' }[value]}>{ { W: 'V', D: 'N', L: 'D' }[value]}</span>)}</div>;
}
export function PanelHeader({ eyebrow, title, description, children }) { return <div className="panel-header"><div>{eyebrow && <div className="eyebrow">{eyebrow}</div>}<h2>{title}</h2>{description && <p>{description}</p>}</div><div className="panel-actions">{children}</div></div>; }
export function Notice({ children, kind = 'info' }) { const Icon = kind === 'warning' ? AlertCircle : Info; return <div className={`notice notice-${kind}`}><Icon size={17} /><div>{children}</div></div>; }
export function Toast({ message, onClose }) {
  useEffect(() => { if (!message) return; const timer = setTimeout(onClose, 4800); return () => clearTimeout(timer); }, [message, onClose]);
  if (!message) return null;
  return <div className="toast" role="status"><CheckCircle2 size={19} /><span>{message}</span><button className="icon-button" aria-label="Fermer la notification" onClick={onClose}><X size={16} /></button></div>;
}
export function Modal({ title, subtitle, children, onClose, wide = false }) {
  const container = useRef(null);
  const closeRef = useRef(onClose);
  closeRef.current = onClose;
  useEffect(() => {
    const previous = document.activeElement;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    container.current?.querySelector('button, input, select, [tabindex="0"]')?.focus();
    const handler = event => {
      if (event.key === 'Escape') closeRef.current();
      if (event.key === 'Tab') {
        const elements = [...container.current.querySelectorAll('button:not(:disabled), input:not(:disabled), select, textarea, a[href], [tabindex="0"]')].filter(el => el.offsetParent !== null && el.tabIndex >= 0);
        const first = elements[0]; const last = elements[elements.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      }
    };
    document.addEventListener('keydown', handler);
    return () => { document.body.style.overflow = previousOverflow; document.removeEventListener('keydown', handler); previous?.focus?.(); };
  }, []);
  return <div className="modal-backdrop" onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}><section ref={container} className={`modal ${wide ? 'modal-wide' : ''}`} role="dialog" aria-modal="true" aria-label={title}><div className="modal-header"><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div><button className="icon-button" onClick={onClose} aria-label="Fermer la fenêtre"><X size={21} /></button></div>{children}</section></div>;
}
export function EmptyState({ icon: Icon = ArrowUpRight, title, description, children }) { return <div className="empty-state"><div className="empty-icon"><Icon size={30} /></div><h3>{title}</h3><p>{description}</p>{children}</div>; }
