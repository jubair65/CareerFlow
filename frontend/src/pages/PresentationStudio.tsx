import { useState, useEffect } from 'react';
import {
  Presentation,
  Video as VideoIcon,
  CheckCircle2,
  Clock,
  Sparkles,
  HardDrive,
  Trash2,
  Play,
  RotateCcw,
  ShieldCheck,
  FileVideo,
  Layers,
  ArrowRight,
  FlipHorizontal
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import { PageHeading, type Notify } from '../components/dashboard/DashboardShared';
import { VideoRecorder } from '../components/presentation/VideoRecorder';
import { PresentationScoreCard } from '../components/presentation/PresentationScoreCard';
import {
  apiGetActivePresentationVideo,
  apiGetPresentationVideoHistory,
  apiDeletePresentationVideo,
  type PresentationVideo
} from '../api/presentation';

export function PresentationStudio({ notify }: { notify: Notify }) {
  const [activeVideo, setActiveVideo] = useState<PresentationVideo | null>(null);
  const [videoHistory, setVideoHistory] = useState<PresentationVideo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showRecorder, setShowRecorder] = useState(false);
  const [isMirroredActive, setIsMirroredActive] = useState(false);

  const loadVideos = async () => {
    setIsLoading(true);
    try {
      const [current, history] = await Promise.all([
        apiGetActivePresentationVideo(),
        apiGetPresentationVideoHistory(),
      ]);
      setActiveVideo(current);
      setVideoHistory(history);
      if (!current) {
        setShowRecorder(true);
      }
    } catch (err: any) {
      console.error('Error fetching presentation videos:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadVideos();
  }, []);

  const handleUploadSuccess = (newVideo: PresentationVideo) => {
    setActiveVideo(newVideo);
    setShowRecorder(false);
    loadVideos();
    notify('Video saved! AI speech and behavioral pipelines can now process your take.', 'success');
  };

  const handleDeleteVideo = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this presentation video?')) return;
    try {
      await apiDeletePresentationVideo(id);
      notify('Presentation video deleted.', 'info');
      loadVideos();
    } catch (err: any) {
      notify('Failed to delete video.', 'error');
    }
  };

  const formatDuration = (seconds: number) => {
    if (!seconds) return '—';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  return (
    <AppShell role="student" notify={notify}>
      <PageHeading
        eyebrow="AI Presentation Lab"
        title="Video Presentation Studio"
        description="Record or upload your 1-3 minute introduction. Our pipeline analyzes speaking pace, filler words, eye contact, and posture."
        action={
          activeVideo && !showRecorder ? (
            <button
              type="button"
              onClick={() => setShowRecorder(true)}
              data-testid="button-record-new-take"
              className="inline-flex items-center gap-2 rounded-xl bg-[#253142] px-4 py-2.5 text-sm font-bold text-[#faf7ef] hover:bg-[#33435a] transition"
            >
              <RotateCcw size={16} /> Record New Take
            </button>
          ) : undefined
        }
      />

      <div className="space-y-8">
        {/* RECORDER / UPLOADER ACCORDION */}
        {showRecorder && (
          <div className="space-y-3">
            {activeVideo && (
              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={() => setShowRecorder(false)}
                  className="text-xs font-bold text-[#687382] hover:text-[#253142]"
                >
                  Cancel and view current video
                </button>
              </div>
            )}
            <VideoRecorder onUploadSuccess={handleUploadSuccess} notify={notify} />
          </div>
        )}

        {/* ACTIVE VIDEO DISPLAY */}
        {activeVideo && !showRecorder && (
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Video Player Card */}
            <div className="lg:col-span-2 overflow-hidden rounded-2xl border border-[#d9dbd1] bg-white p-5 shadow-sm">
              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="flex h-3 w-3 rounded-full bg-[#277254]" />
                  <h3 className="text-base font-bold text-[#253142]">Active Presentation Video</h3>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setIsMirroredActive((prev) => !prev)}
                    className="flex items-center gap-1.5 rounded-lg border border-[#d9dbd1] bg-white px-2.5 py-1 text-xs font-semibold text-[#526072] hover:bg-[#f5f1e6] transition cursor-pointer"
                    title={isMirroredActive ? 'Switch to Normal View' : 'Switch to Mirrored View'}
                    data-testid="button-toggle-mirror-active"
                  >
                    <FlipHorizontal size={13} className={isMirroredActive ? 'text-[#277254]' : ''} />
                    <span>{isMirroredActive ? 'Mirrored' : 'Normal View'}</span>
                  </button>
                  <span
                    data-testid="badge-video-status"
                    className="rounded-lg bg-[#e2f0e9] px-2.5 py-1 text-xs font-bold text-[#277254]"
                  >
                    {activeVideo.status.replace(/_/g, ' ')}
                  </span>
                </div>
              </div>

              {/* Video Player */}
              <div className="aspect-video w-full overflow-hidden rounded-xl bg-black">
                <video
                  src={activeVideo.file_url || activeVideo.file}
                  controls
                  data-testid="active-video-player"
                  className={`h-full w-full object-contain transition-transform duration-300 ${
                    isMirroredActive ? '-scale-x-100 mirror' : ''
                  }`}
                />
              </div>

              {/* Video Metadata bar */}
              <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-xs text-[#687382] border-t border-[#ecefe7] pt-4">
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1.5 font-medium text-[#253142]">
                    <FileVideo size={14} /> {activeVideo.original_filename}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock size={14} /> {formatDuration(activeVideo.duration_seconds)}
                  </span>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => handleDeleteVideo(activeVideo.id)}
                    data-testid="button-delete-video"
                    className="flex items-center gap-1 rounded-lg px-2.5 py-1 text-xs font-semibold text-[#a33d35] hover:bg-[#f7e5e1] transition"
                  >
                    <Trash2 size={13} /> Delete
                  </button>
                </div>
              </div>
            </div>

            {/* Storage & Optimization Card */}
            <div className="space-y-4">
              <div className="rounded-2xl border border-[#d9dbd1] bg-white p-5 shadow-sm space-y-4">
                <div className="flex items-center gap-2 text-sm font-bold text-[#253142]">
                  <HardDrive size={18} className="text-[#277254]" /> Video Storage & Optimization
                </div>

                <div className="space-y-3 pt-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[#687382]">Original Upload Size:</span>
                    <span className="font-semibold text-[#253142]">{activeVideo.formatted_raw_size}</span>
                  </div>

                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[#687382]">Compressed Size (720p H.264):</span>
                    <span className="font-bold text-[#277254]">{activeVideo.formatted_compressed_size}</span>
                  </div>

                  {activeVideo.compression_savings_percent > 0 && (
                    <div className="rounded-xl bg-[#e2f0e9] p-3 text-xs text-[#277254]">
                      <div className="flex items-center gap-1.5 font-bold">
                        <ShieldCheck size={15} /> {activeVideo.compression_savings_percent}% Storage Saved
                      </div>
                      <p className="mt-1 text-[11px] leading-relaxed opacity-90">
                        Normalized via FFmpeg transcoding for lightning-fast AI vision & speech inference.
                      </p>
                    </div>
                  )}

                  <div className="border-t border-[#ecefe7] pt-3 text-xs text-[#687382]">
                    <span className="block text-[11px]">Uploaded on:</span>
                    <span className="font-medium text-[#253142]">
                      {new Date(activeVideo.uploaded_at).toLocaleDateString(undefined, {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                  </div>
                </div>
              </div>

              {/* Next Steps for Sprint 3 Story Pipeline */}
              <div className="rounded-2xl border border-[#ecefe7] bg-[#fbfaf5] p-5">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#277254]">
                  <Sparkles size={14} /> Downstream AI Pipelines
                </div>
                <h4 className="mt-1 text-sm font-bold text-[#253142]">Ready for Speech & Vision Analysis</h4>
                <p className="mt-1.5 text-xs text-[#687382] leading-relaxed">
                  Your video is encoded and queued for US-12 (Whisper transcription & WPM) and US-13 (MediaPipe eye contact & posture).
                </p>
              </div>
            </div>
          </div>
        )}

        {/* PRESENTATION SCORECARD (US-14) */}
        {activeVideo && !showRecorder && (
          <PresentationScoreCard
            videoId={activeVideo.id}
            initialScore={activeVideo.presentation_score}
            notify={notify}
          />
        )}

        {/* Link to Dedicated Video History */}
        {videoHistory.length > 0 && (
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-2xl border border-[#d9dbd1] bg-white p-5 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#f4f6ef] text-[#253142] shrink-0">
                <Layers size={20} />
              </div>
              <div>
                <p className="text-sm font-bold text-[#253142]">
                  You have {videoHistory.length} recorded practice {videoHistory.length === 1 ? 'take' : 'takes'}
                </p>
                <p className="text-xs text-[#687382]">
                  Review your scores, playback reps, and manage takes in the dedicated Video History tab.
                </p>
              </div>
            </div>
            <a
              href="/student/videos"
              className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-[#253142] px-4 py-2 text-xs font-bold text-white hover:bg-[#33435a] transition shrink-0"
            >
              <span>View Video History</span>
              <ArrowRight size={14} />
            </a>
          </div>
        )}
      </div>
    </AppShell>
  );
}
