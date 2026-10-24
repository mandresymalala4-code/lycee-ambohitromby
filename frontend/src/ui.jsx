import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { AnimatePresence, animate, motion, useReducedMotion } from 'framer-motion';
import { AlertTriangle, Check, CheckCircle2, ChevronDown, ChevronLeft, ChevronRight, ChevronUp, Info, Inbox, Search, X, XCircle } from 'lucide-react';
import { norm } from './validators';
import { media } from './api';

/* ---------- Toasts ---------- */
const ToastCtx = createContext(null);
export const useToast = () => useContext(ToastCtx);
export function ToastProvider({ children }) {
  const [items, setItems] = useState([]);
  const push = useCallback((type, message) => {
    const id = Math.random().toString(36).slice(2);
    setItems((l) => [...l.slice(-3), { id, type, message }]);
    setTimeout(() => setItems((l) => l.filter((x) => x.id !== id)), type === 'error' ? 6500 : 4000);
  }, []);
  const api = useMemo(() => ({ success: (m) => push('success', m), error: (m) => push('error', m), info: (m) => push('info', m) }), [push]);
  const icons = { success: CheckCircle2, error: XCircle, info: Info };
  return (
    <ToastCtx.Provider value={api}>
      {children}
      <div className="toasts" aria-live="polite">
        <AnimatePresence>
          {items.map((t) => { const I = icons[t.type]; return (
            <motion.div key={t.id} className={`toast toast-${t.type}`} layout initial={{ opacity: 0, x: 60, scale: .95 }} animate={{ opacity: 1, x: 0, scale: 1 }} exit={{ opacity: 0, x: 60 }} transition={{ type: 'spring', stiffness: 380, damping: 30 }}>
              <I size={18} /><span>{t.message}</span>
              <button className="icon-btn" onClick={() => setItems((l) => l.filter((x) => x.id !== t.id))} aria-label="Fermer"><X size={14} /></button>
            </motion.div>); })}
        </AnimatePresence>
      </div>
    </ToastCtx.Provider>
  );
}

/* ---------- Logo / Avatar ---------- */
export function Logo({ size = 36, src }) {
  if (src) return <img src={media(src)} alt="Logo" width={size} height={size} style={{ borderRadius: 10, objectFit: 'contain' }} />;
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-label="Logo Lycée Ambohitromby">
      <defs><linearGradient id="lg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#3B82F6" /><stop offset="1" stopColor="#1E3A8A" /></linearGradient></defs>
      <circle cx="32" cy="32" r="30" fill="url(#lg)" />
      <path d="M12 40a22 22 0 0 0 40 0" fill="none" stroke="#BFDBFE" strokeWidth="3" strokeLinecap="round" />
      <text x="32" y="38" textAnchor="middle" fontFamily="Segoe UI, Arial" fontWeight="700" fontSize="21" fill="#fff">LA</text>
    </svg>
  );
}
export function Avatar({ src, name = '', size = 34 }) {
  const ini = name.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join('').toUpperCase();
  if (src) return <img className="avatar" src={media(src)} alt={name} style={{ width: size, height: size }} />;
  return <span className="avatar avatar-ini" style={{ width: size, height: size, fontSize: size * 0.38 }}>{ini || '?'}</span>;
}

