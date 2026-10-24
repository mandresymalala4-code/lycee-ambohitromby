import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { Building2, CalendarRange, Lock, LockOpen, Moon, Palette, Save, Sun, Trash2 } from 'lucide-react';
import { api, applyErrors, parseErr, toForm } from '../api';
import { useAuth, useFetch, useSettings, useYear } from '../context';
import { Badge, Field, Logo, PageHeader, Spinner, Tabs, useToast } from '../ui';
import { rules } from '../validators';

function Etab() {
  const { etab, reload } = useSettings(); const toast = useToast();
  const { register, handleSubmit, reset, setError, formState: { errors, isSubmitting } } = useForm();
  const [logo, setLogo] = useState(null); const [prev, setPrev] = useState(null); const [sup, setSup] = useState(false); const [err, setErr] = useState('');
  useEffect(() => { reset({ nom: etab.nom, adresse: etab.adresse, telephone: etab.telephone, email: etab.email }); }, [etab]); // eslint-disable-line
  useEffect(() => { if (!logo) { setPrev(null); return undefined; } const u = URL.createObjectURL(logo); setPrev(u); return () => URL.revokeObjectURL(u); }, [logo]);
  const submit = async (d) => {
    try { await api.put('/parametres/', toForm({ ...d, logo, supprimer_logo: sup ? 'true' : '' }), { headers: { 'Content-Type': 'multipart/form-data' } }); toast.success('Paramètres enregistrés.'); setLogo(null); setSup(false); reload(); }
    catch (e) { toast.error(parseErr(e).message); applyErrors(e, setError); }
  };
  const E = errors;
  return (
    <form className="card" onSubmit={handleSubmit(submit)} noValidate>
      <div className="form-grid">
        <Field label="Nom de l'établissement" required error={E.nom?.message} className="full"><input className="input" {...register('nom', { validate: (v) => (v.trim().length >= 2 && v.trim().length <= 100) || 'Le nom doit contenir entre 2 et 100 caractères.' })} /></Field>
        <Field label="Adresse" required error={E.adresse?.message} className="full"><input className="input" {...register('adresse', { validate: rules.adresse })} /></Field>
        <Field label="Téléphone" required error={E.telephone?.message}><input className="input" {...register('telephone', { validate: rules.telFixe })} /></Field>
        <Field label="Email" error={E.email?.message}><input className="input" {...register('email', { validate: (v) => !v || rules.email(v) })} /></Field>
        <div className="photo-drop full">
          {sup ? <Logo size={64} /> : <Logo size={64} src={prev || etab.logo} />}
          <Field label="Logo de l'établissement" error={err} hint="JPG ou PNG, 2 Mo maximum. Utilisé dans l'application et les PDF.">
            <input type="file" accept=".jpg,.jpeg,.png" className="input" onChange={(e) => { const f = e.target.files[0]; const r = rules.photo(f ? [f] : null); if (r !== true) { setErr('Format de logo non accepté.'); e.target.value = ''; setLogo(null); } else { setErr(''); setLogo(f || null); setSup(false); } }} /></Field>
          {etab.logo && <button type="button" className="btn btn-ghost btn-sm" onClick={() => { setSup(true); setLogo(null); }}><Trash2 size={14} />Revenir au logo provisoire</button>}
        </div>
      </div>
      <div className="row row-end mt"><button className="btn btn-primary" disabled={isSubmitting}>{isSubmitting ? <Spinner size={14} /> : <Save size={16} />}Enregistrer</button></div>
    </form>
  );
}

