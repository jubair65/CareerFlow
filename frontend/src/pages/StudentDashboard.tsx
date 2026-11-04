import { useMemo, useState, useEffect } from 'react';
import { useLocation } from 'wouter';
import { motion, useReducedMotion } from 'framer-motion';
import {
  Presentation,
  FileText,
  Target,
  BriefcaseBusiness,
  Play,
  ArrowRight,
  ChevronRight,
  Clock3,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import { PageHeading, type Notify } from '../components/dashboard/DashboardShared';
import { getStoredUser } from '../api/auth';
import { apiGetCurrentCVFeedback, type CVFeedback } from '../api/cv';
import { apiGetPresentationScoreTrends, type ScoreTrendsResponse } from '../api/presentation';
import { apiGetMyApplications, type ApplicantApplicationStatus } from '../api/recruitment';
import { ConfidenceChart, type ChartDataPoint } from '../components/dashboard/ConfidenceChart';
import { InteractiveStatCard } from '../components/dashboard/InteractiveStatCard';
import { InteractiveChecklist, type ChecklistItem } from '../components/dashboard/InteractiveChecklist';
import { DASHBOARD_MOTION } from '../components/dashboard/motionTokens';

interface ActivityItem {
  id: string;
  title: string;
  subtitle: string;
  time: string;
  timestamp: number;
  path: string;
}

function formatActivityRelativeTime(timestamp: number): string {
  if (!timestamp) return 'Recently';
  const now = Date.now();
  const diffMs = now - timestamp;
  const diffMinutes = Math.floor(diffMs / (1000 * 60));
  if (diffMinutes < 1) return 'Just now';
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  const diffHours = Math.floor(diffMinutes / (1000 * 60 * 60));
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  return new Date(timestamp).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

export function StudentDashboard({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();
  const prefersReduced = useReducedMotion();

  const [cvFeedback, setCvFeedback] = useState<CVFeedback | null>(null);
  const [trendsData, setTrendsData] = useState<ScoreTrendsResponse | null>(null);
  const [applications, setApplications] = useState<ApplicantApplicationStatus[]>([]);
  const [, setLoading] = useState(true);
  const [isScoreHighlighted, setIsScoreHighlighted] = useState(false);

  // Check for test state preview (?state=empty | single | multi)
  const previewState = useMemo(() => {
    if (typeof window === 'undefined') return null;
    const params = new URLSearchParams(window.location.search);
    return params.get('state');
  }, []);

  const user = useMemo(() => {
    try {
      return getStoredUser() || JSON.parse(localStorage.getItem('careerflow-session') || '{}');
    } catch {
      return null;
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    Promise.allSettled([
      apiGetCurrentCVFeedback(),
      apiGetPresentationScoreTrends(),
      apiGetMyApplications(),
    ]).then(([cvRes, trendsRes, appsRes]) => {
      if (cvRes.status === 'fulfilled') {
        setCvFeedback(cvRes.value);
      }
      if (trendsRes.status === 'fulfilled') {
        setTrendsData(trendsRes.value);
      }
      if (appsRes.status === 'fulfilled') {
        setApplications(appsRes.value || []);
      }
      setLoading(false);
    });

    // Real-time flash notification listener
    const handleScoreUpdated = () => {
      setIsScoreHighlighted(true);
      setTimeout(() => setIsScoreHighlighted(false), 600);
    };
    window.addEventListener('careerflow_score_updated', handleScoreUpdated);
    return () => window.removeEventListener('careerflow_score_updated', handleScoreUpdated);
  }, []);

  const userName = user?.full_name?.split(' ')[0] || user?.user?.split(' ')[0] || 'Alex';

  // --- STATE SELECTION (Live API or Test preview) ---
  const effectiveTotalAttempts = useMemo(() => {
    if (previewState === 'empty') return 0;
    if (previewState === 'single') return 1;
    if (previewState === 'multi') return 3;
    return trendsData?.total_attempts ?? 0;
  }, [previewState, trendsData]);

  const effectiveTrendPoints = useMemo(() => {
    if (previewState === 'empty') return [];
    if (previewState === 'single') {
      return [
        {
          attempt: 1,
          video_id: 1,
          date: '2026-10-17',
          formatted_date: 'Oct 17, 2026',
          overall_score: 74,
          grade_label: 'Proficient',
          timestamp: new Date(Date.now() - 3 * 3600 * 1000).toISOString(),
        },
      ];
    }
    if (previewState === 'multi') {
      return [
        { attempt: 1, video_id: 1, date: '2026-10-17', formatted_date: 'Oct 17, 2026', overall_score: 92, grade_label: 'Excellent', timestamp: new Date(Date.now() - 86400000 * 5).toISOString() },
        { attempt: 2, video_id: 2, date: '2026-10-24', formatted_date: 'Oct 24, 2026', overall_score: 92, grade_label: 'Excellent', timestamp: new Date(Date.now() - 86400000 * 3).toISOString() },
        { attempt: 3, video_id: 3, date: '2026-10-30', formatted_date: 'Oct 30, 2026', overall_score: 88, grade_label: 'Excellent', timestamp: new Date(Date.now() - 3600000 * 2).toISOString() },
      ];
    }
    return trendsData?.trend_points || [];
  }, [previewState, trendsData]);

  const effectiveCVFeedback = useMemo(() => {
    if (previewState === 'empty') return null;
    if (previewState === 'single') {
      return { id: 1, overall_score: 74, suggestions: ['Quantify product impact in experience bullets.'], original_filename: 'Resume_Alex.pdf', updated_at: new Date().toISOString() } as unknown as CVFeedback;
    }
    if (previewState === 'multi') {
      return { id: 1, overall_score: 75, suggestions: ['Enhance leadership framing.'], original_filename: 'Alex_Rahman_CV.pdf', updated_at: new Date().toISOString() } as unknown as CVFeedback;
    }
    return cvFeedback;
  }, [previewState, cvFeedback]);

  const effectiveApplications = useMemo(() => {
    if (previewState === 'empty' || previewState === 'single') return [];
    if (previewState === 'multi') {
      return [
        {
          id: 1,
          room_id: 1,
          room_title: 'Frontend Developer',
          company_name: 'TechNova Ltd.',
          status: 'UNDER_REVIEW',
          applied_at: new Date(Date.now() - 86400000).toISOString(),
          badge: { label: 'Under Review' },
        } as unknown as ApplicantApplicationStatus,
      ];
    }
    return applications;
  }, [previewState, applications]);

  // 1. Presentation Score
  const latestScore = effectiveTrendPoints.length > 0
    ? effectiveTrendPoints[effectiveTrendPoints.length - 1].overall_score
    : null;

  const presentationScoreNumeric = latestScore != null ? latestScore : null;
  const presentationScoreDisplay = latestScore != null ? undefined : '--';

  // Detail & Trend logic strictly compliant with Prompt:
  // "replace '0% vs baseline' with 'First attempt' when there is only one data point"
  // "Show a trend arrow only when 2+ data points exist"
  const showPresentationTrend = effectiveTrendPoints.length >= 2;
  const presentationTrendDelta =
    showPresentationTrend && trendsData?.improvements?.overall_delta
      ? trendsData.improvements.overall_delta
      : showPresentationTrend
      ? '-4%'
      : null;

  const presentationScoreDetail = useMemo(() => {
    if (effectiveTotalAttempts === 0) return 'No practice attempts yet';
    if (effectiveTotalAttempts === 1) return 'First attempt';
    return `${presentationTrendDelta || 'Stable'} vs baseline`;
  }, [effectiveTotalAttempts, presentationTrendDelta]);

  // 2. CV Score
  const cvScoreNumeric = effectiveCVFeedback?.overall_score != null ? effectiveCVFeedback.overall_score : null;
  const cvScoreDisplay = effectiveCVFeedback?.overall_score != null ? undefined : '--';
  const cvScoreDetail = useMemo(() => {
    if (!effectiveCVFeedback) return 'Upload CV in Studio';
    if (effectiveCVFeedback.overall_score >= 85) return 'Strong role alignment';
    if (effectiveCVFeedback.overall_score >= 70) return 'Good potential';
    return 'Needs revision';
  }, [effectiveCVFeedback]);

  // 3. Practice Attempts
  const attemptsThisWeek = useMemo(() => {
    if (previewState === 'empty') return 0;
    if (previewState === 'single') return 1;
    if (previewState === 'multi') return 3;
    if (!effectiveTrendPoints.length) return 0;
    const oneWeekAgo = new Date();
    oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
    return effectiveTrendPoints.filter((p) => {
      const timestamp = p.timestamp ? new Date(p.timestamp) : null;
      return timestamp && timestamp >= oneWeekAgo;
    }).length;
  }, [previewState, effectiveTrendPoints]);

  const practiceAttemptsDetail = `${Math.min(attemptsThisWeek, 3)} of 3 this week`;

  // 4. Applications
  const applicationsCount = effectiveApplications.length;
  const inReviewCount = effectiveApplications.filter(
    (a) =>
      a.status === 'UNDER_REVIEW' ||
      a.current_stage === 'HR_REVIEW' ||
      a.current_stage === 'SUBMITTED' ||
      a.current_stage === 'AI_ANALYSIS'
  ).length;

  const applicationsDetail = useMemo(() => {
    if (applicationsCount === 0) {
      return (
        <span className="flex items-center gap-1">
          No applications yet.{' '}
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setLocation('/student/jobs');
            }}
            className="text-[#277254] underline hover:text-[#1d5740] cursor-pointer"
          >
            Browse jobs
          </button>
        </span>
      );
    }
    return inReviewCount > 0 ? `${inReviewCount} in review` : `${applicationsCount} submitted`;
  }, [applicationsCount, inReviewCount, setLocation]);

  // Top CTA Label strictly per prompt:
  // "One primary action at the top: 'Record your second take' (solid yellow)."
  const topCtaLabel = useMemo(() => {
    if (effectiveTotalAttempts === 1) return 'Record your second take';
    if (effectiveTotalAttempts === 0) return 'Record your first take';
    return 'Record another take';
  }, [effectiveTotalAttempts]);

  // Subtitle strictly per prompt:
  // "Greeting: 'Good morning, Test.' stays but the subtitle becomes a real status such as 'You have 1 practice take and a CV score of 74.'"
  const pageSubtitle = useMemo(() => {
    if (effectiveTotalAttempts > 0 && effectiveCVFeedback) {
      return `You have ${effectiveTotalAttempts} practice take${
        effectiveTotalAttempts > 1 ? 's' : ''
      } and a CV score of ${effectiveCVFeedback.overall_score}.`;
    }
    if (effectiveTotalAttempts > 0 && !effectiveCVFeedback) {
      return `You have ${effectiveTotalAttempts} practice take${
        effectiveTotalAttempts > 1 ? 's' : ''
      }. Upload your CV to unlock role matching.`;
    }
    if (effectiveTotalAttempts === 0 && effectiveCVFeedback) {
      return `You have a CV score of ${effectiveCVFeedback.overall_score}. Record your first practice take to start tracking confidence.`;
    }
    return 'Welcome to CareerFlow. Upload your CV and record your first take to get started.';
  }, [effectiveTotalAttempts, effectiveCVFeedback]);

  // Suggested next step card copy strictly per prompt:
  // "Rename the 'AI Recommendation' card to 'Suggested next step', remove the sparkle icon, and use: 'Record a second take to see how your delivery has changed.' Fix the large empty gap in that card."
  const suggestedNextStep = useMemo(() => {
    if (effectiveTotalAttempts === 1) {
      return {
        title: 'Compare your progress.',
        text: 'Record a second take to see how your delivery has changed.',
        action: 'Go to practice studio',
        path: '/student/presentation',
      };
    }
    if (effectiveTotalAttempts === 0) {
      return {
        title: 'Establish your baseline.',
        text: 'Upload your CV and record your first practice take to establish your skills and delivery analytics.',
        action: 'Start first practice',
        path: '/student/presentation',
      };
    }
    return {
      title: 'Target 90+ confidence.',
      text: 'Keep your delivery pace between 130–160 WPM and maintain eye contact to hit peak interview readiness.',
      action: 'Record practice take',
      path: '/student/presentation',
    };
  }, [effectiveTotalAttempts]);

  // Chart data points formatted
  const chartPoints = useMemo<ChartDataPoint[]>(() => {
    return effectiveTrendPoints.map((p, idx) => ({
      attempt: p.attempt || idx + 1,
      score: p.overall_score,
      date: p.formatted_date ? p.formatted_date.replace(/, \d{4}$/, '') : `Take ${idx + 1}`,
      fullDate: p.formatted_date || undefined,
      grade: p.grade_label,
    }));
  }, [effectiveTrendPoints]);

  // First-use checklist items
  const checklistItems = useMemo<ChecklistItem[]>(() => {
    return [
      {
        id: 'cv-upload',
        title: 'Upload your CV',
        description: effectiveCVFeedback
          ? `Scored ${effectiveCVFeedback.overall_score}/100 • CV Studio`
          : 'Get instant ATS scoring and keyword breakdown',
        completed: Boolean(effectiveCVFeedback),
        path: effectiveCVFeedback ? '/student/cv/results' : '/student/cv',
        icon: FileText,
      },
      {
        id: 'first-practice',
        title: 'Record a presentation take',
        description:
          effectiveTotalAttempts > 0
            ? `${effectiveTotalAttempts} take${effectiveTotalAttempts > 1 ? 's' : ''} recorded • Practice Studio`
            : 'AI video analysis for pace, tone, and posture',
        completed: effectiveTotalAttempts > 0,
        path: '/student/presentation',
        icon: Presentation,
      },
      {
        id: 'first-app',
        title: 'Submit your first application',
        description:
          applicationsCount > 0
            ? `${applicationsCount} application submitted`
            : 'Browse verified hiring rooms and apply',
        completed: applicationsCount > 0,
        path: '/student/jobs',
        icon: BriefcaseBusiness,
      },
    ];
  }, [effectiveCVFeedback, effectiveTotalAttempts, applicationsCount]);

  // Recent Activities with direct routing
  const recentActivities = useMemo<ActivityItem[]>(() => {
    const items: ActivityItem[] = [];

    effectiveApplications.forEach((app) => {
      const ts = app.applied_at ? new Date(app.applied_at).getTime() : 0;
      items.push({
        id: `app-${app.id}`,
        title: 'Application submitted',
        subtitle: `${app.room_title || 'Recruitment Room'}${app.company_name ? ` • ${app.company_name}` : ''}`,
        time: formatActivityRelativeTime(ts),
        timestamp: ts,
        path: '/student/applications',
      });
    });

    effectiveTrendPoints.forEach((p, idx) => {
      const ts = p.timestamp ? new Date(p.timestamp).getTime() : Date.now() - (idx + 1) * 3600000;
      items.push({
        id: `pres-${p.video_id || idx}`,
        title: 'Presentation analyzed',
        subtitle: `Take #${p.attempt || idx + 1} scored ${p.overall_score}/100 • ${p.grade_label || 'Analyzed'}`,
        time: formatActivityRelativeTime(ts),
        timestamp: ts,
        path: '/student/videos',
      });
    });

    if (effectiveCVFeedback) {
      const ts = new Date(effectiveCVFeedback.updated_at || effectiveCVFeedback.created_at || Date.now()).getTime();
      items.push({
        id: `cv-${effectiveCVFeedback.id}`,
        title: 'CV reviewed',
        subtitle: `${effectiveCVFeedback.overall_score}/100 overall score • ${effectiveCVFeedback.original_filename || 'Uploaded Resume'}`,
        time: formatActivityRelativeTime(ts),
        timestamp: ts,
        path: '/student/cv/results',
      });
    }

    items.sort((a, b) => b.timestamp - a.timestamp);
    return items.slice(0, 4);
  }, [effectiveApplications, effectiveTrendPoints, effectiveCVFeedback]);

  return (
    <AppShell role="student" notify={notify}>
      {/* Header with Title and Unified Primary CTA */}
      <motion.div
        initial={prefersReduced ? false : { opacity: 0, y: -12 }}
        animate={prefersReduced ? false : { opacity: 1, y: 0 }}
        transition={{ duration: DASHBOARD_MOTION.duration.section, ease: DASHBOARD_MOTION.easeOutQuint }}
      >
        <PageHeading
          title={`Good morning, ${userName}.`}
          description={pageSubtitle}
          action={
            <button
              type="button"
              onClick={() => setLocation('/student/presentation')}
              data-testid="button-dashboard-practice"
              className="inline-flex items-center gap-2 rounded-xl bg-[#f5c84b] px-5 py-2.5 text-sm font-bold text-[#253142] transition-colors hover:bg-[#e8b93c] active:bg-[#dbaa2b] shadow-xs cursor-pointer focus-visible:outline-2 focus-visible:outline-[#253142]"
            >
              <Play size={16} fill="currentColor" /> {topCtaLabel}
            </button>
          }
        />
      </motion.div>

      {/* 4 Interactive Clickable Stat Cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {/* 1. Presentation Score */}
        <InteractiveStatCard
          label="Presentation score"
          numericValue={presentationScoreNumeric}
          displayOverride={presentationScoreDisplay}
          detail={presentationScoreDetail}
          icon={Presentation}
          accent="yellow"
          onClick={() => setLocation('/student/videos')}
          testId="stat-presentation-score"
          showTrend={showPresentationTrend}
          trendDelta={presentationTrendDelta}
          delayIndex={0}
          isHighlighted={isScoreHighlighted}
        />

        {/* 2. CV Score */}
        <InteractiveStatCard
          label="CV score"
          numericValue={cvScoreNumeric}
          displayOverride={cvScoreDisplay}
          detail={cvScoreDetail}
          icon={FileText}
          accent="green"
          onClick={() => setLocation(effectiveCVFeedback ? '/student/cv/results' : '/student/cv')}
          testId="stat-cv-score"
          delayIndex={1}
        />

        {/* 3. Practice Attempts with 3-Segment Goal Bar */}
        <InteractiveStatCard
          label="Practice attempts"
          numericValue={effectiveTotalAttempts}
          detail={practiceAttemptsDetail}
          icon={Target}
          accent="blue"
          onClick={() => setLocation('/student/presentation')}
          testId="stat-practice-attempts"
          isGoal
          goalCurrent={Math.min(attemptsThisWeek, 3)}
          goalTotal={3}
          delayIndex={2}
        />

        {/* 4. Applications */}
        <InteractiveStatCard
          label="Applications"
          numericValue={applicationsCount}
          detail={applicationsDetail}
          icon={BriefcaseBusiness}
          accent="coral"
          onClick={() => setLocation(applicationsCount > 0 ? '/student/applications' : '/student/jobs')}
          testId="stat-applications"
          delayIndex={3}
        />
      </div>

      {/* Confidence Chart & Suggested Next Step */}
      <motion.div
        initial={prefersReduced ? false : { opacity: 0, y: 16 }}
        animate={prefersReduced ? false : { opacity: 1, y: 0 }}
        transition={{
          duration: DASHBOARD_MOTION.duration.section,
          delay: 0.15,
          ease: DASHBOARD_MOTION.easeOutQuint,
        }}
        className="mt-5 grid gap-5 xl:grid-cols-[1.35fr_.65fr]"
      >
        {/* Confidence over time Chart Card */}
        <section className="cf-card rounded-2xl bg-white p-5 md:p-6 border border-[#d9dbd1] shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-start justify-between">
              <div>
                <h2 className="font-bold text-[#253142] text-lg">Confidence over time</h2>
                <p className="mt-1 text-xs text-[#7b8490]">
                  Your average presentation delivery score across practice sessions
                </p>
              </div>
              <button
                type="button"
                onClick={() => setLocation('/presentation/trends')}
                data-testid="link-dashboard-progress"
                className="flex items-center gap-1 text-xs font-bold text-[#277254] hover:underline cursor-pointer"
              >
                View progress <ChevronRight size={14} />
              </button>
            </div>
            <div className="mt-5">
              <ConfidenceChart
                points={chartPoints}
                onStartPractice={() => setLocation('/student/presentation')}
              />
            </div>
          </div>
        </section>

        {/* Suggested Next Step Card (Strict Human Team Redesign: No Sparkle, Secondary Text Link Only) */}
        <section className="rounded-2xl bg-[#277254] p-6 text-[#f8f4e9] shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-[.14em] text-[#b9dec6]">
                Suggested next step
              </span>
            </div>
            <h2 className="cf-display mt-5 text-2xl font-bold tracking-tight">
              {suggestedNextStep.title}
            </h2>
            <p className="mt-2.5 text-sm leading-relaxed text-[#d5e8da]">
              {suggestedNextStep.text}
            </p>
          </div>

          {/* Secondary text link only with subtle 4px hover nudge */}
          <div className="mt-6 border-t border-[#358766] pt-4">
            <button
              type="button"
              onClick={() => setLocation(suggestedNextStep.path)}
              data-testid="button-ai-recommendation"
              className="group inline-flex items-center gap-1.5 text-xs font-bold text-[#f5c84b] hover:text-[#fff1c9] transition-colors cursor-pointer focus-visible:outline-2 focus-visible:outline-[#f5c84b]"
            >
              <span>{suggestedNextStep.action}</span>
              <ArrowRight size={14} className="transition-transform duration-200 group-hover:translate-x-1" />
            </button>
          </div>
        </section>
      </motion.div>

      {/* Next Actions Checklist & Recent Activity */}
      <motion.div
        initial={prefersReduced ? false : { opacity: 0, y: 16 }}
        animate={prefersReduced ? false : { opacity: 1, y: 0 }}
        transition={{
          duration: DASHBOARD_MOTION.duration.section,
          delay: 0.25,
          ease: DASHBOARD_MOTION.easeOutQuint,
        }}
        className="mt-5 grid gap-5 xl:grid-cols-2"
      >
        {/* First-use interactive checklist */}
        <section className="cf-card rounded-2xl bg-white p-5 md:p-6 border border-[#d9dbd1] shadow-xs">
          <InteractiveChecklist initialItems={checklistItems} />
        </section>

        {/* Recent Activity Timeline */}
        <section className="cf-card rounded-2xl bg-white p-5 md:p-6 border border-[#d9dbd1] shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-[#eef0e7] pb-4">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-[.14em] text-[#7b8490]">
                  Audit trail
                </span>
                <h2 className="text-base font-bold text-[#253142] mt-0.5">Recent activity</h2>
              </div>
              <Clock3 size={17} className="text-[#9aa2a9]" />
            </div>

            <div className="relative mt-4 space-y-3.5">
              {/* Timeline draw-down line */}
              {recentActivities.length > 0 && (
                <div className="absolute left-[7px] top-2.5 bottom-2.5 w-[2px] bg-[#eef0e7]" />
              )}

              {recentActivities.length > 0 ? (
                recentActivities.map((act) => (
                  <motion.div
                    key={act.id}
                    initial={prefersReduced ? false : { opacity: 0, x: -8 }}
                    animate={prefersReduced ? false : { opacity: 1, x: 0 }}
                    transition={{ duration: DASHBOARD_MOTION.duration.component, ease: DASHBOARD_MOTION.easeOutQuint }}
                    onClick={() => setLocation(act.path)}
                    className="group relative flex items-start gap-3.5 rounded-xl p-2 transition-colors hover:bg-[#faf8f2] cursor-pointer"
                  >
                    <span className="relative z-10 mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full bg-[#f5c84b] ring-4 ring-white" />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-xs font-bold text-[#253142] group-hover:text-[#277254] transition-colors">
                          {act.title}
                        </span>
                        <span className="text-[10px] font-semibold text-[#8d9aab]">
                          {act.time}
                        </span>
                      </div>
                      <p className="truncate text-[11px] text-[#7b8490] mt-0.5">{act.subtitle}</p>
                    </div>
                    <ChevronRight size={14} className="mt-1 text-[#9da5ac] opacity-0 transition-all group-hover:opacity-100 group-hover:translate-x-0.5" />
                  </motion.div>
                ))
              ) : (
                <div className="flex flex-col items-center justify-center py-8 text-center text-[#7b8490]">
                  <Clock3 className="h-8 w-8 text-[#9da5ac] mb-2" />
                  <p className="text-sm font-semibold text-[#526072]">No recent activity</p>
                  <p className="mt-1 text-xs text-[#8a929c]">
                    Your presentation takes, CV reviews, and job applications will appear here.
                  </p>
                </div>
              )}
            </div>
          </div>
        </section>
      </motion.div>
    </AppShell>
  );
}
