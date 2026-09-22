import { useMemo } from 'react';
import {
  Building2,
  FolderOpen,
  Users,
  Sparkles,
  Plus,
  ArrowRight,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import {
  PageHeading,
  StatCard,
  Chart,
  Badge,
  DataAccessCard,
  clientsSeed,
  type Notify,
} from '../components/dashboard/DashboardShared';
import { getStoredUser } from '../api/auth';

export function AgencyDashboard({ notify }: { notify: Notify }) {
  const user = useMemo(() => {
    try {
      return getStoredUser() || JSON.parse(localStorage.getItem('careerflow-session') || '{}');
    } catch {
      return null;
    }
  }, []);

  const userName = user?.full_name?.split(' ')[0] || user?.user?.split(' ')[0] || 'Nadia';
  const activeClients = useMemo(() => clientsSeed.filter((c) => c.status === 'Active').length, []);

  const handleAction = (label: string) => {
    notify(`Sprint 2 feature: "${label}" workflow will be enabled in next sprint!`, 'info');
  };

  return (
    <AppShell role="agency" notify={notify}>
      <PageHeading
        eyebrow="Recruitment Agency Portal"
        title={`Good morning, ${userName}.`}
        description="A clear view across every client company and candidate pipeline."
        action={
          <button
            type="button"
            onClick={() => handleAction('Create Client Room')}
            data-testid="button-agency-create-room"
            className="inline-flex items-center gap-2 rounded-xl bg-[#277254] px-4 py-2.5 text-sm font-bold text-white hover:bg-[#1f5b43] transition shadow-sm"
          >
            <Plus size={16} /> New room
          </button>
        }
      />

      {/* 4 Metric Cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Client companies"
          value={String(clientsSeed.length)}
          detail={`${activeClients} active client contracts`}
          icon={Building2}
          accent="yellow"
        />
        <StatCard
          label="Open rooms"
          value="6"
          detail="Across 3 clients"
          icon={FolderOpen}
          accent="blue"
        />
        <StatCard
          label="Applicants"
          value="126"
          detail="+18 this week"
          icon={Users}
          accent="green"
        />
        <StatCard
          label="AI shortlisted"
          value="24"
          detail="Ready for client review"
          icon={Sparkles}
          accent="coral"
        />
      </div>

      {/* Client Activity Chart & Client Shortlist Card */}
      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <section className="cf-card rounded-2xl bg-white p-5 md:p-6 border border-[#d9dbd1] shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-bold text-[#253142] text-lg">Client activity</h2>
              <p className="mt-1 text-xs text-[#7b8490]">Applicants across your client portfolio</p>
            </div>
            <button
              type="button"
              onClick={() => handleAction('View Agency Reports')}
              data-testid="link-agency-reports"
              className="text-xs font-bold text-[#277254] hover:underline"
            >
              View report
            </button>
          </div>
          <div className="mt-6">
            <Chart
              values={[44, 53, 48, 71, 66, 82, 91]}
              labels={['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']}
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
            <div className="cf-display mt-6 text-5xl font-bold">24</div>
            <p className="mt-3 max-w-sm text-sm leading-6 text-[#d5e8da]">
              AI-assisted candidate matches are waiting for your agency review before they are forwarded to clients.
            </p>
          </div>
          <button
            type="button"
            onClick={() => handleAction('Review Pipeline')}
            data-testid="button-review-pipeline"
            className="mt-6 inline-flex w-fit items-center gap-2 rounded-xl bg-[#e2f0e9] px-4 py-2.5 text-xs font-bold text-[#277254] hover:bg-[#d2e7dc] transition"
          >
            Review pipeline <ArrowRight size={15} />
          </button>
        </section>
      </div>

      {/* Client Companies & Latest Activity */}
      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <section className="cf-card rounded-2xl bg-white p-5 md:p-6 border border-[#d9dbd1] shadow-sm">
          <div className="flex items-center justify-between border-b border-[#eef0e7] pb-3">
            <h2 className="font-bold text-[#253142] text-lg">Client companies</h2>
            <button
              type="button"
              onClick={() => handleAction('Manage Clients')}
              data-testid="link-agency-clients"
              className="text-xs font-bold text-[#277254] hover:underline"
            >
              Manage
            </button>
          </div>
          <div className="mt-4 space-y-2.5">
            {clientsSeed.map((c) => (
              <div
                key={c.id}
                className="flex items-center gap-3 rounded-xl bg-[#fbfaf5] border border-[#eef0e7] p-3"
              >
                <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#e4edf5] text-[#3a6384]">
                  <Building2 size={18} />
                </div>
                <div className="flex-1">
                  <div className="text-sm font-bold text-[#253142]">{c.companyName}</div>
                  <div className="text-xs text-[#7b8490]">{c.industry} • Contact: {c.contactPerson}</div>
                </div>
                <Badge tone={c.status === 'Active' ? 'good' : 'warn'}>{c.status}</Badge>
              </div>
            ))}
          </div>
        </section>

        <section className="cf-card rounded-2xl bg-white p-5 md:p-6 border border-[#d9dbd1] shadow-sm">
          <h2 className="font-bold text-[#253142] text-lg border-b border-[#eef0e7] pb-3">
            Latest agency activity
          </h2>
          <div className="mt-4 space-y-4">
            {[
              'Nusrat Jahan moved to TechNova shortlist',
              'BrightStack room received 4 new applicants',
              'Evaluation report forwarded to Vertex Digital',
            ].map((activity, i) => (
              <div key={activity} className="flex gap-3 text-sm">
                <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-[#f5c84b]" />
                <div>
                  <div className="font-semibold text-[#253142]">{activity}</div>
                  <div className="mt-0.5 text-xs text-[#7b8490]">
                    {i + 1} hour{i ? 's' : ''} ago
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
