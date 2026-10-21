import React, { useState, useEffect, useMemo } from 'react';
import {
  X,
  Search,
  Trophy,
  Medal,
  Award,
  Users,
  Gauge,
  AlertCircle,
  Clock,
  ArrowUpDown,
  Filter,
  CheckCircle2,
  RefreshCw,
  Sparkles,
  SlidersHorizontal,
  FileText,
  Video,
  Calculator,
} from 'lucide-react';
import type {
  RecruitmentRoom,
  RankedApplicantItem,
  UnrankedApplicantItem,
  RankedApplicantsResponse,
} from '../../api/recruitment';
import { apiGetRankedApplicants, apiCalculateRoomScores } from '../../api/recruitment';
import { ScoreBreakdownModal } from './ScoreBreakdownModal';

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
  const [error, setError] = useState<string | null>(null);

  // Filters & State
  const [activeTab, setActiveTab] = useState<TabMode>('RANKED');
  const [searchQuery, setSearchQuery] = useState('');
  const [minScoreFilter, setMinScoreFilter] = useState<number>(0);
  const [sortBy, setSortBy] = useState<SortOption>('-final_score');
  const [selectedBreakdownApp, setSelectedBreakdownApp] = useState<{ id: number; name: string } | null>(null);

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
      return;
    }

    fetchRankings(true);
  }, [isOpen, room]);

  // Re-fetch when sorting or min-score changes
  useEffect(() => {
    if (isOpen && room) {
      fetchRankings(false);
    }
  }, [sortBy, minScoreFilter]);

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

  const getRankBadgeElement = (rank: number, badge: string) => {
    if (rank === 1) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-900 border border-amber-300 shadow-sm dark:bg-amber-950/60 dark:text-amber-300 dark:border-amber-700">
          <Trophy className="w-3.5 h-3.5 text-amber-500 fill-amber-400" />
          Rank #1
        </span>
      );
    }
    if (rank === 2) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-slate-200 text-slate-800 border border-slate-300 shadow-sm dark:bg-slate-800 dark:text-slate-200 dark:border-slate-600">
          <Medal className="w-3.5 h-3.5 text-slate-400 fill-slate-300" />
          Rank #2
        </span>
      );
    }
    if (rank === 3) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-700/10 text-amber-800 border border-amber-600/30 shadow-sm dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-700/50">
          <Medal className="w-3.5 h-3.5 text-amber-700 fill-amber-600 dark:text-amber-500" />
          Rank #3
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-700 border border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700">
        #{rank}
      </span>
    );
  };

  const getScoreBadgeColor = (score: number) => {
    if (score >= 75) {
      return 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800';
    }
    if (score >= 50) {
      return 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-800';
    }
    return 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-400 dark:border-rose-800';
  };

  const getScoreBarColor = (score: number) => {
    if (score >= 75) return 'bg-emerald-500';
    if (score >= 50) return 'bg-amber-500';
    return 'bg-rose-500';
  };

  if (!isOpen || !room) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div
        className="relative w-full max-w-5xl bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-800 flex flex-col max-h-[90vh] overflow-hidden"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ranked-modal-title"
        data-testid="modal-ranked-applicants"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-800 bg-gray-50/70 dark:bg-gray-900/70">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400 border border-amber-200/50 dark:border-amber-800/50">
              <Trophy className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2
                  id="ranked-modal-title"
                  data-testid="text-ranked-modal-title"
                  className="text-xl font-bold text-gray-900 dark:text-white"
                >
                  Applicant Leaderboard & Rankings
                </h2>
                <span className="text-xs px-2.5 py-0.5 rounded-full font-medium bg-blue-50 text-blue-700 border border-blue-200 dark:bg-blue-950/40 dark:text-blue-400 dark:border-blue-800">
                  Weights: {room.cv_weight}% CV / {room.video_weight}% Video
                </span>
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                {room.title} • {room.company_name}
                {room.department ? ` (${room.department})` : ''}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleRecalculateScores}
              disabled={recalculating}
              title="Recalculate all scores using current weights"
              data-testid="button-recalculate-scores"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${recalculating ? 'animate-spin' : ''}`} />
              {recalculating ? 'Recalculating...' : 'Refresh Scores'}
            </button>
            <button
              onClick={onClose}
              data-testid="button-close-ranked-modal"
              className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              aria-label="Close modal"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Statistical Summary Row */}
        {data && (
          <div data-testid="row-statistical-summary" className="grid grid-cols-2 sm:grid-cols-4 gap-3 px-6 py-3 bg-gray-50/40 dark:bg-gray-900/40 border-b border-gray-100 dark:border-gray-800 text-xs">
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-blue-500" />
              <span className="text-gray-500 dark:text-gray-400">Total Applicants:</span>
              <span data-testid="stat-ranked-total" className="font-bold text-gray-900 dark:text-white">{data.total_applicants}</span>
            </div>
            <div className="flex items-center gap-2">
              <Trophy className="w-4 h-4 text-emerald-500" />
              <span className="text-gray-500 dark:text-gray-400">Ranked Candidates:</span>
              <span data-testid="stat-ranked-count" className="font-bold text-emerald-600 dark:text-emerald-400">{data.ranked_count}</span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-amber-500" />
              <span className="text-gray-500 dark:text-gray-400">Incomplete / Pending:</span>
              <span data-testid="stat-unranked-count" className="font-bold text-amber-600 dark:text-amber-400">{data.unranked_count}</span>
            </div>
            <div className="flex items-center gap-2">
              <Gauge className="w-4 h-4 text-purple-500" />
              <span className="text-gray-500 dark:text-gray-400">Top Score:</span>
              <span data-testid="stat-top-score" className="font-bold text-purple-600 dark:text-purple-400">
                {data.results.length > 0 ? `${data.results[0].final_score.toFixed(1)}/100` : '—'}
              </span>
            </div>
          </div>
        )}

        {/* Navigation Tabs and Controls */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 px-6 py-3 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
          {/* Tabs */}
          <div className="flex items-center p-1 bg-gray-100 dark:bg-gray-800 rounded-lg">
            <button
              onClick={() => setActiveTab('RANKED')}
              data-testid="tab-ranked-leaderboard"
              className={`flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                activeTab === 'RANKED'
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900'
              }`}
            >
              <Trophy className="w-3.5 h-3.5" />
              Ranked Leaderboard ({data?.ranked_count ?? 0})
            </button>
            <button
              onClick={() => setActiveTab('UNRANKED')}
              data-testid="tab-unranked-leaderboard"
              className={`flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                activeTab === 'UNRANKED'
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900'
              }`}
            >
              <Clock className="w-3.5 h-3.5" />
              Evaluation In Progress ({data?.unranked_count ?? 0})
            </button>
          </div>

          {/* Filter Toolbar */}
          <div className="flex flex-wrap items-center gap-2.5">
            {/* Search Input */}
            <div className="relative min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                data-testid="input-ranked-search"
                placeholder="Search candidate or email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && fetchRankings(false)}
                className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              />
            </div>

            {/* Min Score Filter Slider */}
            {activeTab === 'RANKED' && (
              <div className="flex items-center gap-2 px-2.5 py-1 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50 text-xs text-gray-600 dark:text-gray-300">
                <SlidersHorizontal className="w-3.5 h-3.5 text-gray-400" />
                <span data-testid="text-min-score-indicator">Min: {minScoreFilter}</span>
                <input
                  type="range"
                  data-testid="slider-min-score"
                  min="0"
                  max="100"
                  step="5"
                  value={minScoreFilter}
                  onChange={(e) => setMinScoreFilter(parseInt(e.target.value, 10))}
                  className="w-20 accent-blue-600 cursor-pointer"
                  title={`Filter applicants with final score >= ${minScoreFilter}`}
                />
              </div>
            )}

            {/* Sort Dropdown */}
            {activeTab === 'RANKED' && (
              <div className="flex items-center gap-1.5 text-xs">
                <ArrowUpDown className="w-3.5 h-3.5 text-gray-400" />
                <select
                  data-testid="select-ranked-sort"
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as SortOption)}
                  className="px-2.5 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                >
                  <option value="-final_score">Final Score (High to Low)</option>
                  <option value="final_score">Final Score (Low to High)</option>
                  <option value="-cv_score">CV Match Score (High to Low)</option>
                  <option value="-video_score">Video Presentation (High to Low)</option>
                  <option value="-applied_at">Newest First</option>
                  <option value="applied_at">Oldest First</option>
                </select>
              </div>
            )}
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {loading ? (
            <div className="py-20 flex flex-col items-center justify-center gap-3 text-gray-400">
              <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
              <p className="text-sm font-medium">Computing and organizing applicant rankings...</p>
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-400 flex items-center gap-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <p className="text-sm">{error}</p>
            </div>
          ) : activeTab === 'RANKED' ? (
            data?.results.length === 0 ? (
              <div className="py-16 text-center text-gray-400">
                <Trophy className="w-12 h-12 mx-auto stroke-1 text-gray-300 dark:text-gray-700 mb-2" />
                <p className="text-base font-semibold text-gray-700 dark:text-gray-300">
                  No ranked candidates found
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  {minScoreFilter > 0
                    ? `No candidates meet the minimum score threshold of ${minScoreFilter}. Try lowering the filter slider.`
                    : 'Candidates with completed evaluations will appear on this leaderboard.'}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {data?.results.map((applicant) => (
                  <div
                    key={applicant.application_id}
                    data-testid={`card-ranked-applicant-${applicant.rank}`}
                    className={`p-4 rounded-xl border transition-all duration-150 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-white dark:bg-gray-800/70 hover:shadow-md ${
                      applicant.rank === 1
                        ? 'border-amber-300/80 dark:border-amber-700/60 bg-gradient-to-r from-amber-50/40 via-white to-transparent dark:from-amber-950/20 dark:via-gray-800'
                        : applicant.rank === 2
                        ? 'border-slate-300 dark:border-slate-700 bg-gradient-to-r from-slate-50/40 via-white to-transparent dark:from-slate-900/20 dark:via-gray-800'
                        : applicant.rank === 3
                        ? 'border-amber-600/30 dark:border-amber-800/40 bg-gradient-to-r from-amber-900/5 via-white to-transparent'
                        : 'border-gray-200 dark:border-gray-800'
                    }`}
                  >
                    {/* Left: Rank & Candidate Details */}
                    <div className="flex items-center gap-4 min-w-[260px]">
                      <div className="flex-shrink-0" data-testid={`badge-rank-${applicant.rank}`}>
                        {getRankBadgeElement(applicant.rank, applicant.badge)}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <h3
                            data-testid={`text-candidate-name-${applicant.rank}`}
                            className="text-sm font-bold text-gray-900 dark:text-white truncate"
                          >
                            {applicant.candidate_name || 'Anonymous Candidate'}
                          </h3>
                          {applicant.is_partial_score && (
                            <span
                              data-testid={`badge-partial-score-${applicant.rank}`}
                              className="text-[10px] px-1.5 py-0.5 rounded font-medium bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300"
                            >
                              Partial Evaluation
                            </span>
                          )}
                        </div>
                        <p
                          data-testid={`text-candidate-email-${applicant.rank}`}
                          className="text-xs text-gray-500 dark:text-gray-400 truncate"
                        >
                          {applicant.candidate_email}
                        </p>
                        <p className="text-[11px] text-gray-400 mt-0.5">
                          Applied: {new Date(applicant.applied_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>

                    {/* Middle: Component breakdown pills */}
                    <div className="flex items-center gap-2 sm:gap-3 flex-wrap">
                      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 text-xs">
                        <FileText className="w-3.5 h-3.5 text-blue-500" />
                        <span className="text-gray-500 dark:text-gray-400">CV ({room.cv_weight}%):</span>
                        <span
                          data-testid={`text-cv-score-${applicant.rank}`}
                          className="font-semibold text-gray-900 dark:text-white"
                        >
                          {applicant.cv_score !== null ? `${applicant.cv_score.toFixed(1)}` : 'N/A'}
                        </span>
                      </div>

                      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 text-xs">
                        <Video className="w-3.5 h-3.5 text-purple-500" />
                        <span className="text-gray-500 dark:text-gray-400">Video ({room.video_weight}%):</span>
                        <span
                          data-testid={`text-video-score-${applicant.rank}`}
                          className="font-semibold text-gray-900 dark:text-white"
                        >
                          {applicant.video_score !== null ? `${applicant.video_score.toFixed(1)}` : 'N/A'}
                        </span>
                      </div>
                    </div>

                    {/* Right: Final Composite Score Meter & Breakdown Trigger */}
                    <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end">
                      <div className="text-right">
                        <div
                          data-testid={`text-final-score-${applicant.rank}`}
                          className={`inline-flex items-center gap-1 px-3 py-1 rounded-xl font-bold text-sm border ${getScoreBadgeColor(
                            applicant.final_score
                          )}`}
                        >
                          <Gauge className="w-3.5 h-3.5" />
                          <span>{applicant.final_score.toFixed(1)}</span>
                          <span className="text-[10px] opacity-70">/100</span>
                        </div>
                        {/* Progress mini bar */}
                        <div className="w-24 h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full mt-1.5 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${getScoreBarColor(applicant.final_score)}`}
                            style={{ width: `${Math.min(100, applicant.final_score)}%` }}
                          />
                        </div>
                      </div>

                      {/* US-27: Score Breakdown Trigger Button */}
                      <button
                        type="button"
                        onClick={() =>
                          setSelectedBreakdownApp({
                            id: applicant.application_id,
                            name: applicant.candidate_name,
                          })
                        }
                        data-testid={`btn-breakdown-applicant-${applicant.application_id}`}
                        title="View Transparent Score Breakdown"
                        className="p-2 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 hover:border-indigo-500 transition shadow-2xs"
                      >
                        <Calculator className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )
          ) : (
            /* Unranked / Evaluation In Progress View */
            <div className="space-y-4">
              <div className="p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200/70 dark:border-amber-800/50 text-xs text-amber-800 dark:text-amber-300 flex items-start gap-2.5">
                <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                <p>
                  These candidates do not have a calculated final score yet due to pending CV parsing, speech processing, or behavioral analysis. They are isolated from the ranked leaderboard to ensure accurate percentile ranking.
                </p>
              </div>

              {data?.unranked.length === 0 ? (
                <div className="py-16 text-center text-gray-400">
                  <CheckCircle2 className="w-12 h-12 mx-auto stroke-1 text-emerald-400 mb-2" />
                  <p className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                    All candidates have been evaluated!
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    Zero applications are pending analysis in this room.
                  </p>
                </div>
              ) : (
                <div className="space-y-2.5">
                  {data?.unranked.map((unrankedApp) => (
                    <div
                      key={unrankedApp.application_id}
                      data-testid={`card-unranked-applicant-${unrankedApp.application_id}`}
                      className="p-3.5 rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/40 flex items-center justify-between gap-4 text-xs"
                    >
                      <div>
                        <h4
                          data-testid={`text-unranked-name-${unrankedApp.application_id}`}
                          className="font-semibold text-gray-900 dark:text-white"
                        >
                          {unrankedApp.candidate_name || 'Anonymous Candidate'}
                        </h4>
                        <p className="text-gray-500 dark:text-gray-400">
                          {unrankedApp.candidate_email}
                        </p>
                      </div>

                      <div className="flex items-center gap-3">
                        <span
                          data-testid={`text-unranked-reason-${unrankedApp.application_id}`}
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full font-medium bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-200 dark:border-amber-800"
                        >
                          <Clock className="w-3.5 h-3.5" />
                          {unrankedApp.pending_reason}
                        </span>
                        <span className="text-gray-400 text-[11px]">
                          Applied {new Date(unrankedApp.applied_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between px-6 py-3 border-t border-gray-200 dark:border-gray-800 bg-gray-50/70 dark:bg-gray-900/70 text-xs text-gray-500 dark:text-gray-400">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-blue-500" />
            <span>Deterministic Tie-Breaking: CV Match &gt; Video Score &gt; Submission Date</span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-gray-200 hover:bg-gray-300 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 transition-colors"
          >
            Close Leaderboard
          </button>
        </div>
      </div>

      {/* US-27: Transparent Score Breakdown Modal */}
      {selectedBreakdownApp && (
        <ScoreBreakdownModal
          isOpen={Boolean(selectedBreakdownApp)}
          onClose={() => setSelectedBreakdownApp(null)}
          applicationId={selectedBreakdownApp.id}
          candidateName={selectedBreakdownApp.name}
          notify={notify}
        />
      )}
    </div>
  );
}
