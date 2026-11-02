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
  Layers,
  Send,
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
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#e2f0e9] text-[#1f5b43] border border-[#a7d7c1]">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#277254]" />
            Shortlist Confirmed
          </span>
        );
      case 'OVERRIDDEN':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#fef3c7] text-[#92400e] border border-[#fde68a]">
            <ArrowRightLeft className="w-3.5 h-3.5 text-[#d97706]" />
            AI Overridden
          </span>
        );
      case 'REJECTED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#fde8e8] text-[#9b1c1c] border border-[#f8b4b4]">
            <XCircle className="w-3.5 h-3.5 text-[#e02424]" />
            Rejected
          </span>
        );
      case 'ON_HOLD':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#e1effe] text-[#1e429f] border border-[#b4c6fc]">
            <Clock className="w-3.5 h-3.5 text-[#1c64f2]" />
            On Hold
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#f1f3f5] text-[#687382] border border-[#d9dbd1]">
            <Clock className="w-3.5 h-3.5 text-[#7b8490]" />
            Pending HR Review
          </span>
        );
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      data-testid="modal-candidate-review"
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-[#253142]/60 backdrop-blur-xs overflow-y-auto animate-in fade-in"
    >
      <div className="relative w-full max-w-4xl max-h-[92vh] flex flex-col rounded-2xl bg-white border border-[#d9dbd1] shadow-2xl text-[#253142] overflow-hidden">
        
        {/* Top Header */}
        <div className="flex items-start justify-between p-6 border-b border-[#eef0e7] bg-[#fbfaf5]">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-[#e2f0e9] border border-[#a7d7c1] flex items-center justify-center text-[#277254] shadow-xs">
              <User className="w-6 h-6 text-[#277254]" />
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h2 className="text-xl font-bold tracking-tight text-[#253142]" data-testid="heading-candidate-name">
                  {loading ? 'Loading applicant...' : data?.candidate_name || 'Candidate Review'}
                </h2>
                {data && getDecisionBadge(data.hr_decision)}
              </div>
              <p className="text-sm text-[#7b8490] mt-0.5">
                {data?.candidate_email} • Room: <span className="text-[#253142] font-semibold">{data?.room_title}</span>
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleDownloadPdf}
              disabled={downloadingPdf || !applicationId}
              data-testid="button-download-candidate-pdf"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-white text-[#253142] border border-[#d9dbd1] hover:bg-[#fbfaf5] transition disabled:opacity-50 cursor-pointer shadow-xs"
              title="Download evaluation report as PDF"
            >
              {downloadingPdf ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin text-[#277254]" />
              ) : (
                <Download className="w-3.5 h-3.5 text-[#277254]" />
              )}
              <span>{downloadingPdf ? 'Exporting PDF...' : 'Download PDF Report'}</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-xl text-[#7b8490] hover:bg-[#eef0e7] hover:text-[#253142] transition cursor-pointer"
              data-testid="button-close-review-modal"
              aria-label="Close modal"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5 bg-[#faf9f5]">

          {/* US-26 AC#5: Prominent AI Advisory Disclaimer */}
          <div
            className="flex items-start gap-3.5 p-4 rounded-xl bg-[#fef3c7] border border-[#fde68a] text-[#92400e]"
            data-testid="banner-ai-advisory-disclaimer"
          >
            <ShieldAlert className="w-5 h-5 text-[#d97706] shrink-0 mt-0.5" />
            <div className="text-xs sm:text-sm leading-relaxed">
              <strong className="font-bold text-[#78350f]">AI Advisory Disclaimer:</strong>{' '}
              {data?.ai_disclaimer ||
                'AI-generated scores and shortlisting recommendations are advisory tools designed to support, not replace, human hiring decisions.'}
            </div>
          </div>

          {/* Feedback alerts */}
          {errorMsg && (
            <div
              className="flex items-center gap-2 p-3.5 rounded-xl bg-[#fde8e8] border border-[#f8b4b4] text-[#9b1c1c] text-sm"
              data-testid="alert-decision-error"
            >
              <AlertCircle className="w-4 h-4 text-[#e02424] shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {successMsg && (
            <div
              className="flex items-center gap-2 p-3.5 rounded-xl bg-[#e2f0e9] border border-[#a7d7c1] text-[#1f5b43] text-sm"
              data-testid="alert-decision-success"
            >
              <CheckCircle2 className="w-4 h-4 text-[#277254] shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {loading ? (
            <div className="py-16 text-center text-[#7b8490]">
              <div className="inline-block w-8 h-8 border-4 border-[#277254] border-t-transparent rounded-full animate-spin mb-3"></div>
              <p>Gathering candidate score telemetry and AI signals...</p>
            </div>
          ) : data ? (
            <>
              {/* Score & AI Recommendation Dashboard Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
                
                {/* Composite Final Score */}
                <div className="p-4 rounded-2xl bg-white border border-[#d9dbd1] shadow-2xs flex flex-col justify-between">
                  <div className="flex items-center justify-between text-xs font-bold text-[#7b8490] uppercase tracking-wider">
                    <span>Composite Final Score</span>
                    <Award className="w-4 h-4 text-[#d97706]" />
                  </div>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-3xl font-extrabold text-[#253142]" data-testid="text-final-score">
                      {data.final_score !== null ? data.final_score.toFixed(1) : '—'}
                    </span>
                    <span className="text-xs text-[#7b8490]">/ 100</span>
                  </div>
                  <div className="mt-3 text-xs text-[#7b8490] flex items-center justify-between pt-2 border-t border-[#eef0e7]">
                    <span>Weights:</span>
                    <span className="font-semibold text-[#253142]">CV {data.cv_weight}% • Video {data.video_weight}%</span>
                  </div>
                </div>

                {/* Sub-Scores */}
                <div className="p-4 rounded-2xl bg-white border border-[#d9dbd1] shadow-2xs flex flex-col justify-between">
                  <div className="flex items-center justify-between text-xs font-bold text-[#7b8490] uppercase tracking-wider">
                    <span>Component Scores</span>
                    <Layers className="w-4 h-4 text-[#277254]" />
                  </div>
                  <div className="grid grid-cols-2 gap-3 mt-2">
                    <div>
                      <div className="text-xs text-[#7b8490]">CV Score</div>
                      <div className="text-xl font-bold text-[#253142]" data-testid="text-cv-score">
                        {data.cv_score !== null ? data.cv_score.toFixed(1) : '—'}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-[#7b8490]">Video Score</div>
                      <div className="text-xl font-bold text-[#253142]" data-testid="text-video-score">
                        {data.video_score !== null ? data.video_score.toFixed(1) : '—'}
                      </div>
                    </div>
                  </div>
                  <div className="mt-3 text-xs text-[#7b8490] pt-2 border-t border-[#eef0e7]">
                    {data.is_partial_score ? (
                      <span className="text-[#d97706] font-medium">⚠️ Calculated with partial score</span>
                    ) : (
                      <span className="text-[#277254] font-medium">✓ Complete evaluation</span>
                    )}
                  </div>
                </div>

                {/* AI Recommendation (Advisory) */}
                <div className="p-4 rounded-2xl bg-white border border-[#d9dbd1] shadow-2xs flex flex-col justify-between">
                  <div className="flex items-center justify-between text-xs font-bold text-[#7b8490] uppercase tracking-wider">
                    <span>AI Advisory Suggestion</span>
                    <Sparkles className="w-4 h-4 text-[#277254]" />
                  </div>
                  <div className="mt-2">
                    <span
                      className={`inline-block px-2.5 py-1 rounded-lg text-xs font-bold ${
                        data.is_shortlisted
                          ? 'bg-[#e2f0e9] text-[#1f5b43] border border-[#a7d7c1]'
                          : 'bg-[#f1f3f5] text-[#687382] border border-[#d9dbd1]'
                      }`}
                      data-testid="badge-ai-recommendation"
                    >
                      {data.ai_recommendation_label}
                    </span>
                  </div>
                  <p
                    className="mt-2 text-xs text-[#7b8490] line-clamp-2"
                    data-testid="text-ai-recommendation-reason"
                  >
                    {data.shortlist_reason || 'Criteria evaluation applied automatically.'}
                  </p>
                </div>
              </div>

              {/* Navigation Tabs */}
              <div className="flex border-b border-[#eef0e7] bg-white px-2 rounded-xl border border-[#d9dbd1]">
                <button
                  type="button"
                  onClick={() => setActiveTab('OVERVIEW')}
                  className={`px-4 py-2.5 text-xs font-bold border-b-2 transition -mb-px flex items-center gap-2 cursor-pointer ${
                    activeTab === 'OVERVIEW'
                      ? 'border-[#277254] text-[#277254] bg-[#e2f0e9]/40'
                      : 'border-transparent text-[#687382] hover:text-[#253142]'
                  }`}
                  data-testid="tab-review-overview"
                >
                  <FileText className="w-4 h-4" />
                  Signal Overview
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('CV_DETAILS')}
                  className={`px-4 py-2.5 text-xs font-bold border-b-2 transition -mb-px flex items-center gap-2 cursor-pointer ${
                    activeTab === 'CV_DETAILS'
                      ? 'border-[#277254] text-[#277254] bg-[#e2f0e9]/40'
                      : 'border-transparent text-[#687382] hover:text-[#253142]'
                  }`}
                  data-testid="tab-review-cv"
                >
                  <Award className="w-4 h-4" />
                  CV Skills Match ({data.cv_summary.skills_matched.length})
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('VIDEO_DETAILS')}
                  className={`px-4 py-2.5 text-xs font-bold border-b-2 transition -mb-px flex items-center gap-2 cursor-pointer ${
                    activeTab === 'VIDEO_DETAILS'
                      ? 'border-[#277254] text-[#277254] bg-[#e2f0e9]/40'
                      : 'border-transparent text-[#687382] hover:text-[#253142]'
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
                  <div className="p-4 rounded-2xl bg-white border border-[#d9dbd1] shadow-2xs">
                    <h3 className="text-sm font-bold text-[#253142] flex items-center gap-2 mb-3">
                      <Clock className="w-4 h-4 text-[#277254]" />
                      Human Decision Audit Trail
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                      <div>
                        <span className="text-[#7b8490]">Current Status:</span>{' '}
                        <span className="text-[#253142] font-bold" data-testid="audit-current-decision">
                          {data.hr_decision_display}
                        </span>
                      </div>
                      <div>
                        <span className="text-[#7b8490]">Last Reviewed By:</span>{' '}
                        <span className="text-[#253142] font-bold" data-testid="audit-decided-by">
                          {data.hr_decided_by_name || data.hr_decided_by_email || 'Not yet reviewed'}
                        </span>
                      </div>
                      <div>
                        <span className="text-[#7b8490]">Timestamp:</span>{' '}
                        <span className="text-[#253142] font-semibold">
                          {data.hr_decided_at ? new Date(data.hr_decided_at).toLocaleString() : '—'}
                        </span>
                      </div>
                      <div>
                        <span className="text-[#7b8490]">Applied Date:</span>{' '}
                        <span className="text-[#253142] font-semibold">
                          {new Date(data.applied_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    {data.hr_decision_notes && (
                      <div className="mt-3 p-3 rounded-xl bg-[#fbfaf5] border border-[#eef0e7] text-xs text-[#526072]">
                        <span className="font-bold text-[#253142] block mb-1">Previous HR Notes:</span>
                        {data.hr_decision_notes}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {activeTab === 'CV_DETAILS' && (
                <div className="space-y-4">
                  <div className="p-4 rounded-2xl bg-white border border-[#d9dbd1] shadow-2xs">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-sm font-bold text-[#253142]">
                        Skills Match Analysis
                      </h3>
                      <span className="text-xs text-[#7b8490] font-mono">
                        {data.cv_summary.cv_filename || 'Uploaded CV'}
                      </span>
                    </div>

                    {/* Matched skills */}
                    <div className="mb-4">
                      <div className="text-xs text-[#1f5b43] font-bold mb-2 flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-[#277254]" />
                        Matched Required Skills ({data.cv_summary.skills_matched.length})
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {data.cv_summary.skills_matched.length > 0 ? (
                          data.cv_summary.skills_matched.map((skill, idx) => (
                            <span
                              key={idx}
                              className="px-2.5 py-1 rounded-lg text-xs font-medium bg-[#e2f0e9] text-[#1f5b43] border border-[#a7d7c1]"
                              data-testid={`skill-matched-${idx}`}
                            >
                              ✓ {skill}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs text-[#7b8490] italic">No skills matched from room requirements.</span>
                        )}
                      </div>
                    </div>

                    {/* Missing skills */}
                    <div>
                      <div className="text-xs text-[#7b8490] font-bold mb-2 flex items-center gap-1.5">
                        <AlertCircle className="w-3.5 h-3.5 text-[#7b8490]" />
                        Missing Required Skills ({data.cv_summary.skills_missing.length})
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {data.cv_summary.skills_missing.length > 0 ? (
                          data.cv_summary.skills_missing.map((skill, idx) => (
                            <span
                              key={idx}
                              className="px-2.5 py-1 rounded-lg text-xs font-medium bg-[#f1f3f5] text-[#687382] border border-[#d9dbd1]"
                              data-testid={`skill-missing-${idx}`}
                            >
                              ✕ {skill}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs text-[#277254] italic font-semibold">All room required skills matched!</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'VIDEO_DETAILS' && (
                <div className="space-y-4">
                  <div className="p-4 rounded-2xl bg-white border border-[#d9dbd1] shadow-2xs">
                    <h3 className="text-sm font-bold text-[#253142] mb-3 flex items-center gap-2">
                      <Video className="w-4 h-4 text-[#277254]" />
                      Speech & Behavioral Signal Metrics
                    </h3>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                      <div className="p-3 rounded-xl bg-[#fbfaf5] border border-[#d9dbd1]">
                        <div className="text-xs text-[#7b8490]">Speech Score</div>
                        <div className="text-lg font-bold text-[#277254] mt-1">
                          {data.video_summary.speech_score !== null ? `${data.video_summary.speech_score.toFixed(0)}%` : '—'}
                        </div>
                      </div>
                      <div className="p-3 rounded-xl bg-[#fbfaf5] border border-[#d9dbd1]">
                        <div className="text-xs text-[#7b8490]">Visual Presence</div>
                        <div className="text-lg font-bold text-[#277254] mt-1">
                          {data.video_summary.visual_score !== null ? `${data.video_summary.visual_score.toFixed(0)}%` : '—'}
                        </div>
                      </div>
                      <div className="p-3 rounded-xl bg-[#fbfaf5] border border-[#d9dbd1]">
                        <div className="text-xs text-[#7b8490]">Words Per Minute</div>
                        <div className="text-lg font-bold text-[#253142] mt-1">
                          {data.video_summary.wpm || '135'} WPM
                        </div>
                      </div>
                      <div className="p-3 rounded-xl bg-[#fbfaf5] border border-[#d9dbd1]">
                        <div className="text-xs text-[#7b8490]">Filler Words</div>
                        <div className="text-lg font-bold text-[#253142] mt-1">
                          {data.video_summary.filler_words_count || 0}
                        </div>
                      </div>
                    </div>

                    {data.video_summary.summary && (
                      <div className="mt-4 p-3.5 rounded-xl bg-[#fbfaf5] border border-[#eef0e7] text-xs text-[#526072]">
                        <span className="font-bold text-[#253142] block mb-1">AI Executive Summary:</span>
                        {data.video_summary.summary}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Form: Record Human HR Decision (US-26 AC#3 & AC#4) */}
              <form onSubmit={handleSubmit} className="p-5 rounded-2xl bg-white border border-[#d9dbd1] shadow-2xs space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-[#253142] flex items-center gap-2">
                    <ThumbsUp className="w-4 h-4 text-[#277254]" />
                    Record Human HR Decision
                  </h3>
                  <p className="text-xs text-[#7b8490] mt-1">
                    Select an authoritative human hiring action. Overriding the AI shortlist recommendation requires an explicit justification note.
                  </p>
                </div>

                {/* Decision Buttons Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                  <button
                    type="button"
                    onClick={() => setSelectedDecision('CONFIRMED')}
                    className={`p-3 rounded-xl border text-xs font-bold flex flex-col items-center gap-1.5 transition cursor-pointer ${
                      selectedDecision === 'CONFIRMED'
                        ? 'bg-[#e2f0e9] border-[#277254] text-[#1f5b43] shadow-xs ring-2 ring-[#277254]/30'
                        : 'bg-[#fbfaf5] border-[#d9dbd1] text-[#526072] hover:bg-[#eef0e7]'
                    }`}
                    data-testid="btn-decision-confirm"
                  >
                    <CheckCircle2 className="w-5 h-5 text-[#277254]" />
                    Confirm Shortlist
                  </button>

                  <button
                    type="button"
                    onClick={() => setSelectedDecision('OVERRIDDEN')}
                    className={`p-3 rounded-xl border text-xs font-bold flex flex-col items-center gap-1.5 transition cursor-pointer ${
                      selectedDecision === 'OVERRIDDEN'
                        ? 'bg-[#fef3c7] border-[#d97706] text-[#92400e] shadow-xs ring-2 ring-[#d97706]/30'
                        : 'bg-[#fbfaf5] border-[#d9dbd1] text-[#526072] hover:bg-[#eef0e7]'
                    }`}
                    data-testid="btn-decision-override"
                  >
                    <ArrowRightLeft className="w-5 h-5 text-[#d97706]" />
                    Override AI
                  </button>

                  <button
                    type="button"
                    onClick={() => setSelectedDecision('REJECTED')}
                    className={`p-3 rounded-xl border text-xs font-bold flex flex-col items-center gap-1.5 transition cursor-pointer ${
                      selectedDecision === 'REJECTED'
                        ? 'bg-[#fde8e8] border-[#e02424] text-[#9b1c1c] shadow-xs ring-2 ring-[#e02424]/30'
                        : 'bg-[#fbfaf5] border-[#d9dbd1] text-[#526072] hover:bg-[#eef0e7]'
                    }`}
                    data-testid="btn-decision-reject"
                  >
                    <XCircle className="w-5 h-5 text-[#e02424]" />
                    Reject Candidate
                  </button>

                  <button
                    type="button"
                    onClick={() => setSelectedDecision('ON_HOLD')}
                    className={`p-3 rounded-xl border text-xs font-bold flex flex-col items-center gap-1.5 transition cursor-pointer ${
                      selectedDecision === 'ON_HOLD'
                        ? 'bg-[#e1effe] border-[#1c64f2] text-[#1e429f] shadow-xs ring-2 ring-[#1c64f2]/30'
                        : 'bg-[#fbfaf5] border-[#d9dbd1] text-[#526072] hover:bg-[#eef0e7]'
                    }`}
                    data-testid="btn-decision-hold"
                  >
                    <Clock className="w-5 h-5 text-[#1c64f2]" />
                    Put On Hold
                  </button>
                </div>

                {/* Justification Notes Textarea */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <label htmlFor="hr-decision-notes" className="font-bold text-[#253142] flex items-center gap-1.5">
                      <MessageSquare className="w-3.5 h-3.5 text-[#277254]" />
                      Reviewer Feedback & Audit Notes
                      {isOverride && (
                        <span className="text-[#d97706] font-bold" data-testid="badge-override-required">
                          (Mandatory for Overrides)
                        </span>
                      )}
                    </label>
                    <span className="text-[#7b8490] text-[11px]">
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
                    className={`w-full p-3 rounded-xl bg-[#fbfaf5] border text-[#253142] text-xs focus:bg-white focus:outline-none focus:ring-2 transition placeholder:text-[#9aabb5] ${
                      isOverride && decisionNotes.trim().length < 5
                        ? 'border-[#e02424] focus:ring-[#e02424]/30'
                        : 'border-[#d9dbd1] focus:ring-[#277254]/30'
                    }`}
                    data-testid="input-decision-notes"
                  />
                  {isOverride && decisionNotes.trim().length < 5 && (
                    <p className="text-xs text-[#d97706] flex items-center gap-1">
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
                    className="px-4 py-2 rounded-xl text-xs font-bold text-[#526072] hover:bg-[#eef0e7] transition cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting || (isOverride && decisionNotes.trim().length < 5)}
                    className="px-5 py-2.5 rounded-xl text-xs font-bold bg-[#277254] text-white hover:bg-[#1f5b43] shadow-xs transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 cursor-pointer"
                    data-testid="btn-submit-decision"
                  >
                    {submitting ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-white" />
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
            <div className="py-12 text-center text-[#7b8490]">
              No applicant review data found.
            </div>
          )}

        </div>

      </div>
    </div>
  );
}
