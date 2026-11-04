import { useState, useRef } from 'react';
import type { FormEvent, KeyboardEvent } from 'react';
import { useLocation } from 'wouter';
import { ArrowRight, Check, CheckCircle2, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { AuthLayout } from '../components/auth/AuthLayout';
import { AuthField } from '../components/auth/AuthField';
import { apiRegister, apiLogin } from '@/api/auth';
import type { Role, Notify } from '../components/dashboard/DashboardShared';

function CheckTick({ active }: { active: boolean }) {
  return (
    <span
      className={`inline-flex items-center justify-center h-3.5 w-3.5 rounded-full transition-colors ${
        active ? 'bg-[#e2f0e9] text-[#277254]' : 'bg-[#eef0e7] text-[#9ca9b8]'
      }`}
    >
      <svg
        className="h-2.5 w-2.5"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="3.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <motion.path
          d="M20 6L9 17l-5-5"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: active ? 1 : 0 }}
          transition={{ duration: 0.15, ease: [0.22, 1, 0.36, 1] }}
        />
      </svg>
    </span>
  );
}

const ROLES: { id: Role; label: string; desc: string }[] = [
  { id: 'student', label: 'Candidate', desc: 'Practice, get CV feedback and apply to jobs.' },
  { id: 'hr', label: 'Hiring team', desc: 'Create rooms, rank applicants and keep notes.' },
  { id: 'agency', label: 'Agency', desc: 'Manage clients, rooms and candidates in one pipeline.' },
];

