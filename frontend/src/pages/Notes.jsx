import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ClipboardList, Lock, LockOpen, Save, TrendingDown, TrendingUp } from 'lucide-react';
import { api, parseErr } from '../api';
import { useAuth, useFetch, useYear } from '../context';
import { Badge, DataTable, EmptyState, PageHeader, Spinner, StatCard, useToast } from '../ui';
import { n2 } from '../validators';

const BAREME = [[5, 'Très insuffisant'], [8, 'Insuffisant'], [10, 'Médiocre'], [12, 'Passable'], [14, 'Assez bien'], [16, 'Bien'], [18, 'Très bien']];
export const appreciation = (n) => { if (n === null || n === undefined) return ''; for (const [s, l] of BAREME) if (n < s) return l; return 'Excellent'; };
const parse = (v) => { if (v === '' || v === null || v === undefined) return null; const s = String(v).replace(',', '.'); if (!/^\d+(\.\d{1,2})?$/.test(s)) return NaN; const x = Number(s); return x >= 0 && x <= 20 ? x : NaN; };
const calc = (a, b) => { const x = parse(a), y = parse(b); if (x === null || y === null || Number.isNaN(x) || Number.isNaN(y)) return null; return Math.round(((x + y) / 2) * 100 + 1e-9) / 100; };

