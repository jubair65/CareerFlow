import { useState, useEffect } from 'react';
import { useLocation } from 'wouter';
import {
  FileText,
  Sparkles,
  ArrowLeft,
  ArrowRight,
  Check,
  AlertCircle,
  TrendingUp,
  Target,
  SlidersHorizontal,
  Briefcase,
  Search,
  CheckCircle2,
  XCircle,
  RefreshCw,
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
        setCustomCompany(match.company || 'Aurora Labs');
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
        company: customCompany || 'Hiring Company',
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

  return (
    <AppShell role="student" notify={notify}>
      {/* Top Header */}
      <div className="mb-4 flex items-center justify-between">
        <button
          onClick={() => setLocation('/student/cv/results')}
          data-testid="button-back-to-results"
          className="inline-flex items-center gap-2 text-xs font-bold text-[#526072] hover:text-[#253142] transition"
        >
          <ArrowLeft size={15} /> Back to CV Feedback
        </button>

        {currentCv && (
          <Badge tone="good">Active CV: {currentCv.original_filename}</Badge>
        )}
      </div>

      <PageHeading
        eyebrow="US-09 Semantic Intelligence"
        title="CV-Job Semantic Matching"
        description="Evaluate your CV experience against specific target roles. Understand keyword coverage, sub-signals, and missing skill requirements."
      />

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
          {/* Main Grid: Hero Card + Sub-signals Card */}
          <div className="grid gap-6 lg:grid-cols-[1.1fr_.9fr]">
            {/* Hero Role Match Card (Design from CareerFlow-Recruitment-Coach) */}
            <section
              data-testid="card-match-hero"
              className="cf-card rounded-2xl bg-[#253142] p-6 text-[#faf7ef] shadow-sm flex flex-col justify-between relative overflow-hidden"
            >
              <div className="absolute -right-10 -bottom-10 h-40 w-40 rounded-full bg-[#f5c84b]/15 blur-3xl" />

              <div>
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold uppercase tracking-[.14em] text-[#aab5c0]">
                    Role Match • US-09 Signal
                  </span>
                  <span className="rounded-full bg-[#f5c84b]/20 px-3 py-1 font-mono text-xs font-bold text-[#f5c84b]">
                    {matchResult ? `${matchResult.keyword_coverage}% Keyword Coverage` : 'NLP Engine Ready'}
                  </span>
                </div>

                <div className="mt-6 flex items-baseline gap-3">
                  <span
                    className="cf-display text-7xl font-bold leading-none text-[#f5c84b]"
                    data-testid="text-match-score"
                  >
                    {matchResult?.match_score ?? 84}
                  </span>
                  <span className="text-2xl font-semibold text-[#8fa0b5]">/ 100</span>
                </div>

                <h2 className="mt-4 text-2xl font-bold text-[#faf7ef]" data-testid="text-match-headline">
                  {matchResult
                    ? matchResult.match_score >= 80
                      ? `Strong match for ${matchResult.job_title}`
                      : matchResult.match_score >= 65
                      ? `Moderate match for ${matchResult.job_title}`
                      : `Needs keywords for ${matchResult.job_title}`
                    : `Strong match for Product Designer`}
                </h2>
                <p className="mt-2 text-xs leading-5 text-[#c4ccd3]">
                  Based on semantic vector similarity and extracted skill taxonomies in your active CV.
                </p>

                {/* Skills tags list */}
                <div className="mt-5 flex flex-wrap gap-2" data-testid="container-matched-skill-tags">
                  {(matchResult?.skills_matched && matchResult.skills_matched.length > 0
                    ? matchResult.skills_matched
                    : ['Systems Thinking', 'Product Strategy', 'Figma', 'Accessibility']
                  ).map((skill, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 rounded-xl bg-[#37475d] px-3 py-1 text-xs font-bold text-[#f5c84b]"
                    >
                      <Check size={13} className="text-[#84c49f]" /> {skill}
                    </span>
                  ))}
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-[#3d4d62] flex items-center justify-between text-xs text-[#aab5c0]">
                <span>Role: {matchResult?.job_title || 'Product Designer'}</span>
                <span>Company: {matchResult?.company || 'Aurora Labs'}</span>
              </div>
            </section>

            {/* Sub-signals Card (Role Signals) */}
            <section
              data-testid="card-match-signals"
              className="cf-card rounded-2xl bg-white p-6 border border-[#d9dbd1] shadow-sm flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between pb-3 border-b border-[#eef0e7]">
                  <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#526072]">
                    <SlidersHorizontal size={16} className="text-[#277254]" />
                    <span>Role Signal Breakdown</span>
                  </div>
                  <span className="text-xs font-semibold text-[#7b8490]">Sub-category Fit</span>
                </div>

                <div className="mt-5 space-y-4">
                  {[
                    ['Product / Technical Craft', matchResult?.category_scores?.domain_craft ?? 91],
                    ['Cross-functional Collaboration', matchResult?.category_scores?.collaboration ?? 86],
                    ['Ownership & Leadership', matchResult?.category_scores?.leadership ?? 74],
                    ['Accessibility & Quality Standards', matchResult?.category_scores?.accessibility ?? 62],
                  ].map(([label, val]) => (
                    <div key={label as string} className="space-y-1">
                      <div className="flex justify-between text-xs font-bold text-[#253142]">
                        <span>{label as string}</span>
                        <span className={(val as number) >= 80 ? 'text-[#277254]' : 'text-[#9a7922]'}>
                          {val as number}%
                        </span>
                      </div>
                      <div className="h-2 w-full overflow-hidden rounded-full bg-[#eef0e7]">
                        <div
                          className={`h-full transition-all duration-300 ${
                            (val as number) >= 80 ? 'bg-[#277254]' : 'bg-[#f5c84b]'
                          }`}
                          style={{ width: `${val as number}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-[#eef0e7] flex items-center justify-between text-xs text-[#7b8490]">
                <span>Evaluates domain craft, team signals, leadership & standards</span>
              </div>
            </section>
          </div>

          {/* Matched vs Missing Skills Grid */}
          <div className="grid gap-6 md:grid-cols-2">
            {/* Matched Skills */}
            <section className="cf-card rounded-2xl bg-white p-6 border border-[#d9dbd1] shadow-sm">
              <div className="flex items-center gap-2 pb-3 border-b border-[#eef0e7] text-[#277254]">
                <CheckCircle2 size={18} />
                <h3 className="font-bold text-[#253142] text-sm">
                  Matched Skills & Keywords ({matchResult?.skills_matched?.length || 0})
                </h3>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {matchResult?.skills_matched && matchResult.skills_matched.length > 0 ? (
                  matchResult.skills_matched.map((s, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1.5 rounded-xl border border-[#bce2d1] bg-[#e2f0e9] px-3 py-1.5 text-xs font-bold text-[#277254]"
                    >
                      <Check size={13} /> {s}
                    </span>
                  ))
                ) : (
                  <p className="text-xs text-[#7b8490]">No matching skills detected for this role brief.</p>
                )}
              </div>
            </section>

            {/* Missing Skills */}
            <section className="cf-card rounded-2xl bg-white p-6 border border-[#d9dbd1] shadow-sm">
              <div className="flex items-center gap-2 pb-3 border-b border-[#eef0e7] text-[#a33d35]">
                <XCircle size={18} />
                <h3 className="font-bold text-[#253142] text-sm">
                  Missing Skill Requirements ({matchResult?.skills_missing?.length || 0})
                </h3>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {matchResult?.skills_missing && matchResult.skills_missing.length > 0 ? (
                  matchResult.skills_missing.map((s, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1.5 rounded-xl border border-[#f5c7c2] bg-[#f7e5e1] px-3 py-1.5 text-xs font-bold text-[#a33d35]"
                    >
                      + {s}
                    </span>
                  ))
                ) : (
                  <p className="text-xs text-[#277254] font-semibold">
                    Great news! No critical missing skills detected.
                  </p>
                )}
              </div>
            </section>
          </div>

          {/* Interactive Custom Role Comparator Form */}
          <section className="cf-card rounded-2xl bg-white p-6 border border-[#d9dbd1] shadow-sm">
            <div className="flex items-center justify-between pb-4 border-b border-[#eef0e7]">
              <div className="flex items-center gap-2.5">
                <div className="grid h-8 w-8 place-items-center rounded-xl bg-[#e2f0e9] text-[#277254]">
                  <Briefcase size={18} />
                </div>
                <div>
                  <h2 className="font-bold text-[#253142] text-base">Test Match Against Another Role</h2>
                  <p className="text-xs text-[#7b8490]">
                    Select a preset role or input custom job requirements to re-calculate your CV semantic fit in real time.
                  </p>
                </div>
              </div>
              <Badge tone="good">Role Match Sandbox</Badge>
            </div>

            {/* Preset Buttons */}
            <div className="mt-5">
              <label className="text-xs font-bold text-[#526072] uppercase tracking-wider block mb-2">
                Quick Presets
              </label>
              <div className="flex flex-wrap gap-2">
                {PRESET_ROLES.map((preset, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSelectPreset(idx)}
                    className={`rounded-xl border px-3.5 py-2 text-xs font-bold transition ${
                      selectedPresetIndex === idx
                        ? 'border-[#253142] bg-[#253142] text-[#faf7ef]'
                        : 'border-[#ccd0c6] bg-[#fbfaf5] text-[#253142] hover:border-[#253142]'
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
                <label className="text-xs font-bold text-[#253142]">Target Job Title</label>
                <input
                  type="text"
                  value={customTitle}
                  onChange={(e) => setCustomTitle(e.target.value)}
                  placeholder="e.g. Senior Frontend Developer"
                  data-testid="input-match-title"
                  className="mt-1.5 w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3.5 py-2.5 text-xs text-[#253142] focus:border-[#253142] focus:outline-none"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-[#253142]">Company / Organization</label>
                <input
                  type="text"
                  value={customCompany}
                  onChange={(e) => setCustomCompany(e.target.value)}
                  placeholder="e.g. Aurora Labs"
                  data-testid="input-match-company"
                  className="mt-1.5 w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3.5 py-2.5 text-xs text-[#253142] focus:border-[#253142] focus:outline-none"
                />
              </div>

              <div className="md:col-span-2">
                <label className="text-xs font-bold text-[#253142]">
                  Required Skills <span className="font-normal text-[#7b8490]">(Comma separated)</span>
                </label>
                <input
                  type="text"
                  value={customSkills}
                  onChange={(e) => setCustomSkills(e.target.value)}
                  placeholder="e.g. React, TypeScript, TailwindCSS, Accessibility"
                  data-testid="input-match-skills"
                  className="mt-1.5 w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3.5 py-2.5 text-xs text-[#253142] focus:border-[#253142] focus:outline-none"
                />
              </div>

              <div className="md:col-span-2">
                <label className="text-xs font-bold text-[#253142]">Job Description / Requirements Text</label>
                <textarea
                  rows={3}
                  value={customDescription}
                  onChange={(e) => setCustomDescription(e.target.value)}
                  placeholder="Paste target job description responsibilities or brief..."
                  data-testid="input-match-description"
                  className="mt-1.5 w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] p-3.5 text-xs text-[#253142] focus:border-[#253142] focus:outline-none"
                />
              </div>
            </div>

            <div className="mt-5 flex justify-end">
              <button
                type="button"
                disabled={calculating || !customTitle}
                onClick={handleRunMatch}
                data-testid="button-recalculate-match"
                className="inline-flex items-center gap-2 rounded-xl bg-[#253142] px-5 py-2.5 text-xs font-bold text-[#faf7ef] hover:bg-[#33435a] transition disabled:opacity-40"
              >
                <RefreshCw size={14} className={calculating ? 'animate-spin' : ''} />
                {calculating ? 'Evaluating Semantic Vector Match...' : 'Calculate Role Semantic Match'}
              </button>
            </div>
          </section>

          {/* Actionable Recommendations for Role Match */}
          {matchResult?.recommendations && matchResult.recommendations.length > 0 && (
            <section className="cf-card rounded-2xl bg-white p-6 border border-[#d9dbd1] shadow-sm">
              <div className="flex items-center gap-2 pb-3 border-b border-[#eef0e7] text-[#253142]">
                <Sparkles size={18} className="text-[#f5c84b]" />
                <h3 className="font-bold text-[#253142] text-sm">
                  Targeted Edits to Boost Score for {matchResult.job_title}
                </h3>
              </div>
              <div className="mt-4 space-y-2.5">
                {matchResult.recommendations.map((rec, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-3 rounded-xl border border-[#eef0e7] bg-[#fbfaf5] p-3.5 text-xs text-[#253142]"
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
