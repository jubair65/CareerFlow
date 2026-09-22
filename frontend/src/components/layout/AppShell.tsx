import { useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { useLocation } from 'wouter';
import {
  LayoutDashboard,
  Presentation,
  Video,
  FileText,
  BriefcaseBusiness,
  TrendingUp,
  FolderOpen,
  Users,
  Star,
  BarChart3,
  Building2,
  Bell,
  UserRound,
  Settings,
  LogOut,
  Menu,
} from 'lucide-react';
import type { Role, Notify } from '../dashboard/DashboardShared';
import { apiLogout, getStoredUser, apiGetCurrentUser } from '../../api/auth';

export function Logo({ dark = false }: { dark?: boolean }) {
  return (
    <div className="flex items-center gap-2.5" data-testid="brand-careerflow">
      <div
        className={`grid h-9 w-9 place-items-center rounded-xl ${
          dark ? 'bg-[#f5c84b] text-[#253142]' : 'bg-[#253142] text-[#f5c84b]'
        }`}
      >
        <svg viewBox="0 0 24 24" className="h-[21px] w-[21px]" fill="none" aria-hidden="true">
          <path
            d="M4 6.5h5.25c1.52 0 2.75 1.23 2.75 2.75v5.5c0 1.52 1.23 2.75 2.75 2.75H20"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
          <path
            d="m17.2 14.75 2.8 2.75-2.8 2.75"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <circle cx="4" cy="6.5" r="1.55" fill="currentColor" />
          <circle cx="12" cy="9.25" r="1.55" fill="currentColor" />
        </svg>
      </div>
      <span className={`cf-display text-lg font-bold ${dark ? 'text-[#f8f4e9]' : 'text-[#253142]'}`}>
        CareerFlow
      </span>
    </div>
  );
}

export function AppShell({
  role,
  children,
  notify,
}: {
  role: Role;
  children: ReactNode;
  notify: Notify;
}) {
  const [path, setLocation] = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
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
      .catch(() => {
        // Keep stored user fallback
      });
  }, []);

  const nav =
    role === 'student'
      ? [
          { icon: LayoutDashboard, label: 'Overview', path: '/student/dashboard', active: true },
          { icon: Presentation, label: 'Practice', path: '/student/practice' },
          { icon: Video, label: 'Video history', path: '/student/videos' },
          { icon: FileText, label: 'CV studio', path: '/student/cv' },
          { icon: BriefcaseBusiness, label: 'Applications', path: '/student/applications' },
          { icon: TrendingUp, label: 'My progress', path: '/student/progress' },
        ]
      : role === 'hr'
      ? [
          { icon: LayoutDashboard, label: 'Overview', path: '/hr/dashboard', active: true },
          { icon: FolderOpen, label: 'Recruitment rooms', path: '/hr/rooms' },
          { icon: Users, label: 'Applicants', path: '/hr/applicants' },
          { icon: Star, label: 'Shortlisted', path: '/hr/shortlisted' },
          { icon: BarChart3, label: 'Reports', path: '/hr/reports' },
        ]
      : [
          { icon: LayoutDashboard, label: 'Overview', path: '/agency/dashboard', active: true },
          { icon: Building2, label: 'Clients', path: '/agency/clients' },
          { icon: FolderOpen, label: 'Rooms', path: '/agency/rooms' },
          { icon: Users, label: 'Pipeline', path: '/agency/pipeline' },
          { icon: Star, label: 'Shortlisted', path: '/agency/shortlisted' },
          { icon: BarChart3, label: 'Reports', path: '/agency/reports' },
        ];

  const defaultName = role === 'student' ? 'Alex Rahman' : role === 'hr' ? 'Mira Chowdhury' : 'Nadia Karim';
  const displayName = user?.full_name || user?.user || defaultName;
  const initials = displayName
    .split(' ')
    .map((x: string) => x[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase();

  const handleLogout = async () => {
    await apiLogout();
    localStorage.removeItem('careerflow-session');
    localStorage.removeItem('careerflow_user');
    notify('You have been logged out.', 'info');
    setLocation('/login');
  };

  const handleNavClick = (targetPath: string, isOverview?: boolean) => {
    setMobileOpen(false);
    if (isOverview) {
      setLocation(targetPath);
    } else {
      notify('Sprint 2 feature: Full interactive workflow coming in next sprint!', 'info');
    }
  };

  const roleBadgeStyle =
    role === 'hr'
      ? 'bg-[#fff1c9] text-[#8a6a16] border-[#f5c84b]'
      : role === 'agency'
      ? 'bg-[#e4edf5] text-[#2a557a] border-[#3a6384]'
      : 'bg-[#e2f0e9] text-[#277254] border-[#277254]';

  return (
    <div className="cf-shell cf-noise flex min-h-screen bg-[#f5f1e6]">
      {/* Sidebar Navigation */}
      <aside
        className={`cf-sidebar fixed inset-y-0 left-0 z-20 flex w-[252px] flex-col border-r border-[#354255] bg-[#253142] px-4 py-5 transition-transform md:sticky md:top-0 md:h-[100dvh] md:translate-x-0 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <Logo dark />

        <div className="mt-8 flex-1 overflow-y-auto">
          <div className="mb-3 px-3 text-[10px] font-bold uppercase tracking-[.18em] text-[#8d9aab]">
            {role === 'student' ? 'Your workspace' : `${role} workspace`}
          </div>

          <nav className="space-y-1">
            {nav.map(({ icon: Icon, label, path: itemPath, active }) => {
              const isCurrent = path === itemPath || (active && path.startsWith(itemPath));
              return (
                <button
                  key={itemPath}
                  type="button"
                  onClick={() => handleNavClick(itemPath, active)}
                  data-testid={`nav-${label.toLowerCase().replaceAll(' ', '-')}`}
                  className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-semibold transition ${
                    isCurrent
                      ? 'bg-[#f5c84b] text-[#253142]'
                      : 'text-[#b7c0cc] hover:bg-[#303e50] hover:text-[#faf7ef]'
                  }`}
                >
                  <Icon size={17} />
                  <span>{label}</span>
                </button>
              );
            })}
          </nav>

          <div className="my-5 border-t border-[#354255]" />

          <nav className="space-y-1">
            <button
              type="button"
              onClick={() => handleNavClick('/notifications')}
              data-testid="nav-notifications"
              className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-semibold text-[#b7c0cc] hover:bg-[#303e50]"
            >
              <Bell size={17} /> Notifications
              <span className="ml-auto grid h-5 w-5 place-items-center rounded-full bg-[#ee7564] text-[10px] text-white">
                2
              </span>
            </button>
            <button
              type="button"
              onClick={() => handleNavClick('/profile')}
              data-testid="nav-profile"
              className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-semibold text-[#b7c0cc] hover:bg-[#303e50]"
            >
              <UserRound size={17} /> Profile
            </button>
            <button
              type="button"
              onClick={() => handleNavClick('/settings')}
              data-testid="nav-settings"
              className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-semibold text-[#b7c0cc] hover:bg-[#303e50]"
            >
              <Settings size={17} /> Settings
            </button>
          </nav>
        </div>

        {/* User Card & Logout in Sidebar */}
        <div className="rounded-2xl bg-[#303e50] p-3">
          <div className="mb-2 flex items-center gap-2">
            <div className="grid h-8 w-8 place-items-center rounded-full bg-[#f5c84b] text-xs font-bold text-[#253142]">
              {initials || 'U'}
            </div>
            <div className="min-w-0 flex-1">
              <div className="truncate text-xs font-bold text-[#faf7ef]">{displayName}</div>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span
                  data-testid="user-role-badge"
                  className={`rounded border px-1.5 py-0.2 text-[10px] font-bold capitalize ${roleBadgeStyle}`}
                >
                  {role}
                </span>
                <span className="text-[10px] text-[#9ca9b8]">workspace</span>
              </div>
            </div>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            data-testid="button-dashboard-logout"
            className="flex w-full items-center gap-2 rounded-lg px-1 pt-1 text-xs font-semibold text-[#aeb9c6] hover:text-[#f5c84b]"
          >
            <LogOut size={14} /> Log out
          </button>
        </div>
      </aside>

      {/* Mobile Backdrop */}
      {mobileOpen && (
        <button
          type="button"
          aria-label="Close menu"
          onClick={() => setMobileOpen(false)}
          data-testid="button-close-menu"
          className="fixed inset-0 z-10 bg-[#253142]/40 md:hidden"
        />
      )}

      {/* Main Content Area */}
      <main className="min-w-0 flex-1">
        <header className="cf-appbar sticky top-0 z-10 flex h-[72px] items-center justify-between border-b border-[#dedfd6] bg-[#f5f1e6]/90 px-5 backdrop-blur-md md:px-9">
          <button
            type="button"
            onClick={() => setMobileOpen(true)}
            data-testid="button-open-menu"
            className="rounded-lg p-2 text-[#526072] hover:bg-[#eef0e7] md:hidden"
          >
            <Menu size={20} />
          </button>

          <div className="hidden text-sm font-semibold text-[#7b8490] md:block">
            {role === 'student'
              ? 'Build your next yes.'
              : role === 'hr'
              ? 'Make every hiring decision clearer.'
              : 'Move the right people forward.'}
          </div>

          <div className="ml-auto flex items-center gap-3">
            <button
              type="button"
              onClick={() => notify('Sprint 2 feature: In-app notifications coming soon!', 'info')}
              data-testid="button-header-notifications"
              className="relative rounded-xl p-2 text-[#526072] hover:bg-[#eef0e7]"
            >
              <Bell size={18} />
              <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-[#ee7564]" />
            </button>
            <div
              data-testid="button-header-profile"
              className="grid h-9 w-9 place-items-center rounded-full bg-[#dce8e1] text-xs font-bold text-[#277254]"
            >
              {initials || 'U'}
            </div>
          </div>
        </header>

        <div className="p-5 md:p-9">{children}</div>
      </main>
    </div>
  );
}
