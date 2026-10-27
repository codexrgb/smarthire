import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AppLayout } from './components/layout/AppLayout';
import { LandingPage } from './pages/LandingPage';
import { AuthPage } from './pages/AuthPage';
import { CandidateDashboard } from './pages/CandidateDashboard';
import { ResumeAnalyzerPage } from './pages/ResumeAnalyzerPage';
import { JobExplorerPage } from './pages/JobExplorerPage';
import { JobMatchDetailsPage } from './pages/JobMatchDetailsPage';
import { SkillGapPage } from './pages/SkillGapPage';
import { RecruiterDashboard } from './pages/RecruiterDashboard';
import { CandidateManagementPage } from './pages/CandidateManagementPage';
import { JobManagementPage } from './pages/JobManagementPage';
import { ModelAnalyticsPage } from './pages/ModelAnalyticsPage';
import { SettingsPage } from './pages/SettingsPage';
import { Alert } from './components/common/Alert';

// Protected Route Guard
const ProtectedRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 text-slate-500 text-sm">
        Verifying authorization...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth" state={{ from: location }} replace />;
  }

  return children;
};

// Recruiter RBAC Route Guard
const RecruiterRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const { isAuthenticated, isRecruiter, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 text-slate-500 text-sm">
        Checking role permissions...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth" state={{ from: location }} replace />;
  }

  if (!isRecruiter) {
    return (
      <div className="p-8 max-w-xl mx-auto">
        <Alert type="error" title="403 Forbidden">
          Operation requires recruiter or administrator privileges. Candidate accounts cannot view
          recruiter records.
        </Alert>
      </div>
    );
  }

  return children;
};

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
          {/* Public Landing & Auth */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/auth" element={<AuthPage />} />
          <Route path="/login" element={<Navigate to="/auth" replace />} />
          <Route path="/register" element={<Navigate to="/auth" replace />} />

          {/* Application Layout Shell */}
          <Route element={<AppLayout />}>
            {/* Candidate & General Routes */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <CandidateDashboard />
                </ProtectedRoute>
              }
            />
            <Route path="/resumes/analyze" element={<ResumeAnalyzerPage />} />
            <Route path="/jobs" element={<JobExplorerPage />} />
            <Route path="/matching" element={<JobMatchDetailsPage />} />
            <Route path="/skill-gap" element={<SkillGapPage />} />
            <Route path="/analytics" element={<ModelAnalyticsPage />} />
            <Route path="/settings" element={<SettingsPage />} />

            {/* Recruiter-Protected Routes */}
            <Route
              path="/recruiter/dashboard"
              element={
                <RecruiterRoute>
                  <RecruiterDashboard />
                </RecruiterRoute>
              }
            />
            <Route
              path="/recruiter/candidates"
              element={
                <RecruiterRoute>
                  <CandidateManagementPage />
                </RecruiterRoute>
              }
            />
            <Route
              path="/recruiter/jobs"
              element={
                <RecruiterRoute>
                  <JobManagementPage />
                </RecruiterRoute>
              }
            />
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  </ThemeProvider>
  );
};

export default App;
