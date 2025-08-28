import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { useEffect } from 'react';
import { useStore } from '@/store';
import Layout from '@/components/layout/Layout';
import Dashboard from '@/pages/Dashboard';
import Projects from '@/pages/Projects';
import Sessions from '@/pages/Sessions';
import SessionDetail from '@/pages/SessionDetail';
import Prompts from '@/pages/Prompts';
import Search from '@/pages/Search';
import Analytics from '@/pages/Analytics';
import ImportExport from '@/pages/ImportExport';
import Backup from '@/pages/Backup';
import Settings from '@/pages/Settings';
import Admin from '@/pages/Admin';
import RateLimits from '@/pages/RateLimits';
import Login from '@/pages/Login';
import OIDCCallback from '@/pages/OIDCCallback';
import NotFound from '@/pages/NotFound';
import { PageTransition } from '@/components/PageTransition';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

function App() {
  const theme = useStore((state) => state.ui.theme);

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/auth/oidc/callback" element={<OIDCCallback />} />
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <Layout>
                  <PageTransition mode="fade" duration={0.2}>
                    <Routes>
                      <Route
                        path="/"
                        element={<Navigate to="/dashboard" replace />}
                      />
                      <Route path="/dashboard" element={<Dashboard />} />
                      <Route path="/projects" element={<Projects />} />
                      <Route
                        path="/projects/:projectId"
                        element={<Projects />}
                      />
                      <Route path="/sessions" element={<Sessions />} />
                      <Route
                        path="/sessions/:sessionId"
                        element={<SessionDetail />}
                      />
                      <Route path="/prompts" element={<Prompts />} />
                      <Route path="/prompts/:promptId" element={<Prompts />} />
                      <Route path="/search" element={<Search />} />
                      <Route path="/analytics" element={<Analytics />} />
                      <Route path="/import-export" element={<ImportExport />} />
                      <Route path="/backup" element={<Backup />} />
                      <Route path="/rate-limits" element={<RateLimits />} />
                      <Route path="/settings" element={<Settings />} />
                      <Route path="/admin" element={<Admin />} />
                      <Route path="*" element={<NotFound />} />
                    </Routes>
                  </PageTransition>
                </Layout>
              </ProtectedRoute>
            }
          />
        </Routes>
        <Toaster
          position="bottom-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
          }}
        />
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
