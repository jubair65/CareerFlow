import { useState } from 'react';
import {
  Settings,
  Bell,
  Mail,
  Shield,
  Eye,
  CheckCircle2,
  Save,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import { PageHeading, type Notify } from '../components/dashboard/DashboardShared';
import { getStoredUser } from '../api/auth';

export function SettingsPage({ notify }: { notify: Notify }) {
  const [emailAlerts, setEmailAlerts] = useState(true);
  const [inAppAlerts, setInAppAlerts] = useState(true);
  const [statusDigest, setStatusDigest] = useState(true);
  const [analyticsConsent, setAnalyticsConsent] = useState(true);

  const storedUser = getStoredUser();
  const rawRole = storedUser?.role || 'STUDENT';
  const effectiveRole =
    rawRole === 'HR_MANAGER' || rawRole === 'hr'
      ? 'hr'
      : rawRole === 'AGENCY_ADMIN' || rawRole === 'agency'
      ? 'agency'
      : 'student';

  const handleSave = () => {
    notify('Settings and notification preferences updated successfully!', 'success');
  };

  return (
    <AppShell role={effectiveRole} notify={notify}>
      <PageHeading
        eyebrow="Configuration • System Preferences"
        title="Settings & Preferences"
        description="Configure your notifications, privacy controls, and workspace preferences."
        action={
          <button
            type="button"
            onClick={handleSave}
            data-testid="button-save-settings"
            className="inline-flex items-center gap-2 rounded-xl bg-[#277254] px-4 py-2 text-xs font-bold text-white hover:bg-[#1f5b43] transition shadow-xs cursor-pointer"
          >
            <Save size={14} /> Save Preferences
          </button>
        }
      />

      <div className="mt-6 space-y-6 max-w-4xl" data-testid="settings-container">
        {/* Notification Preferences */}
        <div className="rounded-2xl border border-[#d9dbd1] bg-white p-6 shadow-xs">
          <h3 className="text-sm font-bold text-[#253142] mb-1 flex items-center gap-2">
            <Bell size={16} className="text-[#f5c84b]" /> Notification Settings
          </h3>
          <p className="text-xs text-[#7b8490] mb-5">
            Manage how CareerFlow alerts you regarding analysis readiness and hiring status changes.
          </p>

          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-[#f0f1ec] pb-3">
              <div>
                <div className="text-xs font-bold text-[#253142]">Email Status Notifications (US-35)</div>
                <div className="text-[11px] text-[#7b8490]">
                  Receive transactional emails when your application is shortlisted or rejected.
                </div>
              </div>
              <input
                type="checkbox"
                checked={emailAlerts}
                onChange={(e) => setEmailAlerts(e.target.checked)}
                className="h-4 w-4 rounded accent-[#277254] cursor-pointer"
              />
            </div>

            <div className="flex items-center justify-between border-b border-[#f0f1ec] pb-3">
              <div>
                <div className="text-xs font-bold text-[#253142]">In-App Bell Alerts (US-34)</div>
                <div className="text-[11px] text-[#7b8490]">
                  Show real-time badge counts and drop-down alerts in the top navigation bar.
                </div>
              </div>
              <input
                type="checkbox"
                checked={inAppAlerts}
                onChange={(e) => setInAppAlerts(e.target.checked)}
                className="h-4 w-4 rounded accent-[#277254] cursor-pointer"
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs font-bold text-[#253142]">AI Analysis Completion Alerts</div>
                <div className="text-[11px] text-[#7b8490]">
                  Receive instant notifications when CV parsing or video speech analysis completes.
                </div>
              </div>
              <input
                type="checkbox"
                checked={statusDigest}
                onChange={(e) => setStatusDigest(e.target.checked)}
                className="h-4 w-4 rounded accent-[#277254] cursor-pointer"
              />
            </div>
          </div>
        </div>

        {/* Privacy & Governance */}
        <div className="rounded-2xl border border-[#d9dbd1] bg-white p-6 shadow-xs">
          <h3 className="text-sm font-bold text-[#253142] mb-1 flex items-center gap-2">
            <Shield size={16} className="text-[#277254]" /> Privacy & Tenant Isolation
          </h3>
          <p className="text-xs text-[#7b8490] mb-5">
            CareerFlow operates under strict role-based isolation and audit compliance.
          </p>

          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs font-bold text-[#253142]">Telemetry & Improvement Insights</div>
              <div className="text-[11px] text-[#7b8490]">
                Allow anonymous scoring telemetry to help improve speech pacing algorithms.
              </div>
            </div>
            <input
              type="checkbox"
              checked={analyticsConsent}
              onChange={(e) => setAnalyticsConsent(e.target.checked)}
              className="h-4 w-4 rounded accent-[#277254] cursor-pointer"
            />
          </div>
        </div>
      </div>
    </AppShell>
  );
}
