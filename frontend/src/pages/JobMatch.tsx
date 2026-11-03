import { useState, useEffect } from 'react';
import { useLocation } from 'wouter';
import {
  FileText,
  Sparkles,
  ChevronRight,
  Check,
  X,
  SlidersHorizontal,
  Briefcase,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Info,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import { PageHeading, Badge, type Notify } from '../components/dashboard/DashboardShared';
import {
  apiGetCurrentCV,
  apiGetCurrentCVJobMatch,
  apiMatchCVWithJob,
  type CandidateCV,
  type CVJobMatch,
} from '../api/cv';

const PRESET_ROLES = [
  {
    title: 'Product Designer',
    company: 'Aurora Labs',
    skills: ['Figma', 'Product Strategy', 'User Research', 'Accessibility', 'Systems Thinking'],
    description: 'Looking for a Senior Product Designer to drive end-to-end product craft, research synthesis, and accessible design systems.',
  },
  {
    title: 'Senior Frontend Engineer',
    company: 'Northstar Tech',
    skills: ['React', 'TypeScript', 'TailwindCSS', 'Web Accessibility', 'State Management'],
    description: 'Lead web application development using React, TypeScript, and modern component libraries. Drive UI performance and accessibility compliance.',
  },
  {
    title: 'Fullstack Software Developer',
    company: 'Fieldwork Studio',
    skills: ['Python', 'Django', 'React', 'REST API', 'MySQL', 'Docker'],
    description: 'Build end-to-end features across Django backend REST APIs and Vite React frontend. Write robust tests and maintain database models.',
  },
  {
    title: 'Data Analyst & Insights',
    company: 'Quantum Analytics',
    skills: ['Python', 'SQL', 'Data Visualization', 'Pandas', 'Statistics'],
    description: 'Extract business insights from dataset metrics, build executive reporting dashboards, and model candidate pipeline funnels.',
  },
];

/** Score-aware color helpers */
function getScoreTextColor(score: number): string {
  if (score < 40) return 'text-[#dc2626]';
  if (score < 70) return 'text-[#d97706]';
  return 'text-[#166534]';
}

function getSignalBarColor(val: number): string {
  if (val >= 70) return 'bg-[#16a34a]';
  if (val >= 40) return 'bg-[#f59e0b]';
  return 'bg-[#dc2626]';
}

function getSignalTextColor(val: number): string {
  if (val >= 70) return 'text-[#166534]';
  if (val >= 40) return 'text-[#78350f]';
  return 'text-[#991b1b]';
}

/** Placeholder companies that should be hidden if no real company is entered */
const PLACEHOLDER_COMPANIES = new Set([
  'Aurora Labs',
  'Northstar Tech',
  'Fieldwork Studio',
  'Quantum Analytics',
  'CareerFlow Client',
  'CareerFlow Partner',
  'Hiring Company',
]);

export function JobMatch({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();

  const [currentCv, setCurrentCv] = useState<CandidateCV | null>(null);
  const [matchResult, setMatchResult] = useState<CVJobMatch | null>(null);
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);

  // Custom role comparator state
  const [selectedPresetIndex, setSelectedPresetIndex] = useState<number>(0);
  const [customTitle, setCustomTitle] = useState('Product Designer');
  const [customCompany, setCustomCompany] = useState('Aurora Labs');
  const [customSkills, setCustomSkills] = useState('Figma, Product Strategy, User Research, Accessibility');
  const [customDescription, setCustomDescription] = useState(
    'Looking for a Product Designer with strong Figma, user research, product strategy, and accessibility experience.'
  );

  const loadData = async () => {
    try {
      setLoading(true);
      const [cv, match] = await Promise.all([
        apiGetCurrentCV().catch(() => null),
        apiGetCurrentCVJobMatch().catch(() => null),
      ]);
      setCurrentCv(cv);
      setMatchResult(match);

      if (match) {
        setCustomTitle(match.job_title || 'Product Designer');
        setCustomCompany(match.company || '');
        setCustomDescription(match.job_description || '');
        if (match.skills_matched || match.skills_missing) {
          const combined = [...(match.skills_matched || []), ...(match.skills_missing || [])];
          if (combined.length > 0) {
            setCustomSkills(combined.join(', '));
          }
        }
      }
    } catch (err: any) {
      notify('Failed to load semantic match data.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSelectPreset = (idx: number) => {
    setSelectedPresetIndex(idx);
    const preset = PRESET_ROLES[idx];
    setCustomTitle(preset.title);
    setCustomCompany(preset.company);
    setCustomSkills(preset.skills.join(', '));
    setCustomDescription(preset.description);
  };

  const handleRunMatch = async () => {
    if (!currentCv) {
      notify('Please upload an active CV first in Candidate Studio.', 'error');
      return;
    }

    try {
      setCalculating(true);
      const skillsArray = customSkills
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);

      const res = await apiMatchCVWithJob({
        job_title: customTitle || 'Target Role',
        company: customCompany || '',
        job_description: customDescription,
        required_skills: skillsArray,
      });

      setMatchResult(res);
      notify(`Role match evaluated: ${res.match_score}/100 score generated.`, 'success');
    } catch (err: any) {
      const msg = err?.response?.data?.error || err?.message || 'Failed to calculate semantic match.';
      notify(msg, 'error');
    } finally {
      setCalculating(false);
    }
  };

  const score = matchResult?.match_score ?? 0;
  const scoreTextColor = matchResult ? getScoreTextColor(score) : 'text-[#d97706]';

  // Real company only (hide if missing or placeholder)
  const realCompany =
    matchResult?.company &&
    matchResult.company.trim() !== '' &&
    !PLACEHOLDER_COMPANIES.has(matchResult.company.trim())
      ? matchResult.company.trim()
      : null;

  // Build required skills evaluation list
  const requiredSkillsList = Array.from(
    new Set([
      ...(matchResult?.skills_matched || []),
      ...(matchResult?.skills_missing || []),
      ...customSkills.split(',').map((s) => s.trim()).filter(Boolean),
    ])
  ).slice(0, 6);

  return (
    <AppShell role="student" notify={notify}>
      {/* Top Header: Breadcrumbs & Actions */}
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <nav className="flex items-center gap-1.5 text-xs font-semibold text-[#4B5563]" aria-label="Breadcrumb">
          <button
            onClick={() => setLocation('/student/cv')}
            className="hover:text-[#1F2937] transition whitespace-nowrap cursor-pointer"
          >
            CV Studio
          </button>
          <ChevronRight size={13} className="shrink-0 text-[#9ca3af]" />
          <button
            onClick={() => setLocation('/student/cv/results')}
            className="hover:text-[#1F2937] transition whitespace-nowrap cursor-pointer"
          >
            Feedback
          </button>
          <ChevronRight size={13} className="shrink-0 text-[#9ca3af]" />
          <span className="text-[#1F2937] font-bold whitespace-nowrap">Job Match</span>
        </nav>

        {currentCv && (
          <div className="flex items-center gap-2">
            <Badge tone="good">Active CV: {currentCv.original_filename}</Badge>
          </div>
        )}
      </div>

      <PageHeading
        title="CV-Job Semantic Matching"
        description="Evaluate your CV experience against specific target roles. Understand keyword coverage, sub-signals, and missing skill requirements."
      />

      {/* Tab navigation — matches CvResults.tsx */}
      <div className="mb-6 flex items-center border-b border-[#d9dbd1]">
        <button
          type="button"
          onClick={() => setLocation('/student/cv/results')}
          data-testid="tab-cv-review"
          className="border-b-2 border-transparent px-4 py-2.5 text-xs font-semibold text-[#687382] hover:text-[#253142] hover:border-[#ccd0c6] cursor-pointer"
        >
          Review &amp; suggestions
        </button>
        <button
          type="button"
          onClick={() => setLocation('/student/cv/match')}
          data-testid="tab-job-match"
          className="border-b-2 border-[#253142] px-4 py-2.5 text-xs font-bold text-[#253142] cursor-pointer"
        >
          Job match
        </button>
      </div>

      {loading ? (
        <div className="py-20 text-center">
          <div className="mx-auto h-9 w-9 animate-spin rounded-full border-4 border-[#277254] border-t-transparent" />
          <p className="mt-4 text-sm font-semibold text-[#526072]">
            Calculating semantic similarity vector scores...
          </p>
        </div>
      ) : !currentCv ? (
        <div className="py-16 text-center cf-card rounded-2xl bg-white p-8 border border-[#d9dbd1]">
          <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-[#f4f2e9] text-[#7b8490]">
            <FileText size={26} />
          </div>
          <h2 className="mt-4 text-lg font-bold text-[#253142]">No Active CV Document Uploaded</h2>
          <p className="mx-auto mt-2 max-w-md text-xs leading-5 text-[#7b8490]">
            Upload your resume in CV Studio to compare your experience against open role briefs and job descriptions.
          </p>
          <button
            onClick={() => setLocation('/student/cv')}
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-[#253142] px-4 py-2.5 text-xs font-bold text-[#faf7ef] hover:bg-[#33435a]"
          >
            Go to CV Studio
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Main Grid Row 1: Hero Card + Sub-signals Card (shared 1.6fr 1fr grid) */}
          <div className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
            {/* Hero Role Match Card */}
            <section
              data-testid="card-match-hero"
              className="cf-card rounded-2xl bg-white p-6 border border-[#d9dbd1] shadow-sm flex flex-col justify-between"
            >
              <div>
                {/* Top row: label + keyword coverage badge */}
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold uppercase tracking-[.14em] text-[#4B5563]">
                    Role Match • Skill Signal
                  </span>
                  {matchResult && (
                    <span className="rounded-full bg-[#fef3c7] border border-[#fde68a] px-3 py-1 font-mono text-xs font-bold text-[#78350f]">
                      {matchResult.keyword_coverage}% Keyword Coverage
                    </span>
                  )}
                </div>

                {/* Score */}
                <div className="mt-5 flex items-baseline gap-3">
                  <span
                    className={`cf-display text-7xl font-bold leading-none ${scoreTextColor}`}
                    data-testid="text-match-score"
                  >
                    {matchResult?.match_score ?? '—'}
                  </span>
                  {matchResult && <span className="text-xl font-semibold text-[#687382]">/ 100</span>}
                </div>

                {/* Headline - Dark ink #1F2937 for WCAG AA compliance */}
                <h2
                  className="mt-4 text-2xl font-bold text-[#1F2937]"
                  data-testid="text-match-headline"
                >
                  {matchResult
                    ? matchResult.match_score >= 80
                      ? `Strong match for ${matchResult.job_title}`
                      : matchResult.match_score >= 65
                      ? `Moderate match for ${matchResult.job_title}`
                      : `Needs keywords for ${matchResult.job_title}`
                    : `Target Role: ${customTitle}`}
                </h2>

                {/* Body paragraph - at least #4B5563 */}
                <p className="mt-2 text-xs leading-5 text-[#4B5563] font-medium">
                  Based on semantic vector similarity and extracted skill taxonomies in your active CV.
                </p>

                {/* Required skills evaluation group with strict state rendering */}
                <div className="mt-5">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-[#4B5563] block mb-2">
                    Required skills
                  </span>
                  <div className="flex flex-wrap gap-2 pb-2" data-testid="container-matched-skill-tags">
                    {requiredSkillsList.map((skill, idx) => {
                      const isMatched = matchResult?.skills_matched?.includes(skill);
                      const isMissing = matchResult?.skills_missing?.includes(skill);

                      if (isMatched) {
                        return (
                          <span
                            key={idx}
                            className="inline-flex items-center gap-1.5 rounded-xl border border-[#bce2d1] bg-[#e2f0e9] px-3 py-1 text-xs font-bold text-[#166534]"
                          >
                            <Check size={13} className="shrink-0 text-[#166534]" />
                            <span>{skill}</span>
                          </span>
                        );
                      }

                      if (isMissing) {
                        return (
                          <span
                            key={idx}
                            className="inline-flex items-center gap-1.5 rounded-xl border border-[#fecaca] bg-[#fee2e2] px-3 py-1 text-xs font-bold text-[#991b1b]"
                          >
                            <X size={13} className="shrink-0 text-[#991b1b]" />
                            <span>{skill}</span>
                          </span>
                        );
                      }

                      // Neutral required skill before evaluation
                      return (
                        <span
                          key={idx}
                          className="inline-flex items-center gap-1 rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3 py-1 text-xs font-semibold text-[#374151]"
                        >
                          <span>{skill}</span>
                        </span>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Pinned footer with identical divider style */}
              <div className="mt-6 pt-4 border-t border-[#d9dbd1] flex items-center justify-between text-xs text-[#4B5563] font-medium">
                <span>Role: {matchResult?.job_title || customTitle}</span>
                {realCompany && <span>Company: {realCompany}</span>}
              </div>
            </section>

            {/* Role Signal Breakdown Card */}
            <section
              data-testid="card-match-signals"
              className="cf-card rounded-2xl bg-white p-6 border border-[#d9dbd1] shadow-sm flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between pb-3 border-b border-[#d9dbd1]">
                  <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#4B5563]">
                    <SlidersHorizontal size={16} className="text-[#166534]" />
                    <span>Role Signal Breakdown</span>
                  </div>
                  <span className="text-xs font-medium text-[#4B5563]" title="Semantic embeddings vector similarity">
                    Semantic fit
                  </span>
                </div>

                <div className="mt-5 space-y-4">
                  {[
                    ['Product / Technical Craft', matchResult?.category_scores?.domain_craft ?? 81],
                    ['Cross-functional Collaboration', matchResult?.category_scores?.collaboration ?? 50],
                    ['Ownership & Leadership', matchResult?.category_scores?.leadership ?? 65],
                    ['Accessibility & Quality Standards', matchResult?.category_scores?.accessibility ?? 50],
                  ].map(([label, val]) => {
                    const scoreVal = val as number;
                    return (
                      <div key={label as string} className="space-y-1">
                        <div className="flex justify-between text-xs font-bold text-[#1F2937]">
                          <span>{label as string}</span>
                          <span className={getSignalTextColor(scoreVal)}>
                            {scoreVal}%
                          </span>
                        </div>
                        <div className="h-2 w-full overflow-hidden rounded-full bg-[#eef0e7]">
                          <div
                            className={`h-full transition-all duration-300 ${getSignalBarColor(scoreVal)}`}
                            style={{ width: `${scoreVal}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Small legend for bar colors */}
                <div className="mt-4 flex items-center justify-between text-[11px] font-medium text-[#4B5563] pt-2 border-t border-[#eef0e7]">
                  <span className="flex items-center gap-1">
                    <span className="h-2 w-2 rounded-full bg-[#16a34a]" /> &ge;70% Strong
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="h-2 w-2 rounded-full bg-[#f59e0b]" /> 40–69% Moderate
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="h-2 w-2 rounded-full bg-[#dc2626]" /> &lt;40% Needs keywords
                  </span>
                </div>
              </div>

              {/* Informative explanation note */}
              <div className="mt-6 pt-4 border-t border-[#d9dbd1] flex items-center gap-2 text-xs text-[#4B5563]">
                <Info size={14} className="shrink-0 text-[#687382]" />
                <span className="leading-tight">
                  Evaluates domain craft, team signals, leadership &amp; accessibility fit.
                </span>
              </div>
            </section>
          </div>

          {/* Main Grid Row 2: Matched vs Missing Skills (shares 1.6fr 1fr grid) */}
          <div className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
            {/* Matched Skills */}
            <section className="cf-card rounded-2xl bg-white p-6 border border-[#d9dbd1] shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 pb-3 border-b border-[#d9dbd1] text-[#166534]">
                  <CheckCircle2 size={18} />
                  <h3 className="font-bold text-[#1F2937] text-sm">
                    Matched Skills &amp; Keywords ({matchResult?.skills_matched?.length || 0})
                  </h3>
                </div>

                {matchResult?.skills_matched && matchResult.skills_matched.length > 0 ? (
                  <div className="mt-4 flex flex-wrap gap-2 pb-2">
                    {matchResult.skills_matched.map((s, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center gap-1.5 rounded-xl border border-[#bce2d1] bg-[#e2f0e9] px-3 py-1.5 text-xs font-bold text-[#166534]"
                      >
                        <Check size={13} /> {s}
                      </span>
                    ))}
                  </div>
                ) : (
                  <div className="mt-4 flex flex-col items-center justify-center gap-2.5 py-6 px-4 rounded-xl border border-dashed border-[#d9dbd1] bg-[#fbfaf5] text-center">
                    <div className="grid h-10 w-10 place-items-center rounded-2xl bg-[#eef0e7] text-[#687382]">
                      <CheckCircle2 size={20} />
                    </div>
                    <div>
                      <p className="text-xs font-bold text-[#1F2937]">No matching skills detected for this role</p>
                      <p className="mt-0.5 text-[11px] text-[#4B5563]">
                        Add the required keywords to your CV to boost your semantic match score.
                      </p>
                    </div>
                    <button
                      onClick={() => setLocation('/student/cv')}
                      className="mt-1 inline-flex items-center gap-1.5 rounded-xl bg-[#253142] px-3.5 py-2 text-xs font-bold text-[#faf7ef] hover:bg-[#33435a] transition cursor-pointer"
                    >
                      Add these keywords to your CV
                    </button>
                  </div>
                )}
              </div>
            </section>

            {/* Missing Skills */}
            <section className="cf-card rounded-2xl bg-white p-6 border border-[#d9dbd1] shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 pb-3 border-b border-[#d9dbd1] text-[#991b1b]">
                  <XCircle size={18} />
                  <h3 className="font-bold text-[#1F2937] text-sm">
                    Missing Skill Requirements ({matchResult?.skills_missing?.length || 0})
                  </h3>
                </div>

                <div className="mt-4 flex flex-wrap gap-2 pb-2">
                  {matchResult?.skills_missing && matchResult.skills_missing.length > 0 ? (
                    matchResult.skills_missing.map((s, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center gap-1.5 rounded-xl border border-[#fecaca] bg-[#fee2e2] px-3 py-1.5 text-xs font-bold text-[#991b1b]"
                      >
                        + {s}
                      </span>
                    ))
                  ) : (
                    <p className="text-xs font-bold text-[#166534]">
                      {matchResult ? 'Great news! No critical missing skills detected.' : 'Run evaluation to identify skill gaps.'}
                    </p>
                  )}
                </div>
              </div>
            </section>
          </div>

          {/* Interactive Custom Role Comparator Form */}
          <section className="cf-card rounded-2xl bg-white p-6 border border-[#d9dbd1] shadow-sm">
            <div className="flex flex-col gap-3 pb-4 border-b border-[#d9dbd1] sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-2.5">
                <div className="grid h-8 w-8 place-items-center rounded-xl bg-[#e2f0e9] text-[#166534]">
                  <Briefcase size={18} />
                </div>
                <div>
                  <h2 className="font-bold text-[#1F2937] text-base">Test Match Against Another Role</h2>
                  <p className="text-xs text-[#4B5563]">
                    Select a preset role or input custom job requirements to re-calculate your CV semantic fit in real time.
                  </p>
                </div>
              </div>
              <Badge tone="good">Role Match Sandbox</Badge>
            </div>

            {/* Preset Buttons */}
            <div className="mt-5">
              <label className="text-xs font-bold text-[#4B5563] uppercase tracking-wider block mb-2">
                Quick Presets
              </label>
              <div className="flex flex-wrap gap-2">
                {PRESET_ROLES.map((preset, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSelectPreset(idx)}
                    className={`rounded-xl border px-3.5 py-2 text-xs font-bold transition whitespace-nowrap cursor-pointer ${
                      selectedPresetIndex === idx
                        ? 'border-[#253142] bg-[#253142] text-[#faf7ef]'
                        : 'border-[#ccd0c6] bg-[#fbfaf5] text-[#1F2937] hover:border-[#253142]'
                    }`}
                  >
                    {preset.title}
                  </button>
                ))}
              </div>
            </div>

            {/* Inputs Form */}
            <div className="mt-5 grid gap-4 md:grid-cols-2">
              <div>
                <label className="text-xs font-bold text-[#1F2937]">Target Job Title</label>
                <input
                  type="text"
                  value={customTitle}
                  onChange={(e) => setCustomTitle(e.target.value)}
                  placeholder="e.g. Senior Frontend Developer"
                  data-testid="input-match-title"
                  className="mt-1.5 w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3.5 py-2.5 text-xs text-[#1F2937] focus:border-[#253142] focus:outline-none"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-[#1F2937]">Company / Organization</label>
                <input
                  type="text"
                  value={customCompany}
                  onChange={(e) => setCustomCompany(e.target.value)}
                  placeholder="e.g. Aurora Labs"
                  data-testid="input-match-company"
                  className="mt-1.5 w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3.5 py-2.5 text-xs text-[#1F2937] focus:border-[#253142] focus:outline-none"
                />
              </div>

              <div className="md:col-span-2">
                <label className="text-xs font-bold text-[#1F2937]">
                  Required Skills <span className="font-normal text-[#4B5563]">(Comma separated)</span>
                </label>
                <input
                  type="text"
                  value={customSkills}
                  onChange={(e) => setCustomSkills(e.target.value)}
                  placeholder="e.g. React, TypeScript, TailwindCSS, Accessibility"
                  data-testid="input-match-skills"
                  className="mt-1.5 w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3.5 py-2.5 text-xs text-[#1F2937] focus:border-[#253142] focus:outline-none"
                />
              </div>

              <div className="md:col-span-2">
                <label className="text-xs font-bold text-[#1F2937]">Job Description / Requirements Text</label>
                <textarea
                  rows={3}
                  value={customDescription}
                  onChange={(e) => setCustomDescription(e.target.value)}
                  placeholder="Paste target job description responsibilities or brief..."
                  data-testid="input-match-description"
                  className="mt-1.5 w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] p-3.5 text-xs text-[#1F2937] focus:border-[#253142] focus:outline-none"
                />
              </div>
            </div>

            <div className="mt-5 flex justify-end">
              <button
                type="button"
                disabled={calculating || !customTitle}
                onClick={handleRunMatch}
                data-testid="button-recalculate-match"
                className="inline-flex min-h-[44px] items-center gap-2 rounded-xl bg-[#253142] px-5 py-2.5 text-xs font-bold text-[#faf7ef] hover:bg-[#33435a] transition disabled:opacity-40 whitespace-nowrap shadow-xs cursor-pointer"
              >
                <RefreshCw size={18} className={calculating ? 'animate-spin' : ''} />
                <span>{calculating ? 'Evaluating Semantic Vector Match...' : 'Calculate Role Semantic Match'}</span>
              </button>
            </div>
          </section>

          {/* Actionable Recommendations for Role Match */}
          {matchResult?.recommendations && matchResult.recommendations.length > 0 && (
            <section className="cf-card rounded-2xl bg-white p-6 border border-[#d9dbd1] shadow-sm">
              <div className="flex items-center gap-2 pb-3 border-b border-[#d9dbd1] text-[#1F2937]">
                <Sparkles size={18} className="text-[#d97706]" />
                <h3 className="font-bold text-[#1F2937] text-sm">
                  Targeted Edits to Boost Score for {matchResult.job_title}
                </h3>
              </div>
              <div className="mt-4 space-y-2.5">
                {matchResult.recommendations.map((rec, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-3 rounded-xl border border-[#eef0e7] bg-[#fbfaf5] p-3.5 text-xs text-[#1F2937]"
                  >
                    <span className="grid h-6 w-6 place-items-center rounded-full bg-[#253142] text-[11px] font-bold text-[#faf7ef] shrink-0">
                      {idx + 1}
                    </span>
                    <p className="font-semibold leading-relaxed pt-0.5">{rec}</p>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </AppShell>
  );
}
