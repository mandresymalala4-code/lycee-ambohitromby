import { useEffect, useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';
import { BookOpen, Copy, Edit3, Plus, Trash2 } from 'lucide-react';
import { api, applyErrors, parseErr } from '../api';
import { useAuth, useFetch, useYear } from '../context';
import { Badge, ConfirmDialog, DataTable, EmptyState, Field, IconBtn, Modal, PageHeader, Spinner, useToast } from '../ui';

function MatForm({ open, item, classe, onClose, onSaved }) {
  const toast = useToast(); const edit = !!item?.id;
  const { data: profs } = useFetch('/professeurs/', null, [], open);
  const { data: disc } = useFetch('/disciplines/', null, [], open);
  const { register, handleSubmit, reset, watch, setError, formState: { errors, isSubmitting } } = useForm();
  useEffect(() => { if (open) reset(edit ? { nom: item.nom, coefficient: item.coefficient, professeur: item.professeur || '' } : { nom: '', coefficient: 1, professeur: '' }); }, [open, item?.id]); // eslint-disable-line
  const nom = (watch('nom') || '').trim().toLowerCase();
  const candidats = useMemo(() => (profs || []).filter((p) => p.statut === 'VALIDE' && nom && p.matiere_nom.toLowerCase() === nom), [profs, nom]);
  const submit = async (d) => {
    const body = { classe: classe.id, nom: d.nom, coefficient: d.coefficient === '' ? NaN : Number(d.coefficient), professeur: d.professeur ? Number(d.professeur) : null };
    try { edit ? await api.put(`/matieres/${item.id}/`, body) : await api.post('/matieres/', body); toast.success(edit ? 'Matière modifiée.' : 'Matière ajoutée.'); onSaved(); }
    catch (e) { toast.error(parseErr(e).message); applyErrors(e, setError); }
  };
  return (
    <Modal open={open} onClose={onClose} size="sm" title={edit ? 'Modifier la matière' : `Ajouter une matière · ${classe?.nom}`}
      footer={<><button className="btn btn-ghost" onClick={onClose}>Annuler</button><button className="btn btn-primary" disabled={isSubmitting} onClick={handleSubmit(submit)}>{isSubmitting && <Spinner size={14} />}Enregistrer</button></>}>
      <form className="stack" noValidate onSubmit={handleSubmit(submit)}>
        <Field label="Matière" required error={errors.nom?.message}><input className="input" list="mdisc" {...register('nom', { validate: (v) => (v.trim().length >= 2 && v.trim().length <= 100) || 'La matière doit contenir entre 2 et 100 caractères.' })} /><datalist id="mdisc">{disc?.map((d) => <option key={d.id} value={d.nom} />)}</datalist></Field>
        <Field label="Coefficient (1 à 6)" required error={errors.coefficient?.message}><input type="number" min="1" max="6" step="1" className="input" {...register('coefficient', { validate: (v) => (Number.isInteger(Number(v)) && Number(v) >= 1 && Number(v) <= 6) || 'Le coefficient doit être compris entre 1 et 6.' })} /></Field>
        <Field label="Professeur" error={errors.professeur?.message} hint={nom && candidats.length === 0 ? 'Aucun professeur validé n\'enseigne cette matière.' : 'Seuls les professeurs de cette matière sont proposés.'}>
          <select className="input" {...register('professeur')}><option value="">Non affectée</option>{candidats.map((p) => <option key={p.id} value={p.id}>{p.nom} {p.prenoms}</option>)}</select></Field>
      </form>
    </Modal>
  );
}

export default function Matieres() {
  const { user } = useAuth(); const admin = user.role === 'ADMIN'; const { annee } = useYear(); const toast = useToast();
  const { data: classes } = useFetch('/classes/', { annee: annee?.id }, [], !!annee);
  const [cid, setCid] = useState('');
  useEffect(() => { if (classes?.length && !classes.find((c) => String(c.id) === String(cid))) setCid(classes[0].id); }, [classes]); // eslint-disable-line
  const classe = classes?.find((c) => String(c.id) === String(cid));
  const { data, loading, reload } = useFetch('/matieres/', { classe: cid }, [], !!cid);
  const [edit, setEdit] = useState(null); const [del, setDel] = useState(null); const [busy, setBusy] = useState(false);
  const cols = [
    { key: 'nom', label: 'Matière', render: (r) => <b>{r.nom}</b> },
    { key: 'coefficient', label: 'Coefficient', align: 'center', render: (r) => <Badge tone="blue">{r.coefficient}</Badge> },
    { key: 'professeur_nom', label: 'Professeur', render: (r) => (r.professeur_nom ? (<span>{r.professeur_nom} {r.professeur === user.professeur?.id && <Badge tone="green">Ma matière</Badge>}</span>) : <Badge tone="orange">Non affectée</Badge>), text: (r) => r.professeur_nom || 'Non affectée' },
    ...(admin ? [{ key: 'actions', label: '', align: 'right', render: (r) => <div className="row row-end"><IconBtn icon={Edit3} label="Modifier" onClick={() => setEdit(r)} /><IconBtn icon={Trash2} tone="danger" label="Supprimer" onClick={() => setDel(r)} /></div> }] : []),
  ];
  const copier = async () => { try { const { data: d } = await api.post('/matieres/copier-annee-precedente/', { classe: cid }); toast.success(`${d.copiees} matière(s) copiée(s).`); reload(); } catch (e) { toast.error(parseErr(e).message); } };
  const remove = async () => { setBusy(true); try { await api.delete(`/matieres/${del.id}/`); toast.success('Matière supprimée.'); setDel(null); reload(); } catch (e) { toast.error(parseErr(e).message); setDel(null); } finally { setBusy(false); } };
  return (
    <>
      <PageHeader title="Matières" subtitle={`Année scolaire ${annee?.libelle || ''}`}
        actions={<><select className="input" style={{ width: 190 }} value={cid} onChange={(e) => setCid(e.target.value)} aria-label="Classe">{classes?.map((c) => <option key={c.id} value={c.id}>{c.nom}</option>)}</select>
          {admin && <><button className="btn btn-ghost" onClick={copier}><Copy size={16} />Copier l'année précédente</button><button className="btn btn-primary" onClick={() => setEdit({})}><Plus size={16} />Ajouter</button></>}</>} />
      <DataTable columns={cols} rows={data} loading={loading} onRowDoubleClick={admin ? setEdit : undefined} searchPlaceholder="Rechercher une matière…"
        empty={<EmptyState icon={BookOpen} title="Aucune matière" text={`La classe ${classe?.nom || ''} n'a pas encore de matières.`} />} />
      <MatForm open={!!edit} item={edit} classe={classe} onClose={() => setEdit(null)} onSaved={() => { setEdit(null); reload(); }} />
      <ConfirmDialog open={!!del} danger loading={busy} confirmLabel="Supprimer" title="Supprimer la matière" message={`Supprimer la matière « ${del?.nom} » de la classe ${classe?.nom} ?`} onCancel={() => setDel(null)} onConfirm={remove} />
    </>
  );
}
