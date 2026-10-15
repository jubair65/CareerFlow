import React, { useState, useEffect, useMemo } from 'react';
import {
  X,
  Search,
  Users,
  Gauge,
  Award,
  AlertCircle,
  FileText,
  ChevronRight,
  Loader2,
  ArrowUpDown,
  Filter,
  CheckCircle2,
  Download,
  Calendar,
  Share2,
} from 'lucide-react';
import type { RecruitmentRoom, ApplicantCvScoreItem, RoomCvScoresResponse } from '../../api/recruitment';
import { apiGetRoomCvScores } from '../../api/recruitment';
import { CvSkillBreakdownModal } from './CvSkillBreakdownModal';

interface RoomCvScoresModalProps {
  isOpen: boolean;
  onClose: () => void;
  room: RecruitmentRoom | null;
  notify?: (message: string, tone?: 'success' | 'info' | 'error') => void;
}

type ScoreFilter = 'ALL' | 'HIGH' | 'MODERATE' | 'LOW' | 'PENDING';
type SortOption = 'SCORE_DESC' | 'SCORE_ASC' | 'DATE_DESC' | 'NAME_ASC';

export function RoomCvScoresModal({
  isOpen,
  onClose,
  room,
  notify,
}: RoomCvScoresModalProps) {
  const [data, setData] = useState<RoomCvScoresResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters and search
  const [searchQuery, setSearchQuery] = useState('');
  const [scoreFilter, setScoreFilter] = useState<ScoreFilter>('ALL');
  const [sortBy, setSortBy] = useState<SortOption>('SCORE_DESC');

  // Breakdown modal
  const [selectedApplicant, setSelectedApplicant] = useState<ApplicantCvScoreItem | null>(null);

  useEffect(() => {
    if (!isOpen || !room) {
      setData(null);
      setError(null);
      setSearchQuery('');
      setScoreFilter('ALL');
      return;
    }

    const fetchScores = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await apiGetRoomCvScores(room.id);
        setData(res);
      } catch (err: any) {
        const msg = err?.response?.data?.error || 'Failed to load applicant CV match scores.';
        setError(msg);
        notify?.(msg, 'error');
      } finally {
        setLoading(false);
      }
    };

    fetchScores();
  }, [isOpen, room]);

  const filteredApplicants = useMemo(() => {
    if (!data?.results) return [];

    return data.results
      .filter((app) => {
        // Search filter
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase().trim();
          const matchName = app.candidate_name?.toLowerCase().includes(q);
          const matchEmail = app.candidate_email?.toLowerCase().includes(q);
          const matchSkill = app.skills_matched?.some((s) => s.toLowerCase().includes(q));
          if (!matchName && !matchEmail && !matchSkill) return false;
        }

        // Tier filter
        if (scoreFilter === 'HIGH') {
          return app.has_score && (app.match_score ?? 0) >= 75;
        }
        if (scoreFilter === 'MODERATE') {
          return (
            app.has_score &&
            (app.match_score ?? 0) >= 50 &&
            (app.match_score ?? 0) < 75
          );
        }
        if (scoreFilter === 'LOW') {
          return app.has_score && (app.match_score ?? 0) < 50;
        }
        if (scoreFilter === 'PENDING') {
          return !app.has_score || app.match_score === null;
        }

        return true;
      })
      .sort((a, b) => {
        if (sortBy === 'SCORE_DESC') {
          return (b.match_score ?? -1) - (a.match_score ?? -1);
        }
        if (sortBy === 'SCORE_ASC') {
          return (a.match_score ?? 999) - (b.match_score ?? 999);
        }
        if (sortBy === 'DATE_DESC') {
          return new Date(b.applied_at).getTime() - new Date(a.applied_at).getTime();
        }
        if (sortBy === 'NAME_ASC') {
          return (a.candidate_name || a.candidate_email).localeCompare(
            b.candidate_name || b.candidate_email
          );
        }
        return 0;
      });
  }, [data, searchQuery, scoreFilter, sortBy]);

  if (!isOpen || !room) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      data-testid="modal-room-cv-scores"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 overflow-y-auto animate-in fade-in"
    >
      <div className="relative w-full max-w-4xl rounded-2xl bg-white border border-[#d9dbd1] shadow-2xl my-6 overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-[#eef0e7] px-6 py-4 bg-[#fbfaf5]">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#277254] text-white shadow-xs">
              <Award size={20} />
            </div>
            <div>
              <div className="text-[11px] font-bold uppercase tracking-wider text-[#7b8490]">
                US-10 • Applicant CV Match Scores
              </div>
              <h2 className="text-base font-bold text-[#253142]" data-testid="text-room-title-header">
                {room.title}
              </h2>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            data-testid="button-close-cv-scores-modal"
            className="rounded-xl p-1.5 text-[#7b8490] hover:bg-[#eef0e7] hover:text-[#253142] transition"
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6 overflow-y-auto space-y-5">
          {loading ? (
            <div className="flex h-64 flex-col items-center justify-center gap-2">
              <Loader2 size={24} className="animate-spin text-[#277254]" />
              <span className="text-xs text-[#7b8490]">Loading applicant CV scores...</span>
            </div>
          ) : error ? (
            <div className="rounded-xl bg-[#fdf2f0] border border-[#f3bbb5] p-5 text-center space-y-2">
              <AlertCircle size={24} className="mx-auto text-[#b34a40]" />
              <div className="text-sm font-bold text-[#b34a40]">{error}</div>
              <p className="text-xs text-[#7b8490]">
                Ensure you are logged in as the HR Manager who owns this room.
              </p>
            </div>
          ) : (
            <>
              {/* Summary Metric Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3" data-testid="grid-cv-scores-metrics">
                <div className="rounded-xl border border-[#eef0e7] bg-[#fbfaf5] p-3.5">
                  <div className="text-[11px] font-medium text-[#7b8490] flex items-center gap-1.5">
                    <Users size={12} className="text-[#277254]" />
                    Total Applicants
                  </div>
                  <div className="mt-1 text-2xl font-bold text-[#253142]" data-testid="stat-total-applicants">
                    {data?.total_applicants ?? 0}
                  </div>
                </div>

                <div className="rounded-xl border border-[#eef0e7] bg-[#fbfaf5] p-3.5">
                  <div className="text-[11px] font-medium text-[#7b8490] flex items-center gap-1.5">
                    <CheckCircle2 size={12} className="text-[#277254]" />
                    Evaluated CVs
                  </div>
                  <div className="mt-1 text-2xl font-bold text-[#253142]" data-testid="stat-scored-applicants">
                    {data?.scored_applicants ?? 0}
                  </div>
                </div>

                <div className="rounded-xl border border-[#eef0e7] bg-[#fbfaf5] p-3.5">
                  <div className="text-[11px] font-medium text-[#7b8490] flex items-center gap-1.5">
                    <Gauge size={12} className="text-[#b47d00]" />
                    Average CV Score
                  </div>
                  <div className="mt-1 text-2xl font-bold text-[#277254]" data-testid="stat-avg-cv-score">
                    {data?.average_cv_score !== null ? `${data?.average_cv_score}%` : 'N/A'}
                  </div>
                </div>

                <div className="rounded-xl border border-[#eef0e7] bg-[#fbfaf5] p-3.5">
                  <div className="text-[11px] font-medium text-[#7b8490] flex items-center gap-1.5">
                    <Award size={12} className="text-[#277254]" />
                    Top Match Score
                  </div>
                  <div className="mt-1 text-2xl font-bold text-[#253142]" data-testid="stat-highest-cv-score">
                    {data?.highest_cv_score !== null ? `${data?.highest_cv_score}%` : 'N/A'}
                  </div>
                </div>
              </div>

              {/* Search & Filter Bar */}
              <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-[#fbfaf5] p-3 rounded-xl border border-[#eef0e7]">
                <div className="relative w-full sm:w-72">
                  <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#7b8490]" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search candidate name, email, or skill..."
                    data-testid="input-search-cv-scores"
                    className="w-full rounded-lg border border-[#d9dbd1] bg-white pl-8 pr-3 py-1.5 text-xs text-[#253142] placeholder:text-[#98a09c] focus:outline-none focus:ring-2 focus:ring-[#277254]/30"
                  />
                </div>

                <div className="flex items-center gap-2 w-full sm:w-auto justify-between sm:justify-end overflow-x-auto">
                  {/* Tier Filter Buttons */}
                  <div className="flex items-center gap-1 bg-[#eef0e7] p-0.5 rounded-lg text-[11px]">
                    {(['ALL', 'HIGH', 'MODERATE', 'LOW', 'PENDING'] as const).map((t) => (
                      <button
                        key={t}
                        type="button"
                        onClick={() => setScoreFilter(t)}
                        data-testid={`filter-tier-${t.toLowerCase()}`}
                        className={`rounded-md px-2 py-1 font-bold transition ${
                          scoreFilter === t
                            ? 'bg-white text-[#253142] shadow-2xs'
                            : 'text-[#687382] hover:text-[#253142]'
                        }`}
                      >
                        {t === 'ALL'
                          ? 'All'
                          : t === 'HIGH'
                          ? '≥75%'
                          : t === 'MODERATE'
                          ? '50-74%'
                          : t === 'LOW'
                          ? '<50%'
                          : 'No CV'}
                      </button>
                    ))}
                  </div>

                  {/* Sort Select */}
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value as SortOption)}
                    data-testid="select-sort-cv-scores"
                    className="rounded-lg border border-[#d9dbd1] bg-white px-2.5 py-1 text-xs text-[#253142] font-medium focus:outline-none focus:ring-1 focus:ring-[#277254]"
                  >
                    <option value="SCORE_DESC">Score: High to Low</option>
                    <option value="SCORE_ASC">Score: Low to High</option>
                    <option value="DATE_DESC">Newest Applied</option>
                    <option value="NAME_ASC">Name (A-Z)</option>
                  </select>
                </div>
              </div>

              {/* Applicants Table / List */}
              {filteredApplicants.length === 0 ? (
                <div
                  className="rounded-xl border border-dashed border-[#d9dbd1] p-10 text-center space-y-2 bg-white"
                  data-testid="card-empty-cv-scores"
                >
                  <Users size={32} className="mx-auto text-[#98a09c]" />
                  <div className="text-sm font-bold text-[#253142]">No applicants found</div>
                  <p className="text-xs text-[#7b8490] max-w-sm mx-auto">
                    {searchQuery || scoreFilter !== 'ALL'
                      ? 'No applicants match your current search or filter criteria.'
                      : 'Candidates who apply through the room link will automatically appear here with their semantic CV scores.'}
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto rounded-xl border border-[#eef0e7] bg-white">
                  <table className="w-full text-left text-xs" data-testid="table-applicant-cv-scores">
                    <thead className="bg-[#fbfaf5] border-b border-[#eef0e7] text-[11px] font-semibold text-[#7b8490] uppercase tracking-wider">
                      <tr>
                        <th className="px-4 py-3">Candidate</th>
                        <th className="px-4 py-3">CV Score</th>
                        <th className="px-4 py-3">Coverage</th>
                        <th className="px-4 py-3">Matched Skills</th>
                        <th className="px-4 py-3">Missing Skills</th>
                        <th className="px-4 py-3 text-right">Breakdown</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#eef0e7]">
                      {filteredApplicants.map((app) => {
                        const score = app.match_score;
                        const isHigh = score !== null && score >= 75;
                        const isMod = score !== null && score >= 50 && score < 75;

                        return (
                          <tr
                            key={app.application_id}
                            className="hover:bg-[#fbfaf5] transition group"
                            data-testid={`row-applicant-cv-${app.application_id}`}
                          >
                            {/* Candidate Info */}
                            <td className="px-4 py-3.5">
                              <div className="flex items-center gap-2.5">
                                <div className="grid h-8 w-8 place-items-center rounded-full bg-[#e2f0e9] font-bold text-[#1f5b43] text-xs shrink-0">
                                  {(app.candidate_name || app.candidate_email || 'C')
                                    .slice(0, 2)
                                    .toUpperCase()}
                                </div>
                                <div className="min-w-0">
                                  <div className="font-bold text-[#253142] truncate">
                                    {app.candidate_name || app.candidate_email}
                                  </div>
                                  <div className="text-[10px] text-[#7b8490] truncate">
                                    {app.candidate_email}
                                  </div>
                                </div>
                              </div>
                            </td>

                            {/* CV Match Score */}
                            <td className="px-4 py-3.5 whitespace-nowrap">
                              {score !== null ? (
                                <div className="flex items-center gap-2">
                                  <span
                                    className={`inline-flex items-center px-2 py-0.5 rounded-md font-black text-xs ${
                                      isHigh
                                        ? 'bg-[#e2f0e9] text-[#1f5b43] border border-[#a7d7c1]'
                                        : isMod
                                        ? 'bg-[#fff5db] text-[#b47d00] border border-[#f9e09d]'
                                        : 'bg-[#fbe9e7] text-[#b34a40] border border-[#f3bbb5]'
                                    }`}
                                    data-testid={`badge-cv-score-${app.application_id}`}
                                  >
                                    {score}%
                                  </span>
                                  <span className="text-[10px] text-[#7b8490]">
                                    {isHigh ? 'Strong' : isMod ? 'Moderate' : 'Low'}
                                  </span>
                                </div>
                              ) : (
                                <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-[#f1f3f5] text-[#687382] text-[10px] font-medium">
                                  No CV
                                </span>
                              )}
                            </td>

                            {/* Keyword Coverage */}
                            <td className="px-4 py-3.5 whitespace-nowrap">
                              <div className="text-[#253142] font-semibold">
                                {app.has_score ? `${app.keyword_coverage}%` : '—'}
                              </div>
                            </td>

                            {/* Matched Skills Chips */}
                            <td className="px-4 py-3.5 max-w-[180px]">
                              {app.skills_matched.length > 0 ? (
                                <div className="flex flex-wrap gap-1">
                                  {app.skills_matched.slice(0, 3).map((sk, idx) => (
                                    <span
                                      key={idx}
                                      className="inline-flex items-center rounded bg-[#e2f0e9] px-1.5 py-0.5 text-[10px] font-medium text-[#1f5b43]"
                                    >
                                      {sk}
                                    </span>
                                  ))}
                                  {app.skills_matched.length > 3 && (
                                    <span className="text-[10px] text-[#7b8490]">
                                      +{app.skills_matched.length - 3}
                                    </span>
                                  )}
                                </div>
                              ) : (
                                <span className="text-[11px] text-[#98a09c] italic">None</span>
                              )}
                            </td>

                            {/* Missing Skills Chips */}
                            <td className="px-4 py-3.5 max-w-[180px]">
                              {app.skills_missing.length > 0 ? (
                                <div className="flex flex-wrap gap-1">
                                  {app.skills_missing.slice(0, 2).map((sk, idx) => (
                                    <span
                                      key={idx}
                                      className="inline-flex items-center rounded bg-[#fbe9e7] px-1.5 py-0.5 text-[10px] font-medium text-[#b34a40]"
                                    >
                                      {sk}
                                    </span>
                                  ))}
                                  {app.skills_missing.length > 2 && (
                                    <span className="text-[10px] text-[#7b8490]">
                                      +{app.skills_missing.length - 2}
                                    </span>
                                  )}
                                </div>
                              ) : (
                                <span className="text-[10px] text-[#277254] font-medium">All matched</span>
                              )}
                            </td>

                            {/* Action Button */}
                            <td className="px-4 py-3.5 text-right whitespace-nowrap">
                              <button
                                type="button"
                                onClick={() => setSelectedApplicant(app)}
                                data-testid={`button-view-breakdown-${app.application_id}`}
                                className="inline-flex items-center gap-1 rounded-lg bg-[#fbfaf5] border border-[#d9dbd1] px-2.5 py-1 text-xs font-bold text-[#277254] hover:bg-[#e2f0e9] hover:border-[#277254] transition shadow-2xs"
                              >
                                <span>Inspect</span>
                                <ChevronRight size={13} />
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="border-t border-[#eef0e7] px-6 py-3.5 bg-[#fbfaf5] flex items-center justify-between">
          <div className="text-[11px] text-[#7b8490]">
            Displaying {filteredApplicants.length} applicant{filteredApplicants.length === 1 ? '' : 's'}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl bg-[#253142] px-4 py-2 text-xs font-bold text-white hover:bg-[#344458] transition shadow-xs"
          >
            Close
          </button>
        </div>
      </div>

      {/* Embedded Skill Breakdown Modal */}
      <CvSkillBreakdownModal
        isOpen={Boolean(selectedApplicant)}
        onClose={() => setSelectedApplicant(null)}
        applicant={selectedApplicant}
        roomTitle={room.title}
      />
    </div>
  );
}
