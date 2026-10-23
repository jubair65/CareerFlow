import { useState, useEffect } from 'react';
import { useLocation } from 'wouter';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Sparkles,
  Award,
  Mic,
  Eye,
  Activity,
  Layers,
  ArrowUpRight,
  ArrowDownRight,
  Calendar,
  Clock,
  Video as VideoIcon,
  Plus,
  RefreshCw,
  Loader2,
  CheckCircle2,
  ChevronRight,
  Info
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  AreaChart,
  Area
} from 'recharts';
import {
  apiGetPresentationScoreTrends,
  type ScoreTrendsResponse,
  type ScoreTrendPoint
} from '../../api/presentation';
import { type Notify } from '../dashboard/DashboardShared';

interface ScoreTrendsDashboardProps {
  notify?: Notify;
  onSelectAttempt?: (videoId: number) => void;
}

type ChartViewMode = 'OVERALL' | 'CATEGORIES' | 'SPEECH_BREAKDOWN' | 'BEHAVIORAL_BREAKDOWN' | 'ALL';

export function ScoreTrendsDashboard({ notify, onSelectAttempt }: ScoreTrendsDashboardProps) {
  const [, setLocation] = useLocation();
  const [trendsData, setTrendsData] = useState<ScoreTrendsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [viewMode, setViewMode] = useState<ChartViewMode>('OVERALL');
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchTrends = async (showToast = false) => {
    try {
      if (showToast) setIsRefreshing(true);
      const data = await apiGetPresentationScoreTrends();
      setTrendsData(data);
      if (showToast && notify) {
        notify('Score trends updated successfully.', 'success');
      }
    } catch (err: any) {
      console.error('Failed to fetch presentation trends:', err);
      if (notify) {
        notify('Failed to load score trends.', 'error');
      }
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchTrends();
  }, []);

  if (isLoading) {
    return (
      <div className="rounded-2xl border border-[#d9dbd1] bg-white p-12 text-center space-y-4 shadow-xs">
        <Loader2 className="w-9 h-9 text-[#277254] animate-spin mx-auto" />
        <h3 className="text-base font-semibold text-[#253142]">Aggregating Historical Score Curves...</h3>
        <p className="text-xs text-[#687382] max-w-sm mx-auto">
          Synthesizing performance progression, acoustic vocal dynamics, and visual presence across attempts.
        </p>
      </div>
    );
  }

  const totalAttempts = trendsData?.total_attempts ?? 0;
  const trendPoints = trendsData?.trend_points ?? [];
  const improvements = trendsData?.improvements;
  const summary = trendsData?.summary;
  const highlights = trendsData?.highlights ?? [];

  // ==========================================
  // CASE 1: ZERO ATTEMPTS (US-17-T5)
  // ==========================================
  if (totalAttempts === 0) {
    return (
      <div
        data-testid="trends-zero-state"
        className="rounded-2xl border border-[#d9dbd1] bg-white p-8 sm:p-12 text-center space-y-6 shadow-xs relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-64 h-64 bg-[#e2f0e9]/40 rounded-full blur-3xl pointer-events-none" />

        <div className="w-16 h-16 rounded-2xl bg-[#e2f0e9] border border-[#b8d8c7] flex items-center justify-center mx-auto text-[#277254]">
          <TrendingUp className="w-8 h-8" />
        </div>

        <div className="space-y-2 max-w-md mx-auto">
          <h3 className="text-xl font-bold text-[#253142] tracking-tight">
            No Presentation Takes Recorded Yet
          </h3>
          <p className="text-sm text-[#687382] leading-relaxed">
            Record or upload your first presentation practice take to begin tracking your improvement curve across speaking pace, filler control, and eye contact.
          </p>
        </div>

        <div className="pt-2">
          <button
            onClick={() => setLocation('/student/practice')}
            data-testid="button-start-first-trend-take"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#253142] hover:bg-[#33435a] text-white font-semibold text-sm transition-all shadow-sm cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            Record Your First Practice Take
          </button>
        </div>
      </div>
    );
  }

  // ==========================================
  // CASE 2: SINGLE ATTEMPT BASELINE (US-17-T5)
  // ==========================================
  if (totalAttempts === 1 && trendPoints.length === 1) {
    const baseline = trendPoints[0];
    return (
      <div data-testid="trends-single-baseline-state" className="space-y-6">
        <div className="rounded-2xl border border-[#d9dbd1] bg-white p-6 sm:p-8 space-y-6 shadow-xs relative overflow-hidden">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#ecefe7] pb-5">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-xl bg-[#e2f0e9] border border-[#b8d8c7] flex items-center justify-center text-[#277254]">
                <Award className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-semibold uppercase tracking-wider text-[#277254]">
                  Baseline Take Registered
                </span>
                <h3 className="text-lg font-bold text-[#253142]">
                  First Attempt: {baseline.overall} / 100 ({baseline.grade_label})
                </h3>
              </div>
            </div>

            <button
              onClick={() => setLocation('/student/practice')}
              data-testid="button-upload-second-take-cta"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#253142] hover:bg-[#33435a] text-white text-xs font-semibold transition-all shadow-sm cursor-pointer self-start sm:self-auto"
            >
              <Plus className="w-3.5 h-3.5" />
              Record Second Attempt to Unlock Trends
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] p-4">
              <span className="text-xs text-[#687382] uppercase font-semibold">Overall Composite</span>
              <p className="text-2xl font-bold text-[#253142] mt-1">{baseline.overall} / 100</p>
              <span className="text-xs text-[#277254]">Baseline benchmark</span>
            </div>

            <div className="rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] p-4">
              <span className="text-xs text-[#687382] uppercase font-semibold flex items-center gap-1.5">
                <Mic className="w-3.5 h-3.5 text-[#3a6384]" /> Speech Dynamics
              </span>
              <p className="text-2xl font-bold text-[#253142] mt-1">{baseline.speech} / 100</p>
              <span className="text-xs text-[#687382]">{baseline.words_per_minute || 0} WPM • {baseline.filler_word_count || 0} fillers</span>
            </div>

            <div className="rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] p-4">
              <span className="text-xs text-[#687382] uppercase font-semibold flex items-center gap-1.5">
                <Eye className="w-3.5 h-3.5 text-[#9a7922]" /> Visual Presence
              </span>
              <p className="text-2xl font-bold text-[#253142] mt-1">{baseline.behavioral} / 100</p>
              <span className="text-xs text-[#687382]">Eye Contact: {baseline.eye_contact}% • Posture: {baseline.posture}%</span>
            </div>
          </div>

          <div className="rounded-xl border border-[#d9dbd1] bg-[#f4f6ef] p-4 flex items-start gap-3">
            <Info className="w-5 h-5 text-[#277254] shrink-0 mt-0.5" />
            <div className="text-xs text-[#526072] leading-relaxed">
              <strong>Unlock Your Improvement Curve:</strong> A minimum of 2 practice takes is required to chart historical score trajectories. Take a second practice round right now to see your pace, eye contact, and overall progression!
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ==========================================
  // CASE 3: MULTI-ATTEMPT TRENDS DASHBOARD (US-17-T1, T3, T4)
  // ==========================================

  // Custom Recharts Tooltip — light mode
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const point = payload[0].payload as ScoreTrendPoint;
      return (
        <div className="bg-white border border-[#d9dbd1] shadow-xl rounded-xl p-3.5 text-xs text-[#253142] space-y-2 min-w-[210px]">
          <div className="flex items-center justify-between border-b border-[#ecefe7] pb-1.5">
            <span className="font-bold text-[#277254]">Attempt #{point.attempt}</span>
            <span className="text-[#687382] flex items-center gap-1">
              <Calendar className="w-3 h-3" /> {point.formatted_date}
            </span>
          </div>

          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-[#687382]">Overall Score:</span>
              <span className="font-bold text-[#277254]">{point.overall} / 100</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[#687382]">Speech Score:</span>
              <span className="font-bold text-[#3a6384]">{point.speech} / 100</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[#687382]">Behavioral Score:</span>
              <span className="font-bold text-[#9a7922]">{point.behavioral} / 100</span>
            </div>
            {point.words_per_minute && (
              <div className="flex items-center justify-between pt-1 border-t border-[#ecefe7] text-[#687382]">
                <span>Pace / Fillers:</span>
                <span>{point.words_per_minute} WPM ({point.filler_word_count || 0} fillers)</span>
              </div>
            )}
          </div>

          <p className="text-[10px] text-[#98a09c] truncate pt-1 border-t border-[#ecefe7]">
            {point.original_filename}
          </p>
        </div>
      );
    }
    return null;
  };

  const overallDeltaNum = improvements?.overall_diff_points ?? 0;
  const isOverallPositive = overallDeltaNum >= 0;

  return (
    <div data-testid="score-trends-dashboard" className="space-y-6">
      {/* 1. Header Trajectory & Progress Banner (US-17-T1) */}
      <div className="rounded-2xl border border-[#d9dbd1] bg-white p-6 sm:p-7 relative overflow-hidden shadow-xs">
        <div className="absolute top-0 right-0 w-72 h-72 bg-[#e2f0e9]/30 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#e2f0e9] text-[#277254] border border-[#b8d8c7]">
                Progress Trajectory
              </span>
              <span className="text-xs text-[#687382] flex items-center gap-1">
                Across {totalAttempts} Recorded Attempts
              </span>
            </div>

            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#253142] tracking-tight flex items-center gap-3">
              Performance Improvement Curve
              <button
                onClick={() => fetchTrends(true)}
                disabled={isRefreshing}
                title="Refresh score progression data"
                className="p-1.5 rounded-lg border border-[#d9dbd1] bg-[#f4f6ef] hover:bg-[#ecefe7] text-[#687382] hover:text-[#253142] transition cursor-pointer"
              >
                <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              </button>
            </h2>

            {/* Improvement highlights badges (US-17-T4) */}
            <div className="flex flex-wrap items-center gap-2 pt-1">
              {highlights.map((hl, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-[#e2f0e9] text-[#277254] border border-[#b8d8c7]"
                >
                  <Sparkles className="w-3.5 h-3.5 text-[#277254]" />
                  {hl}
                </span>
              ))}
            </div>
          </div>

          {/* Large Delta Widget */}
          <div className="flex items-center gap-4 bg-[#fbfaf5] border border-[#d9dbd1] rounded-2xl p-4 sm:px-6 shadow-xs shrink-0">
            <div className="text-right">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-[#687382]">Total Delta</p>
              <p className="text-xs font-medium text-[#526072]">Attempt 1 → {totalAttempts}</p>
            </div>
            <div
              className={`flex items-center gap-1.5 px-4 py-2 rounded-xl font-black text-xl shadow-xs ${
                isOverallPositive
                  ? 'bg-[#e2f0e9] text-[#277254] border border-[#b8d8c7]'
                  : 'bg-[#fee2e2] text-[#dc2626] border border-[#fca5a5]'
              }`}
            >
              {isOverallPositive ? (
                <ArrowUpRight className="w-5 h-5 text-[#277254]" />
              ) : (
                <ArrowDownRight className="w-5 h-5 text-[#dc2626]" />
              )}
              {improvements?.overall_delta || '+0%'}
            </div>
          </div>
        </div>

        {/* 4 Summary Stat Widgets (US-17-T1) */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mt-6 pt-6 border-t border-[#ecefe7]">
          <div className="rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] p-3.5">
            <span className="text-[11px] uppercase font-semibold text-[#687382]">Latest Take</span>
            <p className="text-xl sm:text-2xl font-bold text-[#253142] mt-1">
              {summary?.latest_score} <span className="text-xs text-[#687382] font-normal">/ 100</span>
            </p>
            <span className="text-[11px] text-[#277254]">Attempt #{totalAttempts}</span>
          </div>

          <div className="rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] p-3.5">
            <span className="text-[11px] uppercase font-semibold text-[#687382]">Personal Best</span>
            <p className="text-xl sm:text-2xl font-bold text-[#277254] mt-1">
              {summary?.highest_score} <span className="text-xs text-[#687382] font-normal">/ 100</span>
            </p>
            <span className="text-[11px] text-[#277254]">Peak achievement</span>
          </div>

          <div className="rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] p-3.5">
            <span className="text-[11px] uppercase font-semibold text-[#687382]">Average Score</span>
            <p className="text-xl sm:text-2xl font-bold text-[#253142] mt-1">
              {summary?.average_score} <span className="text-xs text-[#687382] font-normal">/ 100</span>
            </p>
            <span className="text-[11px] text-[#687382]">Mean across reps</span>
          </div>

          <div className="rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] p-3.5">
            <span className="text-[11px] uppercase font-semibold text-[#687382]">Baseline Take</span>
            <p className="text-xl sm:text-2xl font-bold text-[#526072] mt-1">
              {summary?.first_score} <span className="text-xs text-[#687382] font-normal">/ 100</span>
            </p>
            <span className="text-[11px] text-[#687382]">Starting benchmark</span>
          </div>
        </div>
      </div>

      {/* 2. Chart View Controller & Recharts Graph (US-17-T3 & US-17-T4) */}
      <div className="rounded-2xl border border-[#d9dbd1] bg-white p-6 sm:p-7 space-y-6 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#ecefe7] pb-4">
          <div>
            <h3 className="text-base font-bold text-[#253142] flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-[#277254]" />
              Progression Trajectory
            </h3>
            <p className="text-xs text-[#687382]">
              Hover over points to inspect individual session scores and timestamps
            </p>
          </div>

          {/* Toggleable Chart Series Pills (US-17-T4) */}
          <div className="flex flex-wrap items-center gap-1.5 bg-[#f4f6ef] p-1 rounded-xl border border-[#d9dbd1] self-start sm:self-auto">
            <button
              type="button"
              onClick={() => setViewMode('OVERALL')}
              data-testid="toggle-chart-overall"
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
                viewMode === 'OVERALL'
                  ? 'bg-[#253142] text-white shadow-xs'
                  : 'text-[#687382] hover:text-[#253142]'
              }`}
            >
              Overall
            </button>
            <button
              type="button"
              onClick={() => setViewMode('CATEGORIES')}
              data-testid="toggle-chart-categories"
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
                viewMode === 'CATEGORIES'
                  ? 'bg-[#253142] text-white shadow-xs'
                  : 'text-[#687382] hover:text-[#253142]'
              }`}
            >
              Speech vs. Behavioral
            </button>
            <button
              type="button"
              onClick={() => setViewMode('SPEECH_BREAKDOWN')}
              data-testid="toggle-chart-speech"
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
                viewMode === 'SPEECH_BREAKDOWN'
                  ? 'bg-[#253142] text-white shadow-xs'
                  : 'text-[#687382] hover:text-[#253142]'
              }`}
            >
              Vocal Dynamics
            </button>
            <button
              type="button"
              onClick={() => setViewMode('BEHAVIORAL_BREAKDOWN')}
              data-testid="toggle-chart-behavioral"
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
                viewMode === 'BEHAVIORAL_BREAKDOWN'
                  ? 'bg-[#253142] text-white shadow-xs'
                  : 'text-[#687382] hover:text-[#253142]'
              }`}
            >
              Visual Presence
            </button>
            <button
              type="button"
              onClick={() => setViewMode('ALL')}
              data-testid="toggle-chart-all"
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
                viewMode === 'ALL'
                  ? 'bg-[#253142] text-white shadow-xs'
                  : 'text-[#687382] hover:text-[#253142]'
              }`}
            >
              All Curves
            </button>
          </div>
        </div>

        {/* Recharts Container */}
        <div className="w-full h-72 sm:h-80" data-testid="recharts-line-container">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={trendPoints}
              margin={{ top: 10, right: 20, left: -15, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#ecefe7" vertical={false} />
              <XAxis
                dataKey="attempt"
                stroke="#687382"
                fontSize={12}
                tickLine={false}
                tickFormatter={(value) => `Take #${value}`}
              />
              <YAxis
                domain={[40, 100]}
                stroke="#687382"
                fontSize={12}
                tickLine={false}
                tickCount={6}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                verticalAlign="bottom"
                height={36}
                wrapperStyle={{ fontSize: '12px', paddingTop: '10px', color: '#687382' }}
              />

              {/* OVERALL VIEW */}
              {(viewMode === 'OVERALL' || viewMode === 'ALL') && (
                <Line
                  type="monotone"
                  dataKey="overall"
                  name="Overall Score"
                  stroke="#277254"
                  strokeWidth={3}
                  dot={{ r: 5, fill: '#277254', stroke: '#ffffff', strokeWidth: 2 }}
                  activeDot={{ r: 7, fill: '#277254', stroke: '#e2f0e9', strokeWidth: 3 }}
                />
              )}

              {/* CATEGORIES VIEW */}
              {(viewMode === 'CATEGORIES' || viewMode === 'ALL') && (
                <>
                  <Line
                    type="monotone"
                    dataKey="speech"
                    name="Speech Score"
                    stroke="#3a6384"
                    strokeWidth={2.5}
                    dot={{ r: 4, fill: '#3a6384', stroke: '#ffffff', strokeWidth: 2 }}
                    activeDot={{ r: 6, fill: '#3a6384' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="behavioral"
                    name="Behavioral Score"
                    stroke="#b89c3b"
                    strokeWidth={2.5}
                    dot={{ r: 4, fill: '#b89c3b', stroke: '#ffffff', strokeWidth: 2 }}
                    activeDot={{ r: 6, fill: '#b89c3b' }}
                  />
                </>
              )}

              {/* VOCAL DYNAMICS BREAKDOWN */}
              {viewMode === 'SPEECH_BREAKDOWN' && (
                <>
                  <Line
                    type="monotone"
                    dataKey="pace_score"
                    name="Pacing Cadence"
                    stroke="#3a6384"
                    strokeWidth={2}
                    dot={{ r: 4, fill: '#3a6384' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="filler_score"
                    name="Filler Word Control"
                    stroke="#dc2626"
                    strokeWidth={2}
                    dot={{ r: 4, fill: '#dc2626' }}
                  />
                </>
              )}

              {/* BEHAVIORAL BREAKDOWN */}
              {viewMode === 'BEHAVIORAL_BREAKDOWN' && (
                <>
                  <Line
                    type="monotone"
                    dataKey="eye_contact_score"
                    name="Eye Contact"
                    stroke="#b89c3b"
                    strokeWidth={2}
                    dot={{ r: 4, fill: '#b89c3b' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="posture_score"
                    name="Posture Stability"
                    stroke="#277254"
                    strokeWidth={2}
                    dot={{ r: 4, fill: '#277254' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="engagement_score"
                    name="Expressive Engagement"
                    stroke="#3a6384"
                    strokeWidth={2}
                    dot={{ r: 4, fill: '#3a6384' }}
                  />
                </>
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 3. Chronological Milestone Take Cards */}
      <div className="rounded-2xl border border-[#d9dbd1] bg-white p-6 sm:p-7 space-y-4 shadow-xs">
        <h3 className="text-base font-bold text-[#253142] flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-[#277254]" />
            Historical Take Milestones
          </span>
          <span className="text-xs text-[#687382] font-normal">
            Chronological progression from baseline
          </span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5 pt-2">
          {trendPoints.map((point) => {
            const isBaseline = point.attempt === 1;
            const diffFromBaseline = point.overall - trendPoints[0].overall;

            return (
              <div
                key={point.attempt}
                data-testid={`milestone-take-card-${point.attempt}`}
                onClick={() => {
                  if (onSelectAttempt) {
                    onSelectAttempt(point.video_id);
                  } else {
                    setLocation(`/presentation/history/${point.video_id}`);
                  }
                }}
                className="bg-[#fbfaf5] hover:bg-[#f4f6ef] border border-[#d9dbd1] hover:border-[#b8d8c7] rounded-xl p-4 transition-all duration-150 cursor-pointer space-y-3 group"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-[#e2f0e9] text-[#277254] border border-[#b8d8c7]">
                      Take #{point.attempt}
                    </span>
                    <span className="text-xs text-[#687382]">{point.formatted_date}</span>
                  </div>

                  <span className="text-sm font-extrabold text-[#253142] flex items-center gap-1">
                    {point.overall} <span className="text-[10px] text-[#687382]">/ 100</span>
                  </span>
                </div>

                <div className="text-xs text-[#526072] truncate font-mono">
                  {point.original_filename}
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-[#ecefe7] text-xs">
                  <span className="text-[#687382]">
                    {isBaseline ? (
                      <span className="text-[#277254] font-medium">Starting Baseline</span>
                    ) : diffFromBaseline >= 0 ? (
                      <span className="text-[#277254] font-semibold flex items-center gap-1">
                        <ArrowUpRight className="w-3.5 h-3.5" /> +{diffFromBaseline}% vs baseline
                      </span>
                    ) : (
                      <span className="text-[#dc2626] font-semibold flex items-center gap-1">
                        <ArrowDownRight className="w-3.5 h-3.5" /> {diffFromBaseline}% vs baseline
                      </span>
                    )}
                  </span>

                  <span className="inline-flex items-center gap-0.5 text-[#277254] group-hover:translate-x-0.5 transition-transform text-xs font-semibold">
                    View <ChevronRight className="w-3.5 h-3.5" />
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default ScoreTrendsDashboard;
