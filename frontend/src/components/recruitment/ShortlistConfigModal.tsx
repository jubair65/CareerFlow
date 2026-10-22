import React, { useState, useEffect, useMemo } from 'react';
import {
  X,
  Star,
  Users,
  CheckCircle2,
  Sliders,
  Filter,
  Search,
  RefreshCw,
  Award,
  AlertCircle,
  HelpCircle,
  ShieldCheck,
  ChevronRight,
  TrendingUp,
  XCircle,
  Clock,
  Sparkles,
  Calculator,
} from 'lucide-react';
import type {
  RecruitmentRoom,
  ShortlistStrategyType,
  RoomShortlistResponse,
  ShortlistedApplicantItem,
} from '../../api/recruitment';
import {
  apiGetRoomShortlistCriteria,
  apiUpdateRoomShortlistCriteria,
  apiEvaluateRoomShortlist,
  apiGetShortlistedApplicants,
} from '../../api/recruitment';
import { CandidateReviewModal } from './CandidateReviewModal';
import { ScoreBreakdownModal } from './ScoreBreakdownModal';

interface ShortlistConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  room: RecruitmentRoom | null;
  onShortlistSaved?: (updatedRoom: RecruitmentRoom) => void;
  notify?: (message: string, tone?: 'success' | 'info' | 'error') => void;
}

type ModalTab = 'CRITERIA' | 'RESULTS';
type ApplicantFilter = 'ALL' | 'SHORTLISTED_ONLY' | 'NON_SHORTLISTED';

