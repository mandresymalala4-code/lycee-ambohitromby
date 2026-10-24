import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Edit3, Eye, FileText, GraduationCap, Printer, Receipt, Trash2, UserPlus } from 'lucide-react';
import { api, applyErrors, openPdf, parseErr, toForm } from '../api';
import { useAuth, useFetch, useYear } from '../context';
import { Avatar, Badge, ConfirmDialog, DataTable, EmptyState, Field, IconBtn, Modal, PageHeader, Spinner, useToast } from '../ui';
import { ariary, fmtDate, fmtDateTime, rules } from '../validators';

export function FamilleFields({ register, errors, prefix = '' }) {
  const n = (k) => `${prefix}${k}`; const e = (k) => (prefix ? errors[prefix.slice(0, -1)]?.[k]?.message : errors[k]?.message);
  const opt = (r) => ({ validate: (v) => !v || r(v) });
  return (
    <>
      <div className="section-title">Père</div>
      <Field label="Nom du père" error={e('pere_nom')}><input className="input" {...register(n('pere_nom'), opt(rules.nom))} /></Field>
      <Field label="Prénoms du père" error={e('pere_prenoms')}><input className="input" {...register(n('pere_prenoms'), opt(rules.prenom))} /></Field>
      <div className="section-title">Mère</div>
      <Field label="Nom de la mère" error={e('mere_nom')}><input className="input" {...register(n('mere_nom'), opt(rules.nom))} /></Field>
      <Field label="Prénoms de la mère" error={e('mere_prenoms')}><input className="input" {...register(n('mere_prenoms'), opt(rules.prenom))} /></Field>
      <div className="section-title">Tuteur (si différent)</div>
      <Field label="Nom du tuteur" error={e('tuteur_nom')}><input className="input" {...register(n('tuteur_nom'), opt(rules.nom))} /></Field>
      <Field label="Prénoms du tuteur" error={e('tuteur_prenoms')}><input className="input" {...register(n('tuteur_prenoms'), opt(rules.prenom))} /></Field>
      <Field label="Contact du tuteur" error={e('tuteur_contact')}><input className="input" {...register(n('tuteur_contact'), opt(rules.tel))} /></Field>
      <div className="section-title">Contact et adresse</div>
      <Field label="Contact parent" required error={e('contact_parent')}><input className="input" placeholder="034 00 000 00" {...register(n('contact_parent'), { validate: rules.tel })} /></Field>
      <Field label="Adresse des parents" required error={e('adresse_parents')}><input className="input" {...register(n('adresse_parents'), { validate: rules.adresse })} /></Field>
    </>
  );
}

export function ElevePhotoField({ file, setFile, current, name }) {
  const [url, setUrl] = useState(null);
  useEffect(() => { if (!file) { setUrl(null); return undefined; } const u = URL.createObjectURL(file); setUrl(u); return () => URL.revokeObjectURL(u); }, [file]);
  const [err, setErr] = useState('');
  return (
    <div className="photo-drop full">
      {url ? <img className="avatar" src={url} width={56} height={56} alt="" /> : <Avatar src={current} name={name} size={56} />}
      <Field label="Photo (facultatif)" error={err} hint="JPG ou PNG, 2 Mo maximum">
        <input type="file" accept=".jpg,.jpeg,.png" className="input" onChange={(e) => { const f = e.target.files[0]; const r = rules.photo(f ? [f] : null); if (r !== true) { setErr(r); setFile(null); e.target.value = ''; } else { setErr(''); setFile(f || null); } }} /></Field>
    </div>
  );
}

