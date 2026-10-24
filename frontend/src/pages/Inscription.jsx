import { useEffect, useRef, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { ArrowLeft, ArrowRight, Receipt, Search, UserPlus } from 'lucide-react';
import { api, applyErrors, openPdf, parseErr, toForm } from '../api';
import { useFetch, useYear } from '../context';
import { Avatar, ConfirmDialog, Field, PageHeader, Spinner, Stepper, SuccessCheck, useToast } from '../ui';
import { ariary, rules } from '../validators';
import { ElevePhotoField, FamilleFields } from './Eleves';

const MODES = ['Espèces', 'MVola', 'Orange Money', 'Airtel Money', 'Chèque/Virement'];
const STEPS = ['Classe', 'Élève', 'Famille', 'Paiement'];
const FIELDS = [['classe'], ['eleve.nom', 'eleve.prenoms', 'eleve.date_naissance', 'eleve.sexe', 'eleve.adresse', 'eleve.observation'],
  ['famille.pere_nom', 'famille.pere_prenoms', 'famille.mere_nom', 'famille.mere_prenoms', 'famille.tuteur_nom', 'famille.tuteur_prenoms', 'famille.tuteur_contact', 'famille.contact_parent', 'famille.adresse_parents'], ['mode_paiement']];
const FAM = ['pere_nom', 'pere_prenoms', 'mere_nom', 'mere_prenoms', 'contact_parent', 'adresse_parents', 'tuteur_nom', 'tuteur_prenoms', 'tuteur_contact'];

export default function Inscription() {
  const { annee, reload } = useYear(); const toast = useToast(); const nav = useNavigate();
  const { data: classes } = useFetch('/classes/', { annee: annee?.id }, [], !!annee);
  const { register, handleSubmit, trigger, watch, setValue, getValues, reset, setError, formState: { errors, isSubmitting } } = useForm({ shouldUnregister: false, defaultValues: { mode_paiement: '' } });
  const [step, setStep] = useState(0); const [dir, setDir] = useState(1); const [file, setFile] = useState(null);
  const [existant, setExistant] = useState(null); const [q, setQ] = useState(''); const [res, setRes] = useState([]);
  const [rattacher, setRattacher] = useState(false); const [done, setDone] = useState(null);
  const timer = useRef();
  const classeSel = classes?.find((c) => String(c.id) === String(watch('classe')));

  useEffect(() => {
    clearTimeout(timer.current);
    if (q.trim().length < 2) { setRes([]); return undefined; }
    timer.current = setTimeout(() => api.get('/eleves/recherche/', { params: { q } }).then((r) => setRes(r.data)).catch(() => {}), 250);
    return () => clearTimeout(timer.current);
  }, [q]);

  const choisir = (e) => {
    setExistant(e); setRes([]); setQ('');
    setValue('eleve', { nom: e.nom, prenoms: e.prenoms, date_naissance: e.date_naissance, sexe: e.sexe, adresse: e.adresse, observation: e.observation });
    setValue('famille', e.famille);
  };
  const lookup = async () => {
    const c = (getValues('famille.contact_parent') || '').replace(/\s/g, '');
    if (!/^03\d{8}$/.test(c) || existant) return;
    try { const { data } = await api.get('/familles/par-contact/', { params: { contact: c } }); if (data.famille && !getValues('famille.adresse_parents')) { Object.entries(data.famille).forEach(([k, v]) => setValue(`famille.${k}`, v)); toast.info('Famille existante : informations préremplies.'); } } catch { /* ignore */ }
  };
  const next = async () => { if (await trigger(FIELDS[step])) { setDir(1); setStep((s) => s + 1); } };
  const prev = () => { setDir(-1); setStep((s) => s - 1); };

  const submit = async (d, rat = false) => {
    const body = { annee: annee.id, classe: Number(d.classe), eleve_id: existant?.id || null, eleve: d.eleve, famille: d.famille, mode_paiement: d.mode_paiement, rattacher_famille: rat };
    try {
      const { data } = await api.post('/inscriptions/', body);
      if (file) { try { await api.post(`/eleves/${data.id}/photo/`, toForm({ photo: file }), { headers: { 'Content-Type': 'multipart/form-data' } }); } catch (e) { toast.error(parseErr(e).message); } }
      setDone(data); reload(); toast.success('Inscription enregistrée.');
    } catch (e) {
      const p = parseErr(e);
      if (p.code === 'FAMILLE_EXISTE') { setRattacher(d); return; }
      toast.error(p.message);
      Object.entries(p.champs).forEach(([k, v]) => setError(FAM.includes(k) ? `famille.${k}` : ['nom', 'prenoms', 'date_naissance', 'sexe', 'adresse', 'observation'].includes(k) ? `eleve.${k}` : k, { message: v }));
      if (p.code === 'DEJA_INSCRIT' || p.status === 409) { setStep(1); }
    }
  };
  const again = () => { reset({ mode_paiement: '' }); setDone(null); setStep(0); setFile(null); setExistant(null); };

  if (done) return (
    <><PageHeader title="Inscription" />
      <div className="card" style={{ textAlign: 'center', padding: 40 }}><div style={{ display: 'grid', placeItems: 'center', gap: 10 }}><SuccessCheck />
        <h2>Inscription réussie</h2><p>{done.nom} {done.prenoms} · matricule <b>{done.matricule}</b> · {done.classe_nom}</p>
        <p className="muted">Reçu {done.paiement.numero_recu} · {ariary(done.paiement.total)}</p>
        <div className="row" style={{ justifyContent: 'center' }}><button className="btn btn-primary" onClick={() => openPdf(`/inscriptions/${done.id}/recu/`).catch((e) => toast.error(e.message))}><Receipt size={16} />Imprimer le reçu</button>
          <button className="btn btn-ghost" onClick={again}><UserPlus size={16} />Nouvelle inscription</button><button className="btn btn-ghost" onClick={() => nav('/eleves')}>Voir les élèves</button></div></div></div></>
  );
  const E = errors; const Ee = E.eleve || {};
  const panels = [
    <div key="0" className="form-grid">
      <Field label="Année scolaire"><input className="input" value={annee?.libelle || ''} disabled readOnly /></Field>
      <Field label="Classe" required error={E.classe?.message}><select className="input" {...register('classe', { required: 'Veuillez choisir une classe.' })}><option value="">Choisir une classe…</option>{classes?.map((c) => <option key={c.id} value={c.id}>{c.nom}</option>)}</select></Field>
      {classeSel && <div className="full info-bar">Frais de la classe : droit d'inscription {ariary(classeSel.droit_inscription)} + caisse de soutien {ariary(classeSel.caisse_soutien)} = <b>{ariary(classeSel.total)}</b></div>}
      <div className="full card" style={{ background: 'var(--surface-2)', boxShadow: 'none' }}>
        <h3>Réinscription d'un élève déjà enregistré</h3>
        <div className="search" style={{ maxWidth: 'none' }}><Search size={15} /><input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Nom, prénom ou matricule…" /></div>
        {res.map((r) => <div key={r.id} className="list-item" style={{ cursor: 'pointer' }} onClick={() => choisir(r)}><div className="cell-person"><Avatar src={r.photo} name={r.nom} size={28} /><b>{r.nom} {r.prenoms}</b></div><span className="muted">{r.matricule}</span></div>)}
        {existant && <div className="info-bar mt" style={{ marginBottom: 0 }}>Élève sélectionné : <b>{existant.nom} {existant.prenoms}</b> ({existant.matricule})<button className="btn btn-ghost btn-sm" onClick={() => { setExistant(null); setValue('eleve', {}); }}>Annuler</button></div>}
      </div>
    </div>,
    <div key="1" className="form-grid">
      <Field label="Nom" required error={Ee.nom?.message} hint="En majuscules"><input className="input" {...register('eleve.nom', { validate: rules.nom })} /></Field>
      <Field label="Prénoms" required error={Ee.prenoms?.message}><input className="input" {...register('eleve.prenoms', { validate: rules.prenom })} /></Field>
      <Field label="Date de naissance" required error={Ee.date_naissance?.message}><input type="date" className="input" {...register('eleve.date_naissance', { validate: rules.naissanceEleve })} /></Field>
      <Field label="Sexe" required error={Ee.sexe?.message}><select className="input" {...register('eleve.sexe', { required: 'Veuillez sélectionner le sexe.' })}><option value="">Choisir…</option><option>Garçon</option><option>Fille</option></select></Field>
      <Field label="Adresse" required error={Ee.adresse?.message}><input className="input" {...register('eleve.adresse', { validate: rules.adresse })} /></Field>
      <Field label="Observation" error={Ee.observation?.message}><input className="input" maxLength={255} {...register('eleve.observation')} /></Field>
      {!existant && <ElevePhotoField file={file} setFile={setFile} name="Élève" />}
    </div>,
    <div key="2" className="form-grid"><FamilleFields register={register} errors={E} prefix="famille." /></div>,
    <div key="3" className="stack">
      <Field label="Mode de paiement" required error={E.mode_paiement?.message}><select className="input" {...register('mode_paiement', { required: 'Veuillez choisir le mode de paiement.' })}><option value="">Choisir…</option>{MODES.map((m) => <option key={m}>{m}</option>)}</select></Field>
      <div className="card" style={{ background: 'var(--surface-2)', boxShadow: 'none' }}><h3>Récapitulatif</h3>
        <dl className="kv"><dt>Élève</dt><dd>{watch('eleve.nom')} {watch('eleve.prenoms')}</dd><dt>Classe</dt><dd>{classeSel?.nom}</dd><dt>Année</dt><dd>{annee?.libelle}</dd>
          <dt>Droit d'inscription</dt><dd>{ariary(classeSel?.droit_inscription)}</dd><dt>Caisse de soutien</dt><dd>{ariary(classeSel?.caisse_soutien)}</dd><dt>Total à payer</dt><dd><b style={{ fontSize: 16 }}>{ariary(classeSel?.total)}</b></dd></dl></div>
    </div>,
  ];
  return (
    <>
      <PageHeader title="Inscription d'un élève" subtitle={`Année scolaire ${annee?.libelle || ''}`} />
      <div className="card"><Stepper steps={STEPS} current={step} />
        <AnimatePresence mode="wait" custom={dir}><motion.div key={step} initial={{ opacity: 0, x: 30 * dir }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -30 * dir }} transition={{ duration: .22 }}>{panels[step]}</motion.div></AnimatePresence>
        <div className="row mt" style={{ justifyContent: 'space-between' }}>
          <button className="btn btn-ghost" onClick={prev} disabled={step === 0}><ArrowLeft size={16} />Précédent</button>
          {step < 3 ? <button className="btn btn-primary" onClick={next}>Suivant<ArrowRight size={16} /></button>
            : <button className="btn btn-ok" disabled={isSubmitting} onClick={handleSubmit((d) => submit(d))}>{isSubmitting && <Spinner size={14} />}Valider l'inscription</button>}
        </div>
      </div>
      <ConfirmDialog open={!!rattacher} title="Famille existante" confirmLabel="Rattacher" message="Cette famille existe déjà. Rattacher cet élève à cette famille ?" onCancel={() => setRattacher(false)} onConfirm={() => { const d = rattacher; setRattacher(false); submit(d, true); }} />
    </>
  );
}
