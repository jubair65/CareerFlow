import { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import { useLocation } from 'wouter';
import { ArrowRight, CheckCircle2, Eye, EyeOff, KeyRound, ShieldAlert, ShieldCheck } from 'lucide-react';
import { apiPasswordResetConfirm } from '@/api/auth';

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

export function ResetPasswordPage({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();
  const [uid, setUid] = useState('');
  const [token, setToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlUid = params.get('uid');
    const urlToken = params.get('token');
    const urlEmail = params.get('email');
    const urlCode = params.get('code');

    if (urlUid && urlToken) {
      setUid(urlUid);
      setToken(urlToken);
    } else {
      // Seamlessly redirect to the interactive 4-digit verification code recovery page
      const query = urlEmail
        ? `?email=${encodeURIComponent(urlEmail)}${urlCode ? `&code=${encodeURIComponent(urlCode)}&step=code` : ''}`
        : '';
      setLocation(`/forgot-password${query}`);
    }
  }, [setLocation]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!uid || !token) {
      setError('This password reset link is missing required authentication tokens. Please request a new one.');
      return;
    }
    if (newPassword.length < 8) {
      setError('New password must be at least 8 characters long.');
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
        uid,
        token,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      setSuccess(true);
      notify('Password successfully reset. You can now log in.', 'success');
    } catch (err: any) {
      const errMsg =
        err?.response?.data?.error ||
        (err?.response?.data?.new_password && err.response.data.new_password.join(' ')) ||
        err?.response?.data?.detail ||
        'Password reset failed. The link may have expired or already been used.';
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  const strength = getPasswordStrength(newPassword);
  const hasMissingParams = !uid || !token;

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
          <div className="mb-5 text-xs font-bold uppercase tracking-[.18em] text-[#f5c84b]">Password Security</div>
          <h2 className="cf-display text-5xl font-bold leading-[1.02]">Create your new password.</h2>
          <p className="mt-4 text-sm leading-6 text-[#9daaba]">
            Your new password will immediately replace your old one and invalidate any active password reset links.
          </p>
          <div className="mt-8 flex gap-2">
            <span className="h-1.5 w-10 rounded-full bg-[#f5c84b]" />
            <span className="h-1.5 w-10 rounded-full bg-[#f5c84b]" />
            <span className="h-1.5 w-5 rounded-full bg-[#607084]" />
          </div>
        </div>

        <div className="text-xs text-[#9daaba]">CareerFlow Security · Industry Standard PBKDF2 Hashing</div>
      </div>

      {/* Right Form Container */}
      <div className="flex min-h-[100dvh] flex-col px-5 py-6 md:px-16 md:py-10">
        <div className="flex items-center justify-between md:justify-end">
          <button
            onClick={() => setLocation('/login')}
            data-testid="link-reset-to-login"
            className="text-sm font-bold text-[#526072] hover:text-[#253142]"
          >
            Back to Log in
          </button>
        </div>

        <div className="mx-auto my-auto w-full max-w-[450px] py-12">
          <div className="mb-8">
            <div className="mb-3 text-[11px] font-bold uppercase tracking-[.18em] text-[#9a7922]">Security credential update</div>
            <h1 className="cf-display text-4xl font-bold text-[#253142]">Set New Password</h1>
          </div>

          {success ? (
            <div className="space-y-6" data-testid="reset-success-container">
              <div className="rounded-2xl border border-[#277254]/30 bg-[#e2f0e9] p-6 text-[#277254]">
                <CheckCircle2 size={28} className="mb-3" />
                <h3 className="text-lg font-bold">Password Updated Successfully</h3>
                <p className="mt-1.5 text-xs leading-5 opacity-90" data-testid="reset-success-message">
                  Your password has been securely hashed and saved. Your old credentials will no longer work.
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
          ) : hasMissingParams ? (
            <div className="space-y-5" data-testid="reset-missing-params-container">
              <div className="rounded-2xl border border-[#a33d35]/30 bg-[#f7e5e1] p-5 text-[#a33d35]">
                <ShieldAlert size={28} className="mb-2" />
                <h3 className="font-bold text-base">Invalid or Missing Reset Link</h3>
                <p className="mt-1 text-xs opacity-90">
                  This reset link is missing required authorization parameters or was truncated. Please request a new link.
                </p>
              </div>

              <button
                type="button"
                onClick={() => setLocation('/forgot-password')}
                data-testid="button-go-forgot-password"
                className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#253142] px-4 py-3 text-sm font-semibold text-[#faf7ef] hover:bg-[#33435a] transition"
              >
                Request a New Reset Link <ArrowRight size={16} />
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              {/* New Password */}
              <div>
                <label htmlFor="input-reset-password" className="block mb-1.5 text-sm font-semibold text-[#253142]">
                  New Password
                </label>
                <div className="relative">
                  <input
                    id="input-reset-password"
                    data-testid="input-reset-password"
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Enter at least 8 characters"
                    className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] pl-3.5 pr-11 py-3 font-normal outline-none transition placeholder:text-[#98a09c] focus:border-[#253142] focus:ring-2 focus:ring-[#f5c84b]/45"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((p) => !p)}
                    data-testid="button-toggle-password"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 flex items-center justify-center h-8 w-8 rounded-lg text-[#7b8490] hover:text-[#253142] hover:bg-[#eef0e7] transition focus:outline-none"
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>

                {/* Password Strength Indicator */}
                {newPassword && (
                  <div className="mt-2 space-y-1.5" data-testid="password-strength-meter">
                    <div className="flex items-center justify-between text-xs font-semibold">
                      <span className="text-[#657081]">Strength:</span>
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
                  </div>
                )}
              </div>

              {/* Confirm Password */}
              <div>
                <label htmlFor="input-reset-confirm-password" className="block mb-1.5 text-sm font-semibold text-[#253142]">
                  Confirm New Password
                </label>
                <div className="relative">
                  <input
                    id="input-reset-confirm-password"
                    data-testid="input-reset-confirm-password"
                    type={showConfirmPassword ? 'text' : 'password'}
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Re-enter your new password"
                    className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] pl-3.5 pr-11 py-3 font-normal outline-none transition placeholder:text-[#98a09c] focus:border-[#253142] focus:ring-2 focus:ring-[#f5c84b]/45"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword((p) => !p)}
                    data-testid="button-toggle-confirm-password"
                    aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 flex items-center justify-center h-8 w-8 rounded-lg text-[#7b8490] hover:text-[#253142] hover:bg-[#eef0e7] transition focus:outline-none"
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
                data-testid="button-reset-submit"
                className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#253142] px-4 py-3 text-sm font-semibold text-[#faf7ef] hover:bg-[#33435a] transition disabled:opacity-50"
              >
                {loading ? 'Updating Password…' : 'Save New Password'} {!loading && <ShieldCheck size={16} />}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