function Annees() {
  const { annee, annees, courante, reloadYears, reload } = useYear(); const toast = useToast();
  const { data, loading, reload: rl } = useFetch(`/annees/${annee?.id}/trimestres/`, null, [], !!annee);
  const [ts, setTs] = useState([]); const [busy, setBusy] = useState(false);
  useEffect(() => { if (data) setTs(data.map((t) => ({ ...t }))); }, [data]);
  const setCourante = async (id) => { try { const { data: p } = await api.get('/parametres/'); await api.put('/parametres/', toForm({ nom: p.etablissement.nom, adresse: p.etablissement.adresse, telephone: p.etablissement.telephone, email: p.etablissement.email, annee_courante: id }), { headers: { 'Content-Type': 'multipart/form-data' } }); toast.success('Année courante modifiée.'); reloadYears(); } catch (e) { toast.error(parseErr(e).message); } };
  const saveDates = async () => { setBusy(true); try { await api.put(`/annees/${annee.id}/trimestres/`, { trimestres: ts.map((t) => ({ numero: t.numero, date_debut: t.date_debut, date_fin: t.date_fin })) }); toast.success('Dates des trimestres enregistrées.'); rl(); reload(); } catch (e) { toast.error(parseErr(e).message); } finally { setBusy(false); } };
  const cloture = async (t) => { try { await api.post(`/trimestres/${t.id}/cloture/`, { cloture: !t.cloture }); toast.success(t.cloture ? 'Trimestre rouvert.' : 'Trimestre clôturé.'); rl(); } catch (e) { toast.error(parseErr(e).message); } };
  return (
    <div className="stack">
      <div className="card"><h3>Année scolaire courante</h3><p className="muted mb">Année utilisée par défaut à l'ouverture de l'application.</p>
        <select className="input" style={{ maxWidth: 260 }} value={courante || ''} onChange={(e) => setCourante(e.target.value)}>{annees.map((a) => <option key={a.id} value={a.id}>{a.libelle}</option>)}</select></div>
      <div className="card"><h3>Trimestres · {annee?.libelle}</h3><p className="muted mb">Dates (année choisie dans le sélecteur en haut). Un trimestre clôturé n'est plus modifiable par les professeurs.</p>
        {loading ? <Spinner /> : ts.map((t, i) => (
          <div className="row mb" key={t.id}><b style={{ width: 110 }}>{t.numero === 1 ? '1er' : `${t.numero}ème`} trimestre</b>
            <input type="date" className="input input-sm" value={t.date_debut} onChange={(e) => setTs((l) => l.map((x, j) => (j === i ? { ...x, date_debut: e.target.value } : x)))} /><span>→</span>
            <input type="date" className="input input-sm" value={t.date_fin} onChange={(e) => setTs((l) => l.map((x, j) => (j === i ? { ...x, date_fin: e.target.value } : x)))} />
            {t.cloture ? <Badge tone="red">Clôturé</Badge> : <Badge tone="green">Ouvert</Badge>}
            <button className="btn btn-ghost btn-sm" onClick={() => cloture(t)}>{t.cloture ? <LockOpen size={14} /> : <Lock size={14} />}{t.cloture ? 'Rouvrir' : 'Clôturer'}</button></div>))}
        <div className="row row-end"><button className="btn btn-primary" onClick={saveDates} disabled={busy}>{busy ? <Spinner size={14} /> : <Save size={16} />}Enregistrer les dates</button></div></div>
    </div>
  );
}

function Apparence() {
  const { user, setTheme } = useAuth();
  return (
    <div className="card"><h3>Thème de l'interface</h3><p className="muted mb">Enregistré sur votre compte.</p>
      <div className="row"><button className={`btn ${user.theme === 'CLAIR' ? 'btn-primary' : 'btn-ghost'}`} onClick={() => setTheme('CLAIR')}><Sun size={16} />Clair</button><button className={`btn ${user.theme === 'SOMBRE' ? 'btn-primary' : 'btn-ghost'}`} onClick={() => setTheme('SOMBRE')}><Moon size={16} />Sombre</button></div></div>
  );
}

export default function Parametres() {
  const [tab, setTab] = useState('etab');
  return (
    <>
      <PageHeader title="Paramètres" subtitle="Établissement, années scolaires et apparence" />
      <Tabs value={tab} onChange={setTab} tabs={[{ value: 'etab', label: 'Établissement', icon: <Building2 size={15} /> }, { value: 'annees', label: 'Années & trimestres', icon: <CalendarRange size={15} /> }, { value: 'theme', label: 'Apparence', icon: <Palette size={15} /> }]} />
      {tab === 'etab' && <Etab />}{tab === 'annees' && <Annees />}{tab === 'theme' && <Apparence />}
    </>
  );
}
