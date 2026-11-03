import { useState, useEffect, useMemo } from 'react';
import { useLocation } from 'wouter';
import {
  Building2,
  FolderOpen,
  Users,
  Sparkles,
  Plus,
  ArrowRight,
  Loader2,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import {
  PageHeading,
  StatCard,
  Chart,
  Badge,
  type Notify,
} from '../components/dashboard/DashboardShared';
import { getStoredUser, apiGetCurrentUser } from '../api/auth';
import {
  apiGetAgencyClients,
  apiGetAgencyRooms,
  apiGetAgencyCrossClientApplicants,
  type ClientCompany,
  type RecruitmentRoom,
  type AgencyCrossClientApplicant,
} from '../api/recruitment';
import { AgencyRoomCreateModal } from '../components/agency/AgencyRoomCreateModal';

function getRelativeTime(dateStr: string): string {
  try {
    const diffMs = Date.now() - new Date(dateStr).getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) return `${diffDays}d ago`;
    return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } catch {
    return 'Recently';
  }
}

export function AgencyDashboard({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();

  const [clients, setClients] = useState<ClientCompany[]>([]);
  const [rooms, setRooms] = useState<RecruitmentRoom[]>([]);
  const [applicants, setApplicants] = useState<AgencyCrossClientApplicant[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [createModalOpen, setCreateModalOpen] = useState(false);

  const [user, setUser] = useState<any>(() => {
    try {
      return getStoredUser() || JSON.parse(localStorage.getItem('careerflow-session') || '{}');
    } catch {
      return null;
    }
  });

  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      const [fetchedClients, fetchedRooms, fetchedApplicants, currentUser] = await Promise.all([
        apiGetAgencyClients().catch(() => []),
        apiGetAgencyRooms().catch(() => []),
        apiGetAgencyCrossClientApplicants().catch(() => []),
        apiGetCurrentUser().catch(() => null),
      ]);

      setClients(fetchedClients);
      setRooms(fetchedRooms);
      setApplicants(fetchedApplicants);
      if (currentUser) {
        setUser((prev: any) => ({ ...prev, ...currentUser }));
      }
    } catch (err: any) {
      console.error('Failed to load agency dashboard data:', err);
      notify('Failed to load agency dashboard metrics.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const userName = user?.full_name?.split(' ')[0] || user?.user?.split(' ')[0] || 'Agency Partner';

  const activeClientsCount = useMemo(() => {
    return clients.filter((c) => c.is_active).length;
  }, [clients]);

  const openRoomsCount = useMemo(() => {
    return rooms.filter((r) => r.status === 'ACTIVE').length;
  }, [rooms]);

  const shortlistedApplicants = useMemo(() => {
    return applicants.filter((a) => a.is_shortlisted);
  }, [applicants]);

  const shortlistedCount = shortlistedApplicants.length;
  const shortlistedPct = applicants.length > 0
    ? Math.round((shortlistedCount / applicants.length) * 100)
    : 0;

  // Compute live 7-day flow chart values from real applicant submissions
  const flowChartData = useMemo(() => {
    const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const now = new Date();
    // Monday-based last 7 days calculation
    const days: { label: string; dateStr: string; count: number }[] = [];
    for (let i = 6; i >= 0; i--) {
      const d = new Date();
      d.setDate(now.getDate() - i);
      const dayIndex = (d.getDay() + 6) % 7; // Convert Sun(0) to 6, Mon(1) to 0
      days.push({
        label: dayNames[dayIndex],
        dateStr: d.toISOString().split('T')[0],
        count: 0,
      });
    }

    applicants.forEach((a) => {
      if (a.applied_at) {
        const dStr = a.applied_at.split('T')[0];
        const target = days.find((item) => item.dateStr === dStr);
        if (target) {
          target.count += 1;
        }
      }
    });

    const maxCount = Math.max(...days.map((d) => d.count), 0);
    return {
      values: maxCount > 0 ? days.map((d) => Math.max(16, Math.round((d.count / maxCount) * 100))) : days.map(() => 0),
      labels: days.map((d) => d.label),
      totalThisWeek: days.reduce((sum, d) => sum + d.count, 0),
    };
  }, [applicants]);

  // Derive real dynamic activity feed from live portfolio entities
  const recentActivities = useMemo(() => {
    const list: { id: string; text: string; time: string; timestamp: number }[] = [];

    // Applicants activities
    applicants.forEach((a) => {
      const timeVal = a.applied_at ? new Date(a.applied_at).getTime() : 0;
      if (a.is_shortlisted) {
        list.push({
          id: `app-short-${a.id}`,
          text: `${a.candidate_name} shortlisted for ${a.client_company_name || 'Client'} (${a.room_title})`,
          time: a.shortlisted_at ? getRelativeTime(a.shortlisted_at) : (a.applied_at ? getRelativeTime(a.applied_at) : 'Recently'),
          timestamp: timeVal + 1000,
        });
      }
      list.push({
        id: `app-apply-${a.id}`,
        text: `${a.candidate_name} applied to ${a.room_title} at ${a.client_company_name || 'Client'}`,
        time: a.applied_at ? getRelativeTime(a.applied_at) : 'Recently',
        timestamp: timeVal,
      });
    });

    // Rooms activities
    rooms.forEach((r) => {
      const timeVal = r.created_at ? new Date(r.created_at).getTime() : 0;
      list.push({
        id: `room-${r.id}`,
        text: `Room "${r.title}" active for ${r.client_company_name || r.company_name || 'client'}`,
        time: r.created_at ? getRelativeTime(r.created_at) : 'Recently',
        timestamp: timeVal,
      });
    });

    // Clients activities
    clients.forEach((c) => {
      const timeVal = c.created_at ? new Date(c.created_at).getTime() : 0;
      list.push({
        id: `client-${c.id}`,
        text: `Client company "${c.name}" registered in portfolio`,
        time: c.created_at ? getRelativeTime(c.created_at) : 'Recently',
        timestamp: timeVal,
      });
    });

    list.sort((a, b) => b.timestamp - a.timestamp);
    return list.slice(0, 5);
  }, [applicants, rooms, clients]);

  const handleRoomCreated = (newRoom: RecruitmentRoom) => {
    setRooms((prev) => [newRoom, ...prev]);
    setCreateModalOpen(false);
    notify(`Recruitment room "${newRoom.title}" created successfully.`, 'success');
  };

  return (
    <AppShell role="agency" notify={notify}>
      <PageHeading
        title={`Good morning, ${userName}.`}
        description="A clear view across every client company and candidate pipeline."
        action={
          <button
            type="button"
            onClick={() => setCreateModalOpen(true)}
            data-testid="button-agency-create-room"
            className="inline-flex items-center gap-2 rounded-xl bg-[#277254] px-4 py-2.5 text-sm font-bold text-white hover:bg-[#1f5b43] transition shadow-sm cursor-pointer"
          >
            <Plus size={16} /> New room
          </button>
        }
      />

      {/* 4 Metric Cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div onClick={() => setLocation('/agency/clients')} className="cursor-pointer">
          <StatCard
            label="Client companies"
            value={String(clients.length)}
            detail={`${activeClientsCount} active client contracts`}
            icon={Building2}
            accent="yellow"
          />
        </div>
        <div onClick={() => setLocation('/agency/rooms')} className="cursor-pointer">
          <StatCard
            label="Open rooms"
            value={String(openRoomsCount)}
            detail={rooms.length > 0 ? `${rooms.length} total client rooms` : 'Across client portfolio'}
            icon={FolderOpen}
            accent="blue"
          />
        </div>
        <div onClick={() => setLocation('/agency/pipeline')} className="cursor-pointer" data-testid="card-agency-applicants">
          <StatCard
            label="Applicants"
            value={String(applicants.length)}
            detail={flowChartData.totalThisWeek > 0 ? `+${flowChartData.totalThisWeek} this week` : 'Across all client rooms'}
            icon={Users}
            accent="green"
          />
        </div>
        <div onClick={() => setLocation('/agency/shortlisted')} className="cursor-pointer">
          <StatCard
            label="AI shortlisted"
            value={String(shortlistedCount)}
            detail={applicants.length > 0 ? `${shortlistedPct}% of applicants` : 'Ready for client review'}
            icon={Sparkles}
            accent="coral"
          />
        </div>
      </div>

      {/* Client Activity Chart & Client Shortlist Card */}
      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <section className="cf-card rounded-2xl bg-white p-5 md:p-6 border border-[#d9dbd1] shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-bold text-[#253142] text-lg">Client activity</h2>
              <p className="mt-1 text-xs text-[#7b8490]">Applicants across your client portfolio</p>
            </div>
            <button
              type="button"
              onClick={() => setLocation('/agency/reports')}
              data-testid="link-agency-reports"
              className="text-xs font-bold text-[#277254] hover:underline cursor-pointer"
            >
              View report
            </button>
          </div>
          <div className="mt-6">
            <Chart
              values={flowChartData.values}
              labels={flowChartData.labels}
              color="#3a6384"
            />
          </div>
        </section>

        <section className="rounded-2xl bg-[#277254] p-6 text-[#f8f4e9] shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <div className="text-xs font-bold uppercase tracking-[.13em] text-[#b9dec6]">
                Client-ready shortlist
              </div>
              <Sparkles size={19} className="text-[#f5c84b]" />
            </div>
            <div className="cf-display mt-6 text-5xl font-bold">{shortlistedCount}</div>
            <p className="mt-3 max-w-sm text-sm leading-6 text-[#d5e8da]">
              {shortlistedCount > 0
                ? 'AI-assisted candidate matches are waiting for your agency review before they are forwarded to clients.'
                : 'No candidates currently waiting in client-ready shortlist. Manage your rooms to begin candidate evaluations.'}
            </p>
          </div>
          <button
            type="button"
            onClick={() => setLocation('/agency/shortlisted')}
            data-testid="button-review-pipeline"
            className="mt-6 inline-flex w-fit items-center gap-2 rounded-xl bg-[#e2f0e9] px-4 py-2.5 text-xs font-bold text-[#277254] hover:bg-[#d2e7dc] transition cursor-pointer"
          >
            Review shortlist <ArrowRight size={15} />
          </button>
        </section>
      </div>

      {/* Client Companies & Latest Activity */}
      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <section className="cf-card rounded-2xl bg-white p-5 md:p-6 border border-[#d9dbd1] shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-[#eef0e7] pb-3">
              <h2 className="font-bold text-[#253142] text-lg">Client companies</h2>
              <button
                type="button"
                onClick={() => setLocation('/agency/clients')}
                data-testid="link-agency-clients"
                className="text-xs font-bold text-[#277254] hover:underline cursor-pointer"
              >
                Manage
              </button>
            </div>
            <div className="mt-4 space-y-2.5">
              {isLoading ? (
                <div className="flex items-center justify-center py-8 text-[#7b8490]">
                  <Loader2 size={24} className="animate-spin text-[#277254]" />
                </div>
              ) : clients.length > 0 ? (
                clients.slice(0, 4).map((c) => (
                  <div
                    key={c.id}
                    className="flex items-center gap-3 rounded-xl bg-[#fbfaf5] border border-[#eef0e7] p-3 transition hover:border-[#ccd0c6]"
                  >
                    <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#e4edf5] text-[#3a6384] shrink-0">
                      <Building2 size={18} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-bold text-[#253142] truncate">{c.name}</div>
                      <div className="text-xs text-[#7b8490] truncate">
                        {c.industry || 'General Industry'} • Contact: {c.contact_person || c.contact_email || 'Direct'}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-[11px] font-semibold text-[#687382]">
                        {c.rooms_count ?? 0} {c.rooms_count === 1 ? 'room' : 'rooms'}
                      </span>
                      <Badge tone={c.is_active ? 'good' : 'warn'}>
                        {c.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                  </div>
                ))
              ) : (
                <div className="py-8 text-center text-xs text-[#7b8490]">
                  <p className="font-semibold text-[#253142]">No client companies registered yet</p>
                  <p className="mt-1">Add your client partners to begin creating client recruitment rooms.</p>
                  <button
                    type="button"
                    onClick={() => setLocation('/agency/clients')}
                    className="mt-3 inline-flex items-center gap-1.5 rounded-xl bg-[#277254] px-3.5 py-2 text-xs font-bold text-white hover:bg-[#1f5b43] transition cursor-pointer"
                  >
                    <Plus size={14} /> Add First Client
                  </button>
                </div>
              )}
            </div>
          </div>
        </section>

        <section className="cf-card rounded-2xl bg-white p-5 md:p-6 border border-[#d9dbd1] shadow-sm flex flex-col justify-between">
          <div>
            <h2 className="font-bold text-[#253142] text-lg border-b border-[#eef0e7] pb-3">
              Latest agency activity
            </h2>
            <div className="mt-4 space-y-4">
              {isLoading ? (
                <div className="flex items-center justify-center py-8 text-[#7b8490]">
                  <Loader2 size={24} className="animate-spin text-[#277254]" />
                </div>
              ) : recentActivities.length > 0 ? (
                recentActivities.map((activity) => (
                  <div key={activity.id} className="flex gap-3 text-sm">
                    <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-[#f5c84b]" />
                    <div className="flex-1 min-w-0">
                      <div className="font-semibold text-[#253142] leading-snug">{activity.text}</div>
                      <div className="mt-0.5 text-xs text-[#7b8490]">{activity.time}</div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="py-8 text-center text-xs text-[#7b8490]">
                  <p className="font-semibold text-[#253142]">No recent activity recorded yet</p>
                  <p className="mt-1">Activity across clients, rooms, and candidate submissions will appear here.</p>
                </div>
              )}
            </div>
          </div>
        </section>
      </div>

      {/* Agency Room Create Modal */}
      <AgencyRoomCreateModal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onRoomCreated={handleRoomCreated}
        notify={notify}
      />
    </AppShell>
  );
}
