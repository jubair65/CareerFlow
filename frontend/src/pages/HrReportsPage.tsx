import { useState, useEffect } from 'react';
import { useLocation } from 'wouter';
import {
  BarChart3,
  Download,
  Building2,
  FileText,
  Users,
  Star,
  Loader2,
  Search,
  Filter,
  CheckCircle2,
  RefreshCw,
  FolderOpen,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import { PageHeading, StatCard, type Notify } from '../components/dashboard/DashboardShared';
import {
  apiGetRooms,
  apiGetRankedApplicants,
  apiDownloadRoomSummaryPdf,
  apiDownloadCandidateReportPdf,
  triggerPdfDownload,
  type RecruitmentRoom,
  type RankedApplicantItem,
} from '../api/recruitment';

export function HrReportsPage({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();
  const [rooms, setRooms] = useState<RecruitmentRoom[]>([]);
  const [applicants, setApplicants] = useState<RankedApplicantItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloadingRoomId, setDownloadingRoomId] = useState<number | null>(null);
  const [downloadingAppId, setDownloadingAppId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRoomFilter, setSelectedRoomFilter] = useState('all');

  const fetchData = async () => {
    try {
      setLoading(true);
      const roomList = await apiGetRooms();
      setRooms(roomList);

      const allApps: RankedApplicantItem[] = [];
      for (const r of roomList) {
        try {
          const res = await apiGetRankedApplicants(r.id);
          for (const item of res.ranked_applicants || []) {
            allApps.push({
              ...item,
              room_id: r.id,
              room_title: r.title,
            } as any);
          }
        } catch {
          // Room might be empty
        }
      }
      setApplicants(allApps);
    } catch {
      notify('Failed to load recruitment report data.', 'error');
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
      triggerPdfDownload(blob, `CareerFlow_Room_${roomId}_${cleanTitle}_Summary_Report.pdf`);
      notify(`Room summary PDF for "${title}" downloaded successfully!`, 'success');
    } catch {
      notify('Failed to generate room summary PDF report.', 'error');
    } finally {
      setDownloadingRoomId(null);
    }
  };

  const handleDownloadCandidatePdf = async (appId: number, name: string) => {
    try {
      setDownloadingAppId(appId);
      const blob = await apiDownloadCandidateReportPdf(appId);
      const cleanName = (name || `Candidate_${appId}`).replace(/[^a-zA-Z0-9_-]/g, '_');
      triggerPdfDownload(blob, `CareerFlow_Candidate_${cleanName}_Report.pdf`);
      notify(`Candidate evaluation scorecard for "${name}" downloaded!`, 'success');
    } catch {
      notify('Failed to generate candidate report PDF.', 'error');
    } finally {
      setDownloadingAppId(null);
    }
  };

  const filteredApplicants = applicants.filter((a) => {
    if (selectedRoomFilter !== 'all' && (a as any).room_id !== parseInt(selectedRoomFilter, 10)) {
      return false;
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        a.candidate_name?.toLowerCase().includes(q) ||
        a.candidate_email?.toLowerCase().includes(q) ||
        (a as any).room_title?.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <AppShell role="hr" activeTab="Reports" notify={notify}>
      <PageHeading
        eyebrow="HR Hiring Portal • US-33 Downloadable Reports"
        title="Hiring Reports & Scorecards"
        description="Generate, preview, and download boardroom-ready candidate scorecard dossiers and comprehensive room summary PDF reports."
        action={
          <button
            type="button"
            onClick={fetchData}
            data-testid="button-refresh-reports"
            className="inline-flex items-center gap-1.5 rounded-xl border border-[#d9dbd1] bg-white px-3.5 py-2 text-xs font-bold text-[#253142] hover:bg-[#f8f7f2] transition shadow-xs cursor-pointer"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh Reports
          </button>
        }
      />

      {/* 3 Overview Stat Cards */}
      <div className="mt-6 grid gap-4 sm:grid-cols-3" data-testid="reports-stats">
        <StatCard
          label="Active Hiring Rooms"
          value={String(rooms.length)}
          detail="Available for summary export"
          icon={FolderOpen}
          accent="amber"
        />
        <StatCard
          label="Total Applicant Dossiers"
          value={String(applicants.length)}
          detail="Evaluated candidate scorecards"
          icon={Users}
          accent="blue"
        />
        <StatCard
          label="Shortlisted Reports"
          value={String(applicants.filter((a) => a.is_shortlisted).length)}
          detail="Ready for final panel review"
          icon={Star}
          accent="green"
        />
      </div>

      {/* Section 1: Room Summary PDF Reports */}
      <div className="mt-8">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-[#253142]">Recruitment Room Summary Reports</h2>
            <p className="text-xs text-[#7b8490]">Export full multi-candidate score distribution and room criteria</p>
          </div>
          <button
            type="button"
            onClick={() => setLocation('/hr/rooms')}
            className="text-xs font-bold text-[#277254] hover:underline cursor-pointer"
          >
            Manage Rooms &rarr;
          </button>
        </div>

        {loading ? (
          <div className="flex h-36 items-center justify-center rounded-2xl border border-[#d9dbd1] bg-white">
            <Loader2 size={18} className="animate-spin text-[#277254]" />
          </div>
        ) : rooms.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-[#c8cac0] bg-white p-8 text-center text-xs text-[#7b8490]">
            No recruitment rooms available to generate reports. Create a room to start evaluating candidates.
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" data-testid="room-reports-grid">
            {rooms.map((room) => {
              const isDownloading = downloadingRoomId === room.id;
              const count = room.applicant_count ?? 0;
              return (
                <div
                  key={room.id}
                  data-testid={`room-report-card-${room.id}`}
                  className="flex flex-col justify-between rounded-2xl border border-[#d9dbd1] bg-white p-5 shadow-xs hover:shadow-sm transition"
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="rounded-md bg-[#eef0e7] px-2 py-0.5 text-[10px] font-bold text-[#526072] uppercase">
                        {room.role_category || 'General'}
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
                      data-testid={`button-download-room-summary-${room.id}`}
                      className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#253142] py-2 text-xs font-bold text-white hover:bg-[#33435a] transition disabled:opacity-50 cursor-pointer"
                    >
                      {isDownloading ? (
                        <Loader2 size={13} className="animate-spin text-[#f5c84b]" />
                      ) : (
                        <Download size={13} />
                      )}
                      Download Room PDF Report
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Section 2: Candidate Scorecard Reports */}
      <div className="mt-10">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-bold text-[#253142]">Individual Candidate Scorecard Reports</h2>
            <p className="text-xs text-[#7b8490]">Download comprehensive AI breakdown dossiers for each candidate</p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#7b8490]" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search candidate..."
                className="rounded-xl border border-[#d9dbd1] bg-white py-1.5 pl-8 pr-3 text-xs font-medium text-[#253142] focus:border-[#277254] focus:outline-hidden"
              />
            </div>
            <select
              value={selectedRoomFilter}
              onChange={(e) => setSelectedRoomFilter(e.target.value)}
              className="rounded-xl border border-[#d9dbd1] bg-white px-2.5 py-1.5 text-xs font-bold text-[#253142] focus:border-[#277254] focus:outline-hidden cursor-pointer"
            >
              <option value="all">All Rooms</option>
              {rooms.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.title}
                </option>
              ))}
            </select>
          </div>
        </div>

        {filteredApplicants.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-[#c8cac0] bg-white p-8 text-center text-xs text-[#7b8490]">
            No candidate scorecard reports available.
          </div>
        ) : (
          <div className="overflow-hidden rounded-2xl border border-[#d9dbd1] bg-white shadow-xs">
            <table className="w-full text-left text-xs" data-testid="table-reports-candidates">
              <thead className="border-b border-[#eef0e7] bg-[#fbfaf5] text-[11px] font-bold uppercase tracking-wider text-[#7b8490]">
                <tr>
                  <th className="py-3 px-4">Candidate</th>
                  <th className="py-3 px-4">Room Title</th>
                  <th className="py-3 px-3 text-center">Final Score</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 pr-4 pl-2 text-right">Download</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#eceee7]">
                {filteredApplicants.map((app) => {
                  const isDownloading = downloadingAppId === app.application_id;
                  return (
                    <tr key={app.application_id} className="hover:bg-[#fbfaf7] transition">
                      <td className="py-3 px-4">
                        <div className="font-bold text-[#253142]">{app.candidate_name}</div>
                        <div className="text-[11px] text-[#7b8490]">{app.candidate_email}</div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-bold text-[#253142]">{(app as any).room_title}</div>
                      </td>
                      <td className="py-3 px-3 text-center">
                        <span className="inline-block rounded-lg bg-[#253142] px-2.5 py-0.5 text-xs font-bold text-[#faf7ef]">
                          {Math.round(app.final_score || 0)}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        {app.is_shortlisted ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-[#e2f0e9] px-2.5 py-0.5 text-[11px] font-bold text-[#277254]">
                            <CheckCircle2 size={12} /> Shortlisted
                          </span>
                        ) : (
                          <span className="rounded-full bg-[#f0f1ec] px-2.5 py-0.5 text-[11px] font-bold text-[#526072]">
                            Standard
                          </span>
                        )}
                      </td>
                      <td className="py-3 pr-4 pl-2 text-right">
                        <button
                          type="button"
                          onClick={() => handleDownloadCandidatePdf(app.application_id, app.candidate_name)}
                          disabled={isDownloading}
                          data-testid={`button-download-candidate-pdf-${app.application_id}`}
                          className="inline-flex items-center gap-1.5 rounded-xl border border-[#d9dbd1] bg-white px-3 py-1.5 text-xs font-bold text-[#277254] hover:bg-[#e2f0e9] transition disabled:opacity-50 cursor-pointer shadow-2xs"
                        >
                          {isDownloading ? (
                            <Loader2 size={13} className="animate-spin text-[#277254]" />
                          ) : (
                            <Download size={13} />
                          )}
                          Download PDF
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
