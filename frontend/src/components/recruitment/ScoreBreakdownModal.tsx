import React, { useState, useEffect } from 'react';
import {
  X,
  Calculator,
  Award,
  FileText,
  Video,
  CheckCircle2,
  AlertTriangle,
  Info,
  Clock,
  Layers,
  Sparkles,
  HelpCircle,
} from 'lucide-react';
import {
  apiGetApplicantScoreBreakdown,
  ApplicantScoreBreakdown,
} from '../../api/recruitment';

interface ScoreBreakdownModalProps {
  isOpen: boolean;
  onClose: () => void;
  applicationId: number | null;
  candidateName?: string;
  notify?: (message: string, tone?: 'success' | 'info' | 'error') => void;
}

export function ScoreBreakdownModal({
  isOpen,
  onClose,
  applicationId,
  candidateName,
  notify,
}: ScoreBreakdownModalProps) {
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [data, setData] = useState<ApplicantScoreBreakdown | null>(null);

  useEffect(() => {
    if (!isOpen || !applicationId) {
      setData(null);
      setErrorMsg(null);
      return;
    }

    let isMounted = true;
    async function fetchBreakdown() {
      setLoading(true);
      setErrorMsg(null);
      try {
        const result = await apiGetApplicantScoreBreakdown(applicationId);
        if (isMounted) {
          setData(result);
        }
      } catch (err: any) {
        if (isMounted) {
          const msg =
            err.response?.data?.detail ||
            err.response?.data?.error ||
            'Failed to load score breakdown data.';
          setErrorMsg(msg);
          if (notify) notify(msg, 'error');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    fetchBreakdown();
    return () => {
      isMounted = false;
    };
  }, [isOpen, applicationId]);

  if (!isOpen) return null;

  const cvPoints = data?.cv_component.points_contributed ?? 0;
  const videoPoints = data?.video_component.points_contributed ?? 0;
  const finalScore = data?.final_score ?? 0;

  // Split calculations for visual progress bar
  const cvBarWidth = finalScore > 0 ? (cvPoints / 100) * 100 : 0;
  const videoBarWidth = finalScore > 0 ? (videoPoints / 100) * 100 : 0;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-slate-950/80 backdrop-blur-md overflow-y-auto"
      data-testid="modal-score-breakdown"
    >
      <div className="relative w-full max-w-3xl max-h-[92vh] flex flex-col rounded-2xl bg-gradient-to-b from-slate-900 to-slate-950 border border-slate-800 shadow-2xl text-slate-100 overflow-hidden">
        
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-slate-800 bg-slate-900/60">
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center text-white shadow-lg shadow-indigo-500/20">
              <Calculator className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h2
                  className="text-lg font-bold tracking-tight text-white"
                  data-testid="text-breakdown-candidate-name"
                >
                  {loading
                    ? 'Loading score explanation...'
                    : `${data?.candidate_name || candidateName || 'Candidate'} — Score Breakdown`}
                </h2>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-indigo-950/70 text-indigo-300 border border-indigo-700/50">
                  US-27
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Recruitment Room:{' '}
                <span className="text-slate-200 font-medium">
                  {data?.room_title || 'Loading...'}
                </span>{' '}
                • {data?.candidate_email}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            data-testid="btn-close-breakdown-modal"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          
          {loading ? (
            <div className="py-20 text-center text-slate-400">
              <div className="inline-block w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-3"></div>
              <p className="text-sm">Deconstructing AI scoring metrics & contributions...</p>
            </div>
          ) : errorMsg ? (
            <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-600/40 text-rose-200 text-sm flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          ) : data ? (
            <>
              {/* Top Banner: Composite Final Score & Room Weights */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                
                {/* Final Score Card */}
                <div
                  className="p-4 rounded-xl bg-gradient-to-br from-slate-900 to-indigo-950/40 border border-indigo-500/30 flex flex-col justify-between"
                  data-testid="card-final-score"
                >
                  <div className="flex items-center justify-between text-xs text-indigo-300 font-medium">
                    <span>Composite Final Score</span>
                    <Award className="w-4 h-4 text-amber-400" />
                  </div>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span
                      className="text-4xl font-extrabold text-white tracking-tight"
                      data-testid="text-composite-final-score"
                    >
                      {data.final_score !== null ? data.final_score.toFixed(1) : '—'}
                    </span>
                    <span className="text-xs text-slate-400 font-semibold">/ 100</span>
                  </div>
                  <div className="mt-3 text-xs flex items-center justify-between pt-2 border-t border-slate-800/80">
                    <span className="text-slate-400">Evaluation:</span>
                    {data.is_partial_score ? (
                      <span
                        className="text-amber-400 font-semibold flex items-center gap-1"
                        data-testid="badge-partial-score"
                      >
                        <AlertTriangle className="w-3.5 h-3.5" />
                        Partial (Pro-rated)
                      </span>
                    ) : (
                      <span className="text-emerald-400 font-semibold flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Complete Multi-modal
                      </span>
                    )}
                  </div>
                </div>

                {/* Configured Weights Card */}
                <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 flex flex-col justify-between">
                  <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
                    <span>Configured Evaluation Split</span>
                    <Layers className="w-4 h-4 text-cyan-400" />
                  </div>
                  <div className="mt-2 grid grid-cols-2 gap-2 text-center">
                    <div className="p-2 rounded-lg bg-emerald-950/40 border border-emerald-600/30">
                      <div className="text-[11px] text-emerald-400 font-semibold">CV Weight</div>
                      <div className="text-xl font-bold text-emerald-200 mt-0.5" data-testid="text-cv-weight">
                        {data.cv_weight}%
                      </div>
                    </div>
                    <div className="p-2 rounded-lg bg-cyan-950/40 border border-cyan-600/30">
                      <div className="text-[11px] text-cyan-400 font-semibold">Video Weight</div>
                      <div className="text-xl font-bold text-cyan-200 mt-0.5" data-testid="text-video-weight">
                        {data.video_weight}%
                      </div>
                    </div>
                  </div>
                  <div className="mt-3 text-[11px] text-slate-400 pt-2 border-t border-slate-700/40 text-center">
                    Rule Total: <strong className="text-slate-200">100%</strong>
                  </div>
                </div>

                {/* Score Contribution Shares */}
                <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 flex flex-col justify-between">
                  <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
                    <span>Points Contributed</span>
                    <Sparkles className="w-4 h-4 text-indigo-400" />
                  </div>
                  <div className="mt-2 space-y-1.5 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-emerald-400 flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                        CV Match Points:
                      </span>
                      <strong className="text-white" data-testid="text-cv-points-summary">
                        {data.cv_component.points_contributed !== null
                          ? `+${data.cv_component.points_contributed.toFixed(1)} pts`
                          : '—'}
                      </strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-cyan-400 flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
                        Video Analysis Points:
                      </span>
                      <strong className="text-white" data-testid="text-video-points-summary">
                        {data.video_component.points_contributed !== null
                          ? `+${data.video_component.points_contributed.toFixed(1)} pts`
                          : '—'}
                      </strong>
                    </div>
                  </div>
                  <div className="mt-3 text-[11px] text-slate-400 pt-2 border-t border-slate-700/40 flex items-center justify-between">
                    <span>Total Score:</span>
                    <strong className="text-slate-200">
                      {data.final_score !== null ? `${data.final_score.toFixed(1)} / 100` : '—'}
                    </strong>
                  </div>
                </div>

              </div>

              {/* Visual Split Contribution Bar (US-27-T1 & US-27-T4) */}
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-200 flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-indigo-400" />
                    Visual Component Contribution Split
                  </span>
                  <span className="text-slate-400 text-[11px]">
                    Scale: 0 to 100 Points
                  </span>
                </div>

                {/* Segmented Bar */}
                <div
                  className="h-6 w-full rounded-lg bg-slate-950 p-1 flex overflow-hidden border border-slate-800 gap-1"
                  data-testid="bar-contribution-split"
                >
                  {cvBarWidth > 0 && (
                    <div
                      style={{ width: `${cvBarWidth}%` }}
                      className="h-full bg-gradient-to-r from-emerald-600 to-emerald-500 rounded flex items-center justify-center text-[10px] font-bold text-white transition-all duration-500"
                      title={`CV Match: +${cvPoints.toFixed(1)} pts (${data.cv_component.percentage_of_total ?? 0}%)`}
                    >
                      {cvBarWidth > 12 && `CV +${cvPoints.toFixed(1)}`}
                    </div>
                  )}
                  {videoBarWidth > 0 && (
                    <div
                      style={{ width: `${videoBarWidth}%` }}
                      className="h-full bg-gradient-to-r from-cyan-600 to-cyan-500 rounded flex items-center justify-center text-[10px] font-bold text-white transition-all duration-500"
                      title={`Video Analysis: +${videoPoints.toFixed(1)} pts (${data.video_component.percentage_of_total ?? 0}%)`}
                    >
                      {videoBarWidth > 12 && `Video +${videoPoints.toFixed(1)}`}
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between text-[11px] text-slate-400 px-1">
                  <span className="flex items-center gap-1.5 text-emerald-400">
                    <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500"></span>
                    CV Contribution: +{cvPoints.toFixed(1)} pts ({data.cv_component.percentage_of_total ?? 0}% of total)
                  </span>
                  <span className="flex items-center gap-1.5 text-cyan-400">
                    <span className="w-2.5 h-2.5 rounded-sm bg-cyan-500"></span>
                    Video Contribution: +{videoPoints.toFixed(1)} pts ({data.video_component.percentage_of_total ?? 0}% of total)
                  </span>
                </div>
              </div>

              {/* Mathematical Formula Explanation Box (US-27-T1) */}
              <div
                className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 text-xs space-y-2"
                data-testid="box-formula-display"
              >
                <div className="flex items-center gap-2 font-semibold text-slate-300">
                  <Info className="w-4 h-4 text-indigo-400" />
                  Mathematical Scoring Formula & Arithmetic Derivation
                </div>
                <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 font-mono text-indigo-300 text-xs break-all">
                  {data.formula_display}
                </div>
                <p className="text-[11px] text-slate-400">
                  The Final Applicant Score is calculated strictly as a weighted arithmetic sum:
                  <span className="font-mono text-slate-300 ml-1">
                    Score = (CV Weight × CV Score + Video Weight × Video Score) ÷ 100
                  </span>.
                </p>
              </div>

              {/* Missing Components Alert Banner (US-27-T5) */}
              {data.missing_components_explanation && (
                <div
                  className="p-4 rounded-xl bg-amber-950/40 border border-amber-600/40 text-amber-200 text-xs space-y-1.5"
                  data-testid="alert-missing-components"
                >
                  <div className="flex items-center gap-2 font-bold text-amber-300">
                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                    Partial Score & Missing Signal Notice
                  </div>
                  <p className="leading-relaxed">
                    {data.missing_components_explanation}
                  </p>
                </div>
              )}

              {/* Side-by-Side Granular Component Cards (US-27-T4) */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                
                {/* CV Component Card */}
                <div
                  className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3"
                  data-testid="card-cv-breakdown"
                >
                  <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                    <div className="flex items-center gap-2 font-semibold text-white text-sm">
                      <FileText className="w-4 h-4 text-emerald-400" />
                      CV Match Signal
                    </div>
                    {data.cv_component.is_available ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950/60 text-emerald-300 border border-emerald-600/40">
                        Evaluated
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-950/60 text-rose-300 border border-rose-600/40">
                        Missing
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                      <div className="text-slate-400 text-[11px]">Raw Match Score</div>
                      <div className="text-lg font-bold text-slate-100 mt-0.5" data-testid="text-cv-raw-score">
                        {data.cv_component.raw_score !== null
                          ? `${data.cv_component.raw_score.toFixed(1)} / 100`
                          : 'N/A'}
                      </div>
                    </div>
                    <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                      <div className="text-slate-400 text-[11px]">Weighted Points</div>
                      <div className="text-lg font-bold text-emerald-400 mt-0.5" data-testid="text-cv-points-contributed">
                        {data.cv_component.points_contributed !== null
                          ? `+${data.cv_component.points_contributed.toFixed(1)} pts`
                          : '0.0 pts'}
                      </div>
                    </div>
                  </div>

                  {data.cv_component.is_available ? (
                    <div className="space-y-2 text-xs pt-1">
                      <div className="text-[11px] text-slate-400 font-medium">
                        Matched Skills ({data.cv_component.sub_metrics.skills_matched?.length ?? 0}):
                      </div>
                      <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
                        {(data.cv_component.sub_metrics.skills_matched ?? []).length > 0 ? (
                          data.cv_component.sub_metrics.skills_matched!.map((skill, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-0.5 rounded text-[10px] font-medium bg-emerald-950/40 text-emerald-300 border border-emerald-600/30"
                            >
                              ✓ {skill}
                            </span>
                          ))
                        ) : (
                          <span className="text-slate-500 italic text-[11px]">No skill match details recorded.</span>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="text-xs text-rose-300/90 italic bg-rose-950/20 p-2.5 rounded-lg border border-rose-800/30">
                      {data.cv_component.missing_reason || 'CV file was not provided.'}
                    </div>
                  )}
                </div>

                {/* Video Component Card */}
                <div
                  className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3"
                  data-testid="card-video-breakdown"
                >
                  <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                    <div className="flex items-center gap-2 font-semibold text-white text-sm">
                      <Video className="w-4 h-4 text-cyan-400" />
                      Video Presentation Signal
                    </div>
                    {data.video_component.is_available ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-950/60 text-cyan-300 border border-cyan-600/40">
                        Evaluated
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-950/60 text-rose-300 border border-rose-600/40">
                        Missing
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                      <div className="text-slate-400 text-[11px]">Raw Presentation Score</div>
                      <div className="text-lg font-bold text-slate-100 mt-0.5" data-testid="text-video-raw-score">
                        {data.video_component.raw_score !== null
                          ? `${data.video_component.raw_score.toFixed(1)} / 100`
                          : 'N/A'}
                      </div>
                    </div>
                    <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                      <div className="text-slate-400 text-[11px]">Weighted Points</div>
                      <div className="text-lg font-bold text-cyan-400 mt-0.5" data-testid="text-video-points-contributed">
                        {data.video_component.points_contributed !== null
                          ? `+${data.video_component.points_contributed.toFixed(1)} pts`
                          : '0.0 pts'}
                      </div>
                    </div>
                  </div>

                  {data.video_component.is_available ? (
                    <div className="space-y-2 text-xs pt-1">
                      <div className="text-[11px] text-slate-400 font-medium">Sub-Metrics Breakdown:</div>
                      <div className="grid grid-cols-2 gap-2 text-[11px]">
                        <div className="p-1.5 rounded bg-slate-950/40 border border-slate-800 flex justify-between">
                          <span className="text-slate-400">Speech Score:</span>
                          <strong className="text-slate-200">
                            {data.video_component.sub_metrics.speech_score !== null && data.video_component.sub_metrics.speech_score !== undefined
                              ? `${data.video_component.sub_metrics.speech_score}%`
                              : '—'}
                          </strong>
                        </div>
                        <div className="p-1.5 rounded bg-slate-950/40 border border-slate-800 flex justify-between">
                          <span className="text-slate-400">Visual Presence:</span>
                          <strong className="text-slate-200">
                            {data.video_component.sub_metrics.visual_score !== null && data.video_component.sub_metrics.visual_score !== undefined
                              ? `${data.video_component.sub_metrics.visual_score}%`
                              : '—'}
                          </strong>
                        </div>
                        <div className="p-1.5 rounded bg-slate-950/40 border border-slate-800 flex justify-between">
                          <span className="text-slate-400">Speaking Rate:</span>
                          <strong className="text-slate-200">
                            {data.video_component.sub_metrics.wpm || '135'} WPM
                          </strong>
                        </div>
                        <div className="p-1.5 rounded bg-slate-950/40 border border-slate-800 flex justify-between">
                          <span className="text-slate-400">Filler Words:</span>
                          <strong className="text-slate-200">
                            {data.video_component.sub_metrics.filler_words_count ?? 0}
                          </strong>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-xs text-rose-300/90 italic bg-rose-950/20 p-2.5 rounded-lg border border-rose-800/30">
                      {data.video_component.missing_reason || 'Video submission was not provided.'}
                    </div>
                  )}
                </div>

              </div>
            </>
          ) : null}

        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-slate-800 bg-slate-900/60">
          <div className="text-[11px] text-slate-400 flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-indigo-400" />
            Scores calculated using Room weights configured under US-20.
          </div>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 text-slate-200 hover:bg-slate-700 transition"
          >
            Close Breakdown
          </button>
        </div>

      </div>
    </div>
  );
}