function Fiche({ id, onClose, onEdit, admin }) {
  const { data, loading } = useFetch(`/eleves/${id}/`, null, [id], !!id);
  const toast = useToast();
  const f = data?.famille; const p = data?.paiement;
  const recu = () => openPdf(`/inscriptions/${id}/recu/`).catch((e) => toast.error(e.message));
  return (
    <Modal open={!!id} onClose={onClose} title="Fiche de l'élève" size="lg" footer={<>
      {admin && p && <button className="btn btn-ghost" onClick={recu}><Receipt size={15} />Reçu PDF</button>}
      {admin && <button className="btn btn-ghost" onClick={() => onEdit(data)}><Edit3 size={15} />Modifier</button>}
      <button className="btn btn-primary" onClick={onClose}>Fermer</button></>}>
      {loading || !data ? <div style={{ display: 'grid', placeItems: 'center', padding: 40 }}><Spinner size={26} /></div> : (
        <div className="stack">
          <div className="row"><Avatar src={data.photo} name={`${data.nom} ${data.prenoms}`} size={72} />
            <div><h2>{data.nom} {data.prenoms}</h2><div className="row"><Badge tone="blue">{data.matricule}</Badge><Badge tone="green">{data.classe_nom}</Badge><Badge>{data.annee_libelle}</Badge></div></div></div>
          <div className="grid g2">
            <div className="card"><h3>Identité</h3><dl className="kv"><dt>Naissance</dt><dd>{fmtDate(data.date_naissance)}</dd><dt>Sexe</dt><dd>{data.sexe}</dd><dt>Adresse</dt><dd>{data.adresse}</dd><dt>Observation</dt><dd>{data.observation || '—'}</dd><dt>Inscrit le</dt><dd>{fmtDateTime(data.date_inscription)}</dd></dl></div>
            <div className="card"><h3>Famille</h3><dl className="kv"><dt>Père</dt><dd>{[f.pere_nom, f.pere_prenoms].join(' ').trim() || '—'}</dd><dt>Mère</dt><dd>{[f.mere_nom, f.mere_prenoms].join(' ').trim() || '—'}</dd>
              <dt>Tuteur</dt><dd>{[f.tuteur_nom, f.tuteur_prenoms].join(' ').trim() || '—'}{f.tuteur_contact ? ` · ${f.tuteur_contact}` : ''}</dd><dt>Contact</dt><dd>{f.contact_parent}</dd><dt>Adresse</dt><dd>{f.adresse_parents}</dd></dl></div>
          </div>
          {admin && p && <div className="card"><h3>Paiement</h3><dl className="kv"><dt>Reçu</dt><dd>{p.numero_recu} {p.statut === 'ANNULE' && <Badge tone="red">Annulé</Badge>}</dd><dt>Droit d'inscription</dt><dd>{ariary(p.droit_inscription)}</dd><dt>Caisse de soutien</dt><dd>{ariary(p.caisse_soutien)}</dd><dt>Total</dt><dd><b>{ariary(p.total)}</b></dd><dt>Mode</dt><dd>{p.mode_paiement}</dd></dl></div>}
        </div>)}
    </Modal>
  );
}

function EditEleve({ fiche, onClose, onSaved }) {
  const toast = useToast();
  const { register, handleSubmit, reset, setError, formState: { errors, isSubmitting } } = useForm();
  const [file, setFile] = useState(null); const [rattacher, setRattacher] = useState(false);
  useEffect(() => { if (fiche) { setFile(null); reset({ eleve: { nom: fiche.nom, prenoms: fiche.prenoms, date_naissance: fiche.date_naissance, sexe: fiche.sexe, adresse: fiche.adresse, observation: fiche.observation }, famille: fiche.famille }); } }, [fiche]); // eslint-disable-line
  const send = async (d, rat = false) => {
    try {
      await api.put(`/eleves/${fiche.id}/`, { eleve: d.eleve, famille: d.famille, rattacher_famille: rat });
      if (file) await api.post(`/eleves/${fiche.id}/photo/`, toForm({ photo: file }), { headers: { 'Content-Type': 'multipart/form-data' } });
      toast.success('Élève modifié.'); onSaved();
    } catch (e) { const p = parseErr(e); if (p.code === 'FAMILLE_EXISTE') setRattacher(d); else { toast.error(p.message); const m = {}; Object.entries(p.champs).forEach(([k, v]) => setError(`${['pere_nom', 'pere_prenoms', 'mere_nom', 'mere_prenoms', 'contact_parent', 'adresse_parents', 'tuteur_nom', 'tuteur_prenoms', 'tuteur_contact'].includes(k) ? 'famille' : 'eleve'}.${k}`, { message: v })); } }
  };
  const E = errors.eleve || {};
  return (
    <>
      <Modal open={!!fiche} onClose={onClose} title="Modifier l'élève" size="lg" footer={<><button className="btn btn-ghost" onClick={onClose}>Annuler</button><button className="btn btn-primary" disabled={isSubmitting} onClick={handleSubmit((d) => send(d))}>{isSubmitting && <Spinner size={14} />}Enregistrer</button></>}>
        {fiche && <form className="form-grid" noValidate onSubmit={handleSubmit((d) => send(d))}>
          <div className="section-title">Élève · {fiche.matricule}</div>
          <Field label="Nom" required error={E.nom?.message} hint="En majuscules"><input className="input" {...register('eleve.nom', { validate: rules.nom })} /></Field>
          <Field label="Prénoms" required error={E.prenoms?.message}><input className="input" {...register('eleve.prenoms', { validate: rules.prenom })} /></Field>
          <Field label="Date de naissance" required error={E.date_naissance?.message}><input type="date" className="input" {...register('eleve.date_naissance', { validate: rules.naissanceEleve })} /></Field>
          <Field label="Sexe" required error={E.sexe?.message}><select className="input" {...register('eleve.sexe', { required: 'Veuillez sélectionner le sexe.' })}><option>Garçon</option><option>Fille</option></select></Field>
          <Field label="Adresse" required error={E.adresse?.message}><input className="input" {...register('eleve.adresse', { validate: rules.adresse })} /></Field>
          <Field label="Observation" error={E.observation?.message}><input className="input" maxLength={255} {...register('eleve.observation')} /></Field>
          <ElevePhotoField file={file} setFile={setFile} current={fiche.photo} name={fiche.nom} />
          <FamilleFields register={register} errors={errors} prefix="famille." />
        </form>}
      </Modal>
      <ConfirmDialog open={!!rattacher} title="Famille existante" confirmLabel="Rattacher" message="Cette famille existe déjà. Rattacher cet élève à cette famille ?" onCancel={() => setRattacher(false)} onConfirm={() => { const d = rattacher; setRattacher(false); send(d, true); }} />
    </>
  );
}

export default function Eleves() {
  const { user } = useAuth(); const admin = user.role === 'ADMIN';
  const { annee } = useYear(); const toast = useToast(); const nav = useNavigate();
  const [sp, setSp] = useSearchParams();
  const classe = sp.get('classe') || ''; const sexe = sp.get('sexe') || '';
  const set = (k, v) => { const n = new URLSearchParams(sp); v ? n.set(k, v) : n.delete(k); setSp(n, { replace: true }); };
  const { data: classes } = useFetch('/classes/', { annee: annee?.id }, [], !!annee);
  const { data, loading, reload } = useFetch('/eleves/', { annee: annee?.id, classe: classe || undefined, sexe: sexe || undefined }, [], !!annee);
  const [fiche, setFiche] = useState(null); const [edit, setEdit] = useState(null); const [del, setDel] = useState(null); const [busy, setBusy] = useState(false);
  const cols = [
    { key: 'matricule', label: 'Matricule', render: (r) => <Badge tone="blue">{r.matricule}</Badge> },
    { key: 'nom', label: 'Nom', render: (r) => <div className="cell-person"><Avatar src={r.photo} name={`${r.nom} ${r.prenoms}`} size={30} /><b>{r.nom}</b></div> },
    { key: 'prenoms', label: 'Prénoms' },
    { key: 'date_naissance', label: 'Naissance', render: (r) => fmtDate(r.date_naissance) },
    { key: 'sexe', label: 'Sexe', render: (r) => <Badge tone={r.sexe === 'Fille' ? 'orange' : 'blue'}>{r.sexe}</Badge> },
    { key: 'adresse', label: 'Adresse' },
    { key: 'classe_nom', label: 'Classe', render: (r) => <Badge tone="green">{r.classe_nom}</Badge> },
    { key: 'actions', label: '', align: 'right', render: (r) => (<div className="row row-end"><IconBtn icon={Eye} label="Voir la fiche" onClick={() => setFiche(r.id)} />
      {admin && <><IconBtn icon={Edit3} label="Modifier" onClick={async () => { const { data: f } = await api.get(`/eleves/${r.id}/`); setEdit(f); }} /><IconBtn icon={Trash2} tone="danger" label="Supprimer" onClick={() => setDel(r)} /></>}</div>) },
  ];
  const pdf = () => openPdf('/eleves/pdf/', { annee: annee.id, classe: classe || undefined, sexe: sexe || undefined }).catch((e) => toast.error(e.message));
  const remove = async () => {
    setBusy(true);
    try { await api.delete(`/eleves/${del.id}/`); toast.success('Élève supprimé.'); setDel(null); reload(); } catch (e) { toast.error(parseErr(e).message); setDel(null); } finally { setBusy(false); }
  };
  return (
    <>
      <PageHeader title="Élèves" subtitle={`Année scolaire ${annee?.libelle || ''} · ${data?.length ?? 0} élève(s)`}
        actions={<><button className="btn btn-ghost" onClick={pdf}><Printer size={16} />Imprimer la liste</button>{admin && <button className="btn btn-primary" onClick={() => nav('/inscription')}><UserPlus size={16} />Nouvelle inscription</button>}</>} />
      <DataTable columns={cols} rows={data} loading={loading} onRowDoubleClick={(r) => setFiche(r.id)} searchPlaceholder="Rechercher par nom, prénom ou matricule…"
        toolbar={<><select className="input input-sm" value={classe} onChange={(e) => set('classe', e.target.value)} aria-label="Classe"><option value="">Toutes les classes</option>{classes?.map((c) => <option key={c.id} value={c.id}>{c.nom}</option>)}</select>
          <select className="input input-sm" value={sexe} onChange={(e) => set('sexe', e.target.value)} aria-label="Sexe"><option value="">Tous</option><option>Garçon</option><option>Fille</option></select></>}
        empty={<EmptyState icon={GraduationCap} title="Aucun élève" text="Aucun élève ne correspond à ces critères pour cette année." action={admin && <button className="btn btn-primary btn-sm" onClick={() => nav('/inscription')}>Inscrire un élève</button>} />} />
      <Fiche id={fiche} admin={admin} onClose={() => setFiche(null)} onEdit={(f) => { setFiche(null); setEdit(f); }} />
      <EditEleve fiche={edit} onClose={() => setEdit(null)} onSaved={() => { setEdit(null); reload(); }} />
      <ConfirmDialog open={!!del} danger loading={busy} title="Supprimer l'inscription" confirmLabel="Supprimer" message={`Supprimer l'inscription de ${del?.nom} ${del?.prenoms} ? Le reçu sera conservé avec le statut « Annulé ».`} onCancel={() => setDel(null)} onConfirm={remove} />
    </>
  );
}
