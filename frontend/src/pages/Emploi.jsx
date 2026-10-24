import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { CalendarDays, Plus, Printer, Trash2 } from 'lucide-react';
import { api, applyErrors, openPdf, parseErr } from '../api';
import { useAuth, useFetch, useYear } from '../context';
import { ConfirmDialog, EmptyState, Field, Modal, PageHeader, Spinner, Tabs, useToast } from '../ui';
import { JOURS } from '../validators';

const H0 = 7, H1 = 18, PX = 56;
const COLORS = ['#3B82F6', '#16A34A', '#F59E0B', '#EC4899', '#8B5CF6', '#06B6D4', '#EF4444', '#84CC16', '#F97316', '#64748B'];
const mins = (t) => Number(t.slice(0, 2)) * 60 + Number(t.slice(3, 5));
const HEURES = Array.from({ length: (H1 - H0) * 2 + 1 }, (_, i) => { const m = H0 * 60 + i * 30; return `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`; });

function Grille({ cours, onCell, onCours, mode }) {
  return (
    <div className="card" style={{ padding: 0, overflowX: 'auto' }}>
      <div className="edt">
        <div className="edt-h" />{JOURS.slice(1).map((j) => <div key={j} className="edt-h">{j}</div>)}
        <div className="edt-hours" style={{ height: (H1 - H0) * PX }}>{Array.from({ length: H1 - H0 + 1 }, (_, i) => <span key={i} style={{ top: i * PX }}>{String(H0 + i).padStart(2, '0')}:00</span>)}</div>
        {[1, 2, 3, 4, 5].map((j) => (
          <div key={j} className="edt-col" style={{ height: (H1 - H0) * PX }} onClick={(e) => { if (!onCell || e.target !== e.currentTarget) return; const y = e.nativeEvent.offsetY; const m = H0 * 60 + Math.floor(y / (PX / 2)) * 30; const f = (x) => `${String(Math.floor(x / 60)).padStart(2, '0')}:${String(x % 60).padStart(2, '0')}`; onCell(j, f(m), f(Math.min(m + 120, H1 * 60))); }}>
            {cours.filter((c) => c.jour === j).map((c) => {
              const col = COLORS[c.discipline % COLORS.length]; const top = ((mins(c.heure_debut) - H0 * 60) / 60) * PX; const h = ((mins(c.heure_fin) - mins(c.heure_debut)) / 60) * PX;
              return (<div key={c.id} className="edt-c" style={{ top, height: h - 2, background: `${col}22`, borderColor: col }} onClick={(e) => { e.stopPropagation(); onCours?.(c); }} title={`${c.matiere_nom} · ${c.heure_debut}-${c.heure_fin}`}>
                <b>{c.matiere_nom}</b><div>{mode === 'prof' ? c.classe_nom : c.professeur_nom}</div><div className="muted">{c.heure_debut} – {c.heure_fin}{c.salle ? ` · ${c.salle}` : ''}</div></div>);
            })}
          </div>))}
      </div>
    </div>
  );
}

function CoursForm({ open, item, matieres, onClose, onSaved, onDelete }) {
  const toast = useToast(); const edit = !!item?.id;
  const { register, handleSubmit, reset, setError, formState: { errors, isSubmitting } } = useForm();
  useEffect(() => { if (open) reset({ matiere: item?.matiere || '', jour: item?.jour || 1, heure_debut: item?.heure_debut || '08:00', heure_fin: item?.heure_fin || '10:00', salle: item?.salle || '' }); }, [open, item]); // eslint-disable-line
  const submit = async (d) => {
    const body = { ...d, matiere: Number(d.matiere), jour: Number(d.jour) };
    try { edit ? await api.put(`/emplois-du-temps/${item.id}/`, body) : await api.post('/emplois-du-temps/', body); toast.success(edit ? 'Cours modifié.' : 'Cours ajouté.'); onSaved(); }
    catch (e) { toast.error(parseErr(e).message); applyErrors(e, setError); }
  };
  const E = errors;
  return (
    <Modal open={open} onClose={onClose} size="sm" title={edit ? 'Modifier le cours' : 'Ajouter un cours'} footer={<>{edit && <button className="btn btn-danger" style={{ marginRight: 'auto' }} onClick={onDelete}><Trash2 size={15} />Supprimer</button>}<button className="btn btn-ghost" onClick={onClose}>Annuler</button><button className="btn btn-primary" disabled={isSubmitting} onClick={handleSubmit(submit)}>{isSubmitting && <Spinner size={14} />}Enregistrer</button></>}>
      <form className="form-grid" noValidate onSubmit={handleSubmit(submit)}>
        <Field label="Matière" required error={E.matiere?.message} className="full"><select className="input" {...register('matiere', { required: 'Veuillez choisir une matière.' })}><option value="">Choisir…</option>{matieres?.map((m) => <option key={m.id} value={m.id} disabled={!m.professeur}>{m.nom} {m.professeur_nom ? `· ${m.professeur_nom}` : '(non affectée)'}</option>)}</select></Field>
        <Field label="Jour" required error={E.jour?.message}><select className="input" {...register('jour')}>{[1, 2, 3, 4, 5].map((j) => <option key={j} value={j}>{JOURS[j]}</option>)}</select></Field>
        <Field label="Salle" error={E.salle?.message}><input className="input" maxLength={30} {...register('salle')} /></Field>
        <Field label="Début" required error={E.heure_debut?.message}><select className="input" {...register('heure_debut')}>{HEURES.slice(0, -1).map((h) => <option key={h}>{h}</option>)}</select></Field>
        <Field label="Fin" required error={E.heure_fin?.message}><select className="input" {...register('heure_fin')}>{HEURES.slice(1).map((h) => <option key={h}>{h}</option>)}</select></Field>
      </form>
    </Modal>
  );
}

