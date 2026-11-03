import { useState, useEffect, useCallback } from 'react';
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
import { StudentDashboard } from './pages/StudentDashboard';
import { HrDashboard } from './pages/HrDashboard';
import { AgencyDashboard } from './pages/AgencyDashboard';
import { CvStudio } from './pages/CvStudio';
import { CvResults } from './pages/CvResults';
import { CvProcessingPage } from './components/cv/CvProcessingView';
import { JobMatch } from './pages/JobMatch';
import { PresentationStudio } from './pages/PresentationStudio';
import { VideoHistory } from './pages/VideoHistory';
import { PresentationDetailReportPage } from './pages/PresentationDetailReportPage';
import { ScoreTrendsPage } from './pages/ScoreTrendsPage';
import { RecruitmentRoomsPage } from './pages/RecruitmentRoomsPage';
import { PublicApplicationPage } from './pages/PublicApplicationPage';
import { ForgotPasswordPage } from './pages/ForgotPasswordPage';
import { ResetPasswordPage } from './pages/ResetPasswordPage';
import { AgencyClientManagementPage } from './pages/AgencyClientManagementPage';
import { AgencyRoomsPage } from './pages/AgencyRoomsPage';
import { AgencyApplicantsPipelinePage } from './pages/AgencyApplicantsPipelinePage';
import { NotificationsPage } from './pages/NotificationsPage';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { ApplicantStatusPage } from './pages/ApplicantStatusPage';
import { JobBoardPage } from './pages/JobBoardPage';
import { ProfilePage } from './pages/ProfilePage';
import { SettingsPage } from './pages/SettingsPage';
import { HrApplicantsPage } from './pages/HrApplicantsPage';
import { HrShortlistedPage } from './pages/HrShortlistedPage';
import { HrReportsPage } from './pages/HrReportsPage';
import { AgencyShortlistedPage } from './pages/AgencyShortlistedPage';
import { AgencyReportsPage } from './pages/AgencyReportsPage';


const queryClient = new QueryClient();

type Role = 'student' | 'hr' | 'agency';
type Notify = (message: string, tone?: 'success' | 'info' | 'error') => void;

function Logo({ dark = false }: { dark?: boolean }) {
  return (
    <div className="flex items-center gap-2.5" data-testid="brand-careerflow">
      <div className={`grid h-9 w-9 place-items-center rounded-xl ${dark ? 'bg-[#f5c84b] text-[#253142]' : 'bg-[#253142] text-[#f5c84b]'}`}>
        <svg viewBox="0 0 24 24" className="h-[21px] w-[21px]" fill="none" aria-hidden="true">
          <path d="M4 6.5h5.25c1.52 0 2.75 1.23 2.75 2.75v5.5c0 1.52 1.23 2.75 2.75 2.75H20" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
          <path d="m17.2 14.75 2.8 2.75-2.8 2.75" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
          <circle cx="4" cy="6.5" r="1.55" fill="currentColor" />
          <circle cx="12" cy="9.25" r="1.55" fill="currentColor" />
        </svg>
      </div>
      <span className={`cf-display text-lg font-bold ${dark ? 'text-[#f8f4e9]' : 'text-[#253142]'}`}>CareerFlow</span>
    </div>
  );
}

