import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import { BackgroundBlobs } from './components/BackgroundBlobs';
import { Navbar } from './components/Navbar';

// Lazy load pages for code splitting
const Landing = React.lazy(() => import('./pages/Landing'));
const LoginRegister = React.lazy(() => import('./pages/LoginRegister'));
const Onboarding = React.lazy(() => import('./pages/Onboarding'));
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const PracticeTest = React.lazy(() => import('./pages/PracticeTest'));
const MockTest = React.lazy(() => import('./pages/MockTest'));
const ResultReview = React.lazy(() => import('./pages/ResultReview'));
const StudyPlanner = React.lazy(() => import('./pages/StudyPlanner'));
const PyqAnalysis = React.lazy(() => import('./pages/PyqAnalysis'));
const Analytics = React.lazy(() => import('./pages/Analytics'));
const ChatMentor = React.lazy(() => import('./pages/ChatMentor'));
const Profile = React.lazy(() => import('./pages/Profile'));

// New Overhaul Pages
const PYQ = React.lazy(() => import('./pages/PYQ'));
const AdminPanel = React.lazy(() => import('./pages/AdminPanel'));

// Loading fallback with shimmer effect
const PageLoader: React.FC = () => (
  <div className="min-h-screen flex items-center justify-center bg-surface-50">
    <div className="flex flex-col items-center gap-4">
      <div className="w-12 h-12 rounded-2xl bg-brand-yellow animate-pulse flex items-center justify-center shadow-card">
        <span className="text-brand-black font-extrabold text-lg">💡</span>
      </div>
      <div className="skeleton h-3 w-32" />
    </div>
  </div>
);

// Protected route wrapper
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) return <PageLoader />;
  if (!user) return <Navigate to="/login" replace />;
  
  return <>{children}</>;
};

// Layout with navbar for authenticated pages
const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="page-wrapper min-h-screen bg-surface-50">
      <Navbar />
      <main className="min-h-[calc(100vh-64px)]">
        {children}
      </main>
    </div>
  );
};

const AppRoutes: React.FC = () => {
  const { user, loading } = useAuth();

  if (loading) return <PageLoader />;

  return (
    <AnimatePresence mode="wait">
      <React.Suspense fallback={<PageLoader />}>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={user ? <Navigate to="/dashboard" replace /> : <Landing />} />
          <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : <LoginRegister />} />
          
          {/* Onboarding (authenticated but no nav) */}
          <Route path="/onboarding" element={
            <ProtectedRoute><Onboarding /></ProtectedRoute>
          } />

          {/* Developer Portal (Self authenticated) */}
          <Route path="/admin" element={<AdminPanel />} />

          {/* Protected Routes with Nav */}
          <Route path="/dashboard" element={
            <ProtectedRoute><AppLayout><Dashboard /></AppLayout></ProtectedRoute>
          } />
          <Route path="/practice" element={
            <ProtectedRoute><AppLayout><PracticeTest /></AppLayout></ProtectedRoute>
          } />
          <Route path="/mock-test" element={
            <ProtectedRoute><AppLayout><MockTest /></AppLayout></ProtectedRoute>
          } />
          <Route path="/results" element={
            <ProtectedRoute><AppLayout><ResultReview /></AppLayout></ProtectedRoute>
          } />
          <Route path="/results/:id" element={
            <ProtectedRoute><AppLayout><ResultReview /></AppLayout></ProtectedRoute>
          } />
          <Route path="/study-plan" element={
            <ProtectedRoute><AppLayout><StudyPlanner /></AppLayout></ProtectedRoute>
          } />
          <Route path="/pyq" element={
            <ProtectedRoute><AppLayout><PYQ /></AppLayout></ProtectedRoute>
          } />
          <Route path="/pyq-analysis" element={
            <ProtectedRoute><AppLayout><PyqAnalysis /></AppLayout></ProtectedRoute>
          } />
          <Route path="/analytics" element={
            <ProtectedRoute><AppLayout><Analytics /></AppLayout></ProtectedRoute>
          } />
          <Route path="/chat" element={
            <ProtectedRoute><AppLayout><ChatMentor /></AppLayout></ProtectedRoute>
          } />
          <Route path="/profile" element={
            <ProtectedRoute><AppLayout><Profile /></AppLayout></ProtectedRoute>
          } />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </React.Suspense>
    </AnimatePresence>
  );
};

function App() {
  return (
    <Router>
      <AuthProvider>
        <ToastProvider>
          <BackgroundBlobs />
          <AppRoutes />
        </ToastProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;
