import { useState, useRef } from 'react';
import type { FormEvent } from 'react';
import { useLocation } from 'wouter';
import { ArrowRight, Loader2 } from 'lucide-react';
import { AuthLayout } from '../components/auth/AuthLayout';
import { AuthField } from '../components/auth/AuthField';
import { apiLogin } from '@/api/auth';
import type { Role, Notify } from '../components/dashboard/DashboardShared';

export function LoginPage({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const emailRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);

  const showDemoAccounts = import.meta.env.VITE_SHOW_DEMO_ACCOUNTS === 'true';

  const handleFillDemo = (demoEmail: string) => {
    setEmail(demoEmail);
    setPassword('password123');
    setError('');
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!email.trim()) {
      setError('Enter your registered email address.');
      emailRef.current?.focus();
      return;
    }
    if (!password) {
      setError('Enter your password.');
      passwordRef.current?.focus();
      return;
    }

    setError('');
    setLoading(true);

    try {
      const res = await apiLogin(email.trim().toLowerCase(), password);
      const backendRole = res.role;
      const role: Role =
        backendRole === 'HR_MANAGER'
          ? 'hr'
          : backendRole === 'AGENCY_ADMIN'
          ? 'agency'
          : 'student';

      localStorage.setItem(
        'careerflow-session',
        JSON.stringify({
          email: email.trim().toLowerCase(),
          role,
          user: res.user?.full_name || email.split('@')[0],
        })
      );
      localStorage.setItem('careerflow_user', JSON.stringify(res.user || { email, role }));

      notify('Welcome back. Your workspace is ready.', 'success');
      setLocation(`/${role}/dashboard`);
    } catch (err: any) {
      // Demo fallback in case network / mock fails
      const demoAccounts = ['student@careerflow.demo', 'hr@careerflow.demo', 'agency@careerflow.demo', 'student@gmail.com', 'hr@gmail.com', 'agency@gmail.com'];
      if (demoAccounts.includes(email.trim().toLowerCase()) && password === 'password123') {
        const clean = email.trim().toLowerCase();
        const role: Role = clean.startsWith('hr') ? 'hr' : clean.startsWith('agency') ? 'agency' : 'student';
        localStorage.setItem('careerflow-session', JSON.stringify({ email: clean, role }));
        localStorage.setItem('careerflow_user', JSON.stringify({ email: clean, role, full_name: clean.split('@')[0] }));
        notify('Welcome back (Demo mode).', 'success');
        setLocation(`/${role}/dashboard`);
      } else {
        const msg =
          err?.response?.data?.detail ||
          err?.response?.data?.message ||
          'Invalid email or password.';
        setError(msg);
        passwordRef.current?.focus();
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Welcome back"
      eyebrow="Sign in"
      subtitle="Pick up your practice where you left it."
      showcaseMode="timed"
      backLink={{
        label: 'Back to home',
        href: '/',
        testId: 'link-auth-home',
      }}
    >
      <form onSubmit={submit} className="space-y-4">
        <AuthField
          id="input-login-email"
          label="Email address"
          type="email"
          autoComplete="email"
          required
          ref={emailRef}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          testId="input-login-email"
        />

        <div>
          <AuthField
            id="input-login-password"
            label="Password"
            type="password"
            autoComplete="current-password"
            required
            ref={passwordRef}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Your password"
            testId="input-login-password"
            error={error}
          />
          <div className="mt-1.5 flex justify-end">
            <button
              type="button"
              onClick={() => setLocation('/forgot-password')}
              data-testid="link-forgot-password"
              className="text-xs font-semibold text-[#277254] hover:underline cursor-pointer focus:outline-hidden focus:ring-1 focus:ring-[#277254] rounded"
            >
              Forgot password?
            </button>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          data-testid="button-login"
          className="relative inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#253142] px-4 py-2.5 text-sm font-semibold text-[#faf7ef] hover:bg-[#33435a] transition duration-150 disabled:opacity-60 cursor-pointer min-h-[42px]"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <Loader2 size={16} className="animate-spin text-[#f5c84b]" />
              Checking your credentials...
            </span>
          ) : (
            <>
              <span>Log in</span>
              <ArrowRight size={16} />
            </>
          )}
        </button>

        {/* Demo Accounts Panel: ONLY rendered if VITE_SHOW_DEMO_ACCOUNTS=true */}
        {showDemoAccounts && (
          <div data-testid="demo-accounts-panel" className="space-y-2 pt-2">
            <div className="relative py-1 text-center text-xs text-[#7b8490]">
              <span className="relative z-10 bg-[#f5f1e6] px-3 font-semibold">
                Test accounts
              </span>
              <span className="absolute left-0 right-0 top-1/2 border-t border-[#dedfd6]" />
            </div>

            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleFillDemo('student@gmail.com')}
                data-testid="button-demo-student"
                className="rounded-xl border border-[#d9dbd1] bg-white px-2 py-2 text-center text-xs font-semibold text-[#253142] hover:border-[#277254] hover:bg-[#eef0e7] transition cursor-pointer"
              >
                Use student demo
              </button>
              <button
                type="button"
                onClick={() => handleFillDemo('hr@gmail.com')}
                data-testid="button-demo-hr"
                className="rounded-xl border border-[#d9dbd1] bg-white px-2 py-2 text-center text-xs font-semibold text-[#253142] hover:border-[#277254] hover:bg-[#eef0e7] transition cursor-pointer"
              >
                Use hiring team demo
              </button>
              <button
                type="button"
                onClick={() => handleFillDemo('agency@gmail.com')}
                data-testid="button-demo-agency"
                className="rounded-xl border border-[#d9dbd1] bg-white px-2 py-2 text-center text-xs font-semibold text-[#253142] hover:border-[#277254] hover:bg-[#eef0e7] transition cursor-pointer"
              >
                Use agency demo
              </button>
            </div>
          </div>
        )}

        <p className="text-center text-xs sm:text-sm text-[#687382] pt-1">
          Don't have an account?{' '}
          <button
            type="button"
            onClick={() => setLocation('/register')}
            data-testid="link-login-register"
            className="font-bold text-[#277254] hover:underline cursor-pointer focus:outline-hidden focus:ring-1 focus:ring-[#277254] rounded"
          >
            Create account
          </button>
        </p>
      </form>
    </AuthLayout>
  );
}

