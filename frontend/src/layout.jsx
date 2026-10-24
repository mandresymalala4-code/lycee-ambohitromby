import { useEffect, useRef, useState } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Bell, BookOpen, CalendarDays, ClipboardCheck, FileText, GraduationCap, LayoutDashboard, LogOut, Menu, Moon, PanelLeftClose, PanelLeftOpen, Settings, Sun, UserCircle, UserPlus, Users, School, Award, ClipboardList, KeyRound, Info } from 'lucide-react';
import { api, parseErr } from './api';
import { useAuth, useSettings, useYear } from './context';
import { Avatar, Logo, Modal, Field, Spinner, useToast } from './ui';
import { rules } from './validators';
import About from './About';
import { useForm } from 'react-hook-form';

const ADMIN = [['/', 'Tableau de bord', LayoutDashboard], ['/classes', 'Classes', School], ['/eleves', 'Élèves', GraduationCap], ['/inscription', 'Inscription', UserPlus],
  ['/professeurs', 'Professeurs', Users], ['/matieres', 'Matières', BookOpen], ['/emploi-du-temps', 'Emploi du temps', CalendarDays], ['/absences', 'Absences', ClipboardCheck],
  ['/notes', 'Notes', ClipboardList], ['/resultats', 'Résultats & bulletins', Award], ['/parametres', 'Paramètres', Settings], ['/profil', 'Mon profil', UserCircle]];
const PROF = ADMIN.filter(([p]) => !['/inscription', '/resultats', '/parametres'].includes(p));

export function YearSelector() {
  const { annees, annee, courante, setAnnee } = useYear();
  if (!annee) return null;
  return (
    <select className="input input-sm" style={{ fontWeight: 600 }} value={annee.id} onChange={(e) => setAnnee(e.target.value)} aria-label="Année scolaire">
      {annees.map((a) => <option key={a.id} value={a.id}>{a.libelle}{a.id === courante ? ' (courante)' : ''}</option>)}
    </select>
  );
}

function useOutside(ref, fn) {
  useEffect(() => { const h = (e) => { if (ref.current && !ref.current.contains(e.target)) fn(); }; document.addEventListener('mousedown', h); return () => document.removeEventListener('mousedown', h); }, [ref, fn]);
}

function RouteBar() {
  const loc = useLocation();
  return <motion.div key={loc.pathname} className="route-bar" initial={{ scaleX: 0, opacity: 1 }} animate={{ scaleX: 1, opacity: [1, 1, 0] }} transition={{ duration: .7, ease: 'easeOut' }} />;
}

function Notifs() {
  const [open, setOpen] = useState(false);
  const [list, setList] = useState([]);
  const ref = useRef(); const loc = useLocation(); const nav = useNavigate();
  useOutside(ref, () => setOpen(false));
  useEffect(() => { api.get('/notifications/').then((r) => setList(r.data)).catch(() => {}); }, [loc.pathname, open]);
  useEffect(() => { const t = setInterval(() => api.get('/notifications/').then((r) => setList(r.data)).catch(() => {}), 60000); return () => clearInterval(t); }, []);
  return (
    <div className="rel" ref={ref}>
      <button className="icon-btn" aria-label="Notifications" onClick={() => setOpen((o) => !o)}><Bell size={18} />{list.length > 0 && <span className="dot">{list.length}</span>}</button>
      {open && <div className="menu notif"><div className="menu-head"><b>Notifications</b></div>
        {list.length === 0 && <p className="muted" style={{ padding: 12 }}>Aucune notification.</p>}
        {list.map((n, i) => <a key={i} className="notif-item" href={n.lien} onClick={(e) => { e.preventDefault(); setOpen(false); nav(n.lien); }}>{n.message}</a>)}</div>}
    </div>
  );
}