/* ---------- Petits composants ---------- */
export const Badge = ({ tone = 'gray', children }) => <span className={`badge badge-${tone}`}>{children}</span>;
export function Spinner({ size = 18 }) { return <span className="spinner" style={{ width: size, height: size }} />; }
export const Skeleton = ({ h = 14, w = '100%', style }) => <span className="skeleton" style={{ height: h, width: w, display: 'block', ...style }} />;
export function EmptyState({ icon: Icon = Inbox, title, text, action }) {
  return (
    <motion.div className="empty" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
      <div className="empty-ico"><Icon size={26} /></div><h3>{title}</h3>{text && <p>{text}</p>}{action}
    </motion.div>
  );
}
export function PageHeader({ title, subtitle, actions }) {
  return (<div className="page-head"><div><h1>{title}</h1>{subtitle && <p className="muted">{subtitle}</p>}</div><div className="page-actions">{actions}</div></div>);
}
export function Field({ label, error, required, hint, children, className = '' }) {
  return (
    <label className={`field ${error ? 'has-error' : ''} ${className}`}>
      {label && <span className="field-label">{label}{required && <b className="req"> *</b>}</span>}
      {children}
      {hint && !error && <span className="field-hint">{hint}</span>}
      <AnimatePresence>{error && <motion.span className="field-error" initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>{error}</motion.span>}</AnimatePresence>
    </label>
  );
}
export function Tabs({ tabs, value, onChange }) {
  return (
    <div className="tabs" role="tablist">
      {tabs.map((t) => (
        <button key={t.value} role="tab" aria-selected={value === t.value} className={`tab ${value === t.value ? 'active' : ''}`} onClick={() => onChange(t.value)}>
          {t.icon}{t.label}{t.count ? <span className="tab-count">{t.count}</span> : null}
          {value === t.value && <motion.span layoutId="tabline" className="tab-line" />}
        </button>))}
    </div>
  );
}
export function Counter({ value, decimals = 0, suffix = '' }) {
  const ref = useRef(null);
  const reduce = useReducedMotion();
  const prev = useRef(0);
  useEffect(() => {
    const to = Number(value) || 0;
    if (reduce) { if (ref.current) ref.current.textContent = to.toLocaleString('fr-FR', { minimumFractionDigits: decimals, maximumFractionDigits: decimals }) + suffix; return undefined; }
    const c = animate(prev.current, to, { duration: 0.9, ease: 'easeOut', onUpdate: (v) => { if (ref.current) ref.current.textContent = v.toLocaleString('fr-FR', { minimumFractionDigits: decimals, maximumFractionDigits: decimals }) + suffix; } });
    prev.current = to;
    return () => c.stop();
  }, [value, decimals, suffix, reduce]);
  return <span ref={ref}>0{suffix}</span>;
}
export function StatCard({ icon: Icon, label, value, decimals = 0, suffix = '', tone = 'blue', delay = 0, empty = '—', loading }) {
  return (
    <motion.div className={`card stat stat-${tone}`} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay, duration: .35 }} whileHover={{ y: -3 }}>
      <div className="stat-ico"><Icon size={20} /></div>
      <div><div className="stat-label">{label}</div>
        <div className="stat-value">{loading ? <Skeleton h={22} w={70} /> : (value === null || value === undefined ? empty : <Counter value={value} decimals={decimals} suffix={suffix} />)}</div></div>
    </motion.div>
  );
}
export function SuccessCheck({ size = 72 }) {
  return (
    <motion.svg width={size} height={size} viewBox="0 0 80 80" initial={{ scale: .6, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: 'spring', stiffness: 260, damping: 16 }}>
      <circle cx="40" cy="40" r="36" fill="rgba(22,163,74,.14)" stroke="#16A34A" strokeWidth="3" />
      <motion.path d="M24 41l11 11 21-24" fill="none" stroke="#16A34A" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: .25, duration: .45 }} />
    </motion.svg>
  );
}

/* ---------- Modal / Confirm ---------- */
export function Modal({ open, onClose, title, children, footer, size = 'md', closable = true }) {
  useEffect(() => {
    if (!open) return undefined;
    const k = (e) => { if (e.key === 'Escape' && closable) onClose?.(); };
    document.addEventListener('keydown', k); document.body.style.overflow = 'hidden';
    return () => { document.removeEventListener('keydown', k); document.body.style.overflow = ''; };
  }, [open, onClose, closable]);
  return (
    <AnimatePresence>
      {open && (
        <motion.div className="overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onMouseDown={(e) => { if (e.target === e.currentTarget && closable) onClose?.(); }}>
          <motion.div className={`modal modal-${size}`} role="dialog" aria-modal="true" initial={{ opacity: 0, scale: .92, y: 24 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: .96, y: 12 }} transition={{ type: 'spring', stiffness: 380, damping: 28 }}>
            <div className="modal-head"><h2>{title}</h2>{closable && <button className="icon-btn" onClick={onClose} aria-label="Fermer"><X size={18} /></button>}</div>
            <div className="modal-body">{children}</div>
            {footer && <div className="modal-foot">{footer}</div>}
          </motion.div>
        </motion.div>)}
    </AnimatePresence>
  );
}
export function ConfirmDialog({ open, title = 'Confirmation', message, confirmLabel = 'Confirmer', danger, loading, onConfirm, onCancel, children }) {
  return (
    <Modal open={open} onClose={onCancel} title={title} size="sm" footer={<>
      <button className="btn btn-ghost" onClick={onCancel}>Annuler</button>
      <button className={`btn ${danger ? 'btn-danger' : 'btn-primary'}`} onClick={onConfirm} disabled={loading}>{loading && <Spinner size={14} />}{confirmLabel}</button></>}>
      <div className="confirm"><div className={`confirm-ico ${danger ? 'danger' : ''}`}><AlertTriangle size={22} /></div><div><p>{message}</p>{children}</div></div>
    </Modal>
  );
}

/* ---------- Stepper ---------- */
export function Stepper({ steps, current }) {
  return (
    <ol className="stepper">
      {steps.map((s, i) => (
        <li key={s} className={i < current ? 'done' : i === current ? 'active' : ''}>
          <span className="step-dot">{i < current ? <Check size={14} /> : i + 1}</span><span className="step-label">{s}</span>
          {i < steps.length - 1 && <span className="step-bar"><motion.span animate={{ width: i < current ? '100%' : '0%' }} transition={{ duration: .4 }} /></span>}
        </li>))}
    </ol>
  );
}

