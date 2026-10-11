import React from 'react';
import { HashRouter, Routes, Route } from 'react-router-dom';
import { I18nProvider } from './i18n';
import { AuthProvider } from './lib/auth-context';
import { ToastProvider } from './components/ui/Toast';
import { Shell } from './components/layout/Shell';
import { ProtectedRoute, PublicRoute } from './components/auth/ProtectedRoute';
import { SignIn } from './pages/SignIn';
import { SignUp } from './pages/SignUp';
import { Home } from './pages/Home';
import { Onboarding } from './pages/Onboarding';
import { SeasonDashboard } from './pages/SeasonDashboard';
import { WeeklyCheckin } from './pages/WeeklyCheckin';
import { Impact } from './pages/Impact';
import { About } from './pages/About';
import { NotFound } from './pages/NotFound';

export const App: React.FC = () => {
  return (
    <I18nProvider>
      <AuthProvider>
        <ToastProvider>
          <HashRouter>
            <Shell>
              <Routes>
                <Route
                  path="/signin"
                  element={
                    <PublicRoute>
                      <SignIn />
                    </PublicRoute>
                  }
                />
                <Route
                  path="/signup"
                  element={
                    <PublicRoute>
                      <SignUp />
                    </PublicRoute>
                  }
                />
                <Route
                  path="/onboarding"
                  element={
                    <ProtectedRoute>
                      <Onboarding />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/dashboard/:fieldId"
                  element={
                    <ProtectedRoute>
                      <SeasonDashboard />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/checkin/:fieldId"
                  element={
                    <ProtectedRoute>
                      <WeeklyCheckin />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/checkin"
                  element={
                    <ProtectedRoute>
                      <WeeklyCheckin />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/impact"
                  element={
                    <ProtectedRoute>
                      <Impact />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/about"
                  element={<About />}
                />
                <Route
                  path="/"
                  element={
                    <ProtectedRoute>
                      <Home />
                    </ProtectedRoute>
                  }
                />
                {/* 404 route */}
                <Route path="*" element={<NotFound />} />
              </Routes>
            </Shell>
          </HashRouter>
        </ToastProvider>
      </AuthProvider>
    </I18nProvider>
  );
};

export default App;
