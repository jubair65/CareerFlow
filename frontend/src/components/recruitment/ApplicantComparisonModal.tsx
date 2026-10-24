import React, { useState, useEffect } from 'react';
import {
  X,
  Trophy,
  CheckCircle2,
  FileText,
  Video,
  Eye,
  Activity,
  Gauge,
  Sparkles,
  AlertCircle,
  Clock,
  Scale,
  RefreshCw,
} from 'lucide-react';
import {
  apiCompareApplicants,
  ApplicantComparisonResponse,
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
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/50 backdrop-blur-sm overflow-y-auto"
      data-testid="modal-applicant-comparison"
    >
      <div className="relative w-full max-w-6xl max-h-[94vh] flex flex-col rounded-2xl bg-white border border-[#d9dbd1] shadow-2xl text-[#253142] overflow-hidden">
        
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between p-5 sm:p-6 border-b border-[#ecefe7] bg-[#fbfaf5] gap-4">
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 rounded-xl bg-[#253142] flex items-center justify-center text-white shadow-sm">
              <Scale className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <h2 className="text-lg font-bold text-[#253142] tracking-tight">
                  Side-by-Side Applicant Comparison
                </h2>
                <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-[#e2f0e9] text-[#277254] border border-[#b8d8c7]">
                  {data?.comparison_count ?? applicationIds.length} Candidates
                </span>
                {data && (
                  <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-[#f4f6ef] text-[#526072] border border-[#d9dbd1]">
                    Weights: {data.cv_weight}% CV / {data.video_weight}% Video
                  </span>
                )}
              </div>
              <p className="text-xs text-[#687382] mt-0.5">
                {roomTitle || data?.room_title || 'Recruitment Room'} — Detailed score matrix, skills differentials, and behavioral signals
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 self-end sm:self-auto">
            {data && data.highest_final_score !== null && (
              <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white border border-[#d9dbd1] text-xs shadow-xs">
                <Trophy className="w-4 h-4 text-[#b89c3b]" />
                <span className="text-[#687382]">Top Score:</span>
                <span className="font-bold text-[#b89c3b]">{data.highest_final_score.toFixed(1)}</span>
                {data.average_final_score !== null && (
                  <>
                    <span className="text-[#d9dbd1]">|</span>
                    <span className="text-[#687382]">Avg:</span>
                    <span className="font-semibold text-[#253142]">{data.average_final_score.toFixed(1)}</span>
                  </>
                )}
              </div>
            )}
            <button
              type="button"
              data-testid="btn-close-comparison-modal"
              onClick={onClose}
              className="p-2 rounded-xl text-[#687382] hover:text-[#253142] hover:bg-[#f4f6ef] transition"
              title="Close Comparison"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
          {loading ? (
            <div className="py-24 flex flex-col items-center justify-center gap-3 text-[#687382]">
              <RefreshCw className="w-8 h-8 animate-spin text-[#277254]" />
              <p className="text-sm font-medium">Aggregating applicant scores and skill matrices...</p>
            </div>
          ) : errorMsg ? (
            <div className="p-4 rounded-xl bg-[#fee2e2] border border-[#fca5a5] text-[#dc2626] flex items-center gap-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0 text-[#dc2626]" />
              <p className="text-sm">{errorMsg}</p>
            </div>
          ) : !data || data.applicants.length === 0 ? (
            <div className="py-16 text-center text-[#687382]">
              <AlertCircle className="w-10 h-10 mx-auto text-[#98a09c] mb-2" />
              <p className="text-sm">No applicant comparison data available.</p>
            </div>
          ) : (
            <div className="overflow-x-auto pb-4">
              <div className="min-w-[700px] space-y-6">

                {/* Candidate Overview Columns */}
                <div className="grid gap-4" style={{ gridTemplateColumns: `200px repeat(${data.applicants.length}, minmax(0, 1fr))` }}>
                  
                  {/* Row Label header */}
                  <div className="flex flex-col justify-end pb-3 text-xs font-semibold uppercase tracking-wider text-[#687382]">
                    Candidate Profile
                  </div>

                  {/* Candidate Profile Cards */}
                  {data.applicants.map((applicant) => {
                    const isTopScorer = applicant.best_in.includes('final_score');
                    return (
                      <div
                        key={applicant.application_id}
                        data-testid={`card-comparison-candidate-${applicant.application_id}`}
                        className={`relative p-4 rounded-2xl border transition-all ${
                          isTopScorer
                            ? 'bg-[#fbfaf5] border-[#b89c3b]/40 shadow-md ring-1 ring-[#b89c3b]/20'
                            : 'bg-[#fbfaf5] border-[#d9dbd1]'
                        }`}
                      >
                        {isTopScorer && (
                          <div className="absolute -top-2.5 right-3 flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#f5c84b] text-[#253142] shadow-sm">
                            <Trophy className="w-3 h-3" />
                            Top Scorer
                          </div>
                        )}

                        <div className="flex items-center gap-3">
                          <div
                            className={`w-11 h-11 rounded-xl flex items-center justify-center font-bold text-sm text-white ${
                              isTopScorer
                                ? 'bg-[#253142] ring-2 ring-[#b89c3b]/40'
                                : 'bg-[#687382]'
                            }`}
                          >
                            {applicant.avatar_initials}
                          </div>
                          <div className="min-w-0 flex-1">
                            <h3
                              data-testid={`text-candidate-name-${applicant.application_id}`}
                              className="text-sm font-bold text-[#253142] truncate"
                              title={applicant.candidate_name}
                            >
                              {applicant.candidate_name}
                            </h3>
                            <p className="text-xs text-[#687382] truncate" title={applicant.email}>
                              {applicant.email}
                            </p>
                          </div>
                        </div>

                        {/* Badges row */}
                        <div className="mt-3 flex items-center gap-1.5 flex-wrap">
                          {applicant.is_shortlisted ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-semibold bg-[#e2f0e9] text-[#277254] border border-[#b8d8c7]">
                              <CheckCircle2 className="w-3 h-3 text-[#277254]" />
                              Shortlisted
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-[#f4f6ef] text-[#687382] border border-[#d9dbd1]">
                              Standard
                            </span>
                          )}

                          <span className="px-2 py-0.5 rounded-md text-[11px] font-medium bg-[#f4f6ef] text-[#526072] border border-[#d9dbd1]">
                            {applicant.hr_decision_display || applicant.hr_decision}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Section 1: Final Composite Scores & Differentials */}
                <div className="rounded-xl border border-[#d9dbd1] bg-white p-4 space-y-3">
                  <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#277254] border-b border-[#ecefe7] pb-2">
                    <Gauge className="w-4 h-4" />
                    Composite Score & Group Differentials
                  </div>

                  <div className="grid gap-4 items-center py-2" style={{ gridTemplateColumns: `200px repeat(${data.applicants.length}, minmax(0, 1fr))` }}>
                    <div className="text-xs font-medium text-[#526072]">
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
                                  ? 'text-[#b89c3b]'
                                  : 'text-[#253142]'
                              }`}
                            >
                              {app.final_score.toFixed(1)}
                            </span>
                            <span className="text-xs text-[#98a09c]">/100</span>
                          </div>
                        ) : (
                          <span className="text-xs text-[#b89c3b] font-medium flex items-center gap-1">
                            <Clock className="w-3.5 h-3.5" /> N/A - Pending
                          </span>
                        )}

                        {highestScore !== null && app.final_score !== null && (
                          <span
                            data-testid={`diff-final-${app.application_id}`}
                            className={`text-[11px] px-1.5 py-0.5 rounded font-bold ${
                              app.final_score === highestScore
                                ? 'bg-[#e2f0e9] text-[#277254] border border-[#b8d8c7]'
                                : 'bg-[#fee2e2] text-[#dc2626] border border-[#fca5a5]'
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

                  <div className="grid gap-4 items-center py-1 border-t border-[#ecefe7]" style={{ gridTemplateColumns: `200px repeat(${data.applicants.length}, minmax(0, 1fr))` }}>
                    <div className="text-xs text-[#687382]">Score Tier</div>
                    {data.applicants.map((app) => (
                      <div key={app.application_id} className="text-xs font-semibold">
                        {app.score_tier === 'TIER_HIGH' ? (
                          <span className="text-[#277254]">High (75+)</span>
                        ) : app.score_tier === 'TIER_MEDIUM' ? (
                          <span className="text-[#b89c3b]">Medium (50-74)</span>
                        ) : app.score_tier === 'TIER_LOW' ? (
                          <span className="text-[#dc2626]">Low (&lt;50)</span>
                        ) : (
                          <span className="text-[#687382]">Pending</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Section 2: CV Match & Skill Differential Breakdown */}
                <div className="rounded-xl border border-[#d9dbd1] bg-white p-4 space-y-3">
                  <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#3a6384] border-b border-[#ecefe7] pb-2">
                    <FileText className="w-4 h-4" />
                    CV Semantic Match & Skills Differential
                  </div>

                  {/* CV Match Score */}
                  <div className="grid gap-4 items-center py-2" style={{ gridTemplateColumns: `200px repeat(${data.applicants.length}, minmax(0, 1fr))` }}>
                    <div className="text-xs font-medium text-[#526072]">
                      CV Match Score
                    </div>
                    {data.applicants.map((app) => (
                      <div key={app.application_id} className="flex items-center justify-between gap-2">
                        {app.cv_score !== null ? (
                          <div className="flex items-center gap-2">
                            <span
                              data-testid={`score-cv-${app.application_id}`}
                              className="text-sm font-bold text-[#253142]"
                            >
                              {app.cv_score.toFixed(1)}%
                            </span>
                            {app.best_in.includes('cv_score') && (
                              <span className="text-[10px] px-1.5 py-0.5 rounded font-bold bg-[#e0edf5] text-[#3a6384] border border-[#b3cedf]">
                                Top CV
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-xs text-[#b89c3b] font-medium">N/A - Pending</span>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Matched Skills */}
                  <div className="grid gap-4 items-start py-2 border-t border-[#ecefe7]" style={{ gridTemplateColumns: `200px repeat(${data.applicants.length}, minmax(0, 1fr))` }}>
                    <div className="text-xs font-medium text-[#526072]">
                      Matched Skills
                    </div>
                    {data.applicants.map((app) => (
                      <div key={app.application_id} className="space-y-1.5">
                        <div className="flex items-center gap-1.5">
                          <span className="text-xs font-bold text-[#277254]">
                            {app.matched_skills.length} matched
                          </span>
                          {app.best_in.includes('skills_match') && (
                            <span className="text-[10px] px-1.5 py-0.2 rounded font-bold bg-[#e2f0e9] text-[#277254] border border-[#b8d8c7]">
                              Most Skills
                            </span>
                          )}
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {app.matched_skills.length > 0 ? (
                            app.matched_skills.map((skill, sIdx) => (
                              <span
                                key={sIdx}
                                className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-[#e2f0e9] text-[#277254] border border-[#b8d8c7]"
                              >
                                {skill}
                              </span>
                            ))
                          ) : (
                            <span className="text-[11px] text-[#98a09c] italic">None matched</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Missing Skills */}
                  <div className="grid gap-4 items-start py-2 border-t border-[#ecefe7]" style={{ gridTemplateColumns: `200px repeat(${data.applicants.length}, minmax(0, 1fr))` }}>
                    <div className="text-xs font-medium text-[#526072]">
                      Missing Required Skills
                    </div>
                    {data.applicants.map((app) => (
                      <div key={app.application_id} className="space-y-1.5">
                        <span className="text-xs text-[#687382]">
                          {app.missing_skills.length} missing
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {app.missing_skills.length > 0 ? (
                            app.missing_skills.map((skill, sIdx) => (
                              <span
                                key={sIdx}
                                className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-[#fee2e2] text-[#dc2626] border border-[#fca5a5]"
                              >
                                {skill}
                              </span>
                            ))
                          ) : (
                            <span className="text-[11px] text-[#277254] font-medium">All skills covered</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Section 3: Video Presentation & Behavioral AI Signals */}
                <div className="rounded-xl border border-[#d9dbd1] bg-white p-4 space-y-3">
                  <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#9a7922] border-b border-[#ecefe7] pb-2">
                    <Video className="w-4 h-4" />
                    Video Presentation & Behavioral AI Signals
                  </div>

                  {/* Video Score */}
                  <div className="grid gap-4 items-center py-2" style={{ gridTemplateColumns: `200px repeat(${data.applicants.length}, minmax(0, 1fr))` }}>
                    <div className="text-xs font-medium text-[#526072]">
                      Video Presentation Score
                    </div>
                    {data.applicants.map((app) => (
                      <div key={app.application_id} className="flex items-center justify-between gap-2">
                        {app.video_score !== null ? (
                          <div className="flex items-center gap-2">
                            <span
                              data-testid={`score-video-${app.application_id}`}
                              className="text-sm font-bold text-[#253142]"
                            >
                              {app.video_score.toFixed(1)}/100
                            </span>
                            {app.best_in.includes('video_score') && (
                              <span className="text-[10px] px-1.5 py-0.5 rounded font-bold bg-[#fef3c7] text-[#9a7922] border border-[#fcd34d]">
                                Top Video
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-xs text-[#b89c3b] font-medium">N/A - Pending</span>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Camera Eye Contact */}
                  <div className="grid gap-4 items-center py-2 border-t border-[#ecefe7]" style={{ gridTemplateColumns: `200px repeat(${data.applicants.length}, minmax(0, 1fr))` }}>
                    <div className="text-xs font-medium text-[#526072] flex items-center gap-1.5">
                      <Eye className="w-3.5 h-3.5 text-[#3a6384]" />
                      Camera Eye Contact
                    </div>
                    {data.applicants.map((app) => (
                      <div key={app.application_id} className="flex items-center justify-between gap-2">
                        {app.eye_contact_percent !== null ? (
                          <div className="flex items-center gap-2">
                            <span
                              data-testid={`metric-eye-${app.application_id}`}
                              className="text-xs font-bold text-[#253142]"
                            >
                              {app.eye_contact_percent.toFixed(0)}%
                            </span>
                            {app.best_in.includes('eye_contact') && (
                              <span className="text-[10px] px-1.5 py-0.5 rounded font-bold bg-[#e0edf5] text-[#3a6384] border border-[#b3cedf]">
                                Best Eye Contact
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-xs text-[#98a09c]">N/A</span>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Speaking Pace (WPM) */}
                  <div className="grid gap-4 items-center py-2 border-t border-[#ecefe7]" style={{ gridTemplateColumns: `200px repeat(${data.applicants.length}, minmax(0, 1fr))` }}>
                    <div className="text-xs font-medium text-[#526072] flex items-center gap-1.5">
                      <Activity className="w-3.5 h-3.5 text-[#b89c3b]" />
                      Speaking Pace (WPM)
                    </div>
                    {data.applicants.map((app) => {
                      const isOptimal = app.wpm >= 130 && app.wpm <= 160;
                      return (
                        <div key={app.application_id} className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-[#253142]">
                            {app.wpm > 0 ? `${app.wpm} WPM` : 'N/A'}
                          </span>
                          {app.wpm > 0 && isOptimal && (
                            <span className="text-[10px] px-1.5 py-0.5 rounded font-medium bg-[#e2f0e9] text-[#277254] border border-[#b8d8c7]">
                              Optimal (130-160)
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {/* Filler Words */}
                  <div className="grid gap-4 items-center py-2 border-t border-[#ecefe7]" style={{ gridTemplateColumns: `200px repeat(${data.applicants.length}, minmax(0, 1fr))` }}>
                    <div className="text-xs font-medium text-[#526072]">
                      Filler Words Count
                    </div>
                    {data.applicants.map((app) => (
                      <div key={app.application_id} className="text-xs text-[#526072]">
                        {app.filler_words_count} {app.filler_words_count === 1 ? 'word' : 'words'}
                      </div>
                    ))}
                  </div>

                  {/* Posture Score */}
                  <div className="grid gap-4 items-center py-2 border-t border-[#ecefe7]" style={{ gridTemplateColumns: `200px repeat(${data.applicants.length}, minmax(0, 1fr))` }}>
                    <div className="text-xs font-medium text-[#526072]">
                      Posture & Alignment
                    </div>
                    {data.applicants.map((app) => (
                      <div key={app.application_id} className="text-xs text-[#526072]">
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
        <div className="flex items-center justify-between px-6 py-3 border-t border-[#ecefe7] bg-[#fbfaf5] text-xs text-[#687382]">
          <div className="flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-[#277254]" />
            <span>AI scores and metrics are calculated objectively to support HR hiring decisions.</span>
          </div>

          <button
            type="button"
            data-testid="btn-footer-close-comparison"
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-[#253142] hover:bg-[#33435a] text-white font-medium transition text-xs cursor-pointer"
          >
            Close Matrix
          </button>
        </div>

      </div>
    </div>
  );
}
