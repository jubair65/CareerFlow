import { useState, useEffect, useMemo } from 'react';
import {
  Users,
  Search,
  Building2,
  FolderOpen,
  Sparkles,
  Star,
  CheckCircle2,
  Clock,
  AlertCircle,
  XCircle,
  FileText,
  Video,
  ExternalLink,
  ChevronRight,
  Filter,
  RefreshCw,
  X,
  SlidersHorizontal,
  TrendingUp,
  Percent,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import { PageHeading, StatCard, type Notify } from '../components/dashboard/DashboardShared';
import {
  apiGetAgencyCrossClientApplicants,
  apiGetAgencyCrossClientApplicantStats,
  apiGetAgencyClients,
  apiGetAgencyRooms,
  type AgencyCrossClientApplicant,
  type AgencyCrossClientApplicantStats,
  type ClientCompany,
  type RecruitmentRoom,
} from '../api/recruitment';

export function AgencyApplicantsPipelinePage({ notify }: { notify: Notify }) {
  // Data state
  const [applicants, setApplicants] = useState<AgencyCrossClientApplicant[]>([]);
  const [stats, setStats] = useState<AgencyCrossClientApplicantStats>({
    total_applicants: 0,
    completed_evaluations: 0,
    shortlisted_candidates: 0,
    pending_reviews: 0,
    average_final_score: 0.0,
    clients_count: 0,
    rooms_count: 0,
  });
  const [clients, setClients] = useState<ClientCompany[]>([]);
  const [rooms, setRooms] = useState<RecruitmentRoom[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters state
  const [selectedClientId, setSelectedClientId] = useState<string>('all');
  const [selectedRoomId, setSelectedRoomId] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedShortlist, setSelectedShortlist] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedOrdering, setSelectedOrdering] = useState<string>('-applied_at');

  // Selected applicant for detail modal
  const [detailApplicant, setDetailApplicant] = useState<AgencyCrossClientApplicant | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [applicantsData, statsData, clientsData, roomsData] = await Promise.all([
        apiGetAgencyCrossClientApplicants({
          client_company: selectedClientId !== 'all' ? selectedClientId : undefined,
          room: selectedRoomId !== 'all' ? selectedRoomId : undefined,
          status: selectedStatus !== 'all' ? selectedStatus : undefined,
          shortlisted:
            selectedShortlist === 'shortlisted'
              ? 'true'
              : selectedShortlist === 'non-shortlisted'
              ? 'false'
              : undefined,
          q: searchQuery.trim() || undefined,
          ordering: selectedOrdering,
        }),
        apiGetAgencyCrossClientApplicantStats(),
        apiGetAgencyClients(),
        apiGetAgencyRooms(),
      ]);

      setApplicants(applicantsData);
      setStats(statsData);
      setClients(clientsData);
      setRooms(roomsData);
    } catch {
      notify('Failed to load cross-client applicants pipeline.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedClientId, selectedRoomId, selectedStatus, selectedShortlist, selectedOrdering]);

  // Handle live search debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      apiGetAgencyCrossClientApplicants({
        client_company: selectedClientId !== 'all' ? selectedClientId : undefined,
        room: selectedRoomId !== 'all' ? selectedRoomId : undefined,
        status: selectedStatus !== 'all' ? selectedStatus : undefined,
        shortlisted:
          selectedShortlist === 'shortlisted'
            ? 'true'
            : selectedShortlist === 'non-shortlisted'
            ? 'false'
            : undefined,
        q: searchQuery.trim() || undefined,
        ordering: selectedOrdering,
      })
        .then((data) => setApplicants(data))
        .catch(() => {});
    }, 250);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Filter available rooms based on selected client
  const availableRooms = useMemo(() => {
    if (selectedClientId === 'all') return rooms;
    return rooms.filter((r) => String(r.client_company) === selectedClientId);
  }, [rooms, selectedClientId]);

  const handleResetFilters = () => {
    setSelectedClientId('all');
    setSelectedRoomId('all');
    setSelectedStatus('all');
    setSelectedShortlist('all');
    setSearchQuery('');
    setSelectedOrdering('-applied_at');
  };

  const getScoreBadgeClass = (score: number | null) => {
    if (score === null || score === undefined) {
      return 'bg-[#eef0e7] text-[#7b8490]';
    }
    if (score >= 80) {
      return 'bg-[#e2f0e9] text-[#277254] font-bold border border-[#b9dec6]';
    }
    if (score >= 65) {
      return 'bg-[#e4edf5] text-[#2a557a] font-bold border border-[#b4d2e7]';
    }
    if (score >= 50) {
      return 'bg-[#fbf5e6] text-[#735118] font-bold border border-[#f5c84b]/50';
    }
    return 'bg-[#f7e5e1] text-[#a33d35] font-bold border border-[#f1d6d1]';
  };

  return (
    <AppShell role="agency" notify={notify}>
      <div data-testid="page-agency-applicants" className="space-y-6">
        {/* Page Heading */}
        <PageHeading
          eyebrow="Recruitment Agency • US-31 Cross-Client Pipeline"
          title="Cross-Client Applicant Pipeline"
          description="View, filter, and evaluate candidates across your entire client company portfolio with transparent scores."
          action={
            <button
              type="button"
              onClick={fetchData}
              data-testid="button-refresh-pipeline"
              className="inline-flex items-center gap-2 rounded-xl border border-[#d9dbd1] bg-white px-4 py-2.5 text-xs font-bold text-[#253142] hover:bg-[#eef0e7] transition shadow-2xs"
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh Pipeline
            </button>
          }
        />

        {/* 4 KPI Metric Cards */}
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard
            label="Total Applicants"
            value={String(stats.total_applicants)}
            detail={`Across ${stats.clients_count} clients & ${stats.rooms_count} rooms`}
            icon={Users}
            accent="blue"
          />
          <StatCard
            label="Completed Analyses"
            value={String(stats.completed_evaluations)}
            detail="With calculated scores"
            icon={CheckCircle2}
            accent="green"
          />
          <StatCard
            label="Shortlisted Candidates"
            value={String(stats.shortlisted_candidates)}
            detail="Ready for client forwarding"
            icon={Star}
            accent="coral"
          />
          <StatCard
            label="Average Final Score"
            value={stats.average_final_score > 0 ? `${stats.average_final_score}%` : 'N/A'}
            detail="Overall applicant quality"
            icon={Sparkles}
            accent="yellow"
          />
        </div>

        {/* Filters and Controls Toolbar (US-31-T4) */}
        <div
          data-testid="toolbar-applicant-filters"
          className="rounded-2xl border border-[#d9dbd1] bg-white p-4 shadow-xs space-y-3"
        >
          <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-center">
            {/* Search Input */}
            <div className="sm:col-span-4 relative">
              <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#7b8490]" />
              <input
                type="text"
                data-testid="input-search-applicants"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search candidate name, email, role, or client..."
                className="w-full rounded-xl border border-[#d9dbd1] bg-white pl-9 pr-3.5 py-2 text-xs font-medium text-[#253142] placeholder-[#7b8490]/60 focus:border-[#277254] focus:outline-hidden focus:ring-2 focus:ring-[#277254]/20 transition"
              />
            </div>

            {/* Client Company Filter */}
            <div className="sm:col-span-3">
              <select
                data-testid="select-filter-client"
                value={selectedClientId}
                onChange={(e) => {
                  setSelectedClientId(e.target.value);
                  setSelectedRoomId('all'); // reset room selection when client changes
                }}
                className="w-full rounded-xl border border-[#d9dbd1] bg-white px-3 py-2 text-xs font-semibold text-[#253142] focus:border-[#277254] focus:outline-hidden focus:ring-2 focus:ring-[#277254]/20 transition"
              >
                <option value="all">All Client Companies ({clients.length})</option>
                {clients.map((c) => (
                  <option key={c.id} value={String(c.id)}>
                    {c.name} ({c.industry})
                  </option>
                ))}
              </select>
            </div>

            {/* Room Filter */}
            <div className="sm:col-span-3">
              <select
                data-testid="select-filter-room"
                value={selectedRoomId}
                onChange={(e) => setSelectedRoomId(e.target.value)}
                className="w-full rounded-xl border border-[#d9dbd1] bg-white px-3 py-2 text-xs font-semibold text-[#253142] focus:border-[#277254] focus:outline-hidden focus:ring-2 focus:ring-[#277254]/20 transition"
              >
                <option value="all">All Rooms ({availableRooms.length})</option>
                {availableRooms.map((r) => (
                  <option key={r.id} value={String(r.id)}>
                    {r.title} ({r.company_name})
                  </option>
                ))}
              </select>
            </div>

            {/* Status Filter */}
            <div className="sm:col-span-2">
              <select
                data-testid="select-filter-status"
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="w-full rounded-xl border border-[#d9dbd1] bg-white px-3 py-2 text-xs font-semibold text-[#253142] focus:border-[#277254] focus:outline-hidden focus:ring-2 focus:ring-[#277254]/20 transition"
              >
                <option value="all">All Statuses</option>
                <option value="COMPLETED">Completed</option>
                <option value="ANALYZING">Analyzing</option>
                <option value="PENDING">Pending</option>
                <option value="FAILED">Failed</option>
              </select>
            </div>
          </div>

          {/* Secondary Row: Shortlist & Sorting */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2.5 border-t border-[#eef0e7] text-xs">
            <div className="flex items-center gap-3">
              {/* Shortlist Filter */}
              <div className="flex items-center gap-1.5">
                <span className="font-semibold text-[#526072]">Shortlist:</span>
                <select
                  data-testid="select-filter-shortlist"
                  value={selectedShortlist}
                  onChange={(e) => setSelectedShortlist(e.target.value)}
                  className="rounded-lg border border-[#d9dbd1] bg-white px-2.5 py-1 text-xs font-semibold text-[#253142]"
                >
                  <option value="all">All Candidates</option>
                  <option value="shortlisted">⭐ Shortlisted Only</option>
                  <option value="non-shortlisted">Non-Shortlisted</option>
                </select>
              </div>

              {/* Sorting Filter */}
              <div className="flex items-center gap-1.5">
                <span className="font-semibold text-[#526072]">Sort by:</span>
                <select
                  data-testid="select-sort-ordering"
                  value={selectedOrdering}
                  onChange={(e) => setSelectedOrdering(e.target.value)}
                  className="rounded-lg border border-[#d9dbd1] bg-white px-2.5 py-1 text-xs font-semibold text-[#253142]"
                >
                  <option value="-applied_at">Newest Applications</option>
                  <option value="applied_at">Oldest Applications</option>
                  <option value="-final_score">Highest Final Score</option>
                  <option value="final_score">Lowest Final Score</option>
                  <option value="-cv_score">Highest CV Score</option>
                  <option value="-video_score">Highest Video Score</option>
                </select>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span data-testid="text-pipeline-count" className="text-[#7b8490]">
                Showing <strong>{applicants.length}</strong> applicant records
              </span>
              {(selectedClientId !== 'all' ||
                selectedRoomId !== 'all' ||
                selectedStatus !== 'all' ||
                selectedShortlist !== 'all' ||
                searchQuery.trim() ||
                selectedOrdering !== '-applied_at') && (
                <button
                  type="button"
                  onClick={handleResetFilters}
                  data-testid="button-reset-filters"
                  className="font-bold text-[#277254] hover:underline"
                >
                  Reset filters
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Applicants Table / List View */}
        {loading ? (
          <div className="flex h-64 items-center justify-center rounded-2xl bg-white border border-[#d9dbd1]">
            <div className="flex items-center gap-2 text-sm text-[#7b8490]">
              <Clock size={18} className="animate-spin text-[#277254]" />
              Loading applicant pipeline...
            </div>
          </div>
        ) : applicants.length === 0 ? (
          <div
            data-testid="banner-empty-applicants"
            className="rounded-2xl border border-[#d9dbd1] bg-white p-12 text-center shadow-xs"
          >
            <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-[#eef0e7] text-[#526072]">
              <Users size={28} />
            </div>
            <h3 className="mt-4 text-base font-bold text-[#253142]">No applicant records found</h3>
            <p className="mx-auto mt-1 max-w-sm text-xs text-[#7b8490]">
              {selectedClientId !== 'all' || selectedRoomId !== 'all' || selectedStatus !== 'all' || searchQuery
                ? 'No applications match your active filter criteria. Try clearing or relaxing your filters.'
                : 'Share your recruitment room application links with candidates to start receiving submissions.'}
            </p>
            {(selectedClientId !== 'all' ||
              selectedRoomId !== 'all' ||
              selectedStatus !== 'all' ||
              searchQuery) && (
              <button
                type="button"
                onClick={handleResetFilters}
                className="mt-4 inline-flex items-center gap-1.5 rounded-xl border border-[#d9dbd1] bg-white px-3.5 py-2 text-xs font-bold text-[#277254] hover:bg-[#eef0e7]"
              >
                Clear all filters
              </button>
            )}
          </div>
        ) : (
          <div
            data-testid="container-applicant-table"
            className="rounded-2xl border border-[#d9dbd1] bg-white shadow-xs overflow-hidden"
          >
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[#eef0e7] bg-[#fafaf7] text-[11px] font-bold uppercase tracking-wider text-[#7b8490]">
                    <th className="py-3 px-4">Candidate</th>
                    <th className="py-3 px-4">Client Company</th>
                    <th className="py-3 px-4">Room & Position</th>
                    <th className="py-3 px-3 text-center">CV Score</th>
                    <th className="py-3 px-3 text-center">Video Score</th>
                    <th className="py-3 px-3 text-center">Final Score</th>
                    <th className="py-3 px-4">Status & Shortlist</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#eef0e7]">
                  {applicants.map((app) => {
                    const initials = app.candidate_name
                      .split(' ')
                      .map((n) => n[0])
                      .filter(Boolean)
                      .slice(0, 2)
                      .join('')
                      .toUpperCase();

                    return (
                      <tr
                        key={app.id}
                        data-testid={`applicant-row-${app.id}`}
                        className="hover:bg-[#fafaf7]/80 transition group"
                      >
                        {/* Candidate Name & Email */}
                        <td className="py-3.5 px-4">
                          <div className="flex items-center gap-2.5">
                            <div className="grid h-8 w-8 place-items-center rounded-lg bg-[#e2f0e9] text-[#277254] font-bold text-xs shrink-0">
                              {initials}
                            </div>
                            <div>
                              <div
                                data-testid={`text-candidate-name-${app.id}`}
                                className="font-bold text-[#253142]"
                              >
                                {app.candidate_name}
                              </div>
                              <div
                                data-testid={`text-candidate-email-${app.id}`}
                                className="text-[11px] text-[#7b8490]"
                              >
                                {app.candidate_email}
                              </div>
                            </div>
                          </div>
                        </td>

                        {/* Client Company */}
                        <td className="py-3.5 px-4">
                          <div className="flex items-center gap-1.5 font-bold text-[#253142]" data-testid={`text-client-name-${app.id}`}>
                            <Building2 size={13} className="text-[#277254] shrink-0" />
                            <span>{app.client_company_name}</span>
                          </div>
                          <div className="text-[10px] text-[#7b8490] mt-0.5">
                            {app.client_company_industry}
                          </div>
                        </td>

                        {/* Room & Role Category */}
                        <td className="py-3.5 px-4">
                          <div className="font-semibold text-[#253142]" data-testid={`text-room-title-${app.id}`}>
                            {app.room_title}
                          </div>
                          <div className="flex items-center gap-1.5 mt-0.5">
                            <span className="rounded bg-[#eef0e7] px-1.5 py-0.2 text-[10px] text-[#526072]">
                              {app.role_category}
                            </span>
                            <span className="text-[10px] text-[#7b8490]">
                              {app.experience_level_display || app.experience_level}
                            </span>
                          </div>
                        </td>

                        {/* CV Match Score */}
                        <td className="py-3.5 px-3 text-center">
                          {app.cv_score !== null ? (
                            <span
                              data-testid={`badge-cv-score-${app.id}`}
                              className="font-bold text-[#253142]"
                            >
                              {Math.round(app.cv_score)}%
                            </span>
                          ) : (
                            <span className="text-[#7b8490]">N/A</span>
                          )}
                        </td>

                        {/* Video Presentation Score */}
                        <td className="py-3.5 px-3 text-center">
                          {app.video_score !== null ? (
                            <span
                              data-testid={`badge-video-score-${app.id}`}
                              className="font-bold text-[#253142]"
                            >
                              {Math.round(app.video_score)}%
                            </span>
                          ) : (
                            <span className="text-[#7b8490]">N/A</span>
                          )}
                        </td>

                        {/* Final Weighted Score */}
                        <td className="py-3.5 px-3 text-center">
                          <span
                            data-testid={`badge-final-score-${app.id}`}
                            className={`inline-block px-2 py-0.5 rounded-lg text-xs font-bold ${getScoreBadgeClass(
                              app.final_score
                            )}`}
                          >
                            {app.final_score !== null ? `${Math.round(app.final_score)}%` : 'Pending'}
                          </span>
                        </td>

                        {/* Status & Shortlist Badges */}
                        <td className="py-3.5 px-4">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <span
                              data-testid={`badge-status-${app.id}`}
                              className={`rounded-md px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                                app.status === 'COMPLETED'
                                  ? 'bg-[#e2f0e9] text-[#277254]'
                                  : app.status === 'ANALYZING'
                                  ? 'bg-[#e4edf5] text-[#2a557a]'
                                  : app.status === 'PENDING'
                                  ? 'bg-[#fbf5e6] text-[#735118]'
                                  : 'bg-[#f7e5e1] text-[#a33d35]'
                              }`}
                            >
                              {app.status}
                            </span>
                            {app.is_shortlisted && (
                              <span
                                data-testid={`badge-shortlisted-${app.id}`}
                                className="inline-flex items-center gap-1 rounded-md bg-[#fff1c9] border border-[#f5c84b] px-1.5 py-0.5 text-[10px] font-bold text-[#8a6a16]"
                              >
                                <Star size={10} className="fill-[#8a6a16]" /> Shortlisted
                              </span>
                            )}
                          </div>
                          {app.hr_decision !== 'UNDECIDED' && (
                            <div className="mt-1 text-[10px] text-[#526072] font-semibold">
                              Decision: {app.hr_decision_display || app.hr_decision}
                            </div>
                          )}
                        </td>

                        {/* Actions */}
                        <td className="py-3.5 px-4 text-right">
                          <button
                            type="button"
                            onClick={() => setDetailApplicant(app)}
                            data-testid={`button-view-applicant-${app.id}`}
                            className="inline-flex items-center gap-1 rounded-lg border border-[#d9dbd1] bg-white px-2.5 py-1 text-xs font-bold text-[#253142] hover:bg-[#eef0e7] hover:border-[#253142] transition"
                          >
                            Details <ChevronRight size={13} />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Applicant Details Modal */}
        {detailApplicant && (
          <div
            role="dialog"
            aria-modal="true"
            data-testid="modal-applicant-detail"
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs overflow-y-auto"
          >
            <div className="relative w-full max-w-xl rounded-2xl bg-white p-6 shadow-2xl border border-[#d9dbd1] my-8 animate-in fade-in zoom-in-95 duration-150">
              {/* Header */}
              <div className="flex items-start justify-between border-b border-[#eef0e7] pb-4">
                <div className="flex items-center gap-3">
                  <div className="grid h-11 w-11 place-items-center rounded-xl bg-[#e2f0e9] text-[#277254] font-bold text-base">
                    {detailApplicant.candidate_name
                      .split(' ')
                      .map((n) => n[0])
                      .slice(0, 2)
                      .join('')}
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-[#253142]">
                      {detailApplicant.candidate_name}
                    </h3>
                    <p className="text-xs text-[#7b8490]">{detailApplicant.candidate_email}</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setDetailApplicant(null)}
                  data-testid="button-close-applicant-modal"
                  className="rounded-lg p-1.5 text-[#7b8490] hover:bg-[#eef0e7] hover:text-[#253142] transition"
                >
                  <X size={18} />
                </button>
              </div>

              {/* Target Position & Client info */}
              <div className="mt-4 grid grid-cols-2 gap-3 rounded-xl border border-[#eef0e7] bg-[#fafaf7] p-3.5 text-xs">
                <div>
                  <span className="text-[#7b8490]">Client Company:</span>
                  <div className="font-bold text-[#253142] mt-0.5 flex items-center gap-1">
                    <Building2 size={13} className="text-[#277254]" />
                    {detailApplicant.client_company_name}
                  </div>
                </div>
                <div>
                  <span className="text-[#7b8490]">Opening Position:</span>
                  <div className="font-bold text-[#253142] mt-0.5">
                    {detailApplicant.room_title}
                  </div>
                </div>
              </div>

              {/* Evaluation Scores Breakdown */}
              <div className="mt-4 space-y-2.5">
                <h4 className="text-xs font-bold uppercase tracking-wider text-[#526072]">
                  AI Evaluation Scores
                </h4>
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="rounded-xl border border-[#d9dbd1] p-3 bg-white">
                    <div className="text-[10px] font-semibold text-[#7b8490]">
                      CV Match ({detailApplicant.cv_weight}%)
                    </div>
                    <div className="text-lg font-black text-[#253142] mt-1">
                      {detailApplicant.cv_score !== null ? `${Math.round(detailApplicant.cv_score)}%` : 'N/A'}
                    </div>
                  </div>
                  <div className="rounded-xl border border-[#d9dbd1] p-3 bg-white">
                    <div className="text-[10px] font-semibold text-[#7b8490]">
                      Video ({detailApplicant.video_weight}%)
                    </div>
                    <div className="text-lg font-black text-[#253142] mt-1">
                      {detailApplicant.video_score !== null ? `${Math.round(detailApplicant.video_score)}%` : 'N/A'}
                    </div>
                  </div>
                  <div className="rounded-xl border border-[#277254] bg-[#e2f0e9]/40 p-3">
                    <div className="text-[10px] font-bold text-[#277254]">Final Weighted Score</div>
                    <div className="text-lg font-black text-[#277254] mt-1">
                      {detailApplicant.final_score !== null ? `${Math.round(detailApplicant.final_score)}%` : 'Pending'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Shortlist & Workflow Status */}
              <div className="mt-4 rounded-xl border border-[#eef0e7] bg-[#fafaf7] p-3.5 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-[#7b8490]">Shortlist Status:</span>
                  {detailApplicant.is_shortlisted ? (
                    <span className="inline-flex items-center gap-1 font-bold text-[#8a6a16]">
                      <Star size={13} className="fill-[#f5c84b] text-[#8a6a16]" /> Shortlisted
                    </span>
                  ) : (
                    <span className="text-[#526072] font-semibold">Not Shortlisted</span>
                  )}
                </div>
                {detailApplicant.shortlist_reason && (
                  <div className="text-[11px] text-[#526072] bg-white p-2 rounded-lg border border-[#eef0e7]">
                    <strong>Reason:</strong> {detailApplicant.shortlist_reason}
                  </div>
                )}
                <div className="flex items-center justify-between pt-1 border-t border-[#eef0e7]">
                  <span className="text-[#7b8490]">HR Review Decision:</span>
                  <span className="font-bold text-[#253142]">
                    {detailApplicant.hr_decision_display || detailApplicant.hr_decision}
                  </span>
                </div>
                {detailApplicant.hr_decision_notes && (
                  <div className="text-[11px] text-[#526072] bg-white p-2 rounded-lg border border-[#eef0e7]">
                    <strong>Reviewer Notes:</strong> {detailApplicant.hr_decision_notes}
                  </div>
                )}
              </div>

              {/* Close Button */}
              <div className="mt-5 flex justify-end">
                <button
                  type="button"
                  onClick={() => setDetailApplicant(null)}
                  className="rounded-xl bg-[#253142] px-4 py-2 text-xs font-bold text-white hover:bg-[#33435a] transition"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
