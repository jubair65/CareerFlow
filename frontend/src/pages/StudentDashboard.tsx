import { useMemo } from 'react';
import { useLocation } from 'wouter';
import {
  Presentation,
  FileText,
  Target,
  BriefcaseBusiness,
  Play,
  ArrowRight,
  ChevronRight,
  Sparkles,
  Clock3,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import {
  PageHeading,
  StatCard,
  Chart,
  DataAccessCard,
  type Notify,
} from '../components/dashboard/DashboardShared';
import { getStoredUser } from '../api/auth';

export function StudentDashboard({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();
  const user = useMemo(() => {
    try {
      return getStoredUser() || JSON.parse(localStorage.getItem('careerflow-session') || '{}');
    } catch {
      return null;
    }
  }, []);

  const userName = user?.full_name?.split(' ')[0] || user?.user?.split(' ')[0] || 'Alex';

  const handleAction = (label: string) => {
    notify(`Sprint 2 feature: "${label}" workflow will be enabled in next sprint!`, 'info');
  };

  return (
    <AppShell role="student" notify={notify}>
      <PageHeading
        eyebrow="Student & Candidate Portal"
        title={`Good morning, ${userName}.`}
        description="You are building a stronger case for yourself, one small action at a time."
        action={
          <button
            type="button"
            onClick={() => handleAction('Practice Now')}
            data-testid="button-dashboard-practice"
            className="inline-flex items-center gap-2 rounded-xl bg-[#e2f0e9] px-4 py-2.5 text-sm font-bold text-[#277254] hover:bg-[#d2e7dc] transition"
          >
            <Play size={16} /> Practice now
          </button>
        }
      />

      {/* 4 Metric Cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Presentation score"
          value="82"
          detail="+8 points this month"
          icon={Presentation}
          accent="yellow"
        />
        <StatCard
          label="CV score"
          value="87"
          detail="Strong role alignment"
          icon={FileText}
          accent="green"
        />
        <StatCard
          label="Practice attempts"
          value="12"
          detail="3 this week"
          icon={Target}
          accent="blue"
        />
        <StatCard
          label="Applications"
          value="5"
          detail="2 in review"
          icon={BriefcaseBusiness}
          accent="coral"
        />
      </div>

      {/* Confidence Chart & AI Recommendation */}
      <div className="mt-5 grid gap-5 xl:grid-cols-[1.35fr_.65fr]">
        <section className="cf-card rounded-2xl bg-white p-5 md:p-6 border border-[#d9dbd1] shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="font-bold text-[#253142] text-lg">Confidence over time</h2>
              <p className="mt-1 text-xs text-[#7b8490]">Your average practice take score</p>
            </div>
            <button
              type="button"
              onClick={() => handleAction('View Progress')}
              data-testid="link-dashboard-progress"
              className="flex items-center gap-1 text-xs font-bold text-[#277254] hover:underline"
            >
              View progress <ChevronRight size={14} />
            </button>
          </div>
          <div className="mt-6">
            <Chart
              values={[51, 58, 61, 64, 69, 72, 77, 82]}
              labels={['Apr 1', 'Apr 8', 'Apr 15', 'Apr 22', 'Apr 29', 'May 6', 'May 13', 'Now']}
            />
          </div>
        </section>

        <section className="rounded-2xl bg-[#277254] p-6 text-[#f8f4e9] shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-[.12em] text-[#b9dec6]">
                AI recommendation
              </span>
              <Sparkles size={19} className="text-[#f5c84b]" />
            </div>
            <h2 className="cf-display mt-6 text-2xl font-bold">Make your opening count.</h2>
            <p className="mt-3 text-sm leading-6 text-[#d5e8da]">
              Your answers are thoughtful. Practice a tighter 90-second introduction to land your strongest point sooner.
            </p>
          </div>
          <button
            type="button"
            onClick={() => handleAction('Try this practice')}
            data-testid="button-ai-recommendation"
            className="mt-6 inline-flex w-fit items-center gap-2 rounded-xl bg-[#e2f0e9] px-4 py-2.5 text-xs font-bold text-[#277254] hover:bg-[#d2e7dc] transition"
          >
            Try this practice <ArrowRight size={15} />
          </button>
        </section>
      </div>

      {/* Next Actions & Recent Activity */}
      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <section className="cf-card rounded-2xl bg-white p-5 md:p-6 border border-[#d9dbd1] shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="font-bold text-[#253142] text-lg">Your next actions</h2>
            <button
              type="button"
              onClick={() => handleAction('View all actions')}
              data-testid="button-view-all-actions"
              className="text-xs font-bold text-[#277254] hover:underline"
            >
              View all
            </button>
          </div>
          <div className="mt-4 space-y-2.5">
            <button
              type="button"
              onClick={() => handleAction('Practice introduction')}
              data-testid="action-practice-intro"
              className="flex w-full items-center gap-3 rounded-xl bg-[#fbfaf5] border border-[#eef0e7] p-3.5 text-left hover:bg-[#fff1c9] transition"
            >
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#fff1c9] text-[#8a6a16]">
                <Presentation size={18} />
              </div>
              <div className="flex-1">
                <div className="text-sm font-bold text-[#253142]">Practice your introduction</div>
                <div className="text-xs text-[#7b8490]">8 minutes • Suggested for today</div>
              </div>
              <ChevronRight size={17} className="text-[#9da5ac]" />
            </button>

            <button
              type="button"
              onClick={() => setLocation('/student/cv')}
              data-testid="action-review-cv"
              className="flex w-full items-center gap-3 rounded-xl bg-[#fbfaf5] border border-[#eef0e7] p-3.5 text-left hover:bg-[#e2f0e9] transition"
            >
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#e2f0e9] text-[#277254]">
                <FileText size={18} />
              </div>
              <div className="flex-1">
                <div className="text-sm font-bold text-[#253142]">Review your CV suggestions</div>
                <div className="text-xs text-[#7b8490]">3 improvements waiting in CV Studio</div>
              </div>
              <ChevronRight size={17} className="text-[#9da5ac]" />
            </button>
          </div>
        </section>

        <section className="cf-card rounded-2xl bg-white p-5 md:p-6 border border-[#d9dbd1] shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="font-bold text-[#253142] text-lg">Recent activity</h2>
            <Clock3 size={17} className="text-[#9aa2a9]" />
          </div>
          <div className="mt-4 space-y-4">
            {[
              ['Presentation analyzed', 'Your score moved up to 82', 'Today, 10:42 AM'],
              ['Application submitted', 'Frontend Developer • TechNova Ltd.', 'Yesterday'],
              ['CV reviewed', '87 overall match • 3 suggestions', 'May 16'],
            ].map(([title, subtitle, time]) => (
              <div key={title} className="flex gap-3">
                <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-[#f5c84b]" />
                <div>
                  <div className="text-sm font-bold text-[#253142]">{title}</div>
                  <div className="text-xs text-[#7b8490]">{subtitle}</div>
                  <div className="mt-0.5 text-[10px] font-semibold uppercase tracking-wide text-[#a0a7ad]">
                    {time}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      <DataAccessCard />
    </AppShell>
  );
}
