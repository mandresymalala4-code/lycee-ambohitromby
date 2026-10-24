import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { Edit3, Plus, School, Trash2, Users } from 'lucide-react';
import { api, applyErrors, parseErr } from '../api';
import { useAuth, useFetch, useYear } from '../context';
import { ConfirmDialog, DataTable, EmptyState, Field, IconBtn, Modal, PageHeader, Spinner, useToast } from '../ui';
import { ariary } from '../validators';

function ClasseForm({ open, item, annee, onClose, onSaved }) {
  const toast = useToast();
  const { register, handleSubmit, reset, setError, formState: { errors, isSubmitting } } = useForm();
  const setK = () => {};
  useEffect(() => { if (open) reset(item ? { nom: item.nom, droit_inscription: item.droit_inscription, caisse_soutien: item.caisse_soutien } : { nom: '', droit_inscription: 0, caisse_soutien: 0 }); }, [open, item?.id]); // eslint-disable-line
  const submit = async (d) => {
    const body = { nom: d.nom.trim(), droit_inscription: d.droit_inscription === '' ? NaN : Number(d.droit_inscription), caisse_soutien: d.caisse_soutien === '' ? NaN : Number(d.caisse_soutien), annee: annee.id };
    try { item ? await api.put(`/classes/${item.id}/`, body) : await api.post('/classes/', body); toast.success(item ? 'Classe modifiée.' : 'Classe ajoutée.'); setK(0); onSaved(); }
    catch (e) { toast.error(parseErr(e).message); applyErrors(e, setError); }
  };
  const money = { required: 'Montant invalide.', validate: (v) => (Number.isInteger(Number(v)) && Number(v) >= 0 && Number(v) <= 10000000) || 'Montant invalide.' };
  return (
    <Modal open={open} onClose={() => { setK(0); onClose(); }} title={item ? 'Modifier la classe' : 'Ajouter une classe'} size="sm"
      footer={<><button className="btn btn-ghost" onClick={() => { setK(0); onClose(); }}>Annuler</button><button className="btn btn-primary" disabled={isSubmitting} onClick={handleSubmit(submit)}>{isSubmitting && <Spinner size={14} />}Enregistrer</button></>}>
      <form className="stack" onSubmit={handleSubmit(submit)} noValidate>
        <Field label="Nom de la classe" required error={errors.nom?.message}><input className="input" {...register('nom', { validate: (v) => (v.trim().length >= 2 && v.trim().length <= 50) || 'Le nom doit contenir entre 2 et 50 caractères.' })} /></Field>
        <Field label="Droit d'inscription (Ar)" required error={errors.droit_inscription?.message}><input type="number" min="0" className="input" {...register('droit_inscription', money)} /></Field>
        <Field label="Caisse de soutien (Ar)" required error={errors.caisse_soutien?.message}><input type="number" min="0" className="input" {...register('caisse_soutien', money)} /></Field>
      </form>
    </Modal>
  );
}

export default function Classes() {
  const { user } = useAuth(); const admin = user.role === 'ADMIN';
  const { annee } = useYear(); const toast = useToast(); const nav = useNavigate();
  const { data, loading, reload } = useFetch('/classes/', { annee: annee?.id }, [], !!annee);
  const [edit, setEdit] = useState(null); const [del, setDel] = useState(null); const [busy, setBusy] = useState(false);
  const cols = [
    { key: 'nom', label: 'Classe', render: (r) => <b>{r.nom}</b> },
    { key: 'effectif', label: 'Effectif', align: 'center', render: (r) => <span>{r.effectif} élève{r.effectif > 1 ? 's' : ''}</span>, sortValue: (r) => r.effectif },
    ...(admin ? [
      { key: 'droit_inscription', label: 'Droit d\'inscription', align: 'right', render: (r) => ariary(r.droit_inscription), sortValue: (r) => r.droit_inscription },
      { key: 'caisse_soutien', label: 'Caisse de soutien', align: 'right', render: (r) => ariary(r.caisse_soutien), sortValue: (r) => r.caisse_soutien },
      { key: 'total', label: 'Total', align: 'right', render: (r) => <b>{ariary(r.total)}</b>, sortValue: (r) => r.total }] : []),
    { key: 'actions', label: '', align: 'right', render: (r) => (
      <div className="row row-end"><IconBtn icon={Users} label="Voir les élèves" onClick={() => nav(`/eleves?classe=${r.id}`)} />
        {admin && <><IconBtn icon={Edit3} label="Modifier" onClick={() => setEdit(r)} /><IconBtn icon={Trash2} tone="danger" label="Supprimer" onClick={() => setDel(r)} /></>}</div>) },
  ];
  const remove = async () => {
    setBusy(true);
    try { await api.delete(`/classes/${del.id}/`); toast.success('Classe supprimée.'); setDel(null); reload(); } catch (e) { toast.error(parseErr(e).message); setDel(null); } finally { setBusy(false); }
  };
  return (
    <>
      <PageHeader title="Classes" subtitle={`Année scolaire ${annee?.libelle || ''}${admin ? '' : ' · consultation'}`} actions={admin && <button className="btn btn-primary" onClick={() => setEdit({})}><Plus size={16} />Ajouter une classe</button>} />
      <DataTable columns={cols} rows={data} loading={loading} onRowDoubleClick={(r) => nav(`/eleves?classe=${r.id}`)} searchPlaceholder="Rechercher une classe…"
        empty={<EmptyState icon={School} title="Aucune classe" text="Ajoutez la première classe de cette année." />} />
      <ClasseForm open={!!edit} item={edit?.id ? edit : null} annee={annee} onClose={() => setEdit(null)} onSaved={() => { setEdit(null); reload(); }} />
      <ConfirmDialog open={!!del} danger loading={busy} title="Supprimer la classe" confirmLabel="Supprimer" message={`Supprimer la classe « ${del?.nom} » ? Cette action est définitive.`} onCancel={() => setDel(null)} onConfirm={remove} />
    </>
  );
}