function Button({
  children, onClick, variant = 'primary', className = '', disabled = false, type = 'button', testId
}: {
  children: ReactNode; onClick?: () => void; variant?: 'primary'|'soft'|'ghost'|'danger'|'outline';
  className?: string; disabled?: boolean; type?: 'button'|'submit'; testId?: string;
}) {
  const variants = {
    primary: 'bg-[#253142] text-[#faf7ef] hover:bg-[#33435a]',
    soft: 'bg-[#f5c84b] text-[#253142] hover:bg-[#e8b93c]',
    ghost: 'text-[#526072] hover:bg-[#eef0e7]',
    danger: 'bg-[#f7e5e1] text-[#a33d35] hover:bg-[#f1d6d1]',
    outline: 'border border-[#d7d9cf] bg-transparent text-[#253142] hover:border-[#253142]'
  };
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      data-testid={testId}
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition duration-200 disabled:cursor-not-allowed disabled:opacity-50 ${variants[variant]} ${className}`}
    >
      {children}
    </button>
  );
}

function Field({
  label, value, onChange, placeholder, type = 'text', error, testId, toggleTestId
}: {
  label: string; value: string; onChange: (v: string) => void; placeholder?: string;
  type?: string; error?: string; testId: string; toggleTestId?: string;
}) {
  const [showPassword, setShowPassword] = useState(false);
  const isPassword = type === 'password';
  const effectiveType = isPassword ? (showPassword ? 'text' : 'password') : type;

  const resolvedToggleTestId =
    toggleTestId ||
    (testId === 'input-login-password'
      ? 'button-toggle-password'
      : testId === 'input-register-password'
      ? 'button-toggle-password'
      : testId === 'input-register-confirm-password'
      ? 'button-toggle-confirm-password'
      : `button-toggle-${testId}`);

  return (
    <div className="block space-y-1.5 text-sm font-semibold text-[#253142]">
      <label htmlFor={testId} className="block cursor-pointer">
        {label}
      </label>
      <div className="relative">
        <input
          id={testId}
          data-testid={testId}
          type={effectiveType}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={`w-full rounded-xl border bg-[#fbfaf5] ${
            isPassword ? 'pl-3.5 pr-11' : 'px-3.5'
          } py-3 font-normal outline-none transition placeholder:text-[#98a09c] focus:border-[#253142] focus:ring-2 focus:ring-[#f5c84b]/45 ${
            error ? 'border-[#b34a40]' : 'border-[#d9dbd1]'
          }`}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setShowPassword((prev) => !prev)}
            data-testid={resolvedToggleTestId}
            data-toggle-target={testId}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
            title={showPassword ? 'Hide password' : 'Show password'}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 flex items-center justify-center h-8 w-8 rounded-lg text-[#7b8490] hover:text-[#253142] hover:bg-[#eef0e7] transition focus:outline-none"
          >
            {showPassword ? (
              <EyeOff size={18} className="shrink-0" />
            ) : (
              <Eye size={18} className="shrink-0" />
            )}
          </button>
        )}
      </div>
      {error && <span data-testid="field-error" className="text-xs font-medium text-[#b34a40]">{error}</span>}
    </div>
  );
}

function AuthLayout({ title, eyebrow, children, aside }: { title: string; eyebrow: string; children: ReactNode; aside: string }) {
  const [, setLocation] = useLocation();
  return (
    <div className="cf-shell grid bg-[#f5f1e6] md:grid-cols-[.85fr_1.15fr]">
      <div className="hidden bg-[#253142] p-10 text-[#faf7ef] md:flex md:flex-col md:justify-between">
        <Logo dark />
        <div className="max-w-md pb-14">
          <div className="mb-5 text-xs font-bold uppercase tracking-[.18em] text-[#f5c84b]">{eyebrow}</div>
          <h2 className="cf-display text-5xl font-bold leading-[1.02]">{aside}</h2>
          <div className="mt-8 flex gap-2">
            {[1, 2, 3].map((n) => (
              <span key={n} className={`h-1.5 rounded-full ${n === 1 ? 'w-10 bg-[#f5c84b]' : 'w-5 bg-[#607084]'}`} />
            ))}
          </div>
        </div>
        <div className="text-xs text-[#9daaba]">A focused workspace for the next chapter.</div>
      </div>
      <div className="flex min-h-[100dvh] flex-col px-5 py-6 md:px-16 md:py-10">
        <div className="flex items-center justify-between md:justify-end">
          <div className="md:hidden"><Logo /></div>
          <button onClick={() => setLocation('/')} data-testid="link-auth-home" className="text-sm font-bold text-[#526072] hover:text-[#253142]">
            Back to home
          </button>
        </div>
        <div className="mx-auto my-auto w-full max-w-[450px] py-12">
          <div className="mb-8">
            <div className="mb-3 text-[11px] font-bold uppercase tracking-[.18em] text-[#9a7922]">{eyebrow}</div>
            <h1 className="cf-display text-4xl font-bold text-[#253142]">{title}</h1>
          </div>
          {children}
        </div>
      </div>
    </div>
  );
}

function Landing() {
  return <LandingPage />;
}

function getPasswordStrength(pass: string) {
  let score = 0;
  if (!pass) return { score: 0, label: 'Too short', color: 'bg-[#d9dbd1]' };
  if (pass.length >= 8) score += 1;
  if (/[A-Z]/.test(pass)) score += 1;
  if (/[0-9]/.test(pass)) score += 1;
  if (/[^A-Za-z0-9]/.test(pass)) score += 1;
  if (score <= 1) return { score: 1, label: 'Weak', color: 'bg-[#e26d5c]' };
  if (score === 2) return { score: 2, label: 'Fair', color: 'bg-[#f5c84b]' };
  if (score === 3) return { score: 3, label: 'Good', color: 'bg-[#3a6384]' };
  return { score: 4, label: 'Strong', color: 'bg-[#277254]' };
}

function Register({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState<Role>('student');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [redirecting, setRedirecting] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!name || !email.includes('@')) {
      setError('Add your name and a valid email to continue.');
      return;
    }
    if (password.length < 8) {
      setError('Your password should be at least 8 characters.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Your passwords do not match.');
      return;
    }

    setError('');
    setLoading(true);
    try {
      const backendRole = role === 'hr' ? 'HR_MANAGER' : role === 'agency' ? 'AGENCY_ADMIN' : 'STUDENT';
      const res = await apiRegister({
        email,
        password,
        confirm_password: confirmPassword,
        full_name: name,
        role: backendRole,
      });

      // Auto-login fallback if tokens were not stored directly
      if (!res?.tokens) {
        try {
          await apiLogin(email, password);
        } catch {
          // demo fallback handles localStorage
        }
      }

      // Establish session
      const targetRole: Role = role;
      localStorage.setItem(
        'careerflow-session',
        JSON.stringify({
          email,
          role: targetRole,
          user: res?.user?.full_name || name || email.split('@')[0],
        })
      );
      if (res?.user) {
        localStorage.setItem('careerflow_user', JSON.stringify(res.user));
      } else {
        localStorage.setItem('careerflow_user', JSON.stringify({ email, role: backendRole, full_name: name }));
      }

      setRedirecting(true);
      notify('Registration is complete! Moving to dashboard...', 'success');

      setTimeout(() => {
        setLocation(`/${targetRole}/dashboard`);
      }, 1200);
    } catch (err: any) {
      const errDetail =
        err?.response?.data?.message ||
        (err?.response?.data?.errors && Object.values(err.response.data.errors).flat().join(' ')) ||
        'Registration could not be completed.';
      setError(errDetail);
    } finally {
      setLoading(false);
    }
  };

  const strength = getPasswordStrength(password);

  return (
    <>
      {redirecting && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-sm rounded-2xl bg-[#faf7ef] p-6 shadow-2xl border border-[#d9dbd1] text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-[#e2f0e9] text-[#277254] mb-3">
              <CheckCircle2 size={32} />
            </div>
            <h3 className="text-lg font-bold text-[#253142]">Registration Complete!</h3>
            <p className="mt-1 text-xs text-[#526072]">
              Registration is complete, moving to dashboard...
            </p>
            <div className="mt-4 flex items-center justify-center gap-2 rounded-xl bg-[#eef0e7] px-3 py-2 text-xs font-semibold text-[#277254]">
              <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-[#277254] border-t-transparent" />
              <span>Moving to dashboard...</span>
            </div>
            <button
              type="button"
              onClick={() => setLocation(`/${role}/dashboard`)}
              className="mt-3 text-xs font-semibold text-[#277254] hover:underline"
            >
              Go to dashboard now →
            </button>
          </div>
        </div>
      )}

      <AuthLayout title="Make the next move" eyebrow="Create account" aside="Your best work deserves a clearer runway.">
        <form onSubmit={submit} className="space-y-5">
          <Field label="Full name" value={name} onChange={setName} placeholder="Alex Rahman" testId="input-register-name" />
          <Field label="Email address" value={email} onChange={setEmail} placeholder="you@example.com" type="email" testId="input-register-email" />
          <div>
            <Field
              label="Password"
              value={password}
              onChange={setPassword}
              placeholder="At least 8 characters"
              type="password"
              testId="input-register-password"
            />
            {password && (
              <div className="mt-2 space-y-1.5" data-testid="password-strength-meter">
                <div className="flex items-center justify-between text-xs font-semibold">
                  <span className="text-[#657081]">Password strength:</span>
                  <span className={`font-bold ${strength.score >= 3 ? 'text-[#277254]' : strength.score === 2 ? 'text-[#9a7922]' : 'text-[#b34a40]'}`}>
                    {strength.label}
                  </span>
                </div>
                <div className="grid grid-cols-4 gap-1.5 h-1.5">
                  {[1, 2, 3, 4].map((step) => (
                    <div
                      key={step}
                      className={`rounded-full transition duration-300 ${
                        strength.score >= step ? strength.color : 'bg-[#e2e3db]'
                      }`}
                    />
                  ))}
                </div>
                <div className="flex flex-wrap gap-x-3 gap-y-1 pt-1 text-[11px] text-[#7b8490]">
                  <span className={password.length >= 8 ? 'text-[#277254] font-semibold' : ''}>✓ 8+ chars</span>
                  <span className={/[A-Z]/.test(password) ? 'text-[#277254] font-semibold' : ''}>✓ Uppercase</span>
                  <span className={/[0-9]/.test(password) ? 'text-[#277254] font-semibold' : ''}>✓ Number</span>
                  <span className={/[^A-Za-z0-9]/.test(password) ? 'text-[#277254] font-semibold' : ''}>✓ Symbol</span>
                </div>
              </div>
            )}
          </div>
          <Field label="Confirm password" value={confirmPassword} onChange={setConfirmPassword} placeholder="Re-enter your password" type="password" testId="input-register-confirm-password" />
          <div>
            <div className="mb-2 text-sm font-semibold text-[#253142]">I am joining as</div>
            <div className="grid grid-cols-3 gap-2">
              {(['student', 'hr', 'agency'] as Role[]).map((item) => (
                <button
                  type="button"
                  key={item}
                  onClick={() => setRole(item)}
                  data-testid={`button-role-${item}`}
                  className={`rounded-xl border px-2 py-3 text-xs font-bold capitalize transition ${role === item ? 'border-[#253142] bg-[#253142] text-[#faf7ef]' : 'border-[#d9dbd1] bg-[#fbfaf5] text-[#687382] hover:border-[#9aabb5]'}`}
                >
                  {item === 'hr' ? 'Hiring team' : item === 'agency' ? 'Agency' : 'Candidate'}
                </button>
              ))}
            </div>
          </div>
          {error && <div data-testid="register-error" className="rounded-xl bg-[#f7e5e1] p-3 text-xs font-semibold text-[#a33d35]">{error}</div>}
          <Button type="submit" disabled={loading} className="w-full" testId="button-register">
            {loading ? 'Creating account…' : 'Create workspace'} {!loading && <ArrowRight size={16} />}
          </Button>
          <p className="text-center text-sm text-[#687382]">
            Already have an account?{' '}
            <button type="button" onClick={() => setLocation('/login')} data-testid="link-register-login" className="font-bold text-[#277254]">
              Log in
            </button>
          </p>
        </form>
      </AuthLayout>
    </>
  );
}

function Login({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();
  const [email, setEmail] = useState('student@careerflow.demo');
  const [password, setPassword] = useState('password123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await apiLogin(email, password);
      const backendRole = res.role;
      const role: Role = backendRole === 'HR_MANAGER' ? 'hr' : backendRole === 'AGENCY_ADMIN' ? 'agency' : 'student';

      localStorage.setItem(
        'careerflow-session',
        JSON.stringify({
          email,
          role,
          user: res.user?.full_name || email.split('@')[0],
        })
      );
      localStorage.setItem('careerflow_user', JSON.stringify(res.user || { email, role }));

      notify('Welcome back. Your workspace is ready.', 'success');
      setLocation(`/${role}/dashboard`);
    } catch (err: any) {
      const match = ['student@careerflow.demo', 'hr@careerflow.demo', 'agency@careerflow.demo'].includes(email) && password === 'password123';
      if (match) {
        const role: Role = email.startsWith('hr') ? 'hr' : email.startsWith('agency') ? 'agency' : 'student';
        localStorage.setItem('careerflow-session', JSON.stringify({ email, role }));
        localStorage.setItem('careerflow_user', JSON.stringify({ email, role, full_name: email.split('@')[0] }));
        notify('Welcome back (Demo Mode).', 'success');
        setLocation(`/${role}/dashboard`);
      } else {
        const msg = err?.response?.data?.detail || err?.response?.data?.message || 'Invalid email or password.';
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Welcome back" eyebrow="Sign in" aside="A little more ready than yesterday.">
      <form onSubmit={submit} className="space-y-5">
        <Field label="Email address" value={email} onChange={setEmail} type="email" placeholder="you@example.com" testId="input-login-email" />
        <div>
          <Field label="Password" value={password} onChange={setPassword} type="password" placeholder="Your password" testId="input-login-password" error={error} />
          <div className="mt-1.5 flex justify-end">
            <button
              type="button"
              onClick={() => setLocation('/forgot-password')}
              data-testid="link-forgot-password"
              className="text-xs font-bold text-[#277254] hover:underline"
            >
              Forgot password?
            </button>
          </div>
        </div>

        <Button type="submit" disabled={loading} className="w-full" testId="button-login">
          {loading ? 'Checking your credentials…' : 'Log in'} {!loading && <ArrowRight size={16} />}
        </Button>

        <div className="relative py-2 text-center text-xs text-[#8a929c]">
          <span className="relative z-10 bg-[#f5f1e6] px-3 font-semibold">Test accounts</span>
          <span className="absolute left-0 right-0 top-1/2 border-t border-[#dedfd6]" />
        </div>

        <div className="rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] p-3 text-xs leading-6 text-[#687382]">
          <strong className="text-[#253142]">Try any role:</strong> student@careerflow.demo · hr@careerflow.demo · agency@careerflow.demo
          <br />
          <span className="font-semibold text-[#253142]">Password:</span> password123 (or use any account registered in the app)
        </div>

        <p className="text-center text-sm text-[#687382]">
          New here?{' '}
          <button type="button" onClick={() => setLocation('/register')} data-testid="link-login-register" className="font-bold text-[#277254]">
            Create an account
          </button>
        </p>
      </form>
    </AuthLayout>
  );
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
  if (path === '/login') return <Login notify={notify} />;
  if (path === '/register') return <Register notify={notify} />;
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

  return <Landing />;
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
          <RoutedApp notify={notify} />
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
