import { useState, useEffect, useMemo, useRef } from 'react';
import { useLocation } from 'wouter';
import {
  Users,
  Search,
  ArrowUpDown,
  Download,
  CheckCircle2,
  Clock,
  Building2,
  Layers,
  Loader2,
  RefreshCw,
  Plus,
  Sliders,
  RotateCcw,
  Undo2,
  Sparkles,
  ChevronDown
} from 'lucide-react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { AppShell } from '../components/layout/AppShell';
import { PageHeading, type Notify } from '../components/dashboard/DashboardShared';
import {
  apiGetRooms,
  apiGetRankedApplicants,
  apiUpdateApplicationStage,
  type RecruitmentRoom,
  type RankedApplicantItem,
  type PipelineStage,
  apiDownloadCandidateReportPdf,
  triggerPdfDownload,
} from '../api/recruitment';
import { RankedApplicantsModal } from '../components/recruitment/RankedApplicantsModal';
import { ApplicantComparisonModal } from '../components/recruitment/ApplicantComparisonModal';
import { PageTransition } from '../motion';

interface UndoStageState {
  appId: number;
  candidateName: string;
  fromStage: PipelineStage | string;
  toStage: PipelineStage;
  timerId: NodeJS.Timeout;
  remainingMs: number;
}

const STAGE_OPTIONS: { id: PipelineStage; label: string; bg: string; text: string; border: string }[] = [
  { id: 'APPLIED', label: 'Applied', bg: 'bg-[#f0f1ec]', text: 'text-[#526072]', border: 'border-[#d9dbd1]' },
  { id: 'UNDER_REVIEW', label: 'Under Review', bg: 'bg-[#fef3c7]', text: 'text-[#92400e]', border: 'border-[#fde68a]' },
  { id: 'SHORTLISTED', label: 'Shortlisted', bg: 'bg-[#e2f0e9]', text: 'text-[#277254]', border: 'border-[#b8d8c7]' },
  { id: 'INTERVIEW_ROUND_1', label: 'Interviewing', bg: 'bg-[#dbeafe]', text: 'text-[#1e40af]', border: 'border-[#bfdbfe]' },
  { id: 'OFFERED', label: 'Offered', bg: 'bg-[#f3e8ff]', text: 'text-[#6b21a8]', border: 'border-[#e9d5ff]' },
  { id: 'REJECTED', label: 'Rejected', bg: 'bg-[#fee2e2]', text: 'text-[#991b1b]', border: 'border-[#fecaca]' },
];

