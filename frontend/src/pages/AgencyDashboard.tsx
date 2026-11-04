import { useState, useEffect, useMemo } from 'react';
import { useLocation } from 'wouter';
import { motion, useReducedMotion } from 'framer-motion';
import {
  Building2,
  FolderOpen,
  Users,
  Star,
  Plus,
  ArrowRight,
  ChevronRight,
  Clock3,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import { PageHeading, type Notify } from '../components/dashboard/DashboardShared';
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
import { InteractiveStatCard } from '../components/dashboard/InteractiveStatCard';
import { InteractiveChecklist, type ChecklistItem } from '../components/dashboard/InteractiveChecklist';
import { ActivityFlowChart, type ActivityDataPoint } from '../components/dashboard/ActivityFlowChart';
import { DASHBOARD_MOTION } from '../components/dashboard/motionTokens';

interface AgencyActivityItem {
  id: string;
  title: string;
  subtitle: string;
  time: string;
  timestamp: number;
  path: string;
}

function formatRelativeTime(timestamp: number): string {
  if (!timestamp) return 'Recently';
  const now = Date.now();
  const diffMs = now - timestamp;
  const diffMinutes = Math.floor(diffMs / (1000 * 60));
  if (diffMinutes < 1) return 'Just now';
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  const diffHours = Math.floor(diffMinutes / (1000 * 60 * 60));
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  return new Date(timestamp).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

export function AgencyDashboard({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();
  const prefersReduced = useReducedMotion();

  const [clients, setClients] = useState<ClientCompany[]>([]);
  const [rooms, setRooms] = useState<RecruitmentRoom[]>([]);
  const [applicants, setApplicants] = useState<AgencyCrossClientApplicant[]>([]);
  const [, setIsLoading] = useState(true);
  const [createModalOpen, setCreateModalOpen] = useState(false);

  // Check for test state preview (?state=empty | single | multi)
  const previewState = useMemo(() => {
    if (typeof window === 'undefined') return null;
    const params = new URLSearchParams(window.location.search);
    return params.get('state');
  }, []);

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

      setClients(fetchedClients || []);
      setRooms(fetchedRooms || []);
      setApplicants(fetchedApplicants || []);
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

  const userName = user?.full_name?.split(' ')[0] || user?.user?.split(' ')[0] || 'Nadia';

  // --- DERIVE EFFECTIVE DATA (State Preview or Live API) ---
  const effectiveClients = useMemo(() => {
    if (previewState === 'empty') return [];
    if (previewState === 'single') {
      return [
        { id: 1, name: 'TechNova Ltd.', industry: 'Enterprise SaaS', contact_person: 'Arif Chowdhury', is_active: true, rooms_count: 1 } as unknown as ClientCompany,
      ];
    }
    if (previewState === 'multi') {
      return [
        { id: 1, name: 'TechNova Ltd.', industry: 'Enterprise SaaS', contact_person: 'Arif Chowdhury', is_active: true, rooms_count: 3 },
        { id: 2, name: 'BrightStack Solutions', industry: 'Fintech & Cloud', contact_person: 'Sabrina Rahman', is_active: true, rooms_count: 2 },
        { id: 3, name: 'Vertex Digital', industry: 'Design & Engineering', contact_person: 'Kamal Hossain', is_active: false, rooms_count: 1 },
      ] as unknown as ClientCompany[];
    }
    return clients;
  }, [previewState, clients]);

  const effectiveRooms = useMemo(() => {
    if (previewState === 'empty') return [];
    if (previewState === 'single') {
      return [
        { id: 1, title: 'Frontend Engineer', client_name: 'TechNova Ltd.', status: 'ACTIVE', created_at: new Date().toISOString() } as unknown as RecruitmentRoom,
      ];
    }
    if (previewState === 'multi') {
      return [
        { id: 1, title: 'Frontend Engineer', client_name: 'TechNova Ltd.', status: 'ACTIVE' },
        { id: 2, title: 'Backend Systems Lead', client_name: 'BrightStack', status: 'ACTIVE' },
        { id: 3, title: 'UI/UX Designer', client_name: 'Vertex Digital', status: 'ACTIVE' },
        { id: 4, title: 'DevOps Architect', client_name: 'BrightStack', status: 'ACTIVE' },
        { id: 5, title: 'QA Automation Lead', client_name: 'TechNova Ltd.', status: 'ACTIVE' },
        { id: 6, title: 'Data Analyst', client_name: 'NextGen Labs', status: 'ACTIVE' },
      ] as unknown as RecruitmentRoom[];
    }
    return rooms;
  }, [previewState, rooms]);

  const effectiveApplicants = useMemo(() => {
    if (previewState === 'empty') return [];
    if (previewState === 'single') {
      return [
        { id: 1, candidate_name: 'Alex Rahman', client_company_name: 'TechNova Ltd.', room_title: 'Frontend Engineer', is_shortlisted: true, overall_score: 89, applied_at: new Date(Date.now() - 3600000 * 3).toISOString() } as unknown as AgencyCrossClientApplicant,
      ];
    }
    if (previewState === 'multi') {
      const list: AgencyCrossClientApplicant[] = [];
      const names = ['Alex Rahman', 'Sara Ahmed', 'Tanvir Hasan', 'Nusrat Jahan', 'Fahim Karim', 'Mehedi Hasan'];
      for (let i = 0; i < 24; i++) {
        list.push({
          id: i + 1,
          candidate_name: names[i % names.length],
          client_company_name: i % 2 === 0 ? 'TechNova Ltd.' : 'BrightStack Solutions',
          room_title: i % 2 === 0 ? 'Frontend Engineer' : 'Backend Lead',
          is_shortlisted: i < 18,
          overall_score: 80 + (i % 15),
          applied_at: new Date(Date.now() - (i + 1) * 3600000 * 4).toISOString(),
        } as unknown as AgencyCrossClientApplicant);
      }
      return list;
    }
    return applicants;
  }, [previewState, applicants]);

  const activeClientsCount = effectiveClients.filter((c) => c.is_active).length;
  const openRoomsCount = effectiveRooms.filter((r) => r.status === 'ACTIVE').length;
  const shortlistedCount = effectiveApplicants.filter((a) => a.is_shortlisted).length;
  const applicantsCount = effectiveApplicants.length;
  const shortlistedPct = applicantsCount > 0 ? Math.round((shortlistedCount / applicantsCount) * 100) : 0;

  // 7-day flow chart calculation
  const flowChartData = useMemo<ActivityDataPoint[]>(() => {
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const now = new Date();
    const days: { label: string; dateStr: string; count: number }[] = [];
    for (let i = 6; i >= 0; i--) {
      const d = new Date();
      d.setDate(now.getDate() - i);
      days.push({
        label: dayNames[d.getDay()],
        dateStr: d.toISOString().split('T')[0],
        count: 0,
      });
    }

    if (effectiveApplicants.length > 0) {
      effectiveApplicants.forEach((a, idx) => {
        if (a.applied_at) {
          const dStr = a.applied_at.split('T')[0];
          const target = days.find((item) => item.dateStr === dStr);
          if (target) {
            target.count += 1;
          } else {
            days[idx % days.length].count += 1;
          }
        } else {
          days[idx % days.length].count += 1;
        }
      });
    }

    return days;
  }, [effectiveApplicants]);

  // Dynamic Subtitle
  const pageSubtitle = useMemo(() => {
    if (effectiveClients.length > 0 && openRoomsCount > 0) {
      return `Managing ${effectiveClients.length} client compan${
        effectiveClients.length === 1 ? 'y' : 'ies'
      } with ${openRoomsCount} open recruitment room${openRoomsCount === 1 ? '' : 's'} across your portfolio.`;
    }
    if (effectiveClients.length > 0 && openRoomsCount === 0) {
      return `Managing ${effectiveClients.length} client partner${
        effectiveClients.length === 1 ? '' : 's'
      }. Create client rooms to begin candidate pipelines.`;
    }
    return 'Welcome to your agency workspace. Add your first client partner to begin creating rooms.';
  }, [effectiveClients, openRoomsCount]);

  // First-use checklist items
  const checklistItems = useMemo<ChecklistItem[]>(() => {
    return [
      {
        id: 'register-client',
        title: 'Register client company',
        description:
          effectiveClients.length > 0
            ? `${effectiveClients.length} client${effectiveClients.length === 1 ? '' : 's'} registered • Client Management`
            : 'Add client partner profile and contacts',
        completed: effectiveClients.length > 0,
        path: '/agency/clients',
        icon: Building2,
      },
      {
        id: 'create-room',
        title: 'Launch client recruitment room',
        description:
          effectiveRooms.length > 0
            ? `${effectiveRooms.length} room${effectiveRooms.length === 1 ? '' : 's'} active across portfolio`
            : 'Configure hiring brief and scoring criteria',
        completed: effectiveRooms.length > 0,
        path: '/agency/rooms',
        icon: FolderOpen,
      },
      {
        id: 'forward-shortlist',
        title: 'Review and forward shortlist',
        description:
          shortlistedCount > 0
            ? `${shortlistedCount} candidate${shortlistedCount === 1 ? '' : 's'} client-ready`
            : 'Verify candidate scores before forwarding',
        completed: shortlistedCount > 0,
        path: '/agency/shortlisted',
        icon: Star,
      },
    ];
  }, [effectiveClients, effectiveRooms, shortlistedCount]);

  // Recent Activity Items
  const recentActivities = useMemo<AgencyActivityItem[]>(() => {
    const list: AgencyActivityItem[] = [];

    effectiveApplicants.forEach((a, idx) => {
      const ts = a.applied_at ? new Date(a.applied_at).getTime() : Date.now() - (idx + 1) * 3600000;
      if (a.is_shortlisted) {
        list.push({
          id: `short-${a.id || idx}`,
          title: `${a.candidate_name || 'Candidate'} shortlisted`,
          subtitle: `Ready for client review at ${a.client_company_name || 'Client'} (${a.room_title || 'Room'})`,
          time: formatRelativeTime(ts),
          timestamp: ts + 1000,
          path: '/agency/shortlisted',
        });
      } else {
        list.push({
          id: `app-${a.id || idx}`,
          title: `${a.candidate_name || 'Candidate'} applied`,
          subtitle: `${a.room_title || 'Room'} at ${a.client_company_name || 'Client'}`,
          time: formatRelativeTime(ts),
          timestamp: ts,
          path: '/agency/pipeline',
        });
      }
    });

    effectiveRooms.forEach((r, idx) => {
      const ts = r.created_at ? new Date(r.created_at).getTime() : Date.now() - (idx + 2) * 86400000;
      list.push({
        id: `room-${r.id || idx}`,
        title: `Room ${r.title} active`,
        subtitle: `Client brief configured for candidate matching`,
        time: formatRelativeTime(ts),
        timestamp: ts,
        path: '/agency/rooms',
      });
    });

    list.sort((a, b) => b.timestamp - a.timestamp);
    return list.slice(0, 4);
  }, [effectiveApplicants, effectiveRooms]);

  const handleRoomCreated = (newRoom: RecruitmentRoom) => {
    setRooms((prev) => [newRoom, ...prev]);
    setCreateModalOpen(false);
    notify(`Recruitment room "${newRoom.title}" created successfully.`, 'success');
  };

  return (
    <AppShell role="agency" notify={notify}>
      {/* Header with Title and Primary Action */}
      <motion.div
        initial={prefersReduced ? false : { opacity: 0, y: -12 }}
        animate={prefersReduced ? false : { opacity: 1, y: 0 }}
        transition={{ duration: DASHBOARD_MOTION.duration.section, ease: DASHBOARD_MOTION.easeOutQuint }}
      >
        <PageHeading
          title={`Good morning, ${userName}.`}
          description={pageSubtitle}
          action={
            <button
              type="button"
              onClick={() => setCreateModalOpen(true)}
              data-testid="button-agency-create-room"
              className="inline-flex items-center gap-2 rounded-xl bg-[#277254] px-5 py-2.5 text-sm font-bold text-white transition-colors hover:bg-[#1f5b43] active:bg-[#184734] shadow-xs cursor-pointer focus-visible:outline-2 focus-visible:outline-[#277254]"
            >
              <Plus size={16} /> New room
            </button>
          }
        />
      </motion.div>

      {/* 4 Interactive Clickable Stat Cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {/* 1. Client Companies */}
        <InteractiveStatCard
          label="Client companies"
          numericValue={effectiveClients.length}
          detail={`${activeClientsCount} active client contracts`}
          icon={Building2}
          accent="yellow"
          onClick={() => setLocation('/agency/clients')}
          testId="stat-client-companies"
          delayIndex={0}
        />

        {/* 2. Open Rooms */}
        <InteractiveStatCard
          label="Open rooms"
          numericValue={openRoomsCount}
          detail={`${effectiveRooms.length} total client rooms`}
          icon={FolderOpen}
          accent="blue"
          onClick={() => setLocation('/agency/rooms')}
          testId="stat-open-rooms"
          delayIndex={1}
        />

        {/* 3. Applicants */}
        <InteractiveStatCard
          label="Applicants"
          numericValue={applicantsCount}
          detail={applicantsCount > 0 ? `${applicantsCount} candidates evaluated` : 'Across all client rooms'}
          icon={Users}
          accent="green"
          onClick={() => setLocation('/agency/pipeline')}
          testId="stat-applicants"
          delayIndex={2}
        />

        {/* 4. AI Shortlisted */}
        <InteractiveStatCard
          label="AI Shortlisted"
          numericValue={shortlistedCount}
          detail={applicantsCount > 0 ? `${shortlistedPct}% of applicants` : 'Ready for client review'}
          icon={Star}
          accent="coral"
          onClick={() => setLocation('/agency/shortlisted')}
          testId="stat-ai-shortlisted"
          delayIndex={3}
        />
      </div>

      {/* Client Activity Chart & Client-Ready Shortlist Card */}
      <motion.div
        initial={prefersReduced ? false : { opacity: 0, y: 16 }}
        animate={prefersReduced ? false : { opacity: 1, y: 0 }}
        transition={{
          duration: DASHBOARD_MOTION.duration.section,
          delay: 0.15,
          ease: DASHBOARD_MOTION.easeOutQuint,
        }}
        className="mt-5 grid gap-5 xl:grid-cols-[1.35fr_.65fr]"
      >
        {/* Client Activity Flow Chart */}
        <section className="cf-card rounded-2xl bg-white p-5 md:p-6 border border-[#d9dbd1] shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-start justify-between">
              <div>
                <h2 className="font-bold text-[#253142] text-lg">Client activity</h2>
                <p className="mt-1 text-xs text-[#7b8490]">
                  Applicant volume across your agency portfolio over the last 7 days
                </p>
              </div>
              <button
                type="button"
                onClick={() => setLocation('/agency/reports')}
                data-testid="link-agency-reports"
                className="flex items-center gap-1 text-xs font-bold text-[#277254] hover:underline cursor-pointer"
              >
                View reports <ChevronRight size={14} />
              </button>
            </div>
            <div className="mt-5">
              <ActivityFlowChart
                data={flowChartData}
                color="#3a6384"
                unit="applicants"
                emptyMessage="No candidate submissions across client portfolio in the last 7 days."
              />
            </div>
          </div>
        </section>

        {/* Client-Ready Shortlist Card */}
        <section className="rounded-2xl bg-[#277254] p-6 text-[#f8f4e9] shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-[.14em] text-[#b9dec6]">
                Client-ready shortlist
              </span>
              <Star size={20} className="text-[#f5c84b]" />
            </div>
            <h2 className="cf-display mt-5 text-4xl font-bold tracking-tight">
              {shortlistedCount} ready
            </h2>
            <p className="mt-2.5 text-sm leading-relaxed text-[#d5e8da]">
              {shortlistedCount > 0
                ? 'AI-assisted candidate matches are waiting for your agency review before they are forwarded to clients.'
                : 'No candidates currently waiting in client-ready shortlist. Manage rooms to begin candidate evaluations.'}
            </p>
          </div>

          <div className="mt-6 border-t border-[#358766] pt-4">
            <button
              type="button"
              onClick={() => setLocation('/agency/shortlisted')}
              data-testid="button-review-pipeline"
              className="group inline-flex items-center gap-1.5 text-xs font-bold text-[#f5c84b] hover:text-[#fff1c9] transition-colors cursor-pointer focus-visible:outline-2 focus-visible:outline-[#f5c84b]"
            >
              <span>Review shortlisted pipeline</span>
              <ArrowRight size={14} className="transition-transform duration-200 group-hover:translate-x-1" />
            </button>
          </div>
        </section>
      </motion.div>

      {/* Agency Operations Checklist & Recent Activity */}
      <motion.div
        initial={prefersReduced ? false : { opacity: 0, y: 16 }}
        animate={prefersReduced ? false : { opacity: 1, y: 0 }}
        transition={{
          duration: DASHBOARD_MOTION.duration.section,
          delay: 0.25,
          ease: DASHBOARD_MOTION.easeOutQuint,
        }}
        className="mt-5 grid gap-5 xl:grid-cols-2"
      >
        {/* Operations interactive checklist */}
        <section className="cf-card rounded-2xl bg-white p-5 md:p-6 border border-[#d9dbd1] shadow-xs">
          <InteractiveChecklist initialItems={checklistItems} />
        </section>

        {/* Recent Activity Timeline */}
        <section className="cf-card rounded-2xl bg-white p-5 md:p-6 border border-[#d9dbd1] shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-[#eef0e7] pb-4">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-[.14em] text-[#7b8490]">
                  Portfolio audit trail
                </span>
                <h2 className="text-base font-bold text-[#253142] mt-0.5">Recent agency activity</h2>
              </div>
              <Clock3 size={17} className="text-[#9aa2a9]" />
            </div>

            <div className="relative mt-4 space-y-3.5">
              {recentActivities.length > 0 && (
                <div className="absolute left-[7px] top-2.5 bottom-2.5 w-[2px] bg-[#eef0e7]" />
              )}

              {recentActivities.length > 0 ? (
                recentActivities.map((act) => (
                  <motion.div
                    key={act.id}
                    initial={prefersReduced ? false : { opacity: 0, x: -8 }}
                    animate={prefersReduced ? false : { opacity: 1, x: 0 }}
                    transition={{ duration: DASHBOARD_MOTION.duration.component, ease: DASHBOARD_MOTION.easeOutQuint }}
                    onClick={() => setLocation(act.path)}
                    className="group relative flex items-start gap-3.5 rounded-xl p-2 transition-colors hover:bg-[#faf8f2] cursor-pointer"
                  >
                    <span className="relative z-10 mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full bg-[#f5c84b] ring-4 ring-white" />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-xs font-bold text-[#253142] group-hover:text-[#277254] transition-colors">
                          {act.title}
                        </span>
                        <span className="text-[10px] font-semibold text-[#8d9aab]">
                          {act.time}
                        </span>
                      </div>
                      <p className="truncate text-[11px] text-[#7b8490] mt-0.5">{act.subtitle}</p>
                    </div>
                    <ChevronRight size={14} className="mt-1 text-[#9da5ac] opacity-0 transition-all group-hover:opacity-100 group-hover:translate-x-0.5" />
                  </motion.div>
                ))
              ) : (
                <div className="flex flex-col items-center justify-center py-8 text-center text-[#7b8490]">
                  <Clock3 className="h-8 w-8 text-[#9da5ac] mb-2" />
                  <p className="text-sm font-semibold text-[#526072]">No recent activity recorded</p>
                  <p className="mt-1 text-xs text-[#8a929c]">
                    Client registrations, room creations, and applicant pipeline events will appear here.
                  </p>
                </div>
              )}
            </div>
          </div>
        </section>
      </motion.div>

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
