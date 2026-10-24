import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { AnimatePresence, motion } from 'framer-motion';
import { ArrowLeft, Eye, EyeOff, GraduationCap, Info, KeyRound, LogIn, ShieldCheck, UserPlus } from 'lucide-react';
import { api, applyErrors, parseErr, toForm } from '../api';
import { useAuth, useSettings } from '../context';
import { Field, Logo, Spinner, SuccessCheck, useToast } from '../ui';
import { rules } from '../validators';

function Pw({ reg, error, label, ...p }) {
  const [v, setV] = useState(false);
  return (
    <Field label={label} error={error} required>
      <div className="pw"><input className="input" type={v ? 'text' : 'password'} {...reg} {...p} />
        <button type="button" className="icon-btn" onClick={() => setV(!v)} aria-label="Afficher / masquer">{v ? <EyeOff size={15} /> : <Eye size={15} />}</button></div>
    </Field>
  );
}

function LoginForm({ go }) {
  const { login } = useAuth(); const toast = useToast();
  const { register, handleSubmit, setError, formState: { errors, isSubmitting } } = useForm();
  const [err, setErr] = useState('');
  const submit = async (d) => {
    setErr('');
    try { await login(d.email.trim(), d.password); }
    catch (e) { const p = parseErr(e); setErr(p.message); applyErrors(e, setError); }
  };
  return (
    <form onSubmit={handleSubmit(submit)} className="stack" noValidate>
      <div><h2>Connexion</h2><p className="muted">Accédez à votre espace de gestion.</p></div>
      {err && <div className="alert-bar">{err}</div>}
      <Field label="Adresse email" error={errors.email?.message} required><input className="input" type="email" autoComplete="username" autoFocus {...register('email', { validate: rules.email })} /></Field>
      <Pw label="Mot de passe" reg={register('password', { required: 'Ce champ est obligatoire.' })} error={errors.password?.message} autoComplete="current-password" />
      <button className="btn btn-primary btn-block" disabled={isSubmitting}>{isSubmitting ? <Spinner size={14} /> : <LogIn size={16} />}Se connecter</button>
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <button type="button" className="btn btn-ghost btn-sm" onClick={() => go('forgot')}><KeyRound size={14} />Mot de passe oublié</button>
        <button type="button" className="btn btn-ghost btn-sm" onClick={() => go('register')}><UserPlus size={14} />Créer un compte professeur</button>
      </div>
    </form>
  );
}

function Forgot({ go }) {
  const toast = useToast(); const [ok, setOk] = useState(false);
  const { register, handleSubmit, getValues, setError, formState: { errors, isSubmitting } } = useForm();
  const submit = async (d) => {
    try { await api.post('/auth/mot-de-passe-oublie/', { email: d.email, telephone: d.telephone, mot_de_passe: d.mot_de_passe, confirmation: d.confirmation }); setOk(true); }
    catch (e) { toast.error(parseErr(e).message); applyErrors(e, setError); }
  };
  if (ok) return <div className="stack" style={{ alignItems: 'center', textAlign: 'center' }}><SuccessCheck /><h2>Mot de passe modifié</h2><p className="muted">Vous pouvez vous reconnecter.</p><button className="btn btn-primary" onClick={() => go('login')}>Retour à la connexion</button></div>;
  return (
    <form onSubmit={handleSubmit(submit)} className="stack" noValidate>
      <button type="button" className="btn btn-ghost btn-sm" style={{ alignSelf: 'flex-start' }} onClick={() => go('login')}><ArrowLeft size={14} />Retour</button>
      <div><h2>Mot de passe oublié</h2><p className="muted">Confirmez votre identité avec votre email et votre téléphone.</p></div>
      <Field label="Adresse email" error={errors.email?.message} required><input className="input" type="email" {...register('email', { validate: rules.email })} /></Field>
      <Field label="Téléphone" error={errors.telephone?.message} required><input className="input" placeholder="034 00 000 00" {...register('telephone', { validate: rules.tel })} /></Field>
      <Pw label="Nouveau mot de passe" reg={register('mot_de_passe', { validate: rules.mdp })} error={errors.mot_de_passe?.message} />
      <Pw label="Confirmation" reg={register('confirmation', { validate: (v) => v === getValues('mot_de_passe') || 'Les mots de passe ne correspondent pas.' })} error={errors.confirmation?.message} />
      <button className="btn btn-primary btn-block" disabled={isSubmitting}>{isSubmitting && <Spinner size={14} />}Modifier le mot de passe</button>
    </form>
  );
}

