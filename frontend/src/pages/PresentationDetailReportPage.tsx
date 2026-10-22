import { useState, useEffect } from 'react';
import { useLocation } from 'wouter';
import {
  ArrowLeft,
  Play,
  Sparkles,
  Mic,
  Eye,
  Smile,
  Activity,
  Copy,
  Check,
  AlertCircle,
  ShieldAlert,
  Clock,
  Calendar,
  CheckCircle2,
  Loader2,
  Award
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import { type Notify } from '../components/dashboard/DashboardShared';
import {
  apiGetPresentationVideoDetail,
  type PresentationVideo,
  type SpeechAnalysisData,
  type BehavioralAnalysisData
} from '../api/presentation';
import { WebcamPlaybackPlayer } from '../components/presentation/WebcamPlaybackPlayer';
import { PresentationScoreCard } from '../components/presentation/PresentationScoreCard';
import { SuggestionsList } from '../components/presentation/SuggestionsList';

interface PresentationDetailReportPageProps {
  notify: Notify;
}

export function PresentationDetailReportPage({ notify }: PresentationDetailReportPageProps) {
  const [location, setLocation] = useLocation();
  const [video, setVideo] = useState<PresentationVideo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isForbidden, setIsForbidden] = useState(false);
  const [copiedTranscript, setCopiedTranscript] = useState(false);
  const [isMirrored, setIsMirrored] = useState(true);

  // Extract video ID from path `/presentation/history/:id` or query `?id=:id`
  const extractVideoId = (): number | null => {
    const match = location.match(/\/presentation\/history\/(\d+)/);
    if (match && match[1]) {
      return parseInt(match[1], 10);
    }
    const params = new URLSearchParams(window.location.search);
    const queryId = params.get('video') || params.get('id');
    if (queryId && !isNaN(Number(queryId))) {
      return Number(queryId);
    }
    return null;
  };

  useEffect(() => {
    const videoId = extractVideoId();
    if (!videoId) {
      setErrorMessage('No presentation video ID specified.');
      setIsLoading(false);
      return;
    }

    const fetchDetail = async () => {
      setIsLoading(true);
      setErrorMessage(null);
      setIsForbidden(false);
      try {
        const data = await apiGetPresentationVideoDetail(videoId);
        setVideo(data);
      } catch (err: any) {
        if (err.response?.status === 403) {
          setIsForbidden(true);
          setErrorMessage('Access Denied: You do not have permission to view another student’s presentation analysis.');
        } else if (err.response?.status === 404) {
          setErrorMessage('Presentation video analysis not found.');
        } else {
          setErrorMessage(err.response?.data?.error || 'Failed to load presentation report.');
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchDetail();
  }, [location]);

  const handleCopyTranscript = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedTranscript(true);
    notify('Transcript copied to clipboard!', 'info');
    setTimeout(() => setCopiedTranscript(false), 2000);
  };

  const speech: SpeechAnalysisData | null = video?.speech_analysis || null;
  const behavioral: BehavioralAnalysisData | null = video?.behavioral_analysis || null;
  const score = video?.presentation_score || null;
  const feedback = video?.ai_feedback || null;

  return (
    <AppShell activeTab="videos">
      <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => setLocation('/student/videos')}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg border border-slate-700 bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 hover:text-white transition-all text-sm font-medium shadow-sm"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Presentation History
          </button>

          {video && (
            <div className="flex items-center gap-2">
              <span className="text-xs px-2.5 py-1 rounded-full font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Attempt ID #{video.id}
              </span>
              <span className="text-xs px-2.5 py-1 rounded-full font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                {video.status}
              </span>
            </div>
          )}
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-16 text-center space-y-4">
            <Loader2 className="w-10 h-10 text-indigo-400 animate-spin mx-auto" />
            <h3 className="text-lg font-semibold text-white">Loading Presentation Analysis...</h3>
            <p className="text-sm text-slate-400 max-w-sm mx-auto">
              Synthesizing acoustic vocal dynamics, behavioral posture tracking, and AI coaching recommendations.
            </p>
          </div>
        )}

        {/* Forbidden / Tenant Isolation Guard */}
        {!isLoading && isForbidden && (
          <div className="bg-red-950/30 border border-red-500/30 rounded-2xl p-10 text-center space-y-4">
            <div className="w-14 h-14 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto text-red-400">
              <ShieldAlert className="w-7 h-7" />
            </div>
            <h3 className="text-xl font-bold text-white">Tenant Isolation: Access Forbidden</h3>
            <p className="text-sm text-slate-300 max-w-md mx-auto">
              {errorMessage}
            </p>
            <div className="pt-2">
              <button
                onClick={() => setLocation('/student/videos')}
                className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-semibold transition-all shadow-md shadow-indigo-600/20"
              >
                Return to My Presentations
              </button>
            </div>
          </div>
        )}

        {/* Error / Not Found State */}
        {!isLoading && !isForbidden && errorMessage && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-10 text-center space-y-4">
            <div className="w-14 h-14 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center mx-auto text-amber-400">
              <AlertCircle className="w-7 h-7" />
            </div>
            <h3 className="text-lg font-semibold text-white">Analysis Not Found</h3>
            <p className="text-sm text-slate-400 max-w-sm mx-auto">{errorMessage}</p>
            <button
              onClick={() => setLocation('/student/videos')}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-sm font-medium transition-all"
            >
              Back to History
            </button>
          </div>
        )}

        {/* Successful Analysis View */}
        {!isLoading && !errorMessage && video && (
          <div className="space-y-8 animate-fadeIn">
            {/* Header Card */}
            <div className="bg-gradient-to-r from-slate-900 via-slate-850 to-indigo-950/40 border border-slate-800 rounded-2xl p-6 sm:p-8 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-80 h-80 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />

              <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                      Analysis Report
                    </span>
                    <span className="text-xs text-slate-400 flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5 text-slate-500" />
                      {new Date(video.uploaded_at).toLocaleDateString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </span>
                  </div>

                  <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
                    {video.original_filename}
                  </h1>

                  <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
                    <span className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      Duration: {Math.floor(video.duration_seconds / 60)}m {Math.round(video.duration_seconds % 60)}s
                    </span>
                    <span>•</span>
                    <span>File Format: {video.file_type.toUpperCase()}</span>
                    <span>•</span>
                    <span className="text-emerald-400 font-medium">Status: {video.status}</span>
                  </div>
                </div>

                {score && (
                  <div className="flex items-center gap-4 bg-slate-900/90 border border-slate-700/80 rounded-2xl p-4 sm:px-6 shadow-xl">
                    <div className="text-right">
                      <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Overall Score</p>
                      <p className="text-xs font-medium text-indigo-400">{score.grade_label}</p>
                    </div>
                    <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center text-white font-black text-2xl shadow-lg shadow-indigo-500/20">
                      {score.overall_score}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Score Breakdown Component */}
            {score && (
              <div>
                <h2 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
                  <Award className="w-5 h-5 text-indigo-400" />
                  Score Evaluation Breakdown
                </h2>
                <PresentationScoreCard score={score} />
              </div>
            )}

            {/* AI Coaching Feedback & Suggestions */}
            {feedback && (
              <div>
                <h2 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-indigo-400" />
                  AI Coaching Feedback
                </h2>
                <SuggestionsList feedback={feedback} />
              </div>
            )}

            {/* Speech Analysis Deep-Dive */}
            {speech && (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-7 space-y-6">
                <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                      <Mic className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-white">Speech & Acoustic Breakdown</h3>
                      <p className="text-xs text-slate-400">Vocal rhythm, pace cadence, and filler word detection</p>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
                    <span className="text-xs text-slate-400 uppercase font-semibold">Speaking Pace</span>
                    <p className="text-2xl font-bold text-white mt-1">
                      {speech.words_per_minute} <span className="text-xs text-slate-400 font-normal">WPM</span>
                    </p>
                    <span className="text-xs text-indigo-400">Ideal range: 130 - 160 WPM</span>
                  </div>

                  <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
                    <span className="text-xs text-slate-400 uppercase font-semibold">Filler Words</span>
                    <p className="text-2xl font-bold text-white mt-1">
                      {speech.filler_word_count} <span className="text-xs text-slate-400 font-normal">total</span>
                    </p>
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {Object.entries(speech.filler_words_breakdown || {}).map(([word, cnt]) => (
                        <span key={word} className="text-xs px-2 py-0.5 rounded bg-slate-700/80 text-slate-200">
                          "{word}": {cnt}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
                    <span className="text-xs text-slate-400 uppercase font-semibold">Clarity Rating</span>
                    <p className="text-2xl font-bold text-white mt-1">
                      {speech.clarity_score} <span className="text-xs text-slate-400 font-normal">/ 100</span>
                    </p>
                    <span className="text-xs text-emerald-400">Acoustic clarity index</span>
                  </div>
                </div>

                {/* Verbatim Transcript */}
                {speech.transcript && (
                  <div className="bg-slate-950/70 border border-slate-800/90 rounded-xl p-5 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold uppercase text-slate-400 tracking-wider">
                        Verbatim Transcript
                      </span>
                      <button
                        onClick={() => handleCopyTranscript(speech.transcript)}
                        className="inline-flex items-center gap-1.5 text-xs text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 px-2.5 py-1 rounded transition-colors"
                      >
                        {copiedTranscript ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                        {copiedTranscript ? 'Copied' : 'Copy'}
                      </button>
                    </div>
                    <p className="text-sm text-slate-300 leading-relaxed font-mono">
                      "{speech.transcript}"
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Behavioral & Visual Metrics */}
            {behavioral && (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-7 space-y-6">
                <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-violet-400">
                      <Eye className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-white">Visual & Non-Verbal Signals</h3>
                      <p className="text-xs text-slate-400">Eye contact maintenance, head posture stability, and expressive engagement</p>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
                    <span className="text-xs text-slate-400 uppercase font-semibold">Eye Contact</span>
                    <p className="text-2xl font-bold text-white mt-1">
                      {behavioral.eye_contact_score} <span className="text-xs text-slate-400 font-normal">/ 100</span>
                    </p>
                    <span className="text-xs text-indigo-400">Direct camera gaze ratio</span>
                  </div>

                  <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
                    <span className="text-xs text-slate-400 uppercase font-semibold">Posture Stability</span>
                    <p className="text-2xl font-bold text-white mt-1">
                      {behavioral.posture_score} <span className="text-xs text-slate-400 font-normal">/ 100</span>
                    </p>
                    <span className="text-xs text-emerald-400">Upper body uprightness</span>
                  </div>

                  <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4">
                    <span className="text-xs text-slate-400 uppercase font-semibold">Engagement Signal</span>
                    <p className="text-2xl font-bold text-white mt-1">
                      {behavioral.engagement_score} <span className="text-xs text-slate-400 font-normal">/ 100</span>
                    </p>
                    <span className="text-xs text-purple-400">Facial & expressive engagement</span>
                  </div>
                </div>
              </div>
            )}

            {/* Video Playback Player */}
            {video.video_url && (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <Play className="w-4 h-4 text-indigo-400" />
                    Recorded Video Take Playback
                  </h3>
                  <button
                    onClick={() => setIsMirrored(!isMirrored)}
                    className="text-xs px-2.5 py-1 rounded-md border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-300"
                  >
                    {isMirrored ? 'Disable Mirror' : 'Enable Mirror'}
                  </button>
                </div>
                <div className="max-w-2xl mx-auto rounded-xl overflow-hidden border border-slate-800 bg-black">
                  <WebcamPlaybackPlayer videoUrl={video.video_url} isMirrored={isMirrored} />
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}
export default PresentationDetailReportPage;