export default function Notes() {
  const { user } = useAuth(); const admin = user.role === 'ADMIN'; const { annee } = useYear(); const toast = useToast();
  const [sp, setSp] = useSearchParams();
  const classe = sp.get('classe') || ''; const trimestre = sp.get('trimestre') || '1'; const matiere = sp.get('matiere') || '';
  const setP = (patch) => { const n = new URLSearchParams(sp); Object.entries(patch).forEach(([k, v]) => (v ? n.set(k, v) : n.delete(k))); setSp(n, { replace: true }); };
  const { data: classes } = useFetch('/classes/', { annee: annee?.id }, [], !!annee);
  const { data: matieres } = useFetch('/matieres/', { classe }, [], !!classe);
  const ready = !!(classe && matiere);
  const { data, loading, error, reload } = useFetch('/notes/', { classe, trimestre, matiere }, [], ready);
  const [rows, setRows] = useState([]); const [errs, setErrs] = useState({}); const [saving, setSaving] = useState(false); const [dirty, setDirty] = useState(false);
  useEffect(() => { if (data) { setRows(data.lignes.map((l) => ({ ...l, ds: l.ds ?? '', examen: l.examen ?? '' }))); setErrs({}); setDirty(false); } }, [data]);
  const upd = (id, k, v) => { setRows((rs) => rs.map((r) => (r.inscription_id === id ? { ...r, [k]: v } : r))); setErrs((e) => ({ ...e, [`${k}_${id}`]: undefined })); setDirty(true); };
  const save = async () => {
    const e = {}; rows.forEach((r) => ['ds', 'examen'].forEach((k) => { if (Number.isNaN(parse(r[k]))) e[`${k}_${r.inscription_id}`] = 'La note doit être comprise entre 0 et 20.'; }));
    if (Object.keys(e).length) { setErrs(e); toast.error('La note doit être comprise entre 0 et 20.'); return; }
    setSaving(true);
    try { await api.post('/notes/', { classe: Number(classe), trimestre: Number(trimestre), matiere: Number(matiere), notes: rows.map((r) => ({ inscription_id: r.inscription_id, ds: r.ds, examen: r.examen })) }); toast.success('Notes enregistrées. Moyennes et classements recalculés.'); reload(); }
    catch (er) { const p = parseErr(er); setErrs(p.champs); toast.error(p.message); } finally { setSaving(false); }
  };
  const toggleCloture = async () => { try { await api.post(`/trimestres/${data.trimestre_id}/cloture/`, { cloture: !data.cloture }); toast.success(data.cloture ? 'Trimestre rouvert.' : 'Trimestre clôturé.'); reload(); } catch (e) { toast.error(parseErr(e).message); } };
  const ro = !data?.editable;
  const inp = (r, k) => (<div><input className="input input-sm note-in" inputMode="decimal" disabled={ro} value={r[k]} onChange={(e) => upd(r.inscription_id, k, e.target.value)} aria-label={k} style={errs[`${k}_${r.inscription_id}`] ? { borderColor: 'var(--danger)' } : undefined} />{errs[`${k}_${r.inscription_id}`] && <div className="field-error" style={{ maxWidth: 120 }}>{errs[`${k}_${r.inscription_id}`]}</div>}</div>);
  const cols = [
    { key: 'matricule', label: 'Matricule', render: (r) => <Badge tone="blue">{r.matricule}</Badge> },
    { key: 'nom', label: 'Élève', render: (r) => <span><b>{r.nom}</b> {r.prenoms}</span>, text: (r) => `${r.nom} ${r.prenoms}` },
    { key: 'ds', label: 'DS /20', align: 'center', sortable: false, render: (r) => inp(r, 'ds') },
    { key: 'examen', label: 'Examen /20', align: 'center', sortable: false, render: (r) => inp(r, 'examen') },
    { key: 'note', label: 'Note trimestrielle', align: 'center', sortValue: (r) => calc(r.ds, r.examen) ?? -1, render: (r) => { const n = calc(r.ds, r.examen); return n === null ? <span className="muted">—</span> : <b style={{ color: n < 10 ? 'var(--danger)' : 'var(--ok)' }}>{n2(n)}</b>; } },
    { key: 'appreciation', label: 'Appréciation', sortable: false, render: (r) => { const a = appreciation(calc(r.ds, r.examen)); return a ? <Badge tone={calc(r.ds, r.examen) >= 10 ? 'green' : 'red'}>{a}</Badge> : ''; } },
  ];
  const vals = rows.map((r) => calc(r.ds, r.examen)).filter((x) => x !== null);
  const st = vals.length ? { moy: vals.reduce((a, b) => a + b, 0) / vals.length, max: Math.max(...vals), min: Math.min(...vals) } : null;
  const own = user.professeur?.id;
  return (
    <>
      <PageHeader title="Notes" subtitle={`Note trimestrielle = (DS + Examen) / 2 · ${annee?.libelle || ''}${!admin ? ' · votre matière uniquement' : ''}`} />
      <div className="card mb"><div className="row">
        <select className="input input-sm" value={classe} onChange={(e) => setP({ classe: e.target.value, matiere: '' })} aria-label="Classe"><option value="">Classe…</option>{classes?.map((c) => <option key={c.id} value={c.id}>{c.nom}</option>)}</select>
        <select className="input input-sm" value={trimestre} onChange={(e) => setP({ trimestre: e.target.value })} aria-label="Trimestre"><option value="1">1er trimestre</option><option value="2">2ème trimestre</option><option value="3">3ème trimestre</option></select>
        <select className="input input-sm" value={matiere} onChange={(e) => setP({ matiere: e.target.value })} aria-label="Matière"><option value="">Matière…</option>{matieres?.map((m) => <option key={m.id} value={m.id} disabled={!admin && m.professeur !== own}>{m.nom} (coef. {m.coefficient}){!admin && m.professeur !== own ? ' – non autorisée' : ''}</option>)}</select>
      </div></div>
      {!ready ? <EmptyState icon={ClipboardList} title="Choisissez une classe, un trimestre et une matière" text="La grille de saisie des notes s'affichera ici." />
        : loading ? <div className="card" style={{ display: 'grid', placeItems: 'center', padding: 50 }}><Spinner size={26} /></div> : error ? <div className="alert-bar">{error}</div> : data && (
          <>
            {data.cloture && <div className="info-bar"><Lock size={16} />Trimestre clôturé{admin ? ' : vos corrections seront journalisées.' : ' : contactez l\'administrateur.'}</div>}
            <div className="grid g4 mb">
              <StatCard icon={ClipboardList} label="Notes saisies" value={data.stats.nb_notes} suffix={` / ${data.stats.nb_attendues}`} tone="blue" />
              <StatCard icon={TrendingUp} label="Moyenne de la classe" value={st?.moy ?? null} decimals={2} suffix=" /20" tone="green" />
              <StatCard icon={TrendingUp} label="Note maximale" value={st?.max ?? null} decimals={2} tone="violet" />
              <StatCard icon={TrendingDown} label="Note minimale" value={st?.min ?? null} decimals={2} tone="orange" />
            </div>
            <DataTable columns={cols} rows={rows} rowKey="inscription_id" pageSizes={[25, 50, 100]} searchPlaceholder="Rechercher un élève…"
              toolbar={<>{admin && <button className="btn btn-ghost btn-sm" onClick={toggleCloture}>{data.cloture ? <LockOpen size={14} /> : <Lock size={14} />}{data.cloture ? 'Rouvrir le trimestre' : 'Clôturer le trimestre'}</button>}
                <button className="btn btn-primary btn-sm" disabled={saving || ro || !dirty} onClick={save}>{saving ? <Spinner size={13} /> : <Save size={14} />}Enregistrer les notes</button></>}
              empty={<EmptyState title="Aucun élève dans cette classe" />} />
          </>)}
    </>
  );
}
