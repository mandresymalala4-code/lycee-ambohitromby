import axios from 'axios';

export const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const K = { a: 'lycee_access', r: 'lycee_refresh' };
export const tokens = {
  get access() { return localStorage.getItem(K.a); },
  get refresh() { return localStorage.getItem(K.r); },
  set(a, r) { localStorage.setItem(K.a, a); if (r) localStorage.setItem(K.r, r); },
  clear() { localStorage.removeItem(K.a); localStorage.removeItem(K.r); },
};

export const api = axios.create({ baseURL: `${API}/api`, timeout: 30000 });
api.interceptors.request.use((c) => {
  if (tokens.access && !c.url.startsWith('/auth/')) c.headers.Authorization = `Bearer ${tokens.access}`;
  return c;
});

let refreshing = null;
api.interceptors.response.use((r) => r, async (error) => {
  const cfg = error.config;
  if (error.response?.status === 401 && cfg && !cfg._retry && !cfg.url.startsWith('/auth/') && tokens.refresh) {
    cfg._retry = true;
    try {
      refreshing = refreshing || axios.post(`${API}/api/auth/refresh/`, { refresh: tokens.refresh }).finally(() => { refreshing = null; });
      const { data } = await refreshing;
      tokens.set(data.access, data.refresh);
      cfg.headers.Authorization = `Bearer ${data.access}`;
      return api(cfg);
    } catch {
      tokens.clear();
      window.dispatchEvent(new CustomEvent('lycee:logout', { detail: 'Votre session a expiré. Veuillez vous reconnecter.' }));
    }
  }
  return Promise.reject(error);
});

export const media = (p) => (p ? (p.startsWith('http') ? p : `${API}${p}`) : null);

export function parseErr(e) {
  if (!e?.response) return { message: 'Impossible de contacter le serveur. Vérifiez que le backend est démarré.', champs: {}, status: 0 };
  const d = e.response.data || {};
  return { message: d.message || 'Une erreur est survenue.', champs: d.champs || {}, status: e.response.status, code: d.code };
}

export function applyErrors(e, setError, map = {}) {
  const { champs } = parseErr(e);
  Object.entries(champs).forEach(([k, v]) => setError(map[k] || k, { type: 'server', message: v }));
}

export async function openPdf(url, params = {}) {
  try {
    const r = await api.get(url, { params, responseType: 'blob' });
    const u = URL.createObjectURL(new Blob([r.data], { type: 'application/pdf' }));
    const w = window.open(u, '_blank');
    if (!w) { const a = document.createElement('a'); a.href = u; a.download = 'document.pdf'; a.click(); }
    setTimeout(() => URL.revokeObjectURL(u), 60000);
  } catch (e) {
    let msg = 'Impossible de générer le PDF.';
    try { msg = JSON.parse(await e.response.data.text()).message || msg; } catch { /* ignore */ }
    throw new Error(msg);
  }
}

export const toForm = (obj) => {
  const f = new FormData();
  Object.entries(obj).forEach(([k, v]) => { if (v !== undefined && v !== null && v !== '') f.append(k, v); });
  return f;
};
