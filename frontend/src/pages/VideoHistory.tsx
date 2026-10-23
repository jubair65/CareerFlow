import { useState, useEffect, useMemo } from 'react';
import { useLocation } from 'wouter';
import {
  Play,
  ExternalLink,
  Sparkles,
  Trash2,
  Plus,
  Video as VideoIcon,
  Clock,
  HardDrive,
  X,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Activity,
  Mic,
  Eye,
  Smile,
  Search,
  Filter,
  ArrowUpDown,
  Award,
  TrendingUp,
  BarChart2,
  Copy,
  Check
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import { type Notify } from '../components/dashboard/DashboardShared';
import {
  apiGetPresentationVideoHistory,
  apiGetPresentationVideoDetail,
  apiDeletePresentationVideo,
  apiGetSpeechAnalysis,
  apiGetBehavioralAnalysis,
  apiTriggerSpeechAnalysis,
  apiTriggerBehavioralAnalysis,
  type PresentationVideo,
  type SpeechAnalysisData,
  type BehavioralAnalysisData
} from '../api/presentation';
import { WebcamPlaybackPlayer } from '../components/presentation/WebcamPlaybackPlayer';
import { PresentationScoreCard } from '../components/presentation/PresentationScoreCard';
import { SuggestionsList } from '../components/presentation/SuggestionsList';
import { PipelineStatusAlert } from '../components/presentation/PipelineStatusAlert';
import { ScoreTrendsDashboard } from '../components/presentation/ScoreTrendsDashboard';

export function VideoHistory({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();
  const [videoHistory, setVideoHistory] = useState<PresentationVideo[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // US-17 Tab: 'takes' (History list) vs 'trends' (Analytics & Progress curves)
  const [activeMainTab, setActiveMainTab] = useState<'takes' | 'trends'>('takes');

  // Filter & Search Controls (US-16-T3)
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'COMPLETED' | 'PROCESSING' | 'FAILED'>('ALL');
  const [sortBy, setSortBy] = useState<'NEWEST' | 'OLDEST' | 'SCORE_HIGH' | 'SCORE_LOW' | 'DURATION'>('NEWEST');

  // Modals state
  const [previewVideo, setPreviewVideo] = useState<PresentationVideo | null>(null);
  const [analysisVideo, setAnalysisVideo] = useState<PresentationVideo | null>(null);
  const [speechData, setSpeechData] = useState<SpeechAnalysisData | null>(null);
  const [behavioralData, setBehavioralData] = useState<BehavioralAnalysisData | null>(null);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [triggeringAnalysis, setTriggeringAnalysis] = useState(false);
  const [isMirroredModal, setIsMirroredModal] = useState(true);
  const [copiedTranscript, setCopiedTranscript] = useState(false);

  const loadHistory = async () => {
    setIsLoading(true);
    try {
      const history = await apiGetPresentationVideoHistory();
      setVideoHistory(history);
    } catch (err: any) {
      console.error('Failed to load video history:', err);
      notify('Failed to load video history.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  // Deep-link query parameter support: ?video=<id> or ?id=<id> (US-16-T4) or ?tab=trends (US-17)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const tabParam = params.get('tab');
    if (tabParam === 'trends') {
      setActiveMainTab('trends');
    }

    const videoIdStr = params.get('video') || params.get('id');
    if (videoIdStr && videoHistory.length > 0) {
      const vid = videoHistory.find((v) => v.id === Number(videoIdStr));
      if (vid && analysisVideo?.id !== vid.id) {
        handleOpenAnalysis(vid);
      }
    }
  }, [videoHistory]);

  const handleDeleteVideo = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this practice take?')) return;
    try {
      await apiDeletePresentationVideo(id);
      notify('Practice take deleted.', 'info');
      setVideoHistory((prev) => prev.filter((v) => v.id !== id));
      if (previewVideo?.id === id) setPreviewVideo(null);
      if (analysisVideo?.id === id) setAnalysisVideo(null);
    } catch (err: any) {
      notify('Failed to delete video.', 'error');
    }
  };

  const handleOpenAnalysis = async (video: PresentationVideo) => {
    setAnalysisVideo(video);
    setLoadingAnalysis(true);
    setSpeechData(video.speech_analysis || null);
    setBehavioralData(video.behavioral_analysis || null);

    try {
      // Re-fetch latest detailed object from backend
      const [detail, speech, behavioral] = await Promise.all([
        apiGetPresentationVideoDetail(video.id).catch(() => video),
        video.speech_analysis ? Promise.resolve(video.speech_analysis) : apiGetSpeechAnalysis(video.id).catch(() => null),
        video.behavioral_analysis ? Promise.resolve(video.behavioral_analysis) : apiGetBehavioralAnalysis(video.id).catch(() => null),
      ]);
      setAnalysisVideo(detail);
      setSpeechData(speech);
      setBehavioralData(behavioral);
    } catch (e) {
      console.warn('Analysis fetch error:', e);
    } finally {
      setLoadingAnalysis(false);
    }
  };

  const handleTriggerAnalysis = async () => {
    if (!analysisVideo) return;
    setTriggeringAnalysis(true);
    try {
      const [speech, behavioral] = await Promise.all([
        apiTriggerSpeechAnalysis(analysisVideo.id).catch(() => null),
        apiTriggerBehavioralAnalysis(analysisVideo.id).catch(() => null),
      ]);
      setSpeechData(speech);
      setBehavioralData(behavioral);
      notify('AI Analysis complete!', 'success');
      loadHistory();
    } catch (err: any) {
      notify(err.response?.data?.error || 'AI Analysis pipeline failed.', 'error');
    } finally {
      setTriggeringAnalysis(false);
    }
  };

  const handleCopyTranscript = () => {
    if (!speechData?.transcript) return;
    navigator.clipboard.writeText(speechData.transcript);
    setCopiedTranscript(true);
    setTimeout(() => setCopiedTranscript(false), 2000);
    notify('Transcript copied to clipboard!', 'success');
  };

  const formatDuration = (seconds: number) => {
    if (!seconds) return '00:00';
    const s = Math.max(0, Math.floor(seconds));
    const mins = Math.floor(s / 60);
    const secs = s % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const formatVideoDate = (isoString: string) => {
    if (!isoString) return '—';
    const date = new Date(isoString);
    const now = new Date();
    const isToday =
      date.getDate() === now.getDate() &&
      date.getMonth() === now.getMonth() &&
      date.getFullYear() === now.getFullYear();

    if (isToday) {
      return `Today, ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    }

    const yesterday = new Date(now);
    yesterday.setDate(now.getDate() - 1);
    const isYesterday =
      date.getDate() === yesterday.getDate() &&
      date.getMonth() === yesterday.getMonth() &&
      date.getFullYear() === yesterday.getFullYear();

    if (isYesterday) {
      return `Yesterday, ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    }

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const getVideoTitle = (video: PresentationVideo) => {
    const raw =
      video.original_filename ||
      (video.file ? video.file.split('/').pop()?.split('\\').pop() : '') ||
      `take_${video.id}`;
    const cleanName = raw.replace(/\.[^/.]+$/, '');
    return cleanName || raw;
  };

  const getVideoScore = (video: PresentationVideo): number | null => {
    if (
      video.presentation_score?.overall_score !== undefined &&
      video.presentation_score?.overall_score !== null
    ) {
      return Math.round(video.presentation_score.overall_score);
    }

    if (video.speech_analysis && video.behavioral_analysis) {
      const speechPart = video.speech_analysis.clarity_score;
      const eyePart = video.behavioral_analysis.eye_contact_score;
      const engagementPart = video.behavioral_analysis.engagement_score;
      const posturePart = video.behavioral_analysis.posture_score;
      const behavioralAvg = (eyePart + engagementPart + posturePart) / 3;
      return Math.round(speechPart * 0.5 + behavioralAvg * 0.5);
    }

    if (
      video.speech_analysis?.clarity_score !== undefined &&
      video.speech_analysis?.clarity_score !== null
    ) {
      return Math.round(video.speech_analysis.clarity_score);
    }

    if (
      video.behavioral_analysis?.engagement_score !== undefined &&
      video.behavioral_analysis?.engagement_score !== null
    ) {
      return Math.round(video.behavioral_analysis.engagement_score);
    }

    return null;
  };

  // Trajectory Summary Stats (US-16-T1)
  const stats = useMemo(() => {
    const total = videoHistory.length;
    const scores = videoHistory
      .map(getVideoScore)
      .filter((s): s is number => s !== null);
    const avgScore = scores.length > 0 ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : null;
    const bestScore = scores.length > 0 ? Math.max(...scores) : null;

    const wpms = videoHistory
      .map((v) => v.speech_analysis?.words_per_minute)
      .filter((w): w is number => typeof w === 'number' && w > 0);
    const avgWpm = wpms.length > 0 ? Math.round(wpms.reduce((a, b) => a + b, 0) / wpms.length) : null;

    return { total, avgScore, bestScore, avgWpm };
  }, [videoHistory]);

  // Filtered and Sorted Video List (US-16-T3 & AC 3)
  const filteredVideos = useMemo(() => {
    return videoHistory
      .filter((video) => {
        if (searchTerm.trim()) {
          const term = searchTerm.toLowerCase();
          const title = getVideoTitle(video).toLowerCase();
          if (!title.includes(term)) return false;
        }

        if (statusFilter !== 'ALL') {
          if (statusFilter === 'COMPLETED') {
            if (video.status !== 'COMPLETED' && getVideoScore(video) === null) return false;
          } else if (statusFilter === 'PROCESSING') {
            if (video.status === 'COMPLETED' || video.status === 'FAILED') return false;
          } else if (statusFilter === 'FAILED') {
            if (video.status !== 'FAILED') return false;
          }
        }

        return true;
      })
      .sort((a, b) => {
        if (sortBy === 'NEWEST') {
          return new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime();
        }
        if (sortBy === 'OLDEST') {
          return new Date(a.uploaded_at).getTime() - new Date(b.uploaded_at).getTime();
        }
        if (sortBy === 'SCORE_HIGH') {
          const sa = getVideoScore(a) ?? -1;
          const sb = getVideoScore(b) ?? -1;
          return sb - sa;
        }
        if (sortBy === 'SCORE_LOW') {
          const sa = getVideoScore(a) ?? 999;
          const sb = getVideoScore(b) ?? 999;
          return sa - sb;
        }
        if (sortBy === 'DURATION') {
          return (b.duration_seconds || 0) - (a.duration_seconds || 0);
        }
        return 0;
      });
  }, [videoHistory, searchTerm, statusFilter, sortBy]);

  return (
    <AppShell role="student" notify={notify}>
      <div className="space-y-6">
        {/* Header Section */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <span
              data-testid="heading-eyebrow"
              className="text-xs font-bold uppercase tracking-[.18em] text-[#b89c3b]"
            >
              PRESENTATION HISTORY
            </span>
            <h1
              data-testid="heading-title"
              className="mt-1 text-3xl sm:text-4xl font-extrabold text-[#253142] tracking-tight"
            >
              Your reps, in one place.
            </h1>
            <p className="mt-1 text-sm text-[#687382]">
              Review past AI feedback, compare presentation metrics, and track speech delivery.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setLocation('/student/practice')}
              data-testid="button-new-practice"
              className="inline-flex items-center gap-2 rounded-xl bg-[#253142] px-5 py-2.5 text-sm font-bold text-white hover:bg-[#33435a] transition shadow-sm cursor-pointer"
            >
              <Plus size={16} />
              <span>New practice</span>
            </button>
          </div>
        </div>

        {/* US-17 Tab Navigation: Video Takes vs Score Trends */}
        <div className="flex items-center justify-between border-b border-[#ecefe7] pb-3">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setActiveMainTab('takes')}
              data-testid="tab-takes-history"
              className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition cursor-pointer ${
                activeMainTab === 'takes'
                  ? 'bg-[#253142] text-white shadow-xs'
                  : 'bg-[#f4f6ef] text-[#687382] hover:text-[#253142]'
              }`}
            >
              <VideoIcon size={16} />
              <span>Video Takes ({videoHistory.length})</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveMainTab('trends')}
              data-testid="tab-score-trends"
              className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition cursor-pointer ${
                activeMainTab === 'trends'
                  ? 'bg-[#253142] text-white shadow-xs'
                  : 'bg-[#f4f6ef] text-[#687382] hover:text-[#253142]'
              }`}
            >
              <TrendingUp size={16} />
              <span>Score Trends & Progress</span>
              <span className="hidden sm:inline-block rounded-full bg-[#e2f0e9] px-2 py-0.5 text-[10px] font-bold text-[#277254]">
                Analytics
              </span>
            </button>
          </div>
        </div>

        {/* Tab 2: Score Trends Dashboard (US-17) */}
        {activeMainTab === 'trends' && (
          <ScoreTrendsDashboard
            notify={notify}
            onSelectAttempt={(vidId) => {
              const vid = videoHistory.find((v) => v.id === vidId);
              if (vid) handleOpenAnalysis(vid);
            }}
          />
        )}

        {/* Tab 1: Video Takes List & Overview (US-16) */}
        {activeMainTab === 'takes' && (
          <div className="space-y-6">
            {/* Overview Trajectory Summary Cards (US-16-T1) */}
            {videoHistory.length > 0 && (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {/* Total Takes */}
            <div className="rounded-2xl border border-[#d9dbd1] bg-white p-4 shadow-xs">
              <div className="flex items-center justify-between text-xs font-semibold text-[#687382]">
                <span>Total Reps</span>
                <VideoIcon size={16} className="text-[#253142]" />
              </div>
              <p className="mt-2 text-2xl font-bold text-[#253142]" data-testid="stat-total-takes">
                {stats.total}
              </p>
              <span className="text-[11px] text-[#687382]">Recorded takes</span>
            </div>

            {/* Average Composite Score */}
            <div className="rounded-2xl border border-[#d9dbd1] bg-white p-4 shadow-xs">
              <div className="flex items-center justify-between text-xs font-semibold text-[#687382]">
                <span>Average Score</span>
                <TrendingUp size={16} className="text-[#277254]" />
              </div>
              <p className="mt-2 text-2xl font-bold text-[#277254]" data-testid="stat-avg-score">
                {stats.avgScore !== null ? `${stats.avgScore}/100` : '—'}
              </p>
              <span className="text-[11px] text-[#687382]">Across all takes</span>
            </div>

            {/* Highest Score */}
            <div className="rounded-2xl border border-[#d9dbd1] bg-white p-4 shadow-xs">
              <div className="flex items-center justify-between text-xs font-semibold text-[#687382]">
                <span>Top Score</span>
                <Award size={16} className="text-[#b89c3b]" />
              </div>
              <p className="mt-2 text-2xl font-bold text-[#b89c3b]" data-testid="stat-best-score">
                {stats.bestScore !== null ? `${stats.bestScore}/100` : '—'}
              </p>
              <span className="text-[11px] text-[#687382]">Personal best</span>
            </div>

            {/* Average Speaking Pace */}
            <div className="rounded-2xl border border-[#d9dbd1] bg-white p-4 shadow-xs">
              <div className="flex items-center justify-between text-xs font-semibold text-[#687382]">
                <span>Average Pace</span>
                <Mic size={16} className="text-[#3a6384]" />
              </div>
              <p className="mt-2 text-2xl font-bold text-[#3a6384]" data-testid="stat-avg-pace">
                {stats.avgWpm !== null ? `${stats.avgWpm} WPM` : '—'}
              </p>
              <span className="text-[11px] text-[#687382]">Ideal: 130–160 WPM</span>
            </div>
          </div>
        )}

        {/* Filter and Search Bar (US-16-T3) */}
        {videoHistory.length > 0 && (
          <div className="flex flex-col gap-3 rounded-2xl border border-[#d9dbd1] bg-white p-4 shadow-xs md:flex-row md:items-center md:justify-between">
            {/* Search Input */}
            <div className="relative flex-1">
              <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#98a09c]" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search takes by filename or title..."
                data-testid="input-history-search"
                className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] pl-10 pr-4 py-2 text-xs font-normal outline-none transition placeholder:text-[#98a09c] focus:border-[#253142] focus:ring-1 focus:ring-[#f5c84b]"
              />
              {searchTerm && (
                <button
                  type="button"
                  onClick={() => setSearchTerm('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-[#98a09c] hover:text-[#253142]"
                >
                  Clear
                </button>
              )}
            </div>

            {/* Status Filter and Sort Controls */}
            <div className="flex flex-wrap items-center gap-2">
              <div className="flex items-center gap-1.5 rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3 py-1.5 text-xs text-[#526072]">
                <Filter size={13} className="text-[#687382]" />
                <span className="font-semibold text-[#253142]">Status:</span>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as any)}
                  data-testid="select-history-status"
                  aria-label="Filter takes by analysis status"
                  className="bg-transparent font-medium outline-none cursor-pointer"
                >
                  <option value="ALL">All Takes</option>
                  <option value="COMPLETED">Completed</option>
                  <option value="PROCESSING">Processing</option>
                  <option value="FAILED">Failed</option>
                </select>
              </div>

              <div className="flex items-center gap-1.5 rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3 py-1.5 text-xs text-[#526072]">
                <ArrowUpDown size={13} className="text-[#687382]" />
                <span className="font-semibold text-[#253142]">Sort:</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  data-testid="select-history-sort"
                  aria-label="Sort presentation takes"
                  className="bg-transparent font-medium outline-none cursor-pointer"
                >
                  <option value="NEWEST">Newest First</option>
                  <option value="OLDEST">Oldest First</option>
                  <option value="SCORE_HIGH">Highest Score</option>
                  <option value="SCORE_LOW">Lowest Score</option>
                  <option value="DURATION">Longest Duration</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Video History Table Card (US-16-T3) */}
        <div className="w-full rounded-2xl border border-[#d9dbd1] bg-white shadow-sm overflow-hidden">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center p-12 text-[#687382]">
              <Loader2 size={32} className="animate-spin text-[#277254]" />
              <p className="mt-3 text-sm font-semibold">Loading your practice takes...</p>
            </div>
          ) : videoHistory.length === 0 ? (
            /* Empty State (AC 5) */
            <div className="flex flex-col items-center justify-center p-14 text-center" data-testid="history-empty-state">
              <div className="grid h-16 w-16 place-items-center rounded-2xl bg-[#f4f6ef] text-[#253142] mb-3">
                <VideoIcon size={30} />
              </div>
              <h3 className="text-base font-bold text-[#253142]">No practice takes yet</h3>
              <p className="mt-1 max-w-sm text-xs text-[#687382]">
                Record or upload your first 1 to 3 minute presentation practice take to receive instant AI scoring, speech pacing feedback, and eye contact analysis.
              </p>
              <button
                type="button"
                onClick={() => setLocation('/student/practice')}
                data-testid="button-empty-start-practice"
                className="mt-4 inline-flex items-center gap-2 rounded-xl bg-[#253142] px-5 py-2.5 text-xs font-bold text-white hover:bg-[#33435a] transition shadow cursor-pointer"
              >
                <Plus size={15} /> Start your first practice take
              </button>
            </div>
          ) : filteredVideos.length === 0 ? (
            /* Filter Zero-State */
            <div className="flex flex-col items-center justify-center p-12 text-center text-[#687382]">
              <AlertCircle size={28} className="text-[#98a09c] mb-2" />
              <p className="text-sm font-semibold text-[#253142]">No takes match your current filter</p>
              <p className="text-xs text-[#687382] mt-1">Try clearing your search query or choosing another status.</p>
              <button
                type="button"
                onClick={() => { setSearchTerm(''); setStatusFilter('ALL'); }}
                className="mt-3 text-xs font-bold text-[#277254] hover:underline"
              >
                Reset filters
              </button>
            </div>
          ) : (
            <div className="w-full overflow-x-auto">
              {/* Table Header */}
              <div className="grid grid-cols-[minmax(240px,2fr)_minmax(130px,1fr)_minmax(120px,1fr)_minmax(220px,1.8fr)_minmax(110px,0.8fr)] px-6 py-4 border-b border-[#ecefe7] text-[11px] font-bold uppercase tracking-wider text-[#687382] select-none bg-white">
                <div>PRACTICE TAKE</div>
                <div>RECORDED</div>
                <div className="text-center">SCORE</div>
                <div>KEY AI METRICS</div>
                <div className="text-right pr-2">ACTIONS</div>
              </div>

              {/* Table Body Rows */}
              <div className="divide-y divide-[#ecefe7]">
                {filteredVideos.map((video) => {
                  const title = getVideoTitle(video);
                  const score = getVideoScore(video);
                  const isHighlighted = video.is_active;

                  return (
                    <div
                      key={video.id}
                      data-testid={`history-row-${video.id}`}
                      className={`grid grid-cols-[minmax(240px,2fr)_minmax(130px,1fr)_minmax(120px,1fr)_minmax(220px,1.8fr)_minmax(110px,0.8fr)] px-6 py-4 items-center transition ${
                        isHighlighted ? 'bg-[#fdfaf2] hover:bg-[#fbf7ed]' : 'bg-white hover:bg-[#fbf7ed]/60'
                      }`}
                    >
                      {/* PRACTICE Column */}
                      <div className="flex items-center gap-3.5 pr-2">
                        <button
                          type="button"
                          onClick={() => setPreviewVideo(video)}
                          data-testid={`button-play-take-${video.id}`}
                          title="Watch Take Preview"
                          className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[#253142] text-[#f5c84b] hover:bg-[#33435a] hover:scale-105 active:scale-95 transition shadow-xs cursor-pointer"
                        >
                          <Play size={16} fill="currentColor" className="ml-0.5 text-[#f5c84b]" />
                        </button>
                        <div className="min-w-0">
                          <p className="text-sm font-bold text-[#253142] truncate" title={title}>
                            {title}
                          </p>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className="text-[11px] text-[#687382] font-mono">
                              {formatDuration(video.duration_seconds)}
                            </span>
                            {video.is_active && (
                              <span className="rounded bg-[#e2f0e9] px-1.5 py-0.2 text-[10px] font-bold text-[#277254]">
                                Active
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* DATE Column */}
                      <div className="text-xs font-medium text-[#526072]">
                        {formatVideoDate(video.uploaded_at)}
                      </div>

                      {/* SCORE Column */}
                      <div className="flex flex-col items-center justify-center">
                        <div
                          data-testid={`score-badge-${video.id}`}
                          className={`flex h-10 w-10 items-center justify-center rounded-full border-2 ${
                            score !== null && score >= 85
                              ? 'border-[#277254] text-[#277254] bg-[#e2f0e9]'
                              : score !== null && score >= 70
                              ? 'border-[#d97706] text-[#d97706] bg-[#fef3c7]'
                              : score !== null
                              ? 'border-[#dc2626] text-[#dc2626] bg-[#fee2e2]'
                              : 'border-[#d9dbd1] text-[#687382] bg-white'
                          } text-sm font-bold shadow-xs`}
                        >
                          {score !== null ? (
                            score
                          ) : video.status === 'COMPLETED' || video.status === 'FAILED' ? (
                            '—'
                          ) : (
                            <Loader2 size={14} className="animate-spin text-[#277254]" />
                          )}
                        </div>
                        {score !== null && (
                          <span className="text-[10px] font-semibold text-[#687382] mt-0.5">
                            {score >= 85 ? 'Excellent' : score >= 70 ? 'Competent' : 'Needs Practice'}
                          </span>
                        )}
                      </div>

                      {/* KEY AI METRICS Column (US-16-T3) */}
                      <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
                        {/* Pace chip */}
                        {video.speech_analysis?.words_per_minute ? (
                          <span
                            title="Speaking Pace"
                            className="inline-flex items-center gap-1 rounded-md bg-[#f4f6ef] px-2 py-0.5 font-medium text-[#253142] border border-[#e2e4dc]"
                          >
                            <Mic size={11} className="text-[#277254]" />
                            <span>{Math.round(video.speech_analysis.words_per_minute)} WPM</span>
                          </span>
                        ) : null}

                        {/* Eye Contact chip */}
                        {video.behavioral_analysis?.eye_contact_score !== undefined ? (
                          <span
                            title="Eye Contact Adherence"
                            className="inline-flex items-center gap-1 rounded-md bg-[#f4f6ef] px-2 py-0.5 font-medium text-[#253142] border border-[#e2e4dc]"
                          >
                            <Eye size={11} className="text-[#3a6384]" />
                            <span>{video.behavioral_analysis.eye_contact_score}% Eye</span>
                          </span>
                        ) : null}

                        {/* Posture chip */}
                        {video.behavioral_analysis?.posture_score !== undefined ? (
                          <span
                            title="Posture Alignment"
                            className="inline-flex items-center gap-1 rounded-md bg-[#f4f6ef] px-2 py-0.5 font-medium text-[#253142] border border-[#e2e4dc]"
                          >
                            <Smile size={11} className="text-[#9a7922]" />
                            <span>{video.behavioral_analysis.posture_score}% Posture</span>
                          </span>
                        ) : null}

                        {!video.speech_analysis && !video.behavioral_analysis && (
                          <span className="text-xs text-[#98a09c] italic">
                            {video.status === 'FAILED' ? 'Analysis failed' : 'Processing analysis...'}
                          </span>
                        )}
                      </div>

                      {/* ACTIONS Column */}
                      <div className="flex items-center justify-end gap-1 text-[#687382]">
                        {/* Preview / External Replay */}
                        <button
                          type="button"
                          onClick={() => setPreviewVideo(video)}
                          title="Revisit take playback"
                          data-testid={`button-preview-${video.id}`}
                          className="rounded-lg p-2 hover:bg-[#f4f6ef] hover:text-[#253142] transition cursor-pointer"
                        >
                          <ExternalLink size={16} />
                        </button>

                        {/* AI Analysis Details */}
                        <button
                          type="button"
                          onClick={() => handleOpenAnalysis(video)}
                          title="View Full AI Analysis Report"
                          data-testid={`button-analysis-${video.id}`}
                          className="rounded-lg p-2 hover:bg-[#e2f0e9] hover:text-[#277254] transition cursor-pointer font-bold text-xs inline-flex items-center gap-1"
                        >
                          <Sparkles size={16} className="text-[#277254]" />
                        </button>

                        {/* Delete Take */}
                        <button
                          type="button"
                          onClick={() => handleDeleteVideo(video.id)}
                          title="Delete take"
                          data-testid={`button-delete-${video.id}`}
                          className="rounded-lg p-2 text-[#a33d35]/70 hover:bg-[#f7e5e1] hover:text-[#a33d35] transition cursor-pointer"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    )}
  </div>

      {/* MODAL 1: VIDEO PREVIEW PLAYER MODAL */}
      {previewVideo && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200"
          onClick={() => setPreviewVideo(null)}
        >
          <div
            className="w-full max-w-3xl overflow-hidden rounded-2xl bg-white shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-[#ecefe7] px-6 py-4">
              <div>
                <h3 className="text-base font-bold text-[#253142]">
                  {previewVideo.original_filename || 'Practice Take Playback'}
                </h3>
                <p className="text-xs text-[#687382]">
                  Recorded on {new Date(previewVideo.uploaded_at).toLocaleString()} • Duration:{' '}
                  {formatDuration(previewVideo.duration_seconds)}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setPreviewVideo(null)}
                className="grid h-8 w-8 place-items-center rounded-lg text-[#687382] hover:bg-[#f4f6ef] hover:text-[#253142] transition cursor-pointer"
              >
                <X size={18} />
              </button>
            </div>

            {/* Video Player Body */}
            <div className="p-6">
              <WebcamPlaybackPlayer
                src={previewVideo.file_url || previewVideo.file}
                durationSeconds={previewVideo.duration_seconds}
                isMirrored={isMirroredModal}
                onToggleMirror={() => setIsMirroredModal((prev) => !prev)}
                testId="history-modal-playback"
              />

              {/* Video Specs Banner */}
              <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-xs text-[#687382] bg-[#fbfaf5] border border-[#e8ebd9] rounded-xl px-4 py-3">
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1.5 font-medium text-[#253142]">
                    <HardDrive size={14} className="text-[#277254]" />
                    {previewVideo.formatted_compressed_size || 'Compressed H.264'}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <Clock size={14} />
                    {formatDuration(previewVideo.duration_seconds)}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      const vid = previewVideo;
                      setPreviewVideo(null);
                      handleOpenAnalysis(vid);
                    }}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-[#277254] px-3 py-1.5 text-xs font-bold text-white hover:bg-[#1f5c43] transition cursor-pointer"
                  >
                    <Sparkles size={13} />
                    <span>View AI Analysis</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 2: PAST ANALYSIS DETAIL VIEW (US-16-T4) */}
      {analysisVideo && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200"
          onClick={() => setAnalysisVideo(null)}
          data-testid="past-analysis-detail-modal"
        >
          <div
            className="w-full max-w-3xl max-h-[92vh] overflow-y-auto rounded-2xl bg-white shadow-2xl p-6"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-[#ecefe7] pb-4">
              <div className="flex items-center gap-2.5">
                <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#e2f0e9] text-[#277254]">
                  <Sparkles size={20} />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-[#253142]">
                    {getVideoTitle(analysisVideo)}
                  </h3>
                  <p className="text-xs text-[#687382]">
                    Recorded on {new Date(analysisVideo.uploaded_at).toLocaleDateString()} at{' '}
                    {new Date(analysisVideo.uploaded_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} • Duration: {formatDuration(analysisVideo.duration_seconds)}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setLocation(`/presentation/history/${analysisVideo.id}`)}
                  title="Open Dedicated Full-Screen Report"
                  data-testid="button-open-fullscreen-report"
                  className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-[#dde2d8] text-xs font-semibold text-[#253142] hover:bg-[#f4f6ef] transition cursor-pointer"
                >
                  <ExternalLink size={14} />
                  <span className="hidden sm:inline">Full Report</span>
                </button>
                <button
                  type="button"
                  onClick={() => setAnalysisVideo(null)}
                  data-testid="button-close-analysis-modal"
                  className="grid h-8 w-8 place-items-center rounded-lg text-[#687382] hover:bg-[#f4f6ef] hover:text-[#253142] transition cursor-pointer"
                >
                  <X size={18} />
                </button>
              </div>
            </div>

            {loadingAnalysis ? (
              <div className="flex flex-col items-center justify-center py-16 text-[#687382]">
                <Loader2 size={32} className="animate-spin text-[#277254]" />
                <p className="mt-3 text-sm font-semibold">Retrieving past presentation analysis...</p>
              </div>
            ) : (
              <div className="mt-6 space-y-6">
                {/* Pipeline Resilience Status Alert (US-40) */}
                <PipelineStatusAlert
                  video={analysisVideo}
                  onRetrySuccess={(updated) => {
                    setAnalysisVideo(updated);
                    loadHistory();
                  }}
                  notify={notify}
                />

                {/* Composite Presentation Scorecard (US-14 / US-16) */}
                <PresentationScoreCard
                  videoId={analysisVideo.id}
                  initialScore={analysisVideo.presentation_score}
                  notify={notify}
                />

                {/* AI Executive Coaching Suggestions (US-15 / US-16) */}
                <SuggestionsList
                  videoId={analysisVideo.id}
                  initialFeedback={analysisVideo.ai_feedback}
                  notify={notify}
                />

                {/* Speech Metrics Breakdown Card */}
                <div className="rounded-xl border border-[#ecefe7] bg-[#fbfaf5] p-5">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2 font-bold text-sm text-[#253142]">
                      <Mic size={16} className="text-[#277254]" /> Speech & Articulation Breakdown
                    </div>
                    {speechData && (
                      <span className="rounded-md bg-[#e2f0e9] px-2 py-0.5 text-xs font-bold text-[#277254]">
                        Clarity Score: {speechData.clarity_score}/100
                      </span>
                    )}
                  </div>

                  {speechData ? (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                        <div className="rounded-lg bg-white p-3 border border-[#ecefe7]">
                          <span className="text-[11px] text-[#687382]">Speaking Pace</span>
                          <p className="text-base font-bold text-[#253142]">
                            {speechData.words_per_minute} <span className="text-xs font-normal">WPM</span>
                          </p>
                          <span className="text-[10px] text-[#277254] font-medium">
                            {speechData.words_per_minute >= 130 && speechData.words_per_minute <= 160
                              ? '✓ Target pacing'
                              : speechData.words_per_minute < 130
                              ? 'Slightly slow'
                              : 'Fast tempo'}
                          </span>
                        </div>
                        <div className="rounded-lg bg-white p-3 border border-[#ecefe7]">
                          <span className="text-[11px] text-[#687382]">Filler Words</span>
                          <p className="text-base font-bold text-[#253142]">
                            {speechData.filler_word_count}
                          </p>
                          <span className="text-[10px] text-[#687382]">
                            {speechData.filler_word_count <= 2 ? '✓ Minimal fillers' : 'Practice pausing'}
                          </span>
                        </div>
                        <div className="rounded-lg bg-white p-3 border border-[#ecefe7] col-span-2 sm:col-span-1">
                          <span className="text-[11px] text-[#687382]">Clarity Score</span>
                          <p className="text-base font-bold text-[#277254]">
                            {speechData.clarity_score}%
                          </p>
                          <span className="text-[10px] text-[#277254]">Articulate & clear</span>
                        </div>
                      </div>

                      {/* Filler Words Breakdown Chips */}
                      {speechData.filler_words_breakdown &&
                        Object.keys(speechData.filler_words_breakdown).length > 0 && (
                          <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
                            <span className="text-[#687382] font-semibold">Identified Fillers:</span>
                            {Object.entries(speechData.filler_words_breakdown).map(([word, count]) => (
                              <span
                                key={word}
                                className="inline-flex items-center gap-1 rounded bg-[#fee2e2] px-2 py-0.5 text-[11px] font-bold text-[#dc2626]"
                              >
                                "{word}": {count}
                              </span>
                            ))}
                          </div>
                        )}

                      {/* Verbatim Transcript */}
                      {speechData.transcript && (
                        <div className="mt-4 border-t border-[#ecefe7] pt-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-bold text-[#253142]">Verbatim Transcript:</span>
                            <button
                              type="button"
                              onClick={handleCopyTranscript}
                              className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#277254] hover:underline cursor-pointer"
                            >
                              {copiedTranscript ? <Check size={12} /> : <Copy size={12} />}
                              <span>{copiedTranscript ? 'Copied' : 'Copy'}</span>
                            </button>
                          </div>
                          <p className="text-xs text-[#526072] italic bg-white p-3.5 rounded-lg border border-[#ecefe7] leading-relaxed">
                            "{speechData.transcript}"
                          </p>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-xs text-[#687382]">
                      Speech analysis has not been performed on this take yet.
                    </p>
                  )}
                </div>

                {/* Behavioral & Body Language Metrics */}
                <div className="rounded-xl border border-[#ecefe7] bg-[#fbfaf5] p-5">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2 font-bold text-sm text-[#253142]">
                      <Eye size={16} className="text-[#277254]" /> Behavioral & Body Language Breakdown
                    </div>
                    {behavioralData && (
                      <span className="rounded-md bg-[#e2f0e9] px-2 py-0.5 text-xs font-bold text-[#277254]">
                        Engagement: {behavioralData.engagement_score}/100
                      </span>
                    )}
                  </div>

                  {behavioralData ? (
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                      <div className="rounded-lg bg-white p-3 border border-[#ecefe7]">
                        <span className="text-[11px] text-[#687382]">Eye Contact</span>
                        <p className="text-base font-bold text-[#277254]">
                          {behavioralData.eye_contact_score}%
                        </p>
                        <span className="text-[10px] text-[#687382]">Direct camera gaze</span>
                      </div>
                      <div className="rounded-lg bg-white p-3 border border-[#ecefe7]">
                        <span className="text-[11px] text-[#687382]">Posture Alignment</span>
                        <p className="text-base font-bold text-[#253142]">
                          {behavioralData.posture_score}%
                        </p>
                        <span className="text-[10px] text-[#687382]">Upright shoulder angle</span>
                      </div>
                      <div className="rounded-lg bg-white p-3 border border-[#ecefe7] col-span-2 sm:col-span-1">
                        <span className="text-[11px] text-[#687382]">Engagement</span>
                        <p className="text-base font-bold text-[#253142]">
                          {behavioralData.engagement_score}%
                        </p>
                        <span className="text-[10px] text-[#687382]">Facial expression</span>
                      </div>
                    </div>
                  ) : (
                    <p className="text-xs text-[#687382]">
                      Behavioral analysis has not been performed on this take yet.
                    </p>
                  )}
                </div>

                {/* Action to Re-run or Refresh Analysis */}
                <div className="flex items-center justify-between pt-2">
                  <button
                    type="button"
                    onClick={() => {
                      const vid = analysisVideo;
                      setAnalysisVideo(null);
                      setPreviewVideo(vid);
                    }}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#526072] hover:text-[#253142] cursor-pointer"
                  >
                    <Play size={13} />
                    <span>Watch Video Playback</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleTriggerAnalysis}
                    disabled={triggeringAnalysis}
                    className="inline-flex items-center gap-2 rounded-xl bg-[#277254] px-5 py-2.5 text-xs font-bold text-white hover:bg-[#1f5c43] transition shadow cursor-pointer disabled:opacity-50"
                  >
                    {triggeringAnalysis ? (
                      <>
                        <Loader2 size={14} className="animate-spin" />
                        <span>Running AI Pipeline...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles size={14} />
                        <span>{speechData || behavioralData ? 'Re-run Analysis' : 'Run AI Analysis'}</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </AppShell>
  );
}
