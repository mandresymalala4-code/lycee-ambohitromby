import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { KeyRound, Save } from 'lucide-react';
import { api, applyErrors, parseErr, toForm } from '../api';
import { useAuth } from '../context';
import { Avatar, Badge, Field, PageHeader, Spinner, useToast } from '../ui';
import { rules } from '../validators';
import { ElevePhotoField } from './Eleves';

export default function Profil() {
  const { user, setUser } = useAuth(); const toast = useToast(); const admin = user.role === 'ADMIN';
  const [file, setFile] = useState(null);
  const f = useForm(); const p = useForm();
  useEffect(() => { f.reset({ nom: user.nom, prenom: user.prenom, date_naissance: user.date_naissance, sexe: user.sexe, adresse: user.adresse, telephone: user.telephone, email: user.email }); }, [user]); // eslint-disable-line
  const save = async (d) => {
    const body = admin ? { ...d } : { adresse: d.adresse, telephone: d.telephone };
    try { const { data } = await api.put('/profil/', toForm({ ...body, photo: file }), { headers: { 'Content-Type': 'multipart/form-data' } }); setUser(data); setFile(null); toast.success('Profil mis à jour.'); }
    catch (e) { toast.error(parseErr(e).message); applyErrors(e, f.setError); }
  };
  const pw = async (d) => {
    try { await api.put('/profil/', { ancien_mot_de_passe: d.ancien, nouveau_mot_de_passe: d.nouveau, confirmation: d.confirmation }); toast.success('Mot de passe modifié.'); p.reset({ ancien: '', nouveau: '', confirmation: '' }); }
    catch (e) { const { champs, message } = parseErr(e); toast.error(message); Object.entries(champs).forEach(([k, v]) => p.setError({ ancien_mot_de_passe: 'ancien', nouveau_mot_de_passe: 'nouveau' }[k] || k, { message: v })); }
  };
  const E = f.formState.errors; const P = p.formState.errors;
  return (
    <>
      <PageHeader title="Mon profil" subtitle={admin ? 'Administrateur' : `Professeur · ${user.professeur?.discipline_nom} · ${user.professeur?.code || ''}`} />
      <div className="grid g2" style={{ alignItems: 'start' }}>
        <form className="card" onSubmit={f.handleSubmit(save)} noValidate>
          <div className="row mb"><Avatar src={user.photo} name={user.nom_complet} size={64} /><div><h2>{user.nom_complet}</h2><Badge tone="blue">{user.email}</Badge></div></div>
          <div className="form-grid">
            <Field label="Nom" error={E.nom?.message}><input className="input" disabled={!admin} {...f.register('nom', admin ? { validate: rules.nom } : {})} /></Field>
            <Field label="Prénoms" error={E.prenom?.message}><input className="input" disabled={!admin} {...f.register('prenom', admin ? { validate: rules.prenom } : {})} /></Field>
            <Field label="Date de naissance" error={E.date_naissance?.message}><input type="date" className="input" disabled={!admin} {...f.register('date_naissance', admin ? { validate: rules.naissanceAdulte(18) } : {})} /></Field>
            <Field label="Sexe"><select className="input" disabled={!admin} {...f.register('sexe')}><option>Homme</option><option>Femme</option></select></Field>
            <Field label="Email" error={E.email?.message} className="full"><input className="input" disabled={!admin} {...f.register('email', admin ? { validate: rules.email } : {})} /></Field>
            <Field label="Adresse" required error={E.adresse?.message} className="full"><input className="input" {...f.register('adresse', { validate: rules.adresse })} /></Field>
            <Field label="Téléphone" required error={E.telephone?.message}><input className="input" {...f.register('telephone', { validate: rules.tel })} /></Field>
            <ElevePhotoField file={file} setFile={setFile} current={user.photo} name={user.nom_complet} />
          </div>
          <div className="row row-end mt"><button className="btn btn-primary" disabled={f.formState.isSubmitting}>{f.formState.isSubmitting ? <Spinner size={14} /> : <Save size={16} />}Enregistrer</button></div>
        </form>
        <form className="card" onSubmit={p.handleSubmit(pw)} noValidate>
          <h3 className="row"><KeyRound size={16} />Changer le mot de passe</h3><p className="muted mb">Au moins 8 caractères, avec des lettres et des chiffres.</p>
          <div className="stack">
            <Field label="Mot de passe actuel" error={P.ancien?.message} required><input type="password" className="input" autoComplete="current-password" {...p.register('ancien', { required: 'Ce champ est obligatoire.' })} /></Field>
            <Field label="Nouveau mot de passe" error={P.nouveau?.message} required><input type="password" className="input" autoComplete="new-password" {...p.register('nouveau', { validate: rules.mdp })} /></Field>
            <Field label="Confirmation" error={P.confirmation?.message} required><input type="password" className="input" autoComplete="new-password" {...p.register('confirmation', { validate: (v) => v === p.getValues('nouveau') || 'Les mots de passe ne correspondent pas.' })} /></Field>
            <div className="row row-end"><button className="btn btn-primary" disabled={p.formState.isSubmitting}>{p.formState.isSubmitting && <Spinner size={14} />}Modifier le mot de passe</button></div>
          </div>
        </form>
      </div>
    </>
  );
}
