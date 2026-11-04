import { useState, useEffect } from 'react';
import { useLocation } from 'wouter';
import {
  ArrowLeft,
  Play,
  Sparkles,
  Mic,
  Eye,
  Activity,
  Copy,
  Check,
  AlertCircle,
  ShieldAlert,
  Clock,
  Calendar,
  Loader2,
  Award
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import { PageTransition } from '../motion';
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
      <PageTransition>
        <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
          {/* Navigation Breadcrumb */}
          <div className="flex items-center justify-between">
            <button
              onClick={() => setLocation('/student/videos')}
              className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl border border-[#d9dbd1] bg-white hover:bg-[#f4f6ef] text-[#253142] transition-colors text-xs font-bold shadow-2xs cursor-pointer"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Presentation History
            </button>

            {video && (
              <div className="flex items-center gap-2">
                <span className="text-xs px-3 py-1 rounded-full font-semibold bg-[#e2f0e9] text-[#277254] border border-[#b8d8c7]">
                  Attempt ID #{video.id}
                </span>
                <span className="text-[11px] px-3 py-1 rounded-full font-bold uppercase tracking-wider bg-[#eef0e7] text-[#253142] border border-[#d9dbd1]">
                  {video.status}
                </span>
              </div>
            )}
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="rounded-2xl border border-[#d9dbd1] bg-white p-16 text-center space-y-4 shadow-xs">
              <Loader2 className="w-10 h-10 text-[#277254] animate-spin mx-auto" />
              <h3 className="text-lg font-bold text-[#253142]">Loading Presentation Analysis...</h3>
              <p className="text-xs text-[#687382] max-w-sm mx-auto">
                Synthesizing acoustic vocal dynamics, behavioral posture tracking, and AI coaching recommendations.
              </p>
            </div>
          )}

          {/* Forbidden / Tenant Isolation Guard */}
          {!isLoading && isForbidden && (
            <div className="rounded-2xl border border-[#fecaca] bg-[#fff5f5] p-10 text-center space-y-4 shadow-xs">
              <div className="w-14 h-14 rounded-2xl bg-[#fee2e2] border border-[#fecaca] flex items-center justify-center mx-auto text-[#dc2626]">
                <ShieldAlert className="w-7 h-7" />
              </div>
              <h3 className="text-xl font-bold text-[#253142]">Tenant Isolation: Access Forbidden</h3>
              <p className="text-xs text-[#687382] max-w-md mx-auto">
                {errorMessage}
              </p>
              <div className="pt-2">
                <button
                  onClick={() => setLocation('/student/videos')}
                  className="px-5 py-2.5 bg-[#253142] hover:bg-[#33435a] text-white rounded-xl text-xs font-bold transition-all shadow-xs cursor-pointer"
                >
                  Return to My Presentations
                </button>
              </div>
            </div>
          )}

          {/* Error / Not Found State */}
          {!isLoading && !isForbidden && errorMessage && (
            <div className="rounded-2xl border border-[#fed7aa] bg-[#fffaf5] p-10 text-center space-y-4 shadow-xs">
              <div className="w-14 h-14 rounded-2xl bg-[#ffedd5] border border-[#fed7aa] flex items-center justify-center mx-auto text-[#ea580c]">
                <AlertCircle className="w-7 h-7" />
              </div>
              <h3 className="text-lg font-bold text-[#253142]">Analysis Not Found</h3>
              <p className="text-xs text-[#687382] max-w-sm mx-auto">{errorMessage}</p>
              <button
                onClick={() => setLocation('/student/videos')}
                className="px-4 py-2 bg-[#253142] hover:bg-[#33435a] text-white rounded-xl text-xs font-bold transition-all cursor-pointer"
              >
                Back to History
              </button>
            </div>
          )}

          {/* Successful Analysis View */}
          {!isLoading && !errorMessage && video && (
            <div className="space-y-8">
              {/* Header Card */}
              <div className="rounded-2xl border border-[#d9dbd1] bg-white p-6 sm:p-7 shadow-xs">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#eef0e7] text-[#253142] border border-[#d9dbd1]">
                        Analysis Report
                      </span>
                      <span className="text-xs text-[#687382] flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5 text-[#7b8490]" />
                        {new Date(video.uploaded_at).toLocaleDateString(undefined, {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </span>
                    </div>

                    <h1 className="text-2xl sm:text-3xl font-extrabold text-[#253142] tracking-tight">
                      {video.original_filename}
                    </h1>

                    <div className="flex flex-wrap items-center gap-3 text-xs text-[#687382]">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5 text-[#7b8490]" />
                        Duration: {Math.floor(video.duration_seconds / 60)}m {Math.round(video.duration_seconds % 60)}s
                      </span>
                      <span>•</span>
                      <span>File Format: {video.file_type.toUpperCase()}</span>
                      <span>•</span>
                      <span className="text-[#277254] font-semibold">Status: {video.status}</span>
                    </div>
                  </div>

                  {score && (
                    <div className="flex items-center gap-4 bg-[#fbfaf5] border border-[#d9dbd1] rounded-2xl p-4 sm:px-6 shadow-2xs">
                      <div className="text-right">
                        <p className="text-[11px] font-bold uppercase tracking-wider text-[#7b8490]">Overall Score</p>
                        <p className="text-xs font-bold text-[#277254]">{score.grade_label}</p>
                      </div>
                      <div className="w-14 h-14 rounded-2xl bg-[#253142] flex items-center justify-center text-white font-extrabold text-2xl shadow-sm">
                        {score.overall_score}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Score Breakdown Component */}
              <div>
                <h2 className="text-lg font-bold text-[#253142] mb-3 flex items-center gap-2">
                  <Award className="w-5 h-5 text-[#277254]" />
                  Score Evaluation Breakdown
                </h2>
                <PresentationScoreCard
                  videoId={video.id}
                  initialScore={score}
                  onScoreUpdated={(newScore) => setVideo((prev) => prev ? { ...prev, presentation_score: newScore } : null)}
                  notify={notify}
                />
              </div>

              {/* AI Coaching Feedback & Suggestions */}
              <div>
                <h2 className="text-lg font-bold text-[#253142] mb-3 flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-[#277254]" />
                  AI Coaching Feedback
                </h2>
                <SuggestionsList
                  videoId={video.id}
                  initialFeedback={feedback}
                  notify={notify}
                />
              </div>

              {/* Speech Analysis Deep-Dive */}
              {speech && (
                <div className="rounded-2xl border border-[#d9dbd1] bg-white p-6 sm:p-7 space-y-6 shadow-xs">
                  <div className="flex items-center justify-between border-b border-[#ecefe7] pb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-[#e2f0e9] border border-[#b8d8c7] flex items-center justify-center text-[#277254]">
                        <Mic className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="text-base font-bold text-[#253142]">Speech & Acoustic Breakdown</h3>
                        <p className="text-xs text-[#687382]">Vocal rhythm, pace cadence, and filler word detection</p>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="bg-[#fbfaf5] border border-[#d9dbd1] rounded-xl p-4">
                      <span className="text-[11px] text-[#7b8490] uppercase font-bold tracking-wider">Speaking Pace</span>
                      <p className="text-2xl font-extrabold text-[#253142] mt-1">
                        {speech.words_per_minute} <span className="text-xs text-[#687382] font-normal">WPM</span>
                      </p>
                      <span className="text-xs font-medium text-[#277254]">Ideal range: 130 - 160 WPM</span>
                    </div>

                    <div className="bg-[#fbfaf5] border border-[#d9dbd1] rounded-xl p-4">
                      <span className="text-[11px] text-[#7b8490] uppercase font-bold tracking-wider">Filler Words</span>
                      <p className="text-2xl font-extrabold text-[#253142] mt-1">
                        {speech.filler_word_count} <span className="text-xs text-[#687382] font-normal">total</span>
                      </p>
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {Object.entries(speech.filler_words_breakdown || {}).map(([word, cnt]) => (
                          <span key={word} className="text-xs px-2 py-0.5 rounded-md bg-[#eef0e7] text-[#253142] border border-[#d9dbd1] font-medium">
                            "{word}": {cnt}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="bg-[#fbfaf5] border border-[#d9dbd1] rounded-xl p-4">
                      <span className="text-[11px] text-[#7b8490] uppercase font-bold tracking-wider">Clarity Rating</span>
                      <p className="text-2xl font-extrabold text-[#253142] mt-1">
                        {speech.clarity_score} <span className="text-xs text-[#687382] font-normal">/ 100</span>
                      </p>
                      <span className="text-xs font-medium text-[#277254]">Acoustic clarity index</span>
                    </div>
                  </div>

                  {/* Verbatim Transcript */}
                  {speech.transcript && (
                    <div className="bg-[#f8f9f5] border border-[#d9dbd1] rounded-xl p-5 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-bold uppercase text-[#7b8490] tracking-wider">
                          Verbatim Transcript
                        </span>
                        <button
                          onClick={() => handleCopyTranscript(speech.transcript)}
                          className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#253142] bg-white border border-[#d9dbd1] hover:bg-[#ecefe7] px-2.5 py-1 rounded-lg transition-colors cursor-pointer"
                        >
                          {copiedTranscript ? <Check className="w-3.5 h-3.5 text-[#277254]" /> : <Copy className="w-3.5 h-3.5" />}
                          {copiedTranscript ? 'Copied' : 'Copy'}
                        </button>
                      </div>
                      <p className="text-sm text-[#253142] leading-relaxed italic">
                        "{speech.transcript}"
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Behavioral & Visual Metrics */}
              {behavioral && (
                <div className="rounded-2xl border border-[#d9dbd1] bg-white p-6 sm:p-7 space-y-6 shadow-xs">
                  <div className="flex items-center justify-between border-b border-[#ecefe7] pb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-[#e2f0e9] border border-[#b8d8c7] flex items-center justify-center text-[#277254]">
                        <Eye className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="text-base font-bold text-[#253142]">Visual & Non-Verbal Signals</h3>
                        <p className="text-xs text-[#687382]">Eye contact maintenance, head posture stability, and expressive engagement</p>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="bg-[#fbfaf5] border border-[#d9dbd1] rounded-xl p-4">
                      <span className="text-[11px] text-[#7b8490] uppercase font-bold tracking-wider">Eye Contact</span>
                      <p className="text-2xl font-extrabold text-[#253142] mt-1">
                        {behavioral.eye_contact_score} <span className="text-xs text-[#687382] font-normal">/ 100</span>
                      </p>
                      <span className="text-xs font-medium text-[#277254]">Direct camera gaze ratio</span>
                    </div>

                    <div className="bg-[#fbfaf5] border border-[#d9dbd1] rounded-xl p-4">
                      <span className="text-[11px] text-[#7b8490] uppercase font-bold tracking-wider">Posture Stability</span>
                      <p className="text-2xl font-extrabold text-[#253142] mt-1">
                        {behavioral.posture_score} <span className="text-xs text-[#687382] font-normal">/ 100</span>
                      </p>
                      <span className="text-xs font-medium text-[#277254]">Upper body uprightness</span>
                    </div>

                    <div className="bg-[#fbfaf5] border border-[#d9dbd1] rounded-xl p-4">
                      <span className="text-[11px] text-[#7b8490] uppercase font-bold tracking-wider">Engagement Signal</span>
                      <p className="text-2xl font-extrabold text-[#253142] mt-1">
                        {behavioral.engagement_score} <span className="text-xs text-[#687382] font-normal">/ 100</span>
                      </p>
                      <span className="text-xs font-medium text-[#277254]">Facial & expressive engagement</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Video Playback Player */}
              {video.video_url && (
                <div className="rounded-2xl border border-[#d9dbd1] bg-white p-6 space-y-4 shadow-xs">
                  <div className="flex items-center justify-between border-b border-[#ecefe7] pb-3">
                    <h3 className="text-base font-bold text-[#253142] flex items-center gap-2">
                      <Play className="w-4 h-4 text-[#277254]" />
                      Recorded Video Take Playback
                    </h3>
                    <button
                      onClick={() => setIsMirrored(!isMirrored)}
                      className="text-xs px-2.5 py-1 rounded-lg border border-[#d9dbd1] bg-white hover:bg-[#f4f6ef] text-[#253142] font-semibold transition cursor-pointer"
                    >
                      {isMirrored ? 'Disable Mirror' : 'Enable Mirror'}
                    </button>
                  </div>
                  <div className="max-w-2xl mx-auto rounded-xl overflow-hidden border border-[#d9dbd1] bg-black">
                    <WebcamPlaybackPlayer videoUrl={video.video_url} isMirrored={isMirrored} />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </PageTransition>
    </AppShell>
  );
}
export default PresentationDetailReportPage;
