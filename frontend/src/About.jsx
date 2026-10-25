import { useEffect, useState } from 'react';
import { Download, ExternalLink, FileText, Info, Maximize2, Minimize2, Database, Moon, Sun } from 'lucide-react';
import { Logo, Modal, Tabs } from './ui';
import { useAuth, useSettings } from './context';

export const MPD_URL = '/documentation/mpd.pdf';
export const MPD_NUIT_URL = '/documentation/mpd-nuit.pdf';

export default function About({ open, onClose }) {
  const { etab } = useSettings();
  const { user } = useAuth();
  const sombre = user?.theme === 'SOMBRE';
  const [tab, setTab] = useState('mpd');
  const [full, setFull] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [nuitDispo, setNuitDispo] = useState(false);   // une version « nuit » du PDF existe-t-elle ?
  const [choix, setChoix] = useState(null);            // null = automatique, true = nuit, false = clair

  useEffect(() => {
    if (!open) return;
    fetch(MPD_NUIT_URL, { method: 'HEAD', cache: 'no-store' })
      .then((r) => setNuitDispo(r.ok && (r.headers.get('content-type') || '').includes('pdf')))
      .catch(() => setNuitDispo(false));
  }, [open]);

  const veutNuit = sombre && (choix === null ? nuitDispo : choix);
  const versionNuit = veutNuit && nuitDispo;          // PDF « nuit » natif
  const filtre = veutNuit && !nuitDispo;              // PDF personnalisé : inversion des couleurs
  const src = versionNuit ? MPD_NUIT_URL : MPD_URL;
  useEffect(() => { setLoaded(false); }, [src]);

  return (
    <Modal open={open} onClose={onClose} size={full ? 'full' : 'xl'} title="À propos"
      footer={<>
        {sombre && tab === 'mpd' && (
          <button className="btn btn-ghost" onClick={() => setChoix(!veutNuit)}>
            {veutNuit ? <Sun size={15} /> : <Moon size={15} />}{veutNuit ? 'PDF : version claire' : 'PDF : version nuit'}
          </button>)}
        <button className="btn btn-ghost" onClick={() => setFull((f) => !f)}>{full ? <Minimize2 size={15} /> : <Maximize2 size={15} />}{full ? 'Réduire' : 'Agrandir'}</button>
        <a className="btn btn-ghost" href={src} target="_blank" rel="noreferrer"><ExternalLink size={15} />Ouvrir dans un onglet</a>
        <a className="btn btn-primary" href={src} download={versionNuit ? 'MPD_Lycee_Ambohitromby_nuit.pdf' : 'MPD_Lycee_Ambohitromby.pdf'}><Download size={15} />Télécharger le MPD</a>
      </>}>
      <Tabs value={tab} onChange={setTab} tabs={[{ value: 'mpd', label: 'MPD (PDF)', icon: <Database size={15} /> }, { value: 'app', label: 'Application', icon: <Info size={15} /> }]} />
      {tab === 'app' ? (
        <div className="about-app">
          <div className="row"><Logo size={64} src={etab.logo} /><div><h2 style={{ fontSize: 18 }}>{etab.nom}</h2><p className="muted">Gestion d'étude dans un lycée · version 1.2</p></div></div>
          <dl className="kv mt">
            <dt>Établissement</dt><dd>{etab.adresse || '—'}</dd><dt>Contact</dt><dd>{etab.telephone || '—'} {etab.email ? `· ${etab.email}` : ''}</dd>
            <dt>Backend</dt><dd>Python 3.12 · Django 5.2 · Django REST Framework · JWT</dd><dt>Frontend</dt><dd>React 18 · Vite · Recharts · Framer Motion</dd>
            <dt>Base de données</dt><dd>MySQL / MariaDB (XAMPP) ou SQLite (hébergement gratuit)</dd><dt>Documentation</dt><dd>Le MPD (Modèle Physique des Données) est consultable dans l'onglet « MPD (PDF) ».</dd>
          </dl>
        </div>
      ) : (
        <div className={`pdf-frame ${full ? 'pdf-full' : ''} ${filtre ? 'pdf-inverse' : ''}`}>
          {!loaded && <div className="pdf-loading"><FileText size={28} /><span>Chargement du document…</span></div>}
          <iframe key={src} title="Modèle Physique des Données (MPD)" src={`${src}#view=FitH&toolbar=1`} onLoad={() => setLoaded(true)} />
          <p className="muted pdf-fallback">Le PDF ne s'affiche pas ? <a href={src} target="_blank" rel="noreferrer">Ouvrez-le dans un onglet</a> ou téléchargez-le.</p>
        </div>
      )}
    </Modal>
  );
}
