import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Award, Eye, FileText, Printer, Save } from 'lucide-react';
import { api, openPdf, parseErr } from '../api';
import { useFetch, useYear } from '../context';
import { Badge, DataTable, EmptyState, Field, Modal, PageHeader, Spinner, useToast } from '../ui';
import { n2 } from '../validators';

function Bulletin({ ins, trimestre, onClose }) {
  const toast = useToast();
  const { data, loading } = useFetch(`/bulletins/${ins?.inscription_id}/`, { trimestre }, [ins?.inscription_id], !!ins);
  const [dec, setDec] = useState(''); const [saving, setSaving] = useState(false);
  useEffect(() => { if (data) setDec(data.decision || ''); }, [data]);
  const save = async () => { setSaving(true); try { await api.post('/bulletins/decision/', { inscription: ins.inscription_id, trimestre, texte: dec }); toast.success('Décision enregistrée.'); } catch (e) { toast.error(parseErr(e).message); } finally { setSaving(false); } };
  const pdf = async () => { try { await api.post('/bulletins/decision/', { inscription: ins.inscription_id, trimestre, texte: dec }); await openPdf(`/bulletins/${ins.inscription_id}/pdf/`, { trimestre }); } catch (e) { toast.error(e.message || parseErr(e).message); } };
  return (
    <Modal open={!!ins} onClose={onClose} size="lg" title={`Bulletin · ${ins?.nom || ''} ${ins?.prenoms || ''}`} footer={<><button className="btn btn-ghost" onClick={save} disabled={saving}>{saving ? <Spinner size={13} /> : <Save size={15} />}Enregistrer la décision</button><button className="btn btn-primary" onClick={pdf}><Printer size={15} />Bulletin PDF</button></>}>
      {loading || !data ? <div style={{ display: 'grid', placeItems: 'center', padding: 40 }}><Spinner size={26} /></div> : (
        <div className="stack">
          {data.provisoire && <div className="info-bar">Bulletin provisoire : {data.matieres_sans_note} matière(s) sans note complète.</div>}
          <div className="row"><Badge tone="blue">{data.matricule}</Badge><Badge tone="green">{data.classe}</Badge><Badge>{data.annee}</Badge><Badge tone="orange">Trimestre {data.trimestre}</Badge></div>
          <div className="table-wrap"><table className="table"><thead><tr><th>Matière</th><th>Coef.</th><th>DS</th><th>Examen</th><th>Moyenne</th><th>Points</th><th>Appréciation</th></tr></thead>
            <tbody>{data.lignes.map((l) => <tr key={l.matiere}><td><b>{l.matiere}</b></td><td>{l.coefficient}</td><td>{n2(l.ds)}</td><td>{n2(l.examen)}</td><td>{n2(l.note)}</td><td>{n2(l.points)}</td><td>{l.appreciation || '—'}</td></tr>)}
              <tr><td><b>TOTAL</b></td><td><b>{data.total_coefficients}</b></td><td /><td /><td /><td><b>{n2(data.total_points)}</b></td><td /></tr></tbody></table></div>
          <div className="grid g4"><div className="card"><div className="muted">Moyenne générale</div><b style={{ fontSize: 20 }}>{n2(data.moyenne)} / 20</b></div>
            <div className="card"><div className="muted">Rang</div><b style={{ fontSize: 20 }}>{data.rang ? `${data.rang}${data.rang === 1 ? 'er' : 'e'} / ${data.effectif_classe_classe}` : '—'}</b></div>
            <div className="card"><div className="muted">Absences justifiées</div><b style={{ fontSize: 20 }}>{data.absences_justifiees} h</b></div>
            <div className="card"><div className="muted">Absences injustifiées</div><b style={{ fontSize: 20 }}>{data.absences_injustifiees} h</b></div></div>
          <Field label="Décision du conseil des professeurs"><textarea className="input" rows={3} maxLength={255} value={dec} onChange={(e) => setDec(e.target.value)} placeholder="Ex. : Admis(e) en classe supérieure, encouragements…" /></Field>
        </div>)}
    </Modal>
  );
}

