import { useMemo, useState, useEffect } from 'react';
import { useLocation } from 'wouter';
import {
  Presentation,
  FileText,
  Target,
  BriefcaseBusiness,
  Play,
  ArrowRight,
  ChevronRight,
  Sparkles,
  Clock3,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import {
  PageHeading,
  StatCard,
  Chart,
  type Notify,
} from '../components/dashboard/DashboardShared';
import { getStoredUser } from '../api/auth';
import { apiGetCurrentCVFeedback, type CVFeedback } from '../api/cv';
import { apiGetPresentationScoreTrends, type ScoreTrendsResponse } from '../api/presentation';
import { apiGetMyApplications, type ApplicantApplicationStatus } from '../api/recruitment';

interface ActivityItem {
  id: string;
  title: string;
  subtitle: string;
  time: string;
  timestamp: number;
}

export function StudentDashboard({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();
  const [cvFeedback, setCvFeedback] = useState<CVFeedback | null>(null);
  const [trendsData, setTrendsData] = useState<ScoreTrendsResponse | null>(null);
  const [applications, setApplications] = useState<ApplicantApplicationStatus[]>([]);
  const [, setLoading] = useState(true);

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
  }, []);

  const userName = user?.full_name?.split(' ')[0] || user?.user?.split(' ')[0] || 'Candidate';

  // 1. Presentation Score
  const latestPresentationScore = trendsData?.summary?.latest_score;
  const presentationScoreValue = latestPresentationScore != null ? String(latestPresentationScore) : '--';
  const presentationScoreDetail = latestPresentationScore != null
    ? (trendsData?.improvements?.overall_delta && trendsData.improvements.overall_delta !== '+0%')
      ? `${trendsData.improvements.overall_delta} vs baseline`
      : 'Latest take score'
    : 'No practice attempts yet';

  // 2. CV Score
  const cvScoreValue = cvFeedback?.overall_score != null ? String(cvFeedback.overall_score) : '--';
  const cvScoreDetail = cvFeedback
    ? cvFeedback.overall_score >= 85
      ? 'Strong role alignment'
      : cvFeedback.overall_score >= 70
      ? 'Good potential'
      : 'Needs revision'
    : 'Upload CV in Studio';

  // 3. Practice Attempts
  const totalAttempts = trendsData?.total_attempts ?? 0;
  const practiceAttemptsValue = String(totalAttempts);
  const attemptsThisWeek = useMemo(() => {
    if (!trendsData?.trend_points?.length) return 0;
    const oneWeekAgo = new Date();
    oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
    return trendsData.trend_points.filter((p) => {
      const timestamp = p.timestamp ? new Date(p.timestamp) : null;
      return timestamp && timestamp >= oneWeekAgo;
    }).length;
  }, [trendsData]);

  const practiceAttemptsDetail = totalAttempts > 0
    ? attemptsThisWeek > 0
      ? `${attemptsThisWeek} this week`
      : `${totalAttempts} total take${totalAttempts > 1 ? 's' : ''}`
    : 'Start your first practice';

  // 4. Applications
  const applicationsCount = applications.length;
  const applicationsValue = String(applicationsCount);
  const inReviewCount = applications.filter(
    (a) =>
      a.status === 'UNDER_REVIEW' ||
      a.current_stage === 'HR_REVIEW' ||
      a.current_stage === 'SUBMITTED' ||
      a.current_stage === 'AI_ANALYSIS'
  ).length;

  const applicationsDetail = applicationsCount > 0
    ? inReviewCount > 0
      ? `${inReviewCount} in review`
      : `${applicationsCount} submitted`
    : 'No applications yet';

  // Confidence over time chart
  const chartPoints = useMemo(() => {
    if (!trendsData?.trend_points || trendsData.trend_points.length === 0) {
      return { values: [], labels: [] };
    }
    const slice = trendsData.trend_points.slice(-8);
    return {
      values: slice.map((p) => p.overall_score),
      labels: slice.map((p, idx) =>
        p.formatted_date ? p.formatted_date.replace(/, \d{4}$/, '') : `Take ${idx + 1}`
      ),
    };
  }, [trendsData]);

  // AI Recommendation
  const aiRecommendation = useMemo(() => {
    if (trendsData?.highlights && trendsData.highlights.length > 0) {
      return {
        title: 'Refine your delivery.',
        text: trendsData.highlights[0],
        action: 'Practice presentation',
        path: '/student/presentation',
      };
    }
    if (cvFeedback?.suggestions && cvFeedback.suggestions.length > 0) {
      return {
        title: 'Strengthen your CV.',
        text: cvFeedback.suggestions[0],
        action: 'View CV suggestions',
        path: '/student/cv/results',
      };
    }
    return {
      title: 'Start your preparation.',
      text: 'Upload your CV to extract matching skills and record a presentation take to receive tailored delivery analytics.',
      action: 'Try presentation practice',
      path: '/student/presentation',
    };
  }, [trendsData, cvFeedback]);

  // Recent Activities
  const recentActivities = useMemo<ActivityItem[]>(() => {
    const items: ActivityItem[] = [];

    applications.forEach((app) => {
      items.push({
        id: `app-${app.id}`,
        title: 'Application submitted',
        subtitle: `${app.room_title || 'Recruitment Room'}${app.company_name ? ` • ${app.company_name}` : ''}${
          app.badge?.label ? ` (${app.badge.label})` : ''
        }`,
        time: app.applied_at
          ? new Date(app.applied_at).toLocaleDateString([], { month: 'short', day: 'numeric' })
          : 'Recently',
        timestamp: app.applied_at ? new Date(app.applied_at).getTime() : 0,
      });
    });

    (trendsData?.trend_points || []).forEach((p, idx) => {
      items.push({
        id: `pres-${p.video_id || idx}`,
        title: 'Presentation analyzed',
        subtitle: `Take #${p.attempt} scored ${p.overall_score}/100 • ${p.grade_label}`,
        time:
          p.formatted_date ||
          (p.timestamp
            ? new Date(p.timestamp).toLocaleDateString([], { month: 'short', day: 'numeric' })
            : 'Recently'),
        timestamp: p.timestamp ? new Date(p.timestamp).getTime() : 0,
      });
    });

    if (cvFeedback) {
      items.push({
        id: `cv-${cvFeedback.id}`,
        title: 'CV reviewed',
        subtitle: `${cvFeedback.overall_score}/100 overall score • ${cvFeedback.original_filename || 'Uploaded Resume'}`,
        time: cvFeedback.updated_at
          ? new Date(cvFeedback.updated_at).toLocaleDateString([], { month: 'short', day: 'numeric' })
          : 'Recently',
        timestamp: new Date(cvFeedback.updated_at || cvFeedback.created_at || 0).getTime(),
      });
    }

    items.sort((a, b) => b.timestamp - a.timestamp);
    return items.slice(0, 4);
  }, [applications, trendsData, cvFeedback]);

  return (
    <AppShell role="student" notify={notify}>
      <PageHeading
        title={`Good morning, ${userName}.`}
        description="You are building a stronger case for yourself, one small action at a time."
        action={
          <button
            type="button"
            onClick={() => setLocation('/student/presentation')}
            data-testid="button-dashboard-practice"
            className="inline-flex items-center gap-2 rounded-xl bg-[#e2f0e9] px-4 py-2.5 text-sm font-bold text-[#277254] hover:bg-[#d2e7dc] transition"
          >
            <Play size={16} /> Practice now
          </button>
        }
      />

      {/* 4 Metric Cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div
          onClick={() => setLocation('/student/presentation')}
          className="cursor-pointer transition hover:scale-[1.01]"
          title="Click to view Presentation Studio"
        >
          <StatCard
            label="Presentation score"
            value={presentationScoreValue}
            detail={presentationScoreDetail}
            icon={Presentation}
            accent="yellow"
          />
        </div>
        <div
          onClick={() => setLocation('/student/cv/results')}
          className="cursor-pointer transition hover:scale-[1.01]"
          title="Click to view CV Feedback & Scoring"
        >
          <StatCard
            label="CV score"
            value={cvScoreValue}
            detail={cvScoreDetail}
            icon={FileText}
            accent="green"
          />
        </div>

        <div
          onClick={() => setLocation('/student/videos')}
          className="cursor-pointer transition hover:scale-[1.01]"
          data-testid="card-practice-attempts"
        >
          <StatCard
            label="Practice attempts"
            value={practiceAttemptsValue}
            detail={practiceAttemptsDetail}
            icon={Target}
            accent="blue"
          />
        </div>
        <div
          onClick={() => setLocation('/student/applications')}
          className="cursor-pointer transition hover:scale-[1.01]"
          data-testid="card-applications-status"
        >
          <StatCard
            label="Applications"
            value={applicationsValue}
            detail={applicationsDetail}
            icon={BriefcaseBusiness}
            accent="coral"
          />
        </div>
      </div>

      {/* Confidence Chart & AI Recommendation */}
      <div className="mt-5 grid gap-5 xl:grid-cols-[1.35fr_.65fr]">
        <section className="cf-card rounded-2xl bg-white p-5 md:p-6 border border-[#d9dbd1] shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="font-bold text-[#253142] text-lg">Confidence over time</h2>
              <p className="mt-1 text-xs text-[#7b8490]">Your average practice take score</p>
            </div>
            <button
              type="button"
              onClick={() => setLocation('/presentation/trends')}
              data-testid="link-dashboard-progress"
              className="flex items-center gap-1 text-xs font-bold text-[#277254] hover:underline"
            >
              View progress <ChevronRight size={14} />
            </button>
          </div>
          <div className="mt-6">
            {chartPoints.values.length > 0 ? (
              <Chart values={chartPoints.values} labels={chartPoints.labels} />
            ) : (
              <div className="flex h-44 flex-col items-center justify-center rounded-xl border border-dashed border-[#d9dbd1] bg-[#faf8f2] p-6 text-center">
                <Presentation className="h-7 w-7 text-[#9da5ac] mb-2" />
                <p className="text-sm font-semibold text-[#526072]">No practice sessions recorded yet</p>
                <p className="mt-1 text-xs text-[#8a929c]">
                  Record your first presentation take to start tracking your confidence trend over time.
                </p>
                <button
                  type="button"
                  onClick={() => setLocation('/student/presentation')}
                  className="mt-3 inline-flex items-center gap-1.5 text-xs font-bold text-[#277254] hover:underline"
                >
                  Start practice take →
                </button>
              </div>
            )}
          </div>
        </section>

        <section className="rounded-2xl bg-[#277254] p-6 text-[#f8f4e9] shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-[.12em] text-[#b9dec6]">
                AI recommendation
              </span>
              <Sparkles size={19} className="text-[#f5c84b]" />
            </div>
            <h2 className="cf-display mt-6 text-2xl font-bold">{aiRecommendation.title}</h2>
            <p className="mt-3 text-sm leading-6 text-[#d5e8da]">
              {aiRecommendation.text}
            </p>
          </div>
          <button
            type="button"
            onClick={() => setLocation(aiRecommendation.path)}
            data-testid="button-ai-recommendation"
            className="mt-6 inline-flex w-fit items-center gap-2 rounded-xl bg-[#e2f0e9] px-4 py-2.5 text-xs font-bold text-[#277254] hover:bg-[#d2e7dc] transition"
          >
            {aiRecommendation.action} <ArrowRight size={15} />
          </button>
        </section>
      </div>

      {/* Next Actions & Recent Activity */}
      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <section className="cf-card rounded-2xl bg-white p-5 md:p-6 border border-[#d9dbd1] shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="font-bold text-[#253142] text-lg">Your next actions</h2>
            <button
              type="button"
              onClick={() => setLocation('/student/presentation')}
              data-testid="button-view-all-actions"
              className="text-xs font-bold text-[#277254] hover:underline"
            >
              View all
            </button>
          </div>
          <div className="mt-4 space-y-2.5">
            <button
              type="button"
              onClick={() => setLocation('/student/presentation')}
              data-testid="action-practice-intro"
              className="flex w-full items-center gap-3 rounded-xl bg-[#fbfaf5] border border-[#eef0e7] p-3.5 text-left hover:bg-[#fff1c9] transition"
            >
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#fff1c9] text-[#8a6a16]">
                <Presentation size={18} />
              </div>
              <div className="flex-1">
                <div className="text-sm font-bold text-[#253142]">
                  {totalAttempts > 0 ? 'Continue presentation practice' : 'Practice your introduction'}
                </div>
                <div className="text-xs text-[#7b8490]">
                  {totalAttempts > 0
                    ? `Latest score: ${latestPresentationScore ?? 0}/100 • Target: 90+`
                    : 'Record video • Instant speech & behavioral feedback'}
                </div>
              </div>
              <ChevronRight size={17} className="text-[#9da5ac]" />
            </button>

            <button
              type="button"
              onClick={() => setLocation(cvFeedback ? '/student/cv/results' : '/student/cv')}
              data-testid="action-review-cv"
              className="flex w-full items-center gap-3 rounded-xl bg-[#fbfaf5] border border-[#eef0e7] p-3.5 text-left hover:bg-[#e2f0e9] transition"
            >
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#e2f0e9] text-[#277254]">
                <FileText size={18} />
              </div>
              <div className="flex-1">
                <div className="text-sm font-bold text-[#253142]">
                  {cvFeedback ? 'Review your CV suggestions' : 'Upload your CV in CV Studio'}
                </div>
                <div className="text-xs text-[#7b8490]">
                  {cvFeedback
                    ? `${cvFeedback.suggestions?.length || 0} improvement${
                        (cvFeedback.suggestions?.length || 0) === 1 ? '' : 's'
                      } waiting in CV Studio`
                    : 'Get instant ATS scoring and keyword analysis'}
                </div>
              </div>
              <ChevronRight size={17} className="text-[#9da5ac]" />
            </button>
          </div>
        </section>

        <section className="cf-card rounded-2xl bg-white p-5 md:p-6 border border-[#d9dbd1] shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="font-bold text-[#253142] text-lg">Recent activity</h2>
            <Clock3 size={17} className="text-[#9aa2a9]" />
          </div>
          <div className="mt-4 space-y-4">
            {recentActivities.length > 0 ? (
              recentActivities.map((act) => (
                <div key={act.id} className="flex gap-3">
                  <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-[#f5c84b]" />
                  <div>
                    <div className="text-sm font-bold text-[#253142]">{act.title}</div>
                    <div className="text-xs text-[#7b8490]">{act.subtitle}</div>
                    <div className="mt-0.5 text-[10px] font-semibold uppercase tracking-wide text-[#a0a7ad]">
                      {act.time}
                    </div>
                  </div>
                </div>
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
        </section>
      </div>
    </AppShell>
  );
}
