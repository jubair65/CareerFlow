import React, { useState, useEffect } from 'react';
import {
  X,
  Calculator,
  Award,
  FileText,
  Video,
  AlertTriangle,
  Info,
  Layers,
  Sparkles,
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
      role="dialog"
      aria-modal="true"
      data-testid="modal-score-breakdown"
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-[#253142]/60 backdrop-blur-xs overflow-y-auto animate-in fade-in"
    >
      <div className="relative w-full max-w-3xl max-h-[92vh] flex flex-col rounded-2xl bg-white border border-[#d9dbd1] shadow-2xl text-[#253142] overflow-hidden">
        
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-[#eef0e7] bg-[#fbfaf5]">
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 rounded-xl bg-[#e2f0e9] border border-[#a7d7c1] flex items-center justify-center text-[#277254] shadow-xs">
              <Calculator className="w-5 h-5 text-[#277254]" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h2
                  className="text-lg font-bold tracking-tight text-[#253142]"
                  data-testid="text-breakdown-candidate-name"
                >
                  {loading
                    ? 'Loading score explanation...'
                    : `${data?.candidate_name || candidateName || 'Candidate'} — Score Breakdown`}
                </h2>
                
              </div>
              <p className="text-xs text-[#7b8490] mt-0.5">
                Recruitment Room:{' '}
                <span className="text-[#253142] font-semibold">
                  {data?.room_title || 'Loading...'}
                </span>{' '}
                • {data?.candidate_email}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-[#7b8490] hover:bg-[#eef0e7] hover:text-[#253142] transition cursor-pointer"
            data-testid="btn-close-breakdown-modal"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5 bg-[#faf9f5]">
          
          {loading ? (
            <div className="py-20 text-center text-[#7b8490]">
              <div className="inline-block w-8 h-8 border-4 border-[#277254] border-t-transparent rounded-full animate-spin mb-3"></div>
              <p className="text-sm">Deconstructing AI scoring metrics & contributions...</p>
            </div>
          ) : errorMsg ? (
            <div className="p-4 rounded-xl bg-[#fde8e8] border border-[#f8b4b4] text-[#9b1c1c] text-sm flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-[#e02424] shrink-0" />
              <span>{errorMsg}</span>
            </div>
          ) : data ? (
            <>
              {/* Top Banner: Composite Final Score & Room Weights */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
                
                {/* Final Score Card */}
                <div
                  className="p-4 rounded-2xl bg-white border border-[#d9dbd1] shadow-2xs flex flex-col justify-between"
                  data-testid="card-final-score"
                >
                  <div className="flex items-center justify-between text-xs font-bold text-[#7b8490] uppercase tracking-wider">
                    <span>Composite Final Score</span>
                    <Award className="w-4 h-4 text-[#d97706]" />
                  </div>
                  <div className="mt-2 flex items-baseline gap-1.5">
                    <span className="text-3xl font-extrabold text-[#253142]" data-testid="text-breakdown-final-score">
                      {data.final_score !== null ? data.final_score.toFixed(1) : '—'}
                    </span>
                    <span className="text-xs text-[#7b8490]">/ 100 max</span>
                  </div>
                  <div className="mt-3 text-[11px] text-[#7b8490] pt-2 border-t border-[#eef0e7] flex items-center justify-between">
                    <span>Status:</span>
                    {data.is_partial_score ? (
                      <span className="text-[#d97706] font-bold">Partial Score</span>
                    ) : (
                      <span className="text-[#277254] font-bold">Complete Score</span>
                    )}
                  </div>
                </div>

                {/* Configured Weights */}
                <div className="p-4 rounded-2xl bg-white border border-[#d9dbd1] shadow-2xs flex flex-col justify-between">
                  <div className="flex items-center justify-between text-xs font-bold text-[#7b8490] uppercase tracking-wider">
                    <span>Evaluation Split</span>
                    <Layers className="w-4 h-4 text-[#277254]" />
                  </div>
                  <div className="mt-2 grid grid-cols-2 gap-2 text-center">
                    <div className="p-2 rounded-xl bg-[#e2f0e9]/50 border border-[#a7d7c1]">
                      <div className="text-[11px] text-[#1f5b43] font-bold">CV Weight</div>
                      <div className="text-xl font-extrabold text-[#1f5b43] mt-0.5" data-testid="text-cv-weight">
                        {data.cv_weight}%
                      </div>
                    </div>
                    <div className="p-2 rounded-xl bg-[#fbfaf5] border border-[#d9dbd1]">
                      <div className="text-[11px] text-[#526072] font-bold">Video Weight</div>
                      <div className="text-xl font-extrabold text-[#253142] mt-0.5" data-testid="text-video-weight">
                        {data.video_weight}%
                      </div>
                    </div>
                  </div>
                  <div className="mt-3 text-[11px] text-[#7b8490] pt-2 border-t border-[#eef0e7] text-center">
                    Rule Total: <strong className="text-[#253142]">100%</strong>
                  </div>
                </div>

                {/* Score Contribution Shares */}
                <div className="p-4 rounded-2xl bg-white border border-[#d9dbd1] shadow-2xs flex flex-col justify-between">
                  <div className="flex items-center justify-between text-xs font-bold text-[#7b8490] uppercase tracking-wider">
                    <span>Points Contributed</span>
                    <Sparkles className="w-4 h-4 text-[#277254]" />
                  </div>
                  <div className="mt-2 space-y-1.5 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-[#1f5b43] font-medium flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-[#277254]"></span>
                        CV Match Points:
                      </span>
                      <strong className="text-[#253142]" data-testid="text-cv-points-summary">
                        {data.cv_component.points_contributed !== null
                          ? `+${data.cv_component.points_contributed.toFixed(1)} pts`
                          : '—'}
                      </strong>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[#526072] font-medium flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-[#526072]"></span>
                        Video Analysis Points:
                      </span>
                      <strong className="text-[#253142]" data-testid="text-video-points-summary">
                        {data.video_component.points_contributed !== null
                          ? `+${data.video_component.points_contributed.toFixed(1)} pts`
                          : '—'}
                      </strong>
                    </div>
                  </div>
                  <div className="mt-3 text-[11px] text-[#7b8490] pt-2 border-t border-[#eef0e7] flex items-center justify-between">
                    <span>Total Score:</span>
                    <strong className="text-[#253142]">
                      {data.final_score !== null ? `${data.final_score.toFixed(1)} / 100` : '—'}
                    </strong>
                  </div>
                </div>

              </div>

              {/* Visual Split Contribution Bar */}
              <div className="p-4 rounded-2xl bg-white border border-[#d9dbd1] shadow-2xs space-y-2.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-[#253142] flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-[#277254]" />
                    Visual Component Contribution Split
                  </span>
                  <span className="text-[#7b8490] text-[11px]">
                    Scale: 0 to 100 Points
                  </span>
                </div>

                {/* Segmented Bar */}
                <div
                  className="h-6 w-full rounded-xl bg-[#f1f3f5] p-1 flex overflow-hidden border border-[#d9dbd1] gap-1"
                  data-testid="bar-contribution-split"
                >
                  {cvBarWidth > 0 && (
                    <div
                      style={{ width: `${cvBarWidth}%` }}
                      className="h-full bg-[#277254] rounded-lg flex items-center justify-center text-[10px] font-bold text-white transition-all duration-500 shadow-2xs"
                      title={`CV Match: +${cvPoints.toFixed(1)} pts (${data.cv_component.percentage_of_total ?? 0}%)`}
                    >
                      {cvBarWidth > 12 && `CV +${cvPoints.toFixed(1)}`}
                    </div>
                  )}
                  {videoBarWidth > 0 && (
                    <div
                      style={{ width: `${videoBarWidth}%` }}
                      className="h-full bg-[#526072] rounded-lg flex items-center justify-center text-[10px] font-bold text-white transition-all duration-500 shadow-2xs"
                      title={`Video Analysis: +${videoPoints.toFixed(1)} pts (${data.video_component.percentage_of_total ?? 0}%)`}
                    >
                      {videoBarWidth > 12 && `Video +${videoPoints.toFixed(1)}`}
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between text-[11px] text-[#7b8490] px-1">
                  <span className="flex items-center gap-1.5 text-[#1f5b43] font-medium">
                    <span className="w-2.5 h-2.5 rounded-sm bg-[#277254]"></span>
                    CV Contribution: +{cvPoints.toFixed(1)} pts ({data.cv_component.percentage_of_total ?? 0}% of total)
                  </span>
                  <span className="flex items-center gap-1.5 text-[#526072] font-medium">
                    <span className="w-2.5 h-2.5 rounded-sm bg-[#526072]"></span>
                    Video Contribution: +{videoPoints.toFixed(1)} pts ({data.video_component.percentage_of_total ?? 0}% of total)
                  </span>
                </div>
              </div>

              {/* Mathematical Formula Explanation Box */}
              <div
                className="p-4 rounded-2xl bg-white border border-[#d9dbd1] shadow-2xs text-xs space-y-2"
                data-testid="box-formula-display"
              >
                <div className="flex items-center gap-2 font-bold text-[#253142]">
                  <Info className="w-4 h-4 text-[#277254]" />
                  Mathematical Scoring Formula & Arithmetic Derivation
                </div>
                <div className="p-3 rounded-xl bg-[#fbfaf5] border border-[#eef0e7] font-mono text-[#253142] text-xs break-all">
                  {data.formula_display}
                </div>
                <p className="text-[11px] text-[#7b8490]">
                  The Final Applicant Score is calculated strictly as a weighted arithmetic sum:
                  <span className="font-mono text-[#253142] font-bold ml-1">
                    Score = (CV Weight × CV Score + Video Weight × Video Score) ÷ 100
                  </span>.
                </p>
              </div>

              {/* Missing Components Alert Banner */}
              {data.missing_components_explanation && (
                <div
                  className="p-4 rounded-xl bg-[#fef3c7] border border-[#fde68a] text-[#92400e] text-xs space-y-1.5"
                  data-testid="alert-missing-components"
                >
                  <div className="flex items-center gap-2 font-bold text-[#78350f]">
                    <AlertTriangle className="w-4 h-4 text-[#d97706]" />
                    Partial Score & Missing Signal Notice
                  </div>
                  <p className="leading-relaxed">
                    {data.missing_components_explanation}
                  </p>
                </div>
              )}

              {/* Side-by-Side Granular Component Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                
                {/* CV Component Card */}
                <div
                  className="p-4 rounded-2xl bg-white border border-[#d9dbd1] shadow-2xs space-y-3"
                  data-testid="card-cv-breakdown"
                >
                  <div className="flex items-center justify-between pb-2 border-b border-[#eef0e7]">
                    <div className="flex items-center gap-2 font-bold text-[#253142] text-sm">
                      <FileText className="w-4 h-4 text-[#277254]" />
                      CV Match Signal
                    </div>
                    {data.cv_component.is_available ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#e2f0e9] text-[#1f5b43] border border-[#a7d7c1]">
                        Evaluated
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#fde8e8] text-[#9b1c1c] border border-[#f8b4b4]">
                        Missing
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="p-2.5 rounded-xl bg-[#fbfaf5] border border-[#d9dbd1]">
                      <div className="text-[#7b8490] text-[11px]">Raw Match Score</div>
                      <div className="text-lg font-bold text-[#253142] mt-0.5" data-testid="text-cv-raw-score">
                        {data.cv_component.raw_score !== null
                          ? `${data.cv_component.raw_score.toFixed(1)} / 100`
                          : 'N/A'}
                      </div>
                    </div>
                    <div className="p-2.5 rounded-xl bg-[#fbfaf5] border border-[#d9dbd1]">
                      <div className="text-[#7b8490] text-[11px]">Weighted Points</div>
                      <div className="text-lg font-bold text-[#277254] mt-0.5" data-testid="text-cv-points-contributed">
                        {data.cv_component.points_contributed !== null
                          ? `+${data.cv_component.points_contributed.toFixed(1)} pts`
                          : '0.0 pts'}
                      </div>
                    </div>
                  </div>

                  {data.cv_component.is_available ? (
                    <div className="space-y-2 text-xs pt-1">
                      <div className="text-[11px] text-[#7b8490] font-bold">
                        Matched Skills ({data.cv_component.sub_metrics.skills_matched?.length ?? 0}):
                      </div>
                      <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
                        {(data.cv_component.sub_metrics.skills_matched ?? []).length > 0 ? (
                          data.cv_component.sub_metrics.skills_matched!.map((skill, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-0.5 rounded-lg text-[10px] font-medium bg-[#e2f0e9] text-[#1f5b43] border border-[#a7d7c1]"
                            >
                              ✓ {skill}
                            </span>
                          ))
                        ) : (
                          <span className="text-[#7b8490] italic text-[11px]">No skill match details recorded.</span>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="text-xs text-[#9b1c1c] italic bg-[#fde8e8] p-2.5 rounded-xl border border-[#f8b4b4]">
                      {data.cv_component.missing_reason || 'CV file was not provided.'}
                    </div>
                  )}
                </div>

                {/* Video Component Card */}
                <div
                  className="p-4 rounded-2xl bg-white border border-[#d9dbd1] shadow-2xs space-y-3"
                  data-testid="card-video-breakdown"
                >
                  <div className="flex items-center justify-between pb-2 border-b border-[#eef0e7]">
                    <div className="flex items-center gap-2 font-bold text-[#253142] text-sm">
                      <Video className="w-4 h-4 text-[#277254]" />
                      Video Presentation Signal
                    </div>
                    {data.video_component.is_available ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#e2f0e9] text-[#1f5b43] border border-[#a7d7c1]">
                        Evaluated
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#fde8e8] text-[#9b1c1c] border border-[#f8b4b4]">
                        Missing
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="p-2.5 rounded-xl bg-[#fbfaf5] border border-[#d9dbd1]">
                      <div className="text-[#7b8490] text-[11px]">Raw Presentation Score</div>
                      <div className="text-lg font-bold text-[#253142] mt-0.5" data-testid="text-video-raw-score">
                        {data.video_component.raw_score !== null
                          ? `${data.video_component.raw_score.toFixed(1)} / 100`
                          : 'N/A'}
                      </div>
                    </div>
                    <div className="p-2.5 rounded-xl bg-[#fbfaf5] border border-[#d9dbd1]">
                      <div className="text-[#7b8490] text-[11px]">Weighted Points</div>
                      <div className="text-lg font-bold text-[#277254] mt-0.5" data-testid="text-video-points-contributed">
                        {data.video_component.points_contributed !== null
                          ? `+${data.video_component.points_contributed.toFixed(1)} pts`
                          : '0.0 pts'}
                      </div>
                    </div>
                  </div>

                  {data.video_component.is_available ? (
                    <div className="space-y-2 text-xs pt-1">
                      <div className="text-[11px] text-[#7b8490] font-bold">Sub-Metrics Breakdown:</div>
                      <div className="grid grid-cols-2 gap-2 text-[11px]">
                        <div className="p-1.5 rounded-lg bg-[#fbfaf5] border border-[#d9dbd1] flex justify-between">
                          <span className="text-[#7b8490]">Speech Score:</span>
                          <strong className="text-[#253142]">
                            {data.video_component.sub_metrics.speech_score !== null && data.video_component.sub_metrics.speech_score !== undefined
                              ? `${data.video_component.sub_metrics.speech_score}%`
                              : '—'}
                          </strong>
                        </div>
                        <div className="p-1.5 rounded-lg bg-[#fbfaf5] border border-[#d9dbd1] flex justify-between">
                          <span className="text-[#7b8490]">Visual Presence:</span>
                          <strong className="text-[#253142]">
                            {data.video_component.sub_metrics.visual_score !== null && data.video_component.sub_metrics.visual_score !== undefined
                              ? `${data.video_component.sub_metrics.visual_score}%`
                              : '—'}
                          </strong>
                        </div>
                        <div className="p-1.5 rounded-lg bg-[#fbfaf5] border border-[#d9dbd1] flex justify-between">
                          <span className="text-[#7b8490]">Speaking Rate:</span>
                          <strong className="text-[#253142]">
                            {data.video_component.sub_metrics.wpm || '135'} WPM
                          </strong>
                        </div>
                        <div className="p-1.5 rounded-lg bg-[#fbfaf5] border border-[#d9dbd1] flex justify-between">
                          <span className="text-[#7b8490]">Filler Words:</span>
                          <strong className="text-[#253142]">
                            {data.video_component.sub_metrics.filler_words_count ?? 0}
                          </strong>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-xs text-[#9b1c1c] italic bg-[#fde8e8] p-2.5 rounded-xl border border-[#f8b4b4]">
                      {data.video_component.missing_reason || 'Video submission was not provided.'}
                    </div>
                  )}
                </div>

              </div>
            </>
          ) : null}

        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-[#eef0e7] bg-[#fbfaf5]">
          <div className="text-[11px] text-[#7b8490] flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-[#277254]" />
            Scores calculated using Room weights configured under room evaluation settings.
          </div>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-bold bg-[#253142] text-white hover:bg-[#344458] transition cursor-pointer"
          >
            Close Breakdown
          </button>
        </div>

      </div>
    </div>
  );
}
