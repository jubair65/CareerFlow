import React, { useState, useEffect } from 'react';
import {
  X,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  FileText,
  Video,
  Award,
  Sparkles,
  ArrowRightLeft,
  User,
  Calendar,
  Layers,
  Send,
  HelpCircle,
  ThumbsUp,
  MessageSquare,
  AlertCircle,
  Download,
  Loader2,
} from 'lucide-react';
import {
  apiGetCandidateReviewDetail,
  apiSubmitCandidateDecision,
  apiDownloadCandidateReportPdf,
  triggerPdfDownload,
  CandidateReviewDetail,
  HrDecisionType,
} from '../../api/recruitment';

interface CandidateReviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  applicationId: number | null;
  onDecisionRecorded?: (applicationId: number, decision: string) => void;
  notify?: (message: string, tone?: 'success' | 'info' | 'error') => void;
}

type TabType = 'OVERVIEW' | 'CV_DETAILS' | 'VIDEO_DETAILS';

export function CandidateReviewModal({
  isOpen,
  onClose,
  applicationId,
  onDecisionRecorded,
  notify,
}: CandidateReviewModalProps) {
  const [loading, setLoading] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [data, setData] = useState<CandidateReviewDetail | null>(null);

  // Form State
  const [selectedDecision, setSelectedDecision] = useState<'CONFIRMED' | 'OVERRIDDEN' | 'REJECTED' | 'ON_HOLD'>('CONFIRMED');
  const [decisionNotes, setDecisionNotes] = useState<string>('');
  const [activeTab, setActiveTab] = useState<TabType>('OVERVIEW');
  const [downloadingPdf, setDownloadingPdf] = useState(false);

  const handleDownloadPdf = async () => {
    if (!applicationId) return;
    try {
      setDownloadingPdf(true);
      const blob = await apiDownloadCandidateReportPdf(applicationId);
      const candName = data?.candidate_name?.replace(/\s+/g, '_') || 'Candidate';
      triggerPdfDownload(blob, `CareerFlow_Candidate_${applicationId}_${candName}_Report.pdf`);
      if (notify) notify('Candidate PDF report downloaded successfully.', 'success');
    } catch {
      if (notify) notify('Failed to download candidate PDF report.', 'error');
    } finally {
      setDownloadingPdf(false);
    }
  };

  // Load applicant details when modal opens
  useEffect(() => {
    if (!isOpen || !applicationId) {
      setData(null);
      setErrorMsg(null);
      setSuccessMsg(null);
      return;
    }

    let isMounted = true;
    async function loadData() {
      setLoading(true);
      setErrorMsg(null);
      try {
        const detail = await apiGetCandidateReviewDetail(applicationId);
        if (isMounted) {
          setData(detail);
          if (detail.hr_decision && detail.hr_decision !== 'UNDECIDED') {
            setSelectedDecision(detail.hr_decision as any);
          } else {
            setSelectedDecision(detail.is_shortlisted ? 'CONFIRMED' : 'OVERRIDDEN');
          }
          setDecisionNotes(detail.hr_decision_notes || '');
        }
      } catch (err: any) {
        if (isMounted) {
          const msg = err.response?.data?.error || err.response?.data?.detail || 'Failed to load candidate review details.';
          setErrorMsg(msg);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    loadData();
    return () => {
      isMounted = false;
    };
  }, [isOpen, applicationId]);

  if (!isOpen) return null;

  const isOverride = selectedDecision === 'OVERRIDDEN';
  const isNotesValid = !isOverride || decisionNotes.trim().length >= 5;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!applicationId || !data) return;

    if (isOverride && decisionNotes.trim().length < 5) {
      setErrorMsg('An explanatory justification note (at least 5 characters) is required when overriding the AI recommendation.');
      return;
    }

    setSubmitting(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const res = await apiSubmitCandidateDecision(applicationId, {
        decision: selectedDecision,
        notes: decisionNotes.trim(),
      });

      setSuccessMsg(res.message);
      if (notify) {
        notify(res.message, 'success');
      }

      // Refresh local review state
      const refreshed = await apiGetCandidateReviewDetail(applicationId);
      setData(refreshed);

      if (onDecisionRecorded) {
        onDecisionRecorded(applicationId, selectedDecision);
      }
    } catch (err: any) {
      const serverErr =
        err.response?.data?.notes?.[0] ||
        err.response?.data?.error ||
        err.response?.data?.detail ||
        'Failed to save decision. Please try again.';
      setErrorMsg(serverErr);
      if (notify) {
        notify(serverErr, 'error');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const getDecisionBadge = (decision: HrDecisionType) => {
    switch (decision) {
      case 'CONFIRMED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-950/60 text-emerald-300 border border-emerald-600/40">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            Shortlist Confirmed
          </span>
        );
      case 'OVERRIDDEN':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-950/60 text-amber-300 border border-amber-600/40">
            <ArrowRightLeft className="w-3.5 h-3.5 text-amber-400" />
            AI Overridden
          </span>
        );
      case 'REJECTED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-950/60 text-rose-300 border border-rose-600/40">
            <XCircle className="w-3.5 h-3.5 text-rose-400" />
            Rejected
          </span>
        );
      case 'ON_HOLD':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-950/60 text-blue-300 border border-blue-600/40">
            <Clock className="w-3.5 h-3.5 text-blue-400" />
            On Hold
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            Pending HR Review
          </span>
        );
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-slate-950/80 backdrop-blur-md overflow-y-auto"
      data-testid="modal-candidate-review"
    >
      <div className="relative w-full max-w-4xl max-h-[92vh] flex flex-col rounded-2xl bg-gradient-to-b from-slate-900 to-slate-950 border border-slate-800 shadow-2xl text-slate-100 overflow-hidden">
        
        {/* Top Header */}
        <div className="flex items-start justify-between p-6 border-b border-slate-800 bg-slate-900/60">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center text-white shadow-lg shadow-indigo-500/20">
              <User className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h2 className="text-xl font-bold tracking-tight text-white" data-testid="heading-candidate-name">
                  {loading ? 'Loading applicant...' : data?.candidate_name || 'Candidate Review'}
                </h2>
                {data && getDecisionBadge(data.hr_decision)}
              </div>
              <p className="text-sm text-slate-400 mt-0.5">
                {data?.candidate_email} • Room: <span className="text-slate-200 font-medium">{data?.room_title}</span>
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleDownloadPdf}
              disabled={downloadingPdf || !applicationId}
              data-testid="button-download-candidate-pdf"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 text-slate-200 border border-slate-700 hover:bg-[#277254] hover:text-white hover:border-[#277254] transition disabled:opacity-50"
              title="Download evaluation report as PDF"
            >
              {downloadingPdf ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin text-white" />
              ) : (
                <Download className="w-3.5 h-3.5" />
              )}
              <span>{downloadingPdf ? 'Exporting PDF...' : 'Download PDF Report'}</span>
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              data-testid="button-close-review-modal"
              aria-label="Close modal"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">

          {/* US-26 AC#5: Prominent AI Advisory Disclaimer */}
          <div
            className="flex items-start gap-3.5 p-4 rounded-xl bg-amber-950/30 border border-amber-600/40 text-amber-200"
            data-testid="banner-ai-advisory-disclaimer"
          >
            <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div className="text-xs sm:text-sm leading-relaxed">
              <strong className="font-semibold text-amber-300">AI Advisory Disclaimer:</strong>{' '}
              {data?.ai_disclaimer ||
                'AI-generated scores and shortlisting recommendations are advisory tools designed to support, not replace, human hiring decisions.'}
            </div>
          </div>

          {/* Feedback alerts */}
          {errorMsg && (
            <div
              className="flex items-center gap-2 p-3.5 rounded-xl bg-rose-950/50 border border-rose-600/40 text-rose-200 text-sm"
              data-testid="alert-decision-error"
            >
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {successMsg && (
            <div
              className="flex items-center gap-2 p-3.5 rounded-xl bg-emerald-950/50 border border-emerald-600/40 text-emerald-200 text-sm"
              data-testid="alert-decision-success"
            >
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {loading ? (
            <div className="py-16 text-center text-slate-400">
              <div className="inline-block w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-3"></div>
              <p>Gathering candidate score telemetry and AI signals...</p>
            </div>
          ) : data ? (
            <>
              {/* Score & AI Recommendation Dashboard Card */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                
                {/* Composite Final Score */}
                <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 flex flex-col justify-between">
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span>Composite Final Score</span>
                    <Award className="w-4 h-4 text-amber-400" />
                  </div>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-3xl font-extrabold text-white" data-testid="text-final-score">
                      {data.final_score !== null ? data.final_score.toFixed(1) : '—'}
                    </span>
                    <span className="text-xs text-slate-400">/ 100</span>
                  </div>
                  <div className="mt-3 text-xs text-slate-400 flex items-center justify-between pt-2 border-t border-slate-700/40">
                    <span>Weights:</span>
                    <span>CV {data.cv_weight}% • Video {data.video_weight}%</span>
                  </div>
                </div>

                {/* Sub-Scores */}
                <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 flex flex-col justify-between">
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span>Component Scores</span>
                    <Layers className="w-4 h-4 text-cyan-400" />
                  </div>
                  <div className="grid grid-cols-2 gap-3 mt-2">
                    <div>
                      <div className="text-xs text-slate-400">CV Score</div>
                      <div className="text-xl font-bold text-slate-100" data-testid="text-cv-score">
                        {data.cv_score !== null ? data.cv_score.toFixed(1) : '—'}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-400">Video Score</div>
                      <div className="text-xl font-bold text-slate-100" data-testid="text-video-score">
                        {data.video_score !== null ? data.video_score.toFixed(1) : '—'}
                      </div>
                    </div>
                  </div>
                  <div className="mt-3 text-xs text-slate-400 pt-2 border-t border-slate-700/40">
                    {data.is_partial_score ? (
                      <span className="text-amber-400">⚠️ Calculated with partial score</span>
                    ) : (
                      <span className="text-emerald-400">✓ Complete evaluation</span>
                    )}
                  </div>
                </div>

                {/* AI Recommendation (Advisory) */}
                <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 flex flex-col justify-between">
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span>AI Advisory Suggestion</span>
                    <Sparkles className="w-4 h-4 text-indigo-400" />
                  </div>
                  <div className="mt-2">
                    <span
                      className={`inline-block px-2.5 py-1 rounded-lg text-xs font-semibold ${
                        data.is_shortlisted
                          ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-600/40'
                          : 'bg-slate-800 text-slate-300 border border-slate-700'
                      }`}
                      data-testid="badge-ai-recommendation"
                    >
                      {data.ai_recommendation_label}
                    </span>
                  </div>
                  <p
                    className="mt-2 text-xs text-slate-400 line-clamp-2"
                    data-testid="text-ai-recommendation-reason"
                  >
                    {data.shortlist_reason || 'Criteria evaluation applied automatically.'}
                  </p>
                </div>
              </div>

              {/* Navigation Tabs */}
              <div className="flex border-b border-slate-800">
                <button
                  type="button"
                  onClick={() => setActiveTab('OVERVIEW')}
                  className={`px-4 py-2.5 text-sm font-medium border-b-2 transition -mb-px flex items-center gap-2 ${
                    activeTab === 'OVERVIEW'
                      ? 'border-indigo-500 text-indigo-300 bg-indigo-950/20'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                  data-testid="tab-review-overview"
                >
                  <FileText className="w-4 h-4" />
                  Signal Overview
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('CV_DETAILS')}
                  className={`px-4 py-2.5 text-sm font-medium border-b-2 transition -mb-px flex items-center gap-2 ${
                    activeTab === 'CV_DETAILS'
                      ? 'border-indigo-500 text-indigo-300 bg-indigo-950/20'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                  data-testid="tab-review-cv"
                >
                  <Award className="w-4 h-4" />
                  CV Skills Match ({data.cv_summary.skills_matched.length})
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('VIDEO_DETAILS')}
                  className={`px-4 py-2.5 text-sm font-medium border-b-2 transition -mb-px flex items-center gap-2 ${
                    activeTab === 'VIDEO_DETAILS'
                      ? 'border-indigo-500 text-indigo-300 bg-indigo-950/20'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                  data-testid="tab-review-video"
                >
                  <Video className="w-4 h-4" />
                  Video Presentation Metrics
                </button>
              </div>

              {/* Tab Contents */}
              {activeTab === 'OVERVIEW' && (
                <div className="space-y-4">
                  {/* Current Decision Audit Details */}
                  <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800">
                    <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2 mb-3">
                      <Clock className="w-4 h-4 text-indigo-400" />
                      Human Decision Audit Trail
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                      <div>
                        <span className="text-slate-400">Current Status:</span>{' '}
                        <span className="text-slate-200 font-medium" data-testid="audit-current-decision">
                          {data.hr_decision_display}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400">Last Reviewed By:</span>{' '}
                        <span className="text-slate-200 font-medium" data-testid="audit-decided-by">
                          {data.hr_decided_by_name || data.hr_decided_by_email || 'Not yet reviewed'}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400">Timestamp:</span>{' '}
                        <span className="text-slate-200 font-medium">
                          {data.hr_decided_at ? new Date(data.hr_decided_at).toLocaleString() : '—'}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400">Applied Date:</span>{' '}
                        <span className="text-slate-200 font-medium">
                          {new Date(data.applied_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    {data.hr_decision_notes && (
                      <div className="mt-3 p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs text-slate-300">
                        <span className="font-semibold text-slate-400 block mb-1">Previous HR Notes:</span>
                        {data.hr_decision_notes}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {activeTab === 'CV_DETAILS' && (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-sm font-semibold text-slate-200">
                        Skills Match Analysis
                      </h3>
                      <span className="text-xs text-slate-400 font-mono">
                        {data.cv_summary.cv_filename || 'Uploaded CV'}
                      </span>
                    </div>

                    {/* Matched skills */}
                    <div className="mb-4">
                      <div className="text-xs text-emerald-400 font-medium mb-2 flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Matched Required Skills ({data.cv_summary.skills_matched.length})
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {data.cv_summary.skills_matched.length > 0 ? (
                          data.cv_summary.skills_matched.map((skill, idx) => (
                            <span
                              key={idx}
                              className="px-2.5 py-1 rounded-md text-xs bg-emerald-950/60 text-emerald-300 border border-emerald-600/40"
                              data-testid={`skill-matched-${idx}`}
                            >
                              ✓ {skill}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs text-slate-500 italic">No skills matched from room requirements.</span>
                        )}
                      </div>
                    </div>

                    {/* Missing skills */}
                    <div>
                      <div className="text-xs text-slate-400 font-medium mb-2 flex items-center gap-1.5">
                        <AlertCircle className="w-3.5 h-3.5 text-slate-500" />
                        Missing Required Skills ({data.cv_summary.skills_missing.length})
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {data.cv_summary.skills_missing.length > 0 ? (
                          data.cv_summary.skills_missing.map((skill, idx) => (
                            <span
                              key={idx}
                              className="px-2.5 py-1 rounded-md text-xs bg-slate-800/60 text-slate-400 border border-slate-700"
                              data-testid={`skill-missing-${idx}`}
                            >
                              ✕ {skill}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs text-emerald-400 italic">All room required skills matched!</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'VIDEO_DETAILS' && (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800">
                    <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
                      <Video className="w-4 h-4 text-cyan-400" />
                      Speech & Behavioral Signal Metrics
                    </h3>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                      <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                        <div className="text-xs text-slate-400">Speech Score</div>
                        <div className="text-lg font-bold text-cyan-300 mt-1">
                          {data.video_summary.speech_score !== null ? `${data.video_summary.speech_score.toFixed(0)}%` : '—'}
                        </div>
                      </div>
                      <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                        <div className="text-xs text-slate-400">Visual Presence</div>
                        <div className="text-lg font-bold text-cyan-300 mt-1">
                          {data.video_summary.visual_score !== null ? `${data.video_summary.visual_score.toFixed(0)}%` : '—'}
                        </div>
                      </div>
                      <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                        <div className="text-xs text-slate-400">Words Per Minute</div>
                        <div className="text-lg font-bold text-slate-200 mt-1">
                          {data.video_summary.wpm || '135'} WPM
                        </div>
                      </div>
                      <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                        <div className="text-xs text-slate-400">Filler Words</div>
                        <div className="text-lg font-bold text-slate-200 mt-1">
                          {data.video_summary.filler_words_count || 0}
                        </div>
                      </div>
                    </div>

                    {data.video_summary.summary && (
                      <div className="mt-4 p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-xs text-slate-300">
                        <span className="font-semibold text-slate-400 block mb-1">AI Executive Summary:</span>
                        {data.video_summary.summary}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Form: Record Human HR Decision (US-26 AC#3 & AC#4) */}
              <form onSubmit={handleSubmit} className="p-5 rounded-xl bg-slate-900 border border-indigo-600/30 space-y-4">
                <div>
                  <h3 className="text-base font-semibold text-white flex items-center gap-2">
                    <ThumbsUp className="w-4 h-4 text-indigo-400" />
                    Record Human HR Decision
                  </h3>
                  <p className="text-xs text-slate-400 mt-1">
                    Select an authoritative human hiring action. Overriding the AI shortlist recommendation requires an explicit justification note.
                  </p>
                </div>

                {/* Decision Buttons Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                  <button
                    type="button"
                    onClick={() => setSelectedDecision('CONFIRMED')}
                    className={`p-3 rounded-xl border text-xs font-semibold flex flex-col items-center gap-1.5 transition ${
                      selectedDecision === 'CONFIRMED'
                        ? 'bg-emerald-950 border-emerald-500 text-emerald-200 shadow-lg shadow-emerald-950/50'
                        : 'bg-slate-800/40 border-slate-700/80 text-slate-300 hover:bg-slate-800'
                    }`}
                    data-testid="btn-decision-confirm"
                  >
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    Confirm Shortlist
                  </button>

                  <button
                    type="button"
                    onClick={() => setSelectedDecision('OVERRIDDEN')}
                    className={`p-3 rounded-xl border text-xs font-semibold flex flex-col items-center gap-1.5 transition ${
                      selectedDecision === 'OVERRIDDEN'
                        ? 'bg-amber-950 border-amber-500 text-amber-200 shadow-lg shadow-amber-950/50'
                        : 'bg-slate-800/40 border-slate-700/80 text-slate-300 hover:bg-slate-800'
                    }`}
                    data-testid="btn-decision-override"
                  >
                    <ArrowRightLeft className="w-5 h-5 text-amber-400" />
                    Override AI
                  </button>

                  <button
                    type="button"
                    onClick={() => setSelectedDecision('REJECTED')}
                    className={`p-3 rounded-xl border text-xs font-semibold flex flex-col items-center gap-1.5 transition ${
                      selectedDecision === 'REJECTED'
                        ? 'bg-rose-950 border-rose-500 text-rose-200 shadow-lg shadow-rose-950/50'
                        : 'bg-slate-800/40 border-slate-700/80 text-slate-300 hover:bg-slate-800'
                    }`}
                    data-testid="btn-decision-reject"
                  >
                    <XCircle className="w-5 h-5 text-rose-400" />
                    Reject Candidate
                  </button>

                  <button
                    type="button"
                    onClick={() => setSelectedDecision('ON_HOLD')}
                    className={`p-3 rounded-xl border text-xs font-semibold flex flex-col items-center gap-1.5 transition ${
                      selectedDecision === 'ON_HOLD'
                        ? 'bg-blue-950 border-blue-500 text-blue-200 shadow-lg shadow-blue-950/50'
                        : 'bg-slate-800/40 border-slate-700/80 text-slate-300 hover:bg-slate-800'
                    }`}
                    data-testid="btn-decision-hold"
                  >
                    <Clock className="w-5 h-5 text-blue-400" />
                    Put On Hold
                  </button>
                </div>

                {/* Justification Notes Textarea */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <label htmlFor="hr-decision-notes" className="font-medium text-slate-300 flex items-center gap-1.5">
                      <MessageSquare className="w-3.5 h-3.5 text-indigo-400" />
                      Reviewer Feedback & Audit Notes
                      {isOverride && (
                        <span className="text-amber-400 font-semibold" data-testid="badge-override-required">
                          (Mandatory for Overrides)
                        </span>
                      )}
                    </label>
                    <span className="text-slate-500 text-[11px]">
                      {decisionNotes.length} characters
                    </span>
                  </div>
                  <textarea
                    id="hr-decision-notes"
                    rows={3}
                    value={decisionNotes}
                    onChange={(e) => setDecisionNotes(e.target.value)}
                    placeholder={
                      isOverride
                        ? 'Explain why you are overriding the automated AI recommendation (minimum 5 characters)...'
                        : 'Add optional notes for compliance or audit tracking...'
                    }
                    className={`w-full p-3 rounded-xl bg-slate-950 border text-slate-100 text-sm focus:outline-none focus:ring-2 transition ${
                      isOverride && decisionNotes.trim().length < 5
                        ? 'border-amber-600/70 focus:ring-amber-500/50'
                        : 'border-slate-800 focus:ring-indigo-500/50'
                    }`}
                    data-testid="input-decision-notes"
                  />
                  {isOverride && decisionNotes.trim().length < 5 && (
                    <p className="text-xs text-amber-400 flex items-center gap-1">
                      <AlertTriangle className="w-3.5 h-3.5" />
                      An explanatory note is strictly required when overriding AI recommendations.
                    </p>
                  )}
                </div>

                {/* Submit Action */}
                <div className="flex items-center justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={onClose}
                    className="px-4 py-2 rounded-xl text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting || (isOverride && decisionNotes.trim().length < 5)}
                    className="px-5 py-2 rounded-xl text-sm font-semibold bg-gradient-to-r from-indigo-500 to-cyan-500 text-white shadow-lg shadow-indigo-500/20 hover:from-indigo-600 hover:to-cyan-600 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    data-testid="btn-submit-decision"
                  >
                    {submitting ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        Saving Decision...
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4" />
                        Save Decision
                      </>
                    )}
                  </button>
                </div>
              </form>
            </>
          ) : (
            <div className="py-12 text-center text-slate-400">
              No applicant review data found.
            </div>
          )}

        </div>

      </div>
    </div>
  );
}
