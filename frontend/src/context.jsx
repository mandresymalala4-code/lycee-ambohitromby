import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { api, tokens, parseErr } from './api';
import { useToast } from './ui';

const Auth = createContext(null);
const Year = createContext(null);
const Settings = createContext(null);
export const useAuth = () => useContext(Auth);
export const useYear = () => useContext(Year);
export const useSettings = () => useContext(Settings);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);
  const toast = useToast();
  const idle = useRef();

  const applyTheme = (t) => { document.documentElement.dataset.theme = t === 'SOMBRE' ? 'dark' : 'light'; };

  const clear = useCallback((msg) => {
    tokens.clear(); setUser(null); applyTheme('CLAIR');
    try { window.history.replaceState(null, '', '/'); window.history.pushState(null, '', '/'); } catch { /* ignore */ }
    if (msg) toast.info(msg);
  }, [toast]);

  useEffect(() => {
    (async () => {
      if (tokens.access || tokens.refresh) {
        try { const { data } = await api.get('/profil/'); setUser(data); applyTheme(data.theme); } catch { tokens.clear(); }
      }
      setReady(true);
    })();
  }, []);

  useEffect(() => {
    const h = (e) => clear(e.detail);
    window.addEventListener('lycee:logout', h);
    return () => window.removeEventListener('lycee:logout', h);
  }, [clear]);

  useEffect(() => {
    if (!user) return undefined;
    const reset = () => { clearTimeout(idle.current); idle.current = setTimeout(() => clear('Déconnexion automatique après 30 minutes d\'inactivité.'), 30 * 60 * 1000); };
    ['mousemove', 'keydown', 'click', 'touchstart'].forEach((ev) => window.addEventListener(ev, reset));
    reset();
    return () => { clearTimeout(idle.current); ['mousemove', 'keydown', 'click', 'touchstart'].forEach((ev) => window.removeEventListener(ev, reset)); };
  }, [user, clear]);

  /* Sécurité de session : retour arrière, cache du navigateur (bfcache), autre onglet */
  useEffect(() => {
    const connecte = () => !!(tokens.access || tokens.refresh);
    const onPop = () => {
      if (!connecte()) { window.history.pushState(null, '', '/'); return; }   // déconnecté : on reste sur l'écran de connexion
      const st = window.history.state;
      if (st && st.idx === 0 && !st.lyceeGuard) window.history.go(1);          // connecté : pas de retour avant l'application
    };
    const verifier = () => { if (!connecte()) clear(); else api.get('/profil/').catch(() => {}); };
    const onShow = (e) => { if (e.persisted) { if (!connecte()) window.location.replace('/'); else verifier(); } };
    const onVisible = () => { if (document.visibilityState === 'visible' && user) verifier(); };
    const onStorage = (e) => { if ((e.key === 'lycee_access' || e.key === 'lycee_refresh' || e.key === null) && !connecte()) clear('Vous avez été déconnecté.'); };
    window.addEventListener('popstate', onPop);
    window.addEventListener('pageshow', onShow);
    window.addEventListener('storage', onStorage);
    document.addEventListener('visibilitychange', onVisible);
    return () => { window.removeEventListener('popstate', onPop); window.removeEventListener('pageshow', onShow); window.removeEventListener('storage', onStorage); document.removeEventListener('visibilitychange', onVisible); };
  }, [user, clear]);

  useEffect(() => {
    if (user) window.history.pushState({ ...(window.history.state || {}), lyceeGuard: true }, '', window.location.href);   // entrée tampon
  }, [user?.id]); // eslint-disable-line

  const login = async (email, password) => {
    const { data } = await api.post('/auth/login/', { email, password });
    tokens.set(data.access, data.refresh);
    setUser(data.user); applyTheme(data.user.theme);
    return data.user;
  };
  const logout = async () => {
    const refresh = tokens.refresh;
    try { await api.post('/auth/logout/', { refresh }); } catch { /* ignore */ }
    clear();
  };
  const refreshUser = async () => { const { data } = await api.get('/profil/'); setUser(data); return data; };
  const setTheme = async (t) => {
    applyTheme(t); setUser((u) => ({ ...u, theme: t }));
    try { await api.put('/profil/', { theme: t }); } catch (e) { toast.error(parseErr(e).message); }
  };
  const value = useMemo(() => ({ user, ready, login, logout, refreshUser, setTheme, setUser }), [user, ready]); // eslint-disable-line
  return <Auth.Provider value={value}>{children}</Auth.Provider>;
}

export function YearProvider({ children }) {
  const { user, setUser } = useAuth();
  const [annees, setAnnees] = useState([]);
  const [annee, setAnneeState] = useState(null);
  const [courante, setCourante] = useState(null);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    if (!user) return;
    (async () => {
      const [a, p] = await Promise.all([api.get('/annees/'), api.get('/parametres/')]);
      setAnnees(a.data);
      setCourante(p.data.annee_courante);
      const pref = a.data.find((x) => x.annee_debut === user.annee_preferee) || a.data.find((x) => x.id === p.data.annee_courante) || a.data[0];
      setAnneeState(pref);
    })().catch(() => {});
  }, [user?.id]); // eslint-disable-line

  const setAnnee = async (id) => {
    const a = annees.find((x) => x.id === Number(id));
    if (!a) return;
    setAnneeState(a);
    setUser((u) => ({ ...u, annee_preferee: a.annee_debut }));
    api.put('/profil/', { annee_preferee: a.annee_debut }).catch(() => {});
  };
  const reload = () => setVersion((v) => v + 1);
  const reloadYears = async () => {
    const [a, p] = await Promise.all([api.get('/annees/'), api.get('/parametres/')]);
    setAnnees(a.data); setCourante(p.data.annee_courante);
  };
  return <Year.Provider value={{ annees, annee, courante, setAnnee, version, reload, reloadYears }}>{children}</Year.Provider>;
}

export function SettingsProvider({ children }) {
  const { user } = useAuth();
  const [etab, setEtab] = useState({ nom: 'Lycée Ambohitromby', adresse: '', telephone: '', email: '', logo: null });
  const load = useCallback(async () => {
    try { const { data } = await api.get('/parametres/'); setEtab(data.etablissement); } catch { /* ignore */ }
  }, []);
  useEffect(() => { if (user) load(); }, [user?.id, load]); // eslint-disable-line
  return <Settings.Provider value={{ etab, reload: load }}>{children}</Settings.Provider>;
}

export function useFetch(url, params, deps = [], enabled = true) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tick, setTick] = useState(0);
  const key = JSON.stringify(params || {});
  useEffect(() => {
    if (!enabled) { setLoading(false); return undefined; }
    let alive = true;
    setLoading(true);
    api.get(url, { params }).then((r) => { if (alive) { setData(r.data); setError(null); } })
      .catch((e) => { if (alive) { setError(parseErr(e).message); setData(null); } })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [url, key, tick, enabled, ...deps]); // eslint-disable-line
  return { data, loading, error, reload: () => setTick((t) => t + 1), setData };
}
