import { useState, useEffect } from 'react';
import { useLocation } from 'wouter';
import {
  BarChart3,
  Download,
  Building2,
  FolderOpen,
  Users,
  Star,
  Loader2,
  Search,
  Filter,
  CheckCircle2,
  RefreshCw,
  Send,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import { PageHeading, StatCard, type Notify } from '../components/dashboard/DashboardShared';
import {
  apiGetAgencyClients,
  apiGetAgencyRooms,
  apiGetAgencyCrossClientApplicants,
  apiDownloadRoomSummaryPdf,
  apiDownloadCandidateReportPdf,
  triggerPdfDownload,
  type ClientCompany,
  type RecruitmentRoom,
  type AgencyCrossClientApplicant,
} from '../api/recruitment';

export function AgencyReportsPage({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();
  const [clients, setClients] = useState<ClientCompany[]>([]);
  const [rooms, setRooms] = useState<RecruitmentRoom[]>([]);
  const [applicants, setApplicants] = useState<AgencyCrossClientApplicant[]>([]);
  const [loading, setLoading] = useState(true);

  const [downloadingRoomId, setDownloadingRoomId] = useState<number | null>(null);
  const [downloadingAppId, setDownloadingAppId] = useState<number | null>(null);
  const [selectedClientId, setSelectedClientId] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  const fetchData = async () => {
    try {
      setLoading(true);
      const [clientsRes, roomsRes, appsRes] = await Promise.all([
        apiGetAgencyClients(),
        apiGetAgencyRooms(),
        apiGetAgencyCrossClientApplicants({ limit: 100 }),
      ]);
      setClients(Array.isArray(clientsRes) ? clientsRes : []);
      setRooms(Array.isArray(roomsRes) ? roomsRes : []);
      const list = Array.isArray(appsRes)
        ? appsRes
        : (appsRes as any)?.results || [];
      setApplicants(list);
    } catch {
      notify('Failed to load agency report data.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleDownloadRoomPdf = async (roomId: number, title: string) => {
    try {
      setDownloadingRoomId(roomId);
      const blob = await apiDownloadRoomSummaryPdf(roomId);
      const cleanTitle = (title || `Room_${roomId}`).replace(/[^a-zA-Z0-9_-]/g, '_');
      triggerPdfDownload(blob, `CareerFlow_Agency_Room_${roomId}_${cleanTitle}_Summary.pdf`);
      notify(`Room summary PDF for "${title}" downloaded successfully!`, 'success');
    } catch {
      notify('Failed to generate room summary PDF.', 'error');
    } finally {
      setDownloadingRoomId(null);
    }
  };

  const handleDownloadCandidatePdf = async (appId: number, name: string) => {
    try {
      setDownloadingAppId(appId);
      const blob = await apiDownloadCandidateReportPdf(appId);
      const cleanName = (name || `Candidate_${appId}`).replace(/[^a-zA-Z0-9_-]/g, '_');
      triggerPdfDownload(blob, `CareerFlow_Agency_Dossier_${cleanName}.pdf`);
      notify(`Candidate scorecard PDF for "${name}" downloaded!`, 'success');
    } catch {
      notify('Failed to generate candidate report PDF.', 'error');
    } finally {
      setDownloadingAppId(null);
    }
  };

  // Filtered rooms
  const filteredRooms = rooms.filter((r) => {
    if (selectedClientId !== 'all' && (r as any).client_company !== parseInt(selectedClientId, 10)) {
      return false;
    }
    return true;
  });

  // Filtered candidates
  const filteredCandidates = applicants.filter((a) => {
    if (selectedClientId !== 'all' && a.client_company_id !== parseInt(selectedClientId, 10)) {
      return false;
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        a.candidate_name?.toLowerCase().includes(q) ||
        a.candidate_email?.toLowerCase().includes(q) ||
        a.client_company_name?.toLowerCase().includes(q) ||
        a.room_title?.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <AppShell role="agency" activeTab="Reports" notify={notify}>
      <PageHeading
        eyebrow="Agency Hiring Portal • US-33 Cross-Client Reports"
        title="Client Reports & Dossier Exports"
        description="Comprehensive hiring throughput reports, candidate dossiers, and room summary exports across all client companies."
        action={
          <button
            type="button"
            onClick={fetchData}
            data-testid="button-refresh-agency-reports"
            className="inline-flex items-center gap-1.5 rounded-xl border border-[#d9dbd1] bg-white px-3.5 py-2 text-xs font-bold text-[#253142] hover:bg-[#f8f7f2] transition shadow-xs cursor-pointer"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh Reports
          </button>
        }
      />

      {/* 3 Overview Stat Cards */}
      <div className="mt-6 grid gap-4 sm:grid-cols-3" data-testid="agency-reports-stats">
        <StatCard
          label="Client Companies"
          value={String(clients.length)}
          detail="Active client organizations"
          icon={Building2}
          accent="amber"
        />
        <StatCard
          label="Active Client Rooms"
          value={String(rooms.length)}
          detail="Recruitment rooms managed"
          icon={FolderOpen}
          accent="blue"
        />
        <StatCard
          label="Forwarded Dossiers"
          value={String(applicants.filter((a) => a.is_forwarded).length)}
          detail="Transmitted to client contacts"
          icon={Send}
          accent="green"
        />
      </div>

      {/* Section 1: Client Recruitment Room PDF Exports */}
      <div className="mt-8">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-bold text-[#253142]">Client Room Summary Reports</h2>
            <p className="text-xs text-[#7b8490]">Export multi-candidate score distribution and room criteria for clients</p>
          </div>

          <div className="flex items-center gap-2">
            <Building2 size={14} className="text-[#7b8490]" />
            <select
              value={selectedClientId}
              onChange={(e) => setSelectedClientId(e.target.value)}
              className="rounded-xl border border-[#d9dbd1] bg-white px-3 py-1.5 text-xs font-bold text-[#253142] focus:border-[#277254] focus:outline-hidden cursor-pointer"
            >
              <option value="all">All Clients ({clients.length})</option>
              {clients.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {loading ? (
          <div className="flex h-36 items-center justify-center rounded-2xl border border-[#d9dbd1] bg-white">
            <Loader2 size={18} className="animate-spin text-[#277254]" />
          </div>
        ) : filteredRooms.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-[#c8cac0] bg-white p-8 text-center text-xs text-[#7b8490]">
            No client rooms found for the selected client filter.
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" data-testid="agency-room-reports-grid">
            {filteredRooms.map((room) => {
              const isDownloading = downloadingRoomId === room.id;
              const count = room.applicant_count ?? 0;
              const clientName = room.client_company_name || 'Direct Client';

              return (
                <div
                  key={room.id}
                  data-testid={`agency-room-report-${room.id}`}
                  className="flex flex-col justify-between rounded-2xl border border-[#d9dbd1] bg-white p-5 shadow-xs hover:shadow-sm transition"
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="rounded-md bg-[#e4edf5] px-2 py-0.5 text-[10px] font-bold text-[#2a557a] uppercase">
                        {clientName}
                      </span>
                      <span className="text-[11px] font-bold text-[#7b8490]">
                        {count} applicant{count === 1 ? '' : 's'}
                      </span>
                    </div>
                    <h3 className="mt-2.5 text-sm font-bold text-[#253142] line-clamp-1">
                      {room.title}
                    </h3>
                    <p className="mt-1 text-xs text-[#7b8490] line-clamp-2">
                      {room.department ? `${room.department} • ` : ''}
                      Weights: {Math.round(room.cv_weight)}% CV, {Math.round(room.video_weight)}% Video
                    </p>
                  </div>

                  <div className="mt-4 border-t border-[#eceee7] pt-3">
                    <button
                      type="button"
                      onClick={() => handleDownloadRoomPdf(room.id, room.title)}
                      disabled={isDownloading}
                      data-testid={`button-download-agency-room-pdf-${room.id}`}
                      className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#253142] py-2 text-xs font-bold text-white hover:bg-[#33435a] transition disabled:opacity-50 cursor-pointer"
                    >
                      {isDownloading ? (
                        <Loader2 size={13} className="animate-spin text-[#f5c84b]" />
                      ) : (
                        <Download size={13} />
                      )}
                      Download Room PDF Summary
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Section 2: Candidate Scorecard Exports */}
      <div className="mt-10">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-bold text-[#253142]">Candidate Scorecard Dossiers</h2>
            <p className="text-xs text-[#7b8490]">Export individual candidate evaluation dossiers across client pipelines</p>
          </div>

          <div className="relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#7b8490]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search candidate, room, or client..."
              className="rounded-xl border border-[#d9dbd1] bg-white py-1.5 pl-8 pr-3 text-xs font-medium text-[#253142] focus:border-[#277254] focus:outline-hidden"
            />
          </div>
        </div>

        {filteredCandidates.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-[#c8cac0] bg-white p-8 text-center text-xs text-[#7b8490]">
            No candidate dossiers available for the selected filters.
          </div>
        ) : (
          <div className="overflow-hidden rounded-2xl border border-[#d9dbd1] bg-white shadow-xs">
            <table className="w-full text-left text-xs" data-testid="table-agency-reports-candidates">
              <thead className="border-b border-[#eef0e7] bg-[#fbfaf5] text-[11px] font-bold uppercase tracking-wider text-[#7b8490]">
                <tr>
                  <th className="py-3 px-4">Candidate</th>
                  <th className="py-3 px-4">Client Company</th>
                  <th className="py-3 px-4">Room Title</th>
                  <th className="py-3 px-3 text-center">Final Score</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 pr-4 pl-2 text-right">Download</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#eceee7]">
                {filteredCandidates.map((candidate) => {
                  const isDownloading = downloadingAppId === candidate.id;

                  return (
                    <tr key={candidate.id} className="hover:bg-[#fbfaf7] transition">
                      <td className="py-3 px-4">
                        <div className="font-bold text-[#253142]">{candidate.candidate_name}</div>
                        <div className="text-[11px] text-[#7b8490]">{candidate.candidate_email}</div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-bold text-[#253142]">{candidate.client_company_name}</div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-medium text-[#253142]">{candidate.room_title}</div>
                      </td>
                      <td className="py-3 px-3 text-center">
                        <span className="inline-block rounded-lg bg-[#253142] px-2.5 py-0.5 text-xs font-bold text-[#faf7ef]">
                          {Math.round(candidate.final_score || 0)}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        {candidate.is_shortlisted ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-[#e2f0e9] px-2.5 py-0.5 text-[11px] font-bold text-[#277254]">
                            <CheckCircle2 size={12} /> Shortlisted
                          </span>
                        ) : (
                          <span className="rounded-full bg-[#f0f1ec] px-2.5 py-0.5 text-[11px] font-bold text-[#526072]">
                            In Pipeline
                          </span>
                        )}
                      </td>
                      <td className="py-3 pr-4 pl-2 text-right">
                        <button
                          type="button"
                          onClick={() => handleDownloadCandidatePdf(candidate.id, candidate.candidate_name)}
                          disabled={isDownloading}
                          data-testid={`button-download-agency-candidate-pdf-${candidate.id}`}
                          className="inline-flex items-center gap-1.5 rounded-xl border border-[#d9dbd1] bg-white px-3 py-1.5 text-xs font-bold text-[#277254] hover:bg-[#e2f0e9] transition disabled:opacity-50 cursor-pointer shadow-2xs"
                        >
                          {isDownloading ? (
                            <Loader2 size={13} className="animate-spin text-[#277254]" />
                          ) : (
                            <Download size={13} />
                          )}
                          Download Dossier
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </AppShell>
  );
}
