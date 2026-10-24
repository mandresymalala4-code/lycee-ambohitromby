import { useState } from 'react';
import { Download, ExternalLink, FileText, Info, Maximize2, Minimize2, Database } from 'lucide-react';
import { Logo, Modal, Tabs } from './ui';
import { useSettings } from './context';

export const MPD_URL = '/documentation/mpd.pdf';

export default function About({ open, onClose }) {
  const { etab } = useSettings();
  const [tab, setTab] = useState('mpd');
  const [full, setFull] = useState(false);
  const [loaded, setLoaded] = useState(false);
  return (
    <Modal open={open} onClose={onClose} size={full ? 'full' : 'xl'} title="À propos"
      footer={<>
        <button className="btn btn-ghost" onClick={() => setFull((f) => !f)}>{full ? <Minimize2 size={15} /> : <Maximize2 size={15} />}{full ? 'Réduire' : 'Agrandir'}</button>
        <a className="btn btn-ghost" href={MPD_URL} target="_blank" rel="noreferrer"><ExternalLink size={15} />Ouvrir dans un onglet</a>
        <a className="btn btn-primary" href={MPD_URL} download="MPD_Lycee_Ambohitromby.pdf"><Download size={15} />Télécharger le MPD</a>
      </>}>
      <Tabs value={tab} onChange={setTab} tabs={[{ value: 'mpd', label: 'MPD (PDF)', icon: <Database size={15} /> }, { value: 'app', label: 'Application', icon: <Info size={15} /> }]} />
      {tab === 'app' ? (
        <div className="about-app">
          <div className="row"><Logo size={64} src={etab.logo} /><div><h2 style={{ fontSize: 18 }}>{etab.nom}</h2><p className="muted">Gestion d'étude dans un lycée · version 1.1</p></div></div>
          <dl className="kv mt">
            <dt>Établissement</dt><dd>{etab.adresse || '—'}</dd><dt>Contact</dt><dd>{etab.telephone || '—'} {etab.email ? `· ${etab.email}` : ''}</dd>
            <dt>Backend</dt><dd>Python 3.12 · Django 5.2 · Django REST Framework · JWT</dd><dt>Frontend</dt><dd>React 18 · Vite · Recharts · Framer Motion</dd>
            <dt>Base de données</dt><dd>MySQL / MariaDB (XAMPP) · utf8mb4</dd><dt>Documentation</dt><dd>Le MPD (Modèle Physique des Données) est consultable dans l'onglet « MPD (PDF) ».</dd>
          </dl>
        </div>
      ) : (
        <div className={`pdf-frame ${full ? 'pdf-full' : ''}`}>
          {!loaded && <div className="pdf-loading"><FileText size={28} /><span>Chargement du document…</span></div>}
          <iframe title="Modèle Physique des Données (MPD)" src={`${MPD_URL}#view=FitH&toolbar=1`} onLoad={() => setLoaded(true)} />
          <p className="muted pdf-fallback">Le PDF ne s'affiche pas ? <a href={MPD_URL} target="_blank" rel="noreferrer">Ouvrez-le dans un onglet</a> ou téléchargez-le.</p>
        </div>
      )}
    </Modal>
  );
}
