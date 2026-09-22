import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { useLocation } from 'wouter';
import type { Role, Notify } from '../dashboard/DashboardShared';
import { getStoredTokens, getStoredUser } from '../../api/auth';

export function ProtectedRoute({
  children,
  allowedRoles,
  notify,
}: {
  children: ReactNode;
  allowedRoles?: Role[];
  notify: Notify;
}) {
  const [, setLocation] = useLocation();
  const [authorized, setAuthorized] = useState<boolean | null>(null);

  useEffect(() => {
    const { access } = getStoredTokens();
    const storedUser = getStoredUser();
    const legacySession = localStorage.getItem('careerflow-session');

    // Check basic authentication
    if (!access && !storedUser && !legacySession) {
      notify('Please log in to access your workspace dashboard.', 'error');
      setLocation('/login');
      setAuthorized(false);
      return;
    }

    // Determine current user's role
    const rawRole = storedUser?.role || (legacySession ? JSON.parse(legacySession).role : 'STUDENT');
    const normalizedRole: Role =
      rawRole === 'HR_MANAGER' || rawRole === 'hr'
        ? 'hr'
        : rawRole === 'AGENCY_ADMIN' || rawRole === 'agency'
        ? 'agency'
        : 'student';

    // Verify role permissions if restricted
    if (allowedRoles && !allowedRoles.includes(normalizedRole)) {
      notify(`Access denied: Your account role does not have permission for that dashboard.`, 'error');
      setLocation(`/${normalizedRole}/dashboard`);
      setAuthorized(false);
      return;
    }

    setAuthorized(true);
  }, [allowedRoles, setLocation, notify]);

  if (authorized === null) {
    return (
      <div className="grid min-h-screen place-items-center bg-[#f5f1e6]">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-[#277254] border-t-transparent" />
          <p className="text-sm font-semibold text-[#526072]">Verifying access permissions...</p>
        </div>
      </div>
    );
  }

  if (!authorized) {
    return null;
  }

  return <>{children}</>;
}
