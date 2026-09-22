import { useMemo } from 'react';
import {
  FolderOpen,
  Users,
  Star,
  Gauge,
  Plus,
  ArrowRight,
  ChevronRight,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import {
  PageHeading,
  StatCard,
  Chart,
  Badge,
  DataAccessCard,
  candidatesSeed,
  type Notify,
} from '../components/dashboard/DashboardShared';
import { getStoredUser } from '../api/auth';

export function HrDashboard({ notify }: { notify: Notify }) {
  const user = useMemo(() => {
    try {
      return getStoredUser() || JSON.parse(localStorage.getItem('careerflow-session') || '{}');
    } catch {
      return null;
    }
  }, []);

  const userName = user?.full_name?.split(' ')[0] || user?.user?.split(' ')[0] || 'Mira';

  const handleAction = (label: string) => {
    notify(`Sprint 2 feature: "${label}" workflow will be enabled in next sprint!`, 'info');
  };

  return (
    <AppShell role="hr" notify={notify}>
      <PageHeading
        eyebrow="HR Hiring Portal"
        title={`Good morning, ${userName}.`}
        description="Your hiring workspace is ready for the decisions that matter."
        action={
          <button
            type="button"
            onClick={() => handleAction('Create Recruitment Room')}
            data-testid="button-create-room-dashboard"
            className="inline-flex items-center gap-2 rounded-xl bg-[#277254] px-4 py-2.5 text-sm font-bold text-white hover:bg-[#1f5b43] transition shadow-sm"
          >
            <Plus size={16} /> Create room
          </button>
        }
      />

      {/* 4 Metric Cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Active rooms"
          value="3"
          detail="Across 4 open roles"
          icon={FolderOpen}
          accent="yellow"
        />
        <StatCard
          label="Applicants"
          value="48"
          detail="+12 this week"
          icon={Users}
          accent="blue"
        />
        <StatCard
          label="Shortlisted"
          value="11"
          detail="23% of applicants"
          icon={Star}
          accent="green"
        />
        <StatCard
          label="Average score"
          value="78.4"
          detail="+4.6 this month"
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
              <p className="mt-1 text-xs text-[#7b8490]">Last 7 days across your active rooms</p>
            </div>
            <button
              type="button"
              onClick={() => handleAction('View HR Reports')}
              data-testid="link-hr-reports"
              className="text-xs font-bold text-[#277254] hover:underline"
            >
              View report
            </button>
          </div>
          <div className="mt-6">
            <Chart
              values={[32, 47, 41, 66, 57, 78, 92]}
              labels={['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']}
              color="#277254"
            />
          </div>
        </section>

        <section className="rounded-2xl bg-[#253142] p-6 text-[#faf7ef] shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs font-bold uppercase tracking-[.14em] text-[#f5c84b]">
                  Hiring signal
                </div>
                <div className="cf-display mt-2 text-4xl font-bold">11 ready</div>
              </div>
              <Users size={28} className="text-[#f5c84b]" />
            </div>
            <p className="mt-5 text-sm leading-6 text-[#bfc8d0]">
              Candidates above your minimum score across all active recruitment rooms.
            </p>
          </div>
          <button
            type="button"
            onClick={() => handleAction('Review Shortlist')}
            data-testid="button-view-shortlisted-dashboard"
            className="mt-5 inline-flex w-fit items-center gap-2 rounded-xl bg-[#303e50] px-4 py-2.5 text-xs font-bold text-[#f5c84b] hover:bg-[#3b4c62] transition"
          >
            Review shortlist <ArrowRight size={15} />
          </button>
        </section>
      </div>

      {/* Recent Applications Table */}
      <section className="cf-card mt-5 overflow-hidden rounded-2xl bg-white border border-[#d9dbd1] shadow-sm">
        <div className="flex items-center justify-between p-5 border-b border-[#eef0e7]">
          <h2 className="font-bold text-[#253142] text-lg">Recent applications</h2>
          <button
            type="button"
            onClick={() => handleAction('View all applicants')}
            data-testid="link-hr-applicants"
            className="flex items-center gap-1 text-xs font-bold text-[#277254] hover:underline"
          >
            View all <ChevronRight size={14} />
          </button>
        </div>

        <div className="cf-table-wrap overflow-x-auto">
          <table className="cf-table w-full text-left text-sm">
            <thead className="bg-[#fbfaf5] border-b border-[#eef0e7] text-xs font-semibold text-[#7b8490] uppercase tracking-wider">
              <tr>
                <th className="px-5 py-3.5">Candidate</th>
                <th className="px-5 py-3.5">Role</th>
                <th className="px-5 py-3.5">Score</th>
                <th className="px-5 py-3.5">Applied</th>
                <th className="px-5 py-3.5">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#eef0e7]">
              {candidatesSeed.slice(0, 4).map((c) => (
                <tr key={c.id} className="hover:bg-[#fbfaf5] transition">
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-3">
                      <div className="grid h-8 w-8 place-items-center rounded-full bg-[#dce8e1] text-xs font-bold text-[#277254]">
                        {c.name
                          .split(' ')
                          .map((x) => x[0])
                          .join('')}
                      </div>
                      <span className="font-bold text-[#253142]">{c.name}</span>
                    </div>
                  </td>
                  <td className="px-5 py-4 text-sm text-[#687382]">{c.position}</td>
                  <td className="px-5 py-4 font-bold text-[#253142]">{c.overallScore}</td>
                  <td className="px-5 py-4 text-sm text-[#687382]">{c.appliedAt}</td>
                  <td className="px-5 py-4">
                    <Badge
                      tone={
                        c.status === 'Shortlisted'
                          ? 'good'
                          : c.status === 'Rejected'
                          ? 'bad'
                          : 'warn'
                      }
                    >
                      {c.status}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <DataAccessCard />
    </AppShell>
  );
}
