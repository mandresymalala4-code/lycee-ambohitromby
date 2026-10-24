import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AlertTriangle, CheckCheck, ClipboardCheck, Edit3, FileText, Lock, Printer, Save } from 'lucide-react';
import { api, openPdf, parseErr } from '../api';
import { useAuth, useFetch, useYear } from '../context';
import { Badge, DataTable, EmptyState, Field, PageHeader, Spinner, Tabs, useToast } from '../ui';
import { fmtDate, hh, JOURS, today } from '../validators';

const ST = [['PRESENT', 'Présent'], ['ABSENT', 'Absent'], ['RETARD', 'Retard'], ['JUSTIFIEE', 'Justifiée']];
const dernierJourOuvre = () => { const d = new Date(); while (d.getDay() === 0 || d.getDay() === 6) d.setDate(d.getDate() - 1); return d.toISOString().slice(0, 10); };

function ClasseMatiere({ sp, setP, classes, matieres, user }) {
  const own = user.professeur?.id;
  return (
    <>
      <select className="input input-sm" value={sp.get('classe') || ''} onChange={(e) => { setP({ classe: e.target.value, matiere: '', cours: '' }); }} aria-label="Classe"><option value="">Classe…</option>{classes?.map((c) => <option key={c.id} value={c.id}>{c.nom}</option>)}</select>
      <select className="input input-sm" value={sp.get('matiere') || ''} onChange={(e) => setP({ matiere: e.target.value, cours: '' })} aria-label="Matière"><option value="">Matière…</option>
        {matieres?.map((m) => <option key={m.id} value={m.id} disabled={user.role === 'PROFESSEUR' && m.professeur !== own}>{m.nom}{user.role === 'PROFESSEUR' && m.professeur !== own ? ' (non autorisée)' : ''}</option>)}</select>
    </>
  );
}

