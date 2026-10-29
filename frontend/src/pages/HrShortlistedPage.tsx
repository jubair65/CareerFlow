import { useState, useEffect, useMemo } from 'react';
import { useLocation } from 'wouter';
import {
  Star,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  Clock,
  Download,
  Sliders,
  Building2,
  Award,
  Sparkles,
  Loader2,
  RefreshCw,
  Plus,
  AlertCircle,
  ChevronRight,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import { PageHeading, type Notify } from '../components/dashboard/DashboardShared';
import {
  apiGetRooms,
  apiGetShortlistedApplicants,
  apiSubmitCandidateDecision,
  apiDownloadCandidateReportPdf,
  triggerPdfDownload,
  type RecruitmentRoom,
  type ShortlistedApplicantItem,
} from '../api/recruitment';
import { ShortlistConfigModal } from '../components/recruitment/ShortlistConfigModal';

export function HrShortlistedPage({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();
  const [rooms, setRooms] = useState<RecruitmentRoom[]>([]);
  const [selectedRoomId, setSelectedRoomId] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [decisionFilter, setDecisionFilter] = useState<'all' | 'confirmed' | 'undecided' | 'overridden'>('all');
  const [loading, setLoading] = useState(true);

  // Shortlisted applicants
  const [shortlistedApps, setShortlistedApps] = useState<ShortlistedApplicantItem[]>([]);
  const [downloadingAppId, setDownloadingAppId] = useState<number | null>(null);
  const [updatingAppId, setUpdatingAppId] = useState<number | null>(null);

  // Modal
  const [configRoom, setConfigRoom] = useState<RecruitmentRoom | null>(null);

  const fetchShortlistedData = async () => {
    try {
      setLoading(true);
      const roomList = await apiGetRooms();
      setRooms(roomList);

      const allShortlisted: ShortlistedApplicantItem[] = [];
      for (const room of roomList) {
        try {
          const res = await apiGetShortlistedApplicants(room.id);
          for (const item of res.shortlisted_applicants || []) {
            allShortlisted.push({
              ...item,
              room_id: room.id,
              room_title: room.title,
            } as any);
          }
        } catch {
          // Room might have no applicants
        }
      }

      setShortlistedApps(allShortlisted);
    } catch {
      notify('Failed to load shortlisted applicants.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchShortlistedData();
  }, []);

  // Filtered applicants
  const filteredApps = useMemo(() => {
    let result = [...shortlistedApps];

    if (selectedRoomId !== 'all') {
      const rId = parseInt(selectedRoomId, 10);
      result = result.filter((a: any) => a.room_id === rId);
    }

    if (decisionFilter !== 'all') {
      if (decisionFilter === 'confirmed') {
        result = result.filter((a) => a.hr_decision === 'CONFIRMED');
      } else if (decisionFilter === 'undecided') {
        result = result.filter((a) => !a.hr_decision || a.hr_decision === 'UNDECIDED');
      } else if (decisionFilter === 'overridden') {
        result = result.filter((a) => a.hr_decision === 'OVERRIDDEN');
      }
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

    return result;
  }, [shortlistedApps, selectedRoomId, decisionFilter, searchQuery]);

  const handleConfirmDecision = async (appId: number) => {
    try {
      setUpdatingAppId(appId);
      await apiSubmitCandidateDecision(appId, {
        decision: 'CONFIRMED',
        notes: 'Shortlist confirmed by HR Hiring Manager after evaluation review.',
      });
      notify('Candidate shortlist confirmed successfully! Applicant notification dispatched.', 'success');
      // Update local state
      setShortlistedApps((prev) =>
        prev.map((a) => (a.application_id === appId ? { ...a, hr_decision: 'CONFIRMED' } : a))
      );
    } catch {
      notify('Failed to record confirmation decision.', 'error');
    } finally {
      setUpdatingAppId(null);
    }
  };

  const handleDownloadPdf = async (appId: number, name: string) => {
    try {
      setDownloadingAppId(appId);
      const blob = await apiDownloadCandidateReportPdf(appId);
      const cleanName = (name || `Applicant_${appId}`).replace(/[^a-zA-Z0-9_-]/g, '_');
      triggerPdfDownload(blob, `CareerFlow_Shortlisted_${cleanName}_Report.pdf`);
      notify(`PDF scorecard for ${name} downloaded!`, 'success');
    } catch {
      notify('Failed to generate candidate PDF report.', 'error');
    } finally {
      setDownloadingAppId(null);
    }
  };

  return (
    <AppShell role="hr" activeTab="Shortlisted" notify={notify}>
      <PageHeading
        eyebrow="HR Hiring Portal • US-25 & US-26 Shortlist Management"
        title="Shortlisted Candidates"
        description="Verify candidates qualifying for final round interviews, confirm hiring committee decisions, and export dossiers."
        action={
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={fetchShortlistedData}
              data-testid="button-refresh-shortlist"
              className="inline-flex items-center gap-1.5 rounded-xl border border-[#d9dbd1] bg-white px-3.5 py-2 text-xs font-bold text-[#253142] hover:bg-[#f8f7f2] transition shadow-xs cursor-pointer"
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
            </button>
            <button
              type="button"
              onClick={() => setConfigRoom(rooms[0] || null)}
              disabled={rooms.length === 0}
              data-testid="button-config-shortlist-criteria"
              className="inline-flex items-center gap-2 rounded-xl bg-[#253142] px-4 py-2 text-xs font-bold text-white hover:bg-[#33435a] transition disabled:opacity-40 shadow-xs cursor-pointer"
            >
              <Sliders size={14} /> Configure Shortlist Rules
            </button>
          </div>
        }
      />

      {/* Filter and Search Bar */}
      <div className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-[#d9dbd1] bg-white p-4 shadow-xs" data-testid="shortlist-controls-bar">
        <div className="flex flex-1 flex-wrap items-center gap-3 min-w-[280px]">
          <div className="relative flex-1 min-w-[200px]">
            <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#7b8490]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search shortlisted candidates by name or room..."
              data-testid="input-search-shortlist"
              className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf7] py-2 pl-9 pr-3 text-xs font-medium text-[#253142] focus:border-[#277254] focus:outline-hidden"
            />
          </div>

          <div className="flex items-center gap-2">
            <Building2 size={15} className="text-[#7b8490]" />
            <select
              value={selectedRoomId}
              onChange={(e) => setSelectedRoomId(e.target.value)}
              data-testid="select-shortlist-room"
              className="rounded-xl border border-[#d9dbd1] bg-[#fbfaf7] px-3 py-2 text-xs font-bold text-[#253142] focus:border-[#277254] focus:outline-hidden cursor-pointer"
            >
              <option value="all">All Rooms ({rooms.length})</option>
              {rooms.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.title}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Filter size={14} className="text-[#7b8490]" />
          <select
            value={decisionFilter}
            onChange={(e) => setDecisionFilter(e.target.value as any)}
            data-testid="select-decision-filter"
            className="rounded-xl border border-[#d9dbd1] bg-[#fbfaf7] px-3 py-2 text-xs font-bold text-[#253142] focus:border-[#277254] focus:outline-hidden cursor-pointer"
          >
            <option value="all">All Shortlist Decisions</option>
            <option value="confirmed">Confirmed by HR</option>
            <option value="undecided">Pending HR Confirmation</option>
            <option value="overridden">HR Overridden</option>
          </select>
        </div>
      </div>

      {/* Main Table */}
      {loading ? (
        <div className="mt-6 flex h-64 items-center justify-center rounded-2xl border border-[#d9dbd1] bg-white">
          <div className="flex items-center gap-2 text-sm text-[#7b8490]">
            <Loader2 size={18} className="animate-spin text-[#277254]" />
            Loading shortlisted candidate profiles...
          </div>
        </div>
      ) : filteredApps.length === 0 ? (
        <div className="mt-6 flex flex-col items-center justify-center rounded-2xl border border-dashed border-[#c8cac0] bg-white p-12 text-center" data-testid="empty-shortlist-view">
          <div className="grid h-14 w-14 place-items-center rounded-2xl bg-[#fff4db] text-[#966b0a] mb-4">
            <Star size={28} />
          </div>
          <h3 className="text-base font-bold text-[#253142]">No shortlisted candidates</h3>
          <p className="mt-1 max-w-md text-xs text-[#7b8490]">
            {searchQuery || selectedRoomId !== 'all'
              ? 'No shortlisted profiles match the active filter criteria.'
              : 'Run automatic shortlisting on your recruitment rooms or adjust threshold scores.'}
          </p>
          <button
            type="button"
            onClick={() => setLocation('/hr/applicants')}
            className="mt-5 inline-flex items-center gap-2 rounded-xl bg-[#253142] px-4 py-2 text-xs font-bold text-white hover:bg-[#33435a] transition cursor-pointer"
          >
            Review All Applicants &rarr;
          </button>
        </div>
      ) : (
        <div className="mt-6 overflow-hidden rounded-2xl border border-[#d9dbd1] bg-white shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs" data-testid="table-shortlisted-candidates">
              <thead className="border-b border-[#eef0e7] bg-[#fbfaf5] text-[11px] font-bold uppercase tracking-wider text-[#7b8490]">
                <tr>
                  <th className="py-3 px-4">Candidate</th>
                  <th className="py-3 px-4">Room & Role</th>
                  <th className="py-3 px-3 text-center">Score</th>
                  <th className="py-3 px-4">Shortlist Rationale</th>
                  <th className="py-3 px-4 text-center">HR Decision</th>
                  <th className="py-3 pr-4 pl-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#eceee7]">
                {filteredApps.map((app) => {
                  const isConfirmed = app.hr_decision === 'CONFIRMED';
                  const isUpdating = updatingAppId === app.application_id;
                  const isDownloading = downloadingAppId === app.application_id;

                  return (
                    <tr
                      key={app.application_id}
                      data-testid={`shortlist-row-${app.application_id}`}
                      className="hover:bg-[#fbfaf7] transition"
                    >
                      <td className="py-3.5 px-4">
                        <div className="font-bold text-[#253142]">{app.candidate_name}</div>
                        <div className="text-[11px] text-[#7b8490]">{app.candidate_email}</div>
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="font-bold text-[#253142]">{(app as any).room_title || 'Engineering Role'}</div>
                        <div className="text-[11px] text-[#7b8490]">Rank #{app.rank} in Room</div>
                      </td>
                      <td className="py-3.5 px-3 text-center">
                        <span
                          data-testid={`shortlist-score-${app.application_id}`}
                          className="inline-block rounded-lg bg-[#277254] px-2.5 py-1 text-xs font-black text-white"
                        >
                          {Math.round(app.final_score || 0)}
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="text-xs text-[#526072] max-w-xs truncate">
                          {app.shortlist_reason || 'Qualified via composite multi-modal threshold'}
                        </div>
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        {isConfirmed ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-[#e2f0e9] px-2.5 py-0.5 text-[11px] font-bold text-[#277254]">
                            <CheckCircle2 size={12} /> Confirmed
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-full bg-[#fff4db] px-2.5 py-0.5 text-[11px] font-bold text-[#966b0a]">
                            <Clock size={12} /> Pending Review
                          </span>
                        )}
                      </td>
                      <td className="py-3.5 pr-4 pl-2 text-right">
                        <div className="flex items-center justify-end gap-2">
                          {!isConfirmed && (
                            <button
                              type="button"
                              onClick={() => handleConfirmDecision(app.application_id)}
                              disabled={isUpdating}
                              data-testid={`button-confirm-decision-${app.application_id}`}
                              className="inline-flex items-center gap-1 rounded-xl bg-[#277254] px-3 py-1 text-xs font-bold text-white hover:bg-[#1f5b43] transition disabled:opacity-50 cursor-pointer shadow-2xs"
                            >
                              {isUpdating ? <Loader2 size={12} className="animate-spin" /> : <CheckCircle2 size={12} />}
                              Confirm
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={() => handleDownloadPdf(app.application_id, app.candidate_name)}
                            disabled={isDownloading}
                            title="Download Candidate PDF Dossier"
                            data-testid={`button-download-shortlist-pdf-${app.application_id}`}
                            className="inline-flex items-center gap-1 rounded-lg border border-[#d9dbd1] bg-white px-2.5 py-1 text-xs font-bold text-[#253142] hover:bg-[#f8f7f2] transition disabled:opacity-50 cursor-pointer"
                          >
                            {isDownloading ? <Loader2 size={12} className="animate-spin text-[#277254]" /> : <Download size={12} />}
                            Dossier
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="border-t border-[#dedfd6] bg-[#faf9f5] px-5 py-3 text-xs text-[#7b8490]">
            Total {filteredApps.length} shortlisted candidate{filteredApps.length === 1 ? '' : 's'} across active recruitment rooms.
          </div>
        </div>
      )}

      {/* Shortlist Configuration Modal */}
      {configRoom && (
        <ShortlistConfigModal
          isOpen={Boolean(configRoom)}
          onClose={() => setConfigRoom(null)}
          room={configRoom}
          onShortlistUpdated={() => {
            fetchShortlistedData();
            setConfigRoom(null);
          }}
          notify={notify}
        />
      )}
    </AppShell>
  );
}
