import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
  X,
  XCircle,
  MessageSquare,
  GitCommit,
  Search,
  Trophy,
  Medal,
  Users,
  Gauge,
  AlertCircle,
  Clock,
  ArrowUpDown,
  CheckCircle2,
  RefreshCw,
  Sparkles,
  SlidersHorizontal,
  FileText,
  FileSpreadsheet,
  ChevronDown,
  Video,
  Calculator,
  Scale,
  Download,
  Loader2,
} from 'lucide-react';
import { RecruiterNotesModal } from './RecruiterNotesModal';
import type {
  PipelineStage,
  RecruitmentRoom,
  RankedApplicantItem,
  RankedApplicantsResponse,
  ApplicantExportParams,
} from '../../api/recruitment';
import {
  apiGetRankedApplicants,
  apiCalculateRoomScores,
  apiDownloadRoomSummaryPdf,
  triggerPdfDownload,
  apiDownloadApplicantsCsv,
  apiDownloadApplicantsExcel,
  triggerFileDownload,
  apiSubmitCandidateDecision,
} from '../../api/recruitment';
import { ScoreBreakdownModal } from './ScoreBreakdownModal';
import { ApplicantComparisonModal } from './ApplicantComparisonModal';

interface RankedApplicantsModalProps {
  isOpen: boolean;
  onClose: () => void;
  room: RecruitmentRoom | null;
  notify?: (message: string, tone?: 'success' | 'info' | 'error') => void;
}

type TabMode = 'RANKED' | 'UNRANKED';
type SortOption =
  | '-final_score'
  | 'final_score'
  | '-cv_score'
  | '-video_score'
  | 'applied_at'
  | '-applied_at';

