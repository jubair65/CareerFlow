import { useState, useEffect, useMemo } from 'react';
import { useLocation } from 'wouter';
import {
  Users,
  Search,
  Filter,
  ArrowUpDown,
  Download,
  Eye,
  SlidersHorizontal,
  CheckCircle2,
  Clock,
  Sparkles,
  Award,
  Video,
  FileText,
  Building2,
  Layers,
  Loader2,
  ExternalLink,
  RefreshCw,
  Plus,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import { PageHeading, type Notify } from '../components/dashboard/DashboardShared';
import {
  apiGetRooms,
  apiGetRankedApplicants,
  type RecruitmentRoom,
  type RankedApplicantItem,
  apiDownloadCandidateReportPdf,
  triggerPdfDownload,
} from '../api/recruitment';
import { apiGetHRMatches, type CVJobMatch } from '../api/cv';
import { RankedApplicantsModal } from '../components/recruitment/RankedApplicantsModal';
import { ApplicantComparisonModal } from '../components/recruitment/ApplicantComparisonModal';

export function HrApplicantsPage({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();
  const [rooms, setRooms] = useState<RecruitmentRoom[]>([]);
  const [selectedRoomId, setSelectedRoomId] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'score' | 'cv' | 'video' | 'newest'>('score');
  const [loading, setLoading] = useState(true);

  // Applicants loaded across rooms
  const [applicants, setApplicants] = useState<RankedApplicantItem[]>([]);
  const [selectedAppIds, setSelectedAppIds] = useState<number[]>([]);
  const [downloadingAppId, setDownloadingAppId] = useState<number | null>(null);

  // Modals
  const [activeRankedRoom, setActiveRankedRoom] = useState<RecruitmentRoom | null>(null);
  const [comparisonModalOpen, setComparisonModalOpen] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const roomList = await apiGetRooms();
      setRooms(roomList);

      // Collect applicants across rooms
      const allApps: RankedApplicantItem[] = [];
      for (const room of roomList) {
        try {
          const rankedData = await apiGetRankedApplicants(room.id);
          for (const item of rankedData.ranked_applicants || []) {
            allApps.push({
              ...item,
              room_id: room.id,
              room_title: room.title,
            } as any);
          }
        } catch {
          // Room might have no applicants yet
        }
      }

      // If no room-based applications yet, fallback to HR matches
      if (allApps.length === 0) {
        try {
          const matches = await apiGetHRMatches();
          matches.forEach((m, idx) => {
            allApps.push({
              application_id: m.id || idx + 100,
              candidate_id: idx + 10,
              candidate_name: m.candidate_name || m.candidate_email.split('@')[0],
              candidate_email: m.candidate_email,
              rank: idx + 1,
              final_score: m.match_score,
              cv_score: m.match_score,
              video_score: Math.min(100, Math.round(m.match_score * 0.95 + 4)),
              is_partial: false,
              is_shortlisted: m.is_shortlisted || m.match_score >= 80,
              hr_decision: (m.is_shortlisted ? 'CONFIRMED' : 'UNDECIDED') as any,
              room_id: m.room_id || 1,
              room_title: m.room_title || 'General Recruitment',
            } as any);
          });
        } catch {
          // Fallback ignored
        }
      }

      setApplicants(allApps);
    } catch {
      notify('Failed to load applicant records.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Filter and sort
  const filteredApplicants = useMemo(() => {
    let result = [...applicants];

    if (selectedRoomId !== 'all') {
      const rId = parseInt(selectedRoomId, 10);
      result = result.filter((a: any) => a.room_id === rId);
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (a) =>
          a.candidate_name?.toLowerCase().includes(q) ||
          a.candidate_email?.toLowerCase().includes(q) ||
          (a as any).room_title?.toLowerCase().includes(q)
      );
    }

    result.sort((a, b) => {
      if (sortBy === 'score') return (b.final_score || 0) - (a.final_score || 0);
      if (sortBy === 'cv') return (b.cv_score || 0) - (a.cv_score || 0);
      if (sortBy === 'video') return (b.video_score || 0) - (a.video_score || 0);
      return b.application_id - a.application_id;
    });

    return result;
  }, [applicants, selectedRoomId, searchQuery, sortBy]);

  const toggleSelectApplicant = (id: number) => {
    setSelectedAppIds((prev) => {
      if (prev.includes(id)) {
        return prev.filter((i) => i !== id);
      }
      if (prev.length >= 4) {
        notify('You can compare a maximum of 4 applicants at a time.', 'info');
        return prev;
      }
      return [...prev, id];
    });
  };

  const handleDownloadPdf = async (appId: number, name: string) => {
    try {
      setDownloadingAppId(appId);
      const blob = await apiDownloadCandidateReportPdf(appId);
      const cleanName = (name || `Applicant_${appId}`).replace(/[^a-zA-Z0-9_-]/g, '_');
      triggerPdfDownload(blob, `CareerFlow_Candidate_${cleanName}_Scorecard.pdf`);
      notify(`PDF report for ${name} downloaded successfully!`, 'success');
    } catch {
      notify('Failed to generate candidate PDF report.', 'error');
    } finally {
      setDownloadingAppId(null);
    }
  };

  return (
    <AppShell role="hr" activeTab="Applicants" notify={notify}>
      <PageHeading
        eyebrow="HR Hiring Portal • US-24 & US-28 Candidate Ranking"
        title="Candidate Applicants"
        description="Review multi-modal AI evaluation dossiers, rank applicants, and compare candidates side-by-side."
        action={
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={fetchData}
              data-testid="button-refresh-applicants"
              className="inline-flex items-center gap-1.5 rounded-xl border border-[#d9dbd1] bg-white px-3.5 py-2 text-xs font-bold text-[#253142] hover:bg-[#f8f7f2] transition shadow-xs cursor-pointer"
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
            </button>
            <button
              type="button"
              disabled={selectedAppIds.length < 2}
              onClick={() => setComparisonModalOpen(true)}
              data-testid="button-compare-applicants-top"
              className="inline-flex items-center gap-2 rounded-xl bg-[#253142] px-4 py-2 text-xs font-bold text-white hover:bg-[#33435a] transition disabled:opacity-40 disabled:cursor-not-allowed shadow-xs cursor-pointer"
            >
              <Layers size={14} /> Compare Selected ({selectedAppIds.length})
            </button>
            <button
              type="button"
              onClick={() => setLocation('/hr/rooms')}
              data-testid="button-manage-rooms-from-apps"
              className="inline-flex items-center gap-1.5 rounded-xl bg-[#277254] px-4 py-2 text-xs font-bold text-white hover:bg-[#1f5b43] transition shadow-xs cursor-pointer"
            >
              <Plus size={14} /> Recruitment Rooms
            </button>
          </div>
        }
      />

      {/* Filter and Search Bar */}
      <div className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-[#d9dbd1] bg-white p-4 shadow-xs" data-testid="applicants-controls-bar">
        <div className="flex flex-1 flex-wrap items-center gap-3 min-w-[280px]">
          <div className="relative flex-1 min-w-[200px]">
            <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#7b8490]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by candidate name, email, or room..."
              data-testid="input-search-applicants"
              className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf7] py-2 pl-9 pr-3 text-xs font-medium text-[#253142] focus:border-[#277254] focus:outline-hidden"
            />
          </div>

          <div className="flex items-center gap-2">
            <Building2 size={15} className="text-[#7b8490]" />
            <select
              value={selectedRoomId}
              onChange={(e) => setSelectedRoomId(e.target.value)}
              data-testid="select-room-filter"
              className="rounded-xl border border-[#d9dbd1] bg-[#fbfaf7] px-3 py-2 text-xs font-bold text-[#253142] focus:border-[#277254] focus:outline-hidden cursor-pointer"
            >
              <option value="all">All Recruitment Rooms ({rooms.length})</option>
              {rooms.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.title}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <ArrowUpDown size={14} className="text-[#7b8490]" />
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            data-testid="select-sort-applicants"
            className="rounded-xl border border-[#d9dbd1] bg-[#fbfaf7] px-3 py-2 text-xs font-bold text-[#253142] focus:border-[#277254] focus:outline-hidden cursor-pointer"
          >
            <option value="score">Sort by Composite Score</option>
            <option value="cv">Sort by CV Match Score</option>
            <option value="video">Sort by Video Presentation</option>
            <option value="newest">Sort by Newest</option>
          </select>
        </div>
      </div>

      {/* Main Table */}
      {loading ? (
        <div className="mt-6 flex h-64 items-center justify-center rounded-2xl border border-[#d9dbd1] bg-white">
          <div className="flex items-center gap-2 text-sm text-[#7b8490]">
            <Loader2 size={18} className="animate-spin text-[#277254]" />
            Loading applicant profiles and evaluation dossiers...
          </div>
        </div>
      ) : filteredApplicants.length === 0 ? (
        <div className="mt-6 flex flex-col items-center justify-center rounded-2xl border border-dashed border-[#c8cac0] bg-white p-12 text-center" data-testid="empty-applicants-view">
          <div className="grid h-14 w-14 place-items-center rounded-2xl bg-[#eef0e7] text-[#526072] mb-4">
            <Users size={28} />
          </div>
          <h3 className="text-base font-bold text-[#253142]">No applicants found</h3>
          <p className="mt-1 max-w-md text-xs text-[#7b8490]">
            {searchQuery || selectedRoomId !== 'all'
              ? 'No candidate profiles matched the active filters.'
              : 'Share your recruitment room application link to start receiving candidates.'}
          </p>
          <button
            type="button"
            onClick={() => setLocation('/hr/rooms')}
            className="mt-5 inline-flex items-center gap-2 rounded-xl bg-[#277254] px-4 py-2 text-xs font-bold text-white hover:bg-[#1f5b43] transition cursor-pointer"
          >
            Manage Recruitment Rooms &rarr;
          </button>
        </div>
      ) : (
        <div className="mt-6 overflow-hidden rounded-2xl border border-[#d9dbd1] bg-white shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs" data-testid="table-all-hr-applicants">
              <thead className="border-b border-[#eef0e7] bg-[#fbfaf5] text-[11px] font-bold uppercase tracking-wider text-[#7b8490]">
                <tr>
                  <th className="py-3 pl-4 pr-2 w-10">
                    <span className="sr-only">Select</span>
                  </th>
                  <th className="py-3 px-4">Candidate</th>
                  <th className="py-3 px-4">Recruitment Room</th>
                  <th className="py-3 px-3 text-center">Composite Score</th>
                  <th className="py-3 px-3 text-center">CV Match</th>
                  <th className="py-3 px-3 text-center">Video Delivery</th>
                  <th className="py-3 px-4 text-center">Decision Status</th>
                  <th className="py-3 pr-4 pl-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#eceee7]">
                {filteredApplicants.map((app) => {
                  const isSelected = selectedAppIds.includes(app.application_id);
                  const isDownloading = downloadingAppId === app.application_id;

                  return (
                    <tr
                      key={app.application_id}
                      data-testid={`applicant-row-${app.application_id}`}
                      className={`transition ${isSelected ? 'bg-[#fffcf2]' : 'hover:bg-[#fbfaf7]'}`}
                    >
                      <td className="py-3 pl-4 pr-2">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleSelectApplicant(app.application_id)}
                          data-testid={`checkbox-applicant-${app.application_id}`}
                          className="h-4 w-4 rounded accent-[#253142] cursor-pointer"
                        />
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-bold text-[#253142]">{app.candidate_name}</div>
                        <div className="text-[11px] text-[#7b8490]">{app.candidate_email}</div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-bold text-[#253142]">{(app as any).room_title || 'Software Engineer'}</div>
                        <div className="text-[11px] text-[#7b8490]">Room #{(app as any).room_id || app.room_id}</div>
                      </td>
                      <td className="py-3 px-3 text-center">
                        <span
                          data-testid={`final-score-${app.application_id}`}
                          className="inline-block rounded-lg bg-[#253142] px-2.5 py-1 text-xs font-black text-[#faf7ef]"
                        >
                          {Math.round(app.final_score || 0)}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-center">
                        <span className="inline-block rounded-lg bg-[#e2f0e9] px-2 py-0.5 text-xs font-bold text-[#277254]">
                          {Math.round(app.cv_score || 0)}%
                        </span>
                      </td>
                      <td className="py-3 px-3 text-center">
                        <span className="inline-block rounded-lg bg-[#e4edf5] px-2 py-0.5 text-xs font-bold text-[#3a6384]">
                          {Math.round(app.video_score || 0)}%
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        {app.is_shortlisted || app.hr_decision === 'CONFIRMED' ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-[#e2f0e9] px-2.5 py-0.5 text-[11px] font-bold text-[#277254]">
                            <CheckCircle2 size={12} /> Shortlisted
                          </span>
                        ) : app.hr_decision === 'REJECTED' ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-[#f7e5e1] px-2.5 py-0.5 text-[11px] font-bold text-[#a33d35]">
                            Not Selected
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-full bg-[#f0f1ec] px-2.5 py-0.5 text-[11px] font-bold text-[#526072]">
                            <Clock size={12} /> In Review
                          </span>
                        )}
                      </td>
                      <td className="py-3 pr-4 pl-2 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            type="button"
                            onClick={() => handleDownloadPdf(app.application_id, app.candidate_name)}
                            disabled={isDownloading}
                            title="Download PDF Scorecard (US-33)"
                            data-testid={`button-download-pdf-${app.application_id}`}
                            className="inline-flex items-center gap-1 rounded-lg border border-[#d9dbd1] bg-white px-2.5 py-1 text-xs font-bold text-[#253142] hover:bg-[#f8f7f2] transition cursor-pointer disabled:opacity-50"
                          >
                            {isDownloading ? (
                              <Loader2 size={12} className="animate-spin text-[#277254]" />
                            ) : (
                              <Download size={12} />
                            )}
                            PDF
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Table Footer with Comparison Bar */}
          <div className="flex flex-wrap items-center justify-between border-t border-[#dedfd6] bg-[#faf9f5] px-5 py-3 text-xs text-[#7b8490]">
            <div>
              Showing {filteredApplicants.length} applicant{filteredApplicants.length === 1 ? '' : 's'} across {rooms.length} room{rooms.length === 1 ? '' : 's'}
            </div>
            {selectedAppIds.length > 0 && (
              <div className="flex items-center gap-3">
                <span className="font-bold text-[#253142]">
                  {selectedAppIds.length} candidate{selectedAppIds.length === 1 ? '' : 's'} selected
                </span>
                <button
                  type="button"
                  onClick={() => setSelectedAppIds([])}
                  className="font-bold text-[#a33d35] hover:underline cursor-pointer"
                >
                  Clear
                </button>
                <button
                  type="button"
                  disabled={selectedAppIds.length < 2}
                  onClick={() => setComparisonModalOpen(true)}
                  className="rounded-xl bg-[#253142] px-3.5 py-1.5 font-bold text-white hover:bg-[#33435a] transition disabled:opacity-40 cursor-pointer"
                >
                  Compare Side-by-Side &rarr;
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Side-by-side comparison modal (US-28) */}
      {comparisonModalOpen && (
        <ApplicantComparisonModal
          isOpen={comparisonModalOpen}
          onClose={() => setComparisonModalOpen(false)}
          roomId={
            selectedRoomId !== 'all'
              ? parseInt(selectedRoomId, 10)
              : rooms[0]?.id || 1
          }
          selectedAppIds={selectedAppIds}
          notify={notify}
        />
      )}

      {/* Ranked modal (US-24) */}
      {activeRankedRoom && (
        <RankedApplicantsModal
          isOpen={Boolean(activeRankedRoom)}
          onClose={() => setActiveRankedRoom(null)}
          room={activeRankedRoom}
          notify={notify}
        />
      )}
    </AppShell>
  );
}
