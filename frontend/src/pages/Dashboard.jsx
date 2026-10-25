import { Link, useNavigate } from 'react-router-dom';
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { AlertTriangle, BookOpen, CalendarCheck, CheckCircle2, ClipboardList, Clock, GraduationCap, Percent, School, TimerReset, TrendingUp, UserCheck, Users, Wallet } from 'lucide-react';
import { useAuth, useFetch, useYear } from '../context';
import { Badge, EmptyState, PageHeader, StatCard } from '../ui';
import { ariary, fmtDate, hh } from '../validators';

const COL = ['#3B82F6', '#EC4899', '#16A34A', '#F59E0B', '#8B5CF6', '#06B6D4'];
const tip = { contentStyle: { background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 10, fontSize: 12, color: 'var(--text)' }, labelStyle: { color: 'var(--text)' }, itemStyle: { color: 'var(--text)' } };
const mois = (m) => { const [y, mm] = m.split('-'); return ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc'][Number(mm) - 1] + ' ' + y.slice(2); };

function Charts({ d, prof }) {
  const abs = (d.graph_absences || []).map((x) => ({ ...x, m: mois(x.mois) }));
  return (
    <div className="grid g2 mt stagger">
      {!prof && <div className="card chart-card"><h3>Effectifs par classe</h3><div className="chart-box">{d.graph_effectifs.some((x) => x.effectif) ? <ResponsiveContainer><BarChart data={d.graph_effectifs}><CartesianGrid strokeDasharray="3 3" stroke="var(--border)" /><XAxis dataKey="classe" fontSize={11} interval={0} /><YAxis allowDecimals={false} fontSize={11} /><Tooltip {...tip} /><Bar dataKey="effectif" name="Élèves" fill="#3B82F6" radius={[6, 6, 0, 0]} animationDuration={900} /></BarChart></ResponsiveContainer> : <EmptyState title="Aucun élève inscrit" />}</div></div>}
      {!prof && <div className="card chart-card"><h3>Répartition garçons / filles</h3><div className="chart-box">{d.graph_sexe.some((x) => x.value) ? <ResponsiveContainer><PieChart><Pie data={d.graph_sexe} dataKey="value" nameKey="name" innerRadius={55} outerRadius={85} paddingAngle={3} animationDuration={900}>{d.graph_sexe.map((_, i) => <Cell key={i} fill={COL[i]} />)}</Pie><Tooltip {...tip} /><Legend /></PieChart></ResponsiveContainer> : <EmptyState title="Aucune donnée" />}</div></div>}
      <div className="card chart-card"><h3>Moyennes par classe{d.trimestre_moyennes ? ` · T${d.trimestre_moyennes}` : ''}</h3><div className="chart-box">{d.graph_moyennes.length ? <ResponsiveContainer><BarChart data={d.graph_moyennes}><CartesianGrid strokeDasharray="3 3" stroke="var(--border)" /><XAxis dataKey="classe" fontSize={11} interval={0} /><YAxis domain={[0, 20]} fontSize={11} /><Tooltip {...tip} /><Bar dataKey="moyenne" name="Moyenne /20" fill="#16A34A" radius={[6, 6, 0, 0]} animationDuration={900} /></BarChart></ResponsiveContainer> : <EmptyState title="Pas encore de notes" text="Les moyennes apparaîtront après la saisie des notes." />}</div></div>
      <div className="card chart-card"><h3>Heures d'absence par mois</h3><div className="chart-box">{abs.length ? <ResponsiveContainer><AreaChart data={abs}><CartesianGrid strokeDasharray="3 3" stroke="var(--border)" /><XAxis dataKey="m" fontSize={11} /><YAxis fontSize={11} /><Tooltip {...tip} /><Legend /><Area type="monotone" dataKey="injustifiees" name="Injustifiées" stroke="#DC2626" fill="#DC262633" animationDuration={900} /><Area type="monotone" dataKey="justifiees" name="Justifiées" stroke="#3B82F6" fill="#3B82F633" animationDuration={900} /></AreaChart></ResponsiveContainer> : <EmptyState title="Aucune absence enregistrée" />}</div></div>
    </div>
  );
}

function Alertes({ list }) {
  return (
    <div className="card"><h3 className="row"><AlertTriangle size={16} color="#DC2626" />Alertes d'absences (&gt; 15 h injustifiées)</h3>
      {list.length === 0 ? <p className="muted">Aucun élève n'a dépassé 15 heures d'absences injustifiées.</p> : list.map((a, i) => (
        <div className="list-item" key={i}><div><b>{a.nom} {a.prenoms}</b><div className="muted">{a.classe} · {a.matricule}</div></div><Badge tone="red">{a.heures} h · T{a.trimestre}</Badge></div>))}
    </div>
  );
}

function Admin({ annee }) {
  const { data: d, loading } = useFetch('/statistiques/admin/', { annee: annee.id }, []);
  const nav = useNavigate();
  const s = d || {};
  return (
    <>
      <div className="grid g4 stagger">
        <StatCard loading={loading} icon={GraduationCap} label="Élèves inscrits" value={s.total_eleves} tone="blue" delay={0} />
        <StatCard loading={loading} icon={Users} label="Professeurs" value={s.total_professeurs} tone="violet" delay={.04} />
        <StatCard loading={loading} icon={School} label="Classes" value={s.total_classes} tone="green" delay={.08} />
        <StatCard loading={loading} icon={Percent} label="Taux de présence" value={s.taux_presence} decimals={1} suffix=" %" tone="green" delay={.12} />
        <StatCard loading={loading} icon={Clock} label="Heures d'absence" value={s.total_absences_heures} decimals={1} suffix=" h" tone="orange" delay={.16} />
        <StatCard loading={loading} icon={TrendingUp} label="Moyenne générale" value={s.moyenne_generale} decimals={2} suffix=" /20" tone="blue" delay={.2} />
        <StatCard loading={loading} icon={Wallet} label="Droits encaissés (Ar)" value={s.total_droits} tone="violet" delay={.24} />
        <StatCard loading={loading} icon={AlertTriangle} label="Alertes absences" value={s.alertes?.length} tone="red" delay={.28} />
      </div>
      {d && <>
        <Charts d={d} />
        <div className="grid g3 mt stagger">
          <div className="card"><h3>Comptes professeurs en attente {d.en_attente_total > 0 && <Badge tone="orange">{d.en_attente_total}</Badge>}</h3>
            {d.en_attente.length === 0 ? <p className="muted">Aucune demande en attente.</p> : d.en_attente.map((p) => <div key={p.id} className="list-item"><div><b>{p.nom}</b><div className="muted">{p.matiere}</div></div><button className="btn btn-sm btn-primary" onClick={() => nav('/professeurs?onglet=attente')}>Examiner</button></div>)}</div>
          <div className="card"><h3>Dernières inscriptions</h3>
            {d.dernieres_inscriptions.length === 0 ? <p className="muted">Aucune inscription pour cette année.</p> : d.dernieres_inscriptions.map((i) => <div key={i.id} className="list-item"><div><b>{i.nom}</b><div className="muted">{i.matricule} · {i.classe}</div></div><span className="muted">{fmtDate(i.date)}</span></div>)}</div>
          <Alertes list={d.alertes} />
        </div></>}
    </>
  );
}

function Prof({ annee }) {
  const { data: d, loading } = useFetch('/statistiques/professeur/', { annee: annee.id }, []);
  const s = d || {};
  return (
    <>
      <div className="grid g4 stagger">
        <StatCard loading={loading} icon={School} label="Mes classes" value={s.mes_classes} tone="blue" />
        <StatCard loading={loading} icon={GraduationCap} label="Mes élèves" value={s.mes_eleves} tone="violet" delay={.04} />
        <StatCard loading={loading} icon={CalendarCheck} label="Cours aujourd'hui" value={s.cours_aujourd_hui} tone="green" delay={.08} />
        <StatCard loading={loading} icon={Clock} label="Heures / semaine" value={s.heures_semaine} decimals={1} suffix=" h" tone="orange" delay={.12} />
        <StatCard loading={loading} icon={ClipboardList} label={`Notes saisies (T${s.trimestre_courant || ''})`} value={s.notes_saisies_pct} suffix=" %" tone="blue" delay={.16} />
        <StatCard loading={loading} icon={TrendingUp} label={`Moyenne · ${s.matiere || 'ma matière'}`} value={s.moyenne_matiere} decimals={2} suffix=" /20" tone="green" delay={.2} />
      </div>
      {d && <>
        <div className="card mt"><h3 className="row"><CalendarCheck size={16} />Mes cours d'aujourd'hui</h3>
          {d.cours_du_jour.length === 0 ? <p className="muted">Aucun cours aujourd'hui.</p> : d.cours_du_jour.map((c) => (
            <div key={c.id} className="list-item"><div><b>{c.classe_nom}</b> · {c.matiere_nom}<div className="muted">{c.heure_debut} – {c.heure_fin}{c.salle ? ` · ${c.salle}` : ''}</div></div>
              {c.appel_fait ? <Badge tone="green"><CheckCircle2 size={12} />Appel fait</Badge> : <Link className="btn btn-primary btn-sm" to={`/absences?classe=${c.classe}&matiere=${c.matiere}&date=${c.date}&cours=${c.id}`}>Faire l'appel</Link>}</div>))}
        </div>
        <Charts d={d} prof />
        <div className="mt"><Alertes list={d.alertes} /></div></>}
    </>
  );
}

export default function Dashboard() {
  const { user } = useAuth(); const { annee } = useYear();
  return (
    <>
      <PageHeader title={`Bonjour ${user.prenom}`} subtitle={`Tableau de bord · Année scolaire ${annee?.libelle || ''}`} />
      {annee ? (user.role === 'ADMIN' ? <Admin annee={annee} key={annee.id} /> : <Prof annee={annee} key={annee.id} />) : null}
    </>
  );
}
