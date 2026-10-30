import { useState, useEffect, useMemo } from 'react';
import { useLocation } from 'wouter';
import {
  UserRound,
  Mail,
  ShieldCheck,
  Building2,
  Calendar,
  KeyRound,
  LogOut,
  CheckCircle2,
  Lock,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import { PageHeading, type Notify } from '../components/dashboard/DashboardShared';
import { apiGetCurrentUser, getStoredUser, apiLogout } from '../api/auth';

export function ProfilePage({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();
  const [user, setUser] = useState<any>(() => {
    try {
      return getStoredUser() || JSON.parse(localStorage.getItem('careerflow-session') || '{}');
    } catch {
      return null;
    }
  });

  useEffect(() => {
    apiGetCurrentUser()
      .then((data) => setUser(data))
      .catch(() => {});
  }, []);

  const rawRole = user?.role || 'STUDENT';
  const effectiveRole =
    rawRole === 'HR_MANAGER' || rawRole === 'hr'
      ? 'hr'
      : rawRole === 'AGENCY_ADMIN' || rawRole === 'agency'
      ? 'agency'
      : 'student';

  const displayName = user?.full_name || user?.user || user?.email?.split('@')[0] || 'User';
  const email = user?.email || 'user@example.com';
  const initials = displayName
    .split(' ')
    .map((n: string) => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase();

  const handleLogout = async () => {
    try {
      await apiLogout();
    } catch {
      // Continue client cleanup
    }
    localStorage.removeItem('careerflow-session');
    localStorage.removeItem('careerflow-user');
    notify('Successfully signed out.', 'info');
    setLocation('/login');
  };

  return (
    <AppShell role={effectiveRole} notify={notify}>
      <PageHeading
        eyebrow="Account Settings • User Identity"
        title="My Profile"
        description="Manage your account profile, role credentials, and active session details."
        action={
          <button
            type="button"
            onClick={handleLogout}
            data-testid="button-profile-logout"
            className="inline-flex items-center gap-2 rounded-xl border border-[#d9dbd1] bg-white px-4 py-2 text-xs font-bold text-[#a33d35] hover:bg-[#f7e5e1] transition shadow-xs cursor-pointer"
          >
            <LogOut size={14} /> Log out
          </button>
        }
      />

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_2fr]" data-testid="profile-container">
        {/* Profile Card */}
        <div className="rounded-2xl border border-[#d9dbd1] bg-white p-6 shadow-xs text-center">
          <div className="mx-auto grid h-24 w-24 place-items-center rounded-full bg-[#f5c84b] text-2xl font-black text-[#253142] shadow-sm">
            {initials || 'U'}
          </div>
          <h2 className="mt-4 text-lg font-bold text-[#253142]" data-testid="profile-display-name">
            {displayName}
          </h2>
          <p className="text-xs text-[#7b8490]" data-testid="profile-display-email">
            {email}
          </p>

          <div className="mt-4 inline-flex items-center gap-1.5 rounded-full border border-[#d9dbd1] bg-[#f8f7f2] px-3 py-1 text-xs font-bold capitalize text-[#253142]">
            <ShieldCheck size={14} className="text-[#277254]" />
            <span>{effectiveRole} Workspace</span>
          </div>

          <div className="mt-6 border-t border-[#eceee7] pt-4 text-left space-y-2 text-xs text-[#526072]">
            <div className="flex justify-between">
              <span className="text-[#7b8490]">Account status:</span>
              <span className="font-bold text-[#277254]">Active</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#7b8490]">Security tier:</span>
              <span className="font-bold text-[#253142]">Standard Multi-Factor</span>
            </div>
          </div>
        </div>

        {/* Detailed Info & Settings */}
        <div className="space-y-6">
          <div className="rounded-2xl border border-[#d9dbd1] bg-white p-6 shadow-xs">
            <h3 className="text-sm font-bold text-[#253142] mb-4 flex items-center gap-2">
              <UserRound size={16} className="text-[#277254]" /> Account Credentials
            </h3>
            <div className="grid gap-4 sm:grid-cols-2 text-xs">
              <div className="rounded-xl border border-[#e5e7eb] bg-[#faf9f5] p-3.5">
                <div className="text-[#7b8490]">Full Name</div>
                <div className="mt-1 font-bold text-[#253142]">{displayName}</div>
              </div>
              <div className="rounded-xl border border-[#e5e7eb] bg-[#faf9f5] p-3.5">
                <div className="text-[#7b8490]">Email Address</div>
                <div className="mt-1 font-bold text-[#253142]">{email}</div>
              </div>
              <div className="rounded-xl border border-[#e5e7eb] bg-[#faf9f5] p-3.5">
                <div className="text-[#7b8490]">Role & Permissions</div>
                <div className="mt-1 font-bold text-[#253142] capitalize">{rawRole.replace('_', ' ')}</div>
              </div>
              <div className="rounded-xl border border-[#e5e7eb] bg-[#faf9f5] p-3.5">
                <div className="text-[#7b8490]">Platform Version</div>
                <div className="mt-1 font-bold text-[#253142]">CareerFlow 1.0 (Sprint 6)</div>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-[#d9dbd1] bg-white p-6 shadow-xs">
            <h3 className="text-sm font-bold text-[#253142] mb-2 flex items-center gap-2">
              <Lock size={16} className="text-[#3a6384]" /> Password & Security
            </h3>
            <p className="text-xs text-[#7b8490] mb-4">
              Manage your password reset tokens and security credentials.
            </p>
            <button
              type="button"
              onClick={() => setLocation('/forgot-password')}
              data-testid="button-profile-reset-pwd"
              className="inline-flex items-center gap-2 rounded-xl bg-[#253142] px-4 py-2.5 text-xs font-bold text-white hover:bg-[#33435a] transition cursor-pointer"
            >
              <KeyRound size={14} /> Request Password Reset Link
            </button>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