export default function Resultats() {
  const { annee } = useYear(); const toast = useToast();
  const [sp, setSp] = useSearchParams(); const classe = sp.get('classe') || ''; const trimestre = sp.get('trimestre') || '1';
  const setP = (patch) => { const n = new URLSearchParams(sp); Object.entries(patch).forEach(([k, v]) => (v ? n.set(k, v) : n.delete(k))); setSp(n, { replace: true }); };
  const { data: classes } = useFetch('/classes/', { annee: annee?.id }, [], !!annee);
  const { data, loading, error } = useFetch('/resultats/', { classe, trimestre }, [], !!classe);
  const [view, setView] = useState(null);
  const cols = [
    { key: 'rang', label: 'Rang', align: 'center', sortValue: (r) => r.rang ?? 999, render: (r) => (r.rang ? <Badge tone={r.rang <= 3 ? 'green' : 'gray'}>{r.rang}{r.rang === 1 ? 'er' : 'e'}</Badge> : '—') },
    { key: 'matricule', label: 'Matricule' }, { key: 'nom', label: 'Nom', render: (r) => <span><b>{r.nom}</b> {r.prenoms}</span>, text: (r) => `${r.nom} ${r.prenoms}` },
    ...(data?.matieres || []).map((m) => ({ key: `m${m.id}`, label: `${m.nom} (${m.coefficient})`, align: 'center', sortValue: (r) => r.notes[m.id] ?? -1, text: (r) => String(r.notes[m.id] ?? ''), render: (r) => n2(r.notes[m.id]) })),
    { key: 'total_points', label: 'Points', align: 'center', render: (r) => n2(r.total_points) },
    { key: 'moyenne', label: 'Moyenne', align: 'center', sortValue: (r) => r.moyenne ?? -1, render: (r) => (r.moyenne === null ? '—' : <b style={{ color: r.moyenne < 10 ? 'var(--danger)' : 'var(--ok)' }}>{n2(r.moyenne)}</b>) },
    { key: 'appreciation', label: 'Appréciation' },
    { key: 'actions', label: '', align: 'right', render: (r) => <button className="btn btn-ghost btn-sm" onClick={() => setView(r)}><Eye size={14} />Bulletin</button> },
  ];
  return (
    <>
      <PageHeader title="Résultats & bulletins" subtitle={`Classement avec ex æquo (1, 2, 2, 4) · ${annee?.libelle || ''}`} />
      <div className="card mb"><div className="row">
        <select className="input input-sm" value={classe} onChange={(e) => setP({ classe: e.target.value })} aria-label="Classe"><option value="">Classe…</option>{classes?.map((c) => <option key={c.id} value={c.id}>{c.nom}</option>)}</select>
        <select className="input input-sm" value={trimestre} onChange={(e) => setP({ trimestre: e.target.value })} aria-label="Trimestre"><option value="1">1er trimestre</option><option value="2">2ème trimestre</option><option value="3">3ème trimestre</option></select>
        {classe && <button className="btn btn-primary btn-sm" onClick={() => openPdf(`/bulletins/classe/${classe}/pdf/`, { trimestre }).catch((e) => toast.error(e.message))}><FileText size={14} />Bulletins de la classe (PDF)</button>}
      </div></div>
      {!classe ? <EmptyState icon={Award} title="Choisissez une classe" text="Les résultats et le classement s'affichent ici." /> : error ? <div className="alert-bar">{error}</div> :
        <DataTable columns={cols} rows={data?.lignes} loading={loading} rowKey="inscription_id" pageSizes={[25, 50, 100]} onRowDoubleClick={setView} searchPlaceholder="Rechercher un élève…" empty={<EmptyState icon={Award} title="Aucun élève" text="Cette classe n'a pas d'élèves inscrits." />} />}
      <Bulletin ins={view} trimestre={trimestre} onClose={() => setView(null)} />
    </>
  );
}
