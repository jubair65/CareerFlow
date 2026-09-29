import { useState, useRef, useEffect, useCallback } from 'react';
import {
  Upload,
  Video,
  Camera,
  Play,
  Square,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  FileVideo,
  Clock,
  Sparkles,
  ShieldCheck,
  Pause,
  Loader2,
  HardDrive,
  FlipHorizontal
} from 'lucide-react';
import fixWebmDuration from 'fix-webm-duration';
import { WebcamPlaybackPlayer } from './WebcamPlaybackPlayer';
import { apiUploadPresentationVideo, type PresentationVideo } from '../../api/presentation';

interface VideoRecorderProps {
  onUploadSuccess: (video: PresentationVideo) => void;
  notify?: (message: string, tone?: 'success' | 'info' | 'error') => void;
}

const MAX_FILE_SIZE_BYTES = 250 * 1024 * 1024; // 250 MB
const MAX_DURATION_SECONDS = 180; // 3 minutes

export function VideoRecorder({ onUploadSuccess, notify }: VideoRecorderProps) {
  const [activeTab, setActiveTab] = useState<'upload' | 'record'>('record');

  // File Upload State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [filePreviewUrl, setFilePreviewUrl] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Webcam Recording State
  const videoPreviewRef = useRef<HTMLVideoElement | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recordedChunksRef = useRef<Blob[]>([]);

  const [isCameraActive, setIsCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [recordingState, setRecordingState] = useState<'idle' | 'recording' | 'paused' | 'stopped'>('idle');
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const [recordedPreviewUrl, setRecordedPreviewUrl] = useState<string | null>(null);
  const [isMirrored, setIsMirrored] = useState(true);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const timerIntervalRef = useRef<number | null>(null);
  const recordingStartTimeRef = useRef<number>(0);
  const totalRecordedMsRef = useRef<number>(0);
  const lastResumeTimeRef = useRef<number>(0);

  // Stop camera stream cleanly
  const stopCameraStream = useCallback(() => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
    if (videoPreviewRef.current) {
      videoPreviewRef.current.srcObject = null;
    }
    setIsCameraActive(false);
  }, []);

  // Request camera and microphone access
  const startCamera = async () => {
    setCameraError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'user',
        },
        audio: true,
      });
      mediaStreamRef.current = stream;
      if (videoPreviewRef.current) {
        videoPreviewRef.current.srcObject = stream;
        videoPreviewRef.current.play();
      }
      setIsCameraActive(true);
    } catch (err: any) {
      console.error('Camera initialization failed:', err);
      let msg = 'Could not access your webcam/microphone.';
      if (err.name === 'NotAllowedError') {
        msg = 'Camera permission was denied. Please allow camera and mic permissions in your browser.';
      } else if (err.name === 'NotFoundError') {
        msg = 'No camera or microphone found on your device.';
      }
      setCameraError(msg);
      setIsCameraActive(false);
    }
  };

  // Switch tabs
  const handleTabChange = (tab: 'upload' | 'record') => {
    setActiveTab(tab);
    setUploadError(null);
    if (tab === 'upload') {
      stopCameraStream();
    } else {
      if (!isCameraActive && !recordedBlob) {
        startCamera();
      }
    }
  };

  useEffect(() => {
    if (activeTab === 'record' && !recordedBlob) {
      startCamera();
    }
    return () => {
      stopCameraStream();
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    };
  }, [activeTab]);

  // Clean up object URLs on unmount
  useEffect(() => {
    return () => {
      if (filePreviewUrl) URL.revokeObjectURL(filePreviewUrl);
      if (recordedPreviewUrl) URL.revokeObjectURL(recordedPreviewUrl);
    };
  }, [filePreviewUrl, recordedPreviewUrl]);

  // Handle Drag & Drop
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const validateAndSetFile = (file: File) => {
    setUploadError(null);
    const validExtensions = ['.mp4', '.webm', '.mov'];
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();

    if (!validExtensions.includes(ext)) {
      setUploadError(`Unsupported video format "${ext}". Please upload an .mp4, .webm, or .mov file.`);
      return;
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      const mb = (file.size / (1024 * 1024)).toFixed(1);
      setUploadError(`File size (${mb}MB) exceeds the maximum allowed limit of 250MB.`);
      return;
    }

    setSelectedFile(file);
    if (filePreviewUrl) URL.revokeObjectURL(filePreviewUrl);
    setFilePreviewUrl(URL.createObjectURL(file));
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  // Start Webcam Recording
  const startRecording = () => {
    if (!mediaStreamRef.current) {
      startCamera();
      return;
    }

    recordedChunksRef.current = [];
    setRecordedBlob(null);
    if (recordedPreviewUrl) URL.revokeObjectURL(recordedPreviewUrl);
    setRecordedPreviewUrl(null);
    setElapsedSeconds(0);
    recordingStartTimeRef.current = Date.now();
    lastResumeTimeRef.current = Date.now();
    totalRecordedMsRef.current = 0;

    // Pick best supported MIME type
    let mimeType = 'video/webm;codecs=vp8,opus';
    if (!MediaRecorder.isTypeSupported(mimeType)) {
      mimeType = MediaRecorder.isTypeSupported('video/mp4') ? 'video/mp4' : 'video/webm';
    }

    try {
      // 1.2 Mbps bitrate constraint gives high quality ~27MB 3-min video natively
      const recorder = new MediaRecorder(mediaStreamRef.current, {
        mimeType,
        videoBitsPerSecond: 1_200_000,
      });

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          recordedChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        const rawBlob = new Blob(recordedChunksRef.current, { type: mimeType });
        let finalBlob = rawBlob;

        // Accurate duration in milliseconds for WebM metadata patching
        const recordedMs = Math.max(1000, totalRecordedMsRef.current || (elapsedSeconds * 1000) || 1000);

        if (mimeType.includes('webm')) {
          try {
            finalBlob = await fixWebmDuration(rawBlob, recordedMs, { logger: false });
          } catch (e) {
            console.warn('Could not patch WebM duration header:', e);
          }
        }

        setRecordedBlob(finalBlob);
        const url = URL.createObjectURL(finalBlob);
        setRecordedPreviewUrl(url);
        stopCameraStream();
        setRecordingState('stopped');
      };

      recorder.start(1000); // 1-second chunks
      mediaRecorderRef.current = recorder;
      setRecordingState('recording');

      // Start elapsed timer
      timerIntervalRef.current = window.setInterval(() => {
        setElapsedSeconds((prev) => {
          if (prev + 1 >= MAX_DURATION_SECONDS) {
            stopRecording();
            return MAX_DURATION_SECONDS;
          }
          return prev + 1;
        });
      }, 1000);
    } catch (e: any) {
      console.error('Failed to start MediaRecorder:', e);
      setCameraError('Recording failed to initialize. Please check browser support.');
    }
  };

  const pauseRecording = () => {
    if (mediaRecorderRef.current && recordingState === 'recording') {
      mediaRecorderRef.current.pause();
      totalRecordedMsRef.current += Date.now() - lastResumeTimeRef.current;
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
      setRecordingState('paused');
    }
  };

  const resumeRecording = () => {
    if (mediaRecorderRef.current && recordingState === 'paused') {
      mediaRecorderRef.current.resume();
      lastResumeTimeRef.current = Date.now();
      setRecordingState('recording');
      timerIntervalRef.current = window.setInterval(() => {
        setElapsedSeconds((prev) => {
          if (prev + 1 >= MAX_DURATION_SECONDS) {
            stopRecording();
            return MAX_DURATION_SECONDS;
          }
          return prev + 1;
        });
      }, 1000);
    }
  };

  const stopRecording = () => {
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }
    if (recordingState === 'recording') {
      totalRecordedMsRef.current += Date.now() - lastResumeTimeRef.current;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
  };

  const retakeRecording = () => {
    if (recordedPreviewUrl) URL.revokeObjectURL(recordedPreviewUrl);
    setRecordedBlob(null);
    setRecordedPreviewUrl(null);
    setElapsedSeconds(0);
    totalRecordedMsRef.current = 0;
    setRecordingState('idle');
    startCamera();
  };

  // Upload Handlers
  const handleUploadFile = async () => {
    if (!selectedFile) return;
    setIsProcessing(true);
    setUploadError(null);
    setUploadProgress(0);

    try {
      const result = await apiUploadPresentationVideo(selectedFile, selectedFile.name, (pct) => {
        setUploadProgress(pct);
      });
      notify?.(result.message || 'Video uploaded and compressed successfully!', 'success');
      onUploadSuccess(result.video);
      setSelectedFile(null);
      setFilePreviewUrl(null);
      setUploadProgress(null);
    } catch (err: any) {
      const msg = err.response?.data?.error || err.message || 'Video upload failed.';
      setUploadError(msg);
      notify?.(msg, 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleUploadRecordedVideo = async () => {
    if (!recordedBlob) return;
    setIsProcessing(true);
    setUploadError(null);
    setUploadProgress(0);

    const timestamp = new Date().toISOString().replace(/[-:T.]/g, '').slice(0, 14);
    const filename = `webcam_recording_${timestamp}.webm`;

    try {
      const result = await apiUploadPresentationVideo(recordedBlob, filename, (pct) => {
        setUploadProgress(pct);
      });
      notify?.(result.message || 'Webcam recording uploaded and compressed!', 'success');
      onUploadSuccess(result.video);
      setRecordedBlob(null);
      setRecordedPreviewUrl(null);
      setRecordingState('idle');
      setUploadProgress(null);
    } catch (err: any) {
      const msg = err.response?.data?.error || err.message || 'Recording upload failed.';
      setUploadError(msg);
      notify?.(msg, 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="w-full rounded-2xl border border-[#d9dbd1] bg-white p-6 shadow-sm">
      {/* Header Tabs */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-[#ecefe7] pb-5">
        <div>
          <div className="inline-flex items-center gap-2 rounded-lg bg-[#e2f0e9] px-2.5 py-1 text-xs font-bold text-[#277254]">
            <Sparkles size={14} /> Presentation AI Studio
          </div>
          <h3 className="mt-1 text-xl font-bold text-[#253142]">Record or Upload Presentation Video</h3>
          <p className="text-xs text-[#687382]">
            Deliver a 1 to 3 minute professional introduction for speech & behavioral AI feedback.
          </p>
        </div>

        {/* Tab Buttons */}
        <div className="flex rounded-xl bg-[#f4f6ef] p-1">
          <button
            type="button"
            onClick={() => handleTabChange('record')}
            data-testid="tab-record-webcam"
            className={`flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-bold transition ${
              activeTab === 'record'
                ? 'bg-white text-[#253142] shadow-sm'
                : 'text-[#687382] hover:text-[#253142]'
            }`}
          >
            <Camera size={15} /> Record Webcam
          </button>
          <button
            type="button"
            onClick={() => handleTabChange('upload')}
            data-testid="tab-upload-file"
            className={`flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-bold transition ${
              activeTab === 'upload'
                ? 'bg-white text-[#253142] shadow-sm'
                : 'text-[#687382] hover:text-[#253142]'
            }`}
          >
            <Upload size={15} /> Upload File
          </button>
        </div>
      </div>

      {/* Info Banner: 250MB Support + Auto Compression */}
      <div className="my-4 flex items-center justify-between rounded-xl bg-[#fbfaf5] border border-[#e8ebd9] px-4 py-2.5 text-xs text-[#526072]">
        <div className="flex items-center gap-2">
          <HardDrive size={15} className="text-[#277254]" />
          <span>
            Supports high-resolution uploads up to <strong className="text-[#253142]">250 MB</strong> (max 3 mins).
          </span>
        </div>
        <div className="hidden sm:flex items-center gap-1.5 font-medium text-[#277254]">
          <ShieldCheck size={14} /> Auto-compressed to &lt;50 MB via FFmpeg
        </div>
      </div>

      {/* Upload Error Banner */}
      {uploadError && (
        <div data-testid="upload-error-banner" className="mb-4 flex items-center gap-2 rounded-xl bg-[#f7e5e1] px-4 py-3 text-sm font-semibold text-[#a33d35]">
          <AlertCircle size={18} className="shrink-0" />
          <span>{uploadError}</span>
        </div>
      )}

      {/* TAB 1: WEBCAM RECORDING */}
      {activeTab === 'record' && (
        <div className="space-y-4">
          {cameraError && (
            <div className="flex items-center gap-3 rounded-xl bg-[#f7e5e1] p-4 text-sm text-[#a33d35]">
              <AlertCircle size={20} className="shrink-0" />
              <div>
                <p className="font-bold">Camera Access Required</p>
                <p className="text-xs">{cameraError}</p>
                <button
                  type="button"
                  onClick={startCamera}
                  className="mt-2 text-xs font-bold underline hover:no-underline"
                >
                  Retry camera connection
                </button>
              </div>
            </div>
          )}

          {/* Recording & Preview Container */}
          <div className="relative aspect-video w-full overflow-hidden rounded-2xl bg-[#1a2330] shadow-inner">
            {/* Live Camera Stream */}
            {!recordedPreviewUrl && (
              <div className="relative h-full w-full">
                <video
                  ref={videoPreviewRef}
                  autoPlay
                  playsInline
                  muted
                  data-testid="webcam-live-preview"
                  style={{
                    transform: isMirrored ? 'scaleX(-1)' : 'none',
                    WebkitTransform: isMirrored ? 'scaleX(-1)' : 'none',
                  }}
                  className="h-full w-full object-cover transition-transform duration-300"
                />

                {/* Mirror Toggle Button during Live Camera */}
                <div className="absolute top-4 right-4 z-10">
                  <button
                    type="button"
                    onClick={() => setIsMirrored((prev) => !prev)}
                    title={isMirrored ? 'Switch to Normal View' : 'Switch to Mirrored View'}
                    data-testid="button-toggle-mirror-live"
                    className="flex items-center gap-1.5 rounded-full bg-black/60 border border-white/20 px-3 py-1.5 text-xs font-semibold text-white backdrop-blur-md hover:bg-black/80 transition shadow-sm cursor-pointer"
                  >
                    <FlipHorizontal size={14} className={isMirrored ? 'text-[#f5c84b]' : 'text-white/70'} />
                    <span>{isMirrored ? 'Mirrored' : 'Normal'}</span>
                  </button>
                </div>
              </div>
            )}

            {/* Recorded Video Playback Preview with Fixed Time Bar and Mirror Mode */}
            {recordedPreviewUrl && (
              <WebcamPlaybackPlayer
                src={recordedPreviewUrl}
                durationSeconds={totalRecordedMsRef.current ? Math.round(totalRecordedMsRef.current / 1000) : elapsedSeconds}
                isMirrored={isMirrored}
                onToggleMirror={() => setIsMirrored((prev) => !prev)}
                testId="webcam-recorded-preview"
              />
            )}

            {/* Timer Overlay (Only shown during active recording) */}
            {!recordedPreviewUrl && recordingState === 'recording' && (
              <div className="absolute top-4 left-4 flex items-center gap-2 rounded-full bg-black/60 px-3.5 py-1.5 text-xs font-bold text-white backdrop-blur-md">
                <span className="h-2.5 w-2.5 rounded-full bg-red-500 animate-pulse" />
                <span>REC</span>
                <span className="font-mono text-sm">{formatTimer(elapsedSeconds)}</span>
                <span className="text-white/60">/ 03:00</span>
              </div>
            )}

            {!recordedPreviewUrl && recordingState === 'paused' && (
              <div className="absolute top-4 left-4 flex items-center gap-2 rounded-full bg-yellow-500/80 px-3 py-1 text-xs font-bold text-[#253142] backdrop-blur-md">
                <Pause size={12} /> PAUSED ({formatTimer(elapsedSeconds)})
              </div>
            )}

            {/* Countdown warning when approaching 3 mins */}
            {!recordedPreviewUrl && recordingState === 'recording' && elapsedSeconds >= 150 && (
              <div className="absolute top-14 left-4 rounded-lg bg-red-600/90 px-2.5 py-1 text-xs font-bold text-white animate-bounce">
                {MAX_DURATION_SECONDS - elapsedSeconds}s remaining
              </div>
            )}
          </div>

          {/* Recording Action Controls */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
            <div className="flex items-center gap-2">
              {recordingState === 'idle' && !recordedBlob && (
                <button
                  type="button"
                  onClick={startRecording}
                  disabled={!isCameraActive || isProcessing}
                  data-testid="button-start-recording"
                  className="flex items-center gap-2 rounded-xl bg-[#253142] px-5 py-2.5 text-sm font-bold text-[#f5c84b] hover:bg-[#33435a] transition disabled:opacity-50"
                >
                  <Play size={16} fill="currentColor" /> Start Recording
                </button>
              )}

              {recordingState === 'recording' && (
                <>
                  <button
                    type="button"
                    onClick={pauseRecording}
                    className="flex items-center gap-1.5 rounded-xl border border-[#d9dbd1] bg-white px-4 py-2.5 text-sm font-semibold text-[#253142] hover:bg-[#f5f1e6] transition"
                  >
                    <Pause size={16} /> Pause
                  </button>
                  <button
                    type="button"
                    onClick={stopRecording}
                    data-testid="button-stop-recording"
                    className="flex items-center gap-2 rounded-xl bg-red-600 px-5 py-2.5 text-sm font-bold text-white hover:bg-red-700 transition"
                  >
                    <Square size={16} fill="currentColor" /> Stop Recording
                  </button>
                </>
              )}

              {recordingState === 'paused' && (
                <>
                  <button
                    type="button"
                    onClick={resumeRecording}
                    className="flex items-center gap-1.5 rounded-xl bg-[#253142] px-4 py-2.5 text-sm font-bold text-white hover:bg-[#33435a] transition"
                  >
                    <Play size={16} /> Resume
                  </button>
                  <button
                    type="button"
                    onClick={stopRecording}
                    className="flex items-center gap-2 rounded-xl bg-red-600 px-4 py-2.5 text-sm font-bold text-white hover:bg-red-700 transition"
                  >
                    <Square size={16} fill="currentColor" /> Stop
                  </button>
                </>
              )}

              {recordedBlob && (
                <button
                  type="button"
                  onClick={retakeRecording}
                  disabled={isProcessing}
                  data-testid="button-retake-recording"
                  className="flex items-center gap-1.5 rounded-xl border border-[#d9dbd1] bg-white px-4 py-2.5 text-sm font-semibold text-[#526072] hover:bg-[#f5f1e6] transition"
                >
                  <RotateCcw size={15} /> Retake
                </button>
              )}
            </div>

            {/* Submit Recorded Video */}
            {recordedBlob && (
              <button
                type="button"
                onClick={handleUploadRecordedVideo}
                disabled={isProcessing}
                data-testid="button-submit-recording"
                className="flex items-center gap-2 rounded-xl bg-[#277254] px-6 py-2.5 text-sm font-bold text-white hover:bg-[#1f5c43] shadow-md transition disabled:opacity-50"
              >
                {isProcessing ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    <span>Compressing & Saving...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 size={16} />
                    <span>Submit for AI Analysis</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: FILE UPLOAD */}
      {activeTab === 'upload' && (
        <div className="space-y-4">
          <input
            ref={fileInputRef}
            type="file"
            accept="video/mp4,video/webm,video/quicktime,.mp4,.webm,.mov"
            onChange={handleFileSelect}
            className="hidden"
            data-testid="input-video-file"
          />

          {!selectedFile ? (
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              data-testid="dropzone-video-upload"
              className={`flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-10 text-center cursor-pointer transition ${
                isDragging
                  ? 'border-[#277254] bg-[#e2f0e9]/30 scale-[1.01]'
                  : 'border-[#d0d4c8] bg-[#fbfaf5] hover:border-[#253142] hover:bg-[#f5f1e6]'
              }`}
            >
              <div className="grid h-16 w-16 place-items-center rounded-2xl bg-[#e2f0e9] text-[#277254] mb-3">
                <FileVideo size={32} />
              </div>
              <h4 className="text-base font-bold text-[#253142]">Drag and drop your presentation video</h4>
              <p className="mt-1 text-xs text-[#687382]">
                Supports <strong className="text-[#253142]">.mp4, .webm, .mov</strong> up to 250MB (max 3 minutes)
              </p>
              <button
                type="button"
                className="mt-4 rounded-xl bg-[#253142] px-4 py-2 text-xs font-bold text-white hover:bg-[#33435a] transition"
              >
                Browse Files
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Selected File Details */}
              <div className="flex items-center justify-between rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] p-4">
                <div className="flex items-center gap-3">
                  <div className="grid h-10 w-10 place-items-center rounded-lg bg-[#e2f0e9] text-[#277254]">
                    <FileVideo size={20} />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-[#253142]">{selectedFile.name}</p>
                    <p className="text-xs text-[#687382]">
                      {(selectedFile.size / (1024 * 1024)).toFixed(1)} MB • {selectedFile.type || 'Video'}
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedFile(null);
                    setFilePreviewUrl(null);
                  }}
                  disabled={isProcessing}
                  className="rounded-lg px-3 py-1.5 text-xs font-bold text-[#a33d35] hover:bg-[#f7e5e1] transition"
                >
                  Change File
                </button>
              </div>

              {/* Video Preview */}
              {filePreviewUrl && (
                <div className="aspect-video w-full overflow-hidden rounded-2xl bg-black">
                  <video src={filePreviewUrl} controls className="h-full w-full object-contain" />
                </div>
              )}

              {/* Upload Button */}
              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={handleUploadFile}
                  disabled={isProcessing}
                  data-testid="button-upload-file-submit"
                  className="flex items-center gap-2 rounded-xl bg-[#277254] px-6 py-2.5 text-sm font-bold text-white hover:bg-[#1f5c43] shadow-md transition disabled:opacity-50"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      <span>Uploading & Compressing...</span>
                    </>
                  ) : (
                    <>
                      <Upload size={16} />
                      <span>Upload & Process Video</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Progress & Processing Indicator */}
      {isProcessing && (
        <div className="mt-5 rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] p-4">
          <div className="flex items-center justify-between text-xs font-bold text-[#253142] mb-1.5">
            <span className="flex items-center gap-2">
              <Loader2 size={14} className="animate-spin text-[#277254]" />
              {uploadProgress !== null && uploadProgress < 100
                ? `Uploading video file (${uploadProgress}%)...`
                : 'Compressing to 720p H.264 (<50MB) with FFmpeg...'}
            </span>
            <span>{uploadProgress !== null ? `${uploadProgress}%` : ''}</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-[#e8ebd9]">
            <div
              className="h-full bg-[#277254] transition-all duration-300"
              style={{ width: `${uploadProgress || 100}%` }}
            />
          </div>
          <p className="mt-2 text-[11px] text-[#687382]">
            Please keep this tab open while your video is uploaded, normalized, and prepared for AI analysis.
          </p>
        </div>
      )}
    </div>
  );
}
