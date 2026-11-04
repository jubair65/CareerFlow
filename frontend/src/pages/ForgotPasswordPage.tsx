import { useState, useEffect, useRef } from 'react';
import type { FormEvent } from 'react';
import { useLocation } from 'wouter';
import { ArrowRight, CheckCircle2, Loader2, RefreshCw } from 'lucide-react';
import { AuthLayout } from '../components/auth/AuthLayout';
import { AuthField } from '../components/auth/AuthField';
import {
  apiPasswordResetRequest,
  apiPasswordResetVerifyCode,
  apiPasswordResetConfirm,
} from '@/api/auth';

type Notify = (message: string, tone?: 'success' | 'info' | 'error') => void;

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

export function ForgotPasswordPage({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();

  // Wizard step: 1 (Email), 2 (Code), 3 (New Password), 4 (Success)
  const [step, setStep] = useState<1 | 2 | 3 | 4>(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('step') === 'code' || sessionStorage.getItem('cf_reset_step') === '2') {
      return 2;
    }
    return 1;
  });

  const [email, setEmail] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get('email') || sessionStorage.getItem('cf_reset_email') || '';
  });
  const [code, setCode] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get('code') || '';
  });

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [infoMessage, setInfoMessage] = useState('');

  // Resend countdown timer for Step 2
  const [resendTimer, setResendTimer] = useState(30);
  const [canResend, setCanResend] = useState(false);

  const emailInputRef = useRef<HTMLInputElement>(null);
  const codeInputRef = useRef<HTMLInputElement>(null);
  const passwordInputRef = useRef<HTMLInputElement>(null);

  // Resend countdown effect
  useEffect(() => {
    if (step !== 2) return;
    setResendTimer(30);
    setCanResend(false);

    const interval = setInterval(() => {
      setResendTimer((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          setCanResend(true);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [step]);

  const updateStep = (nextStep: 1 | 2 | 3 | 4) => {
    setStep(nextStep);
    sessionStorage.setItem('cf_reset_step', String(nextStep));
    setError('');
  };

  const updateEmail = (val: string) => {
    setEmail(val);
    sessionStorage.setItem('cf_reset_email', val);
  };

  // Step 1: Submit Email
  const handleRequestCode = async (e: FormEvent) => {
    e.preventDefault();
    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address.');
      emailInputRef.current?.focus();
      return;
    }

    setError('');
    setLoading(true);

    try {
      const cleanEmail = email.trim().toLowerCase();
      updateEmail(cleanEmail);
      await apiPasswordResetRequest(cleanEmail);
      // Blind enumeration compliant message:
      setInfoMessage("If that email is registered, we've sent a code.");
      notify("If that email is registered, we've sent a code.", 'info');
      updateStep(2);
    } catch {
      // Even if network fails or email is not found, keep blind enumeration safe
      setInfoMessage("If that email is registered, we've sent a code.");
      updateStep(2);
    } finally {
      setLoading(false);
    }
  };

  // Resend code action on Step 2
  const handleResendCode = async () => {
    if (!canResend || loading) return;
    setLoading(true);
    setError('');
    try {
      await apiPasswordResetRequest(email.trim().toLowerCase());
      notify("If that email is registered, we've sent a code.", 'info');
      setResendTimer(30);
      setCanResend(false);
    } catch {
      notify("If that email is registered, we've sent a code.", 'info');
      setResendTimer(30);
      setCanResend(false);
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Verify Code
  const handleVerifyCode = async (e: FormEvent) => {
    e.preventDefault();
    const cleanCode = code.trim();
    if (!cleanCode || cleanCode.length < 4) {
      setError('Please enter your verification code.');
      codeInputRef.current?.focus();
      return;
    }

    setError('');
    setLoading(true);

    try {
      await apiPasswordResetVerifyCode(email, cleanCode);
      notify('Code verified. Please choose a new password.', 'success');
      updateStep(3);
    } catch (err: any) {
      const errMsg =
        err?.response?.data?.error ||
        err?.response?.data?.message ||
        'Invalid or expired verification code. Please request a new one.';
      setError(errMsg);
      codeInputRef.current?.focus();
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Set New Password
  const handleResetPassword = async (e: FormEvent) => {
    e.preventDefault();
    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters.');
      passwordInputRef.current?.focus();
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setError('');
    setLoading(true);

    try {
      await apiPasswordResetConfirm({
        email: email.trim().toLowerCase(),
        code: code.trim(),
        new_password: newPassword,
        confirm_password: confirmPassword,
      });

      notify('Your password has been reset. You can now log in.', 'success');
      sessionStorage.removeItem('cf_reset_step');
      sessionStorage.removeItem('cf_reset_email');
      updateStep(4);
    } catch (err: any) {
      const errMsg =
        err?.response?.data?.error ||
        err?.response?.data?.message ||
        'Could not update password. Please check your verification code.';
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  const strength = getPasswordStrength(newPassword);

  const eyebrowText =
    step === 1
      ? 'Step 1 of 3: Email'
      : step === 2
      ? 'Step 2 of 3: Code'
      : step === 3
      ? 'Step 3 of 3: New password'
      : 'Complete';

  const titleText =
    step === 1
      ? 'Forgot password'
      : step === 2
      ? 'Enter verification code'
      : step === 3
      ? 'Choose new password'
      : 'Password restored';

  const subtitleText =
    step === 1
      ? "Enter your registered email and we'll send you a code."
      : step === 2
      ? `We sent a verification code to ${email || 'your email'}. Enter the code below.`
      : step === 3
      ? 'Choose a strong password containing at least 8 characters.'
      : 'Your credentials have been updated successfully.';

  return (
    <AuthLayout
      title={titleText}
      eyebrow={eyebrowText}
      subtitle={subtitleText}
      showcaseMode="stepped"
      showcaseStep={step === 4 ? 3 : step}
      backLink={{
        label: 'Back to log in',
        href: '/login',
        testId: 'link-back-login',
      }}
    >
      {/* STEP 1: Enter Email */}
      {step === 1 && (
        <form onSubmit={handleRequestCode} className="space-y-4">
          <AuthField
            id="input-forgot-email"
            label="Registered email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="name@example.com"
            testId="input-forgot-email"
            error={error}
          />

          <button
            type="submit"
            disabled={loading}
            data-testid="button-forgot-submit"
            className="relative inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#253142] px-4 py-2.5 text-sm font-semibold text-[#faf7ef] hover:bg-[#33435a] transition duration-150 disabled:opacity-50 cursor-pointer min-h-[42px]"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <Loader2 size={16} className="animate-spin text-[#f5c84b]" />
                Sending code...
              </span>
            ) : (
              <>
                <span>Send code</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>

          <p className="text-center text-xs sm:text-sm text-[#687382] pt-2">
            Remember your password?{' '}
            <button
              type="button"
              onClick={() => setLocation('/login')}
              data-testid="link-forgot-to-login"
              className="font-bold text-[#277254] hover:underline cursor-pointer"
            >
              Back to log in
            </button>
          </p>
        </form>
      )}

      {/* STEP 2: Enter Verification Code */}
      {step === 2 && (
        <form onSubmit={handleVerifyCode} className="space-y-4">
          {infoMessage && (
            <div
              data-testid="forgot-info-banner"
              className="rounded-xl border border-[#b9dec6] bg-[#e2f0e9] p-3 text-xs font-semibold text-[#277254]"
            >
              {infoMessage}
            </div>
          )}

          <AuthField
            id="input-verification-code"
            label="Verification code"
            type="text"
            inputMode="numeric"
            autoComplete="one-time-code"
            maxLength={6}
            required
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
            placeholder="Enter code"
            testId="input-verification-code"
            error={error}
          />

          <div className="flex items-center justify-between text-xs text-[#7b8490]">
            <button
              type="button"
              onClick={() => updateStep(1)}
              className="font-semibold text-[#277254] hover:underline cursor-pointer"
            >
              Change email
            </button>

            {canResend ? (
              <button
                type="button"
                onClick={handleResendCode}
                disabled={loading}
                data-testid="button-resend-code"
                className="inline-flex items-center gap-1 font-bold text-[#277254] hover:underline cursor-pointer"
              >
                <RefreshCw size={12} /> Resend code
              </button>
            ) : (
              <span className="font-medium text-[#7b8490]">
                Resend in {resendTimer}s
              </span>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            data-testid="button-verify-code"
            className="relative inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#253142] px-4 py-2.5 text-sm font-semibold text-[#faf7ef] hover:bg-[#33435a] transition duration-150 disabled:opacity-50 cursor-pointer min-h-[42px]"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <Loader2 size={16} className="animate-spin text-[#f5c84b]" />
                Verifying code...
              </span>
            ) : (
              <>
                <span>Verify code</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </form>
      )}

      {/* STEP 3: Enter New Password */}
      {step === 3 && (
        <form onSubmit={handleResetPassword} className="space-y-4">
          <div>
            <AuthField
              id="input-new-password"
              label="New password"
              type="password"
              autoComplete="new-password"
              required
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="At least 8 characters"
              testId="input-new-password"
            />
            {newPassword && (
              <div className="mt-2 space-y-1" data-testid="password-strength-meter">
                <div className="flex items-center justify-between text-xs font-semibold">
                  <span className="text-[#657081]">Password strength:</span>
                  <span
                    className={`font-bold ${
                      strength.score >= 3
                        ? 'text-[#277254]'
                        : strength.score === 2
                        ? 'text-[#9a7922]'
                        : 'text-[#b34a40]'
                    }`}
                  >
                    {strength.label}
                  </span>
                </div>
                <div className="grid grid-cols-4 gap-1 h-1.5">
                  {[1, 2, 3, 4].map((s) => (
                    <div
                      key={s}
                      className={`rounded-full transition duration-200 ${
                        strength.score >= s ? strength.color : 'bg-[#e2e3db]'
                      }`}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>

          <AuthField
            id="input-confirm-password"
            label="Confirm new password"
            type="password"
            autoComplete="new-password"
            required
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Re-enter your new password"
            testId="input-confirm-password"
            error={error}
          />

          <button
            type="submit"
            disabled={loading}
            data-testid="button-confirm-password"
            className="relative inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#253142] px-4 py-2.5 text-sm font-semibold text-[#faf7ef] hover:bg-[#33435a] transition duration-150 disabled:opacity-50 cursor-pointer min-h-[42px]"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <Loader2 size={16} className="animate-spin text-[#f5c84b]" />
                Updating password...
              </span>
            ) : (
              <>
                <span>Reset password</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </form>
      )}

      {/* STEP 4: Success State */}
      {step === 4 && (
        <div
          data-testid="reset-success-card"
          className="rounded-2xl border border-[#b9dec6] bg-white p-6 text-center shadow-xs space-y-4"
        >
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[#e2f0e9] text-[#277254]">
            <CheckCircle2 size={28} />
          </div>
          <div>
            <h2 className="text-lg font-bold text-[#253142]">Password updated</h2>
            <p className="mt-1 text-xs text-[#657081]">
              Your password has been updated. You can now log into your workspace with your new credentials.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setLocation('/login')}
            data-testid="button-success-to-login"
            className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#253142] px-4 py-2.5 text-sm font-semibold text-[#faf7ef] hover:bg-[#33435a] transition cursor-pointer"
          >
            <span>Proceed to log in</span>
            <ArrowRight size={16} />
          </button>
        </div>
      )}
    </AuthLayout>
  );
}
