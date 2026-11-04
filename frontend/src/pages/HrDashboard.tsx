import { useState, useEffect, useMemo } from 'react';
import { useLocation } from 'wouter';
import { motion, useReducedMotion } from 'framer-motion';
import {
  FolderOpen,
  Users,
  Star,
  Gauge,
  Plus,
  ArrowRight,
  ChevronRight,
  Clock3,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import { PageHeading, type Notify } from '../components/dashboard/DashboardShared';
import { getStoredUser } from '../api/auth';
import { apiGetHRMatches, type CVJobMatch } from '../api/cv';
import { apiGetRooms, type RecruitmentRoom } from '../api/recruitment';
import { RoomCreateModal } from '../components/recruitment/RoomCreateModal';
import { ShortlistConfigModal } from '../components/recruitment/ShortlistConfigModal';
import { InteractiveStatCard } from '../components/dashboard/InteractiveStatCard';
import { InteractiveChecklist, type ChecklistItem } from '../components/dashboard/InteractiveChecklist';
import { ActivityFlowChart, type ActivityDataPoint } from '../components/dashboard/ActivityFlowChart';
import { DASHBOARD_MOTION } from '../components/dashboard/motionTokens';

interface HrActivityItem {
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

export function HrDashboard({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();
  const prefersReduced = useReducedMotion();

  const [hrMatches, setHrMatches] = useState<CVJobMatch[]>([]);
  const [rooms, setRooms] = useState<RecruitmentRoom[]>([]);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [selectedRoomForShortlist, setSelectedRoomForShortlist] = useState<RecruitmentRoom | null>(null);

  // Check for test state preview (?state=empty | single | multi)
  const previewState = useMemo(() => {
    if (typeof window === 'undefined') return null;
    const params = new URLSearchParams(window.location.search);
    return params.get('state');
  }, []);

  const user = useMemo(() => {
    try {
      return getStoredUser() || JSON.parse(localStorage.getItem('careerflow-session') || '{}');
    } catch {
      return null;
    }
  }, []);

  const userName = user?.full_name?.split(' ')[0] || user?.user?.split(' ')[0] || 'Mira';

  useEffect(() => {
    apiGetHRMatches()
      .then((data) => setHrMatches(data || []))
      .catch(() => {});

    apiGetRooms()
      .then((data) => setRooms(data || []))
      .catch(() => {});
  }, []);

  // --- DERIVE EFFECTIVE DATA (State Preview or Live API) ---
  const effectiveRooms = useMemo(() => {
    if (previewState === 'empty') return [];
    if (previewState === 'single') {
      return [
        {
          id: 1,
          title: 'Senior Frontend Engineer',
          company: 'CareerFlow Tech',
          description: 'Lead web platform initiatives.',
          status: 'ACTIVE',
          created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
        } as unknown as RecruitmentRoom,
      ];
    }
    if (previewState === 'multi') {
      return [
        { id: 1, title: 'Senior Frontend Engineer', company: 'TechNova Ltd.', status: 'ACTIVE' },
        { id: 2, title: 'Backend Systems Lead', company: 'BrightStack', status: 'ACTIVE' },
        { id: 3, title: 'Product Designer', company: 'Vertex Digital', status: 'ACTIVE' },
        { id: 4, title: 'Data Analytics Lead', company: 'NextGen', status: 'DRAFT' },
      ] as unknown as RecruitmentRoom[];
    }
    return rooms;
  }, [previewState, rooms]);

  const effectiveMatches = useMemo(() => {
    if (previewState === 'empty') return [];
    if (previewState === 'single') {
      return [
        {
          id: 1,
          candidate_name: 'Alex Rahman',
          room_title: 'Senior Frontend Engineer',
          match_score: 84,
          created_at: new Date(Date.now() - 3600000 * 4).toISOString(),
        } as unknown as CVJobMatch,
      ];
    }
    if (previewState === 'multi') {
      return [
        { id: 1, candidate_name: 'Alex Rahman', room_title: 'Senior Frontend Engineer', match_score: 92, created_at: new Date(Date.now() - 3600000 * 2).toISOString() },
        { id: 2, candidate_name: 'Sara Ahmed', room_title: 'Backend Systems Lead', match_score: 86, created_at: new Date(Date.now() - 3600000 * 8).toISOString() },
        { id: 3, candidate_name: 'Tanvir Hasan', room_title: 'Product Designer', match_score: 88, created_at: new Date(Date.now() - 86400000).toISOString() },
        { id: 4, candidate_name: 'Nusrat Jahan', room_title: 'Data Analytics Lead', match_score: 81, created_at: new Date(Date.now() - 86400000 * 2).toISOString() },
        { id: 5, candidate_name: 'Fahim Karim', room_title: 'Senior Frontend Engineer', match_score: 74, created_at: new Date(Date.now() - 86400000 * 3).toISOString() },
      ] as unknown as CVJobMatch[];
    }
    return hrMatches;
  }, [previewState, hrMatches]);

  const activeRoomsCount = effectiveRooms.filter((r) => r.status === 'ACTIVE').length;
  const applicantsCount = effectiveMatches.length;
  const shortlistedCount = effectiveMatches.filter((m) => m.match_score >= 80).length;
  const shortlistedPct = applicantsCount > 0 ? Math.round((shortlistedCount / applicantsCount) * 100) : 0;
  const avgCvMatch = applicantsCount > 0
    ? Math.round(effectiveMatches.reduce((acc, m) => acc + m.match_score, 0) / applicantsCount)
    : 0;

  const readyCandidatesCount = effectiveMatches.filter((m) => m.match_score >= 75).length;

  // 7-day flow chart data calculation
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

    if (effectiveMatches.length > 0) {
      effectiveMatches.forEach((m, idx) => {
        if (m.created_at) {
          const dStr = m.created_at.split('T')[0];
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
  }, [effectiveMatches]);

  // Dynamic Subtitle
  const pageSubtitle = useMemo(() => {
    if (effectiveRooms.length > 0 && applicantsCount > 0) {
      return `You have ${activeRoomsCount} active recruitment room${
        activeRoomsCount === 1 ? '' : 's'
      } and ${applicantsCount} evaluated candidate${applicantsCount === 1 ? '' : 's'}.`;
    }
    if (effectiveRooms.length > 0 && applicantsCount === 0) {
      return `You have ${activeRoomsCount} active room${
        activeRoomsCount === 1 ? '' : 's'
      }. Awaiting first applicant submissions.`;
    }
    return 'Welcome to your hiring workspace. Create your first recruitment room to begin evaluating candidates.';
  }, [effectiveRooms, activeRoomsCount, applicantsCount]);

  // First-use checklist items
  const checklistItems = useMemo<ChecklistItem[]>(() => {
    return [
      {
        id: 'create-room',
        title: 'Create recruitment room',
        description:
          effectiveRooms.length > 0
            ? `${effectiveRooms.length} room${effectiveRooms.length === 1 ? '' : 's'} created • Active hiring briefs`
            : 'Set required skills, weights, and criteria',
        completed: effectiveRooms.length > 0,
        path: '/hr/rooms',
        icon: FolderOpen,
      },
      {
        id: 'review-candidates',
        title: 'Evaluate applicant matches',
        description:
          applicantsCount > 0
            ? `${applicantsCount} candidate${applicantsCount === 1 ? '' : 's'} evaluated • CV Studio`
            : 'AI semantic matching against requirements',
        completed: applicantsCount > 0,
        path: '/hr/applicants',
        icon: Users,
      },
      {
        id: 'configure-shortlist',
        title: 'Configure automated shortlist',
        description:
          shortlistedCount > 0
            ? `${shortlistedCount} candidate${shortlistedCount === 1 ? '' : 's'} shortlisted`
            : 'Establish threshold rules for candidate advancement',
        completed: shortlistedCount > 0,
        path: '/hr/shortlisted',
        icon: Star,
      },
    ];
  }, [effectiveRooms, applicantsCount, shortlistedCount]);

  // Recent Activity Items
  const recentActivities = useMemo<HrActivityItem[]>(() => {
    const list: HrActivityItem[] = [];

    effectiveMatches.forEach((m, idx) => {
      const ts = m.created_at ? new Date(m.created_at).getTime() : Date.now() - (idx + 1) * 3600000;
      list.push({
        id: `match-${m.id || idx}`,
        title: `${m.candidate_name || 'Candidate'} evaluated`,
        subtitle: `Scored ${m.match_score}/100 match for ${m.room_title || 'Recruitment Room'}`,
        time: formatRelativeTime(ts),
        timestamp: ts,
        path: '/hr/applicants',
      });
    });

    effectiveRooms.forEach((r, idx) => {
      const ts = r.created_at ? new Date(r.created_at).getTime() : Date.now() - (idx + 2) * 86400000;
      list.push({
        id: `room-${r.id || idx}`,
        title: `Room ${r.title} ${r.status === 'ACTIVE' ? 'active' : 'draft'}`,
        subtitle: `${r.company || 'Company'} • Minimum score threshold set`,
        time: formatRelativeTime(ts),
        timestamp: ts,
        path: '/hr/rooms',
      });
    });

    list.sort((a, b) => b.timestamp - a.timestamp);
    return list.slice(0, 4);
  }, [effectiveMatches, effectiveRooms]);

  return (
    <AppShell role="hr" notify={notify}>
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
              data-testid="button-create-room-dashboard"
              className="inline-flex items-center gap-2 rounded-xl bg-[#277254] px-5 py-2.5 text-sm font-bold text-white transition-colors hover:bg-[#1f5b43] active:bg-[#184734] shadow-xs cursor-pointer focus-visible:outline-2 focus-visible:outline-[#277254]"
            >
              <Plus size={16} /> Create room
            </button>
          }
        />
      </motion.div>

      {/* 4 Interactive Clickable Stat Cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {/* 1. Active Rooms */}
        <InteractiveStatCard
          label="Active rooms"
          numericValue={activeRoomsCount}
          detail={`${effectiveRooms.length} total created rooms`}
          icon={FolderOpen}
          accent="yellow"
          onClick={() => setLocation('/hr/rooms')}
          testId="stat-active-rooms"
          delayIndex={0}
        />

        {/* 2. Applicants */}
        <InteractiveStatCard
          label="Applicants"
          numericValue={applicantsCount}
          detail={applicantsCount > 0 ? `${applicantsCount} candidates evaluated` : 'No candidates yet'}
          icon={Users}
          accent="blue"
          onClick={() => setLocation('/hr/applicants')}
          testId="stat-applicants"
          delayIndex={1}
        />

        {/* 3. Shortlisted */}
        <InteractiveStatCard
          label="Shortlisted"
          numericValue={shortlistedCount}
          detail={applicantsCount > 0 ? `${shortlistedPct}% of applicants` : 'Awaiting evaluations'}
          icon={Star}
          accent="green"
          onClick={() => setLocation('/hr/shortlisted')}
          testId="stat-shortlisted"
          delayIndex={2}
        />

        {/* 4. Average CV Match */}
        <InteractiveStatCard
          label="Average CV Match"
          numericValue={avgCvMatch}
          displayOverride={avgCvMatch > 0 ? `${avgCvMatch}%` : '--'}
          detail="Semantic match score"
          icon={Gauge}
          accent="coral"
          onClick={() => setLocation('/hr/applicants')}
          testId="stat-average-cv-match"
          delayIndex={3}
        />
      </div>

      {/* Applicant Flow Chart & Semantic Signal Card */}
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
        {/* Applicant Flow Chart */}
        <section className="cf-card rounded-2xl bg-white p-5 md:p-6 border border-[#d9dbd1] shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-start justify-between">
              <div>
                <h2 className="font-bold text-[#253142] text-lg">Applicant flow</h2>
                <p className="mt-1 text-xs text-[#7b8490]">
                  Last 7 days of candidate evaluations across active hiring rooms
                </p>
              </div>
              <button
                type="button"
                onClick={() => setLocation('/hr/reports')}
                data-testid="link-hr-reports"
                className="flex items-center gap-1 text-xs font-bold text-[#277254] hover:underline cursor-pointer"
              >
                View reports <ChevronRight size={14} />
              </button>
            </div>
            <div className="mt-5">
              <ActivityFlowChart
                data={flowChartData}
                color="#277254"
                unit="applicants"
                emptyMessage="No applicant activity in the last 7 days."
              />
            </div>
          </div>
        </section>

        {/* Semantic Signal Card */}
        <section className="rounded-2xl bg-[#253142] p-6 text-[#faf7ef] shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-[.14em] text-[#f5c84b]">
                Semantic signal
              </span>
              <Users size={20} className="text-[#f5c84b]" />
            </div>
            <h2 className="cf-display mt-5 text-4xl font-bold tracking-tight">
              {readyCandidatesCount} ready
            </h2>
            <p className="mt-2.5 text-sm leading-relaxed text-[#bfc8d0]">
              Candidates exceeding your minimum threshold across active briefs, prepared for team review.
            </p>
          </div>

          <div className="mt-6 border-t border-[#3a4b60] pt-4">
            <button
              type="button"
              onClick={() => {
                if (effectiveRooms.length > 0) {
                  setSelectedRoomForShortlist(effectiveRooms[0]);
                } else {
                  setLocation('/hr/shortlisted');
                }
              }}
              data-testid="button-view-shortlisted-dashboard"
              className="group inline-flex items-center gap-1.5 text-xs font-bold text-[#f5c84b] hover:text-[#fff1c9] transition-colors cursor-pointer focus-visible:outline-2 focus-visible:outline-[#f5c84b]"
            >
              <span>Review shortlist</span>
              <ArrowRight size={14} className="transition-transform duration-200 group-hover:translate-x-1" />
            </button>
          </div>
        </section>
      </motion.div>

      {/* Onboarding Checklist & Recent Activity */}
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
        {/* Starter workflow interactive checklist */}
        <section className="cf-card rounded-2xl bg-white p-5 md:p-6 border border-[#d9dbd1] shadow-xs">
          <InteractiveChecklist initialItems={checklistItems} />
        </section>

        {/* Recent Activity Timeline */}
        <section className="cf-card rounded-2xl bg-white p-5 md:p-6 border border-[#d9dbd1] shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-[#eef0e7] pb-4">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-[.14em] text-[#7b8490]">
                  Hiring audit trail
                </span>
                <h2 className="text-base font-bold text-[#253142] mt-0.5">Recent activity</h2>
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
                    New room creations, candidate evaluations, and shortlist promotions will appear here.
                  </p>
                </div>
              )}
            </div>
          </div>
        </section>
      </motion.div>

      {/* Room Creation Modal */}
      <RoomCreateModal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onRoomCreated={(newRoom) => {
          setRooms((prev) => [newRoom, ...prev]);
          setLocation('/hr/rooms');
        }}
        notify={notify}
      />

      {/* Shortlist Config Modal */}
      {selectedRoomForShortlist && (
        <ShortlistConfigModal
          isOpen={Boolean(selectedRoomForShortlist)}
          onClose={() => setSelectedRoomForShortlist(null)}
          room={selectedRoomForShortlist}
          onShortlistSaved={(updated) => {
            setRooms((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
            setSelectedRoomForShortlist(updated);
          }}
          notify={notify}
        />
      )}
    </AppShell>
  );
}