export function RegisterPage({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState<Role>('student');

  const [nameError, setNameError] = useState('');
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [confirmPasswordError, setConfirmPasswordError] = useState('');
  const [generalError, setGeneralError] = useState('');

  const [loading, setLoading] = useState(false);
  const [redirecting, setRedirecting] = useState(false);

  const nameInputRef = useRef<HTMLInputElement>(null);
  const emailInputRef = useRef<HTMLInputElement>(null);
  const passwordInputRef = useRef<HTMLInputElement>(null);
  const confirmPasswordInputRef = useRef<HTMLInputElement>(null);
  const roleButtonsRef = useRef<(HTMLButtonElement | null)[]>([]);

  // Password rules validation
  const hasMinLength = password.length >= 8;
  const hasNumber = /[0-9]/.test(password);
  const hasLetter = /[a-zA-Z]/.test(password);
  const isPasswordValid = hasMinLength && hasNumber && hasLetter;

  // Confirm password match
  const hasConfirmText = confirmPassword.length > 0;
  const passwordsMatch = hasConfirmText && password === confirmPassword;

  const handleRoleKeyDown = (e: KeyboardEvent<HTMLButtonElement>, currentIndex: number) => {
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      e.preventDefault();
      const nextIndex = (currentIndex + 1) % ROLES.length;
      setRole(ROLES[nextIndex].id);
      roleButtonsRef.current[nextIndex]?.focus();
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      e.preventDefault();
      const prevIndex = (currentIndex - 1 + ROLES.length) % ROLES.length;
      setRole(ROLES[prevIndex].id);
      roleButtonsRef.current[prevIndex]?.focus();
    }
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setNameError('');
    setEmailError('');
    setPasswordError('');
    setConfirmPasswordError('');
    setGeneralError('');

    if (!name.trim()) {
      setNameError('Enter your full name.');
      nameInputRef.current?.focus();
      return;
    }

    if (!email.trim() || !email.includes('@')) {
      setEmailError('Enter a valid email address.');
      emailInputRef.current?.focus();
      return;
    }

    if (!isPasswordValid) {
      setPasswordError('Please meet all password requirements.');
      passwordInputRef.current?.focus();
      return;
    }

    if (password !== confirmPassword) {
      setConfirmPasswordError('Passwords do not match.');
      confirmPasswordInputRef.current?.focus();
      return;
    }

    setLoading(true);
    try {
      const backendRole =
        role === 'hr' ? 'HR_MANAGER' : role === 'agency' ? 'AGENCY_ADMIN' : 'STUDENT';

      const res = await apiRegister({
        email: email.trim().toLowerCase(),
        password,
        confirm_password: confirmPassword,
        full_name: name.trim(),
        role: backendRole,
      });

      if (!res?.tokens) {
        try {
          await apiLogin(email.trim().toLowerCase(), password);
        } catch {}
      }

      const targetRole: Role = role;
      localStorage.setItem(
        'careerflow-session',
        JSON.stringify({
          email: email.trim().toLowerCase(),
          role: targetRole,
          user: res?.user?.full_name || name.trim() || email.split('@')[0],
        })
      );

      if (res?.user) {
        localStorage.setItem('careerflow_user', JSON.stringify(res.user));
      } else {
        localStorage.setItem(
          'careerflow_user',
          JSON.stringify({ email: email.trim().toLowerCase(), role: backendRole, full_name: name.trim() })
        );
      }

      setRedirecting(true);
      notify('Registration complete! Moving to your workspace...', 'success');

      setTimeout(() => {
        setLocation(`/${targetRole}/dashboard`);
      }, 1000);
    } catch (err: any) {
      const errDetail =
        err?.response?.data?.message ||
        (err?.response?.data?.errors &&
          Object.values(err.response.data.errors).flat().join(' ')) ||
        'Registration could not be completed. Please try again.';
      setGeneralError(errDetail);
    } finally {
      setLoading(false);
    }
  };

  const selectedRoleDesc = ROLES.find((r) => r.id === role)?.desc || '';

  return (
    <>
      {redirecting && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 animate-in fade-in duration-150">
          <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-2xl border border-[#d9dbd1] text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[#e2f0e9] text-[#277254] mb-3">
              <CheckCircle2 size={28} />
            </div>
            <h3 className="text-base font-bold text-[#253142]">Registration complete</h3>
            <p className="mt-1 text-xs text-[#687382]">
              Moving to your workspace dashboard...
            </p>
            <div className="mt-4 flex items-center justify-center gap-2 rounded-xl bg-[#eef0e7] px-3 py-2 text-xs font-semibold text-[#277254]">
              <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-[#277254] border-t-transparent" />
              <span>Entering workspace...</span>
            </div>
          </div>
        </div>
      )}

      <AuthLayout
        title="Make the next move"
        eyebrow="Create account"
        subtitle="Set up your workspace to practice, evaluate, or recruit."
        showcaseMode="role"
        showcaseRole={role}
        backLink={{
          label: 'Back to home',
          href: '/',
          testId: 'link-auth-home',
        }}
      >
        <form onSubmit={submit} className="space-y-3.5" noValidate>
          {/* Full Name */}
          <AuthField
            id="input-register-name"
            label="Full name"
            type="text"
            autoComplete="name"
            required
            ref={nameInputRef}
            value={name}
            onChange={(e) => {
              setName(e.target.value);
              if (nameError) setNameError('');
            }}
            placeholder="Alex Rahman"
            testId="input-register-name"
            error={nameError}
          />

          {/* Email Address */}
          <AuthField
            id="input-register-email"
            label="Email address"
            type="email"
            autoComplete="email"
            required
            ref={emailInputRef}
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              if (emailError) setEmailError('');
            }}
            placeholder="you@example.com"
            testId="input-register-email"
            error={emailError}
          />

          {/* Password with persistent helper text & live checklist */}
          <div>
            <AuthField
              id="input-register-password"
              label="Password"
              type="password"
              autoComplete="new-password"
              required
              ref={passwordInputRef}
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                if (passwordError) setPasswordError('');
              }}
              placeholder="At least 8 characters"
              testId="input-register-password"
              error={passwordError}
            />

            {/* Persistent live checklist under field */}
            <div
              data-testid="password-checklist"
              className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-[#657081]"
            >
              <div className="flex items-center gap-1.5">
                <CheckTick active={hasMinLength} />
                <span className={hasMinLength ? 'text-[#277254] font-semibold' : ''}>
                  8+ characters
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckTick active={hasNumber} />
                <span className={hasNumber ? 'text-[#277254] font-semibold' : ''}>
                  One number
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckTick active={hasLetter} />
                <span className={hasLetter ? 'text-[#277254] font-semibold' : ''}>
                  One letter
                </span>
              </div>
            </div>
          </div>

          {/* Confirm Password with inline feedback */}
          <div>
            <AuthField
              id="input-register-confirm-password"
              label="Confirm password"
              type="password"
              autoComplete="new-password"
              required
              ref={confirmPasswordInputRef}
              value={confirmPassword}
              onChange={(e) => {
                setConfirmPassword(e.target.value);
                if (confirmPasswordError) setConfirmPasswordError('');
              }}
              placeholder="Re-enter your password"
              testId="input-register-confirm-password"
              error={confirmPasswordError}
            />
            {hasConfirmText && (
              <div
                data-testid="confirm-password-feedback"
                className="mt-1 text-[11px] font-semibold"
              >
                {passwordsMatch ? (
                  <span className="inline-flex items-center gap-1 text-[#277254]">
                    <Check size={12} strokeWidth={3} /> Passwords match
                  </span>
                ) : (
                  <span className="text-[#a33d35]">Passwords don't match</span>
                )}
              </div>
            )}
          </div>

          {/* Role Selector: accessible radiogroup with arrow-key navigation */}
          <div>
            <label id="role-radiogroup-label" className="block mb-1.5 text-xs sm:text-sm font-semibold text-[#253142]">
              I am joining as
            </label>
            <div
              role="radiogroup"
              aria-labelledby="role-radiogroup-label"
              data-testid="role-selector-radiogroup"
              className="grid grid-cols-3 gap-2"
            >
              {ROLES.map((item, idx) => {
                const isSelected = role === item.id;
                return (
                  <button
                    type="button"
                    key={item.id}
                    role="radio"
                    aria-checked={isSelected}
                    tabIndex={isSelected ? 0 : -1}
                    ref={(el) => (roleButtonsRef.current[idx] = el)}
                    onKeyDown={(e) => handleRoleKeyDown(e, idx)}
                    onClick={() => setRole(item.id)}
                    data-testid={`button-role-${item.id}`}
                    className={`rounded-xl border px-2 py-2 text-xs font-bold transition focus:outline-hidden focus:ring-2 focus:ring-[#f5c84b]/60 cursor-pointer ${
                      isSelected
                        ? 'border-[#253142] bg-[#253142] text-[#faf7ef] shadow-xs'
                        : 'border-[#c8cac0] bg-white text-[#253142] hover:border-[#253142]'
                    }`}
                  >
                    {item.label}
                  </button>
                );
              })}
            </div>
            {/* Dynamic one-line description based on selected role */}
            <p
              data-testid="role-description"
              className="mt-1.5 text-[11px] text-[#657081] font-medium"
            >
              {selectedRoleDesc}
            </p>
          </div>

          {/* Consent line */}
          <p className="text-[11px] text-[#7b8490] leading-snug">
            By creating an account you agree to the Terms and Privacy Policy.
          </p>

          {/* General submission error */}
          {generalError && (
            <div
              data-testid="register-error"
              className="rounded-xl border border-[#f1d6d1] bg-[#f7e5e1] p-2.5 text-xs font-semibold text-[#a33d35]"
            >
              {generalError}
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            data-testid="button-register"
            className="relative inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#253142] px-4 py-2.5 text-sm font-semibold text-[#faf7ef] hover:bg-[#33435a] transition duration-150 disabled:opacity-60 cursor-pointer min-h-[42px]"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <Loader2 size={16} className="animate-spin text-[#f5c84b]" />
                Creating account...
              </span>
            ) : (
              <>
                <span>Create account</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>

          {/* Link back to login */}
          <p className="text-center text-xs sm:text-sm text-[#687382] pt-0.5">
            Already have an account?{' '}
            <button
              type="button"
              onClick={() => setLocation('/login')}
              data-testid="link-register-login"
              className="font-bold text-[#277254] hover:underline cursor-pointer focus:outline-hidden focus:ring-1 focus:ring-[#277254] rounded"
            >
              Log in
            </button>
          </p>
        </form>
      </AuthLayout>
    </>
  );
}

