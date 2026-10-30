import { useState, useEffect, useMemo } from 'react';
import { useLocation } from 'wouter';
import {
  BriefcaseBusiness,
  Building2,
  Calendar,
  CheckCircle2,
  Clock,
  ChevronRight,
  ChevronDown,
  Sparkles,
  Award,
  Video,
  FileText,
  AlertCircle,
  XCircle,
  ArrowRight,
  Mail,
  Bell,
  RefreshCw,
  Loader2,
  ExternalLink,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import { PageHeading, type Notify } from '../components/dashboard/DashboardShared';
import {
  apiGetMyApplicationStatuses,
  type ApplicantApplicationStatus,
  type ApplicationStage,
} from '../api/recruitment';

export function ApplicantStatusPage({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();
  const [applications, setApplications] = useState<ApplicantApplicationStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterTab, setFilterTab] = useState<'all' | 'shortlisted' | 'review' | 'rejected'>('all');
  const [expandedLogs, setExpandedLogs] = useState<Record<number, boolean>>({});

  const fetchApplications = async () => {
    try {
      setLoading(true);
      const data = await apiGetMyApplicationStatuses();
      setApplications(data);
    } catch {
      notify('Unable to load application statuses. Please try again.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, []);

  const toggleLogs = (appId: number) => {
    setExpandedLogs((prev) => ({ ...prev, [appId]: !prev[appId] }));
  };

  // Counts
  const counts = useMemo(() => {
    const total = applications.length;
    const shortlisted = applications.filter(
      (a) =>
        a.is_shortlisted ||
        a.hr_decision === 'CONFIRMED' ||
        (a.hr_decision === 'OVERRIDDEN' && a.is_shortlisted)
    ).length;
    const rejected = applications.filter((a) => a.hr_decision === 'REJECTED').length;
    const review = total - shortlisted - rejected;
    return { total, shortlisted, rejected, review: Math.max(0, review) };
  }, [applications]);

  // Filtered applications
  const filteredApps = useMemo(() => {
    if (filterTab === 'shortlisted') {
      return applications.filter(
        (a) =>
          a.is_shortlisted ||
          a.hr_decision === 'CONFIRMED' ||
          (a.hr_decision === 'OVERRIDDEN' && a.is_shortlisted)
      );
    }
    if (filterTab === 'rejected') {
      return applications.filter((a) => a.hr_decision === 'REJECTED');
    }
    if (filterTab === 'review') {
      return applications.filter(
        (a) =>
          !a.is_shortlisted &&
          a.hr_decision !== 'CONFIRMED' &&
          a.hr_decision !== 'REJECTED'
      );
    }
    return applications;
  }, [applications, filterTab]);

  const formatDate = (isoString: string | null) => {
    if (!isoString) return 'Pending';
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    } catch {
      return 'Pending';
    }
  };

  return (
    <AppShell role="student" notify={notify}>
      <PageHeading
        eyebrow="Candidate Portal • US-35 Application Tracking"
        title="Application Status & Next Steps"
        description="Transparent, end-to-end milestone tracking for your job applications and HR decisions."
        action={
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={fetchApplications}
              data-testid="button-refresh-applications"
              className="inline-flex items-center gap-2 rounded-xl border border-[#d9dbd1] bg-white px-3.5 py-2 text-xs font-bold text-[#253142] hover:bg-[#f8f7f2] transition shadow-xs cursor-pointer"
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
            </button>
            <button
              type="button"
              onClick={() => setLocation('/student/practice')}
              data-testid="button-practice-from-status"
              className="inline-flex items-center gap-2 rounded-xl bg-[#277254] px-4 py-2 text-xs font-bold text-white hover:bg-[#1f5b43] transition shadow-xs cursor-pointer shrink-0"
            >
              <Video size={14} /> Practice Interview
            </button>
          </div>
        }
      />

      {/* Filter Tabs */}
      <div className="mt-6 flex flex-wrap items-center gap-2 border-b border-[#dedfd6] pb-3" data-testid="status-filter-tabs">
        <button
          type="button"
          onClick={() => setFilterTab('all')}
          data-testid="filter-tab-all"
          className={`flex items-center gap-2 rounded-xl px-3.5 py-2 text-xs font-bold transition cursor-pointer ${
            filterTab === 'all'
              ? 'bg-[#253142] text-[#faf7ef]'
              : 'bg-white text-[#526072] border border-[#d9dbd1] hover:bg-[#eef0e7]'
          }`}
        >
          <span>All Applications</span>
          <span className={`rounded-full px-1.5 py-0.2 text-[10px] ${filterTab === 'all' ? 'bg-[#f5c84b] text-[#253142]' : 'bg-[#eef0e7] text-[#253142]'}`}>
            {counts.total}
          </span>
        </button>

        <button
          type="button"
          onClick={() => setFilterTab('shortlisted')}
          data-testid="filter-tab-shortlisted"
          className={`flex items-center gap-2 rounded-xl px-3.5 py-2 text-xs font-bold transition cursor-pointer ${
            filterTab === 'shortlisted'
              ? 'bg-[#277254] text-white'
              : 'bg-white text-[#277254] border border-[#d9dbd1] hover:bg-[#e2f0e9]'
          }`}
        >
          <Award size={13} />
          <span>Shortlisted</span>
          <span className={`rounded-full px-1.5 py-0.2 text-[10px] ${filterTab === 'shortlisted' ? 'bg-white text-[#277254]' : 'bg-[#e2f0e9] text-[#277254]'}`}>
            {counts.shortlisted}
          </span>
        </button>

        <button
          type="button"
          onClick={() => setFilterTab('review')}
          data-testid="filter-tab-review"
          className={`flex items-center gap-2 rounded-xl px-3.5 py-2 text-xs font-bold transition cursor-pointer ${
            filterTab === 'review'
              ? 'bg-[#3a6384] text-white'
              : 'bg-white text-[#526072] border border-[#d9dbd1] hover:bg-[#e4edf5]'
          }`}
        >
          <Clock size={13} />
          <span>In Review</span>
          <span className={`rounded-full px-1.5 py-0.2 text-[10px] ${filterTab === 'review' ? 'bg-white text-[#3a6384]' : 'bg-[#e4edf5] text-[#3a6384]'}`}>
            {counts.review}
          </span>
        </button>

        <button
          type="button"
          onClick={() => setFilterTab('rejected')}
          data-testid="filter-tab-rejected"
          className={`flex items-center gap-2 rounded-xl px-3.5 py-2 text-xs font-bold transition cursor-pointer ${
            filterTab === 'rejected'
              ? 'bg-[#a33d35] text-white'
              : 'bg-white text-[#526072] border border-[#d9dbd1] hover:bg-[#f7e5e1]'
          }`}
        >
          <XCircle size={13} />
          <span>Not Selected</span>
          <span className={`rounded-full px-1.5 py-0.2 text-[10px] ${filterTab === 'rejected' ? 'bg-white text-[#a33d35]' : 'bg-[#f7e5e1] text-[#a33d35]'}`}>
            {counts.rejected}
          </span>
        </button>
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div className="mt-8 flex h-64 items-center justify-center rounded-2xl border border-[#d9dbd1] bg-white">
          <div className="flex items-center gap-2 text-sm text-[#7b8490]">
            <Loader2 size={18} className="animate-spin text-[#277254]" />
            Loading application records...
          </div>
        </div>
      ) : filteredApps.length === 0 ? (
        <div className="mt-8 flex flex-col items-center justify-center rounded-2xl border border-dashed border-[#c8cac0] bg-white p-12 text-center" data-testid="empty-applications-state">
          <div className="grid h-14 w-14 place-items-center rounded-2xl bg-[#eef0e7] text-[#526072] mb-4">
            <BriefcaseBusiness size={28} />
          </div>
          <h3 className="text-base font-bold text-[#253142]">No applications found</h3>
          <p className="mt-1 max-w-md text-xs text-[#7b8490]">
            {filterTab === 'all'
              ? "You haven't submitted applications to any recruitment rooms yet. Complete an application or sharpen your presentation skills in the studio."
              : `No applications match the '${filterTab}' filter criteria.`}
          </p>
          <div className="mt-5 flex items-center gap-3">
            <button
              type="button"
              onClick={() => setLocation('/student/practice')}
              data-testid="empty-action-practice"
              className="inline-flex items-center gap-2 rounded-xl bg-[#253142] px-4 py-2.5 text-xs font-bold text-white hover:bg-[#33435a] transition"
            >
              <Video size={14} /> Open Practice Studio
            </button>
            <button
              type="button"
              onClick={() => setLocation('/student/cv')}
              data-testid="empty-action-cv"
              className="inline-flex items-center gap-2 rounded-xl border border-[#d9dbd1] bg-white px-4 py-2.5 text-xs font-bold text-[#253142] hover:bg-[#f8f7f2] transition"
            >
              <FileText size={14} /> Review CV Studio
            </button>
          </div>
        </div>
      ) : (
        <div className="mt-6 space-y-6" data-testid="applications-status-list">
          {filteredApps.map((app) => {
            const isShortlisted =
              app.is_shortlisted ||
              app.hr_decision === 'CONFIRMED' ||
              (app.hr_decision === 'OVERRIDDEN' && app.is_shortlisted);
            const isRejected = app.hr_decision === 'REJECTED';
            const hasDecision = app.hr_decision !== 'UNDECIDED';
            const logsOpen = expandedLogs[app.id] ?? false;

            return (
              <div
                key={app.id}
                data-testid={`application-card-${app.id}`}
                className="overflow-hidden rounded-2xl border border-[#d9dbd1] bg-white shadow-xs transition hover:shadow-sm"
              >
                {/* Header & Badges */}
                <div className="border-b border-[#eceee7] bg-[#faf9f5] p-5 sm:flex sm:items-center sm:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="text-lg font-bold text-[#253142]" data-testid={`app-title-${app.id}`}>
                        {app.room_title}
                      </h2>
                      {isShortlisted ? (
                        <span
                          data-testid={`badge-status-shortlisted-${app.id}`}
                          className="inline-flex items-center gap-1.5 rounded-full bg-[#e2f0e9] px-3 py-1 text-xs font-bold text-[#277254]"
                        >
                          <CheckCircle2 size={13} /> Shortlisted
                        </span>
                      ) : isRejected ? (
                        <span
                          data-testid={`badge-status-rejected-${app.id}`}
                          className="inline-flex items-center gap-1.5 rounded-full bg-[#f7e5e1] px-3 py-1 text-xs font-bold text-[#a33d35]"
                        >
                          <XCircle size={13} /> Not Selected
                        </span>
                      ) : app.hr_decision === 'ON_HOLD' ? (
                        <span
                          data-testid={`badge-status-hold-${app.id}`}
                          className="inline-flex items-center gap-1.5 rounded-full bg-[#fff4db] px-3 py-1 text-xs font-bold text-[#966b0a]"
                        >
                          <Clock size={13} /> Application On Hold
                        </span>
                      ) : (
                        <span
                          data-testid={`badge-status-review-${app.id}`}
                          className="inline-flex items-center gap-1.5 rounded-full bg-[#e4edf5] px-3 py-1 text-xs font-bold text-[#3a6384]"
                        >
                          <Clock size={13} /> In HR Review
                        </span>
                      )}
                    </div>
                    <div className="mt-1 flex flex-wrap items-center gap-4 text-xs text-[#7b8490]">
                      <span className="flex items-center gap-1">
                        <Building2 size={13} /> {app.company_name}
                      </span>
                      {app.room_department && (
                        <span>• {app.room_department}</span>
                      )}
                      <span className="flex items-center gap-1">
                        <Calendar size={13} /> Applied on {formatDate(app.applied_at)}
                      </span>
                    </div>
                  </div>

                  {/* Score Pill if available */}
                  {app.final_score !== null && (
                    <div className="mt-4 sm:mt-0 flex items-center gap-3">
                      <div className="rounded-xl border border-[#d9dbd1] bg-white px-3.5 py-1.5 text-right">
                        <div className="text-[10px] font-bold uppercase tracking-wider text-[#7b8490]">
                          Composite Score
                        </div>
                        <div
                          data-testid={`app-final-score-${app.id}`}
                          className="text-base font-black text-[#253142]"
                        >
                          {Math.round(app.final_score)}
                          <span className="text-xs font-normal text-[#7b8490]">/100</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Progress Timeline Stepper */}
                <div className="p-5 sm:p-6">
                  <div className="mb-3 flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-[#7b8490]">
                      Evaluation Milestones
                    </span>
                    <span className="text-xs font-medium text-[#7b8490]">
                      Stage {app.stages.filter((s) => s.is_completed).length} of {app.stages.length} Completed
                    </span>
                  </div>

                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-4 sm:gap-2">
                    {app.stages.map((stage, idx) => {
                      const isComplete = stage.is_completed;
                      const isActive = stage.is_active;

                      let stepColor = 'bg-[#f0f1ec] text-[#7b8490] border-[#d9dbd1]';
                      if (isComplete) {
                        stepColor = 'bg-[#e2f0e9] text-[#277254] border-[#277254]';
                      } else if (isActive) {
                        stepColor = 'bg-[#fff4db] text-[#966b0a] border-[#f5c84b]';
                      }

                      return (
                        <div
                          key={stage.key}
                          data-testid={`stage-${stage.key.toLowerCase()}-${app.id}`}
                          className={`relative rounded-xl border p-3.5 transition ${
                            isComplete
                              ? 'border-[#c5d8ce] bg-[#f8fbf9]'
                              : isActive
                              ? 'border-[#f2d89b] bg-[#fffcf5]'
                              : 'border-[#e2e4dc] bg-[#fafaf7]'
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <div
                              className={`grid h-6 w-6 place-items-center rounded-full text-xs font-bold border ${stepColor}`}
                            >
                              {isComplete ? <CheckCircle2 size={14} /> : stage.stage}
                            </div>
                            <span className="truncate text-xs font-bold text-[#253142]">
                              {stage.title}
                            </span>
                          </div>
                          <p className="mt-1.5 text-[11px] text-[#7b8490] line-clamp-2">
                            {stage.description}
                          </p>
                          <div className="mt-2 text-[10px] font-medium text-[#9ca3af]">
                            {stage.timestamp ? formatDate(stage.timestamp) : 'In queue'}
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Deep Signals & Feedback */}
                  {(app.cv_score !== null || app.video_score !== null || app.hr_decision_notes || app.shortlist_reason) && (
                    <div className="mt-5 grid gap-4 sm:grid-cols-2">
                      {/* Score Breakdown summary */}
                      <div className="rounded-xl border border-[#dedfd6] bg-[#fcfbf9] p-4">
                        <div className="flex items-center gap-2 text-xs font-bold text-[#253142]">
                          <Sparkles size={14} className="text-[#f5c84b]" /> Multi-Modal Signals
                        </div>
                        <div className="mt-3 grid grid-cols-2 gap-3 text-xs">
                          <div className="rounded-lg bg-white p-2.5 border border-[#e5e7eb]">
                            <div className="text-[10px] text-[#7b8490]">CV Skill Match</div>
                            <div className="font-bold text-[#253142]">
                              {app.cv_score !== null ? `${Math.round(app.cv_score)}/100` : 'Pending'}
                            </div>
                          </div>
                          <div className="rounded-lg bg-white p-2.5 border border-[#e5e7eb]">
                            <div className="text-[10px] text-[#7b8490]">Video Presentation</div>
                            <div className="font-bold text-[#253142]">
                              {app.video_score !== null ? `${Math.round(app.video_score)}/100` : 'Pending'}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Review Notes / Advice */}
                      <div className="rounded-xl border border-[#dedfd6] bg-[#fcfbf9] p-4">
                        <div className="flex items-center gap-2 text-xs font-bold text-[#253142]">
                          <FileText size={14} className="text-[#3a6384]" /> Hiring Committee Note
                        </div>
                        <p className="mt-2 text-xs text-[#526072] leading-relaxed">
                          {app.hr_decision_notes ||
                            app.shortlist_reason ||
                            (isShortlisted
                              ? 'Shortlisted for candidate review. The hiring team will be in touch with next steps.'
                              : 'Your application is progressing through automated evaluation.')}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Audit & Notification History Accordion */}
                  <div className="mt-4 border-t border-[#eceee7] pt-3">
                    <button
                      type="button"
                      onClick={() => toggleLogs(app.id)}
                      data-testid={`button-toggle-audit-logs-${app.id}`}
                      className="flex items-center gap-2 text-xs font-bold text-[#526072] hover:text-[#253142] transition cursor-pointer"
                    >
                      <Bell size={13} />
                      <span>
                        Notification Audit Log ({app.notification_logs.length} event{app.notification_logs.length === 1 ? '' : 's'})
                      </span>
                      {logsOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    </button>

                    {logsOpen && (
                      <div
                        data-testid={`audit-logs-container-${app.id}`}
                        className="mt-3 rounded-xl border border-[#dedfd6] bg-[#faf9f5] p-3 text-xs"
                      >
                        {app.notification_logs.length === 0 ? (
                          <div className="text-[11px] text-[#7b8490]">
                            No external status notifications recorded yet.
                          </div>
                        ) : (
                          <div className="space-y-2">
                            {app.notification_logs.map((log) => (
                              <div
                                key={log.id}
                                className="flex items-center justify-between border-b border-[#e5e6df] pb-1.5 last:border-b-0 last:pb-0"
                              >
                                <div className="flex items-center gap-2">
                                  <Mail size={12} className={log.email_sent ? 'text-[#277254]' : 'text-[#7b8490]'} />
                                  <span className="font-bold text-[#253142]">{log.status_type_display}</span>
                                  <span className="text-[11px] text-[#7b8490]">
                                    ({log.email_sent ? 'Email delivered' : 'In-app notification'})
                                  </span>
                                </div>
                                <span className="text-[10px] text-[#9ca3af]">
                                  {formatDate(log.dispatched_at)}
                                </span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* Card Footer Actions */}
                <div className="flex items-center justify-between border-t border-[#dedfd6] bg-[#fbfbfa] px-5 py-3 text-xs">
                  <div className="text-[11px] text-[#7b8490]">
                    Status verified with hiring room records.
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => setLocation('/student/practice')}
                      className="font-bold text-[#277254] hover:underline cursor-pointer"
                    >
                      Practice interview &rarr;
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </AppShell>
  );
}