/* ---------- DataTable ---------- */
export function DataTable({ columns, rows, loading, onRowDoubleClick, toolbar, empty, pageSizes = [10, 25, 50], searchPlaceholder = 'Rechercher…', rowKey = 'id', rowClass, search = true }) {
  const [q, setQ] = useState('');
  const [sort, setSort] = useState(null);
  const [page, setPage] = useState(0);
  const [size, setSize] = useState(pageSizes[0]);
  const data = rows || [];
  const filtered = useMemo(() => {
    const n = norm(q).trim();
    let out = n ? data.filter((r) => columns.some((c) => c.searchable !== false && c.key !== 'actions' && norm(c.text ? c.text(r) : r[c.key]).includes(n))) : data;
    if (sort) {
      const c = columns.find((x) => x.key === sort.key);
      const val = (r) => (c.sortValue ? c.sortValue(r) : c.text ? c.text(r) : r[c.key]);
      out = [...out].sort((a, b) => { const x = val(a), y = val(b); const r = typeof x === 'number' && typeof y === 'number' ? x - y : String(x ?? '').localeCompare(String(y ?? ''), 'fr', { numeric: true }); return sort.dir === 'asc' ? r : -r; });
    }
    return out;
  }, [data, q, sort, columns]);
  useEffect(() => setPage(0), [q, size, rows]);
  const pages = Math.max(1, Math.ceil(filtered.length / size));
  const cur = Math.min(page, pages - 1);
  const view = filtered.slice(cur * size, cur * size + size);
  const toggle = (c) => { if (c.sortable === false || c.key === 'actions') return; setSort((s) => (s?.key === c.key ? (s.dir === 'asc' ? { key: c.key, dir: 'desc' } : null) : { key: c.key, dir: 'asc' })); };
  return (
    <div className="card table-card">
      <div className="table-bar">
        {search && <div className="search"><Search size={15} /><input value={q} onChange={(e) => setQ(e.target.value)} placeholder={searchPlaceholder} aria-label="Recherche" />{q && <button className="icon-btn" onClick={() => setQ('')}><X size={13} /></button>}</div>}
        <div className="table-tools">{toolbar}</div>
      </div>
      <div className="table-wrap">
        <table className="table">
          <thead><tr>{columns.map((c) => (
            <th key={c.key} style={{ width: c.width, textAlign: c.align }} className={c.sortable === false || c.key === 'actions' ? '' : 'sortable'} onClick={() => toggle(c)}>
              <span>{c.label}{sort?.key === c.key && (sort.dir === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />)}</span></th>))}</tr></thead>
          <tbody>
            {loading && Array.from({ length: 5 }).map((_, i) => <tr key={i}>{columns.map((c) => <td key={c.key}><Skeleton h={12} /></td>)}</tr>)}
            {!loading && view.map((r, i) => (
              <motion.tr key={r[rowKey] ?? i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: Math.min(i, 10) * .015 }}
                onDoubleClick={() => onRowDoubleClick?.(r)} className={`${onRowDoubleClick ? 'clickable' : ''} ${rowClass ? rowClass(r) : ''}`}>
                {columns.map((c) => <td key={c.key} style={{ textAlign: c.align }}>{c.render ? c.render(r, cur * size + i) : r[c.key]}</td>)}
              </motion.tr>))}
          </tbody>
        </table>
        {!loading && filtered.length === 0 && (empty || <EmptyState title={q ? 'Aucun résultat' : 'Aucune donnée'} text={q ? 'Modifiez votre recherche.' : 'Rien à afficher pour le moment.'} />)}
      </div>
      <div className="table-foot">
        <span className="muted">{filtered.length === 0 ? '0 résultat' : `${cur * size + 1}–${Math.min(filtered.length, cur * size + size)} sur ${filtered.length}`}</span>
        <div className="pager">
          <select className="input input-sm" value={size} onChange={(e) => setSize(Number(e.target.value))} aria-label="Lignes par page">{pageSizes.map((s) => <option key={s} value={s}>{s} / page</option>)}</select>
          <button className="icon-btn" disabled={cur === 0} onClick={() => setPage(cur - 1)} aria-label="Page précédente"><ChevronLeft size={16} /></button>
          <span className="muted">{cur + 1} / {pages}</span>
          <button className="icon-btn" disabled={cur >= pages - 1} onClick={() => setPage(cur + 1)} aria-label="Page suivante"><ChevronRight size={16} /></button>
        </div>
      </div>
    </div>
  );
}

export const IconBtn = ({ icon: I, label, onClick, tone, disabled }) => (
  <button className={`icon-btn ${tone ? `tone-${tone}` : ''}`} title={label} aria-label={label} onClick={(e) => { e.stopPropagation(); onClick?.(e); }} disabled={disabled}><I size={16} /></button>
);
