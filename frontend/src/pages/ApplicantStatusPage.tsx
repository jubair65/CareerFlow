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
  Search,
  X,
  Eye,
  Sliders,
  Check,
  Percent,
  Film,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import { PageHeading, type Notify } from '../components/dashboard/DashboardShared';
import {
  apiGetMyApplications,
  apiGetMyApplicationDetail,
  apiGetMyApplicationStatuses,
  type ApplicantApplicationStatus,
  type ApplicationStage,
} from '../api/recruitment';

export function ApplicantStatusPage({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();
  const [applications, setApplications] = useState<ApplicantApplicationStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterTab, setFilterTab] = useState<'all' | 'shortlisted' | 'review' | 'rejected'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedLogs, setExpandedLogs] = useState<Record<number, boolean>>({});
  const [selectedAppModal, setSelectedAppModal] = useState<ApplicantApplicationStatus | null>(null);
  const [modalLoading, setModalLoading] = useState(false);

  const fetchApplications = async () => {
    try {
      setLoading(true);
      // Primary: US-43 Candidate Applications endpoint
      const data = await apiGetMyApplications();
      setApplications(data);
    } catch {
      try {
        // Fallback: US-35 Status endpoint
        const fallbackData = await apiGetMyApplicationStatuses();
        setApplications(fallbackData);
      } catch {
        notify('Unable to load application statuses. Please try again.', 'error');
      }
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

  const handleOpenDetailModal = async (app: ApplicantApplicationStatus) => {
    setSelectedAppModal(app);
    setModalLoading(true);
    try {
      const freshDetail = await apiGetMyApplicationDetail(app.id);
      setSelectedAppModal(freshDetail);
    } catch {
      // Keep displaying the clicked application data if fresh fetch fails
    } finally {
      setModalLoading(false);
    }
  };

  const handleCloseDetailModal = () => {
    setSelectedAppModal(null);
  };

  // Counts & Metrics
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

    const scoredApps = applications.filter((a) => a.final_score !== null && a.final_score !== undefined);
    const avgScore =
      scoredApps.length > 0
        ? Math.round(
            scoredApps.reduce((acc, a) => acc + Number(a.final_score), 0) / scoredApps.length
          )
        : null;

    return {
      total,
      shortlisted,
      rejected,
      review: Math.max(0, review),
      avgScore,
    };
  }, [applications]);

  // Filtered applications based on tabs and search query
  const filteredApps = useMemo(() => {
    return applications.filter((app) => {
      // Status filter
      if (filterTab === 'shortlisted') {
        const isShortlisted =
          app.is_shortlisted ||
          app.hr_decision === 'CONFIRMED' ||
          (app.hr_decision === 'OVERRIDDEN' && app.is_shortlisted);
        if (!isShortlisted) return false;
      } else if (filterTab === 'rejected') {
        if (app.hr_decision !== 'REJECTED') return false;
      } else if (filterTab === 'review') {
        const isShortlisted =
          app.is_shortlisted ||
          app.hr_decision === 'CONFIRMED' ||
          (app.hr_decision === 'OVERRIDDEN' && app.is_shortlisted);
        if (isShortlisted || app.hr_decision === 'REJECTED') return false;
      }

      // Keyword search query
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase().trim();
        const matchTitle = app.room_title?.toLowerCase().includes(query) ?? false;
        const matchCompany = app.company_name?.toLowerCase().includes(query) ?? false;
        const matchDept = app.room_department?.toLowerCase().includes(query) ?? false;
        const matchCategory = app.room_role_category?.toLowerCase().includes(query) ?? false;
        if (!matchTitle && !matchCompany && !matchDept && !matchCategory) {
          return false;
        }
      }

      return true;
    });
  }, [applications, filterTab, searchQuery]);

  const formatDate = (isoString: string | null | undefined) => {
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

  const formatFileSize = (bytes?: number | null) => {
    if (!bytes || bytes <= 0) return 'Standard file';
    if (bytes < 1024 * 1024) {
      return `${Math.round(bytes / 1024)} KB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDuration = (seconds?: number | null) => {
    if (!seconds || seconds <= 0) return 'Recorded clip';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    if (mins === 0) return `${secs}s`;
    return `${mins}m ${secs}s`;
  };

  const renderBadge = (app: ApplicantApplicationStatus) => {
    const isShortlisted =
      app.is_shortlisted ||
      app.hr_decision === 'CONFIRMED' ||
      (app.hr_decision === 'OVERRIDDEN' && app.is_shortlisted);
    const isRejected = app.hr_decision === 'REJECTED';

    if (isShortlisted) {
      return (
        <span
          data-testid={`badge-status-shortlisted-${app.id}`}
          className="inline-flex items-center gap-1.5 rounded-full bg-[#e2f0e9] px-3 py-1 text-xs font-bold text-[#277254]"
        >
          <CheckCircle2 size={13} /> Shortlisted
        </span>
      );
    }
    if (isRejected) {
      return (
        <span
          data-testid={`badge-status-rejected-${app.id}`}
          className="inline-flex items-center gap-1.5 rounded-full bg-[#f7e5e1] px-3 py-1 text-xs font-bold text-[#a33d35]"
        >
          <XCircle size={13} /> Not Selected
        </span>
      );
    }
    if (app.hr_decision === 'ON_HOLD') {
      return (
        <span
          data-testid={`badge-status-hold-${app.id}`}
          className="inline-flex items-center gap-1.5 rounded-full bg-[#fff4db] px-3 py-1 text-xs font-bold text-[#966b0a]"
        >
          <Clock size={13} /> Application On Hold
        </span>
      );
    }
    if (app.status === 'ANALYZING') {
      return (
        <span
          data-testid={`badge-status-review-${app.id}`}
          className="inline-flex items-center gap-1.5 rounded-full bg-[#e4edf5] px-3 py-1 text-xs font-bold text-[#3a6384]"
        >
          <Loader2 size={13} className="animate-spin" /> AI Analyzing
        </span>
      );
    }
    return (
      <span
        data-testid={`badge-status-review-${app.id}`}
        className="inline-flex items-center gap-1.5 rounded-full bg-[#e4edf5] px-3 py-1 text-xs font-bold text-[#3a6384]"
      >
        <Clock size={13} /> In HR Review
      </span>
    );
  };

  return (
    <AppShell role="student" notify={notify}>
      <PageHeading
        eyebrow="Candidate Portal • US-43 My Applications Dashboard"
        title="My Applications & Hiring Pipeline"
        description="Track all your submitted recruitment room applications, live evaluation milestones, and hiring committee decisions."
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
              <Video size={14} /> Practice Studio
            </button>
          </div>
        }
      />

      {/* Summary Metrics Cards */}
      <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-5" data-testid="summary-metrics-bar">
        <div className="rounded-2xl border border-[#d9dbd1] bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between text-xs font-bold text-[#7b8490]">
            <span>Total Applied</span>
            <BriefcaseBusiness size={15} className="text-[#253142]" />
          </div>
          <div className="mt-2 text-2xl font-black text-[#253142]" data-testid="metric-total-applications">
            {counts.total}
          </div>
          <div className="mt-0.5 text-[11px] text-[#7b8490]">Active submissions</div>
        </div>

        <div className="rounded-2xl border border-[#c5d8ce] bg-[#f8fbf9] p-4 shadow-xs">
          <div className="flex items-center justify-between text-xs font-bold text-[#277254]">
            <span>Shortlisted</span>
            <Award size={15} className="text-[#277254]" />
          </div>
          <div className="mt-2 text-2xl font-black text-[#277254]" data-testid="metric-shortlisted-applications">
            {counts.shortlisted}
          </div>
          <div className="mt-0.5 text-[11px] text-[#277254]/80">Qualified candidates</div>
        </div>

        <div className="rounded-2xl border border-[#f2d89b] bg-[#fffcf5] p-4 shadow-xs">
          <div className="flex items-center justify-between text-xs font-bold text-[#966b0a]">
            <span>In Review</span>
            <Clock size={15} className="text-[#966b0a]" />
          </div>
          <div className="mt-2 text-2xl font-black text-[#966b0a]" data-testid="metric-review-applications">
            {counts.review}
          </div>
          <div className="mt-0.5 text-[11px] text-[#966b0a]/80">Committee evaluation</div>
        </div>

        <div className="rounded-2xl border border-[#f3cec7] bg-[#fdf8f7] p-4 shadow-xs">
          <div className="flex items-center justify-between text-xs font-bold text-[#a33d35]">
            <span>Not Selected</span>
            <XCircle size={15} className="text-[#a33d35]" />
          </div>
          <div className="mt-2 text-2xl font-black text-[#a33d35]" data-testid="metric-rejected-applications">
            {counts.rejected}
          </div>
          <div className="mt-0.5 text-[11px] text-[#a33d35]/80">Closed reviews</div>
        </div>

        <div className="col-span-2 sm:col-span-1 rounded-2xl border border-[#dedfd6] bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between text-xs font-bold text-[#7b8490]">
            <span>Average Score</span>
            <Sparkles size={15} className="text-[#f5c84b]" />
          </div>
          <div className="mt-2 text-2xl font-black text-[#253142]" data-testid="metric-average-score">
            {counts.avgScore !== null ? `${counts.avgScore}%` : '—'}
          </div>
          <div className="mt-0.5 text-[11px] text-[#7b8490]">Composite benchmark</div>
        </div>
      </div>

      {/* Search and Filters Bar */}
      <div className="mt-6 flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#dedfd6] pb-4">
        {/* Filter Tabs */}
        <div className="flex flex-wrap items-center gap-2" data-testid="status-filter-tabs">
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
            <span
              className={`rounded-full px-1.5 py-0.2 text-[10px] ${
                filterTab === 'all' ? 'bg-[#f5c84b] text-[#253142]' : 'bg-[#eef0e7] text-[#253142]'
              }`}
            >
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
            <span
              className={`rounded-full px-1.5 py-0.2 text-[10px] ${
                filterTab === 'shortlisted' ? 'bg-white text-[#277254]' : 'bg-[#e2f0e9] text-[#277254]'
              }`}
            >
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
            <span
              className={`rounded-full px-1.5 py-0.2 text-[10px] ${
                filterTab === 'review' ? 'bg-white text-[#3a6384]' : 'bg-[#e4edf5] text-[#3a6384]'
              }`}
            >
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
            <span
              className={`rounded-full px-1.5 py-0.2 text-[10px] ${
                filterTab === 'rejected' ? 'bg-white text-[#a33d35]' : 'bg-[#f7e5e1] text-[#a33d35]'
              }`}
            >
              {counts.rejected}
            </span>
          </button>
        </div>

        {/* Search Input Box */}
        <div className="relative w-full sm:w-72">
          <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#7b8490]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search role or company..."
            data-testid="input-search-applications"
            className="w-full rounded-xl border border-[#d9dbd1] bg-white pl-9 pr-8 py-2 text-xs text-[#253142] placeholder-[#7b8490] focus:border-[#277254] focus:outline-hidden transition shadow-xs"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => setSearchQuery('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#7b8490] hover:text-[#253142] cursor-pointer"
            >
              <X size={13} />
            </button>
          )}
        </div>
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
        <div
          className="mt-8 flex flex-col items-center justify-center rounded-2xl border border-dashed border-[#c8cac0] bg-white p-12 text-center"
          data-testid="empty-applications-state"
        >
          <div className="grid h-14 w-14 place-items-center rounded-2xl bg-[#eef0e7] text-[#526072] mb-4">
            <BriefcaseBusiness size={28} />
          </div>
          <h3 className="text-base font-bold text-[#253142]">No applications found</h3>
          <p className="mt-1 max-w-md text-xs text-[#7b8490]">
            {searchQuery
              ? `No application matches your search query "${searchQuery}". Try a different keyword.`
              : filterTab === 'all'
              ? "You haven't submitted applications to any recruitment rooms yet. Complete an application or sharpen your presentation skills in the studio."
              : `No applications match the '${filterTab}' filter criteria.`}
          </p>
          <div className="mt-5 flex items-center gap-3">
            {searchQuery ? (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="inline-flex items-center gap-2 rounded-xl bg-[#253142] px-4 py-2.5 text-xs font-bold text-white hover:bg-[#33435a] transition cursor-pointer"
              >
                Clear Search Filter
              </button>
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => setLocation('/student/practice')}
                  data-testid="empty-action-practice"
                  className="inline-flex items-center gap-2 rounded-xl bg-[#253142] px-4 py-2.5 text-xs font-bold text-white hover:bg-[#33435a] transition cursor-pointer"
                >
                  <Video size={14} /> Open Practice Studio
                </button>
                <button
                  type="button"
                  onClick={() => setLocation('/student/cv')}
                  data-testid="empty-action-cv"
                  className="inline-flex items-center gap-2 rounded-xl border border-[#d9dbd1] bg-white px-4 py-2.5 text-xs font-bold text-[#253142] hover:bg-[#f8f7f2] transition cursor-pointer"
                >
                  <FileText size={14} /> Review CV Studio
                </button>
              </>
            )}
          </div>
        </div>
      ) : (
        <div className="mt-6 space-y-6" data-testid="applications-status-list">
          {filteredApps.map((app) => {
            const isShortlisted =
              app.is_shortlisted ||
              app.hr_decision === 'CONFIRMED' ||
              (app.hr_decision === 'OVERRIDDEN' && app.is_shortlisted);
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
                      {renderBadge(app)}
                      {app.room_experience_level && (
                        <span className="rounded-md border border-[#d9dbd1] bg-white px-2 py-0.5 text-[10px] font-bold text-[#526072] uppercase tracking-wider">
                          {app.room_experience_level}
                        </span>
                      )}
                    </div>
                    <div className="mt-1 flex flex-wrap items-center gap-4 text-xs text-[#7b8490]">
                      <span className="flex items-center gap-1 font-medium text-[#253142]">
                        <Building2 size={13} className="text-[#526072]" /> {app.company_name}
                      </span>
                      {app.room_department && <span>• {app.room_department}</span>}
                      {app.room_role_category && <span>• {app.room_role_category}</span>}
                      <span className="flex items-center gap-1">
                        <Calendar size={13} /> Applied on {formatDate(app.applied_at)}
                      </span>
                    </div>
                  </div>

                  {/* Score Pill if available */}
                  {app.final_score !== null && (
                    <div className="mt-4 sm:mt-0 flex items-center gap-3">
                      <div className="rounded-xl border border-[#d9dbd1] bg-white px-3.5 py-1.5 text-right shadow-xs">
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
                    {app.stages.map((stage) => {
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

                  {/* Multi-modal Submission Artifacts & Signals */}
                  <div className="mt-5 grid gap-4 sm:grid-cols-2">
                    {/* Multi-Modal Artifact Details (US-43-T4) */}
                    <div className="rounded-xl border border-[#dedfd6] bg-[#fcfbf9] p-4">
                      <div className="flex items-center justify-between text-xs font-bold text-[#253142]">
                        <span className="flex items-center gap-2">
                          <Sparkles size={14} className="text-[#f5c84b]" /> Submitted Artifacts
                        </span>
                        {app.cv_weight !== undefined && app.video_weight !== undefined && (
                          <span className="text-[10px] font-normal text-[#7b8490]">
                            Weight: {app.cv_weight}% CV • {app.video_weight}% Video
                          </span>
                        )}
                      </div>
                      <div className="mt-3 grid grid-cols-2 gap-3 text-xs">
                        <div className="rounded-lg bg-white p-2.5 border border-[#e5e7eb]">
                          <div className="flex items-center gap-1.5 text-[10px] font-bold text-[#526072]">
                            <FileText size={12} className="text-[#277254]" /> CV Match
                          </div>
                          <div className="mt-1 font-bold text-[#253142] truncate">
                            {app.cv_details?.original_filename || 'CV Document'}
                          </div>
                          <div className="mt-0.5 text-[10px] text-[#7b8490]">
                            {app.cv_score !== null ? `${Math.round(app.cv_score)}/100 match` : 'Analysis pending'}
                          </div>
                        </div>
                        <div className="rounded-lg bg-white p-2.5 border border-[#e5e7eb]">
                          <div className="flex items-center gap-1.5 text-[10px] font-bold text-[#526072]">
                            <Film size={12} className="text-[#3a6384]" /> Video Pitch
                          </div>
                          <div className="mt-1 font-bold text-[#253142] truncate">
                            {app.video_details?.original_filename || 'Video Pitch'}
                          </div>
                          <div className="mt-0.5 text-[10px] text-[#7b8490]">
                            {app.video_score !== null ? `${Math.round(app.video_score)}/100 delivery` : 'Analysis pending'}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Hiring Committee Notes / Shortlist Reason */}
                    <div className="rounded-xl border border-[#dedfd6] bg-[#fcfbf9] p-4">
                      <div className="flex items-center gap-2 text-xs font-bold text-[#253142]">
                        <FileText size={14} className="text-[#3a6384]" /> Hiring Feedback & Decisions
                      </div>
                      <p className="mt-2 text-xs text-[#526072] leading-relaxed">
                        {app.hr_decision_notes ||
                          app.shortlist_reason ||
                          (isShortlisted
                            ? 'Shortlisted by the recruitment committee. The hiring team will reach out with interview schedules.'
                            : 'Your application is progressing through automated evaluation.')}
                      </p>
                    </div>
                  </div>

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
                        Notification Audit Log ({app.notification_logs.length} event
                        {app.notification_logs.length === 1 ? '' : 's'})
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
                                  <Mail
                                    size={12}
                                    className={log.email_sent ? 'text-[#277254]' : 'text-[#7b8490]'}
                                  />
                                  <span className="font-bold text-[#253142]">
                                    {log.status_type_display}
                                  </span>
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
                  <div className="flex items-center gap-4">
                    <button
                      type="button"
                      onClick={() => handleOpenDetailModal(app)}
                      data-testid={`button-view-details-${app.id}`}
                      className="inline-flex items-center gap-1.5 font-bold text-[#253142] hover:text-[#277254] transition cursor-pointer"
                    >
                      <Eye size={13} /> View Dossier Details
                    </button>
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

      {/* Application Detail Modal (US-43-T4) */}
      {selectedAppModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs animate-in fade-in duration-150"
          data-testid="modal-application-detail"
        >
          <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-3xl border border-[#d9dbd1] bg-white shadow-2xl">
            {/* Modal Header */}
            <div className="sticky top-0 z-10 flex items-center justify-between border-b border-[#dedfd6] bg-white/95 px-6 py-4 backdrop-blur-md">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-bold text-[#253142]" data-testid="modal-room-title">
                    {selectedAppModal.room_title}
                  </h3>
                  {renderBadge(selectedAppModal)}
                </div>
                <div className="mt-0.5 flex items-center gap-2 text-xs text-[#7b8490]">
                  <span className="font-semibold text-[#253142]">{selectedAppModal.company_name}</span>
                  {selectedAppModal.room_department && <span>• {selectedAppModal.room_department}</span>}
                  {selectedAppModal.room_role_category && <span>• {selectedAppModal.room_role_category}</span>}
                </div>
              </div>
              <button
                type="button"
                onClick={handleCloseDetailModal}
                data-testid="button-close-detail-modal"
                className="grid h-8 w-8 place-items-center rounded-xl border border-[#d9dbd1] text-[#7b8490] hover:bg-[#f8f7f2] hover:text-[#253142] transition cursor-pointer"
              >
                <X size={16} />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-6">
              {modalLoading && (
                <div className="flex items-center justify-center gap-2 rounded-xl bg-[#f8fbf9] p-3 text-xs text-[#277254]">
                  <Loader2 size={14} className="animate-spin" /> Synchronizing application records...
                </div>
              )}

              {/* Evaluation Scoring Overview */}
              <div className="rounded-2xl border border-[#dedfd6] bg-[#faf9f5] p-5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#7b8490]">
                    <Sliders size={14} className="text-[#277254]" /> Evaluation Model & Weights
                  </div>
                  {selectedAppModal.final_score !== null && (
                    <div className="flex items-baseline gap-1">
                      <span className="text-[10px] font-bold text-[#7b8490] uppercase">Composite Score:</span>
                      <span className="text-lg font-black text-[#253142]">
                        {Math.round(selectedAppModal.final_score)}/100
                      </span>
                    </div>
                  )}
                </div>

                <div className="mt-4 grid grid-cols-2 gap-4">
                  <div className="rounded-xl border border-[#dedfd6] bg-white p-3.5 shadow-xs">
                    <div className="flex items-center justify-between text-xs text-[#7b8490]">
                      <span className="font-bold text-[#253142]">CV Skill Weight</span>
                      <span className="font-bold text-[#277254]">{selectedAppModal.cv_weight ?? 50}%</span>
                    </div>
                    <div className="mt-2 text-sm font-bold text-[#253142]">
                      {selectedAppModal.cv_score !== null
                        ? `${Math.round(selectedAppModal.cv_score)}/100`
                        : 'Score pending'}
                    </div>
                    <div className="mt-1 text-[10px] text-[#7b8490]">
                      Automated parsing against job requirements
                    </div>
                  </div>

                  <div className="rounded-xl border border-[#dedfd6] bg-white p-3.5 shadow-xs">
                    <div className="flex items-center justify-between text-xs text-[#7b8490]">
                      <span className="font-bold text-[#253142]">Video Pitch Weight</span>
                      <span className="font-bold text-[#3a6384]">{selectedAppModal.video_weight ?? 50}%</span>
                    </div>
                    <div className="mt-2 text-sm font-bold text-[#253142]">
                      {selectedAppModal.video_score !== null
                        ? `${Math.round(selectedAppModal.video_score)}/100`
                        : 'Score pending'}
                    </div>
                    <div className="mt-1 text-[10px] text-[#7b8490]">
                      Multi-modal speech & behavioral delivery
                    </div>
                  </div>
                </div>
              </div>

              {/* Submitted Artifact Details (US-43-T4) */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-[#7b8490] mb-3">
                  Submitted Candidate Artifacts
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {/* CV Details */}
                  <div className="rounded-xl border border-[#dedfd6] bg-white p-4 shadow-xs">
                    <div className="flex items-center gap-2">
                      <div className="grid h-8 w-8 place-items-center rounded-lg bg-[#e2f0e9] text-[#277254]">
                        <FileText size={16} />
                      </div>
                      <div className="flex-1 truncate">
                        <div className="text-xs font-bold text-[#253142] truncate">
                          {selectedAppModal.cv_details?.original_filename || 'Candidate Resume'}
                        </div>
                        <div className="text-[10px] text-[#7b8490]">
                          {formatFileSize(selectedAppModal.cv_details?.file_size)} • {selectedAppModal.cv_details?.file_type?.toUpperCase() || 'PDF'}
                        </div>
                      </div>
                    </div>
                    <div className="mt-3 flex items-center justify-between border-t border-[#eceee7] pt-2 text-[11px]">
                      <span className="text-[#7b8490]">Submitted</span>
                      <span className="font-medium text-[#253142]">
                        {formatDate(selectedAppModal.cv_details?.uploaded_at || selectedAppModal.applied_at)}
                      </span>
                    </div>
                  </div>

                  {/* Video Details */}
                  <div className="rounded-xl border border-[#dedfd6] bg-white p-4 shadow-xs">
                    <div className="flex items-center gap-2">
                      <div className="grid h-8 w-8 place-items-center rounded-lg bg-[#e4edf5] text-[#3a6384]">
                        <Film size={16} />
                      </div>
                      <div className="flex-1 truncate">
                        <div className="text-xs font-bold text-[#253142] truncate">
                          {selectedAppModal.video_details?.original_filename || 'Video Pitch'}
                        </div>
                        <div className="text-[10px] text-[#7b8490]">
                          Duration: {formatDuration(selectedAppModal.video_details?.duration_seconds)}
                        </div>
                      </div>
                    </div>
                    <div className="mt-3 flex items-center justify-between border-t border-[#eceee7] pt-2 text-[11px]">
                      <span className="text-[#7b8490]">Processing Status</span>
                      <span className="font-medium text-[#277254]">
                        {selectedAppModal.video_details?.status || 'COMPLETED'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Progress Milestones Stepper */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-[#7b8490] mb-3">
                  Application Milestones Timeline
                </h4>
                <div className="space-y-2.5">
                  {selectedAppModal.stages.map((stage) => (
                    <div
                      key={stage.key}
                      className={`flex items-start gap-3 rounded-xl border p-3 ${
                        stage.is_completed
                          ? 'border-[#c5d8ce] bg-[#f8fbf9]'
                          : stage.is_active
                          ? 'border-[#f2d89b] bg-[#fffcf5]'
                          : 'border-[#dedfd6] bg-white opacity-70'
                      }`}
                    >
                      <div
                        className={`grid h-6 w-6 place-items-center rounded-full text-xs font-bold border shrink-0 mt-0.5 ${
                          stage.is_completed
                            ? 'bg-[#e2f0e9] text-[#277254] border-[#277254]'
                            : stage.is_active
                            ? 'bg-[#fff4db] text-[#966b0a] border-[#f5c84b]'
                            : 'bg-[#f0f1ec] text-[#7b8490] border-[#d9dbd1]'
                        }`}
                      >
                        {stage.is_completed ? <Check size={12} /> : stage.stage}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-[#253142]">{stage.title}</span>
                          <span className="text-[10px] text-[#7b8490]">
                            {stage.timestamp ? formatDate(stage.timestamp) : 'In queue'}
                          </span>
                        </div>
                        <p className="mt-0.5 text-[11px] text-[#526072]">{stage.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Hiring Committee Decision & Feedback */}
              {(selectedAppModal.hr_decision_notes || selectedAppModal.shortlist_reason) && (
                <div className="rounded-2xl border border-[#dedfd6] bg-[#fcfbf9] p-4">
                  <div className="flex items-center gap-2 text-xs font-bold text-[#253142]">
                    <FileText size={14} className="text-[#3a6384]" /> Hiring Committee Feedback
                  </div>
                  {selectedAppModal.shortlist_reason && (
                    <div className="mt-2 text-xs text-[#526072]">
                      <span className="font-bold text-[#253142]">Shortlist Note: </span>
                      {selectedAppModal.shortlist_reason}
                    </div>
                  )}
                  {selectedAppModal.hr_decision_notes && (
                    <div className="mt-1 text-xs text-[#526072]">
                      <span className="font-bold text-[#253142]">Review Feedback: </span>
                      {selectedAppModal.hr_decision_notes}
                    </div>
                  )}
                </div>
              )}

              {/* Room Job Context if available */}
              {selectedAppModal.room_description && (
                <div className="rounded-2xl border border-[#dedfd6] bg-white p-4">
                  <div className="text-xs font-bold text-[#253142] mb-1">Role Description</div>
                  <p className="text-xs text-[#526072] leading-relaxed line-clamp-3">
                    {selectedAppModal.room_description}
                  </p>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="sticky bottom-0 z-10 flex items-center justify-between border-t border-[#dedfd6] bg-[#faf9f5] px-6 py-4">
              <button
                type="button"
                onClick={() => {
                  handleCloseDetailModal();
                  setLocation('/student/practice');
                }}
                className="inline-flex items-center gap-2 rounded-xl bg-[#277254] px-4 py-2 text-xs font-bold text-white hover:bg-[#1f5b43] transition cursor-pointer"
              >
                <Video size={14} /> Practice Pitch for this Role
              </button>
              <button
                type="button"
                onClick={handleCloseDetailModal}
                className="rounded-xl border border-[#d9dbd1] bg-white px-4 py-2 text-xs font-bold text-[#253142] hover:bg-[#f8f7f2] transition cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