export function HrApplicantsPage({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();
  const prefersReduced = useReducedMotion();

  const [rooms, setRooms] = useState<RecruitmentRoom[]>([]);
  const [selectedRoomId, setSelectedRoomId] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'score' | 'cv' | 'video' | 'newest'>('score');
  const [loading, setLoading] = useState(true);

  // Multi-modal Score Weight Sliders (CV 50% / Video 50%)
  const [cvWeight, setCvWeight] = useState<number>(50);
  const videoWeight = 100 - cvWeight;

  // Pipeline Stage Filter
  const [stageFilter, setStageFilter] = useState<'ALL' | PipelineStage>('ALL');

  // Applicants loaded across rooms
  const [applicants, setApplicants] = useState<RankedApplicantItem[]>([]);
  const [selectedAppIds, setSelectedAppIds] = useState<number[]>([]);
  const [downloadingAppId, setDownloadingAppId] = useState<number | null>(null);

  // 5-second Undo Toast on Stage Change
  const [undoToast, setUndoToast] = useState<UndoStageState | null>(null);
  const undoRef = useRef<UndoStageState | null>(null);
  undoRef.current = undoToast;

  // Modals
  const [activeRankedRoom, setActiveRankedRoom] = useState<RecruitmentRoom | null>(null);
  const [comparisonModalOpen, setComparisonModalOpen] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const roomList = await apiGetRooms();
      setRooms(roomList);

      const allApps: RankedApplicantItem[] = [];
      const seenAppIds = new Set<number>();

      for (const room of roomList) {
        try {
          const rankedData = await apiGetRankedApplicants(room.id);
          for (const item of rankedData.results || []) {
            if (!seenAppIds.has(item.application_id)) {
              seenAppIds.add(item.application_id);
              allApps.push({
                ...item,
                room_id: room.id,
                room_title: room.title,
                stage: (item.stage || (item.is_shortlisted ? 'SHORTLISTED' : 'APPLIED')) as PipelineStage,
              } as any);
            }
          }
          for (const item of rankedData.unranked || []) {
            if (!seenAppIds.has(item.application_id)) {
              seenAppIds.add(item.application_id);
              allApps.push({
                ...item,
                room_id: room.id,
                room_title: room.title,
                stage: (item.stage || (item.is_shortlisted ? 'SHORTLISTED' : 'APPLIED')) as PipelineStage,
              } as any);
            }
          }
        } catch {
          // Room might have no applicants yet
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
    return () => {
      // Clear undo timer on unmount
      if (undoRef.current) {
        clearTimeout(undoRef.current.timerId);
      }
    };
  }, []);

  // Compute dynamic score based on weight mix
  const computeCompositeScore = (app: RankedApplicantItem): number => {
    const cv = app.cv_score ?? 0;
    const vid = app.video_score ?? 0;
    return Math.round((cv * cvWeight + vid * videoWeight) / 100);
  };

  // Filter and sort applicants with FLIP support
  const filteredApplicants = useMemo(() => {
    let result = [...applicants];

    if (selectedRoomId !== 'all') {
      const rId = parseInt(selectedRoomId, 10);
      result = result.filter((a: any) => a.room_id === rId);
    }

    if (stageFilter !== 'ALL') {
      result = result.filter((a) => {
        const curStage = a.stage || (a.is_shortlisted ? 'SHORTLISTED' : 'APPLIED');
        return curStage === stageFilter;
      });
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
      if (sortBy === 'score') {
        const scoreA = computeCompositeScore(a);
        const scoreB = computeCompositeScore(b);
        return scoreB - scoreA;
      }
      if (sortBy === 'cv') return (b.cv_score || 0) - (a.cv_score || 0);
      if (sortBy === 'video') return (b.video_score || 0) - (a.video_score || 0);
      return b.application_id - a.application_id;
    });

    return result;
  }, [applicants, selectedRoomId, stageFilter, searchQuery, sortBy, cvWeight, videoWeight]);

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

  // Stage Change with 5-Second Undo Toast
  const handleStageChange = (app: RankedApplicantItem, newStage: PipelineStage) => {
    const currentStage = app.stage || (app.is_shortlisted ? 'SHORTLISTED' : 'APPLIED');
    if (currentStage === newStage) return;

    // Clear previous pending toast if exists
    if (undoToast) {
      clearTimeout(undoToast.timerId);
      // Persist the previous pending one immediately
      apiUpdateApplicationStage(undoToast.appId, undoToast.toStage).catch(() => {});
    }

    // 1. Optimistic local update
    setApplicants((prev) =>
      prev.map((a) =>
        a.application_id === app.application_id
          ? { ...a, stage: newStage, is_shortlisted: newStage === 'SHORTLISTED' }
          : a
      )
    );

    // 2. Set 5-second timer before sending backend API request
    const timerId = setTimeout(async () => {
      try {
        await apiUpdateApplicationStage(app.application_id, newStage);
        notify(`${app.candidate_name} moved to ${newStage.replace('_', ' ')}.`, 'success');
      } catch {
        notify('Failed to update stage on server.', 'error');
      } finally {
        setUndoToast(null);
      }
    }, 5000);

    setUndoToast({
      appId: app.application_id,
      candidateName: app.candidate_name,
      fromStage: currentStage,
      toStage: newStage,
      timerId,
      remainingMs: 5000,
    });
  };

  const handleUndoStage = () => {
    if (!undoToast) return;
    clearTimeout(undoToast.timerId);

    // Revert optimistic update
    setApplicants((prev) =>
      prev.map((a) =>
        a.application_id === undoToast.appId
          ? {
              ...a,
              stage: undoToast.fromStage as PipelineStage,
              is_shortlisted: undoToast.fromStage === 'SHORTLISTED',
            }
          : a
      )
    );

    notify(`Stage change reverted for ${undoToast.candidateName}.`, 'info');
    setUndoToast(null);
  };

  return (
    <AppShell role="hr" activeTab="Applicants" notify={notify}>
      <PageTransition>
        <PageHeading
          title="Candidate Applicants"
          description="Review multi-modal AI evaluation dossiers, adjust scoring weights, and manage candidate pipeline stages."
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

        {/* 1. Interactive Multi-modal Weight Adjustment Controls (FLIP Reorder Engine) */}
        <div className="mt-6 rounded-2xl border border-[#d9dbd1] bg-white p-5 shadow-xs">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#f4f6ef] text-[#277254]">
                <Sliders size={20} />
              </div>
              <div>
                <h3 className="text-sm font-bold text-[#253142]">Evaluation Weight Model</h3>
                <p className="text-xs text-[#7b8490]">
                  Dynamic scoring mix: sliding weights instantly recalculates and smoothly re-ranks all applicants.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 bg-[#fbfaf5] border border-[#d9dbd1] rounded-xl px-3 py-1.5 text-xs font-bold">
                <span className="text-[#277254]">CV Match: {cvWeight}%</span>
                <span className="text-[#d9dbd1]">•</span>
                <span className="text-[#3a6384]">Video Delivery: {videoWeight}%</span>
              </div>
              {cvWeight !== 50 && (
                <button
                  type="button"
                  onClick={() => setCvWeight(50)}
                  title="Reset to 50/50 baseline"
                  className="inline-flex items-center gap-1 text-xs font-semibold text-[#7b8490] hover:text-[#253142] transition cursor-pointer"
                >
                  <RotateCcw size={13} /> Reset
                </button>
              )}
            </div>
          </div>

          <div className="mt-4 flex items-center gap-4">
            <span className="text-xs font-bold text-[#277254] w-14">CV {cvWeight}%</span>
            <input
              type="range"
              min={0}
              max={100}
              step={5}
              value={cvWeight}
              onChange={(e) => setCvWeight(Number(e.target.value))}
              aria-label="Adjust CV vs Video score weighting"
              className="flex-1 h-2 bg-[#ecefe7] rounded-lg appearance-none cursor-pointer accent-[#277254]"
            />
            <span className="text-xs font-bold text-[#3a6384] w-16 text-right">Video {videoWeight}%</span>
          </div>
        </div>

        {/* 2. Pipeline Stage Filter Pill Bar */}
        <div className="mt-4 flex flex-wrap items-center gap-1 bg-[#f5f1e6] p-1.5 rounded-2xl border border-[#e5e3d8] overflow-x-auto">
          {[
            { id: 'ALL' as const, label: 'All Candidates', count: applicants.length },
            { id: 'APPLIED' as const, label: 'Applied', count: applicants.filter((a) => (a.stage || 'APPLIED') === 'APPLIED').length },
            { id: 'UNDER_REVIEW' as const, label: 'Under Review', count: applicants.filter((a) => a.stage === 'UNDER_REVIEW').length },
            { id: 'SHORTLISTED' as const, label: 'Shortlisted', count: applicants.filter((a) => a.stage === 'SHORTLISTED' || a.is_shortlisted).length },
            { id: 'INTERVIEW_ROUND_1' as const, label: 'Interviewing', count: applicants.filter((a) => a.stage === 'INTERVIEW_ROUND_1').length },
            { id: 'OFFERED' as const, label: 'Offered', count: applicants.filter((a) => a.stage === 'OFFERED').length },
            { id: 'REJECTED' as const, label: 'Rejected', count: applicants.filter((a) => a.stage === 'REJECTED').length },
          ].map((tab) => {
            const isActive = stageFilter === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setStageFilter(tab.id)}
                className={`relative rounded-xl px-3.5 py-1.5 text-xs font-bold transition-colors whitespace-nowrap cursor-pointer ${
                  isActive ? 'text-white' : 'text-[#687382] hover:text-[#253142]'
                }`}
              >
                {isActive && (
                  <motion.div
                    layoutId="active-stage-pill"
                    transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
                    className="absolute inset-0 bg-[#253142] rounded-xl shadow-2xs"
                  />
                )}
                <span className="relative z-10 flex items-center gap-1.5">
                  {tab.label}
                  <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${isActive ? 'bg-white/20 text-white' : 'bg-[#e9e6dc] text-[#526072]'}`}>
                    {tab.count}
                  </span>
                </span>
              </button>
            );
          })}
        </div>

        {/* 3. Search and Room Filter Bar */}
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-[#d9dbd1] bg-white p-4 shadow-xs" data-testid="applicants-controls-bar">
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
              <option value="score">Sort by Dynamic Score (CV {cvWeight}% / Video {videoWeight}%)</option>
              <option value="cv">Sort by CV Match Score</option>
              <option value="video">Sort by Video Presentation</option>
              <option value="newest">Sort by Newest</option>
            </select>
          </div>
        </div>

        {/* 4. Main Applicants Table with 450ms FLIP Reordering */}
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
              {searchQuery || selectedRoomId !== 'all' || stageFilter !== 'ALL'
                ? 'No candidate profiles matched the active filters.'
                : 'Share your recruitment room application link to start receiving candidates.'}
            </p>
            <button
              type="button"
              onClick={() => {
                setSearchQuery('');
                setSelectedRoomId('all');
                setStageFilter('ALL');
              }}
              className="mt-5 inline-flex items-center gap-2 rounded-xl bg-[#253142] px-4 py-2 text-xs font-bold text-white hover:bg-[#33435a] transition cursor-pointer"
            >
              Reset Filters
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
                    <th className="py-3 px-4 text-center">Pipeline Stage</th>
                    <th className="py-3 pr-4 pl-2 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#eceee7]">
                  <AnimatePresence>
                    {filteredApplicants.map((app) => {
                      const isSelected = selectedAppIds.includes(app.application_id);
                      const isDownloading = downloadingAppId === app.application_id;
                      const dynamicScore = computeCompositeScore(app);
                      const currentStage = app.stage || (app.is_shortlisted ? 'SHORTLISTED' : 'APPLIED');
                      const stageMeta = STAGE_OPTIONS.find((s) => s.id === currentStage) || STAGE_OPTIONS[0];

                      return (
                        <motion.tr
                          key={app.application_id}
                          layout="position"
                          initial={prefersReduced ? { opacity: 0 } : { opacity: 0, y: 8 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={prefersReduced ? { opacity: 0 } : { opacity: 0, height: 0, overflow: 'hidden' }}
                          transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
                          data-testid={`applicant-row-${app.application_id}`}
                          className={`transition-colors ${isSelected ? 'bg-[#fffcf2]' : 'hover:bg-[#fbfaf7]'}`}
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
                              {dynamicScore}
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
                            {/* Interactive Stage Selector with 5s Undo Toast */}
                            <div className="relative inline-block">
                              <select
                                value={currentStage}
                                onChange={(e) => handleStageChange(app, e.target.value as PipelineStage)}
                                title="Click to advance or move candidate stage"
                                className={`text-[11px] font-bold rounded-full px-2.5 py-1 border transition-colors cursor-pointer appearance-none pr-6 focus:outline-none focus:ring-1 focus:ring-[#277254] ${stageMeta.bg} ${stageMeta.text} ${stageMeta.border}`}
                              >
                                {STAGE_OPTIONS.map((opt) => (
                                  <option key={opt.id} value={opt.id}>
                                    {opt.label}
                                  </option>
                                ))}
                              </select>
                              <ChevronDown size={11} className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 opacity-60" />
                            </div>
                          </td>
                          <td className="py-3 pr-4 pl-2 text-right">
                            <div className="flex items-center justify-end gap-1.5">
                              <button
                                type="button"
                                onClick={() => handleDownloadPdf(app.application_id, app.candidate_name)}
                                disabled={isDownloading}
                                title="Download PDF Scorecard"
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
                        </motion.tr>
                      );
                    })}
                  </AnimatePresence>
                </tbody>
              </table>
            </div>

            {/* Table Footer with Comparison Bar */}
            <div className="flex flex-wrap items-center justify-between border-t border-[#dedfd6] bg-[#faf9f5] px-5 py-3 text-xs text-[#7b8490]">
              <div>
                Showing {filteredApplicants.length} candidate{filteredApplicants.length === 1 ? '' : 's'} across {rooms.length} room{rooms.length === 1 ? '' : 's'}
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
                    className="rounded-xl bg-[#253142] px-3.5 py-1.5 font-bold text-white hover:bg-[#33435a] transition disabled:opacity-40 cursor-pointer shadow-xs"
                  >
                    Compare Side-by-Side &rarr;
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 5. Floating Bottom Undo Toast on Stage Change */}
        <AnimatePresence>
          {undoToast && (
            <motion.div
              initial={prefersReduced ? { opacity: 0 } : { opacity: 0, y: 24, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={prefersReduced ? { opacity: 0 } : { opacity: 0, y: 16, scale: 0.95 }}
              transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
              className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-4 bg-[#253142] text-white px-5 py-3 rounded-2xl shadow-xl border border-[#3b495c] max-w-md w-full"
            >
              <div className="flex-1 min-w-0">
                <div className="text-xs font-semibold truncate">
                  Moved <strong className="text-[#f5c84b]">{undoToast.candidateName}</strong> to{' '}
                  <span className="uppercase tracking-wider text-[11px] font-bold">{undoToast.toStage.replace('_', ' ')}</span>
                </div>
                {/* 5-second progress countdown line */}
                <div className="mt-1.5 h-1 w-full bg-white/20 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: '100%' }}
                    animate={{ width: '0%' }}
                    transition={{ duration: 5, ease: 'linear' }}
                    className="h-full bg-[#f5c84b]"
                  />
                </div>
              </div>

              <button
                type="button"
                onClick={handleUndoStage}
                className="inline-flex items-center gap-1.5 rounded-xl bg-white/10 hover:bg-white/20 text-[#f5c84b] px-3 py-1.5 text-xs font-bold transition cursor-pointer shrink-0"
              >
                <Undo2 size={13} /> Undo
              </button>
            </motion.div>
          )}
        </AnimatePresence>

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
            applicationIds={selectedAppIds}
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
      </PageTransition>
    </AppShell>
  );
}
export default HrApplicantsPage;
