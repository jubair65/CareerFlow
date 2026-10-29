import { useState, useEffect, useMemo } from 'react';
import { useLocation } from 'wouter';
import {
  Star,
  Send,
  Download,
  Building2,
  FolderOpen,
  Search,
  CheckCircle2,
  Clock,
  Loader2,
  RefreshCw,
  Filter,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import { PageHeading, type Notify } from '../components/dashboard/DashboardShared';
import {
  apiGetAgencyCrossClientApplicants,
  apiGetAgencyClients,
  apiGetAgencyRooms,
  apiDownloadCandidateReportPdf,
  triggerPdfDownload,
  type AgencyCrossClientApplicant,
  type ClientCompany,
  type RecruitmentRoom,
} from '../api/recruitment';
import { ForwardCandidatesModal } from '../components/recruitment/ForwardCandidatesModal';

export function AgencyShortlistedPage({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();
  const [candidates, setCandidates] = useState<AgencyCrossClientApplicant[]>([]);
  const [clients, setClients] = useState<ClientCompany[]>([]);
  const [rooms, setRooms] = useState<RecruitmentRoom[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [selectedClientId, setSelectedClientId] = useState<string>('all');
  const [selectedRoomId, setSelectedRoomId] = useState<string>('all');
  const [forwardFilter, setForwardFilter] = useState<'all' | 'unforwarded' | 'forwarded'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Selection & Forwarding Modal
  const [selectedAppIds, setSelectedAppIds] = useState<number[]>([]);
  const [forwardModalOpen, setForwardModalOpen] = useState(false);
  const [candidatesToForward, setCandidatesToForward] = useState<AgencyCrossClientApplicant[]>([]);
  const [downloadingAppId, setDownloadingAppId] = useState<number | null>(null);

  const fetchShortlistData = async () => {
    try {
      setLoading(true);
      const [applicantsRes, clientsRes, roomsRes] = await Promise.all([
        apiGetAgencyCrossClientApplicants({ is_shortlisted: 'true' }),
        apiGetAgencyClients(),
        apiGetAgencyRooms(),
      ]);
      setCandidates(applicantsRes.results || []);
      setClients(clientsRes);
      setRooms(roomsRes);
    } catch {
      notify('Failed to load agency shortlisted candidate pipeline.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchShortlistData();
  }, []);

  // Filtered Candidates
  const filteredCandidates = useMemo(() => {
    let result = [...candidates];

    if (selectedClientId !== 'all') {
      const cId = parseInt(selectedClientId, 10);
      result = result.filter((c) => c.client_company_id === cId);
    }

    if (selectedRoomId !== 'all') {
      const rId = parseInt(selectedRoomId, 10);
      result = result.filter((c) => c.room_id === rId);
    }

    if (forwardFilter === 'forwarded') {
      result = result.filter((c) => c.is_forwarded);
    } else if (forwardFilter === 'unforwarded') {
      result = result.filter((c) => !c.is_forwarded);
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (c) =>
          c.candidate_name?.toLowerCase().includes(q) ||
          c.email?.toLowerCase().includes(q) ||
          c.client_company?.toLowerCase().includes(q) ||
          c.room_title?.toLowerCase().includes(q)
      );
    }

    return result;
  }, [candidates, selectedClientId, selectedRoomId, forwardFilter, searchQuery]);

  const toggleSelect = (id: number) => {
    setSelectedAppIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const handleOpenBulkForward = () => {
    const selected = candidates.filter((c) => selectedAppIds.includes(c.application_id));
    setCandidatesToForward(selected);
    setForwardModalOpen(true);
  };

  const handleOpenSingleForward = (candidate: AgencyCrossClientApplicant) => {
    setCandidatesToForward([candidate]);
    setForwardModalOpen(true);
  };

  const handleDownloadPdf = async (appId: number, name: string) => {
    try {
      setDownloadingAppId(appId);
      const blob = await apiDownloadCandidateReportPdf(appId);
      const cleanName = (name || `Candidate_${appId}`).replace(/[^a-zA-Z0-9_-]/g, '_');
      triggerPdfDownload(blob, `CareerFlow_Dossier_${cleanName}.pdf`);
      notify(`Candidate dossier PDF for "${name}" downloaded!`, 'success');
    } catch {
      notify('Failed to generate candidate dossier PDF.', 'error');
    } finally {
      setDownloadingAppId(null);
    }
  };

  return (
    <AppShell role="agency" activeTab="Shortlisted" notify={notify}>
      <PageHeading
        eyebrow="Agency Hiring Portal • US-32 Forward Shortlist"
        title="Shortlisted Candidate Dossiers"
        description="Review top candidates qualifying across client hiring rooms and dispatch dossiers directly to client representatives."
        action={
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={fetchShortlistData}
              data-testid="button-refresh-agency-shortlist"
              className="inline-flex items-center gap-1.5 rounded-xl border border-[#d9dbd1] bg-white px-3.5 py-2 text-xs font-bold text-[#253142] hover:bg-[#f8f7f2] transition shadow-xs cursor-pointer"
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
            </button>
            <button
              type="button"
              disabled={selectedAppIds.length === 0}
              onClick={handleOpenBulkForward}
              data-testid="button-forward-selected-top"
              className="inline-flex items-center gap-2 rounded-xl bg-[#277254] px-4 py-2 text-xs font-bold text-white hover:bg-[#1f5b43] transition disabled:opacity-40 disabled:cursor-not-allowed shadow-xs cursor-pointer"
            >
              <Send size={14} /> Forward to Client ({selectedAppIds.length})
            </button>
          </div>
        }
      />

      {/* Filter and Search Bar */}
      <div className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-[#d9dbd1] bg-white p-4 shadow-xs" data-testid="agency-shortlist-controls">
        <div className="flex flex-1 flex-wrap items-center gap-3 min-w-[280px]">
          <div className="relative flex-1 min-w-[180px]">
            <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#7b8490]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search candidate, client company, or room..."
              data-testid="input-agency-shortlist-search"
              className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf7] py-2 pl-9 pr-3 text-xs font-medium text-[#253142] focus:border-[#277254] focus:outline-hidden"
            />
          </div>

          <div className="flex items-center gap-2">
            <Building2 size={15} className="text-[#7b8490]" />
            <select
              value={selectedClientId}
              onChange={(e) => setSelectedClientId(e.target.value)}
              data-testid="select-client-filter"
              className="rounded-xl border border-[#d9dbd1] bg-[#fbfaf7] px-3 py-2 text-xs font-bold text-[#253142] focus:border-[#277254] focus:outline-hidden cursor-pointer"
            >
              <option value="all">All Clients ({clients.length})</option>
              {clients.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <FolderOpen size={15} className="text-[#7b8490]" />
            <select
              value={selectedRoomId}
              onChange={(e) => setSelectedRoomId(e.target.value)}
              data-testid="select-agency-room-filter"
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
            value={forwardFilter}
            onChange={(e) => setForwardFilter(e.target.value as any)}
            data-testid="select-forward-status-filter"
            className="rounded-xl border border-[#d9dbd1] bg-[#fbfaf7] px-3 py-2 text-xs font-bold text-[#253142] focus:border-[#277254] focus:outline-hidden cursor-pointer"
          >
            <option value="all">All Delivery Statuses</option>
            <option value="unforwarded">Ready to Forward</option>
            <option value="forwarded">Already Forwarded</option>
          </select>
        </div>
      </div>

      {/* Main Table */}
      {loading ? (
        <div className="mt-6 flex h-64 items-center justify-center rounded-2xl border border-[#d9dbd1] bg-white">
          <div className="flex items-center gap-2 text-sm text-[#7b8490]">
            <Loader2 size={18} className="animate-spin text-[#277254]" />
            Loading shortlisted candidate dossiers...
          </div>
        </div>
      ) : filteredCandidates.length === 0 ? (
        <div className="mt-6 flex flex-col items-center justify-center rounded-2xl border border-dashed border-[#c8cac0] bg-white p-12 text-center" data-testid="empty-agency-shortlist">
          <div className="grid h-14 w-14 place-items-center rounded-2xl bg-[#fff4db] text-[#966b0a] mb-4">
            <Star size={28} />
          </div>
          <h3 className="text-base font-bold text-[#253142]">No shortlisted candidates found</h3>
          <p className="mt-1 max-w-md text-xs text-[#7b8490]">
            {searchQuery || selectedClientId !== 'all' || selectedRoomId !== 'all'
              ? 'No shortlisted profiles match the current filter selection.'
              : 'Review your client candidate pipeline and qualify applicants to generate shortlist dossiers.'}
          </p>
          <button
            type="button"
            onClick={() => setLocation('/agency/pipeline')}
            className="mt-5 inline-flex items-center gap-2 rounded-xl bg-[#253142] px-4 py-2 text-xs font-bold text-white hover:bg-[#33435a] transition cursor-pointer"
          >
            View Full Pipeline &rarr;
          </button>
        </div>
      ) : (
        <div className="mt-6 overflow-hidden rounded-2xl border border-[#d9dbd1] bg-white shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs" data-testid="table-agency-shortlisted-candidates">
              <thead className="border-b border-[#eef0e7] bg-[#fbfaf5] text-[11px] font-bold uppercase tracking-wider text-[#7b8490]">
                <tr>
                  <th className="py-3 pl-4 pr-2 w-10">
                    <span className="sr-only">Select</span>
                  </th>
                  <th className="py-3 px-4">Candidate</th>
                  <th className="py-3 px-4">Client Company</th>
                  <th className="py-3 px-4">Room Title</th>
                  <th className="py-3 px-3 text-center">Final Score</th>
                  <th className="py-3 px-4 text-center">Client Delivery</th>
                  <th className="py-3 pr-4 pl-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#eceee7]">
                {filteredCandidates.map((candidate) => {
                  const isSelected = selectedAppIds.includes(candidate.application_id);
                  const isDownloading = downloadingAppId === candidate.application_id;

                  return (
                    <tr
                      key={candidate.application_id}
                      data-testid={`agency-shortlist-row-${candidate.application_id}`}
                      className={`hover:bg-[#fbfaf7] transition ${isSelected ? 'bg-[#fffcf2]' : ''}`}
                    >
                      <td className="py-3.5 pl-4 pr-2">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleSelect(candidate.application_id)}
                          data-testid={`checkbox-forward-${candidate.application_id}`}
                          className="h-4 w-4 rounded accent-[#277254] cursor-pointer"
                        />
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="font-bold text-[#253142]">{candidate.candidate_name}</div>
                        <div className="text-[11px] text-[#7b8490]">{candidate.email}</div>
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-1.5 font-bold text-[#253142]">
                          <Building2 size={13} className="text-[#3a6384]" />
                          {candidate.client_company}
                        </div>
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="font-medium text-[#253142]">{candidate.room_title}</div>
                      </td>
                      <td className="py-3.5 px-3 text-center">
                        <span className="inline-block rounded-lg bg-[#277254] px-2.5 py-0.5 text-xs font-black text-white">
                          {Math.round(candidate.final_score || 0)}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        {candidate.is_forwarded ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-[#e2f0e9] px-2.5 py-0.5 text-[11px] font-bold text-[#277254]">
                            <CheckCircle2 size={12} /> Forwarded
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-full bg-[#fff4db] px-2.5 py-0.5 text-[11px] font-bold text-[#966b0a]">
                            <Clock size={12} /> Ready to Forward
                          </span>
                        )}
                      </td>
                      <td className="py-3.5 pr-4 pl-2 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            type="button"
                            onClick={() => handleOpenSingleForward(candidate)}
                            title="Forward Dossier to Client Contact"
                            data-testid={`button-forward-single-${candidate.application_id}`}
                            className="inline-flex items-center gap-1 rounded-lg bg-[#277254] px-2.5 py-1 text-xs font-bold text-white hover:bg-[#1f5b43] transition cursor-pointer shadow-2xs"
                          >
                            <Send size={12} /> Forward
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDownloadPdf(candidate.application_id, candidate.candidate_name)}
                            disabled={isDownloading}
                            title="Download Candidate PDF Dossier"
                            data-testid={`button-download-dossier-${candidate.application_id}`}
                            className="inline-flex items-center gap-1 rounded-lg border border-[#d9dbd1] bg-white px-2.5 py-1 text-xs font-bold text-[#253142] hover:bg-[#f8f7f2] transition disabled:opacity-50 cursor-pointer"
                          >
                            {isDownloading ? <Loader2 size={12} className="animate-spin text-[#277254]" /> : <Download size={12} />}
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

          <div className="flex flex-wrap items-center justify-between border-t border-[#dedfd6] bg-[#faf9f5] px-5 py-3 text-xs text-[#7b8490]">
            <div>
              Showing {filteredCandidates.length} shortlisted candidate dossier{filteredCandidates.length === 1 ? '' : 's'} across {clients.length} client{clients.length === 1 ? '' : 's'}.
            </div>
            {selectedAppIds.length > 0 && (
              <div className="flex items-center gap-3">
                <span className="font-bold text-[#253142]">{selectedAppIds.length} selected</span>
                <button
                  type="button"
                  onClick={() => setSelectedAppIds([])}
                  className="font-bold text-[#a33d35] hover:underline cursor-pointer"
                >
                  Clear
                </button>
                <button
                  type="button"
                  onClick={handleOpenBulkForward}
                  className="rounded-xl bg-[#277254] px-3.5 py-1.5 font-bold text-white hover:bg-[#1f5b43] transition cursor-pointer shadow-2xs"
                >
                  Forward Selected to Client &rarr;
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Forwarding Modal Dialog (US-32) */}
      <ForwardCandidatesModal
        isOpen={forwardModalOpen}
        onClose={() => setForwardModalOpen(false)}
        candidates={candidatesToForward}
        clients={clients}
        onForwardSuccess={() => {
          fetchShortlistData();
          setSelectedAppIds([]);
        }}
        notify={notify}
      />
    </AppShell>
  );
}
