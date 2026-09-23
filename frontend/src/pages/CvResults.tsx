import { useState, useEffect } from 'react';
import { useLocation } from 'wouter';
import {
  FileText,
  Sparkles,
  ArrowLeft,
  Download,
  RotateCw,
  CheckCircle2,
  AlertTriangle,
  Lightbulb,
  TrendingUp,
  Award,
  Layers,
  Search,
  BookOpen,
  Briefcase,
  Sliders,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import {
  PageHeading,
  Badge,
  DataAccessCard,
  type Notify,
} from '../components/dashboard/DashboardShared';
import {
  apiGetCurrentCV,
  apiGetCurrentCVFeedback,
  apiGenerateCVFeedback,
  type CandidateCV,
  type CVFeedback,
} from '../api/cv';

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
      textColor: 'text-[#277254]',
      bgColor: 'bg-[#e2f0e9]',
      borderColor: 'border-[#277254]/30',
      description: 'Your CV demonstrates high keyword density, measurable achievements, and clean ATS structure.',
    };
  }
  if (score >= 70) {
    return {
      label: 'Good potential',
      tone: 'warn',
      textColor: 'text-[#9a7922]',
      bgColor: 'bg-[#fff4ca]',
      borderColor: 'border-[#d8c98e]',
      description: 'Solid foundation with clear technical skills, but could benefit from more quantifiable impact metrics.',
    };
  }
  return {
    label: 'Needs revision',
    tone: 'bad',
    textColor: 'text-[#a33d35]',
    bgColor: 'bg-[#f7e5e1]',
    borderColor: 'border-[#b34a40]/30',
    description: 'Add essential sections, include specific action verbs, and quantify your achievements to pass ATS screening.',
  };
}

