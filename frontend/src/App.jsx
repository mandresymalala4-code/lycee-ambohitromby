import { lazy, Suspense } from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { useAuth } from './context';
import Layout from './layout';
import Login from './pages/Login';
import { Spinner } from './ui';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const Classes = lazy(() => import('./pages/Classes'));
const Eleves = lazy(() => import('./pages/Eleves'));
const Inscription = lazy(() => import('./pages/Inscription'));
const Professeurs = lazy(() => import('./pages/Professeurs'));
const Matieres = lazy(() => import('./pages/Matieres'));
const Emploi = lazy(() => import('./pages/Emploi'));
const Absences = lazy(() => import('./pages/Absences'));
const Notes = lazy(() => import('./pages/Notes'));
const Resultats = lazy(() => import('./pages/Resultats'));
const Parametres = lazy(() => import('./pages/Parametres'));
const Profil = lazy(() => import('./pages/Profil'));

const Fallback = () => <div style={{ display: 'grid', placeItems: 'center', padding: 60 }}><Spinner size={28} /></div>;

function Page({ children }) {
  const l = useLocation();
  return <motion.div key={l.pathname} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .25 }}>{children}</motion.div>;
}

export default function App() {
  const { user, ready } = useAuth();
  const loc = useLocation();
  if (!ready) return <div style={{ height: '100%', display: 'grid', placeItems: 'center' }}><Spinner size={32} /></div>;
  if (!user) return <Login />;
  const admin = user.role === 'ADMIN';
  const R = (el) => <Page>{el}</Page>;
  return (
    <Layout>
      <Suspense fallback={<Fallback />}>
        <AnimatePresence mode="wait">
          <Routes location={loc} key={loc.pathname}>
            <Route path="/" element={R(<Dashboard />)} />
            <Route path="/classes" element={R(<Classes />)} />
            <Route path="/eleves" element={R(<Eleves />)} />
            <Route path="/professeurs" element={R(<Professeurs />)} />
            <Route path="/matieres" element={R(<Matieres />)} />
            <Route path="/emploi-du-temps" element={R(<Emploi />)} />
            <Route path="/absences" element={R(<Absences />)} />
            <Route path="/notes" element={R(<Notes />)} />
            <Route path="/profil" element={R(<Profil />)} />
            {admin && <Route path="/inscription" element={R(<Inscription />)} />}
            {admin && <Route path="/resultats" element={R(<Resultats />)} />}
            {admin && <Route path="/parametres" element={R(<Parametres />)} />}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AnimatePresence>
      </Suspense>
    </Layout>
  );
}
