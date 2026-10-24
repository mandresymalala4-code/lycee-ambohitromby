import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useSearchParams } from 'react-router-dom';
import { Ban, Check, Edit3, Eye, Mail, Phone, PlayCircle, Plus, Printer, Trash2, UserCheck, Users, X } from 'lucide-react';
import { api, applyErrors, openPdf, parseErr, toForm } from '../api';
import { useAuth, useFetch } from '../context';
import { Avatar, Badge, ConfirmDialog, DataTable, EmptyState, Field, IconBtn, Modal, PageHeader, Spinner, Tabs, useToast } from '../ui';
import { fmtDate, fmtDateTime, rules } from '../validators';
import { ElevePhotoField } from './Eleves';

function ProfForm({ item, open, onClose, onSaved, disciplines }) {
  const toast = useToast(); const edit = !!item?.id;
  const { register, handleSubmit, reset, getValues, setError, formState: { errors, isSubmitting } } = useForm();
  const [file, setFile] = useState(null);
  useEffect(() => { if (open) { setFile(null); reset(edit ? { nom: item.nom, prenom: item.prenoms, date_naissance: item.date_naissance, sexe: item.sexe, adresse: item.adresse, telephone: item.telephone, email: item.email, cin: item.cin, matiere: item.matiere_nom, observation: item.observation } : { nom: '', prenom: '', date_naissance: '', sexe: '', adresse: '', telephone: '', email: '', cin: '', matiere: '', observation: '', mot_de_passe: '', confirmation: '' }); } }, [open, item?.id]); // eslint-disable-line
  const submit = async (d) => {
    const body = toForm({ ...d, photo: file });
    try { edit ? await api.put(`/professeurs/${item.id}/`, body, { headers: { 'Content-Type': 'multipart/form-data' } }) : await api.post('/professeurs/', body, { headers: { 'Content-Type': 'multipart/form-data' } }); toast.success(edit ? 'Professeur modifié.' : 'Professeur ajouté.'); onSaved(); }
    catch (e) { toast.error(parseErr(e).message); applyErrors(e, setError); }
  };
  const E = errors;
  return (
    <Modal open={open} onClose={onClose} size="lg" title={edit ? 'Modifier le professeur' : 'Ajouter un professeur'}
      footer={<><button className="btn btn-ghost" onClick={onClose}>Annuler</button><button className="btn btn-primary" disabled={isSubmitting} onClick={handleSubmit(submit)}>{isSubmitting && <Spinner size={14} />}Enregistrer</button></>}>
      <form className="form-grid" noValidate onSubmit={handleSubmit(submit)}>
        <Field label="Nom" required error={E.nom?.message} hint="En majuscules"><input className="input" {...register('nom', { validate: rules.nom })} /></Field>
        <Field label="Prénoms" required error={E.prenom?.message}><input className="input" {...register('prenom', { validate: rules.prenom })} /></Field>
        <Field label="Date de naissance" required error={E.date_naissance?.message}><input type="date" className="input" {...register('date_naissance', { validate: rules.naissanceAdulte(21) })} /></Field>
        <Field label="Sexe" required error={E.sexe?.message}><select className="input" {...register('sexe', { required: 'Veuillez sélectionner le sexe.' })}><option value="">Choisir…</option><option>Homme</option><option>Femme</option></select></Field>
        <Field label="Adresse" required error={E.adresse?.message} className="full"><input className="input" {...register('adresse', { validate: rules.adresse })} /></Field>
        <Field label="Téléphone" required error={E.telephone?.message}><input className="input" {...register('telephone', { validate: rules.tel })} /></Field>
        <Field label="Email" required error={E.email?.message}><input type="email" className="input" {...register('email', { validate: rules.email })} /></Field>
        <Field label="CIN (14 chiffres)" required error={E.cin?.message}><input className="input" inputMode="numeric" {...register('cin', { validate: rules.cin })} /></Field>
        <Field label="Matière enseignée" required error={E.matiere?.message}><input className="input" list="discs" {...register('matiere', { validate: rules.obligatoire })} /><datalist id="discs">{disciplines?.map((d) => <option key={d.id} value={d.nom} />)}</datalist></Field>
        {!edit && <><Field label="Mot de passe provisoire" required error={E.mot_de_passe?.message}><input type="text" className="input" {...register('mot_de_passe', { validate: rules.mdp })} /></Field>
          <Field label="Confirmation" required error={E.confirmation?.message}><input type="text" className="input" {...register('confirmation', { validate: (v) => v === getValues('mot_de_passe') || 'Les mots de passe ne correspondent pas.' })} /></Field></>}
        <Field label="Observation" error={E.observation?.message} className="full"><input className="input" maxLength={255} {...register('observation')} /></Field>
        <ElevePhotoField file={file} setFile={setFile} current={item?.photo} name={item?.nom || 'P'} />
      </form>
    </Modal>
  );
}