export function ShortlistConfigModal({
  isOpen,
  onClose,
  room,
  onShortlistSaved,
  notify,
}: ShortlistConfigModalProps) {
  const [activeTab, setActiveTab] = useState<ModalTab>('RESULTS');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [recalculating, setRecalculating] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Criteria State
  const [strategy, setStrategy] = useState<ShortlistStrategyType>('NONE');
  const [minScore, setMinScore] = useState<number>(75);
  const [topN, setTopN] = useState<number>(5);

  // Results State
  const [shortlistData, setShortlistData] = useState<RoomShortlistResponse | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [applicantFilter, setApplicantFilter] = useState<ApplicantFilter>('ALL');
  const [selectedAppForReview, setSelectedAppForReview] = useState<number | null>(null);
  const [selectedAppForBreakdown, setSelectedAppForBreakdown] = useState<number | null>(null);
  const [selectedAppBreakdownName, setSelectedAppBreakdownName] = useState<string | undefined>(undefined);

  // Load criteria and candidates on open
  useEffect(() => {
    if (!isOpen || !room) {
      setShortlistData(null);
      setErrorMsg(null);
      setActiveTab('RESULTS');
      return;
    }

    // Set initial criteria from room if present
    setStrategy(room.shortlist_strategy || 'NONE');
    setMinScore(room.shortlist_min_score !== null && room.shortlist_min_score !== undefined ? room.shortlist_min_score : 75);
    setTopN(room.shortlist_top_n || 5);

    fetchShortlistData();
  }, [isOpen, room]);

  const fetchShortlistData = async (showLoadingSpinner = true) => {
    if (!room) return;
    try {
      if (showLoadingSpinner) setLoading(true);
      setErrorMsg(null);

      // Fetch evaluated applicants
      const data = await apiGetShortlistedApplicants(room.id, true);
      setShortlistData(data);

      if (data.strategy) {
        setStrategy(data.strategy);
        if (data.min_score !== null) setMinScore(data.min_score);
        if (data.top_n !== null) setTopN(data.top_n);
      }
    } catch (err: any) {
      const msg = err?.response?.data?.error || 'Failed to fetch room shortlist data.';
      setErrorMsg(msg);
      notify?.(msg, 'error');
    } finally {
      if (showLoadingSpinner) setLoading(false);
    }
  };

  const handleSaveCriteria = async () => {
    if (!room) return;

    // Client-side validation before submission
    if (strategy === 'MIN_SCORE' || strategy === 'COMBINED') {
      if (minScore === null || isNaN(minScore) || minScore < 0 || minScore > 100) {
        notify?.('Minimum score threshold must be between 0 and 100.', 'error');
        return;
      }
    }
    if (strategy === 'TOP_N' || strategy === 'COMBINED') {
      if (!topN || isNaN(topN) || topN < 1) {
        notify?.('Candidate count (Top N) must be at least 1.', 'error');
        return;
      }
    }

    try {
      setSaving(true);
      setErrorMsg(null);

      const payload = {
        shortlist_strategy: strategy,
        shortlist_min_score: strategy === 'MIN_SCORE' || strategy === 'COMBINED' ? minScore : null,
        shortlist_top_n: strategy === 'TOP_N' || strategy === 'COMBINED' ? topN : null,
      };

      const res = await apiUpdateRoomShortlistCriteria(room.id, payload);

      notify?.(res.message || 'Shortlist criteria saved successfully!', 'success');

      // Update room in parent state if callback provided
      if (onShortlistSaved) {
        onShortlistSaved({
          ...room,
          shortlist_strategy: strategy,
          shortlist_min_score: payload.shortlist_min_score,
          shortlist_top_n: payload.shortlist_top_n,
        });
      }

      // Refresh results and switch to results tab
      await fetchShortlistData(false);
      setActiveTab('RESULTS');
    } catch (err: any) {
      const errDetails = err?.response?.data;
      let msg = 'Failed to save shortlisting criteria.';
      if (errDetails) {
        if (typeof errDetails === 'string') msg = errDetails;
        else if (errDetails.shortlist_strategy) msg = String(errDetails.shortlist_strategy);
        else if (errDetails.shortlist_min_score) msg = String(errDetails.shortlist_min_score);
        else if (errDetails.shortlist_top_n) msg = String(errDetails.shortlist_top_n);
        else if (errDetails.error) msg = String(errDetails.error);
      }
      setErrorMsg(msg);
      notify?.(msg, 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleEvaluateNow = async () => {
    if (!room) return;
    try {
      setRecalculating(true);
      const res = await apiEvaluateRoomShortlist(room.id);
      setShortlistData(res.evaluation);
      notify?.(res.message || 'Shortlist evaluation refreshed!', 'success');
    } catch (err: any) {
      notify?.('Failed to re-evaluate shortlisting.', 'error');
    } finally {
      setRecalculating(false);
    }
  };

  // Filtered applicants
  const filteredApplicants = useMemo(() => {
    if (!shortlistData?.all_applicants) return [];
    return shortlistData.all_applicants.filter((app) => {
      const matchSearch =
        searchQuery === '' ||
        app.candidate_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        app.candidate_email.toLowerCase().includes(searchQuery.toLowerCase());

      const matchFilter =
        applicantFilter === 'ALL' ||
        (applicantFilter === 'SHORTLISTED_ONLY' && app.is_shortlisted) ||
        (applicantFilter === 'NON_SHORTLISTED' && !app.is_shortlisted);

      return matchSearch && matchFilter;
    });
  }, [shortlistData, searchQuery, applicantFilter]);

  if (!isOpen || !room) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      data-testid="modal-shortlist-config"
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#253142]/60 p-3 sm:p-5 backdrop-blur-xs animate-in fade-in"
    >
      <div className="relative flex flex-col w-full max-w-4xl max-h-[92vh] rounded-2xl bg-white border border-[#d9dbd1] shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#eef0e7] px-6 py-4 bg-[#fbfaf5]">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#e2f0e9] text-[#277254] border border-[#a7d7c1]">
              <Star size={20} className="fill-[#277254]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-[#253142]">{room.title}</h3>
                <span className="rounded-md bg-[#e2f0e9] border border-[#a7d7c1] px-2 py-0.5 text-[10px] font-bold text-[#1f5b43]">
                  US-25 Shortlisting
                </span>
              </div>
              <p className="text-xs text-[#7b8490]">
                {room.company_name} {room.department ? `• ${room.department}` : ''} • Configurable screening rules & automatic shortlist
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            data-testid="button-close-shortlist-modal"
            className="rounded-xl p-1.5 text-[#7b8490] hover:bg-[#eef0e7] hover:text-[#253142] transition"
          >
            <X size={18} />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center justify-between border-b border-[#eef0e7] px-6 py-2 bg-white">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setActiveTab('RESULTS')}
              data-testid="tab-shortlist-results"
              className={`flex items-center gap-2 rounded-xl px-3.5 py-2 text-xs font-bold transition ${
                activeTab === 'RESULTS'
                  ? 'bg-[#277254] text-white shadow-xs'
                  : 'text-[#687382] hover:bg-[#f5f1e6] hover:text-[#253142]'
              }`}
            >
              <Users size={14} />
              <span>Shortlisted Candidates</span>
              {shortlistData && (
                <span
                  className={`rounded-full px-2 py-0.2 text-[10px] font-bold ${
                    activeTab === 'RESULTS'
                      ? 'bg-white/20 text-white'
                      : 'bg-[#e2f0e9] text-[#277254]'
                  }`}
                >
                  {shortlistData.shortlisted_count}
                </span>
              )}
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('CRITERIA')}
              data-testid="tab-shortlist-criteria"
              className={`flex items-center gap-2 rounded-xl px-3.5 py-2 text-xs font-bold transition ${
                activeTab === 'CRITERIA'
                  ? 'bg-[#277254] text-white shadow-xs'
                  : 'text-[#687382] hover:bg-[#f5f1e6] hover:text-[#253142]'
              }`}
            >
              <Sliders size={14} />
              <span>Configure Rules</span>
              {strategy !== 'NONE' && (
                <span className="rounded-full bg-[#fef3c7] text-[#92400e] text-[10px] font-bold px-1.5 py-0.2">
                  Active
                </span>
              )}
            </button>
          </div>

          {activeTab === 'RESULTS' && (
            <button
              type="button"
              onClick={handleEvaluateNow}
              disabled={recalculating}
              data-testid="button-reevaluate-shortlist"
              className="inline-flex items-center gap-1.5 rounded-xl border border-[#ccd0c6] bg-white px-3 py-1.5 text-xs font-bold text-[#253142] hover:bg-[#f5f1e6] transition disabled:opacity-50"
            >
              <RefreshCw size={12} className={recalculating ? 'animate-spin' : ''} />
              <span>Re-evaluate</span>
            </button>
          )}
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5 bg-[#faf9f5]">
          {errorMsg && (
            <div
              data-testid="alert-shortlist-error"
              className="flex items-start gap-2.5 rounded-xl bg-[#f7e5e1] border border-[#e8aba5] p-3 text-xs text-[#a33d35]"
            >
              <AlertCircle size={16} className="shrink-0 mt-0.5" />
              <div>
                <strong className="font-bold">Notice:</strong> {errorMsg}
              </div>
            </div>
          )}

          {/* TAB 1: CRITERIA CONFIGURATION */}
          {activeTab === 'CRITERIA' && (
            <div className="space-y-6" data-testid="section-shortlist-criteria-form">
              <div>
                <h4 className="text-sm font-bold text-[#253142]">Select Shortlisting Rule Strategy</h4>
                <p className="mt-0.5 text-xs text-[#7b8490]">
                  Configure how CareerFlow automatically screens and tags top candidate applications for this room.
                </p>
              </div>

              {/* 4 Strategy Cards */}
              <div className="grid gap-3 sm:grid-cols-2">
                {/* 1. Min Score */}
                <div
                  onClick={() => setStrategy('MIN_SCORE')}
                  data-testid="card-strategy-min-score"
                  className={`cursor-pointer rounded-2xl p-4 border transition ${
                    strategy === 'MIN_SCORE'
                      ? 'border-[#277254] bg-[#e2f0e9]/40 shadow-sm ring-2 ring-[#277254]/20'
                      : 'border-[#d9dbd1] bg-white hover:border-[#277254]/50'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <div className="grid h-8 w-8 place-items-center rounded-lg bg-[#e2f0e9] text-[#277254]">
                        <TrendingUp size={16} />
                      </div>
                      <span className="font-bold text-xs text-[#253142]">Minimum Score Threshold</span>
                    </div>
                    <input
                      type="radio"
                      name="strategy"
                      checked={strategy === 'MIN_SCORE'}
                      onChange={() => setStrategy('MIN_SCORE')}
                      className="accent-[#277254]"
                    />
                  </div>
                  <p className="mt-2 text-xs text-[#687382] leading-5">
                    Shortlist all candidates who achieve a final weighted score at or above your configured threshold.
                  </p>
                </div>

                {/* 2. Top N */}
                <div
                  onClick={() => setStrategy('TOP_N')}
                  data-testid="card-strategy-top-n"
                  className={`cursor-pointer rounded-2xl p-4 border transition ${
                    strategy === 'TOP_N'
                      ? 'border-[#277254] bg-[#e2f0e9]/40 shadow-sm ring-2 ring-[#277254]/20'
                      : 'border-[#d9dbd1] bg-white hover:border-[#277254]/50'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <div className="grid h-8 w-8 place-items-center rounded-lg bg-[#fef3c7] text-[#92400e]">
                        <Award size={16} />
                      </div>
                      <span className="font-bold text-xs text-[#253142]">Top N Candidates</span>
                    </div>
                    <input
                      type="radio"
                      name="strategy"
                      checked={strategy === 'TOP_N'}
                      onChange={() => setStrategy('TOP_N')}
                      className="accent-[#277254]"
                    />
                  </div>
                  <p className="mt-2 text-xs text-[#687382] leading-5">
                    Shortlist the top N ranked candidates in the room, breaking any ties deterministically by CV & Video metrics.
                  </p>
                </div>

                {/* 3. Combined */}
                <div
                  onClick={() => setStrategy('COMBINED')}
                  data-testid="card-strategy-combined"
                  className={`cursor-pointer rounded-2xl p-4 border transition ${
                    strategy === 'COMBINED'
                      ? 'border-[#277254] bg-[#e2f0e9]/40 shadow-sm ring-2 ring-[#277254]/20'
                      : 'border-[#d9dbd1] bg-white hover:border-[#277254]/50'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <div className="grid h-8 w-8 place-items-center rounded-lg bg-[#f0f4ff] text-[#3b4fa0]">
                        <Sparkles size={16} />
                      </div>
                      <span className="font-bold text-xs text-[#253142]">Combined (Top N + Min Score)</span>
                    </div>
                    <input
                      type="radio"
                      name="strategy"
                      checked={strategy === 'COMBINED'}
                      onChange={() => setStrategy('COMBINED')}
                      className="accent-[#277254]"
                    />
                  </div>
                  <p className="mt-2 text-xs text-[#687382] leading-5">
                    Shortlist up to N candidates who also strictly meet the minimum score bar (avoids shortlisting low-scoring candidates).
                  </p>
                </div>

                {/* 4. Disabled */}
                <div
                  onClick={() => setStrategy('NONE')}
                  data-testid="card-strategy-none"
                  className={`cursor-pointer rounded-2xl p-4 border transition ${
                    strategy === 'NONE'
                      ? 'border-[#253142] bg-[#f5f1e6] shadow-sm ring-2 ring-[#253142]/20'
                      : 'border-[#d9dbd1] bg-white hover:border-[#253142]/50'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <div className="grid h-8 w-8 place-items-center rounded-lg bg-[#f1f3f5] text-[#687382]">
                        <XCircle size={16} />
                      </div>
                      <span className="font-bold text-xs text-[#253142]">Disabled (Manual Review)</span>
                    </div>
                    <input
                      type="radio"
                      name="strategy"
                      checked={strategy === 'NONE'}
                      onChange={() => setStrategy('NONE')}
                      className="accent-[#253142]"
                    />
                  </div>
                  <p className="mt-2 text-xs text-[#687382] leading-5">
                    Disable automatic shortlisting. All applications remain under manual HR review without automated decisions.
                  </p>
                </div>
              </div>

              {/* Dynamic Strategy Inputs */}
              {(strategy === 'MIN_SCORE' || strategy === 'COMBINED') && (
                <div className="rounded-2xl bg-white p-5 border border-[#d9dbd1] space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-xs font-bold text-[#253142] flex items-center gap-1.5">
                        <TrendingUp size={14} className="text-[#277254]" /> Minimum Final Score Required (%)
                      </label>
                      <p className="text-[11px] text-[#7b8490] mt-0.5">
                        Candidates whose weighted final score is equal to or greater than this will be shortlisted.
                      </p>
                    </div>
                    <span className="font-mono text-sm font-bold text-[#277254] bg-[#e2f0e9] px-2.5 py-1 rounded-lg">
                      {minScore}%
                    </span>
                  </div>
                  <div className="flex items-center gap-4">
                    <input
                      type="range"
                      min={0}
                      max={100}
                      step={1}
                      value={minScore}
                      onChange={(e) => setMinScore(Number(e.target.value))}
                      data-testid="slider-shortlist-min-score"
                      className="w-full accent-[#277254] cursor-pointer"
                    />
                    <input
                      type="number"
                      min={0}
                      max={100}
                      value={minScore}
                      onChange={(e) => setMinScore(Math.max(0, Math.min(100, Number(e.target.value))))}
                      data-testid="input-shortlist-min-score"
                      className="w-20 rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3 py-1.5 text-xs text-center font-bold text-[#253142] focus:outline-none focus:ring-2 focus:ring-[#277254]/30"
                    />
                  </div>
                </div>
              )}

              {(strategy === 'TOP_N' || strategy === 'COMBINED') && (
                <div className="rounded-2xl bg-white p-5 border border-[#d9dbd1] space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-xs font-bold text-[#253142] flex items-center gap-1.5">
                        <Award size={14} className="text-[#92400e]" /> Required Candidate Count (Top N)
                      </label>
                      <p className="text-[11px] text-[#7b8490] mt-0.5">
                        Maximum number of top-ranked applicants to automatically select into the shortlist.
                      </p>
                    </div>
                    <span className="font-mono text-sm font-bold text-[#92400e] bg-[#fef3c7] px-2.5 py-1 rounded-lg">
                      Top {topN}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    {[3, 5, 10, 15, 20].map((n) => (
                      <button
                        key={n}
                        type="button"
                        onClick={() => setTopN(n)}
                        data-testid={`quick-top-n-${n}`}
                        className={`rounded-xl px-3 py-1.5 text-xs font-bold transition ${
                          topN === n
                            ? 'bg-[#253142] text-white'
                            : 'border border-[#d9dbd1] bg-[#fbfaf5] text-[#526072] hover:bg-[#eef0e7]'
                        }`}
                      >
                        Top {n}
                      </button>
                    ))}
                    <div className="flex items-center gap-1.5 ml-auto">
                      <span className="text-xs text-[#7b8490]">Custom:</span>
                      <input
                        type="number"
                        min={1}
                        max={500}
                        value={topN}
                        onChange={(e) => setTopN(Math.max(1, Number(e.target.value)))}
                        data-testid="input-shortlist-top-n"
                        className="w-20 rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3 py-1.5 text-xs text-center font-bold text-[#253142] focus:outline-none focus:ring-2 focus:ring-[#277254]/30"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="pt-3 flex items-center justify-end gap-3 border-t border-[#eef0e7]">
                <button
                  type="button"
                  onClick={() => setActiveTab('RESULTS')}
                  className="rounded-xl px-4 py-2 text-xs font-semibold text-[#526072] hover:bg-[#eef0e7] transition"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSaveCriteria}
                  disabled={saving}
                  data-testid="button-save-shortlist-criteria"
                  className="inline-flex items-center gap-2 rounded-xl bg-[#277254] px-5 py-2.5 text-xs font-bold text-white hover:bg-[#1f5b43] transition shadow-sm disabled:opacity-50"
                >
                  {saving ? (
                    <>
                      <RefreshCw size={14} className="animate-spin" /> Saving & Evaluating...
                    </>
                  ) : (
                    <>
                      <CheckCircle2 size={15} /> Save & Apply Shortlist
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* TAB 2: RESULTS & SHORTLISTED CANDIDATES */}
          {activeTab === 'RESULTS' && (
            <div className="space-y-5" data-testid="section-shortlist-results">
              {/* Stat Cards */}
              <div className="grid gap-3 sm:grid-cols-4">
                <div className="rounded-2xl bg-white p-4 border border-[#d9dbd1] shadow-2xs">
                  <div className="text-[11px] font-bold text-[#7b8490] uppercase tracking-wider">
                    Total Applicants
                  </div>
                  <div className="mt-1 text-2xl font-bold text-[#253142]">
                    {shortlistData?.total_applicants ?? 0}
                  </div>
                  <div className="text-[11px] text-[#9aabb5] mt-0.5">Applied to this room</div>
                </div>

                <div className="rounded-2xl bg-[#e2f0e9]/50 p-4 border border-[#a7d7c1] shadow-2xs">
                  <div className="text-[11px] font-bold text-[#1f5b43] uppercase tracking-wider flex items-center gap-1">
                    <Star size={12} className="fill-[#1f5b43]" /> Shortlisted
                  </div>
                  <div className="mt-1 text-2xl font-bold text-[#1f5b43]">
                    {shortlistData?.shortlisted_count ?? 0}
                  </div>
                  <div className="text-[11px] text-[#277254] mt-0.5">
                    {shortlistData?.total_applicants
                      ? `${Math.round(((shortlistData.shortlisted_count || 0) / shortlistData.total_applicants) * 100)}% of applicants`
                      : '0%'}
                  </div>
                </div>

                <div className="rounded-2xl bg-white p-4 border border-[#d9dbd1] shadow-2xs">
                  <div className="text-[11px] font-bold text-[#7b8490] uppercase tracking-wider">
                    Under Review
                  </div>
                  <div className="mt-1 text-2xl font-bold text-[#526072]">
                    {shortlistData?.non_shortlisted_count ?? 0}
                  </div>
                  <div className="text-[11px] text-[#9aabb5] mt-0.5">Not shortlisted</div>
                </div>

                <div className="rounded-2xl bg-white p-4 border border-[#d9dbd1] shadow-2xs">
                  <div className="text-[11px] font-bold text-[#7b8490] uppercase tracking-wider">
                    Rule Strategy
                  </div>
                  <div className="mt-1 text-xs font-bold text-[#253142] truncate">
                    {strategy === 'MIN_SCORE'
                      ? `Score ≥ ${minScore}%`
                      : strategy === 'TOP_N'
                      ? `Top ${topN} Ranked`
                      : strategy === 'COMBINED'
                      ? `Top ${topN} (≥${minScore}%)`
                      : 'Disabled'}
                  </div>
                  <button
                    type="button"
                    onClick={() => setActiveTab('CRITERIA')}
                    className="text-[11px] text-[#277254] hover:underline font-bold mt-1 inline-flex items-center gap-0.5"
                  >
                    Edit Rule <ChevronRight size={11} />
                  </button>
                </div>
              </div>

              {/* Filter & Search Bar */}
              <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-white p-3.5 rounded-2xl border border-[#d9dbd1]">
                <div className="relative w-full sm:w-72">
                  <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#7b8490]" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search candidates by name or email..."
                    data-testid="input-search-shortlist"
                    className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] pl-9 pr-3 py-1.5 text-xs text-[#253142] focus:outline-none focus:ring-2 focus:ring-[#277254]/30"
                  />
                </div>

                <div className="flex items-center gap-1.5 bg-[#f5f1e6] p-1 rounded-xl w-full sm:w-auto justify-end">
                  {(
                    [
                      { key: 'ALL', label: 'All Candidates' },
                      { key: 'SHORTLISTED_ONLY', label: '⭐ Shortlisted Only' },
                      { key: 'NON_SHORTLISTED', label: 'Under Review' },
                    ] as const
                  ).map((f) => (
                    <button
                      key={f.key}
                      type="button"
                      onClick={() => setApplicantFilter(f.key)}
                      data-testid={`filter-${f.key.toLowerCase()}`}
                      className={`rounded-lg px-2.5 py-1 text-xs font-bold transition ${
                        applicantFilter === f.key
                          ? 'bg-[#253142] text-white shadow-2xs'
                          : 'text-[#687382] hover:text-[#253142]'
                      }`}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Applicants Table */}
              <div className="overflow-hidden rounded-2xl bg-white border border-[#d9dbd1] shadow-2xs">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs" data-testid="table-shortlisted-applicants">
                    <thead className="bg-[#fbfaf5] border-b border-[#eef0e7] text-[11px] font-bold text-[#7b8490] uppercase tracking-wider">
                      <tr>
                        <th className="px-4 py-3">Rank & Candidate</th>
                        <th className="px-4 py-3">Final Score</th>
                        <th className="px-4 py-3">Status</th>
                        <th className="px-4 py-3">Shortlist Reason / Criteria Explanation</th>
                        <th className="px-4 py-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#eef0e7]">
                      {filteredApplicants.length > 0 ? (
                        filteredApplicants.map((app) => (
                          <tr
                            key={app.application_id}
                            className={`hover:bg-[#fbfaf5] transition ${
                              app.is_shortlisted ? 'bg-[#e2f0e9]/15' : ''
                            }`}
                            data-testid={`row-applicant-${app.application_id}`}
                          >
                            {/* Candidate & Rank */}
                            <td className="px-4 py-3.5">
                              <div className="flex items-center gap-2.5">
                                <div
                                  className={`grid h-7 w-7 place-items-center rounded-lg text-xs font-bold ${
                                    app.rank === 1
                                      ? 'bg-[#fef3c7] text-[#92400e] border border-[#fde68a]'
                                      : app.rank === 2
                                      ? 'bg-[#f1f3f5] text-[#526072] border border-[#ccd0c6]'
                                      : app.rank === 3
                                      ? 'bg-[#f7e5e1] text-[#a33d35] border border-[#e8aba5]'
                                      : 'bg-[#fbfaf5] text-[#7b8490] border border-[#eef0e7]'
                                  }`}
                                >
                                  {app.rank ? `#${app.rank}` : '—'}
                                </div>
                                <div>
                                  <div className="font-bold text-[#253142]">
                                    {app.candidate_name || app.candidate_email}
                                  </div>
                                  <div className="text-[11px] text-[#7b8490]">
                                    {app.candidate_email}
                                  </div>
                                </div>
                              </div>
                            </td>

                            {/* Final Score */}
                            <td className="px-4 py-3.5">
                              {app.final_score !== null ? (
                                <div className="space-y-0.5">
                                  <span className="inline-flex items-center gap-1 rounded-md bg-[#e2f0e9] px-2 py-0.5 text-xs font-bold text-[#277254]">
                                    {app.final_score.toFixed(1)}%
                                  </span>
                                  <div className="text-[10px] text-[#7b8490]">
                                    CV: {app.cv_score !== null ? `${app.cv_score}%` : 'N/A'} • Vid:{' '}
                                    {app.video_score !== null ? `${app.video_score}%` : 'N/A'}
                                  </div>
                                </div>
                              ) : (
                                <span className="inline-flex items-center gap-1 text-[11px] text-[#9aabb5] italic">
                                  Score pending
                                </span>
                              )}
                            </td>

                            {/* Shortlist Status */}
                            <td className="px-4 py-3.5">
                              {app.is_shortlisted ? (
                                <span
                                  data-testid={`badge-shortlisted-${app.application_id}`}
                                  className="inline-flex items-center gap-1 rounded-lg bg-[#277254] text-white px-2.5 py-1 text-[11px] font-bold shadow-2xs"
                                >
                                  <Star size={12} className="fill-white" />
                                  Shortlisted
                                </span>
                              ) : (
                                <span
                                  data-testid={`badge-under-review-${app.application_id}`}
                                  className="inline-flex items-center gap-1 rounded-lg bg-[#f1f3f5] text-[#687382] px-2.5 py-1 text-[11px] font-semibold"
                                >
                                  Under Review
                                </span>
                              )}
                            </td>

                            {/* Explanation / Criteria Reason */}
                            <td className="px-4 py-3.5">
                              <div className="text-xs text-[#526072] leading-relaxed">
                                {app.shortlist_reason || 'Criteria evaluation pending.'}
                              </div>
                              {app.shortlisted_at && (
                                <div className="text-[10px] text-[#9aabb5] flex items-center gap-1 mt-0.5">
                                  <Clock size={10} />
                                  <span>Shortlisted {new Date(app.shortlisted_at).toLocaleDateString()}</span>
                                </div>
                              )}
                            </td>

                            {/* Actions (Review & Score Breakdown) */}
                            <td className="px-4 py-3.5 text-right">
                              <div className="flex items-center justify-end gap-1.5">
                                <button
                                  type="button"
                                  onClick={() => {
                                    setSelectedAppForBreakdown(app.application_id);
                                    setSelectedAppBreakdownName(app.candidate_name);
                                  }}
                                  data-testid={`btn-breakdown-applicant-${app.application_id}`}
                                  className="inline-flex items-center gap-1.5 rounded-xl border border-indigo-200 bg-indigo-50/50 hover:bg-indigo-600 hover:text-white px-2.5 py-1 text-xs font-bold text-indigo-700 transition shadow-2xs"
                                  title="Explainable Score Breakdown"
                                >
                                  <Calculator size={13} />
                                  <span>Breakdown</span>
                                </button>
                                <button
                                  type="button"
                                  onClick={() => setSelectedAppForReview(app.application_id)}
                                  data-testid={`btn-review-applicant-${app.application_id}`}
                                  className="inline-flex items-center gap-1.5 rounded-xl border border-[#d9dbd1] bg-white px-2.5 py-1 text-xs font-bold text-[#253142] hover:bg-[#253142] hover:text-white transition shadow-2xs"
                                >
                                  <span>Review</span>
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={5} className="p-8 text-center text-xs text-[#7b8490]">
                            {searchQuery || applicantFilter !== 'ALL'
                              ? 'No candidates match your current search or status filter.'
                              : 'No applicants found in this room yet.'}
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between border-t border-[#eef0e7] px-6 py-3.5 bg-[#fbfaf5]">
          <div className="text-xs text-[#7b8490]">
            {shortlistData
              ? `${shortlistData.shortlisted_count} of ${shortlistData.total_applicants} applicants shortlisted`
              : 'Loading shortlisting data...'}
          </div>
          <button
            type="button"
            onClick={onClose}
            data-testid="button-close-shortlist-footer"
            className="rounded-xl bg-[#253142] px-4 py-2 text-xs font-bold text-white hover:bg-[#344458] transition"
          >
            Close
          </button>
        </div>
      </div>

      {/* US-26: Candidate Review and Human Decision Modal */}
      {selectedAppForReview && (
        <CandidateReviewModal
          isOpen={Boolean(selectedAppForReview)}
          onClose={() => setSelectedAppForReview(null)}
          applicationId={selectedAppForReview}
          onDecisionRecorded={(_appId, _decision) => {
            fetchShortlistData(false);
          }}
          notify={notify}
        />
      )}

      {/* US-27: Explainable Applicant Score Breakdown Modal */}
      {selectedAppForBreakdown && (
        <ScoreBreakdownModal
          isOpen={Boolean(selectedAppForBreakdown)}
          onClose={() => setSelectedAppForBreakdown(null)}
          applicationId={selectedAppForBreakdown}
          candidateName={selectedAppBreakdownName}
          notify={notify}
        />
      )}
    </div>
  );
}