function Appel({ sp, setP, classes, matieres }) {
  const { user } = useAuth(); const toast = useToast();
  const classe = sp.get('classe'); const matiere = sp.get('matiere'); const date = sp.get('date') || dernierJourOuvre(); const cours = sp.get('cours');
  const ready = !!(classe && matiere);
  const seances = useFetch('/appels/seances/', { classe, matiere, date }, [], ready);
  useEffect(() => { if (seances.data?.length === 1 && !cours) setP({ cours: String(seances.data[0].id) }); }, [seances.data]); // eslint-disable-line
  const { data, loading, error, reload } = useFetch('/appels/', { classe, matiere, date, cours: cours || undefined }, [], ready);
  const [rows, setRows] = useState([]); const [editing, setEditing] = useState(false); const [duree, setDuree] = useState(''); const [errs, setErrs] = useState({}); const [saving, setSaving] = useState(false);
  useEffect(() => { if (data) { setRows(data.lignes.map((l) => ({ ...l }))); setEditing(!data.appel); setErrs({}); setDuree(data.duree || ''); } }, [data]);
  const dureeEff = Number(data?.duree || duree || 0);
  const upd = (id, patch) => setRows((rs) => rs.map((r) => (r.inscription_id === id ? { ...r, ...patch } : r)));
  const setStatut = (r, s) => upd(r.inscription_id, { statut: s, heures_absence: s === 'PRESENT' ? 0 : s === 'RETARD' ? 0.25 : dureeEff || '', motif: s === 'JUSTIFIEE' ? r.motif : '' });
  const save = async () => {
    setSaving(true); setErrs({});
    const body = { classe: Number(classe), matiere: Number(matiere), date, jour: new Date(`${date}T12:00`).getDay(), cours: cours ? Number(cours) : null, duree_heures: duree || undefined,
      lignes: rows.map((r) => ({ inscription_id: r.inscription_id, statut: r.statut, heures_absence: r.statut === 'PRESENT' ? 0 : r.heures_absence, motif: r.motif, observation: r.observation })) };
    try {
      data.appel ? await api.put(`/appels/${data.appel.id}/`, body) : await api.post('/appels/', body);
      toast.success('Appel enregistré.'); reload();
    } catch (e) { const p = parseErr(e); setErrs(p.champs); toast.error(p.message); } finally { setSaving(false); }
  };
  const readOnly = !editing || !data?.editable;
  const cols = [
    { key: 'matricule', label: 'Matricule', render: (r) => <Badge tone="blue">{r.matricule}</Badge> },
    { key: 'nom', label: 'Élève', render: (r) => <div><b>{r.nom}</b> {r.prenoms}{r.alerte && <Badge tone="red"><AlertTriangle size={11} />&gt; 15 h</Badge>}</div>, text: (r) => `${r.nom} ${r.prenoms}` },
    { key: 'statut', label: 'Statut', sortable: false, render: (r) => <div className="seg">{ST.map(([v, l]) => <button key={v} disabled={readOnly} className={`${r.statut === v ? 'on' : ''} s-${v}`} onClick={() => setStatut(r, v)}>{l}</button>)}</div> },
    { key: 'heures_absence', label: 'Heures', sortable: false, render: (r) => (
      <div><input type="number" step="0.25" min="0" max={dureeEff || undefined} className="input input-sm note-in" disabled={readOnly || r.statut === 'PRESENT'} value={r.statut === 'PRESENT' ? 0 : r.heures_absence} onChange={(e) => upd(r.inscription_id, { heures_absence: e.target.value })} />
        {errs[`heures_${r.inscription_id}`] && <div className="field-error">{errs[`heures_${r.inscription_id}`]}</div>}</div>) },
    { key: 'motif', label: 'Motif', sortable: false, render: (r) => (<div><input className="input input-sm" style={{ width: 150 }} maxLength={255} disabled={readOnly || r.statut !== 'JUSTIFIEE'} placeholder={r.statut === 'JUSTIFIEE' ? 'Obligatoire' : ''} value={r.motif} onChange={(e) => upd(r.inscription_id, { motif: e.target.value })} />{errs[`motif_${r.inscription_id}`] && <div className="field-error">{errs[`motif_${r.inscription_id}`]}</div>}</div>) },
    { key: 'observation', label: 'Observation', sortable: false, render: (r) => <input className="input input-sm" style={{ width: 150 }} maxLength={255} disabled={readOnly} value={r.observation} onChange={(e) => upd(r.inscription_id, { observation: e.target.value })} /> },
    { key: 'total_mensuel', label: 'Mois', align: 'center', render: (r) => hh(r.total_mensuel) },
    { key: 'total_trimestriel', label: 'Trimestre', align: 'center', render: (r) => hh(r.total_trimestriel) },
  ];
  const nbAbs = rows.filter((r) => r.statut !== 'PRESENT').length;
  const sc = seances.data || [];
  return (
    <>
      <div className="card mb"><div className="row">
        <ClasseMatiere sp={sp} setP={setP} classes={classes} matieres={matieres} user={user} />
        <input type="date" className="input input-sm" value={date} max={today()} onChange={(e) => setP({ date: e.target.value, cours: '' })} aria-label="Date" />
        {ready && <span className="muted">{JOURS[new Date(`${date}T12:00`).getDay()] || 'Week-end'}</span>}
        {ready && sc.length > 0 && <select className="input input-sm" value={cours || ''} onChange={(e) => setP({ cours: e.target.value })} aria-label="Séance"><option value="">Séance…</option>{sc.map((c) => <option key={c.id} value={c.id}>{c.heure_debut} – {c.heure_fin}</option>)}</select>}
        {ready && user.role === 'ADMIN' && !cours && <input type="number" step="0.25" min="0.25" max="11" className="input input-sm" style={{ width: 130 }} placeholder="Durée (h)" value={duree} onChange={(e) => setDuree(e.target.value)} />}
      </div></div>
      {!ready ? <EmptyState icon={ClipboardCheck} title="Choisissez une classe et une matière" text={user.role === 'PROFESSEUR' ? 'Seule votre matière est disponible pour l\'appel.' : 'Sélectionnez la classe, la matière et la date pour faire l\'appel.'} />
        : loading || seances.loading ? <div className="card" style={{ display: 'grid', placeItems: 'center', padding: 50 }}><Spinner size={26} /></div>
        : error ? <div className="alert-bar"><AlertTriangle size={16} />{error}</div>
        : data && (<>
          {data.cloture && <div className="info-bar"><Lock size={16} />Trimestre clôturé{user.role === 'ADMIN' ? ' (modification réservée à l\'administrateur).' : ' : contactez l\'administrateur.'}</div>}
          {data.appel && <div className="info-bar"><ClipboardCheck size={16} />Appel déjà enregistré par {data.appel.saisi_par || '—'} · séance de {data.appel.duree_heures} h</div>}
          <DataTable columns={cols} rows={rows} rowKey="inscription_id" rowClass={(r) => (r.alerte ? 'row-alert' : '')} pageSizes={[25, 50, 100]} searchPlaceholder="Rechercher un élève…"
            toolbar={<>{!readOnly && <button className="btn btn-ghost btn-sm" onClick={() => setRows((rs) => rs.map((r) => ({ ...r, statut: 'PRESENT', heures_absence: 0, motif: '' })))}><CheckCheck size={14} />Tous présents</button>}
              <button className="btn btn-ghost btn-sm" disabled={!data.appel} onClick={() => openPdf('/appels/pdf/', { classe, matiere, date, cours: cours || undefined }).catch((e) => toast.error(e.message))}><Printer size={14} />Feuille d'appel</button>
              {data.appel && data.editable && !editing && <button className="btn btn-warn btn-sm" onClick={() => setEditing(true)}><Edit3 size={14} />Modifier</button>}
              {data.editable && editing && <button className="btn btn-ok btn-sm" onClick={save} disabled={saving}>{saving ? <Spinner size={13} /> : <Save size={14} />}Enregistrer l'appel</button>}</>}
            empty={<EmptyState title="Aucun élève dans cette classe" />} />
          <p className="muted mt">{rows.length} élève(s) · {nbAbs} absent(s) ou en retard</p></>)}
    </>
  );
}

function Recap({ sp, setP, classes, matieres }) {
  const { user } = useAuth(); const toast = useToast();
  const classe = sp.get('classe'); const periode = sp.get('periode') || 'trimestre'; const mois = sp.get('mois') || today().slice(0, 7); const trimestre = sp.get('trimestre') || '1';
  const prof = user.role === 'PROFESSEUR';
  const mat = prof ? matieres?.find((m) => m.professeur === user.professeur?.id)?.id : sp.get('matiere');
  const params = { classe, periode, mois: periode === 'mois' ? mois : undefined, trimestre: periode === 'trimestre' ? trimestre : undefined, matiere: mat || undefined };
  const { data, loading, error } = useFetch('/absences/recapitulatif/', params, [], !!classe);
  const cols = [
    { key: 'matricule', label: 'Matricule' }, { key: 'nom', label: 'Nom', render: (r) => <b>{r.nom}</b> }, { key: 'prenoms', label: 'Prénoms' },
    { key: 'justifiees', label: 'Justifiées', align: 'center', render: (r) => hh(r.justifiees) }, { key: 'injustifiees', label: 'Injustifiées', align: 'center', render: (r) => hh(r.injustifiees) },
    { key: 'retards', label: 'Retards', align: 'center', render: (r) => r.retards || 0 }, { key: 'total', label: 'Total', align: 'center', render: (r) => <b>{hh(r.total)}</b> },
    { key: 'alerte', label: 'Alerte', align: 'center', sortValue: (r) => (r.alerte ? 1 : 0), render: (r) => (r.alerte ? <Badge tone="red"><AlertTriangle size={11} />&gt; 15 h</Badge> : '') },
  ];
  return (
    <>
      <div className="card mb"><div className="row">
        <select className="input input-sm" value={classe || ''} onChange={(e) => setP({ classe: e.target.value, matiere: '' })} aria-label="Classe"><option value="">Classe…</option>{classes?.map((c) => <option key={c.id} value={c.id}>{c.nom}</option>)}</select>
        {!prof && <select className="input input-sm" value={sp.get('matiere') || ''} onChange={(e) => setP({ matiere: e.target.value })} aria-label="Matière"><option value="">Toutes les matières</option>{matieres?.map((m) => <option key={m.id} value={m.id}>{m.nom}</option>)}</select>}
        <div className="seg"><button className={periode === 'mois' ? 'on' : ''} onClick={() => setP({ periode: 'mois' })}>Mensuel</button><button className={periode === 'trimestre' ? 'on' : ''} onClick={() => setP({ periode: 'trimestre' })}>Trimestriel</button></div>
        {periode === 'mois' ? <input type="month" className="input input-sm" value={mois} onChange={(e) => setP({ mois: e.target.value })} /> : <select className="input input-sm" value={trimestre} onChange={(e) => setP({ trimestre: e.target.value })}><option value="1">1er trimestre</option><option value="2">2ème trimestre</option><option value="3">3ème trimestre</option></select>}
      </div></div>
      {!classe ? <EmptyState icon={FileText} title="Choisissez une classe" text="Le récapitulatif des absences s'affiche ici." /> : error ? <div className="alert-bar">{error}</div> :
        <DataTable columns={cols} rows={data?.lignes} loading={loading} rowKey="inscription_id" rowClass={(r) => (r.alerte ? 'row-alert' : '')} pageSizes={[25, 50, 100]}
          toolbar={<button className="btn btn-ghost btn-sm" onClick={() => openPdf('/absences/rapport/pdf/', params).catch((e) => toast.error(e.message))}><Printer size={14} />Rapport PDF</button>} />}
    </>
  );
}

function Alertes({ annee }) {
  const { data, loading } = useFetch('/absences/alertes/', { annee: annee?.id }, [], !!annee);
  const cols = [{ key: 'matricule', label: 'Matricule' }, { key: 'nom', label: 'Nom', render: (r) => <b>{r.nom}</b> }, { key: 'prenoms', label: 'Prénoms' }, { key: 'classe', label: 'Classe' },
    { key: 'trimestre', label: 'Trimestre', align: 'center', render: (r) => `T${r.trimestre}` }, { key: 'heures', label: 'Heures injustifiées', align: 'center', render: (r) => <Badge tone="red">{hh(r.heures)}</Badge> }];
  return <DataTable columns={cols} rows={data} loading={loading} rowKey="inscription_id" empty={<EmptyState icon={AlertTriangle} title="Aucune alerte" text="Aucun élève ne dépasse 15 heures d'absences injustifiées." />} />;
}

export default function Absences() {
  const { user } = useAuth(); const { annee } = useYear();
  const [sp, setSp] = useSearchParams();
  const tab = sp.get('tab') || 'appel';
  const setP = (patch) => { const n = new URLSearchParams(sp); Object.entries(patch).forEach(([k, v]) => (v ? n.set(k, v) : n.delete(k))); setSp(n, { replace: true }); };
  const { data: classes } = useFetch('/classes/', { annee: annee?.id }, [], !!annee);
  const { data: matieres } = useFetch('/matieres/', { classe: sp.get('classe') }, [], !!sp.get('classe'));
  return (
    <>
      <PageHeader title="Absences" subtitle={`Appel, récapitulatifs et alertes · ${annee?.libelle || ''}${user.role === 'PROFESSEUR' ? ' · votre matière uniquement' : ''}`} />
      <Tabs value={tab} onChange={(v) => setP({ tab: v })} tabs={[{ value: 'appel', label: 'Faire l\'appel', icon: <ClipboardCheck size={15} /> }, { value: 'recap', label: 'Récapitulatif & rapports', icon: <FileText size={15} /> }, { value: 'alertes', label: 'Alertes', icon: <AlertTriangle size={15} /> }]} />
      {tab === 'appel' && <Appel sp={sp} setP={setP} classes={classes} matieres={matieres} />}
      {tab === 'recap' && <Recap sp={sp} setP={setP} classes={classes} matieres={matieres} />}
      {tab === 'alertes' && <Alertes annee={annee} />}
    </>
  );
}
