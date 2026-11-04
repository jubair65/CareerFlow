import { useState, useEffect, useCallback, lazy, Suspense } from 'react';
import type { FormEvent, ReactNode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from '@/components/ui/toaster';
import { TooltipProvider } from '@/components/ui/tooltip';
import { useLocation, Router as WouterRouter } from 'wouter';
import {
  ArrowRight, BriefcaseBusiness, Building2, Check, CheckCircle2,
  Eye, EyeOff, Home, LockKeyhole, LogOut, Play, ShieldCheck, Sparkles, TrendingUp, X
} from 'lucide-react';
import { apiRegister, apiLogin, apiLogout, apiGetCurrentUser, getStoredUser } from '@/api/auth';
import { LandingPage } from './components/landing/LandingPage';
import { ProtectedRoute } from './components/auth/ProtectedRoute';

// Route-level code splitting (Phase 4)
const StudentDashboard = lazy(() => import('./pages/StudentDashboard').then(m => ({ default: m.StudentDashboard })));
const HrDashboard = lazy(() => import('./pages/HrDashboard').then(m => ({ default: m.HrDashboard })));
const AgencyDashboard = lazy(() => import('./pages/AgencyDashboard').then(m => ({ default: m.AgencyDashboard })));
const CvStudio = lazy(() => import('./pages/CvStudio').then(m => ({ default: m.CvStudio })));
const CvResults = lazy(() => import('./pages/CvResults').then(m => ({ default: m.CvResults })));
const CvProcessingPage = lazy(() => import('./components/cv/CvProcessingView').then(m => ({ default: m.CvProcessingPage })));
const JobMatch = lazy(() => import('./pages/JobMatch').then(m => ({ default: m.JobMatch })));
const PresentationStudio = lazy(() => import('./pages/PresentationStudio').then(m => ({ default: m.PresentationStudio })));
const VideoHistory = lazy(() => import('./pages/VideoHistory').then(m => ({ default: m.VideoHistory })));
const PresentationDetailReportPage = lazy(() => import('./pages/PresentationDetailReportPage').then(m => ({ default: m.PresentationDetailReportPage })));
const ScoreTrendsPage = lazy(() => import('./pages/ScoreTrendsPage').then(m => ({ default: m.ScoreTrendsPage })));
const RecruitmentRoomsPage = lazy(() => import('./pages/RecruitmentRoomsPage').then(m => ({ default: m.RecruitmentRoomsPage })));
const PublicApplicationPage = lazy(() => import('./pages/PublicApplicationPage').then(m => ({ default: m.PublicApplicationPage })));
const ForgotPasswordPage = lazy(() => import('./pages/ForgotPasswordPage').then(m => ({ default: m.ForgotPasswordPage })));
const ResetPasswordPage = lazy(() => import('./pages/ResetPasswordPage').then(m => ({ default: m.ResetPasswordPage })));
const LoginPage = lazy(() => import('./pages/LoginPage').then(m => ({ default: m.LoginPage })));
const RegisterPage = lazy(() => import('./pages/RegisterPage').then(m => ({ default: m.RegisterPage })));
const AgencyClientManagementPage = lazy(() => import('./pages/AgencyClientManagementPage').then(m => ({ default: m.AgencyClientManagementPage })));
const AgencyRoomsPage = lazy(() => import('./pages/AgencyRoomsPage').then(m => ({ default: m.AgencyRoomsPage })));
const AgencyApplicantsPipelinePage = lazy(() => import('./pages/AgencyApplicantsPipelinePage').then(m => ({ default: m.AgencyApplicantsPipelinePage })));
const NotificationsPage = lazy(() => import('./pages/NotificationsPage').then(m => ({ default: m.NotificationsPage })));
const ApplicantStatusPage = lazy(() => import('./pages/ApplicantStatusPage').then(m => ({ default: m.ApplicantStatusPage })));
const JobBoardPage = lazy(() => import('./pages/JobBoardPage').then(m => ({ default: m.JobBoardPage })));
const ProfilePage = lazy(() => import('./pages/ProfilePage').then(m => ({ default: m.ProfilePage })));
const SettingsPage = lazy(() => import('./pages/SettingsPage').then(m => ({ default: m.SettingsPage })));
const HrApplicantsPage = lazy(() => import('./pages/HrApplicantsPage').then(m => ({ default: m.HrApplicantsPage })));
const HrShortlistedPage = lazy(() => import('./pages/HrShortlistedPage').then(m => ({ default: m.HrShortlistedPage })));
const HrReportsPage = lazy(() => import('./pages/HrReportsPage').then(m => ({ default: m.HrReportsPage })));
const AgencyShortlistedPage = lazy(() => import('./pages/AgencyShortlistedPage').then(m => ({ default: m.AgencyShortlistedPage })));
const AgencyReportsPage = lazy(() => import('./pages/AgencyReportsPage').then(m => ({ default: m.AgencyReportsPage })));
const NotFound = lazy(() => import('./pages/not-found'));

function PageSuspenseFallback() {
  return (
    <div className="flex min-h-[50vh] w-full items-center justify-center p-8" data-testid="page-suspense-fallback">
      <div className="flex flex-col items-center gap-3">
        <div className="h-8 w-8 animate-spin rounded-full border-3 border-[#277254] border-t-transparent" />
        <span className="text-xs font-semibold text-[#7b8490]">Loading page...</span>
      </div>
    </div>
  );
}


const queryClient = new QueryClient();

type Role = 'student' | 'hr' | 'agency';
type Notify = (message: string, tone?: 'success' | 'info' | 'error') => void;


function Landing() {
  return <LandingPage />;
}

function DashboardRedirect({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();

  useEffect(() => {
    const user = getStoredUser();
    const sessionStr = localStorage.getItem('careerflow-session');
    let session = null;
    try {
      session = sessionStr ? JSON.parse(sessionStr) : null;
    } catch {}

    const rawRole = user?.role || session?.role;

    if (!rawRole) {
      notify('Please log in to view your dashboard.', 'info');
      setLocation('/login');
      return;
    }

    const role: Role =
      rawRole === 'HR_MANAGER' || rawRole === 'hr'
        ? 'hr'
        : rawRole === 'AGENCY_ADMIN' || rawRole === 'agency'
        ? 'agency'
        : 'student';

    setLocation(`/${role}/dashboard`);
  }, [setLocation, notify]);

  return (
    <div className="grid min-h-screen place-items-center bg-[#f5f1e6]">
      <div className="flex flex-col items-center gap-3">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-[#277254] border-t-transparent" />
        <p className="text-sm font-semibold text-[#526072]">Opening your workspace dashboard...</p>
      </div>
    </div>
  );
}

function RoutedApp({ notify }: { notify: Notify }) {
  const [path] = useLocation();
  if (path === '/') return <Landing />;
  if (path === '/login') return <LoginPage notify={notify} />;
  if (path === '/register') return <RegisterPage notify={notify} />;
  if (path === '/forgot-password') return <ForgotPasswordPage notify={notify} />;
  if (path === '/reset-password' || path.startsWith('/reset-password')) return <ResetPasswordPage notify={notify} />;

  if (path === '/student/dashboard') {
    return (
      <ProtectedRoute allowedRoles={['student']} notify={notify}>
        <StudentDashboard notify={notify} />
      </ProtectedRoute>
    );
  }

  if (path === '/student/cv') {
    return (
      <ProtectedRoute allowedRoles={['student']} notify={notify}>
        <CvStudio notify={notify} />
      </ProtectedRoute>
    );
  }

  if (path === '/student/cv/processing') {
    return (
      <ProtectedRoute allowedRoles={['student']} notify={notify}>
        <CvProcessingPage notify={notify} />
      </ProtectedRoute>
    );
  }

  if (path === '/student/cv/results' || path === '/student/cv/feedback') {
    return (
      <ProtectedRoute allowedRoles={['student']} notify={notify}>
        <CvResults notify={notify} />
      </ProtectedRoute>
    );
  }

  if (path === '/student/cv/match') {
    return (
      <ProtectedRoute allowedRoles={['student']} notify={notify}>
        <JobMatch notify={notify} />
      </ProtectedRoute>
    );
  }

  if (path === '/student/presentation' || path === '/student/practice') {
    return (
      <ProtectedRoute allowedRoles={['student']} notify={notify}>
        <PresentationStudio notify={notify} />
      </ProtectedRoute>
    );
  }

  if (path === '/student/videos' || path === '/presentation/history' || path === '/student/presentation/history') {
    return (
      <ProtectedRoute allowedRoles={['student']} notify={notify}>
        <VideoHistory notify={notify} />
      </ProtectedRoute>
    );
  }

  if (path.startsWith('/presentation/history/')) {
    return (
      <ProtectedRoute allowedRoles={['student']} notify={notify}>
        <PresentationDetailReportPage notify={notify} />
      </ProtectedRoute>
    );
  }

  if (path === '/presentation/trends' || path === '/student/presentation/trends' || path === '/student/trends' || path === '/student/progress') {
    return (
      <ProtectedRoute allowedRoles={['student']} notify={notify}>
        <ScoreTrendsPage notify={notify} />
      </ProtectedRoute>
    );
  }


  if (path === '/hr/dashboard') {
    return (
      <ProtectedRoute allowedRoles={['hr']} notify={notify}>
        <HrDashboard notify={notify} />
      </ProtectedRoute>
    );
  }

  if (path === '/hr/rooms') {
    return (
      <ProtectedRoute allowedRoles={['hr']} notify={notify}>
        <RecruitmentRoomsPage notify={notify} />
      </ProtectedRoute>
    );
  }

  if (path === '/agency/dashboard') {
    return (
      <ProtectedRoute allowedRoles={['agency']} notify={notify}>
        <AgencyDashboard notify={notify} />
      </ProtectedRoute>
    );
  }

  if (path === '/agency/clients' || path === '/agency/client-companies') {
    return (
      <ProtectedRoute allowedRoles={['agency']} notify={notify}>
        <AgencyClientManagementPage notify={notify} />
      </ProtectedRoute>
    );
  }

  if (path === '/agency/rooms') {
    return (
      <ProtectedRoute allowedRoles={['agency']} notify={notify}>
        <AgencyRoomsPage notify={notify} />
      </ProtectedRoute>
    );
  }

  if (path === '/agency/pipeline' || path === '/agency/applicants') {
    return (
      <ProtectedRoute allowedRoles={['agency']} notify={notify}>
        <AgencyApplicantsPipelinePage notify={notify} />
      </ProtectedRoute>
    );
  }

  if (path === '/notifications' || path === '/student/notifications') {
    return (
      <ProtectedRoute allowedRoles={['student', 'hr', 'agency']} notify={notify}>
        <NotificationsPage notify={notify} />
      </ProtectedRoute>
    );
  }

  if (
    path === '/student/applications' ||
    path === '/applications/my-status' ||
    path === '/applications' ||
    path === '/my-applications'
  ) {
    return (
      <ProtectedRoute allowedRoles={['student']} notify={notify}>
        <ApplicantStatusPage notify={notify} />
      </ProtectedRoute>
    );
  }

  if (path === '/student/jobs' || path === '/jobs') {
    return (
      <ProtectedRoute allowedRoles={['student']} notify={notify}>
        <JobBoardPage notify={notify} />
      </ProtectedRoute>
    );
  }

  if (
    path === '/profile' ||
    path === '/student/profile' ||
    path === '/hr/profile' ||
    path === '/agency/profile'
  ) {
    return (
      <ProtectedRoute allowedRoles={['student', 'hr', 'agency']} notify={notify}>
        <ProfilePage notify={notify} />
      </ProtectedRoute>
    );
  }

  if (
    path === '/settings' ||
    path === '/student/settings' ||
    path === '/hr/settings' ||
    path === '/agency/settings'
  ) {
    return (
      <ProtectedRoute allowedRoles={['student', 'hr', 'agency']} notify={notify}>
        <SettingsPage notify={notify} />
      </ProtectedRoute>
    );
  }

  if (path === '/hr/applicants') {
    return (
      <ProtectedRoute allowedRoles={['hr']} notify={notify}>
        <HrApplicantsPage notify={notify} />
      </ProtectedRoute>
    );
  }

  if (path === '/hr/shortlisted') {
    return (
      <ProtectedRoute allowedRoles={['hr']} notify={notify}>
        <HrShortlistedPage notify={notify} />
      </ProtectedRoute>
    );
  }

  if (path === '/hr/reports') {
    return (
      <ProtectedRoute allowedRoles={['hr']} notify={notify}>
        <HrReportsPage notify={notify} />
      </ProtectedRoute>
    );
  }

  if (path === '/agency/shortlisted') {
    return (
      <ProtectedRoute allowedRoles={['agency']} notify={notify}>
        <AgencyShortlistedPage notify={notify} />
      </ProtectedRoute>
    );
  }

  if (path === '/agency/reports') {
    return (
      <ProtectedRoute allowedRoles={['agency']} notify={notify}>
        <AgencyReportsPage notify={notify} />
      </ProtectedRoute>
    );
  }

  if (path.startsWith('/apply/')) {
    return <PublicApplicationPage notify={notify} />;
  }

  if (path === '/dashboard' || path.startsWith('/dashboard')) {
    return <DashboardRedirect notify={notify} />;
  }

  if (path === '/' || path === '') {
    return <Landing />;
  }

  return <NotFound />;
}

function App() {
  const [toast, setToast] = useState<{ message: string; tone: 'success' | 'info' | 'error' } | null>(null);
  const notify: Notify = useCallback((message, tone = 'success') => {
    setToast({ message, tone });
    window.setTimeout(() => setToast(null), 4000);
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, '')}>
          <Suspense fallback={<PageSuspenseFallback />}>
            <RoutedApp notify={notify} />
          </Suspense>
        </WouterRouter>
        <Toaster />
        {toast && (
          <div
            role="status"
            data-testid="toast-message"
            className={`fixed bottom-5 right-5 z-50 flex max-w-sm items-center gap-3 rounded-2xl px-4 py-3 text-sm font-semibold shadow-xl ${
              toast.tone === 'error'
                ? 'bg-[#f7e5e1] text-[#a33d35]'
                : toast.tone === 'info'
                ? 'bg-[#e4edf5] text-[#3a6384]'
                : 'bg-[#e2f0e9] text-[#277254]'
            }`}
          >
            <CheckCircle2 size={17} />
            {toast.message}
            <button onClick={() => setToast(null)} data-testid="button-close-toast" className="ml-2 opacity-60 hover:opacity-100">
              <X size={15} />
            </button>
          </div>
        )}
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
