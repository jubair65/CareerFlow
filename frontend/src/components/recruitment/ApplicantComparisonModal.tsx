import React, { useState, useEffect } from 'react';
import {
  X,
  Users,
  Trophy,
  CheckCircle2,
  XCircle,
  FileText,
  Video,
  Eye,
  Activity,
  Gauge,
  Sparkles,
  AlertCircle,
  Clock,
  Award,
  Zap,
  TrendingUp,
  TrendingDown,
  Layers,
  Scale,
  RefreshCw,
} from 'lucide-react';
import {
  apiCompareApplicants,
  ApplicantComparisonResponse,
  ApplicantComparisonItem,
} from '../../api/recruitment';

interface ApplicantComparisonModalProps {
  isOpen: boolean;
  onClose: () => void;
  roomId: number | string | null;
  roomTitle?: string;
  applicationIds: number[];
  notify?: (message: string, tone?: 'success' | 'info' | 'error') => void;
}

export function ApplicantComparisonModal({
  isOpen,
  onClose,
  roomId,
  roomTitle,
  applicationIds,
  notify,
}: ApplicantComparisonModalProps) {
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [data, setData] = useState<ApplicantComparisonResponse | null>(null);

  useEffect(() => {
    if (!isOpen || !roomId || applicationIds.length < 2) {
      setData(null);
      setErrorMsg(null);
      return;
    }

    let isMounted = true;
    async function fetchComparison() {
      setLoading(true);
      setErrorMsg(null);
      try {
        const result = await apiCompareApplicants(roomId, applicationIds);
        if (isMounted) {
          setData(result);
        }
      } catch (err: any) {
        if (isMounted) {
          const msg =
            err.response?.data?.application_ids?.[0] ||
            err.response?.data?.error ||
            err.response?.data?.detail ||
            'Failed to load applicant comparison.';
          setErrorMsg(msg);
          notify?.(msg, 'error');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    fetchComparison();
    return () => {
      isMounted = false;
    };
  }, [isOpen, roomId, JSON.stringify(applicationIds)]);

  if (!isOpen) return null;

  const highestScore = data?.highest_final_score ?? null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-950/80 backdrop-blur-md overflow-y-auto"
      data-testid="modal-applicant-comparison"
    >
      <div className="relative w-full max-w-6xl max-h-[94vh] flex flex-col rounded-2xl bg-gradient-to-b from-slate-900 to-slate-950 border border-slate-800 shadow-2xl text-slate-100 overflow-hidden">
        
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between p-5 sm:p-6 border-b border-slate-800 bg-slate-900/60 gap-4">
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-indigo-500/20">
              <Scale className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <h2 className="text-lg font-bold text-white tracking-tight">
                  Side-by-Side Applicant Comparison
                </h2>
                <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  {data?.comparison_count ?? applicationIds.length} Candidates
                </span>
                {data && (
                  <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">
                    Weights: {data.cv_weight}% CV / {data.video_weight}% Video
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                {roomTitle || data?.room_title || 'Recruitment Room'} — Detailed score matrix, skills differentials, and behavioral signals
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 self-end sm:self-auto">
            {data && data.highest_final_score !== null && (
              <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700 text-xs">
                <Trophy className="w-4 h-4 text-amber-400" />
                <span className="text-slate-400">Top Score:</span>
                <span className="font-bold text-amber-300">{data.highest_final_score.toFixed(1)}</span>
                {data.average_final_score !== null && (
                  <>
                    <span className="text-slate-600">|</span>
                    <span className="text-slate-400">Avg:</span>
                    <span className="font-semibold text-slate-200">{data.average_final_score.toFixed(1)}</span>
                  </>
                )}
              </div>
            )}
            <button
              type="button"
              data-testid="btn-close-comparison-modal"
              onClick={onClose}
              className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/70 transition"
              title="Close Comparison"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
          {loading ? (
            <div className="py-24 flex flex-col items-center justify-center gap-3 text-slate-400">
              <RefreshCw className="w-8 h-8 animate-spin text-indigo-400" />
              <p className="text-sm font-medium">Aggregating applicant scores and skill matrices...</p>
            </div>
          ) : errorMsg ? (
            <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 flex items-center gap-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-400" />
              <p className="text-sm">{errorMsg}</p>
            </div>
          ) : !data || data.applicants.length === 0 ? (
            <div className="py-16 text-center text-slate-400">
              <AlertCircle className="w-10 h-10 mx-auto text-slate-500 mb-2" />
              <p className="text-sm">No applicant comparison data available.</p>
            </div>
          ) : (
            <div className="overflow-x-auto pb-4">
              <div className="min-w-[700px] space-y-6">

                {/* Candidate Overview Columns */}
                <div className="grid gap-4" style={{ gridTemplateColumns: `200px repeat(${data.applicants.length}, minmax(0, 1fr))` }}>
                  
                  {/* Row Label header */}
                  <div className="flex flex-col justify-end pb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Candidate Profile
                  </div>

                  {/* Candidate Profile Cards */}
                  {data.applicants.map((applicant, index) => {
                    const isTopScorer = applicant.best_in.includes('final_score');
                    return (
                      <div
                        key={applicant.application_id}
                        data-testid={`card-comparison-candidate-${applicant.application_id}`}
                        className={`relative p-4 rounded-2xl border transition-all ${
                          isTopScorer
                            ? 'bg-gradient-to-b from-indigo-950/40 via-slate-900 to-slate-900 border-indigo-500/60 shadow-lg shadow-indigo-950/30 ring-1 ring-indigo-500/30'
                            : 'bg-slate-900/70 border-slate-800'
                        }`}
                      >
                        {isTopScorer && (
                          <div className="absolute -top-2.5 right-3 flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-400 text-slate-950 shadow-md">
                            <Trophy className="w-3 h-3 fill-slate-950" />
                            Top Scorer
                          </div>
                        )}

                        <div className="flex items-center gap-3">
                          <div
                            className={`w-11 h-11 rounded-xl flex items-center justify-center font-bold text-sm text-white ${
                              isTopScorer
                                ? 'bg-gradient-to-br from-indigo-500 to-cyan-500 ring-2 ring-indigo-400/50'
                                : 'bg-slate-800 border border-slate-700 text-slate-200'
                            }`}
                          >
                            {applicant.avatar_initials}
                          </div>
                          <div className="min-w-0 flex-1">
                            <h3
                              data-testid={`text-candidate-name-${applicant.application_id}`}
                              className="text-sm font-bold text-white truncate"
                              title={applicant.candidate_name}
                            >
                              {applicant.candidate_name}
                            </h3>
                            <p className="text-xs text-slate-400 truncate" title={applicant.email}>
                              {applicant.email}
                            </p>
                          </div>
                        </div>

                        {/* Badges row */}
                        <div className="mt-3 flex items-center gap-1.5 flex-wrap">
                          {applicant.is_shortlisted ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                              Shortlisted
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-800 text-slate-400 border border-slate-700">
                              Standard
                            </span>
                          )}

                          <span className="px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-800/80 text-slate-300 border border-slate-700">
                            {applicant.hr_decision_display || applicant.hr_decision}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Section 1: Final Composite Scores & Differentials */}
                <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 space-y-3">
                  <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-indigo-400 border-b border-slate-800 pb-2">
                    <Gauge className="w-4 h-4" />
                    Composite Score & Group Differentials
                  </div>

                  <div className="grid gap-4 items-center py-2" style={{ gridTemplateColumns: `200px repeat(${data.applicants.length}, minmax(0, 1fr))` }}>
                    <div className="text-xs font-medium text-slate-300">
                      Final Score ({data.cv_weight}% CV / {data.video_weight}% Vid)
                    </div>
                    {data.applicants.map((app) => (
                      <div key={app.application_id} className="flex items-center justify-between gap-2">
                        {app.final_score !== null ? (
                          <div className="flex items-baseline gap-1">
                            <span
                              data-testid={`score-final-${app.application_id}`}
                              className={`text-lg font-extrabold ${
                                app.best_in.includes('final_score')
                                  ? 'text-amber-300'
                                  : 'text-white'
                              }`}
                            >
                              {app.final_score.toFixed(1)}
                            </span>
                            <span className="text-xs text-slate-500">/100</span>
                          </div>
                        ) : (
                          <span className="text-xs text-amber-400/80 font-medium flex items-center gap-1">
                            <Clock className="w-3.5 h-3.5" /> N/A - Pending
                          </span>
                        )}

                        {highestScore !== null && app.final_score !== null && (
                          <span
                            data-testid={`diff-final-${app.application_id}`}
                            className={`text-[11px] px-1.5 py-0.5 rounded font-bold ${
                              app.final_score === highestScore
                                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                                : 'bg-rose-500/10 text-rose-300 border border-rose-500/20'
                            }`}
                          >
                            {app.final_score === highestScore
                              ? 'Best'
                              : `-${(highestScore - app.final_score).toFixed(1)}`}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>

                  <div className="grid gap-4 items-center py-1 border-t border-slate-800/60" style={{ gridTemplateColumns: `200px repeat(${data.applicants.length}, minmax(0, 1fr))` }}>
                    <div className="text-xs text-slate-400">Score Tier</div>
                    {data.applicants.map((app) => (
                      <div key={app.application_id} className="text-xs font-semibold text-slate-300">
                        {app.score_tier === 'TIER_HIGH' ? (
                          <span className="text-emerald-400">High (75+)</span>
                        ) : app.score_tier === 'TIER_MEDIUM' ? (
                          <span className="text-amber-400">Medium (50-74)</span>
                        ) : app.score_tier === 'TIER_LOW' ? (
                          <span className="text-rose-400">Low (&lt;50)</span>
                        ) : (
                          <span className="text-slate-400">Pending</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Section 2: CV Match & Skill Differential Breakdown */}
                <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 space-y-3">
                  <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-cyan-400 border-b border-slate-800 pb-2">
                    <FileText className="w-4 h-4" />
                    CV Semantic Match & Skills Differential
                  </div>

                  {/* CV Match Score */}
                  <div className="grid gap-4 items-center py-2" style={{ gridTemplateColumns: `200px repeat(${data.applicants.length}, minmax(0, 1fr))` }}>
                    <div className="text-xs font-medium text-slate-300">
                      CV Match Score
                    </div>
                    {data.applicants.map((app) => (
                      <div key={app.application_id} className="flex items-center justify-between gap-2">
                        {app.cv_score !== null ? (
                          <div className="flex items-center gap-2">
                            <span
                              data-testid={`score-cv-${app.application_id}`}
                              className="text-sm font-bold text-slate-100"
                            >
                              {app.cv_score.toFixed(1)}%
                            </span>
                            {app.best_in.includes('cv_score') && (
                              <span className="text-[10px] px-1.5 py-0.5 rounded font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                                Top CV
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-xs text-amber-400/80 font-medium">N/A - Pending</span>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Matched Skills */}
                  <div className="grid gap-4 items-start py-2 border-t border-slate-800/60" style={{ gridTemplateColumns: `200px repeat(${data.applicants.length}, minmax(0, 1fr))` }}>
                    <div className="text-xs font-medium text-slate-300">
                      Matched Skills
                    </div>
                    {data.applicants.map((app) => (
                      <div key={app.application_id} className="space-y-1.5">
                        <div className="flex items-center gap-1.5">
                          <span className="text-xs font-bold text-emerald-400">
                            {app.matched_skills.length} matched
                          </span>
                          {app.best_in.includes('skills_match') && (
                            <span className="text-[10px] px-1.5 py-0.2 rounded font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                              Most Skills
                            </span>
                          )}
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {app.matched_skills.length > 0 ? (
                            app.matched_skills.map((skill, sIdx) => (
                              <span
                                key={sIdx}
                                className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-950/60 text-emerald-300 border border-emerald-800/60"
                              >
                                {skill}
                              </span>
                            ))
                          ) : (
                            <span className="text-[11px] text-slate-500 italic">None matched</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Missing Skills */}
                  <div className="grid gap-4 items-start py-2 border-t border-slate-800/60" style={{ gridTemplateColumns: `200px repeat(${data.applicants.length}, minmax(0, 1fr))` }}>
                    <div className="text-xs font-medium text-slate-300">
                      Missing Required Skills
                    </div>
                    {data.applicants.map((app) => (
                      <div key={app.application_id} className="space-y-1.5">
                        <span className="text-xs text-slate-400">
                          {app.missing_skills.length} missing
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {app.missing_skills.length > 0 ? (
                            app.missing_skills.map((skill, sIdx) => (
                              <span
                                key={sIdx}
                                className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-rose-950/40 text-rose-300 border border-rose-900/50"
                              >
                                {skill}
                              </span>
                            ))
                          ) : (
                            <span className="text-[11px] text-emerald-400 font-medium">All skills covered</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Section 3: Video Presentation & Behavioral AI Signals */}
                <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 space-y-3">
                  <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-purple-400 border-b border-slate-800 pb-2">
                    <Video className="w-4 h-4" />
                    Video Presentation & Behavioral AI Signals
                  </div>

                  {/* Video Score */}
                  <div className="grid gap-4 items-center py-2" style={{ gridTemplateColumns: `200px repeat(${data.applicants.length}, minmax(0, 1fr))` }}>
                    <div className="text-xs font-medium text-slate-300">
                      Video Presentation Score
                    </div>
                    {data.applicants.map((app) => (
                      <div key={app.application_id} className="flex items-center justify-between gap-2">
                        {app.video_score !== null ? (
                          <div className="flex items-center gap-2">
                            <span
                              data-testid={`score-video-${app.application_id}`}
                              className="text-sm font-bold text-slate-100"
                            >
                              {app.video_score.toFixed(1)}/100
                            </span>
                            {app.best_in.includes('video_score') && (
                              <span className="text-[10px] px-1.5 py-0.5 rounded font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                                Top Video
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-xs text-amber-400/80 font-medium">N/A - Pending</span>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Camera Eye Contact */}
                  <div className="grid gap-4 items-center py-2 border-t border-slate-800/60" style={{ gridTemplateColumns: `200px repeat(${data.applicants.length}, minmax(0, 1fr))` }}>
                    <div className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
                      <Eye className="w-3.5 h-3.5 text-indigo-400" />
                      Camera Eye Contact
                    </div>
                    {data.applicants.map((app) => (
                      <div key={app.application_id} className="flex items-center justify-between gap-2">
                        {app.eye_contact_percent !== null ? (
                          <div className="flex items-center gap-2">
                            <span
                              data-testid={`metric-eye-${app.application_id}`}
                              className="text-xs font-bold text-slate-200"
                            >
                              {app.eye_contact_percent.toFixed(0)}%
                            </span>
                            {app.best_in.includes('eye_contact') && (
                              <span className="text-[10px] px-1.5 py-0.5 rounded font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                                Best Eye Contact
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-xs text-slate-500">N/A</span>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Speaking Pace (WPM) */}
                  <div className="grid gap-4 items-center py-2 border-t border-slate-800/60" style={{ gridTemplateColumns: `200px repeat(${data.applicants.length}, minmax(0, 1fr))` }}>
                    <div className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
                      <Activity className="w-3.5 h-3.5 text-amber-400" />
                      Speaking Pace (WPM)
                    </div>
                    {data.applicants.map((app) => {
                      const isOptimal = app.wpm >= 130 && app.wpm <= 160;
                      return (
                        <div key={app.application_id} className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-slate-200">
                            {app.wpm > 0 ? `${app.wpm} WPM` : 'N/A'}
                          </span>
                          {app.wpm > 0 && isOptimal && (
                            <span className="text-[10px] px-1.5 py-0.5 rounded font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                              Optimal (130-160)
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {/* Filler Words */}
                  <div className="grid gap-4 items-center py-2 border-t border-slate-800/60" style={{ gridTemplateColumns: `200px repeat(${data.applicants.length}, minmax(0, 1fr))` }}>
                    <div className="text-xs font-medium text-slate-300">
                      Filler Words Count
                    </div>
                    {data.applicants.map((app) => (
                      <div key={app.application_id} className="text-xs text-slate-300">
                        {app.filler_words_count} {app.filler_words_count === 1 ? 'word' : 'words'}
                      </div>
                    ))}
                  </div>

                  {/* Posture Score */}
                  <div className="grid gap-4 items-center py-2 border-t border-slate-800/60" style={{ gridTemplateColumns: `200px repeat(${data.applicants.length}, minmax(0, 1fr))` }}>
                    <div className="text-xs font-medium text-slate-300">
                      Posture & Alignment
                    </div>
                    {data.applicants.map((app) => (
                      <div key={app.application_id} className="text-xs text-slate-300">
                        {app.posture_score !== null ? `${app.posture_score.toFixed(0)}/100` : 'N/A'}
                      </div>
                    ))}
                  </div>
                </div>

              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-3 border-t border-slate-800 bg-slate-900/70 text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>AI scores and metrics are calculated objectively to support HR hiring decisions.</span>
          </div>

          <button
            type="button"
            data-testid="btn-footer-close-comparison"
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium transition text-xs"
          >
            Close Matrix
          </button>
        </div>

      </div>
    </div>
  );
}