function ProfFiche({ p, onClose, admin }) {
  return (
    <Modal open={!!p} onClose={onClose} title="Fiche du professeur" footer={<button className="btn btn-primary" onClick={onClose}>Fermer</button>}>
      {p && <div className="stack"><div className="row"><Avatar src={p.photo} name={`${p.nom} ${p.prenoms}`} size={68} /><div><h2>{p.nom} {p.prenoms}</h2><div className="row">{p.code && <Badge tone="blue">{p.code}</Badge>}<Badge tone="green">{p.matiere_nom}</Badge>{p.statut === 'SUSPENDU' && <Badge tone="orange">Suspendu</Badge>}</div></div></div>
        <dl className="kv"><dt>Téléphone</dt><dd>{p.telephone}</dd><dt>Email</dt><dd>{p.email}</dd><dt>Sexe</dt><dd>{p.sexe}</dd>
          {admin && <><dt>Naissance</dt><dd>{fmtDate(p.date_naissance)}</dd><dt>Adresse</dt><dd>{p.adresse}</dd><dt>CIN</dt><dd>{p.cin}</dd><dt>Observation</dt><dd>{p.observation || '—'}</dd></>}</dl></div>}
    </Modal>
  );
}

export default function Professeurs() {
  const { user } = useAuth(); const admin = user.role === 'ADMIN'; const toast = useToast();
  const [sp, setSp] = useSearchParams(); const tab = sp.get('onglet') === 'attente' && admin ? 'attente' : 'liste';
  const [matiere, setMatiere] = useState(''); const [sexe, setSexe] = useState('');
  const { data, loading, reload } = useFetch('/professeurs/', { matiere: matiere || undefined, sexe: sexe || undefined });
  const att = useFetch('/professeurs/en-attente/', null, [], admin);
  const { data: disc } = useFetch('/disciplines/');
  const [edit, setEdit] = useState(null); const [fiche, setFiche] = useState(null); const [del, setDel] = useState(null); const [refus, setRefus] = useState(null); const [motif, setMotif] = useState(''); const [busy, setBusy] = useState(false);
  const refreshAll = () => { reload(); att.reload(); };
  const act = async (p, action, body, ok) => { try { await api.post(`/professeurs/${p.id}/${action}/`, body || {}); toast.success(ok); refreshAll(); } catch (e) { toast.error(parseErr(e).message); } };
  const cols = [
    { key: 'code', label: 'Code', render: (r) => <Badge tone="blue">{r.code}</Badge> },
    { key: 'nom', label: 'Nom', render: (r) => <div className="cell-person"><Avatar src={r.photo} name={`${r.nom} ${r.prenoms}`} size={30} /><b>{r.nom}</b></div> },
    { key: 'prenoms', label: 'Prénoms' },
    { key: 'matiere_nom', label: 'Matière', render: (r) => <Badge tone="green">{r.matiere_nom}</Badge> },
    { key: 'telephone', label: 'Téléphone', render: (r) => <span className="row" style={{ gap: 4 }}><Phone size={12} />{r.telephone}</span> },
    { key: 'email', label: 'Email', render: (r) => <span className="row" style={{ gap: 4 }}><Mail size={12} />{r.email}</span> },
    ...(admin ? [{ key: 'statut', label: 'Statut', render: (r) => r.statut === 'SUSPENDU' ? <Badge tone="orange">Suspendu</Badge> : <Badge tone="green">Actif</Badge> }] : []),
    { key: 'actions', label: '', align: 'right', render: (r) => (<div className="row row-end"><IconBtn icon={Eye} label="Voir la fiche" onClick={() => setFiche(r)} />
      {admin && <><IconBtn icon={Edit3} label="Modifier" onClick={() => setEdit(r)} />
        {r.statut === 'SUSPENDU' ? <IconBtn icon={PlayCircle} tone="ok" label="Réactiver" onClick={() => act(r, 'reactiver', null, 'Compte réactivé.')} /> : <IconBtn icon={Ban} tone="warn" label="Suspendre" onClick={() => act(r, 'suspendre', null, 'Compte suspendu.')} />}
        <IconBtn icon={Trash2} tone="danger" label="Supprimer" onClick={() => setDel(r)} /></>}</div>) },
  ];
  const colsAtt = [
    { key: 'nom', label: 'Nom', render: (r) => <div className="cell-person"><Avatar src={r.photo} name={r.nom} size={30} /><b>{r.nom} {r.prenoms}</b></div>, text: (r) => `${r.nom} ${r.prenoms}` },
    { key: 'matiere_nom', label: 'Matière' }, { key: 'email', label: 'Email' }, { key: 'telephone', label: 'Téléphone' },
    { key: 'date_creation', label: 'Demande', render: (r) => fmtDateTime(r.date_creation) },
    { key: 'statut', label: 'Statut', render: (r) => r.statut === 'REFUSE' ? <Badge tone="red">Refusé</Badge> : <Badge tone="orange">En attente</Badge> },
    { key: 'actions', label: '', align: 'right', render: (r) => (<div className="row row-end"><IconBtn icon={Eye} label="Voir" onClick={() => setFiche(r)} /><button className="btn btn-ok btn-sm" onClick={() => act(r, 'valider', null, 'Compte validé : le professeur est enregistré.')}><Check size={14} />Valider</button>
      {r.statut !== 'REFUSE' && <button className="btn btn-ghost btn-sm" onClick={() => { setMotif(''); setRefus(r); }}><X size={14} />Refuser</button>}</div>) },
  ];
  const remove = async () => { setBusy(true); try { await api.delete(`/professeurs/${del.id}/`); toast.success('Professeur supprimé.'); setDel(null); refreshAll(); } catch (e) { toast.error(parseErr(e).message); setDel(null); } finally { setBusy(false); } };
  const nAtt = att.data?.filter((x) => x.statut === 'EN_ATTENTE').length || 0;
  return (
    <>
      <PageHeader title="Professeurs" subtitle={admin ? 'Gestion du corps enseignant et validation des comptes' : 'Consultation'}
        actions={admin && <><button className="btn btn-ghost" onClick={() => openPdf('/professeurs/pdf/', { sexe: sexe || undefined, matiere: matiere || undefined }).catch((e) => toast.error(e.message))}><Printer size={16} />Imprimer</button><button className="btn btn-primary" onClick={() => setEdit({})}><Plus size={16} />Ajouter</button></>} />
      {admin && <Tabs value={tab} onChange={(v) => setSp(v === 'attente' ? { onglet: 'attente' } : {})} tabs={[{ value: 'liste', label: 'Professeurs', icon: <Users size={15} /> }, { value: 'attente', label: 'Comptes en attente', icon: <UserCheck size={15} />, count: nAtt }]} />}
      {tab === 'liste' ? (
        <DataTable columns={cols} rows={data} loading={loading} onRowDoubleClick={(r) => setFiche(r)} searchPlaceholder="Rechercher par nom, prénom ou code…"
          toolbar={<><select className="input input-sm" value={matiere} onChange={(e) => setMatiere(e.target.value)} aria-label="Matière"><option value="">Toutes les matières</option>{disc?.map((d) => <option key={d.id} value={d.id}>{d.nom}</option>)}</select>
            <select className="input input-sm" value={sexe} onChange={(e) => setSexe(e.target.value)} aria-label="Sexe"><option value="">Tous</option><option>Homme</option><option>Femme</option></select></>}
          empty={<EmptyState icon={Users} title="Aucun professeur" text="Aucun professeur ne correspond à ces critères." />} />
      ) : (
        <DataTable columns={colsAtt} rows={att.data} loading={att.loading} onRowDoubleClick={(r) => setFiche(r)} empty={<EmptyState icon={UserCheck} title="Aucune demande" text="Aucun compte professeur n'attend de validation." />} />)}
      <ProfForm open={!!edit} item={edit} disciplines={disc} onClose={() => setEdit(null)} onSaved={() => { setEdit(null); refreshAll(); }} />
      <ProfFiche p={fiche} admin={admin} onClose={() => setFiche(null)} />
      <ConfirmDialog open={!!del} danger loading={busy} confirmLabel="Supprimer" title="Supprimer le professeur" message={`Supprimer ${del?.nom} ${del?.prenoms} ? Ses matières deviendront « Non affectées » et ses cours seront retirés de l'emploi du temps.`} onCancel={() => setDel(null)} onConfirm={remove} />
      <ConfirmDialog open={!!refus} danger confirmLabel="Refuser" title="Refuser le compte" message={`Refuser la demande de ${refus?.nom} ${refus?.prenoms} ?`} onCancel={() => setRefus(null)} onConfirm={() => { act(refus, 'refuser', { motif }, 'Compte refusé.'); setRefus(null); }}>
        <Field label="Motif (facultatif)"><input className="input" maxLength={255} value={motif} onChange={(e) => setMotif(e.target.value)} /></Field></ConfirmDialog>
    </>
  );
}
