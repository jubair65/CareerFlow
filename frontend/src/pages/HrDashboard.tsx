import { useState, useEffect, useMemo } from 'react';
import { useLocation } from 'wouter';
import {
  FolderOpen,
  Users,
  Star,
  Gauge,
  Plus,
  ArrowRight,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import {
  PageHeading,
  StatCard,
  Chart,
  type Notify,
} from '../components/dashboard/DashboardShared';
import { getStoredUser } from '../api/auth';
import { apiGetHRMatches, type CVJobMatch } from '../api/cv';
import { apiGetRooms, type RecruitmentRoom } from '../api/recruitment';
import { RoomCreateModal } from '../components/recruitment/RoomCreateModal';
import { ShortlistConfigModal } from '../components/recruitment/ShortlistConfigModal';

export function HrDashboard({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();
  const [hrMatches, setHrMatches] = useState<CVJobMatch[]>([]);
  const [rooms, setRooms] = useState<RecruitmentRoom[]>([]);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [selectedRoomForShortlist, setSelectedRoomForShortlist] = useState<RecruitmentRoom | null>(null);

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
      .then((data) => setHrMatches(data))
      .catch(() => {});

    apiGetRooms()
      .then((data) => setRooms(data))
      .catch(() => {});
  }, []);

  const handleAction = (label: string) => {
    notify(`Workflow "${label}" activated in HR workspace!`, 'info');
  };

  const activeRoomsCount = rooms.filter((r) => r.status === 'ACTIVE').length;

  // Derive live stats strictly from real API data; 0 when no data exists
  const applicantsCount = hrMatches.length;
  const shortlistedCount = hrMatches.filter((m) => m.match_score >= 80).length;
  const shortlistedPct = applicantsCount > 0
    ? Math.round((shortlistedCount / applicantsCount) * 100)
    : 0;
  const avgCvMatch = hrMatches.length > 0
    ? Math.round(hrMatches.reduce((acc, m) => acc + m.match_score, 0) / hrMatches.length)
    : 0;

  // Compute live 7-day flow chart values from real match creation dates
  const flowChartData = useMemo(() => {
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

    hrMatches.forEach((m) => {
      if (m.created_at) {
        const dStr = m.created_at.split('T')[0];
        const target = days.find((item) => item.dateStr === dStr);
        if (target) {
          target.count += 1;
        } else {
          days[0].count += 1;
        }
      } else {
        days[days.length - 1].count += 1;
      }
    });

    return {
      values: days.map((d) => d.count),
      labels: days.map((d) => d.label),
    };
  }, [hrMatches]);

  return (
    <AppShell role="hr" notify={notify}>
      <PageHeading
title={`Good morning, ${userName}.`}
        description="Your hiring workspace is ready for candidate evaluation, room creation, and CV match scoring."
        action={
          <button
            type="button"
            onClick={() => setCreateModalOpen(true)}
            data-testid="button-create-room-dashboard"
            className="inline-flex items-center gap-2 rounded-xl bg-[#277254] px-4 py-2.5 text-sm font-bold text-white hover:bg-[#1f5b43] transition shadow-sm"
          >
            <Plus size={16} /> Create room
          </button>
        }
      />

      {/* 4 Metric Cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div onClick={() => setLocation('/hr/rooms')} className="cursor-pointer">
          <StatCard
            label="Active rooms"
            value={rooms.length > 0 ? `${activeRoomsCount}` : "0"}
            detail={`${rooms.length} total created rooms`}
            icon={FolderOpen}
            accent="yellow"
          />
        </div>
        <StatCard
          label="Applicants"
          value={`${applicantsCount}`}
          detail={applicantsCount > 0 ? `${applicantsCount} candidates evaluated` : 'No candidates yet'}
          icon={Users}
          accent="blue"
        />
        <StatCard
          label="Shortlisted"
          value={`${shortlistedCount}`}
          detail={`${shortlistedPct}% of applicants`}
          icon={Star}
          accent="green"
        />
        <StatCard
          label="Average CV Match"
          value={`${avgCvMatch}`}
          detail="Semantic match score"
          icon={Gauge}
          accent="coral"
        />
      </div>

      {/* Applicant Flow Chart & Hiring Signal Card */}
      <div className="mt-5 grid gap-5 xl:grid-cols-[1.2fr_.8fr]">
        <section className="cf-card rounded-2xl bg-white p-5 md:p-6 border border-[#d9dbd1] shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-bold text-[#253142] text-lg">Applicant flow</h2>
              <p className="mt-1 text-xs text-[#7b8490]">Last 7 days across active candidate rooms</p>
            </div>
            <button
              type="button"
              onClick={() => handleAction('View HR Reports')}
              data-testid="link-hr-reports"
              className="text-xs font-bold text-[#277254] hover:underline cursor-pointer"
            >
              View report
            </button>
          </div>
          <div className="mt-6">
            <Chart
              values={flowChartData.values}
              labels={flowChartData.labels}
              color="#277254"
              unit=" applicants"
            />
          </div>
        </section>

        <section className="rounded-2xl bg-[#253142] p-6 text-[#faf7ef] shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs font-bold uppercase tracking-[.14em] text-[#f5c84b]">
                  Semantic Signal
                </div>
                <div className="cf-display mt-2 text-4xl font-bold">
                  {hrMatches.filter((m) => m.match_score >= 75).length} ready
                </div>
              </div>
              <Users size={28} className="text-[#f5c84b]" />
            </div>
            <p className="mt-5 text-sm leading-6 text-[#bfc8d0]">
              Candidates exceeding your minimum score threshold across all active hiring briefs.
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              if (rooms.length > 0) {
                setSelectedRoomForShortlist(rooms[0]);
              } else {
                handleAction('Review Shortlist');
              }
            }}
            data-testid="button-view-shortlisted-dashboard"
            className="mt-5 inline-flex w-fit items-center gap-2 rounded-xl bg-[#303e50] px-4 py-2.5 text-xs font-bold text-[#f5c84b] hover:bg-[#3b4c62] transition cursor-pointer"
          >
            Review shortlist <ArrowRight size={15} />
          </button>
        </section>
      </div>

      <RoomCreateModal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onRoomCreated={(newRoom) => {
          setRooms((prev) => [newRoom, ...prev]);
          setLocation('/hr/rooms');
        }}
        notify={notify}
      />

      {/* US-25 Room Automatic Shortlisting Modal */}
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
