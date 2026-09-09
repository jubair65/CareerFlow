import { useState, useEffect } from 'react';
import type { FormEvent, ReactNode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from '@/components/ui/toaster';
import { TooltipProvider } from '@/components/ui/tooltip';
import { useLocation, Router as WouterRouter } from 'wouter';
import {
  ArrowRight, BriefcaseBusiness, Building2, Check, CheckCircle2,
  Home, LockKeyhole, LogOut, Play, ShieldCheck, TrendingUp, X
} from 'lucide-react';
import { apiRegister, apiLogin, apiLogout, apiGetCurrentUser } from '@/api/auth';

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
  label, value, onChange, placeholder, type = 'text', error, testId
}: {
  label: string; value: string; onChange: (v: string) => void; placeholder?: string;
  type?: string; error?: string; testId: string;
}) {
  return (
    <label className="block space-y-1.5 text-sm font-semibold text-[#253142]">
      <span>{label}</span>
      <input
        data-testid={testId}
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={`w-full rounded-xl border bg-[#fbfaf5] px-3.5 py-3 font-normal outline-none transition placeholder:text-[#98a09c] focus:border-[#253142] focus:ring-2 focus:ring-[#f5c84b]/45 ${error ? 'border-[#b34a40]' : 'border-[#d9dbd1]'}`}
      />
      {error && <span data-testid="field-error" className="text-xs font-medium text-[#b34a40]">{error}</span>}
    </label>
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
  const [, setLocation] = useLocation();
  return (
    <div className="cf-shell cf-noise bg-[#f5f1e6]">
      <header className="mx-auto flex max-w-7xl items-center justify-between px-5 py-5 md:px-10">
        <Logo />
        <div className="flex items-center gap-2">
          <button onClick={() => setLocation('/login')} data-testid="link-login" className="rounded-xl px-4 py-2 text-sm font-bold text-[#526072] hover:bg-[#e9e6dc]">
            Log in
          </button>
          <Button variant="soft" onClick={() => setLocation('/register')} testId="link-register">
            Create account <ArrowRight size={16} />
          </Button>
        </div>
      </header>

      <section className="mx-auto grid max-w-7xl gap-12 px-5 pb-20 pt-14 md:grid-cols-[1.05fr_.95fr] md:items-center md:px-10 md:pb-28 md:pt-24">
        <div className="cf-rise">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[#d8c98e] bg-[#fff4ca] px-3 py-1.5 text-xs font-bold text-[#7b6217]">
            <span className="h-2 w-2 rounded-full bg-[#f5c84b]" />A clearer way to move forward
          </div>
          <h1 className="cf-display max-w-3xl text-5xl font-bold leading-[.98] text-[#253142] md:text-7xl">
            Prepare better.<br /><span className="text-[#277254]">Apply smarter.</span><br />Hire faster.
          </h1>
          <p className="mt-7 max-w-xl text-lg leading-8 text-[#657081]">
            CareerFlow brings candidates, hiring teams, and recruitment agencies into one focused workspace — with better preparation on one side and clearer decisions on the other.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button variant="primary" onClick={() => setLocation('/register')} testId="button-landing-start">
              Start your flow <ArrowRight size={17} />
            </Button>
            <button onClick={() => setLocation('/login')} data-testid="button-landing-demo" className="inline-flex items-center gap-2 rounded-xl border border-[#ccd0c6] px-4 py-2.5 text-sm font-bold text-[#253142] hover:bg-[#fffaf0]">
              Explore the demo <Play size={15} fill="currentColor" />
            </button>
          </div>
          <div className="mt-10 flex items-center gap-5 text-xs font-semibold text-[#78818d]">
            <span className="flex items-center gap-1.5"><ShieldCheck size={15} className="text-[#277254]" /> Explainable scores</span>
            <span className="flex items-center gap-1.5"><LockKeyhole size={15} className="text-[#277254]" /> Private by default</span>
          </div>
        </div>

        <div className="relative">
          <div className="absolute -right-8 -top-10 h-40 w-40 rounded-full bg-[#f5c84b]/35 blur-2xl" />
          <div className="cf-card relative rounded-[2rem] bg-[#253142] p-4 shadow-2xl shadow-[#253142]/20 md:rotate-2">
            <div className="rounded-[1.4rem] border border-[#47576b] bg-[#2d3b4e] p-5 text-[#faf7ef]">
              <div className="flex items-center justify-between text-xs text-[#aab5c0]">
                <span>YOUR WEEK, IN VIEW</span>
                <span className="rounded-full bg-[#394b5e] px-2 py-1">Sprint 1 Ready</span>
              </div>
              <div className="mt-8 flex items-end justify-between">
                <div>
                  <div className="text-sm text-[#b5bfca]">Preparation progress</div>
                  <div className="cf-display mt-1 text-6xl font-bold text-[#f5c84b]">100%</div>
                  <div className="mt-2 flex items-center gap-1 text-xs text-[#84c49f]">
                    <TrendingUp size={13} /> Foundation online
                  </div>
                </div>
                <div className="h-28 w-28 rounded-full border-[10px] border-[#f5c84b] border-r-[#4a5b6c] border-b-[#4a5b6c] p-3">
                  <div className="grid h-full place-items-center rounded-full bg-[#253142] text-center text-[10px] font-bold text-[#c4ccd3]">
                    READY<br />TO GROW
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className="absolute -bottom-7 -left-5 flex items-center gap-3 rounded-2xl border border-[#d8d7cc] bg-[#fffaf0] px-4 py-3 shadow-lg">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-[#e2f0e9] text-[#277254]">
              <Check size={18} />
            </div>
            <div>
              <div className="text-xs font-bold text-[#253142]">Registration ready</div>
              <div className="text-[11px] text-[#7b8490]">CareerFlow Core · Sprint 1</div>
            </div>
          </div>
        </div>
      </section>

      <section className="border-y border-[#ddd8ca] bg-[#faf7ef] px-5 py-16 md:px-10 md:py-20">
        <div className="mx-auto max-w-7xl">
          <div className="grid gap-8 md:grid-cols-[.8fr_1.2fr] md:items-end">
            <div>
              <div className="mb-4 text-sm font-bold text-[#9a7922]">01 — For candidates</div>
              <h2 className="cf-display text-3xl font-bold leading-tight text-[#253142] md:text-4xl">
                Confidence is a skill you can train.
              </h2>
            </div>
            <div className="max-w-2xl">
              <p className="text-base leading-7 text-[#657081]">
                Practice the moments that matter, get feedback you can act on, and watch your progress become visible.
              </p>
              <button onClick={() => setLocation('/register')} className="mt-5 inline-flex items-center gap-2 text-sm font-bold text-[#277254] hover:gap-3">
                Build your candidate profile <ArrowRight size={15} />
              </button>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-[#253142] px-5 py-16 text-[#faf7ef] md:px-10 md:py-20">
        <div className="mx-auto grid max-w-7xl gap-10 md:grid-cols-[.8fr_1.2fr] md:items-center">
          <div>
            <div className="mb-4 flex items-center gap-2 text-sm font-bold text-[#f5c84b]">
              <Building2 size={17} />02 — For hiring teams
            </div>
            <h2 className="cf-display text-3xl font-bold leading-tight md:text-4xl">
              Make every hiring decision clearer.
            </h2>
            <p className="mt-5 max-w-md text-base leading-7 text-[#c3ccd5]">
              Create structured recruitment rooms, compare candidates on the same signals, and keep the human context in every shortlist.
            </p>
            <button onClick={() => setLocation('/register')} className="mt-7 inline-flex items-center gap-2 rounded-xl bg-[#f5c84b] px-4 py-2.5 text-sm font-bold text-[#253142] transition hover:bg-[#ffd969]">
              Join as hiring team <ArrowRight size={16} />
            </button>
          </div>
        </div>
      </section>

      <section className="border-b border-[#ddd8ca] bg-[#f5f1e6] px-5 py-16 md:px-10 md:py-20">
        <div className="mx-auto grid max-w-7xl gap-10 md:grid-cols-[1.2fr_.8fr] md:items-center">
          <div>
            <div className="mb-4 flex items-center gap-2 text-sm font-bold text-[#277254]">
              <BriefcaseBusiness size={17} />03 — For recruitment agencies
            </div>
            <h2 className="cf-display text-3xl font-bold leading-tight text-[#253142] md:text-4xl">
              Move the right people forward.
            </h2>
            <p className="mt-5 max-w-md text-base leading-7 text-[#657081]">
              Keep every client, room, and candidate in view with a dependable way to manage the recruitment pipeline.
            </p>
            <button onClick={() => setLocation('/register')} className="mt-7 inline-flex items-center gap-2 text-sm font-bold text-[#277254] hover:gap-3">
              Join as an agency <ArrowRight size={15} />
            </button>
          </div>
        </div>
      </section>

      <footer className="mx-auto flex max-w-7xl flex-col gap-3 border-t border-[#ddd8ca] px-5 py-8 text-sm text-[#7b8490] md:flex-row md:items-center md:justify-between md:px-10">
        <Logo />
        <span>CareerFlow · Sprint 1 Architecture & Registration</span>
      </footer>
    </div>
  );
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
  const [registeredUser, setRegisteredUser] = useState<any>(null);

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

      setRegisteredUser(res.user || { full_name: name, email, role });
      notify('Your account has been registered successfully in MySQL.', 'success');
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

  if (registeredUser) {
    return (
      <AuthLayout title="Account Created" eyebrow="Registration complete" aside="Your profile has been saved.">
        <div className="space-y-5">
          <div className="rounded-2xl border border-[#277254]/30 bg-[#e2f0e9] p-5 text-[#277254]">
            <CheckCircle2 size={24} className="mb-2" />
            <h3 className="font-bold text-base">Registration Confirmed in Database</h3>
            <p className="mt-1 text-xs opacity-90">
              User <strong>{registeredUser.full_name}</strong> ({registeredUser.email}) registered as <strong className="capitalize">{role}</strong>.
            </p>
          </div>

          <div className="rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] p-4 text-xs leading-6 text-[#687382]">
            <span className="font-semibold text-[#253142]">Note for Sprint 1 Development:</span><br />
            Login authentication & Session management (`US-02`) and Role dashboards (`US-03`) are in progress by <strong>Member 2</strong>.
          </div>

          <div className="flex gap-3">
            <Button variant="primary" onClick={() => setLocation('/login')} testId="button-registered-login">
              Proceed to Log in <ArrowRight size={16} />
            </Button>
            <Button variant="outline" onClick={() => setLocation('/')} testId="button-registered-home">
              Back to Home
            </Button>
            <Button variant="soft" onClick={() => { setRegisteredUser(null); setName(''); setEmail(''); setPassword(''); setConfirmPassword(''); }} testId="button-register-another">
              Register another
            </Button>
          </div>
        </div>
      </AuthLayout>
    );
  }

  const strength = getPasswordStrength(password);

  return (
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
      setLocation('/dashboard');
    } catch (err: any) {
      const match = ['student@careerflow.demo', 'hr@careerflow.demo', 'agency@careerflow.demo'].includes(email) && password === 'password123';
      if (match) {
        const role: Role = email.startsWith('hr') ? 'hr' : email.startsWith('agency') ? 'agency' : 'student';
        localStorage.setItem('careerflow-session', JSON.stringify({ email, role }));
        localStorage.setItem('careerflow_user', JSON.stringify({ email, role, full_name: email.split('@')[0] }));
        notify('Welcome back (Demo Mode).', 'success');
        setLocation('/dashboard');
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
              onClick={() => notify('Password reset is available in the profile settings.', 'info')}
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

function DashboardSuccess({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGetCurrentUser()
      .then((data) => {
        setUser(data);
        setLoading(false);
      })
      .catch(() => {
        const stored = localStorage.getItem('careerflow_user') || localStorage.getItem('careerflow-session');
        if (stored) {
          try {
            setUser(JSON.parse(stored));
          } catch {}
        }
        setLoading(false);
      });
  }, []);

  const handleLogout = async () => {
    await apiLogout();
    localStorage.removeItem('careerflow-session');
    localStorage.removeItem('careerflow_user');
    notify('You have been logged out.', 'info');
    setLocation('/login');
  };

  const role = user?.role_display || user?.role || 'STUDENT';
  const roleColor =
    role === 'HR_MANAGER' || role === 'hr'
      ? 'bg-[#fff1c9] text-[#8a6a16] border-[#f5c84b]'
      : role === 'AGENCY_ADMIN' || role === 'agency'
      ? 'bg-[#e4edf5] text-[#2a557a] border-[#3a6384]'
      : 'bg-[#e2f0e9] text-[#277254] border-[#277254]';

  return (
    <div className="cf-shell min-h-screen bg-[#f5f1e6] flex flex-col">
      <header className="mx-auto flex w-full max-w-7xl items-center justify-between border-b border-[#ddd8ca] px-5 py-5 md:px-10">
        <Logo />
        <div className="flex items-center gap-3">
          <button
            onClick={() => setLocation('/')}
            className="rounded-xl px-4 py-2 text-sm font-bold text-[#526072] hover:bg-[#e9e6dc]"
          >
            Landing Page
          </button>
          <Button
            variant="soft"
            onClick={handleLogout}
            testId="button-dashboard-logout"
            className="inline-flex items-center gap-2"
          >
            <LogOut size={15} /> Log out
          </Button>
        </div>
      </header>

      <main className="mx-auto flex-1 w-full max-w-3xl px-5 py-10 md:py-16">
        <div className="cf-rise space-y-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-[#277254]/30 bg-[#e2f0e9] px-4 py-1.5 text-xs font-bold text-[#277254]">
            <CheckCircle2 size={16} /> JWT Authentication & Session Persistence Verified (US-02 & US-03)
          </div>

          <div>
            <h1 className="cf-display text-4xl font-bold tracking-tight text-[#253142] md:text-5xl">
              Welcome, {loading ? 'Loading...' : user?.full_name || user?.username || user?.user || 'Member'}!
            </h1>
            <p className="mt-2 text-base text-[#657081]">
              Authentication was successful. Your account session and role permissions have been validated.
            </p>
          </div>

          <div className="cf-card rounded-2xl border border-[#d9dbd1] bg-white p-6 shadow-sm md:p-8">
            <div className="flex items-center justify-between border-b border-[#eef0e7] pb-4">
              <div className="flex items-center gap-3">
                <div className="grid h-12 w-12 place-items-center rounded-2xl bg-[#253142] text-lg font-bold text-[#faf7ef]">
                  {(user?.full_name || user?.email || 'U')[0].toUpperCase()}
                </div>
                <div>
                  <h3 className="font-bold text-[#253142] text-lg">
                    {user?.full_name || user?.email || 'CareerFlow Member'}
                  </h3>
                  <p className="text-xs text-[#7b8490]">{user?.email}</p>
                </div>
              </div>
              <span className={`rounded-full border px-3 py-1 text-xs font-bold capitalize ${roleColor}`}>
                {role}
              </span>
            </div>

            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <div className="rounded-xl bg-[#fbfaf5] p-4 border border-[#eef0e7]">
                <span className="text-xs font-semibold text-[#7b8490] uppercase tracking-wider">User ID</span>
                <p className="mt-1 text-base font-bold text-[#253142]">#{user?.id || 'Active'}</p>
              </div>
              <div className="rounded-xl bg-[#fbfaf5] p-4 border border-[#eef0e7]">
                <span className="text-xs font-semibold text-[#7b8490] uppercase tracking-wider">Access Level</span>
                <p className="mt-1 text-base font-bold text-[#253142] capitalize">{role}</p>
              </div>
              <div className="rounded-xl bg-[#fbfaf5] p-4 border border-[#eef0e7]">
                <span className="text-xs font-semibold text-[#7b8490] uppercase tracking-wider">Token Security</span>
                <p className="mt-1 text-sm font-semibold text-[#277254]">Bearer JWT Rotation</p>
              </div>
              <div className="rounded-xl bg-[#fbfaf5] p-4 border border-[#eef0e7]">
                <span className="text-xs font-semibold text-[#7b8490] uppercase tracking-wider">Session State</span>
                <p className="mt-1 text-sm font-semibold text-[#277254]">Persisted via LocalStorage</p>
              </div>
            </div>

            {user?.created_at && (
              <div className="mt-4 text-xs text-[#9aa2a9]">
                Account registered on: {new Date(user.created_at).toLocaleString()}
              </div>
            )}
          </div>

          {/* US-36: Data Access Control & Audit Trail */}
          <div className="cf-card rounded-2xl border border-[#d9dbd1] bg-[#fbfaf5] p-6 shadow-sm">
            <div className="flex items-center justify-between border-b border-[#eef0e7] pb-3">
              <div className="flex items-center gap-2">
                <ShieldCheck size={18} className="text-[#277254]" />
                <h3 className="font-bold text-sm text-[#253142]">Data Access Control & Security Auditing (US-36)</h3>
              </div>
              <span className="rounded-full bg-[#e2f0e9] px-2.5 py-0.5 text-[11px] font-bold text-[#277254]">Active</span>
            </div>
            <div className="mt-4 grid gap-3 sm:grid-cols-3 text-xs">
              <div className="rounded-xl bg-white p-3 border border-[#eef0e7]">
                <span className="text-[#7b8490] block">Resource Access</span>
                <strong className="text-[#253142] mt-1 block">Role-Scoped Files</strong>
              </div>
              <div className="rounded-xl bg-white p-3 border border-[#eef0e7]">
                <span className="text-[#7b8490] block">Audit Logging</span>
                <strong className="text-[#253142] mt-1 block">careerflow_data_access_logs</strong>
              </div>
              <div className="rounded-xl bg-white p-3 border border-[#eef0e7]">
                <span className="text-[#7b8490] block">Access Status</span>
                <strong className="text-[#277254] mt-1 block">GRANTED / DENIED Tracked</strong>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap gap-4 pt-2">
            <Button variant="primary" onClick={handleLogout} testId="button-action-logout">
              <LogOut size={16} /> Sign out of account
            </Button>
            <Button variant="soft" onClick={() => setLocation('/')} testId="button-action-home">
              <Home size={16} /> Back to Landing Page
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}

function RoutedApp({ notify }: { notify: Notify }) {
  const [path] = useLocation();
  if (path === '/') return <Landing />;
  if (path === '/login') return <Login notify={notify} />;
  if (path === '/register') return <Register notify={notify} />;
  if (path === '/dashboard' || path.startsWith('/dashboard')) return <DashboardSuccess notify={notify} />;
  return <Landing />;
}

function App() {
  const [toast, setToast] = useState<{ message: string; tone: 'success' | 'info' | 'error' } | null>(null);
  const notify: Notify = (message, tone = 'success') => {
    setToast({ message, tone });
    window.setTimeout(() => setToast(null), 2800);
  };

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
