import { useState, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { useLocation } from 'wouter';
import {
  LayoutDashboard,
  Presentation,
  Video,
  FileText,
  Briefcase,
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
import { apiLogout, getStoredUser, apiGetCurrentUser, apiGetCandidateProfile, storeUser } from '../../api/auth';
import { NotificationCenter } from './NotificationCenter';
import {
  apiGetNotifications,
  onNotificationsUpdated,
} from '../../api/notifications';
import { Logo as BrandLogo, type LogoTone } from '../brand/Logo';

export function Logo({ dark = false, tone }: { dark?: boolean; tone?: LogoTone }) {
  const resolvedTone: LogoTone = tone || (dark ? 'onDark' : 'color');
  return <BrandLogo tone={resolvedTone} />;
}

export interface AppShellProps {
  role?: Role;
  activeTab?: string;
  activeNav?: string;
  children: ReactNode;
  notify?: Notify;
}

export function AppShell({
  role,
  activeTab,
  activeNav,
  children,
  notify = () => {},
}: AppShellProps) {
  const prefersReduced = useReducedMotion();
  const [path, setLocation] = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && mobileOpen) {
        setMobileOpen(false);
      }
    };
    if (mobileOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [mobileOpen]);
  const [user, setUser] = useState<any>(() => {
    try {
      return getStoredUser() || JSON.parse(localStorage.getItem('careerflow-session') || '{}');
    } catch {
      return null;
    }
  });
  const [unreadCount, setUnreadCount] = useState<number>(0);

  const [avatarError, setAvatarError] = useState(false);
  const avatarUrl = user?.avatar_url || getStoredUser()?.avatar_url;

  useEffect(() => {
    setAvatarError(false);
  }, [avatarUrl]);

  useEffect(() => {
    apiGetCurrentUser()
      .then((data) => {
        setUser((prev: any) => ({ ...prev, ...data }));
        const curr = getStoredUser() || {};
        storeUser({ ...curr, ...data });

        if (!data?.avatar_url) {
          apiGetCandidateProfile()
            .then((prof) => {
              if (prof?.avatar_url) {
                setUser((prev: any) => ({ ...prev, avatar_url: prof.avatar_url }));
                storeUser({ ...curr, ...data, avatar_url: prof.avatar_url });
              }
            })
            .catch(() => {});
        }
      })
      .catch(() => {
        apiGetCandidateProfile()
          .then((prof) => {
            if (prof?.avatar_url) {
              setUser((prev: any) => ({ ...prev, avatar_url: prof.avatar_url }));
              const curr = getStoredUser() || {};
              storeUser({ ...curr, avatar_url: prof.avatar_url });
            }
          })
          .catch(() => {});
      });

    const handleUserUpdate = (e: any) => {
      if (e?.detail) {
        setUser((prev: any) => ({ ...prev, ...e.detail }));
      }
    };
    window.addEventListener('careerflow_user_updated', handleUserUpdate);
    return () => window.removeEventListener('careerflow_user_updated', handleUserUpdate);
  }, []);

  const refreshUnreadCount = useCallback(async () => {
    try {
      const data = await apiGetNotifications();
      setUnreadCount(data.unread_count ?? 0);
    } catch {
      // Ignore network/auth errors in polling
    }
  }, []);

  useEffect(() => {
    refreshUnreadCount();
    const unsubscribe = onNotificationsUpdated((count) => {
      if (typeof count === 'number') {
        setUnreadCount(count);
      } else {
        refreshUnreadCount();
      }
    });
    const interval = setInterval(refreshUnreadCount, 30000);
    return () => {
      unsubscribe();
      clearInterval(interval);
    };
  }, [refreshUnreadCount]);

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
  }, [path]);

  const storedUser = getStoredUser();
  const rawRole =
    user?.role ||
    storedUser?.role ||
    (() => {
      try {
        return JSON.parse(localStorage.getItem('careerflow-session') || '{}')?.role;
      } catch {
        return 'STUDENT';
      }
    })();

  const effectiveRole: Role =
    role ||
    (rawRole === 'HR_MANAGER' || rawRole === 'hr'
      ? 'hr'
      : rawRole === 'AGENCY_ADMIN' || rawRole === 'agency'
      ? 'agency'
      : 'student');

  const nav =
    effectiveRole === 'student'
      ? [
          { icon: LayoutDashboard, label: 'Overview', path: '/student/dashboard', active: true },
          { icon: Briefcase, label: 'Job Board', path: '/student/jobs' },
          { icon: Presentation, label: 'Practice', path: '/student/practice' },
          { icon: Video, label: 'Video history', path: '/student/videos' },
          { icon: FileText, label: 'CV studio', path: '/student/cv' },
          { icon: BriefcaseBusiness, label: 'Applications', path: '/student/applications' },
          { icon: TrendingUp, label: 'My progress', path: '/student/progress' },
        ]
      : effectiveRole === 'hr'
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

  const defaultName = effectiveRole === 'student' ? 'Alex Rahman' : effectiveRole === 'hr' ? 'Mira Chowdhury' : 'Nadia Karim';
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
    if (!targetPath) return;

    let dest = targetPath;
    if (dest === '/student/progress') {
      dest = '/presentation/trends';
    } else if (dest === '/student/applications') {
      dest = '/applications/my-status';
    } else if (dest === '/dashboard') {
      dest =
        effectiveRole === 'hr'
          ? '/hr/dashboard'
          : effectiveRole === 'agency'
          ? '/agency/dashboard'
          : '/student/dashboard';
    }
    setLocation(dest);
  };

  const isNotificationsActive =
    path === '/notifications' ||
    path === '/student/notifications' ||
    activeNav === '/notifications' ||
    activeNav === 'notifications';

  const isProfileActive =
    path === '/profile' ||
    path === '/student/profile' ||
    path === '/hr/profile' ||
    path === '/agency/profile';

  const isSettingsActive =
    path === '/settings' ||
    path === '/student/settings' ||
    path === '/hr/settings' ||
    path === '/agency/settings';

  const roleBadgeStyle =
    effectiveRole === 'hr'
      ? 'bg-[#fff1c9] text-[#8a6a16] border-[#f5c84b]'
      : effectiveRole === 'agency'
      ? 'bg-[#e4edf5] text-[#2a557a] border-[#3a6384]'
      : 'bg-[#e2f0e9] text-[#277254] border-[#277254]';

  return (
    <div className="cf-shell cf-noise flex min-h-screen w-full bg-[#f5f1e6]">
      {/* Sidebar Navigation */}
      <aside
        className={`cf-sidebar fixed inset-y-0 left-0 z-20 flex w-[252px] shrink-0 flex-col border-r border-[#354255] bg-[#253142] px-4 py-5 transition-transform md:sticky md:top-0 md:h-[100dvh] md:translate-x-0 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <Logo dark />

        <div className="mt-8 flex-1 overflow-y-auto">
          <div className="mb-3 px-3 text-[10px] font-bold uppercase tracking-[.18em] text-[#8d9aab]">
            {effectiveRole === 'student' ? 'Your workspace' : `${effectiveRole} workspace`}
          </div>

          <nav className="space-y-1">
            {nav.map(({ icon: Icon, label, path: itemPath, active }) => {
              const isCurrent =
                path === itemPath ||
                (active && path === itemPath) ||
                (itemPath === '/student/cv' && path.startsWith('/student/cv')) ||
                (itemPath === '/student/jobs' && (path === '/student/jobs' || path === '/jobs' || path.startsWith('/student/jobs'))) ||
                (itemPath === '/student/applications' && (path === '/student/applications' || path.startsWith('/applications'))) ||
                (itemPath === '/agency/pipeline' && (path === '/agency/applicants' || path === '/agency/pipeline')) ||
                (itemPath === '/student/videos' && (path === '/presentation/history' || path.startsWith('/presentation/history'))) ||
                (itemPath === '/student/progress' && (path === '/student/progress' || path === '/presentation/trends' || path === '/student/trends')) ||
                (activeTab && activeTab.toLowerCase() === label.toLowerCase());
              return (
                <button
                  key={itemPath}
                  type="button"
                  onClick={() => handleNavClick(itemPath, active)}
                  data-testid={`nav-${label.toLowerCase().replaceAll(' ', '-')}`}
                  className={`relative flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-semibold transition ${
                    isCurrent
                      ? 'text-[#253142]'
                      : 'text-[#b7c0cc] hover:bg-[#303e50] hover:text-[#faf7ef]'
                  }`}
                >
                  {isCurrent && (
                    <motion.div
                      layoutId="active-sidebar-pill"
                      className="absolute inset-0 rounded-xl bg-[#f5c84b]"
                      transition={prefersReduced ? { duration: 0 } : { duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
                    />
                  )}
                  <span className="relative z-10 flex items-center gap-3">
                    <Icon size={17} />
                    <span>{label}</span>
                  </span>
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
              className={`relative flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-semibold transition ${
                isNotificationsActive
                  ? 'text-[#253142]'
                  : 'text-[#b7c0cc] hover:bg-[#303e50] hover:text-[#faf7ef]'
              }`}
            >
              {isNotificationsActive && (
                <motion.div
                  layoutId="active-sidebar-pill"
                  className="absolute inset-0 rounded-xl bg-[#f5c84b]"
                  transition={prefersReduced ? { duration: 0 } : { duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
                />
              )}
              <span className="relative z-10 flex items-center gap-3 w-full">
                <Bell size={17} />
                <span>Notifications</span>
                {unreadCount > 0 && (
                  <span
                    data-testid="sidebar-notification-badge"
                    className={`ml-auto grid min-h-5 min-w-5 place-items-center rounded-full px-1.5 text-[10px] font-bold ${
                      isNotificationsActive
                        ? 'bg-[#253142] text-[#f5c84b]'
                        : 'bg-[#ee7564] text-white shadow-xs'
                    }`}
                  >
                    {unreadCount > 9 ? '9+' : unreadCount}
                  </span>
                )}
              </span>
            </button>
            <button
              type="button"
              onClick={() => handleNavClick('/profile')}
              data-testid="nav-profile"
              className={`relative flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-semibold transition ${
                isProfileActive
                  ? 'text-[#253142]'
                  : 'text-[#b7c0cc] hover:bg-[#303e50] hover:text-[#faf7ef]'
              }`}
            >
              {isProfileActive && (
                <motion.div
                  layoutId="active-sidebar-pill"
                  className="absolute inset-0 rounded-xl bg-[#f5c84b]"
                  transition={prefersReduced ? { duration: 0 } : { duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
                />
              )}
              <span className="relative z-10 flex items-center gap-3">
                <UserRound size={17} />
                <span>Profile</span>
              </span>
            </button>
            <button
              type="button"
              onClick={() => handleNavClick('/settings')}
              data-testid="nav-settings"
              className={`relative flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-semibold transition ${
                isSettingsActive
                  ? 'text-[#253142]'
                  : 'text-[#b7c0cc] hover:bg-[#303e50] hover:text-[#faf7ef]'
              }`}
            >
              {isSettingsActive && (
                <motion.div
                  layoutId="active-sidebar-pill"
                  className="absolute inset-0 rounded-xl bg-[#f5c84b]"
                  transition={prefersReduced ? { duration: 0 } : { duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
                />
              )}
              <span className="relative z-10 flex items-center gap-3">
                <Settings size={17} />
                <span>Settings</span>
              </span>
            </button>
          </nav>
        </div>

        {/* User Card & Logout in Sidebar */}
        <div className="rounded-2xl bg-[#303e50] p-3">
          <div className="mb-2 flex items-center gap-2">
            <div className="grid h-8 w-8 place-items-center rounded-full bg-[#f5c84b] text-xs font-bold text-[#253142] overflow-hidden shrink-0">
              {avatarUrl && !avatarError ? (
                <img
                  src={avatarUrl}
                  alt={displayName}
                  className="h-full w-full object-cover"
                  onError={() => setAvatarError(true)}
                />
              ) : (
                initials || 'U'
              )}
            </div>
            <div className="min-w-0 flex-1">
              <div className="truncate text-xs font-bold text-[#faf7ef]">{displayName}</div>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span
                  data-testid="user-role-badge"
                  className={`rounded border px-1.5 py-0.2 text-[10px] font-bold capitalize ${roleBadgeStyle}`}
                >
                  {effectiveRole}
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
      <main className="min-w-0 flex-1 w-full max-w-full">
        <header className="cf-appbar sticky top-0 z-20 flex h-[72px] items-center justify-between border-b border-[#dedfd6] bg-[#f5f1e6] px-4 sm:px-6 lg:px-8">
          <button
            type="button"
            onClick={() => setMobileOpen(true)}
            data-testid="button-open-menu"
            className="rounded-lg p-2 text-[#526072] hover:bg-[#eef0e7] md:hidden"
          >
            <Menu size={20} />
          </button>

          <div className="hidden text-sm font-semibold text-[#7b8490] md:block truncate">
            {effectiveRole === 'student'
              ? 'Build your next yes.'
              : effectiveRole === 'hr'
              ? 'Make every hiring decision clearer.'
              : 'Move the right people forward.'}
          </div>

          <div className="ml-auto flex items-center gap-3 shrink-0">
            <NotificationCenter
              onNotificationClick={handleNavClick}
              onUnreadCountChange={setUnreadCount}
            />
            <button
              type="button"
              onClick={() => handleNavClick('/profile')}
              data-testid="button-header-profile"
              title="View Profile"
              className="grid h-9 w-9 place-items-center rounded-full bg-[#dce8e1] text-xs font-bold text-[#277254] hover:ring-2 hover:ring-[#277254]/30 transition cursor-pointer overflow-hidden shrink-0"
            >
              {avatarUrl && !avatarError ? (
                <img
                  src={avatarUrl}
                  alt={displayName}
                  className="h-full w-full object-cover"
                  onError={() => setAvatarError(true)}
                />
              ) : (
                initials || 'U'
              )}
            </button>
          </div>
        </header>

        <motion.div
          key={path}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={prefersReduced ? { duration: 0 } : { duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
          className="p-4 sm:p-6 lg:p-8 min-w-0 w-full max-w-full"
        >
          {children}
        </motion.div>
      </main>
    </div>
  );
}