export function CvResults({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();

  const [currentCv, setCurrentCv] = useState<CandidateCV | null>(null);
  const [feedback, setFeedback] = useState<CVFeedback | null>(null);
  const [loading, setLoading] = useState(true);
  const [reanalyzing, setReanalyzing] = useState(false);

  const loadFeedbackData = async () => {
    try {
      setLoading(true);
      const [cv, fb] = await Promise.all([
        apiGetCurrentCV().catch(() => null),
        apiGetCurrentCVFeedback().catch(() => null),
      ]);
      setCurrentCv(cv);
      setFeedback(fb);
    } catch (err: any) {
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
    try {
      setReanalyzing(true);
      const updated = await apiGenerateCVFeedback(currentCv.id);
      setFeedback(updated);
      notify('CV analysis and score recalculated successfully.', 'success');
    } catch (err: any) {
      notify('Failed to recalculate CV feedback. Please try again.', 'error');
    } finally {
      setReanalyzing(false);
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
CAREERFLOW CV FEEDBACK & EVALUATION REPORT (US-08)
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
3. TOP THREE ACTIONABLE EDITS
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

  return (
    <AppShell role="student" notify={notify}>
      {/* Back button and breadcrumb */}
      <div className="mb-4 flex items-center justify-between">
        <button
          onClick={() => setLocation('/student/cv')}
          data-testid="button-back-to-cv"
          className="inline-flex items-center gap-2 text-xs font-bold text-[#526072] hover:text-[#253142] transition"
        >
          <ArrowLeft size={15} /> Back to CV Studio
        </button>

        <div className="flex items-center gap-2">
          <button
            onClick={handleReanalyze}
            disabled={reanalyzing || !currentCv}
            data-testid="button-reanalyze-cv"
            className="inline-flex items-center gap-1.5 rounded-xl border border-[#ccd0c6] bg-white px-3.5 py-2 text-xs font-bold text-[#253142] hover:bg-[#fffaf0] transition disabled:opacity-50"
          >
            <RotateCw size={13} className={reanalyzing ? 'animate-spin' : ''} />
            {reanalyzing ? 'Recalculating...' : 'Recalculate Score'}
          </button>

          {feedback && (
            <button
              onClick={handleDownloadReport}
              data-testid="button-download-report"
              className="inline-flex items-center gap-1.5 rounded-xl bg-[#253142] px-3.5 py-2 text-xs font-bold text-[#faf7ef] hover:bg-[#33435a] transition"
            >
              <Download size={13} /> Download Report
            </button>
          )}
        </div>
      </div>

      <PageHeading
        eyebrow="Candidate Studio • US-08 Evaluation"
        title="CV Feedback & Scoring"
        description="Comprehensive analysis of your CV document against professional recruiter rubrics, ATS readability standards, and keyword density."
      />

      {loading ? (
        <div className="py-20 text-center">
          <div className="mx-auto h-9 w-9 animate-spin rounded-full border-4 border-[#277254] border-t-transparent" />
          <p className="mt-4 text-sm font-semibold text-[#526072]">
            Analyzing CV document & calculating feedback signals...
          </p>
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
            <Sparkles size={15} /> Generate Score & Feedback
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Top Row: Score Hero Banner + CV Meta */}
          <div className="grid gap-6 lg:grid-cols-[1.1fr_.9fr]">
            {/* Score Hero Banner */}
            <section
              data-testid="card-overall-score"
              className="cf-card rounded-2xl bg-[#253142] p-6 text-[#faf7ef] shadow-sm flex flex-col justify-between relative overflow-hidden"
            >
              <div className="absolute -right-8 -top-8 h-36 w-36 rounded-full bg-[#f5c84b]/15 blur-2xl" />

              <div>
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold uppercase tracking-[.14em] text-[#aab5c0]">
                    Composite CV Score
                  </span>
                  <div
                    className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold ${tier?.bgColor} ${tier?.textColor}`}
                    data-testid="badge-alignment-tier"
                  >
                    <CheckCircle2 size={13} /> {tier?.label}
                  </div>
                </div>

                <div className="mt-6 flex items-end gap-6">
                  <div>
                    <div className="flex items-baseline gap-2">
                      <span
                        className="cf-display text-7xl font-bold leading-none text-[#f5c84b]"
                        data-testid="text-overall-score"
                      >
                        {feedback.overall_score}
                      </span>
                      <span className="text-xl font-semibold text-[#8fa0b5]">/ 100</span>
                    </div>
                    <p className="mt-3 text-xs leading-5 text-[#c4ccd3] max-w-md">
                      {tier?.description}
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-[#3d4d62] flex flex-wrap items-center justify-between gap-3 text-xs text-[#aab5c0]">
                <div className="flex items-center gap-2">
                  <FileText size={15} className="text-[#f5c84b]" />
                  <span className="font-semibold text-[#faf7ef] truncate max-w-[220px]">
                    {feedback.original_filename}
                  </span>
                </div>
                <span>Updated: {formatDate(feedback.updated_at)}</span>
              </div>
            </section>

            {/* Quick Summary / Status Card */}
            <section className="cf-card rounded-2xl bg-white p-6 border border-[#d9dbd1] shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#526072] pb-3 border-b border-[#eef0e7]">
                  <Award size={16} className="text-[#277254]" />
                  <span>Evaluation Summary & Key Signals</span>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-4">
                  <div className="rounded-xl border border-[#eef0e7] bg-[#fbfaf5] p-3.5">
                    <span className="text-[11px] font-semibold text-[#7b8490]">Keywords & Verbs</span>
                    <div className="mt-1 text-xl font-bold text-[#253142]">
                      {feedback.keyword_strength_score}%
                    </div>
                    <span className="text-[11px] text-[#277254] font-medium">
                      {feedback.extracted_skills?.length || 0} skills detected
                    </span>
                  </div>

                  <div className="rounded-xl border border-[#eef0e7] bg-[#fbfaf5] p-3.5">
                    <span className="text-[11px] font-semibold text-[#7b8490]">Clarity & Metrics</span>
                    <div className="mt-1 text-xl font-bold text-[#253142]">
                      {feedback.clarity_score}%
                    </div>
                    <span className="text-[11px] text-[#277254] font-medium">
                      {feedback.signal_breakdown?.clarity_impact?.metrics_count || 0} metrics found
                    </span>
                  </div>

                  <div className="rounded-xl border border-[#eef0e7] bg-[#fbfaf5] p-3.5">
                    <span className="text-[11px] font-semibold text-[#7b8490]">Structure & Layout</span>
                    <div className="mt-1 text-xl font-bold text-[#253142]">
                      {feedback.formatting_score}%
                    </div>
                    <span className="text-[11px] text-[#526072] font-medium">
                      {feedback.signal_breakdown?.formatting?.detected_sections?.length || 5}/5 sections
                    </span>
                  </div>

                  <div className="rounded-xl border border-[#eef0e7] bg-[#fbfaf5] p-3.5">
                    <span className="text-[11px] font-semibold text-[#7b8490]">Work & Education</span>
                    <div className="mt-1 text-xl font-bold text-[#253142]">
                      {Math.round((feedback.experience_score + feedback.education_score) / 2)}%
                    </div>
                    <span className="text-[11px] text-[#526072] font-medium">
                      Complete profiles
                    </span>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-[#eef0e7] flex items-center justify-between text-xs text-[#7b8490]">
                <span>Rubric weight: 20% Format • 30% Keywords • 30% Impact • 20% Fit</span>
              </div>
            </section>
          </div>

          {/* Three Useful Edits Callout Card */}
          <section
            data-testid="card-actionable-suggestions"
            className="cf-card rounded-2xl bg-white p-6 border border-[#d9dbd1] shadow-sm"
          >
            <div className="flex items-center justify-between pb-4 border-b border-[#eef0e7]">
              <div className="flex items-center gap-2.5">
                <div className="grid h-8 w-8 place-items-center rounded-xl bg-[#fff4ca] text-[#9a7922]">
                  <Lightbulb size={18} />
                </div>
                <div>
                  <h2 className="font-bold text-[#253142] text-base">Three Useful Edits</h2>
                  <p className="text-xs text-[#7b8490]">
                    Prioritized recommendations to boost your CV ATS score and recruiter impressions
                  </p>
                </div>
              </div>
              <Badge tone="good">Instant Boosts</Badge>
            </div>

            <div className="mt-5 grid gap-4 md:grid-cols-3" data-testid="container-suggestions">
              {feedback.suggestions?.map((suggestion, idx) => (
                <div
                  key={idx}
                  data-testid={`suggestion-item-${idx + 1}`}
                  className="relative rounded-2xl border border-[#e5e7dc] bg-[#fbfaf5] p-5 flex flex-col justify-between transition hover:border-[#253142] hover:shadow-sm"
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="grid h-7 w-7 place-items-center rounded-full bg-[#253142] text-xs font-bold text-[#faf7ef]">
                        {idx + 1}
                      </span>
                      <span className="text-[11px] font-bold uppercase tracking-wider text-[#9a7922]">
                        Recommendation
                      </span>
                    </div>
                    <p className="mt-3.5 text-xs font-semibold leading-relaxed text-[#253142]">
                      {suggestion}
                    </p>
                  </div>
                  <div className="mt-4 pt-3 border-t border-[#eef0e7] flex items-center gap-1.5 text-[11px] font-medium text-[#277254]">
                    <TrendingUp size={13} />
                    <span>Improves ATS match</span>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Signal Breakdown Section */}
          <section
            data-testid="card-signal-breakdown"
            className="cf-card rounded-2xl bg-white p-6 border border-[#d9dbd1] shadow-sm"
          >
            <div className="flex items-center gap-2 pb-4 border-b border-[#eef0e7]">
              <Sliders size={18} className="text-[#526072]" />
              <h2 className="font-bold text-[#253142] text-base">Signal Breakdown</h2>
              <span className="ml-auto text-xs text-[#7b8490]">Weighted Rubric Analysis</span>
            </div>

            <div className="mt-5 space-y-5">
              {/* 1. Keyword Strength */}
              <div className="space-y-1.5" data-testid="signal-keyword-strength">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-[#253142]">
                    Keyword Strength & Action Verbs{' '}
                    <span className="font-normal text-[#7b8490]">(Weight: 30%)</span>
                  </span>
                  <span className="font-bold text-[#253142]">{feedback.keyword_strength_score}%</span>
                </div>
                <div className="h-2.5 w-full overflow-hidden rounded-full bg-[#eef0e7]">
                  <div
                    className="h-full bg-[#277254] transition-all duration-300"
                    style={{ width: `${feedback.keyword_strength_score}%` }}
                  />
                </div>
                <div className="flex justify-between text-[11px] text-[#7b8490]">
                  <span>
                    Action verbs found:{' '}
                    {feedback.signal_breakdown?.keyword_strength?.action_verbs_found?.join(', ') ||
                      'Standard'}
                  </span>
                  <span>{feedback.extracted_skills?.length || 0} skills</span>
                </div>
              </div>

              {/* 2. Clarity & Impact */}
              <div className="space-y-1.5" data-testid="signal-clarity-impact">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-[#253142]">
                    Clarity & Measurable Impact{' '}
                    <span className="font-normal text-[#7b8490]">(Weight: 30%)</span>
                  </span>
                  <span className="font-bold text-[#253142]">{feedback.clarity_score}%</span>
                </div>
                <div className="h-2.5 w-full overflow-hidden rounded-full bg-[#eef0e7]">
                  <div
                    className="h-full bg-[#f5c84b] transition-all duration-300"
                    style={{ width: `${feedback.clarity_score}%` }}
                  />
                </div>
                <div className="flex justify-between text-[11px] text-[#7b8490]">
                  <span>
                    Quantifiable metrics detected:{' '}
                    {feedback.signal_breakdown?.clarity_impact?.metric_samples?.join(', ') || 'None'}
                  </span>
                  <span>{feedback.signal_breakdown?.clarity_impact?.metrics_count || 0} occurrences</span>
                </div>
              </div>

              {/* 3. Formatting & Section Completeness */}
              <div className="space-y-1.5" data-testid="signal-formatting">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-[#253142]">
                    Formatting & Section Completeness{' '}
                    <span className="font-normal text-[#7b8490]">(Weight: 20%)</span>
                  </span>
                  <span className="font-bold text-[#253142]">{feedback.formatting_score}%</span>
                </div>
                <div className="h-2.5 w-full overflow-hidden rounded-full bg-[#eef0e7]">
                  <div
                    className="h-full bg-[#394b5e] transition-all duration-300"
                    style={{ width: `${feedback.formatting_score}%` }}
                  />
                </div>
                <div className="flex justify-between text-[11px] text-[#7b8490]">
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
                  <span className="font-bold text-[#253142]">
                    Experience Depth & Roles{' '}
                    <span className="font-normal text-[#7b8490]">(Weight: 10%)</span>
                  </span>
                  <span className="font-bold text-[#253142]">{feedback.experience_score}%</span>
                </div>
                <div className="h-2.5 w-full overflow-hidden rounded-full bg-[#eef0e7]">
                  <div
                    className="h-full bg-[#277254] transition-all duration-300"
                    style={{ width: `${feedback.experience_score}%` }}
                  />
                </div>
                <div className="flex justify-between text-[11px] text-[#7b8490]">
                  <span>
                    Roles parsed: {feedback.signal_breakdown?.experience?.records_count || 0} records
                  </span>
                  <span>Work & Capstone history</span>
                </div>
              </div>

              {/* 5. Education Fit */}
              <div className="space-y-1.5" data-testid="signal-education">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-[#253142]">
                    Education Fit & Qualifications{' '}
                    <span className="font-normal text-[#7b8490]">(Weight: 10%)</span>
                  </span>
                  <span className="font-bold text-[#253142]">{feedback.education_score}%</span>
                </div>
                <div className="h-2.5 w-full overflow-hidden rounded-full bg-[#eef0e7]">
                  <div
                    className="h-full bg-[#277254] transition-all duration-300"
                    style={{ width: `${feedback.education_score}%` }}
                  />
                </div>
                <div className="flex justify-between text-[11px] text-[#7b8490]">
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
            <div className="flex items-center justify-between pb-4 border-b border-[#eef0e7]">
              <div className="flex items-center gap-2">
                <Search size={18} className="text-[#526072]" />
                <h2 className="font-bold text-[#253142] text-base">Extracted Skills Taxonomy</h2>
              </div>
              <span className="text-xs font-semibold text-[#7b8490]">
                {feedback.extracted_skills?.length || 0} recognized skills
              </span>
            </div>

            <div className="mt-4 flex flex-wrap gap-2" data-testid="container-skills-badges">
              {feedback.extracted_skills && feedback.extracted_skills.length > 0 ? (
                feedback.extracted_skills.map((skill, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center rounded-xl border border-[#d8d7cc] bg-[#fbfaf5] px-3 py-1.5 text-xs font-bold text-[#253142] shadow-2xs hover:border-[#253142] transition"
                  >
                    {skill}
                  </span>
                ))
              ) : (
                <p className="text-xs text-[#7b8490]">
                  No skills recognized from the current skills taxonomy. Try adding explicit keywords in your Skills section.
                </p>
              )}
            </div>
          </section>
        </div>
      )}

      <DataAccessCard />
    </AppShell>
  );
}
