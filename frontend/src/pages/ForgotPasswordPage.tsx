import { useState } from 'react';
import type { FormEvent } from 'react';
import { useLocation } from 'wouter';
import { ArrowRight, CheckCircle2, Eye, EyeOff, KeyRound, Mail, ShieldCheck, RefreshCw } from 'lucide-react';
import { apiPasswordResetRequest, apiPasswordResetVerifyCode, apiPasswordResetConfirm } from '@/api/auth';

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

  // Wizard steps: 'EMAIL' -> 'CODE' -> 'NEW_PASSWORD' -> 'SUCCESS'
  const [email, setEmail] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get('email') || sessionStorage.getItem('cf_reset_email') || '';
  });
  const [code, setCode] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get('code') || '';
  });
  const [step, setStep] = useState<'EMAIL' | 'CODE' | 'NEW_PASSWORD' | 'SUCCESS'>(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('step') === 'code' || sessionStorage.getItem('cf_reset_step') === 'CODE') {
      return 'CODE';
    }
    return 'EMAIL';
  });

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const updateStep = (newStep: 'EMAIL' | 'CODE' | 'NEW_PASSWORD' | 'SUCCESS') => {
    setStep(newStep);
    sessionStorage.setItem('cf_reset_step', newStep);
  };

  const updateEmail = (newEmail: string) => {
    setEmail(newEmail);
    sessionStorage.setItem('cf_reset_email', newEmail);
  };

  // Step 1: Request 4-digit code
  const handleRequestCode = async (e: FormEvent) => {
    e.preventDefault();
    if (!email || !email.includes('@')) {
      setError('Please provide a valid registered email address.');
      return;
    }

    setError('');
    setLoading(true);

    try {
      updateEmail(email.trim().toLowerCase());
      await apiPasswordResetRequest(email.trim().toLowerCase());
      notify('4-digit verification code generated! Check your terminal.', 'success');
      updateStep('CODE');
    } catch (err: any) {
      const errMsg = err?.response?.data?.error || err?.response?.data?.message || 'Could not send verification code. Please try again.';
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Verify 4-digit code
  const handleVerifyCode = async (e: FormEvent) => {
    e.preventDefault();
    const cleanCode = code.trim();
    if (cleanCode.length !== 4 || !/^\d{4}$/.test(cleanCode)) {
      setError('Please enter the 4-digit verification code.');
      return;
    }

    setError('');
    setLoading(true);

    try {
      await apiPasswordResetVerifyCode(email, cleanCode);
      notify('Code verified! You can now choose your new password.', 'success');
      updateStep('NEW_PASSWORD');
    } catch (err: any) {
      const errMsg = err?.response?.data?.code || err?.response?.data?.error || 'Invalid or expired verification code. Please check your terminal or request a new code.';
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Set new password
  const handleResetPassword = async (e: FormEvent) => {
    e.preventDefault();
    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters long.');
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
        email,
        code: code.trim(),
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      sessionStorage.removeItem('cf_reset_step');
      sessionStorage.removeItem('cf_reset_email');
      notify('Password successfully reset! Old credentials revoked.', 'success');
      setStep('SUCCESS');
    } catch (err: any) {
      const errMsg =
        err?.response?.data?.error ||
        (err?.response?.data?.new_password && err.response.data.new_password.join(' ')) ||
        err?.response?.data?.detail ||
        'Password update failed. Code may have expired.';
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  const strength = getPasswordStrength(newPassword);

  return (
    <div className="cf-shell grid min-h-screen bg-[#f5f1e6] md:grid-cols-[.85fr_1.15fr]">
      {/* Left Brand Panel */}
      <div className="hidden bg-[#253142] p-10 text-[#faf7ef] md:flex md:flex-col md:justify-between">
        <div className="flex items-center gap-2.5" data-testid="brand-careerflow">
          <div className="grid h-9 w-9 place-items-center rounded-xl bg-[#f5c84b] text-[#253142]">
            <KeyRound className="h-[21px] w-[21px]" />
          </div>
          <span className="cf-display text-lg font-bold text-[#f8f4e9]">CareerFlow</span>
        </div>

        <div className="max-w-md pb-14">
          <div className="mb-5 text-xs font-bold uppercase tracking-[.18em] text-[#f5c84b]">Account Recovery</div>
          <h2 className="cf-display text-5xl font-bold leading-[1.02]">
            {step === 'EMAIL' && 'Regain access securely.'}
            {step === 'CODE' && 'Verify your identity.'}
            {step === 'NEW_PASSWORD' && 'Create your new password.'}
            {step === 'SUCCESS' && 'Password restored.'}
          </h2>
          <p className="mt-4 text-sm leading-6 text-[#9daaba]">
            {step === 'EMAIL' && 'Enter your registered email. We generate a 4-digit security code for verification.'}
            {step === 'CODE' && 'Check your backend terminal (or email inbox) for the 4-digit code and paste it below.'}
            {step === 'NEW_PASSWORD' && 'Set your new password. It will immediately replace your old one.'}
            {step === 'SUCCESS' && 'Your credentials are updated. You can now log into your CareerFlow workspace.'}
          </p>

          <div className="mt-8 flex gap-2">
            <span className={`h-1.5 rounded-full transition-all ${step === 'EMAIL' ? 'w-10 bg-[#f5c84b]' : 'w-5 bg-[#607084]'}`} />
            <span className={`h-1.5 rounded-full transition-all ${step === 'CODE' ? 'w-10 bg-[#f5c84b]' : 'w-5 bg-[#607084]'}`} />
            <span className={`h-1.5 rounded-full transition-all ${step === 'NEW_PASSWORD' ? 'w-10 bg-[#f5c84b]' : 'w-5 bg-[#607084]'}`} />
          </div>
        </div>

        <div className="text-xs text-[#9daaba]">CareerFlow Security · 4-Digit Instant Verification</div>
      </div>

      {/* Right Content Panel */}
      <div className="flex min-h-[100dvh] flex-col px-5 py-6 md:px-16 md:py-10">
        <div className="flex items-center justify-between md:justify-end">
          <button
            onClick={() => setLocation('/login')}
            data-testid="link-back-login"
            className="text-sm font-bold text-[#526072] hover:text-[#253142]"
          >
            Back to Log in
          </button>
        </div>

        <div className="mx-auto my-auto w-full max-w-[450px] py-12">
          {/* STEP 1: Enter Email */}
          {step === 'EMAIL' && (
            <div>
              <div className="mb-8">
                <div className="mb-3 text-[11px] font-bold uppercase tracking-[.18em] text-[#9a7922]">Step 1 of 3</div>
                <h1 className="cf-display text-4xl font-bold text-[#253142]">Forgot Password</h1>
                <p className="mt-2 text-sm text-[#657081]">
                  Enter your registered email address to receive a 4-digit verification code.
                </p>
              </div>

              <form onSubmit={handleRequestCode} className="space-y-5">
                <div>
                  <label htmlFor="input-forgot-email" className="block mb-1.5 text-sm font-semibold text-[#253142]">
                    Registered Email Address
                  </label>
                  <div className="relative">
                    <input
                      id="input-forgot-email"
                      data-testid="input-forgot-email"
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="name@example.com"
                      className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3.5 py-3 font-normal outline-none transition placeholder:text-[#98a09c] focus:border-[#253142] focus:ring-2 focus:ring-[#f5c84b]/45"
                    />
                    <Mail size={18} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#98a09c]" />
                  </div>
                </div>

                {error && (
                  <div data-testid="forgot-error-message" className="rounded-xl bg-[#f7e5e1] p-3 text-xs font-semibold text-[#a33d35]">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  data-testid="button-forgot-submit"
                  className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#253142] px-4 py-3 text-sm font-semibold text-[#faf7ef] hover:bg-[#33435a] transition disabled:opacity-50"
                >
                  {loading ? 'Generating Code…' : 'Send 4-Digit Code'} {!loading && <ArrowRight size={16} />}
                </button>

                <p className="text-center text-sm text-[#687382]">
                  Remember your password?{' '}
                  <button
                    type="button"
                    onClick={() => setLocation('/login')}
                    data-testid="link-forgot-to-login"
                    className="font-bold text-[#277254] hover:underline"
                  >
                    Log in
                  </button>
                </p>
              </form>
            </div>
          )}

          {/* STEP 2: Enter & Verify 4-Digit Code */}
          {step === 'CODE' && (
            <div>
              <div className="mb-8">
                <div className="mb-3 text-[11px] font-bold uppercase tracking-[.18em] text-[#9a7922]">Step 2 of 3</div>
                <h1 className="cf-display text-4xl font-bold text-[#253142]">Enter 4-Digit Code</h1>
                <p className="mt-2 text-sm text-[#657081]">
                  A 4-digit code was generated for <strong>{email}</strong>. Check your backend terminal (or email).
                </p>
              </div>

              <div className="mb-5 rounded-xl border border-[#d8c98e] bg-[#fff8db] p-4 text-xs text-[#7b6217] leading-5">
                <div className="font-bold flex items-center gap-1.5 mb-1.5 text-sm text-[#55420a]">
                  <span>💻</span> Terminal Verification Code
                </div>
                <p>
                  Look at your backend terminal running <code>py manage.py runserver</code>.
                </p>
                <div className="font-mono bg-black/5 p-2 rounded-lg mt-2 text-xs text-[#403106] border border-[#d8c98e]/60">
                  VERIFICATION CODE : &gt;&gt;&gt;&nbsp;&nbsp;<strong>[ 4-DIGITS ]</strong>&nbsp;&nbsp;&lt;&lt;&lt;
                </div>
                <p className="mt-2 text-[11px] opacity-85">
                  Copy those 4 digits from the terminal and paste them below to verify your identity.
                </p>
              </div>

              <form onSubmit={handleVerifyCode} className="space-y-5">
                <div>
                  <label htmlFor="input-verification-code" className="block mb-1.5 text-sm font-semibold text-[#253142]">
                    4-Digit Verification Code
                  </label>
                  <input
                    id="input-verification-code"
                    data-testid="input-verification-code"
                    type="text"
                    maxLength={4}
                    autoFocus
                    required
                    value={code}
                    onChange={(e) => {
                      const val = e.target.value.replace(/\D/g, '').slice(0, 4);
                      setCode(val);
                      if (val.length === 4) setError('');
                    }}
                    onPaste={(e) => {
                      e.preventDefault();
                      const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 4);
                      setCode(pasted);
                      if (pasted.length === 4) setError('');
                    }}
                    placeholder="••••"
                    className="w-full text-center text-3xl font-mono tracking-[0.5em] rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-4 py-3 outline-none transition placeholder:text-[#98a09c] focus:border-[#253142] focus:ring-2 focus:ring-[#f5c84b]/45"
                  />
                </div>

                {error && (
                  <div data-testid="code-error-message" className="rounded-xl bg-[#f7e5e1] p-3 text-xs font-semibold text-[#a33d35]">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading || code.trim().length !== 4}
                  data-testid="button-verify-code"
                  className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#253142] px-4 py-3 text-sm font-semibold text-[#faf7ef] hover:bg-[#33435a] transition disabled:opacity-50"
                >
                  {loading ? 'Verifying…' : 'Verify Code'} {!loading && <ShieldCheck size={16} />}
                </button>

                <div className="flex items-center justify-between pt-2 text-xs">
                  <button
                    type="button"
                    onClick={() => { updateStep('EMAIL'); setError(''); }}
                    className="font-semibold text-[#526072] hover:text-[#253142]"
                  >
                    ← Change Email
                  </button>
                  <button
                    type="button"
                    onClick={handleRequestCode}
                    className="inline-flex items-center gap-1 font-semibold text-[#277254] hover:underline"
                  >
                    <RefreshCw size={12} /> Resend Code
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* STEP 3: Set New Password */}
          {step === 'NEW_PASSWORD' && (
            <div>
              <div className="mb-8">
                <div className="mb-3 text-[11px] font-bold uppercase tracking-[.18em] text-[#277254]">Step 3 of 3 · Code Verified ✓</div>
                <h1 className="cf-display text-4xl font-bold text-[#253142]">Set New Password</h1>
                <p className="mt-2 text-sm text-[#657081]">
                  Choose a new password for <strong>{email}</strong>.
                </p>
              </div>

              <form onSubmit={handleResetPassword} className="space-y-5">
                <div>
                  <label htmlFor="input-new-password" className="block mb-1.5 text-sm font-semibold text-[#253142]">
                    New Password
                  </label>
                  <div className="relative">
                    <input
                      id="input-new-password"
                      data-testid="input-new-password"
                      type={showPassword ? 'text' : 'password'}
                      required
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="At least 8 characters"
                      className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] pl-3.5 pr-11 py-3 font-normal outline-none transition placeholder:text-[#98a09c] focus:border-[#253142] focus:ring-2 focus:ring-[#f5c84b]/45"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((p) => !p)}
                      data-testid="button-toggle-password"
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 flex items-center justify-center h-8 w-8 rounded-lg text-[#7b8490] hover:text-[#253142] transition"
                    >
                      {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>

                  {newPassword && (
                    <div className="mt-2 space-y-1.5" data-testid="password-strength-meter">
                      <div className="flex items-center justify-between text-xs font-semibold">
                        <span className="text-[#657081]">Strength:</span>
                        <span className={`font-bold ${strength.score >= 3 ? 'text-[#277254]' : strength.score === 2 ? 'text-[#9a7922]' : 'text-[#b34a40]'}`}>
                          {strength.label}
                        </span>
                      </div>
                      <div className="grid grid-cols-4 gap-1.5 h-1.5">
                        {[1, 2, 3, 4].map((s) => (
                          <div key={s} className={`rounded-full transition duration-300 ${strength.score >= s ? strength.color : 'bg-[#e2e3db]'}`} />
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div>
                  <label htmlFor="input-confirm-password" className="block mb-1.5 text-sm font-semibold text-[#253142]">
                    Confirm New Password
                  </label>
                  <div className="relative">
                    <input
                      id="input-confirm-password"
                      data-testid="input-confirm-password"
                      type={showConfirmPassword ? 'text' : 'password'}
                      required
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Re-enter your password"
                      className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] pl-3.5 pr-11 py-3 font-normal outline-none transition placeholder:text-[#98a09c] focus:border-[#253142] focus:ring-2 focus:ring-[#f5c84b]/45"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword((p) => !p)}
                      data-testid="button-toggle-confirm-password"
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 flex items-center justify-center h-8 w-8 rounded-lg text-[#7b8490] hover:text-[#253142] transition"
                    >
                      {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>

                {error && (
                  <div data-testid="reset-error-message" className="rounded-xl bg-[#f7e5e1] p-3 text-xs font-semibold text-[#a33d35]">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  data-testid="button-submit-new-password"
                  className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#253142] px-4 py-3 text-sm font-semibold text-[#faf7ef] hover:bg-[#33435a] transition disabled:opacity-50"
                >
                  {loading ? 'Updating Password…' : 'Change Password'} {!loading && <ShieldCheck size={16} />}
                </button>
              </form>
            </div>
          )}

          {/* STEP 4: Success View */}
          {step === 'SUCCESS' && (
            <div className="space-y-6" data-testid="forgot-success-container">
              <div className="rounded-2xl border border-[#277254]/30 bg-[#e2f0e9] p-6 text-[#277254]">
                <CheckCircle2 size={32} className="mb-3" />
                <h3 className="text-xl font-bold">Password Reset Successful!</h3>
                <p className="mt-2 text-xs leading-5 opacity-90">
                  Your new password is now active. Your old credentials and the 4-digit verification code have been safely revoked.
                </p>
              </div>

              <button
                type="button"
                onClick={() => setLocation('/login')}
                data-testid="button-proceed-login"
                className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#253142] px-4 py-3 text-sm font-semibold text-[#faf7ef] hover:bg-[#33435a] transition"
              >
                Proceed to Log in <ArrowRight size={16} />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