function ForcePassword() {
  const { user, refreshUser, logout } = useAuth(); const toast = useToast();
  const { register, handleSubmit, getValues, formState: { errors, isSubmitting }, setError } = useForm();
  const submit = async (d) => {
    try { await api.put('/profil/', { ancien_mot_de_passe: d.ancien, nouveau_mot_de_passe: d.nouveau, confirmation: d.confirmation }); toast.success('Mot de passe modifié.'); await refreshUser(); }
    catch (e) { const { champs, message } = parseErr(e); Object.entries(champs).forEach(([k, v]) => setError({ ancien_mot_de_passe: 'ancien', nouveau_mot_de_passe: 'nouveau' }[k] || k, { message: v })); toast.error(message); }
  };
  return (
    <Modal open={!!user?.doit_changer_mdp} closable={false} title="Changez votre mot de passe" size="sm"
      footer={<><button className="btn btn-ghost" onClick={logout}>Se déconnecter</button><button className="btn btn-primary" disabled={isSubmitting} onClick={handleSubmit(submit)}>{isSubmitting && <Spinner size={14} />}Enregistrer</button></>}>
      <p className="muted mb">Votre mot de passe est provisoire. Choisissez-en un nouveau pour continuer.</p>
      <div className="stack">
        <Field label="Mot de passe actuel" error={errors.ancien?.message}><input type="password" className="input" {...register('ancien', { required: 'Ce champ est obligatoire.' })} /></Field>
        <Field label="Nouveau mot de passe" error={errors.nouveau?.message}><input type="password" className="input" {...register('nouveau', { validate: rules.mdp })} /></Field>
        <Field label="Confirmation" error={errors.confirmation?.message}><input type="password" className="input" {...register('confirmation', { validate: (v) => v === getValues('nouveau') || 'Les mots de passe ne correspondent pas.' })} /></Field>
      </div>
    </Modal>
  );
}

export default function Layout({ children }) {
  const { user, logout, setTheme } = useAuth();
  const { etab } = useSettings();
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem('sb_collapsed') === '1');
  const [open, setOpen] = useState(false);
  const [menu, setMenu] = useState(false);
  const [about, setAbout] = useState(false);
  const ref = useRef(); const loc = useLocation(); const nav = useNavigate();
  useOutside(ref, () => setMenu(false));
  useEffect(() => setOpen(false), [loc.pathname]);
  useEffect(() => { localStorage.setItem('sb_collapsed', collapsed ? '1' : '0'); }, [collapsed]);
  const items = user.role === 'ADMIN' ? ADMIN : PROF;
  const dark = user.theme === 'SOMBRE';
  return (
    <div className="app">
      <aside className={`sidebar ${collapsed ? 'collapsed' : ''} ${open ? 'open' : ''}`}>
        <div className="sb-brand"><Logo size={34} src={etab.logo} /><div><b>{etab.nom.toUpperCase()}</b><small>{user.role === 'ADMIN' ? 'Espace administrateur' : 'Espace professeur'}</small></div></div>
        <nav className="nav">{items.map(([to, label, I]) => (
          <NavLink key={to} to={to} end={to === '/'} title={label}>
            {({ isActive }) => <>{isActive && <motion.span layoutId="navpill" className="nav-pill" transition={{ type: 'spring', stiffness: 420, damping: 34 }} />}<I size={18} /><span>{label}</span></>}
          </NavLink>))}</nav>
        <div className="sb-foot"><button onClick={() => setAbout(true)} title="À propos"><Info size={18} /><span>À propos</span></button><button onClick={() => setCollapsed((c) => !c)} className="hide-sm">{collapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}<span>Réduire le menu</span></button></div>
      </aside>
      <div className={`scrim ${open ? 'on' : ''}`} onClick={() => setOpen(false)} />
      <div className={`main ${collapsed ? 'collapsed' : ''}`}>
        <RouteBar />
        <header className="topbar">
          <button className="icon-btn burger" aria-label="Menu" onClick={() => setOpen(true)}><Menu size={20} /></button>
          <YearSelector /><div className="grow" />
          <button className="btn btn-ghost btn-sm about-btn" onClick={() => setAbout(true)}><Info size={15} /><span className="hide-sm">À propos</span></button>
          <Notifs />
          <button className="icon-btn" aria-label="Changer de thème" onClick={() => setTheme(dark ? 'CLAIR' : 'SOMBRE')}>{dark ? <Sun size={18} /> : <Moon size={18} />}</button>
          <div className="rel" ref={ref}>
            <button className="icon-btn" style={{ width: 38, height: 38 }} onClick={() => setMenu((m) => !m)} aria-label="Compte"><Avatar src={user.photo} name={user.nom_complet} size={32} /></button>
            {menu && <div className="menu">
              <div className="menu-head"><b>{user.nom_complet}</b><div className="muted" style={{ fontSize: 11 }}>{user.role === 'ADMIN' ? 'Administrateur' : `Professeur · ${user.professeur?.discipline_nom}`}</div></div>
              <button className="menu-item" onClick={() => { setMenu(false); nav('/profil'); }}><UserCircle size={16} />Mon profil</button>
              <button className="menu-item" onClick={logout}><LogOut size={16} />Se déconnecter</button></div>}
          </div>
        </header>
        <main className="content"><div className="content-in">{children}</div></main>
      </div>
      <ForcePassword />
      <About open={about} onClose={() => setAbout(false)} />
    </div>
  );
}
