const L = 'A-ZÀ-ÖØ-Þ';
export const rules = {
  nom: (v) => { const s = (v || '').trim().replace(/\s+/g, ' '); return (s.length >= 2 && s.length <= 100 && s === s.toUpperCase() && new RegExp(`^[${L} '’-]+$`).test(s)) || 'Le nom doit être en majuscules (2 à 100 caractères).'; },
  prenom: (v) => { const s = (v || '').trim().replace(/\s+/g, ' '); return (s.length >= 2 && s.length <= 100 && s.split(/[ -]/).filter(Boolean).every((t) => /^[A-ZÀ-ÖØ-Þ][a-zß-öø-ÿ'’]*$/.test(t))) || 'Le prénom doit commencer par une majuscule suivie de minuscules.'; },
  adresse: (v) => { const n = (v || '').trim().length; return (n >= 3 && n <= 120) || "L'adresse doit contenir entre 3 et 120 caractères."; },
  tel: (v) => /^03\d{8}$/.test((v || '').replace(/[\s.-]/g, '')) || 'Téléphone invalide (10 chiffres, commençant par 03).',
  telFixe: (v) => /^0[23]\d{8}$/.test((v || '').replace(/[\s.-]/g, '')) || 'Téléphone invalide.',
  email: (v) => (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test((v || '').trim()) && v.length <= 150) || 'Adresse email invalide.',
  mdp: (v) => (!!v && v.length >= 8 && v.length <= 128 && /[A-Za-z]/.test(v) && /\d/.test(v)) || 'Le mot de passe doit contenir au moins 8 caractères avec des lettres et des chiffres.',
  cin: (v) => /^\d{14}$/.test((v || '').replace(/\s/g, '')) || 'Le CIN doit contenir exactement 14 chiffres.',
  obligatoire: (v) => (v !== undefined && v !== null && String(v).trim() !== '') || 'Ce champ est obligatoire.',
  naissanceEleve: (v) => { if (!v) return 'Ce champ est obligatoire.'; return (v >= '1998-01-01' && v <= '2013-12-31') || 'Date de naissance hors limites.'; },
  naissanceAdulte: (min) => (v) => {
    if (!v) return 'Ce champ est obligatoire.';
    const d = new Date(v); const t = new Date(); let a = t.getFullYear() - d.getFullYear();
    if (t.getMonth() < d.getMonth() || (t.getMonth() === d.getMonth() && t.getDate() < d.getDate())) a -= 1;
    return (v > '1950-01-01' && a >= min) || `Date de naissance invalide (${min} ans minimum).`;
  },
  photo: (f) => { if (!f || !f.length) return true; const x = f[0]; return (/\.(jpe?g|png)$/i.test(x.name) && x.size <= 2 * 1024 * 1024) || 'Format de photo non accepté (JPG ou PNG, 2 Mo maximum).'; },
};
export const ariary = (n) => `${Number(n || 0).toLocaleString('fr-FR').replace(/\u202f|\u00a0/g, ' ')} Ar`;
export const fmtDate = (d) => (d ? new Date(d).toLocaleDateString('fr-FR') : '');
export const fmtDateTime = (d) => (d ? new Date(d).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' }) : '');
export const n2 = (x) => (x === null || x === undefined ? '—' : Number(x).toFixed(2).replace('.', ','));
export const hh = (x) => `${String(Number(x || 0)).replace('.', ',')} h`;
export const today = () => new Date().toISOString().slice(0, 10);
export const JOURS = ['', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi'];
export const norm = (s) => String(s ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
