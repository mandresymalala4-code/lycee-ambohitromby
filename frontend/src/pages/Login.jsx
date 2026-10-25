import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { AnimatePresence, motion } from 'framer-motion';
import { ArrowLeft, ArrowRight, Eye, EyeOff, GraduationCap, Info, KeyRound, LogIn, ShieldCheck, UserPlus } from 'lucide-react';
import { api, applyErrors, parseErr, toForm } from '../api';
import { useAuth, useSettings } from '../context';
import { Avatar, Field, Logo, Spinner, Stepper, SuccessCheck, useToast } from '../ui';
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

const REG_STEPS = ['Identité', 'Coordonnées', 'Sécurité'];
const REG_FIELDS = [['nom', 'prenom', 'date_naissance', 'sexe'], ['adresse', 'telephone', 'email', 'cin', 'matiere'], ['mot_de_passe', 'confirmation']];

function Register({ go }) {
  const toast = useToast(); const [ok, setOk] = useState(false); const [disc, setDisc] = useState([]);
  const [step, setStep] = useState(0); const [dir, setDir] = useState(1);
  const [photo, setPhoto] = useState(null); const [photoUrl, setPhotoUrl] = useState(null); const [photoErr, setPhotoErr] = useState('');
  const [srv, setSrv] = useState({});   // erreurs renvoyées par le serveur (doublons, etc.), effacées dès que le champ est modifié
  const { register, handleSubmit, trigger, watch, getValues, formState: { errors, isSubmitting } } = useForm({ shouldUnregister: false });
  useEffect(() => { api.get('/disciplines/').then((r) => setDisc(r.data)).catch(() => {}); }, []);
  useEffect(() => { if (!photo) { setPhotoUrl(null); return undefined; } const u = URL.createObjectURL(photo); setPhotoUrl(u); return () => URL.revokeObjectURL(u); }, [photo]);

  const R = (name, opts) => register(name, { ...opts, onChange: () => setSrv((x) => { if (!x[name]) return x; const { [name]: _omit, ...rest } = x; return rest; }) });
  const err = (k) => errors[k]?.message || srv[k];

  const next = async () => {
    const okStep = await trigger(REG_FIELDS[step]);
    if (!okStep || REG_FIELDS[step].some((f) => srv[f])) return;
    setDir(1); setStep((s) => Math.min(s + 1, 2));
  };
  const prev = () => { setDir(-1); setStep((s) => Math.max(s - 1, 0)); };

  const submit = async (d) => {
    const body = { ...d, photo };
    try { await api.post('/auth/register-professeur/', toForm(body), { headers: { 'Content-Type': 'multipart/form-data' } }); setOk(true); }
    catch (e) {
      const p = parseErr(e); toast.error(p.message);
      setSrv(p.champs);
      const first = REG_FIELDS.findIndex((fs) => fs.some((f) => p.champs[f]) || (fs === REG_FIELDS[0] && p.champs.photo));
      if (first >= 0) { setDir(first < step ? -1 : 1); setStep(first); }
    }
  };
  const onFile = (e) => {
    const f = e.target.files[0];
    const r = rules.photo(f ? [f] : null);
    if (r !== true) { setPhotoErr(r); setPhoto(null); e.target.value = ''; } else { setPhotoErr(''); setPhoto(f || null); }
  };

  if (ok) return <div className="stack" style={{ alignItems: 'center', textAlign: 'center' }}><SuccessCheck /><h2>Compte créé</h2><p className="muted">Votre compte sera actif après validation par l'administrateur.</p><button className="btn btn-primary" onClick={() => go('login')}>Retour à la connexion</button></div>;

  const panels = [
    <div key="0" className="form-grid">
      <Field label="Nom" required error={err('nom')} hint="En majuscules"><input className="input" autoFocus {...R('nom', { validate: rules.nom })} /></Field>
      <Field label="Prénoms" required error={err('prenom')}><input className="input" {...R('prenom', { validate: rules.prenom })} /></Field>
      <Field label="Date de naissance" required error={err('date_naissance')}><input type="date" className="input" {...R('date_naissance', { validate: rules.naissanceAdulte(21) })} /></Field>
      <Field label="Sexe" required error={err('sexe')}><select className="input" {...R('sexe', { required: 'Veuillez sélectionner le sexe.' })}><option value="">Choisir…</option><option>Homme</option><option>Femme</option></select></Field>
      <div className="photo-drop full">
        {photoUrl ? <img className="avatar" src={photoUrl} width={56} height={56} alt="" /> : <Avatar name={`${watch('nom') || ''} ${watch('prenom') || ''}`} size={56} />}
        <Field label="Photo (facultatif)" error={photoErr || srv.photo} hint={photo ? `Photo sélectionnée : ${photo.name}` : 'JPG ou PNG, 2 Mo maximum'}><input type="file" accept=".jpg,.jpeg,.png" className="input" onChange={onFile} /></Field>
      </div>
    </div>,
    <div key="1" className="form-grid">
      <Field label="Adresse" required error={err('adresse')} className="full"><input className="input" autoFocus {...R('adresse', { validate: rules.adresse })} /></Field>
      <Field label="Téléphone" required error={err('telephone')}><input className="input" placeholder="034 00 000 00" {...R('telephone', { validate: rules.tel })} /></Field>
      <Field label="Email" required error={err('email')}><input type="email" className="input" {...R('email', { validate: rules.email })} /></Field>
      <Field label="CIN (14 chiffres)" required error={err('cin')}><input className="input" inputMode="numeric" {...R('cin', { validate: rules.cin })} /></Field>
      <Field label="Matière enseignée" required error={err('matiere')}><input className="input" list="disc" {...R('matiere', { validate: rules.obligatoire })} /><datalist id="disc">{disc.map((d) => <option key={d.id} value={d.nom} />)}</datalist></Field>
    </div>,
    <div key="2" className="stack">
      <div className="form-grid">
        <Pw label="Mot de passe" reg={R('mot_de_passe', { validate: rules.mdp })} error={err('mot_de_passe')} autoFocus />
        <Pw label="Confirmation" reg={R('confirmation', { validate: (v) => v === getValues('mot_de_passe') || 'Les mots de passe ne correspondent pas.' })} error={err('confirmation')} />
      </div>
      <p className="field-hint">Au moins 8 caractères, avec des lettres et des chiffres.</p>
      <div className="card" style={{ background: 'var(--surface-2)', boxShadow: 'none' }}>
        <h3>Récapitulatif</h3>
        <dl className="kv"><dt>Nom</dt><dd>{watch('nom')} {watch('prenom')}</dd><dt>Email</dt><dd>{watch('email')}</dd><dt>Téléphone</dt><dd>{watch('telephone')}</dd><dt>Matière</dt><dd>{watch('matiere')}</dd></dl>
      </div>
    </div>,
  ];

  return (
    <form onSubmit={(e) => { e.preventDefault(); if (step < 2) next(); else handleSubmit(submit)(e); }} noValidate>
      <button type="button" className="btn btn-ghost btn-sm" onClick={() => go('login')} style={{ marginBottom: 10 }}><ArrowLeft size={14} />Retour</button>
      <h2>Créer un compte professeur</h2><p className="muted mb">Votre compte sera validé par l'administrateur avant activation.</p>
      <Stepper steps={REG_STEPS} current={step} />
      <AnimatePresence mode="wait" initial={false}>
        <motion.div key={step} initial={{ opacity: 0, x: 28 * dir }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -28 * dir }} transition={{ duration: .2 }}>{panels[step]}</motion.div>
      </AnimatePresence>
      <div className="row mt" style={{ justifyContent: 'space-between' }}>
        {step > 0 ? <button type="button" className="btn btn-ghost" onClick={prev}><ArrowLeft size={16} />Précédent</button> : <span />}
        {step < 2
          ? <button type="submit" className="btn btn-primary">Suivant<ArrowRight size={16} /></button>
          : <button className="btn btn-ok" disabled={isSubmitting}>{isSubmitting && <Spinner size={14} />}Créer mon compte</button>}
      </div>
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