export default function Emploi() {
  const { user } = useAuth(); const admin = user.role === 'ADMIN'; const { annee } = useYear(); const toast = useToast();
  const [tab, setTab] = useState(admin ? 'classe' : 'perso');
  const { data: classes } = useFetch('/classes/', { annee: annee?.id }, [], !!annee);
  const [cid, setCid] = useState('');
  useEffect(() => { if (classes?.length && !classes.find((c) => String(c.id) === String(cid))) setCid(classes[0].id); }, [classes]); // eslint-disable-line
  const perso = tab === 'perso';
  const { data, loading, reload } = useFetch(perso ? '/mon-emploi-du-temps/' : '/emplois-du-temps/', perso ? { annee: annee?.id } : { classe: cid }, [], perso ? !!annee : !!cid);
  const { data: matieres } = useFetch('/matieres/', { classe: cid }, [], admin && !!cid);
  const [edit, setEdit] = useState(null); const [del, setDel] = useState(null);
  const classe = classes?.find((c) => String(c.id) === String(cid));
  const pdf = () => (perso ? openPdf('/mon-emploi-du-temps/pdf/', { annee: annee.id }) : openPdf('/emplois-du-temps/pdf/', { classe: cid })).catch((e) => toast.error(e.message));
  const remove = async () => { try { await api.delete(`/emplois-du-temps/${del.id}/`); toast.success('Cours supprimé.'); setDel(null); setEdit(null); reload(); } catch (e) { toast.error(parseErr(e).message); setDel(null); } };
  return (
    <>
      <PageHeader title="Emploi du temps" subtitle={perso ? 'Votre emploi du temps personnel (généré automatiquement)' : `Classe ${classe?.nom || ''} · ${annee?.libelle || ''}`}
        actions={<><button className="btn btn-ghost" onClick={pdf}><Printer size={16} />Imprimer (PDF)</button>{admin && !perso && <button className="btn btn-primary" onClick={() => setEdit({})}><Plus size={16} />Ajouter un cours</button>}</>} />
      {!admin && <Tabs value={tab} onChange={setTab} tabs={[{ value: 'perso', label: 'Mon emploi du temps' }, { value: 'classe', label: 'Par classe' }]} />}
      {!perso && <div className="row mb"><select className="input" style={{ width: 220 }} value={cid} onChange={(e) => setCid(e.target.value)} aria-label="Classe">{classes?.map((c) => <option key={c.id} value={c.id}>{c.nom}</option>)}</select>{admin && <span className="muted">Cliquez sur une plage vide pour ajouter un cours, sur un cours pour le modifier.</span>}</div>}
      {loading ? <div className="card" style={{ display: 'grid', placeItems: 'center', padding: 60 }}><Spinner size={26} /></div> : (data?.length === 0 && !admin ? <EmptyState icon={CalendarDays} title="Aucun cours" text="Aucun cours n'est planifié." /> :
        <Grille cours={data || []} mode={perso ? 'prof' : 'classe'} onCell={admin && !perso ? (jour, d, f) => setEdit({ jour, heure_debut: d, heure_fin: f }) : undefined} onCours={admin && !perso ? setEdit : undefined} />)}
      {admin && !perso && data?.length === 0 && !loading && <p className="muted mt">Aucun cours planifié pour cette classe. Ajoutez le premier cours.</p>}
      <CoursForm open={!!edit} item={edit} matieres={matieres} onClose={() => setEdit(null)} onSaved={() => { setEdit(null); reload(); }} onDelete={() => setDel(edit)} />
      <ConfirmDialog open={!!del} danger confirmLabel="Supprimer" title="Supprimer le cours" message="Supprimer ce cours de l'emploi du temps ?" onCancel={() => setDel(null)} onConfirm={remove} />
    </>
  );
}