export function RankedApplicantsModal({
  isOpen,
  onClose,
  room,
  notify,
}: RankedApplicantsModalProps) {
  const [data, setData] = useState<RankedApplicantsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [recalculating, setRecalculating] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [exportMenuOpen, setExportMenuOpen] = useState(false);
  const [exportingFormat, setExportingFormat] = useState<'csv' | 'excel' | null>(null);
  const exportMenuRef = useRef<HTMLDivElement>(null);
  const modalRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  // Filters & State
  const [activeTab, setActiveTab] = useState<TabMode>('RANKED');
  const [searchQuery, setSearchQuery] = useState('');
  const [minScoreFilter, setMinScoreFilter] = useState<number>(0);
  const [sortBy, setSortBy] = useState<SortOption>('-final_score');
  const [shortlistedOnly, setShortlistedOnly] = useState(false);
  const [breakdownAppId, setBreakdownAppId] = useState<number | null>(null);
  const [breakdownCandidateName, setBreakdownCandidateName] = useState<string | undefined>(undefined);

  // Selection & Bulk Actions State
  const [selectedAppIds, setSelectedAppIds] = useState<number[]>([]);
  const [isComparisonModalOpen, setIsComparisonModalOpen] = useState(false);

  // US-47: Recruiter Notes & Pipeline Stage Filter / Modal State
  const [selectedStageFilter, setSelectedStageFilter] = useState<string>('ALL');
  const [notesModalOpen, setNotesModalOpen] = useState(false);
  const [notesAppId, setNotesAppId] = useState<number | null>(null);
  const [notesCandidateName, setNotesCandidateName] = useState('');
  const [notesCandidateEmail, setNotesCandidateEmail] = useState('');
  const [notesCurrentStage, setNotesCurrentStage] = useState<PipelineStage>('APPLIED');

  // Background scroll lock & Esc / Focus trap
  useEffect(() => {
    if (!isOpen) return;

    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
        return;
      }

      if (e.key === 'Tab' && modalRef.current) {
        const focusableElements = modalRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusableElements.length > 0) {
          const firstElement = focusableElements[0];
          const lastElement = focusableElements[focusableElements.length - 1];

          if (e.shiftKey) {
            if (document.activeElement === firstElement) {
              lastElement?.focus();
              e.preventDefault();
            }
          } else {
            if (document.activeElement === lastElement) {
              firstElement?.focus();
              e.preventDefault();
            }
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      document.body.style.overflow = originalOverflow;
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  // Close export dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (exportMenuRef.current && !exportMenuRef.current.contains(event.target as Node)) {
        setExportMenuOpen(false);
      }
    };
    if (exportMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [exportMenuOpen]);

  const handleDownloadRoomSummaryPdf = async () => {
    if (!room) return;
    try {
      setDownloadingPdf(true);
      const blob = await apiDownloadRoomSummaryPdf(room.id);
      const titleClean = room.title.replace(/\s+/g, '_');
      triggerPdfDownload(blob, `CareerFlow_Room_${room.id}_${titleClean}_Summary_Report.pdf`);
      if (notify) notify('Room Summary Report downloaded successfully.', 'success');
    } catch {
      if (notify) notify('Failed to download room summary PDF report.', 'error');
    } finally {
      setDownloadingPdf(false);
    }
  };

  const handleExport = async (format: 'csv' | 'excel') => {
    if (!room) return;
    try {
      setExportingFormat(format);
      setExportMenuOpen(false);
      const exportParams: ApplicantExportParams = {
        min_score: minScoreFilter > 0 ? minScoreFilter : undefined,
        search: searchQuery.trim() || undefined,
        ordering: sortBy,
        shortlisted: shortlistedOnly ? true : undefined,
        include_unranked: true,
      };

      if (format === 'csv') {
        const blob = await apiDownloadApplicantsCsv(room.id, exportParams);
        const titleClean = (room.title || 'Room').replace(/\s+/g, '_');
        triggerFileDownload(blob, `CareerFlow_Room_${room.id}_${titleClean}_Applicants.csv`);
        notify?.('Applicants CSV export downloaded successfully.', 'success');
      } else {
        const blob = await apiDownloadApplicantsExcel(room.id, exportParams);
        const titleClean = (room.title || 'Room').replace(/\s+/g, '_');
        triggerFileDownload(blob, `CareerFlow_Room_${room.id}_${titleClean}_Applicants.xlsx`);
        notify?.('Applicants Excel export downloaded successfully.', 'success');
      }
    } catch {
      notify?.(`Failed to export applicants as ${format.toUpperCase()}.`, 'error');
    } finally {
      setExportingFormat(null);
    }
  };

  const toggleApplicantSelection = (appId: number) => {
    setSelectedAppIds((prev) => {
      if (prev.includes(appId)) {
        return prev.filter((id) => id !== appId);
      }
      return [...prev, appId];
    });
  };

  const rankedAppIds = useMemo(() => {
    return data?.results.map((r) => r.application_id) || [];
  }, [data]);

  const allRankedSelected = useMemo(() => {
    return (
      rankedAppIds.length > 0 &&
      rankedAppIds.every((id) => selectedAppIds.includes(id))
    );
  }, [rankedAppIds, selectedAppIds]);

  const toggleSelectAll = () => {
    if (allRankedSelected) {
      setSelectedAppIds([]);
    } else {
      setSelectedAppIds(rankedAppIds);
    }
  };

  const clearSelection = () => {
    setSelectedAppIds([]);
  };

  const handleBulkShortlist = async () => {
    if (selectedAppIds.length === 0) return;
    try {
      for (const id of selectedAppIds) {
        await apiSubmitCandidateDecision(id, {
          decision: 'CONFIRMED',
          notes: 'Bulk shortlist confirmation from Leaderboard',
        });
      }
      notify?.(`Shortlisted ${selectedAppIds.length} candidate(s)`, 'success');
      clearSelection();
      fetchRankings(false);
    } catch {
      notify?.('Failed to bulk shortlist some candidates.', 'error');
    }
  };

  const handleBulkReject = async () => {
    if (selectedAppIds.length === 0) return;
    try {
      for (const id of selectedAppIds) {
        await apiSubmitCandidateDecision(id, {
          decision: 'REJECTED',
          notes: 'Bulk rejection from Leaderboard',
        });
      }
      notify?.(`Rejected ${selectedAppIds.length} candidate(s)`, 'info');
      clearSelection();
      fetchRankings(false);
    } catch {
      notify?.('Failed to bulk reject some candidates.', 'error');
    }
  };

  const fetchRankings = async (showLoadingSpinner = true) => {
    if (!room) return;
    try {
      if (showLoadingSpinner) setLoading(true);
      setError(null);
      const res = await apiGetRankedApplicants(room.id, {
        min_score: minScoreFilter > 0 ? minScoreFilter : undefined,
        search: searchQuery.trim() || undefined,
        ordering: sortBy,
        include_unranked: true,
        shortlisted: shortlistedOnly ? true : undefined,
        stage: selectedStageFilter !== 'ALL' ? selectedStageFilter : undefined,
      });
      setData(res);
    } catch (err: any) {
      const msg = err?.response?.data?.error || 'Failed to fetch ranked applicants.';
      setError(msg);
      notify?.(msg, 'error');
    } finally {
      if (showLoadingSpinner) setLoading(false);
    }
  };

  useEffect(() => {
    if (!isOpen || !room) {
      setData(null);
      setError(null);
      setSearchQuery('');
      setMinScoreFilter(0);
      setSortBy('-final_score');
      setActiveTab('RANKED');
      setSelectedAppIds([]);
      setIsComparisonModalOpen(false);
      setShortlistedOnly(false);
      setExportMenuOpen(false);
      setExportingFormat(null);
      return;
    }

    setSelectedAppIds([]);
    setIsComparisonModalOpen(false);
    fetchRankings(true);
  }, [isOpen, room]);

  // Re-fetch when sorting, min-score, or shortlisted filter changes
  useEffect(() => {
    if (isOpen && room) {
      fetchRankings(false);
    }
  }, [sortBy, minScoreFilter, shortlistedOnly, selectedStageFilter]);

  const handleRecalculateScores = async () => {
    if (!room) return;
    try {
      setRecalculating(true);
      const res = await apiCalculateRoomScores(room.id);
      notify?.(
        `Recalculated scores for ${res.processed_count} applicants using ${res.weights_used.cv_weight}% CV / ${res.weights_used.video_weight}% Video.`,
        'success'
      );
      await fetchRankings(false);
    } catch (err: any) {
      const msg = err?.response?.data?.error || 'Failed to recalculate applicant scores.';
      notify?.(msg, 'error');
    } finally {
      setRecalculating(false);
    }
  };

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    const day = d.getDate();
    const month = d.toLocaleString('en-US', { month: 'short' });
    const year = d.getFullYear();
    return `${day} ${month} ${year}`;
  };

  const getRankBadgeElement = (rank: number) => {
    if (rank === 1) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#fef3c7] text-[#92400e] border border-[#fde68a] shadow-2xs whitespace-nowrap">
          <Trophy className="w-4 h-4 text-amber-500 fill-amber-400 shrink-0" />
          Rank #1
        </span>
      );
    }
    if (rank === 2) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#f1f3f5] text-[#526072] border border-[#d9dbd1] shadow-2xs whitespace-nowrap">
          <Medal className="w-4 h-4 text-slate-400 fill-slate-300 shrink-0" />
          Rank #2
        </span>
      );
    }
    if (rank === 3) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#fdf2e9] text-[#a04000] border border-[#f5cba7] shadow-2xs whitespace-nowrap">
          <Medal className="w-4 h-4 text-amber-700 fill-amber-600 shrink-0" />
          Rank #3
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-[#f8f9fa] text-[#526072] border border-[#d9dbd1] whitespace-nowrap">
        #{rank}
      </span>
    );
  };

  const getScoreBadgeColor = (score: number) => {
    if (score >= 75) {
      return 'bg-[#e2f0e9] text-[#1f5b43] border-[#a7d7c1]';
    }
    if (score >= 50) {
      return 'bg-[#fef3c7] text-[#92400e] border-[#fde68a]';
    }
    return 'bg-[#fde8e8] text-[#9b1c1c] border-[#f8b4b4]';
  };

  const getScoreBarColor = (score: number) => {
    if (score >= 75) return 'bg-[#277254]';
    if (score >= 50) return 'bg-[#d97706]';
    return 'bg-[#e02424]';
  };

  const isTiedWithHigher = (applicant: RankedApplicantItem, index: number) => {
    if (index === 0 || !data?.results) return false;
    const prev = data.results[index - 1];
    return prev !== undefined && Math.abs(prev.final_score - applicant.final_score) < 0.001;
  };

  if (!isOpen || !room) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-5 bg-[#253142]/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div
        ref={modalRef}
        className="relative w-full max-w-6xl bg-white rounded-2xl shadow-2xl border border-[#d9dbd1] flex flex-col max-h-[92vh] overflow-hidden"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ranked-modal-title"
        data-testid="modal-ranked-applicants"
      >
        {/* HEADER */}
        <div className="relative flex flex-col sm:flex-row sm:items-center justify-between gap-3.5 px-4 sm:px-6 py-4 border-b border-[#eef0e7] bg-[#fbfaf5] shrink-0">
          {/* Trophy + Title / Subtitle Block (flex: 1, min-width: 0) */}
          <div className="flex items-center gap-3 flex-1 min-w-0 pr-10 sm:pr-0">
            <div className="p-2.5 rounded-xl bg-amber-50 text-amber-600 border border-amber-200/60 shrink-0">
              <Trophy className="w-5 h-5 text-amber-500 fill-amber-400" />
            </div>
            <div className="min-w-0 flex-1">
              <h2
                id="ranked-modal-title"
                data-testid="text-ranked-modal-title"
                className="text-base sm:text-xl font-bold text-[#253142] truncate"
              >
                Applicant Leaderboard & Rankings
              </h2>
              <div className="flex items-center flex-wrap gap-2 mt-1">
                <span className="text-xs text-[#7b8490] truncate">
                  {room.title} • {room.company_name}{room.department ? ` (${room.department})` : ''}
                </span>
                <span className="inline-flex items-center text-[11px] px-2.5 py-0.5 rounded-full font-semibold bg-[#e2f0e9] text-[#1f5b43] border border-[#a7d7c1] whitespace-nowrap">
                  Weights: {room.cv_weight}% CV / {room.video_weight}% Video
                </span>
              </div>
            </div>
          </div>

          {/* Action Group */}
          <div className="flex items-center flex-wrap gap-2 shrink-0">
            {/* Primary: Export Data Dropdown */}
            <div className="relative" ref={exportMenuRef}>
              <button
                type="button"
                onClick={() => setExportMenuOpen((prev) => !prev)}
                disabled={!!exportingFormat}
                title="Export candidates as CSV or Excel"
                data-testid="button-export-applicants"
                className="h-10 px-3.5 sm:px-4 inline-flex items-center gap-2 text-xs font-bold rounded-xl bg-[#277254] hover:bg-[#1f5b43] text-white transition-colors disabled:opacity-50 shadow-xs whitespace-nowrap cursor-pointer"
                aria-haspopup="true"
                aria-expanded={exportMenuOpen}
              >
                {exportingFormat ? (
                  <Loader2 className="w-4 h-4 animate-spin shrink-0" />
                ) : (
                  <FileSpreadsheet className="w-4 h-4 shrink-0" />
                )}
                <span>{exportingFormat ? `Exporting ${exportingFormat.toUpperCase()}...` : 'Export Data'}</span>
                <ChevronDown className={`w-3.5 h-3.5 shrink-0 transition-transform ${exportMenuOpen ? 'rotate-180' : ''}`} />
              </button>
              {exportMenuOpen && (
                <div className="absolute right-0 mt-1.5 w-52 bg-white rounded-xl shadow-xl border border-[#d9dbd1] py-1.5 z-50 animate-in fade-in zoom-in-95 duration-100">
                  <button
                    type="button"
                    onClick={() => handleExport('csv')}
                    data-testid="button-export-csv"
                    className="w-full flex items-center gap-2.5 px-3.5 py-2 text-xs text-left text-[#253142] hover:bg-[#fbfaf5] transition-colors cursor-pointer"
                  >
                    <FileText className="w-4 h-4 text-blue-500 shrink-0" />
                    <div>
                      <div className="font-semibold">Export as CSV</div>
                      <div className="text-[10px] text-[#7b8490]">Streamed UTF-8 with BOM</div>
                    </div>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleExport('excel')}
                    data-testid="button-export-excel"
                    className="w-full flex items-center gap-2.5 px-3.5 py-2 text-xs text-left text-[#253142] hover:bg-[#fbfaf5] transition-colors cursor-pointer"
                  >
                    <FileSpreadsheet className="w-4 h-4 text-[#277254] shrink-0" />
                    <div>
                      <div className="font-semibold">Export as Excel (.xlsx)</div>
                      <div className="text-[10px] text-[#7b8490]">Styled workbook with metrics</div>
                    </div>
                  </button>
                </div>
              )}
            </div>

            {/* Secondary: Download Summary Report */}
            <button
              type="button"
              onClick={handleDownloadRoomSummaryPdf}
              disabled={downloadingPdf}
              title="Download complete room assessment report as PDF"
              data-testid="button-download-room-summary-pdf"
              className="h-10 px-3.5 sm:px-4 inline-flex items-center gap-2 text-xs font-bold rounded-xl border border-[#277254] text-[#277254] bg-white hover:bg-[#e2f0e9]/50 transition-colors disabled:opacity-50 whitespace-nowrap cursor-pointer shadow-2xs"
            >
              {downloadingPdf ? (
                <Loader2 className="w-4 h-4 animate-spin text-[#277254] shrink-0" />
              ) : (
                <Download className="w-4 h-4 text-[#277254] shrink-0" />
              )}
              <span>{downloadingPdf ? 'Exporting PDF...' : 'Download Summary Report'}</span>
            </button>

            {/* Ghost: Refresh Scores */}
            <button
              type="button"
              onClick={handleRecalculateScores}
              disabled={recalculating}
              title="Refresh Scores"
              aria-label="Refresh Scores"
              data-testid="button-recalculate-scores"
              className="h-10 w-10 inline-flex items-center justify-center rounded-xl border border-[#d9dbd1] bg-white text-[#526072] hover:text-[#253142] hover:bg-[#fbfaf5] transition-colors disabled:opacity-50 cursor-pointer shrink-0 shadow-2xs"
            >
              <RefreshCw className={`w-4 h-4 ${recalculating ? 'animate-spin text-[#277254]' : ''}`} />
            </button>

            {/* Close Button: Absolute top-right on mobile, inline in action group on desktop */}
            <button
              type="button"
              onClick={onClose}
              data-testid="button-close-ranked-modal"
              aria-label="Close modal"
              className="absolute top-3.5 right-3.5 sm:static h-10 w-10 inline-flex items-center justify-center text-[#7b8490] hover:text-[#253142] hover:bg-[#eef0e7] rounded-xl transition-colors cursor-pointer shrink-0"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* STATS BAR (4 equal columns on desktop, 2x2 on mobile) */}
        {data && (
          <div
            data-testid="row-statistical-summary"
            className="grid grid-cols-2 md:grid-cols-4 gap-3 px-4 sm:px-6 py-3 bg-[#fbfaf5] border-b border-[#eef0e7] text-xs shrink-0"
          >
            <div className="flex items-center gap-2 min-w-0">
              <Users className="w-4 h-4 text-blue-500 shrink-0" />
              <span className="text-[#7b8490] whitespace-nowrap">Total Applicants:</span>
              <span data-testid="stat-ranked-total" className="font-bold text-[#253142]">
                {data.total_applicants}
              </span>
            </div>
            <div className="flex items-center gap-2 min-w-0">
              <Trophy className="w-4 h-4 text-emerald-600 shrink-0" />
              <span className="text-[#7b8490] whitespace-nowrap">Ranked Candidates:</span>
              <span data-testid="stat-ranked-count" className="font-bold text-[#277254]">
                {data.ranked_count}
              </span>
            </div>
            <div className="flex items-center gap-2 min-w-0">
              <Clock className="w-4 h-4 text-amber-600 shrink-0" />
              <span className="text-[#7b8490] whitespace-nowrap">Incomplete / Pending:</span>
              <span data-testid="stat-unranked-count" className="font-bold text-[#92400e]">
                {data.unranked_count}
              </span>
            </div>
            <div className="flex items-center gap-2 min-w-0">
              <Gauge className="w-4 h-4 text-purple-600 shrink-0" />
              <span className="text-[#7b8490] whitespace-nowrap">Top Score:</span>
              <span data-testid="stat-top-score" className="font-bold text-purple-700">
                {data.results.length > 0 ? `${data.results[0].final_score.toFixed(1)}/100` : '—'}
              </span>
            </div>
          </div>
        )}

        {/* CONTROLS SECTION (TABS + RESTRUCTURED FILTER TOOLBAR) */}
        <div className="px-4 sm:px-6 py-3 border-b border-[#eef0e7] bg-white space-y-3 shrink-0">
          {/* TABS (Equal width, 1 line, badges) */}
          <div className="flex sm:grid sm:grid-cols-2 gap-1 p-1 bg-[#eef0e7] rounded-xl w-full overflow-x-auto [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden">
            <button
              type="button"
              onClick={() => setActiveTab('RANKED')}
              data-testid="tab-ranked-leaderboard"
              className={`flex-1 sm:flex-initial min-w-fit sm:min-w-0 flex items-center justify-center gap-1.5 sm:gap-2 py-2 px-2.5 sm:px-3 text-xs font-bold rounded-lg transition-colors whitespace-nowrap cursor-pointer ${
                activeTab === 'RANKED'
                  ? 'bg-white text-[#253142] shadow-xs'
                  : 'text-[#687382] hover:text-[#253142]'
              }`}
            >
              <Trophy className="w-4 h-4 text-amber-500 shrink-0" />
              <span>Ranked Leaderboard</span>
              <span
                className={`text-[10px] px-1.5 py-0.5 rounded-full font-bold shrink-0 ${
                  activeTab === 'RANKED'
                    ? 'bg-[#e2f0e9] text-[#1f5b43]'
                    : 'bg-[#d9dbd1] text-[#526072]'
                }`}
              >
                {data?.ranked_count ?? 0}
              </span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('UNRANKED')}
              data-testid="tab-unranked-leaderboard"
              className={`flex-1 sm:flex-initial min-w-fit sm:min-w-0 flex items-center justify-center gap-1.5 sm:gap-2 py-2 px-2.5 sm:px-3 text-xs font-bold rounded-lg transition-colors whitespace-nowrap cursor-pointer ${
                activeTab === 'UNRANKED'
                  ? 'bg-white text-[#253142] shadow-xs'
                  : 'text-[#687382] hover:text-[#253142]'
              }`}
            >
              <Clock className="w-4 h-4 text-amber-600 shrink-0" />
              <span>Evaluation In Progress</span>
              <span
                className={`text-[10px] px-1.5 py-0.5 rounded-full font-bold shrink-0 ${
                  activeTab === 'UNRANKED'
                    ? 'bg-[#fef3c7] text-[#92400e]'
                    : 'bg-[#d9dbd1] text-[#526072]'
                }`}
              >
                {data?.unranked_count ?? 0}
              </span>
            </button>
          </div>

          {/* FILTER TOOLBAR: ROW 1 (Search + Min Score Slider + Sort Dropdown + Shortlisted Toggle) */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Search Input (flex:1, min-width 260px, never clipped) */}
            <div className="relative flex-1 min-w-[260px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#7b8490]" />
              <input
                type="text"
                data-testid="input-ranked-search"
                placeholder="Search name or email"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && fetchRankings(false)}
                className="w-full pl-9 pr-3 h-10 text-xs rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] text-[#253142] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#277254]/30"
              />
            </div>

            {/* Min Score Filter Slider (0-100 range with visible label) */}
            {activeTab === 'RANKED' && (
              <div className="inline-flex items-center gap-2 px-3 h-10 rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] text-xs text-[#253142] whitespace-nowrap shrink-0">
                <SlidersHorizontal className="w-4 h-4 text-[#7b8490] shrink-0" />
                <span data-testid="text-min-score-indicator">
                  Min: <strong className="font-bold">{minScoreFilter}</strong>
                </span>
                <input
                  type="range"
                  data-testid="slider-min-score"
                  min="0"
                  max="100"
                  step="5"
                  value={minScoreFilter}
                  onChange={(e) => setMinScoreFilter(parseInt(e.target.value, 10))}
                  className="w-20 accent-[#277254] cursor-pointer"
                  title={`Filter applicants with final score >= ${minScoreFilter}`}
                />
              </div>
            )}

            {/* Sort Dropdown (with sort icon adornment inside on the left) */}
            {activeTab === 'RANKED' && (
              <div className="relative inline-flex items-center shrink-0 min-w-[190px]">
                <ArrowUpDown className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#7b8490] pointer-events-none" />
                <select
                  data-testid="select-ranked-sort"
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as SortOption)}
                  className="w-full pl-9 pr-7 h-10 text-xs font-semibold rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] text-[#253142] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#277254]/30 cursor-pointer appearance-none"
                >
                  <option value="-final_score">Final Score (High to Low)</option>
                  <option value="final_score">Final Score (Low to High)</option>
                  <option value="-cv_score">CV Match Score (High to Low)</option>
                  <option value="-video_score">Video Presentation (High to Low)</option>
                  <option value="-applied_at">Newest First</option>
                  <option value="applied_at">Oldest First</option>
                </select>
                <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#7b8490] pointer-events-none" />
              </div>
            )}

            {/* Shortlisted Only Toggle */}
            <button
              type="button"
              data-testid="button-filter-shortlisted-only"
              onClick={() => setShortlistedOnly((prev) => !prev)}
              className={`inline-flex items-center gap-1.5 px-3 h-10 rounded-xl text-xs font-bold border transition-all whitespace-nowrap cursor-pointer shrink-0 ${
                shortlistedOnly
                  ? 'bg-[#e2f0e9] text-[#1f5b43] border-[#a7d7c1] shadow-2xs'
                  : 'bg-[#fbfaf5] text-[#526072] border-[#d9dbd1] hover:bg-[#eef0e7]'
              }`}
              title="Filter by shortlisted candidates only"
            >
              <CheckCircle2
                className={`w-4 h-4 ${shortlistedOnly ? 'text-[#277254]' : 'text-[#7b8490]'}`}
              />
              <span>Shortlisted Only</span>
            </button>
          </div>

          {/* FILTER TOOLBAR: ROW 2 (Horizontally scrollable stage chips, no divider, inline label) */}
          <div className="flex items-center gap-2 overflow-x-auto whitespace-nowrap py-0.5 [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden">
            <span className="text-xs font-bold text-[#526072] flex items-center gap-1 shrink-0">
              <GitCommit className="w-4 h-4 text-indigo-600 shrink-0" />
              Stage:
            </span>
            {[
              { key: 'ALL', label: 'All Stages', testId: 'filter-stage-all' },
              { key: 'APPLIED', label: 'Applied', testId: 'filter-stage-applied' },
              { key: 'UNDER_REVIEW', label: 'Under Review', testId: 'filter-stage-under-review' },
              { key: 'SHORTLISTED', label: 'Shortlisted', testId: 'filter-stage-shortlisted' },
              { key: 'INTERVIEW_ROUND_1', label: 'Round 1', testId: 'filter-stage-round1' },
              { key: 'INTERVIEW_ROUND_2', label: 'Round 2', testId: 'filter-stage-round2' },
              { key: 'OFFERED', label: 'Offered', testId: 'filter-stage-offered' },
              { key: 'HIRED', label: 'Hired', testId: 'filter-stage-hired' },
              { key: 'REJECTED', label: 'Rejected', testId: 'filter-stage-rejected' },
            ].map((pill) => (
              <button
                key={pill.key}
                type="button"
                data-testid={pill.testId}
                onClick={() => setSelectedStageFilter(pill.key)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition shrink-0 cursor-pointer whitespace-nowrap ${
                  selectedStageFilter === pill.key
                    ? 'bg-[#253142] text-white shadow-2xs'
                    : 'bg-[#fbfaf5] border border-[#d9dbd1] text-[#526072] hover:bg-[#eef0e7]'
                }`}
              >
                {pill.label}
              </button>
            ))}
          </div>
        </div>

        {/* MODAL BODY (Internal scroll, max-height calc(100vh - 160px)) */}
        <div className="flex-1 overflow-y-auto p-3 sm:p-6 space-y-3 bg-[#faf9f5] max-h-[calc(100vh-160px)]">
          {loading ? (
            <div className="py-20 flex flex-col items-center justify-center gap-3 text-[#7b8490]">
              <RefreshCw className="w-8 h-8 animate-spin text-[#277254]" />
              <p className="text-sm font-medium">Computing and organizing applicant rankings...</p>
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl bg-[#fde8e8] border border-[#f8b4b4] text-[#9b1c1c] flex items-center gap-3">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <p className="text-sm">{error}</p>
            </div>
          ) : activeTab === 'RANKED' ? (
            data?.results.length === 0 ? (
              <div className="py-16 text-center text-[#7b8490]">
                <Trophy className="w-12 h-12 mx-auto stroke-1 text-[#d9dbd1] mb-2" />
                <p className="text-base font-semibold text-[#253142]">
                  No ranked candidates found
                </p>
                <p className="text-xs text-[#7b8490] mt-1">
                  {minScoreFilter > 0
                    ? `No candidates meet the minimum score threshold of ${minScoreFilter}. Try lowering the filter slider.`
                    : 'Candidates with completed evaluations will appear on this leaderboard.'}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto pb-2 [scrollbar-width:thin]">
                <div className="min-w-[820px] space-y-2.5">
                  {/* Table Header with Select-All Checkbox */}
                  <div className="grid grid-cols-[24px_120px_minmax(220px,1fr)_auto_auto_auto] items-center gap-4 px-4 py-2 text-[11px] font-bold text-[#7b8490] uppercase tracking-wider border-b border-[#eef0e7]">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        checked={allRankedSelected}
                        onChange={toggleSelectAll}
                        aria-label="Select all ranked applicants"
                        title="Select all applicants"
                        className="w-4 h-4 rounded border-[#d9dbd1] text-[#277254] focus:ring-[#277254] accent-[#277254] cursor-pointer"
                      />
                    </div>
                    <div>Rank</div>
                    <div>Candidate Info</div>
                    <div>Score Components</div>
                    <div className="text-right">Final Score</div>
                    <div className="text-right">Actions</div>
                  </div>

                  {/* Candidate Cards Grid */}
                  {data?.results.map((applicant, idx) => {
                    const isTied = isTiedWithHigher(applicant, idx);
                    return (
                      <div
                        key={applicant.application_id}
                        data-testid={`card-ranked-applicant-${applicant.rank}`}
                        className={`p-4 rounded-xl border transition-all duration-150 grid grid-cols-[24px_120px_minmax(220px,1fr)_auto_auto_auto] items-center gap-4 bg-white hover:shadow-xs ${
                          applicant.rank === 1
                            ? 'border-amber-300/80 bg-gradient-to-r from-amber-50/30 via-white to-transparent'
                            : applicant.rank === 2
                            ? 'border-slate-300 bg-gradient-to-r from-slate-50/40 via-white to-transparent'
                            : applicant.rank === 3
                            ? 'border-amber-600/30 bg-gradient-to-r from-amber-900/5 via-white to-transparent'
                            : 'border-[#d9dbd1]'
                        }`}
                      >
                        {/* 1. Checkbox */}
                        <div className="flex items-center">
                          <input
                            type="checkbox"
                            data-testid={`checkbox-compare-${applicant.application_id}`}
                            aria-label={`Select ${applicant.candidate_name || 'candidate'}`}
                            checked={selectedAppIds.includes(applicant.application_id)}
                            onChange={() => toggleApplicantSelection(applicant.application_id)}
                            className="w-4 h-4 rounded border-[#d9dbd1] text-[#277254] focus:ring-[#277254] accent-[#277254] cursor-pointer transition"
                          />
                        </div>

                        {/* 2. Rank Badge */}
                        <div className="flex flex-col items-start gap-1" data-testid={`badge-rank-${applicant.rank}`}>
                          {getRankBadgeElement(applicant.rank)}
                          {isTied && (
                            <span
                              className="inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded bg-[#fef3c7] text-[#92400e] border border-[#fde68a] cursor-help max-w-[115px] truncate"
                              title="Tie – ranked by submission date"
                            >
                              <Clock className="w-3 h-3 text-[#d97706] shrink-0" />
                              <span className="truncate">Tie (by date)</span>
                            </span>
                          )}
                        </div>

                        {/* 3. Candidate Info (Name with ellipsis & tooltip, email, date, stage chip) */}
                        <div className="min-w-0 pr-2">
                          <h3
                            data-testid={`text-candidate-name-${applicant.rank}`}
                            title={applicant.candidate_name || 'Anonymous Candidate'}
                            className="text-sm font-bold text-[#253142] truncate"
                          >
                            {applicant.candidate_name || 'Anonymous Candidate'}
                          </h3>
                          <p
                            data-testid={`text-candidate-email-${applicant.rank}`}
                            title={applicant.candidate_email}
                            className="text-xs text-[#7b8490] truncate mt-0.5"
                          >
                            {applicant.candidate_email}
                          </p>
                          <p className="text-[11px] text-[#9aabb5] mt-0.5">
                            Applied: {formatDate(applicant.applied_at)}
                          </p>
                          <div className="mt-1 flex items-center gap-1.5 flex-wrap">
                            <span
                              data-testid={`badge-candidate-stage-${applicant.rank}`}
                              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200 whitespace-nowrap"
                            >
                              <GitCommit className="w-3 h-3 text-indigo-500 shrink-0" />
                              {applicant.stage_display || applicant.stage || 'Applied'}
                            </span>
                            {applicant.is_partial_score && (
                              <span
                                data-testid={`badge-partial-score-${applicant.rank}`}
                                className="text-[10px] px-1.5 py-0.5 rounded font-medium bg-amber-100 text-amber-800 border border-amber-200 whitespace-nowrap"
                              >
                                Partial Evaluation
                              </span>
                            )}
                          </div>
                        </div>

                        {/* 4. Score Component Chips (Always side by side, nowrap) */}
                        <div className="flex items-center gap-2 flex-nowrap whitespace-nowrap">
                          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#fbfaf5] border border-[#d9dbd1] text-xs shrink-0">
                            <FileText className="w-4 h-4 text-[#277254] shrink-0" />
                            <span className="text-[#7b8490]">CV ({room.cv_weight}%):</span>
                            <span
                              data-testid={`text-cv-score-${applicant.rank}`}
                              className="font-bold text-[#253142]"
                            >
                              {applicant.cv_score !== null ? `${applicant.cv_score.toFixed(1)}` : 'N/A'}
                            </span>
                          </div>

                          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#fbfaf5] border border-[#d9dbd1] text-xs shrink-0">
                            <Video className="w-4 h-4 text-purple-600 shrink-0" />
                            <span className="text-[#7b8490]">Video ({room.video_weight}%):</span>
                            <span
                              data-testid={`text-video-score-${applicant.rank}`}
                              className="font-bold text-[#253142]"
                            >
                              {applicant.video_score !== null ? `${applicant.video_score.toFixed(1)}` : 'N/A'}
                            </span>
                          </div>
                        </div>

                        {/* 5. Final Composite Score Meter */}
                        <div className="text-right whitespace-nowrap">
                          <div
                            data-testid={`text-final-score-${applicant.rank}`}
                            className={`inline-flex items-center gap-1 px-3 py-1 rounded-xl font-bold text-sm border shadow-2xs ${getScoreBadgeColor(
                              applicant.final_score
                            )}`}
                          >
                            <Gauge className="w-4 h-4 shrink-0" />
                            <span>{applicant.final_score.toFixed(1)}</span>
                            <span className="text-[10px] opacity-70">/100</span>
                          </div>
                          <div className="w-24 h-1.5 bg-[#eef0e7] rounded-full mt-1.5 ml-auto overflow-hidden">
                            <div
                              className={`h-full rounded-full ${getScoreBarColor(applicant.final_score)}`}
                              style={{ width: `${Math.min(100, applicant.final_score)}%` }}
                            />
                          </div>
                        </div>

                        {/* 6. Actions (Notes & Breakdown buttons) */}
                        <div className="flex items-center justify-end gap-2 whitespace-nowrap">
                          <button
                            type="button"
                            data-testid={`button-open-notes-${applicant.application_id}`}
                            onClick={() => {
                              setNotesAppId(applicant.application_id);
                              setNotesCandidateName(applicant.candidate_name);
                              setNotesCandidateEmail(applicant.candidate_email);
                              setNotesCurrentStage(applicant.stage || 'APPLIED');
                              setNotesModalOpen(true);
                            }}
                            className="h-8 px-2.5 rounded-lg border border-blue-200 bg-blue-50/60 hover:bg-blue-600 hover:text-white text-blue-700 font-semibold text-xs transition inline-flex items-center gap-1.5 shadow-2xs cursor-pointer"
                            title="Internal Recruiter Notes & Stage"
                          >
                            <MessageSquare className="w-4 h-4 shrink-0" />
                            <span>Notes</span>
                            {(applicant.notes_count ?? 0) > 0 && (
                              <span
                                data-testid={`badge-notes-count-${applicant.application_id}`}
                                className="px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-blue-600 text-white"
                              >
                                {applicant.notes_count}
                              </span>
                            )}
                          </button>

                          <button
                            type="button"
                            data-testid={`btn-score-breakdown-${applicant.application_id}`}
                            onClick={() => {
                              setBreakdownAppId(applicant.application_id);
                              setBreakdownCandidateName(applicant.candidate_name);
                            }}
                            className="h-8 px-2.5 rounded-lg border border-indigo-200 bg-indigo-50/60 hover:bg-indigo-600 hover:text-white text-indigo-700 font-semibold text-xs transition inline-flex items-center gap-1.5 shadow-2xs cursor-pointer"
                            title="View Explainable Score Breakdown"
                          >
                            <Calculator className="w-4 h-4 shrink-0" />
                            <span>Breakdown</span>
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )
          ) : (
            /* Unranked / Evaluation In Progress View */
            <div className="space-y-4">
              <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-800 flex items-start gap-2.5">
                <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <p>
                  These candidates do not have a calculated final score yet due to pending CV parsing, speech processing, or behavioral analysis. They are isolated from the ranked leaderboard to ensure accurate percentile ranking.
                </p>
              </div>

              {data?.unranked.length === 0 ? (
                <div className="py-16 text-center text-[#7b8490]">
                  <CheckCircle2 className="w-12 h-12 mx-auto stroke-1 text-emerald-500 mb-2" />
                  <p className="text-sm font-semibold text-[#253142]">
                    All candidates have been evaluated!
                  </p>
                  <p className="text-xs text-[#7b8490] mt-1">
                    Zero applications are pending analysis in this room.
                  </p>
                </div>
              ) : (
                <div className="space-y-2.5">
                  {data?.unranked.map((unrankedApp) => (
                    <div
                      key={unrankedApp.application_id}
                      data-testid={`card-unranked-applicant-${unrankedApp.application_id}`}
                      className="p-3.5 rounded-xl border border-[#d9dbd1] bg-white flex items-center justify-between gap-4 text-xs"
                    >
                      <div>
                        <h4
                          data-testid={`text-unranked-name-${unrankedApp.application_id}`}
                          className="font-bold text-[#253142]"
                        >
                          {unrankedApp.candidate_name || 'Anonymous Candidate'}
                        </h4>
                        <p className="text-[#7b8490]">
                          {unrankedApp.candidate_email}
                        </p>
                      </div>

                      <div className="flex items-center gap-3">
                        <span
                          data-testid={`text-unranked-reason-${unrankedApp.application_id}`}
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full font-medium bg-amber-100 text-amber-800 border border-amber-200"
                        >
                          <Clock className="w-3.5 h-3.5" />
                          {unrankedApp.pending_reason}
                        </span>
                        <span className="text-[#9aabb5] text-[11px]">
                          Applied {formatDate(unrankedApp.applied_at)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* BULK SELECTION & COMPARISON STICKY BOTTOM BAR */}
        {activeTab === 'RANKED' && selectedAppIds.length > 0 && (
          <div
            data-testid="bar-applicant-comparison"
            className="sticky bottom-0 z-30 px-4 sm:px-6 py-3 bg-white/95 backdrop-blur-md border-t border-[#d9dbd1] shadow-[0_-4px_16px_rgba(0,0,0,0.08)] flex flex-wrap items-center justify-between gap-3 animate-in fade-in slide-in-from-bottom-2 duration-150"
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-[#e2f0e9] text-[#277254] flex items-center justify-center font-bold text-xs border border-[#a7d7c1]">
                {selectedAppIds.length}
              </div>
              <div>
                <p className="text-xs font-bold text-[#253142]">
                  {selectedAppIds.length} candidate{selectedAppIds.length > 1 ? 's' : ''} selected
                </p>
                <p className="text-[11px] text-[#7b8490]">
                  Perform bulk actions or side-by-side comparison
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              <button
                type="button"
                onClick={handleBulkShortlist}
                className="h-8 px-3 rounded-lg text-xs font-bold bg-[#e2f0e9] text-[#1f5b43] border border-[#a7d7c1] hover:bg-[#d0e8dc] transition inline-flex items-center gap-1.5 cursor-pointer whitespace-nowrap shadow-2xs"
              >
                <CheckCircle2 className="w-3.5 h-3.5 text-[#277254]" />
                <span>Shortlist</span>
              </button>
              <button
                type="button"
                onClick={handleBulkReject}
                className="h-8 px-3 rounded-lg text-xs font-bold bg-[#fde8e8] text-[#9b1c1c] border border-[#f8b4b4] hover:bg-[#fcd0d0] transition inline-flex items-center gap-1.5 cursor-pointer whitespace-nowrap shadow-2xs"
              >
                <XCircle className="w-3.5 h-3.5 text-[#e02424]" />
                <span>Reject</span>
              </button>
              <button
                type="button"
                onClick={() => handleExport('csv')}
                className="h-8 px-3 rounded-lg text-xs font-bold bg-[#fbfaf5] text-[#253142] border border-[#d9dbd1] hover:bg-[#eef0e7] transition inline-flex items-center gap-1.5 cursor-pointer whitespace-nowrap shadow-2xs"
              >
                <Download className="w-3.5 h-3.5 text-[#277254]" />
                <span>Export</span>
              </button>
              {selectedAppIds.length >= 2 && selectedAppIds.length <= 4 && (
                <button
                  type="button"
                  data-testid="btn-compare-now"
                  onClick={() => setIsComparisonModalOpen(true)}
                  className="h-8 px-3.5 rounded-lg text-xs font-bold bg-[#253142] text-white hover:bg-[#344458] transition inline-flex items-center gap-1.5 cursor-pointer whitespace-nowrap shadow-xs"
                >
                  <Scale className="w-3.5 h-3.5" />
                  <span>Compare ({selectedAppIds.length})</span>
                </button>
              )}
              <button
                type="button"
                data-testid="btn-clear-selection"
                onClick={clearSelection}
                className="h-8 px-3 rounded-lg text-xs font-medium text-[#7b8490] hover:text-[#253142] hover:bg-[#fbfaf5] transition cursor-pointer whitespace-nowrap"
              >
                Clear
              </button>
            </div>
          </div>
        )}

        {/* MODAL FOOTER */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 px-4 sm:px-6 py-3 border-t border-[#eef0e7] bg-[#fbfaf5] text-xs text-[#7b8490] shrink-0">
          <div className="flex items-center gap-2 text-center sm:text-left text-[11px] sm:text-xs">
            <Sparkles className="w-4 h-4 text-[#277254] shrink-0" />
            <span>Deterministic Tie-Breaking: CV Match &gt; Video Score &gt; Submission Date</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="w-full sm:w-auto px-4 py-2 rounded-xl text-xs font-bold bg-[#253142] text-white hover:bg-[#344458] transition-colors cursor-pointer shrink-0"
          >
            Close Leaderboard
          </button>
        </div>
      </div>

      {/* US-27: Explainable Applicant Score Breakdown Modal */}
      {breakdownAppId && (
        <ScoreBreakdownModal
          isOpen={Boolean(breakdownAppId)}
          onClose={() => setBreakdownAppId(null)}
          applicationId={breakdownAppId}
          candidateName={breakdownCandidateName}
          notify={notify}
        />
      )}

      {/* US-47: Recruiter Notes & Pipeline Stage Management Modal */}
      {notesModalOpen && notesAppId && room && (
        <RecruiterNotesModal
          isOpen={notesModalOpen}
          onClose={() => setNotesModalOpen(false)}
          applicationId={notesAppId}
          candidateName={notesCandidateName}
          candidateEmail={notesCandidateEmail}
          roomTitle={room.title}
          currentStage={notesCurrentStage}
          onStageUpdated={() => fetchRankings(false)}
          onNoteCountChanged={() => fetchRankings(false)}
          notify={notify}
        />
      )}

      {/* US-28: Side-by-Side Applicant Comparison Modal */}
      {isComparisonModalOpen && room && (
        <ApplicantComparisonModal
          isOpen={isComparisonModalOpen}
          onClose={() => setIsComparisonModalOpen(false)}
          roomId={room.id}
          roomTitle={room.title}
          applicationIds={selectedAppIds}
          notify={notify}
        />
      )}
    </div>
  );
}
