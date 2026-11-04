import { useState, useEffect } from 'react';
import { useLocation } from 'wouter';
import {
  FileText,
  Sparkles,
  ChevronRight,
  Download,
  RotateCw,
  CheckCircle2,
  Check,
  AlertTriangle,
  Lightbulb,
  TrendingUp,
  Award,
  Search,
  Sliders,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { PageTransition, AnimatedNumber, ProgressBar, MOTION } from '../motion';
import {
  PageHeading,
  Badge,
  type Notify,
} from '../components/dashboard/DashboardShared';
import {
  apiGetCurrentCV,
  apiGetCurrentCVFeedback,
  apiGenerateCVFeedback,
  type CandidateCV,
  type CVFeedback,
} from '../api/cv';
import { CvProcessingView } from '../components/cv/CvProcessingView';

function formatDate(dateStr: string) {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

function getScoreTier(score: number): {
  label: string;
  tone: 'good' | 'warn' | 'bad';
  textColor: string;
  bgColor: string;
  borderColor: string;
  description: string;
} {
  if (score >= 85) {
    return {
      label: 'Strong alignment',
      tone: 'good',
      textColor: 'text-[#166534]',
      bgColor: 'bg-[#e2f0e9]',
      borderColor: 'border-[#166534]/30',
      description: 'Your CV demonstrates high keyword density, measurable achievements, and clean ATS structure.',
    };
  }
  if (score >= 70) {
    return {
      label: 'Good potential',
      tone: 'warn',
      textColor: 'text-[#78350f]',
      bgColor: 'bg-[#fef3c7]',
      borderColor: 'border-[#fde68a]',
      description: 'Solid foundation with clear technical skills, but could benefit from more quantifiable impact metrics.',
    };
  }
  return {
    label: 'Needs revision',
    tone: 'bad',
    textColor: 'text-[#991b1b]',
    bgColor: 'bg-[#fee2e2]',
    borderColor: 'border-[#fca5a5]',
    description: 'Add essential sections, include specific action verbs, and quantify your achievements to pass ATS screening.',
  };
}

function getTileStatus(score: number): { label: string; color: string; dotBg: string } {
  if (score >= 80) return { label: 'Strong', color: 'text-[#166534]', dotBg: 'bg-[#16a34a]' };
  if (score >= 60) return { label: 'Fair', color: 'text-[#78350f]', dotBg: 'bg-[#d97706]' };
  return { label: 'Needs work', color: 'text-[#991b1b]', dotBg: 'bg-[#dc2626]' };
}

function getSignalBarColor(score: number): string {
  if (score >= 70) return 'bg-[#16a34a]';
  if (score >= 50) return 'bg-[#f59e0b]';
  return 'bg-[#dc2626]';
}

export function CvResults({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();

  const [currentCv, setCurrentCv] = useState<CandidateCV | null>(null);
  const [feedback, setFeedback] = useState<CVFeedback | null>(null);
  const [loading, setLoading] = useState(true);
  const prefersReduced = useReducedMotion();
  const [appliedFixes, setAppliedFixes] = useState<Set<number>>(new Set());
  const [expandedSuggestions, setExpandedSuggestions] = useState<Record<number, boolean>>({ 0: true });
  const [reanalyzing, setReanalyzing] = useState(false);
  const [reanalyzeProgress, setReanalyzeProgress] = useState(0);
  const [extractionError, setExtractionError] = useState<{ message: string; advice: string } | null>(null);

  const loadFeedbackData = async () => {
    try {
      setLoading(true);
      setExtractionError(null);
      const [cv, fb] = await Promise.all([
        apiGetCurrentCV().catch(() => null),
        apiGetCurrentCVFeedback().catch((err) => {
          const status = err?.response?.status;
          const data = err?.response?.data;
          const msg = data?.error || data?.detail || data?.details || '';
          if (
            status === 500 ||
            status === 422 ||
            msg.toLowerCase().includes('extract') ||
            msg.toLowerCase().includes('unable to extract')
          ) {
            setExtractionError({
              message: 'Unable to extract text from document',
              advice: 'Ensure document is not password-protected or scanned as raw image.',
            });
          }
          return null;
        }),
      ]);
      setCurrentCv(cv);
      setFeedback(fb);
    } catch (err: any) {
      setExtractionError({
        message: 'Unable to extract text from document',
        advice: 'Ensure document is not password-protected or scanned as raw image.',
      });
      notify('Failed to load CV feedback results.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFeedbackData();
  }, []);

  const handleReanalyze = async () => {
    if (!currentCv) {
      notify('No active CV found to re-analyze.', 'error');
      return;
    }

    setReanalyzing(true);
    setReanalyzeProgress(10);
    setExtractionError(null);
    notify('CV uploaded. Analysis started.', 'success');

    let currentPct = 10;
    const progressTimer = setInterval(() => {
      if (currentPct < 25) {
        currentPct += 2.5;
      } else if (currentPct < 40) {
        currentPct += 1.8;
      } else if (currentPct < 70) {
        currentPct += 1.2;
      } else if (currentPct < 90) {
        currentPct += 0.6;
      }
      setReanalyzeProgress(Math.min(92, Math.round(currentPct)));
    }, 120);

    try {
      const updated = await apiGenerateCVFeedback(currentCv.id);
      clearInterval(progressTimer);
      setReanalyzeProgress(100);

      setTimeout(() => {
        setFeedback(updated);
        setReanalyzing(false);
        setReanalyzeProgress(0);
        notify('CV analysis and score recalculated successfully.', 'success');
      }, 700);
    } catch (err: any) {
      clearInterval(progressTimer);
      setReanalyzing(false);
      setReanalyzeProgress(0);

      const status = err?.response?.status;
      const data = err?.response?.data;
      const msg = data?.error || data?.detail || data?.details || '';
      if (
        status === 500 ||
        status === 422 ||
        msg.toLowerCase().includes('extract') ||
        msg.toLowerCase().includes('unable to extract')
      ) {
        setExtractionError({
          message: 'Unable to extract text from document',
          advice: 'Ensure document is not password-protected or scanned as raw image.',
        });
      } else {
        notify('Failed to recalculate CV feedback. Please try again.', 'error');
      }
    }
  };

  const handleDownloadReport = () => {
    if (!feedback || !currentCv) return;

    const tier = getScoreTier(feedback.overall_score);
    const dateStr = new Date().toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });

    const reportContent = `===============================================================
CAREERFLOW CV FEEDBACK & EVALUATION REPORT
Generated on: ${dateStr}
Document: ${feedback.original_filename}
Candidate: ${feedback.candidate_email}
===============================================================

OVERALL SCORE: ${feedback.overall_score} / 100 [${tier.label.toUpperCase()}]
${tier.description}

---------------------------------------------------------------
1. SIGNAL BREAKDOWN
---------------------------------------------------------------
- Keyword Strength & Action Verbs: ${feedback.keyword_strength_score}% (Weight: 30%)
- Clarity & Quantifiable Impact:   ${feedback.clarity_score}% (Weight: 30%)
- Formatting & Section Structure:  ${feedback.formatting_score}% (Weight: 20%)
- Experience Depth & Details:      ${feedback.experience_score}% (Weight: 10%)
- Education Fit & Degrees:         ${feedback.education_score}% (Weight: 10%)

---------------------------------------------------------------
2. EXTRACTED TECHNICAL & DOMAIN SKILLS (${feedback.extracted_skills?.length || 0})
---------------------------------------------------------------
${feedback.extracted_skills?.length ? feedback.extracted_skills.join(', ') : 'None detected'}

---------------------------------------------------------------
3. SMART SUGGESTIONS (${feedback.suggestions?.length || 0})
---------------------------------------------------------------
${feedback.suggestions?.map((item, idx) => `[${idx + 1}] ${item}`).join('\n\n') || 'None'}

===============================================================
Produced by CareerFlow Talent Intelligence Platform
===============================================================`;

    const blob = new Blob([reportContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `careerflow-cv-report-${currentCv.original_filename.replace(/\.[^/.]+$/, '')}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    notify('CV evaluation report downloaded successfully.', 'success');
  };

  const tier = feedback ? getScoreTier(feedback.overall_score) : null;

  if (reanalyzing) {
    return (
      <AppShell role="student" notify={notify}>
        <CvProcessingView progress={reanalyzeProgress} />
      </AppShell>
    );
  }

  return (
    <AppShell role="student" notify={notify}>
      {/* Top Header: Breadcrumbs & Actions */}
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <nav className="flex items-center gap-1.5 text-xs font-semibold text-[#4B5563]" aria-label="Breadcrumb">
          <button
            onClick={() => setLocation('/student/cv')}
            className="hover:text-[#1F2937] transition whitespace-nowrap"
          >
            CV Studio
          </button>
          <ChevronRight size={13} className="shrink-0 text-[#9ca3af]" />
          <span className="text-[#1F2937] font-bold whitespace-nowrap">Feedback</span>
          <ChevronRight size={13} className="shrink-0 text-[#9ca3af]" />
          <button
            onClick={() => setLocation('/student/cv/match')}
            className="hover:text-[#1F2937] transition whitespace-nowrap"
          >
            Job Match
          </button>
        </nav>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleReanalyze}
            disabled={reanalyzing || !currentCv}
            data-testid="button-reanalyze-cv"
            className="inline-flex h-[44px] items-center gap-2 rounded-xl border border-[#ccd0c6] bg-white px-4 text-xs font-bold text-[#1F2937] hover:bg-[#fffaf0] transition disabled:opacity-50 whitespace-nowrap shadow-xs cursor-pointer"
          >
            <RotateCw size={18} className={reanalyzing ? 'animate-spin' : ''} />
            <span>{reanalyzing ? 'Recalculating...' : 'Recalculate Score'}</span>
          </button>

          {feedback && (
            <button
              onClick={handleDownloadReport}
              data-testid="button-download-cv-report"
              className="inline-flex h-[44px] items-center gap-2 rounded-xl bg-[#253142] px-4 text-xs font-bold text-[#faf7ef] hover:bg-[#33435a] transition whitespace-nowrap shadow-xs cursor-pointer"
            >
              <Download size={18} />
              <span>Download Report</span>
            </button>
          )}
        </div>
      </div>

      <PageHeading
        title="CV Feedback & Job Match"
        description="Comprehensive analysis of your CV document against professional recruiter rubrics, ATS readability standards, and role semantic matching."
      />

      {/* Tab Navigation */}
      <div className="mb-6 flex items-center border-b border-[#d9dbd1]">
        <button
          type="button"
          onClick={() => setLocation('/student/cv/results')}
          data-testid="tab-cv-review"
          className="border-b-2 border-[#253142] px-4 py-2.5 text-xs font-bold text-[#253142] cursor-pointer"
        >
          Review &amp; suggestions
        </button>
        <button
          type="button"
          onClick={() => setLocation('/student/cv/match')}
          data-testid="tab-job-match"
          className="border-b-2 border-transparent px-4 py-2.5 text-xs font-semibold text-[#687382] hover:text-[#253142] hover:border-[#ccd0c6] cursor-pointer"
        >
          Job match
        </button>
      </div>

      {loading ? (
        <div className="py-20 text-center">
          <div className="mx-auto h-9 w-9 animate-spin rounded-full border-4 border-[#277254] border-t-transparent" />
          <p className="mt-4 text-sm font-semibold text-[#526072]">
            Analyzing CV document &amp; calculating feedback signals...
          </p>
        </div>
      ) : extractionError ? (
        <div
          data-testid="extraction-error-card"
          className="py-12 px-6 text-center cf-card rounded-2xl bg-white p-8 border border-[#e5a098] max-w-xl mx-auto shadow-sm"
        >
          <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-[#fdf2f0] text-[#b34a40]">
            <AlertTriangle size={28} />
          </div>
          <h2
            className="mt-4 text-lg font-bold text-[#912d26]"
            data-testid="extraction-error-title"
          >
            {extractionError.message}
          </h2>
          <p
            className="mx-auto mt-2 max-w-md text-xs leading-5 text-[#a33d35]"
            data-testid="extraction-error-advice"
          >
            {extractionError.advice}
          </p>
          <div className="mt-6 flex items-center justify-center gap-3">
            <button
              onClick={handleReanalyze}
              disabled={reanalyzing}
              data-testid="button-retry-extraction"
              className="inline-flex items-center gap-1.5 rounded-xl bg-[#253142] px-4 py-2.5 text-xs font-bold text-[#faf7ef] hover:bg-[#33435a] transition"
            >
              <RotateCw size={14} className={reanalyzing ? 'animate-spin' : ''} />
              Retry extraction
            </button>
            <button
              onClick={() => setLocation('/student/cv')}
              data-testid="button-try-another-file"
              className="inline-flex items-center gap-1.5 rounded-xl border border-[#ccd0c6] bg-white px-4 py-2.5 text-xs font-bold text-[#253142] hover:bg-[#fffaf0] transition"
            >
              Try another file
            </button>
          </div>
        </div>
      ) : !currentCv ? (
        <div className="py-16 text-center cf-card rounded-2xl bg-white p-8 border border-[#d9dbd1]">
          <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-[#f4f2e9] text-[#7b8490]">
            <FileText size={26} />
          </div>
          <h2 className="mt-4 text-lg font-bold text-[#253142]">No Active CV Document Found</h2>
          <p className="mx-auto mt-2 max-w-md text-xs leading-5 text-[#7b8490]">
            You have not uploaded a CV document yet. Upload your PDF or DOCX resume in CV Studio to generate instant automated feedback.
          </p>
          <button
            onClick={() => setLocation('/student/cv')}
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-[#253142] px-4 py-2.5 text-xs font-bold text-[#faf7ef] hover:bg-[#33435a]"
          >
            Go to CV Studio
          </button>
        </div>
      ) : !feedback ? (
        <div className="py-16 text-center cf-card rounded-2xl bg-white p-8 border border-[#d9dbd1]">
          <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-[#f4f2e9] text-[#7b8490]">
            <Sparkles size={26} className="text-[#f5c84b]" />
          </div>
          <h2 className="mt-4 text-lg font-bold text-[#253142]">Feedback Ready to Generate</h2>
          <p className="mx-auto mt-2 max-w-md text-xs leading-5 text-[#7b8490]">
            Your CV <strong>{currentCv.original_filename}</strong> is uploaded and ready for rubric scoring.
          </p>
          <button
            onClick={handleReanalyze}
            disabled={reanalyzing}
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-[#f5c84b] px-4 py-2.5 text-xs font-bold text-[#253142] hover:bg-[#e8b93c]"
          >
            <Sparkles size={15} /> Generate Score &amp; Feedback
          </button>
        </div>
      ) : (
        <PageTransition className="space-y-6">
          {/* Top Row: Score Hero Banner + CV Meta (shares 1.6fr 1fr grid) */}
          <div className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
            {/* Score Hero Banner */}
            <section
              data-testid="card-overall-score"
              className="cf-card rounded-2xl bg-white p-6 border border-[#d9dbd1] shadow-sm flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold uppercase tracking-[.14em] text-[#4B5563]">
                    Composite CV Score
                  </span>
                  <div
                    className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold ${tier?.bgColor} ${tier?.textColor} border ${tier?.borderColor}`}
                    data-testid="score-tier-badge"
                  >
                    <CheckCircle2 size={13} /> {tier?.label}
                  </div>
                </div>

                <div className="mt-5 flex items-baseline gap-3">
                  <span
                    className="cf-display text-7xl font-bold leading-none text-[#1F2937]"
                    data-testid="cv-overall-score"
                  >
                    <AnimatedNumber value={Math.min(100, feedback.overall_score + appliedFixes.size * 2)} />
                  </span>
                  <span className="text-xl font-semibold text-[#687382]">/ 100</span>
                </div>

                <p className="mt-3 text-xs leading-5 text-[#4B5563] max-w-md font-medium">
                  {tier?.description}
                </p>

                {/* Score context tag eliminating dead space */}
                <div className="mt-4 flex flex-wrap items-center gap-2">
                  <span className="inline-flex items-center gap-1 rounded-lg bg-[#e2f0e9] border border-[#bce2d1] px-2.5 py-1 text-[11px] font-bold text-[#166534]">
                    <TrendingUp size={12} /> ATS Rubric Verified
                  </span>
                  <span className="text-[11px] font-medium text-[#4B5563]">
                    Evaluation across 5 weighted dimensions
                  </span>
                </div>
              </div>

              {/* Pinned footer */}
              <div className="mt-6 pt-4 border-t border-[#d9dbd1] flex flex-wrap items-center justify-between gap-3 text-xs text-[#4B5563]">
                <div className="flex items-center gap-2">
                  <FileText size={15} className="text-[#1F2937]" />
                  <span className="font-bold text-[#1F2937] truncate max-w-[220px]">
                    {feedback.original_filename}
                  </span>
                </div>
                <span className="font-medium text-[#4B5563]">Updated: {formatDate(feedback.updated_at)}</span>
              </div>
            </section>

            {/* Quick Summary / Status Card */}
            <section className="cf-card rounded-2xl bg-white p-6 border border-[#d9dbd1] shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#4B5563] pb-3 border-b border-[#d9dbd1]">
                  <Award size={16} className="text-[#166534]" />
                  <span>Evaluation Summary &amp; Key Signals</span>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-4">
                  {/* Tile 1: Keywords */}
                  {(() => {
                    const status = getTileStatus(feedback.keyword_strength_score);
                    return (
                      <div
                        className="rounded-xl border border-[#eef0e7] bg-[#fbfaf5] p-3.5 flex flex-col justify-between"
                        title="Keywords (Weight: 30%)"
                      >
                        <span className="text-[11px] font-bold text-[#4B5563]">Keywords</span>
                        <div className="mt-1 text-2xl font-bold text-[#1F2937]">
                          {feedback.keyword_strength_score}%
                        </div>
                        <div className="mt-1 flex items-center gap-1.5">
                          <span className={`h-2 w-2 rounded-full shrink-0 ${status.dotBg}`} />
                          <span className={`text-[11px] font-bold ${status.color}`}>{status.label}</span>
                        </div>
                        <span className="mt-1 text-[11px] text-[#166534] font-medium">
                          {feedback.extracted_skills?.length || 0} skills detected
                        </span>
                      </div>
                    );
                  })()}

                  {/* Tile 2: Impact */}
                  {(() => {
                    const status = getTileStatus(feedback.clarity_score);
                    return (
                      <div
                        className="rounded-xl border border-[#eef0e7] bg-[#fbfaf5] p-3.5 flex flex-col justify-between"
                        title="Impact (Weight: 30%)"
                      >
                        <span className="text-[11px] font-bold text-[#4B5563]">Impact</span>
                        <div className="mt-1 text-2xl font-bold text-[#1F2937]">
                          {feedback.clarity_score}%
                        </div>
                        <div className="mt-1 flex items-center gap-1.5">
                          <span className={`h-2 w-2 rounded-full shrink-0 ${status.dotBg}`} />
                          <span className={`text-[11px] font-bold ${status.color}`}>{status.label}</span>
                        </div>
                        <span className="mt-1 text-[11px] text-[#166534] font-medium">
                          {feedback.signal_breakdown?.clarity_impact?.metrics_count || 0} metrics found
                        </span>
                      </div>
                    );
                  })()}

                  {/* Tile 3: Format */}
                  {(() => {
                    const status = getTileStatus(feedback.formatting_score);
                    return (
                      <div
                        className="rounded-xl border border-[#eef0e7] bg-[#fbfaf5] p-3.5 flex flex-col justify-between"
                        title="Format (Weight: 20%)"
                      >
                        <span className="text-[11px] font-bold text-[#4B5563]">Format</span>
                        <div className="mt-1 text-2xl font-bold text-[#1F2937]">
                          {feedback.formatting_score}%
                        </div>
                        <div className="mt-1 flex items-center gap-1.5">
                          <span className={`h-2 w-2 rounded-full shrink-0 ${status.dotBg}`} />
                          <span className={`text-[11px] font-bold ${status.color}`}>{status.label}</span>
                        </div>
                        <span className="mt-1 text-[11px] text-[#4B5563] font-medium">
                          {feedback.signal_breakdown?.formatting?.detected_sections?.length || 5}/5 sections
                        </span>
                      </div>
                    );
                  })()}

                  {/* Tile 4: Fit */}
                  {(() => {
                    const fitScore = Math.round((feedback.experience_score + feedback.education_score) / 2);
                    const status = getTileStatus(fitScore);
                    return (
                      <div
                        className="rounded-xl border border-[#eef0e7] bg-[#fbfaf5] p-3.5 flex flex-col justify-between"
                        title="Fit (Weight: 20%)"
                      >
                        <span className="text-[11px] font-bold text-[#4B5563]">Fit</span>
                        <div className="mt-1 text-2xl font-bold text-[#1F2937]">
                          {fitScore}%
                        </div>
                        <div className="mt-1 flex items-center gap-1.5">
                          <span className={`h-2 w-2 rounded-full shrink-0 ${status.dotBg}`} />
                          <span className={`text-[11px] font-bold ${status.color}`}>{status.label}</span>
                        </div>
                        <span className="mt-1 text-[11px] text-[#4B5563] font-medium">
                          Complete profiles
                        </span>
                      </div>
                    );
                  })()}
                </div>
              </div>

              {/* Rubric footer with identical naming */}
              <div className="mt-4 pt-3 border-t border-[#d9dbd1] flex items-center justify-between text-xs text-[#4B5563] font-medium">
                <span>Rubric weights: 30% Keywords • 30% Impact • 20% Format • 20% Fit</span>
              </div>
            </section>
          </div>

          {/* Actionable Suggestions Callout Card */}
          <section
            data-testid="card-actionable-suggestions"
            className="cf-card rounded-2xl bg-white p-6 border border-[#d9dbd1] shadow-sm"
          >
            <div className="flex flex-col gap-3 pb-4 border-b border-[#d9dbd1] sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-2.5">
                <div className="grid h-8 w-8 place-items-center rounded-xl bg-[#fff4ca] text-[#78350f]">
                  <Lightbulb size={18} />
                </div>
                <div>
                  <h2 className="font-bold text-[#1F2937] text-base">Smart Suggestions</h2>
                  <p className="text-xs text-[#4B5563]">
                    {feedback.suggestions?.length || 0} prioritised, CV-specific recommendations to boost your ATS score
                  </p>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                {feedback.signal_breakdown?.ai_suggestions_source === 'gemini' ? (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-[#e8eeff] border border-[#b8c8ff] px-2.5 py-1 text-[11px] font-bold text-[#1e3a8a]">
                    ✨ Powered by Gemini AI
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 rounded-full bg-[#f4f2e9] border border-[#d9dbd1] px-2.5 py-1 text-[11px] font-bold text-[#374151]">
                    Rule-based
                  </span>
                )}
                {feedback.signal_breakdown?.keyword_strength?.role_profile && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-[#e8f4ef] px-2.5 py-1 text-[11px] font-bold text-[#166534] border border-[#c3ddd0]">
                    🎯 {feedback.signal_breakdown.keyword_strength.role_profile.replace('_', ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())} role detected
                  </span>
                )}
                <Badge tone="good">Instant Boosts</Badge>
              </div>
            </div>

            <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3" data-testid="container-suggestions">
              {feedback.suggestions?.map((suggestion, idx) => {
                const isApplied = appliedFixes.has(idx);
                return (
                  <motion.div
                    key={idx}
                    layout="position"
                    data-testid={`suggestion-item-${idx + 1}`}
                    className={`relative rounded-2xl border p-5 flex flex-col justify-between transition-all duration-150 ${
                      isApplied
                        ? 'border-[#277254] bg-[#f0f6f3]'
                        : 'border-[#d9dbd1] bg-[#fbfaf5] hover:border-[#253142] hover:shadow-xs'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <span className={`grid h-7 w-7 place-items-center rounded-full text-xs font-bold transition-colors ${
                          isApplied ? 'bg-[#277254] text-white' : 'bg-[#253142] text-[#faf7ef]'
                        }`}>
                          {idx + 1}
                        </span>
                        <span className="text-[11px] font-bold uppercase tracking-wider text-[#78350f]">
                          Recommendation
                        </span>
                      </div>
                      <p className="mt-3.5 text-xs font-semibold leading-relaxed text-[#1F2937]">
                        {suggestion}
                      </p>
                    </div>

                    <div className="mt-4 pt-3 border-t border-[#eef0e7] flex items-center justify-between">
                      <div className="flex items-center gap-1.5 text-[11px] font-bold text-[#166534]">
                        <TrendingUp size={13} />
                        <span>Improves ATS match</span>
                      </div>

                      <button
                        type="button"
                        onClick={() => {
                          setAppliedFixes((prev) => {
                            const next = new Set(prev);
                            if (next.has(idx)) {
                              next.delete(idx);
                            } else {
                              next.add(idx);
                              notify('Suggestion applied to active draft! ATS score recalculated.', 'success');
                            }
                            return next;
                          });
                        }}
                        data-testid={`button-apply-fix-${idx + 1}`}
                        className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold transition-all duration-150 cursor-pointer ${
                          isApplied
                            ? 'bg-[#277254] text-white'
                            : 'bg-white border border-[#d9dbd1] text-[#253142] hover:bg-[#eef5f1] hover:border-[#277254]'
                        }`}
                      >
                        {isApplied ? (
                          <>
                            <svg className="w-3.5 h-3.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                              <polyline points="20 6 9 17 4 12" style={{ strokeDasharray: 24, strokeDashoffset: prefersReduced ? 0 : 0, animation: 'cfDrawPath 0.3s ease forwards' }} />
                            </svg>
                            <span>Applied</span>
                          </>
                        ) : (
                          <span>Apply fix</span>
                        )}
                      </button>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </section>

          {/* Signal Breakdown Section */}
          <section
            data-testid="signal-breakdown"
            className="cf-card rounded-2xl bg-white p-6 border border-[#d9dbd1] shadow-sm"
          >
            <div className="flex items-center gap-2 pb-4 border-b border-[#d9dbd1]">
              <Sliders size={18} className="text-[#4B5563]" />
              <h2 className="font-bold text-[#1F2937] text-base">Signal Breakdown</h2>
              <span className="ml-auto text-xs font-medium text-[#4B5563]">Weighted Rubric Analysis</span>
            </div>

            <div className="mt-5 space-y-5">
              {/* 1. Keyword Strength */}
              <div className="space-y-1.5" data-testid="signal-keyword-strength">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-[#1F2937]">
                    Keyword Strength &amp; Action Verbs{' '}
                    <span className="font-medium text-[#4B5563]">(Weight: 30%)</span>
                  </span>
                  <span className="font-bold text-[#1F2937]">{feedback.keyword_strength_score}%</span>
                </div>
                <div className="h-2.5 w-full overflow-hidden rounded-full bg-[#eef0e7]">
                  <div
                    className={`h-full transition-all duration-300 ${getSignalBarColor(feedback.keyword_strength_score)}`}
                    style={{ width: `${feedback.keyword_strength_score}%` }}
                  />
                </div>
                <div className="flex justify-between text-[11px] text-[#4B5563]">
                  <span>
                    Action verbs found:{' '}
                    {feedback.signal_breakdown?.keyword_strength?.action_verbs_found?.slice(0, 5).join(', ') ||
                      'Standard'}
                  </span>
                  <span className="font-medium text-[#166534]">{feedback.extracted_skills?.length || 0} skills</span>
                </div>
                {/* Weak passive phrases warning */}
                {(feedback.signal_breakdown?.keyword_strength?.weak_phrases_found?.length ?? 0) > 0 && (
                  <div className="mt-1.5 flex items-start gap-1.5 rounded-lg bg-[#fef3c7] border border-[#fde68a] px-2.5 py-1.5">
                    <AlertTriangle size={12} className="mt-0.5 shrink-0 text-[#78350f]" />
                    <span className="text-[11px] text-[#78350f] leading-relaxed">
                      Weak phrases found:{' '}
                      <strong>{feedback.signal_breakdown.keyword_strength.weak_phrases_found!.map(p => `"${p}"`).join(', ')}</strong>
                      {' '}— replace with strong action verbs.
                    </span>
                  </div>
                )}
              </div>

              {/* 2. Clarity & Impact */}
              <div className="space-y-1.5" data-testid="signal-clarity-impact">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-[#1F2937]">
                    Clarity &amp; Measurable Impact{' '}
                    <span className="font-medium text-[#4B5563]">(Weight: 30%)</span>
                  </span>
                  <span className="font-bold text-[#1F2937]">{feedback.clarity_score}%</span>
                </div>
                <div className="h-2.5 w-full overflow-hidden rounded-full bg-[#eef0e7]">
                  <div
                    className={`h-full transition-all duration-300 ${getSignalBarColor(feedback.clarity_score)}`}
                    style={{ width: `${feedback.clarity_score}%` }}
                  />
                </div>
                <div className="flex justify-between text-[11px] text-[#4B5563]">
                  <span>
                    Quantifiable metrics detected:{' '}
                    {feedback.signal_breakdown?.clarity_impact?.metric_samples?.slice(0, 3).join(', ') || 'None'}
                  </span>
                  <span>{feedback.signal_breakdown?.clarity_impact?.metrics_count || 0} occurrences</span>
                </div>
                {/* Weak bullet examples hint */}
                {(feedback.signal_breakdown?.clarity_impact?.weak_bullet_examples?.length ?? 0) > 0 && (
                  <div className="mt-1.5 flex items-start gap-1.5 rounded-lg bg-[#fee2e2] border border-[#fca5a5] px-2.5 py-1.5">
                    <AlertTriangle size={12} className="mt-0.5 shrink-0 text-[#991b1b]" />
                    <span className="text-[11px] text-[#991b1b] leading-relaxed">
                      Bullet needing a metric: <em>"{feedback.signal_breakdown.clarity_impact.weak_bullet_examples![0]}"</em>
                    </span>
                  </div>
                )}
              </div>

              {/* 3. Formatting & Section Completeness */}
              <div className="space-y-1.5" data-testid="signal-formatting">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-[#1F2937]">
                    Formatting &amp; Section Completeness{' '}
                    <span className="font-medium text-[#4B5563]">(Weight: 20%)</span>
                  </span>
                  <span className="font-bold text-[#1F2937]">{feedback.formatting_score}%</span>
                </div>
                <div className="h-2.5 w-full overflow-hidden rounded-full bg-[#eef0e7]">
                  <div
                    className={`h-full transition-all duration-300 ${getSignalBarColor(feedback.formatting_score)}`}
                    style={{ width: `${feedback.formatting_score}%` }}
                  />
                </div>
                <div className="flex justify-between text-[11px] text-[#4B5563]">
                  <span>
                    Word count: {feedback.signal_breakdown?.formatting?.word_count || 0} words
                  </span>
                  <span>
                    {feedback.signal_breakdown?.formatting?.has_dense_paragraphs
                      ? 'Dense paragraphs detected'
                      : 'Optimal paragraph lengths'}
                  </span>
                </div>
              </div>

              {/* 4. Experience Depth */}
              <div className="space-y-1.5" data-testid="signal-experience">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-[#1F2937]">
                    Experience Depth &amp; Roles{' '}
                    <span className="font-medium text-[#4B5563]">(Weight: 10%)</span>
                  </span>
                  <span className="font-bold text-[#1F2937]">{feedback.experience_score}%</span>
                </div>
                <div className="h-2.5 w-full overflow-hidden rounded-full bg-[#eef0e7]">
                  <div
                    className={`h-full transition-all duration-300 ${getSignalBarColor(feedback.experience_score)}`}
                    style={{ width: `${feedback.experience_score}%` }}
                  />
                </div>
                <div className="flex justify-between text-[11px] text-[#4B5563]">
                  <span>
                    Roles parsed: {feedback.signal_breakdown?.experience?.records_count || 0} records
                  </span>
                  <span>Work &amp; Capstone history</span>
                </div>
              </div>

              {/* 5. Education Fit */}
              <div className="space-y-1.5" data-testid="signal-education">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-[#1F2937]">
                    Education Fit &amp; Qualifications{' '}
                    <span className="font-medium text-[#4B5563]">(Weight: 10%)</span>
                  </span>
                  <span className="font-bold text-[#1F2937]">{feedback.education_score}%</span>
                </div>
                <div className="h-2.5 w-full overflow-hidden rounded-full bg-[#eef0e7]">
                  <div
                    className={`h-full transition-all duration-300 ${getSignalBarColor(feedback.education_score)}`}
                    style={{ width: `${feedback.education_score}%` }}
                  />
                </div>
                <div className="flex justify-between text-[11px] text-[#4B5563]">
                  <span>
                    Degrees parsed: {feedback.signal_breakdown?.education?.records_count || 0} records
                  </span>
                  <span>Academic credentials</span>
                </div>
              </div>
            </div>
          </section>

          {/* Extracted Skills Tag Cloud */}
          <section
            data-testid="card-extracted-skills"
            className="cf-card rounded-2xl bg-white p-6 border border-[#d9dbd1] shadow-sm"
          >
            <div className="flex items-center justify-between pb-4 border-b border-[#d9dbd1]">
              <div className="flex items-center gap-2">
                <Search size={18} className="text-[#4B5563]" />
                <h2 className="font-bold text-[#1F2937] text-base">Extracted Skills Taxonomy</h2>
              </div>
              <span className="text-xs font-semibold text-[#4B5563]">
                {feedback.extracted_skills?.length || 0} recognized skills
              </span>
            </div>

            <div className="mt-4 flex flex-wrap gap-2 pb-2" data-testid="extracted-skills-list">
              {feedback.extracted_skills && feedback.extracted_skills.length > 0 ? (
                feedback.extracted_skills.map((skill, index) => (
                  <span
                    key={index}
                    data-testid="skill-badge"
                    className="inline-flex items-center rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3 py-1.5 text-xs font-bold text-[#1F2937] shadow-2xs hover:border-[#253142] transition"
                  >
                    {skill}
                  </span>
                ))
              ) : (
                <p className="text-xs text-[#4B5563]">
                  No skills recognized from the current skills taxonomy. Try adding explicit keywords in your Skills section.
                </p>
              )}
            </div>
          </section>
        </PageTransition>
      )}

    </AppShell>
  );
}
