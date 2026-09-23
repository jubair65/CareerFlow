import { useState, useEffect, useMemo } from 'react';
import {
  FolderOpen,
  Users,
  Star,
  Gauge,
  Plus,
  ArrowRight,
  ChevronRight,
  Eye,
  CheckCircle2,
  XCircle,
  FileText,
  X,
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
import { apiGetHRMatches, type CVJobMatch } from '../api/cv';

export function HrDashboard({ notify }: { notify: Notify }) {
  const [hrMatches, setHrMatches] = useState<CVJobMatch[]>([]);
  const [selectedMatch, setSelectedMatch] = useState<CVJobMatch | null>(null);

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
  }, []);

  const handleAction = (label: string) => {
    notify(`Workflow "${label}" activated in HR workspace!`, 'info');
  };

  return (
    <AppShell role="hr" notify={notify}>
      <PageHeading
        eyebrow="HR Hiring Portal • US-09 CV Intelligence"
        title={`Good morning, ${userName}.`}
        description="Your hiring workspace is ready for candidate evaluation and CV match scoring."
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
          value={hrMatches.length > 0 ? `${hrMatches.length}` : "48"}
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
          label="Average CV Match"
          value={
            hrMatches.length > 0
              ? `${Math.round(hrMatches.reduce((acc, m) => acc + m.match_score, 0) / hrMatches.length)}`
              : "82.4"
          }
          detail="US-09 Semantic score"
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
                  US-09 Semantic Signal
                </div>
                <div className="cf-display mt-2 text-4xl font-bold">
                  {hrMatches.filter((m) => m.match_score >= 75).length || 11} ready
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
            onClick={() => handleAction('Review Shortlist')}
            data-testid="button-view-shortlisted-dashboard"
            className="mt-5 inline-flex w-fit items-center gap-2 rounded-xl bg-[#303e50] px-4 py-2.5 text-xs font-bold text-[#f5c84b] hover:bg-[#3b4c62] transition"
          >
            Review shortlist <ArrowRight size={15} />
          </button>
        </section>
      </div>

      {/* Recent Applications Table with US-09 CV Match Scores */}
      <section className="cf-card mt-5 overflow-hidden rounded-2xl bg-white border border-[#d9dbd1] shadow-sm">
        <div className="flex items-center justify-between p-5 border-b border-[#eef0e7]">
          <div>
            <h2 className="font-bold text-[#253142] text-lg">Candidate CV Match Scores (US-09)</h2>
            <p className="text-xs text-[#7b8490]">Real-time semantic similarity and skill coverage evaluation</p>
          </div>
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
          <table className="cf-table w-full text-left text-sm" data-testid="table-hr-applicants">
            <thead className="bg-[#fbfaf5] border-b border-[#eef0e7] text-xs font-semibold text-[#7b8490] uppercase tracking-wider">
              <tr>
                <th className="px-5 py-3.5">Candidate</th>
                <th className="px-5 py-3.5">Target Role</th>
                <th className="px-5 py-3.5">CV Match Score</th>
                <th className="px-5 py-3.5">Keyword Coverage</th>
                <th className="px-5 py-3.5">Status</th>
                <th className="px-5 py-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#eef0e7]">
              {hrMatches.length > 0
                ? hrMatches.map((m) => (
                    <tr key={m.id} className="hover:bg-[#fbfaf5] transition" data-testid={`row-applicant-${m.id}`}>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          <div className="grid h-8 w-8 place-items-center rounded-full bg-[#dce8e1] text-xs font-bold text-[#277254]">
                            {(m.candidate_name || m.candidate_email || 'C')
                              .split(' ')
                              .map((x) => x[0])
                              .join('')
                              .toUpperCase()}
                          </div>
                          <div>
                            <div className="font-bold text-[#253142]">{m.candidate_name || m.candidate_email}</div>
                            <div className="text-[11px] text-[#7b8490]">{m.original_filename}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-4 text-sm text-[#687382] font-semibold">{m.job_title}</td>
                      <td className="px-5 py-4">
                        <span className="inline-flex items-center gap-1 rounded-lg bg-[#e2f0e9] px-2.5 py-1 text-xs font-bold text-[#277254]">
                          {m.match_score} / 100
                        </span>
                      </td>
                      <td className="px-5 py-4 text-sm font-semibold text-[#253142]">
                        {m.keyword_coverage}%
                      </td>
                      <td className="px-5 py-4">
                        <Badge tone={m.match_score >= 80 ? 'good' : m.match_score >= 65 ? 'warn' : 'neutral'}>
                          {m.match_score >= 80 ? 'Shortlisted' : 'Under Review'}
                        </Badge>
                      </td>
                      <td className="px-5 py-4 text-right">
                        <button
                          type="button"
                          onClick={() => setSelectedMatch(m)}
                          data-testid={`button-review-applicant-${m.id}`}
                          className="inline-flex items-center gap-1.5 rounded-lg border border-[#ccd0c6] bg-white px-3 py-1.5 text-xs font-bold text-[#253142] hover:bg-[#fffaf0] transition"
                        >
                          <Eye size={13} /> Review Signal
                        </button>
                      </td>
                    </tr>
                  ))
                : candidatesSeed.slice(0, 4).map((c) => (
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
                      <td className="px-5 py-4 font-bold text-[#277254]">{c.overallScore} / 100</td>
                      <td className="px-5 py-4 text-sm font-semibold text-[#253142]">84%</td>
                      <td className="px-5 py-4">
                        <Badge tone={c.status === 'Shortlisted' ? 'good' : c.status === 'Rejected' ? 'bad' : 'warn'}>
                          {c.status}
                        </Badge>
                      </td>
                      <td className="px-5 py-4 text-right">
                        <button
                          type="button"
                          onClick={() => handleAction(`Review candidate ${c.name}`)}
                          className="inline-flex items-center gap-1.5 rounded-lg border border-[#ccd0c6] bg-white px-3 py-1.5 text-xs font-bold text-[#253142] hover:bg-[#fffaf0]"
                        >
                          <Eye size={13} /> Review Signal
                        </button>
                      </td>
                    </tr>
                  ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Candidate Signal Review Modal (matching CareerFlow-Recruitment-Coach design) */}
      {selectedMatch && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#253142]/60 p-4 backdrop-blur-xs">
          <div className="w-full max-w-xl rounded-2xl bg-white p-6 shadow-2xl border border-[#d9dbd1]">
            <div className="flex items-center justify-between pb-4 border-b border-[#eef0e7]">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-[#9a7922]">
                  CANDIDATE CV EVALUATION (US-09)
                </span>
                <h3 className="text-xl font-bold text-[#253142]">
                  {selectedMatch.candidate_name || selectedMatch.candidate_email}
                </h3>
                <p className="text-xs text-[#687382]">{selectedMatch.job_title} · {selectedMatch.company}</p>
              </div>
              <button
                type="button"
                onClick={() => setSelectedMatch(null)}
                data-testid="button-close-review-modal"
                className="grid h-8 w-8 place-items-center rounded-xl bg-[#f4f2e9] text-[#253142] hover:bg-[#e2dfd2]"
              >
                <X size={16} />
              </button>
            </div>

            <div className="mt-5 flex items-center gap-5 rounded-2xl bg-[#253142] p-5 text-[#faf7ef]">
              <div>
                <div className="text-xs uppercase tracking-wider text-[#aab5c0]">CV Match Score</div>
                <div className="cf-display text-5xl font-bold text-[#f5c84b] mt-1">
                  {selectedMatch.match_score}
                </div>
              </div>
              <div className="border-l border-[#3d4d62] pl-5">
                <h4 className="font-bold text-sm text-[#faf7ef]">
                  {selectedMatch.match_score >= 80 ? 'Strong alignment for role' : 'Moderate candidate fit'}
                </h4>
                <p className="text-xs text-[#c4ccd3] mt-1">
                  Keyword coverage: <strong>{selectedMatch.keyword_coverage}%</strong>
                </p>
              </div>
            </div>

            <div className="mt-5 space-y-3 text-xs">
              <div className="font-bold text-[#253142]">Extracted Matched Skills:</div>
              <div className="flex flex-wrap gap-1.5">
                {selectedMatch.skills_matched?.map((s, i) => (
                  <span key={i} className="rounded-lg bg-[#e2f0e9] px-2.5 py-1 font-bold text-[#277254]">
                    ✓ {s}
                  </span>
                ))}
              </div>

              {selectedMatch.skills_missing?.length > 0 && (
                <>
                  <div className="font-bold text-[#253142] mt-3">Missing Role Keywords:</div>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedMatch.skills_missing?.map((s, i) => (
                      <span key={i} className="rounded-lg bg-[#f7e5e1] px-2.5 py-1 font-bold text-[#a33d35]">
                        + {s}
                      </span>
                    ))}
                  </div>
                </>
              )}
            </div>

            <div className="mt-6 pt-4 border-t border-[#eef0e7] flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setSelectedMatch(null)}
                className="rounded-xl border border-[#ccd0c6] px-4 py-2 text-xs font-bold text-[#253142]"
              >
                Close
              </button>
              <button
                type="button"
                onClick={() => {
                  notify(`Candidate ${selectedMatch.candidate_name || selectedMatch.candidate_email} shortlisted!`, 'success');
                  setSelectedMatch(null);
                }}
                data-testid="button-shortlist-candidate"
                className="rounded-xl bg-[#277254] px-4 py-2 text-xs font-bold text-white hover:bg-[#1f5b43]"
              >
                Shortlist Candidate
              </button>
            </div>
          </div>
        </div>
      )}

      <DataAccessCard />
    </AppShell>
  );
}