function Register({ go }) {
  const toast = useToast(); const [ok, setOk] = useState(false); const [disc, setDisc] = useState([]);
  const { register, handleSubmit, getValues, setError, formState: { errors, isSubmitting } } = useForm();
  useEffect(() => { api.get('/disciplines/').then((r) => setDisc(r.data)).catch(() => {}); }, []);
  const submit = async (d) => {
    const body = { ...d, photo: d.photo?.[0] };
    try { await api.post('/auth/register-professeur/', toForm(body), { headers: { 'Content-Type': 'multipart/form-data' } }); setOk(true); }
    catch (e) { toast.error(parseErr(e).message); applyErrors(e, setError); }
  };
  if (ok) return <div className="stack" style={{ alignItems: 'center', textAlign: 'center' }}><SuccessCheck /><h2>Compte créé</h2><p className="muted">Votre compte sera actif après validation par l'administrateur.</p><button className="btn btn-primary" onClick={() => go('login')}>Retour à la connexion</button></div>;
  const E = errors;
  return (
    <form onSubmit={handleSubmit(submit)} noValidate>
      <button type="button" className="btn btn-ghost btn-sm" onClick={() => go('login')} style={{ marginBottom: 10 }}><ArrowLeft size={14} />Retour</button>
      <h2>Créer un compte professeur</h2><p className="muted mb">Votre compte sera validé par l'administrateur avant activation.</p>
      <div className="form-grid">
        <Field label="Nom" required error={E.nom?.message} hint="En majuscules"><input className="input" {...register('nom', { validate: rules.nom })} /></Field>
        <Field label="Prénoms" required error={E.prenom?.message}><input className="input" {...register('prenom', { validate: rules.prenom })} /></Field>
        <Field label="Date de naissance" required error={E.date_naissance?.message}><input type="date" className="input" {...register('date_naissance', { validate: rules.naissanceAdulte(21) })} /></Field>
        <Field label="Sexe" required error={E.sexe?.message}><select className="input" {...register('sexe', { required: 'Veuillez sélectionner le sexe.' })}><option value="">Choisir…</option><option>Homme</option><option>Femme</option></select></Field>
        <Field label="Adresse" required error={E.adresse?.message} className="full"><input className="input" {...register('adresse', { validate: rules.adresse })} /></Field>
        <Field label="Téléphone" required error={E.telephone?.message}><input className="input" placeholder="034 00 000 00" {...register('telephone', { validate: rules.tel })} /></Field>
        <Field label="Email" required error={E.email?.message}><input type="email" className="input" {...register('email', { validate: rules.email })} /></Field>
        <Field label="CIN (14 chiffres)" required error={E.cin?.message}><input className="input" inputMode="numeric" {...register('cin', { validate: rules.cin })} /></Field>
        <Field label="Matière enseignée" required error={E.matiere?.message}><input className="input" list="disc" {...register('matiere', { validate: rules.obligatoire })} /><datalist id="disc">{disc.map((d) => <option key={d.id} value={d.nom} />)}</datalist></Field>
        <Pw label="Mot de passe" reg={register('mot_de_passe', { validate: rules.mdp })} error={E.mot_de_passe?.message} />
        <Pw label="Confirmation" reg={register('confirmation', { validate: (v) => v === getValues('mot_de_passe') || 'Les mots de passe ne correspondent pas.' })} error={E.confirmation?.message} />
        <Field label="Photo (facultatif)" error={E.photo?.message} className="full" hint="JPG ou PNG, 2 Mo maximum"><input type="file" accept=".jpg,.jpeg,.png" className="input" {...register('photo', { validate: rules.photo })} /></Field>
      </div>
      <button className="btn btn-primary btn-block mt" disabled={isSubmitting}>{isSubmitting && <Spinner size={14} />}Créer mon compte</button>
    </form>
  );
}

export default function Login() {
  const [mode, setMode] = useState('login');
  const [about, setAbout] = useState(false);
  const { etab } = useSettings();
  return (
    <div className="auth">
      <div className="auth-hero">
        <div className="orb" style={{ width: 340, height: 340, right: -90, bottom: -80 }} /><div className="orb" style={{ width: 180, height: 180, left: '40%', top: '55%' }} />
        <div className="row"><Logo size={46} /><b style={{ fontSize: 15, letterSpacing: '.06em' }}>LYCÉE AMBOHITROMBY</b></div>
        <div><motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>Gestion d'étude,<br />simple et fiable.</motion.h1>
          <p>Inscriptions, absences, notes, bulletins et emplois du temps : toute la vie scolaire de l'établissement réunie dans un seul espace sécurisé.</p></div>
        <div className="row" style={{ opacity: .85 }}><ShieldCheck size={18} /><span>Accès sécurisé · Données centralisées</span><GraduationCap size={18} style={{ marginLeft: 12 }} /></div>
      </div>
      <div className="auth-panel">
        <div className={`auth-box ${mode === 'register' ? 'wide' : ''}`}>
          <div className="row mb" style={{ gap: 8 }}><Logo size={30} /><b style={{ color: 'var(--primary)' }}>LYCÉE AMBOHITROMBY</b></div>
          <AnimatePresence mode="wait"><motion.div key={mode} initial={{ opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -24 }} transition={{ duration: .22 }}>
            {mode === 'login' && <LoginForm go={setMode} />}{mode === 'register' && <Register go={setMode} />}{mode === 'forgot' && <Forgot go={setMode} />}
          </motion.div></AnimatePresence>
        </div>
      </div>
    </div>
  );
}
