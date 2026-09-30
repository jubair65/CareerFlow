import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  Volume2,
  VolumeX,
  Maximize2,
  Minimize2,
  FlipHorizontal
} from 'lucide-react';

interface WebcamPlaybackPlayerProps {
  src: string;
  durationSeconds: number;
  isMirrored: boolean;
  onToggleMirror: () => void;
  testId?: string;
}

export function WebcamPlaybackPlayer({
  src,
  durationSeconds,
  isMirrored,
  onToggleMirror,
  testId = 'webcam-recorded-preview'
}: WebcamPlaybackPlayerProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const progressBarRef = useRef<HTMLDivElement | null>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [videoDuration, setVideoDuration] = useState<number>(durationSeconds);
  const [isSeeking, setIsSeeking] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const [hoverPosition, setHoverPosition] = useState<number | null>(null);
  const [hoverTime, setHoverTime] = useState<number | null>(null);

  const controlsTimeoutRef = useRef<number | null>(null);

  // Fallback to recorded elapsed duration if video.duration is Infinity, NaN, or 0
  const safeDuration =
    videoDuration && isFinite(videoDuration) && !isNaN(videoDuration) && videoDuration > 0
      ? videoDuration
      : Math.max(1, durationSeconds);

  // Percentage must strictly stay between 0% and 100%
  const progressPercent = Math.min(100, Math.max(0, (currentTime / safeDuration) * 100));

  const formatTimer = (seconds: number) => {
    const s = Math.max(0, Math.floor(seconds));
    const mins = Math.floor(s / 60);
    const secs = s % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Video metadata loaded
  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      const d = videoRef.current.duration;
      if (d && isFinite(d) && !isNaN(d) && d > 0) {
        setVideoDuration(d);
      }
    }
  };

  // Playhead time update
  const handleTimeUpdate = () => {
    if (!isSeeking && videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
      // In case duration became finite after starting playback
      const d = videoRef.current.duration;
      if (d && isFinite(d) && !isNaN(d) && d > 0 && d !== videoDuration) {
        setVideoDuration(d);
      }
    }
  };

  // Toggle play/pause
  const togglePlayPause = useCallback(() => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
    } else {
      if (currentTime >= safeDuration - 0.3) {
        videoRef.current.currentTime = 0;
        setCurrentTime(0);
      }
      videoRef.current.play().catch(console.error);
    }
  }, [isPlaying, currentTime, safeDuration]);

  // Restart 5 seconds back
  const handleSeekBack = () => {
    if (!videoRef.current) return;
    const newTime = Math.max(0, videoRef.current.currentTime - 5);
    videoRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };

  // Calculate target seek time from mouse clientX
  const calculateSeekTime = useCallback(
    (clientX: number) => {
      if (!progressBarRef.current) return 0;
      const rect = progressBarRef.current.getBoundingClientRect();
      const clickRatio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
      return clickRatio * safeDuration;
    },
    [safeDuration]
  );

  const handleProgressBarMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsSeeking(true);
    const target = calculateSeekTime(e.clientX);
    if (videoRef.current) {
      videoRef.current.currentTime = target;
    }
    setCurrentTime(target);
  };

  const handleProgressBarMouseMove = (e: React.MouseEvent) => {
    if (!progressBarRef.current) return;
    const rect = progressBarRef.current.getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    setHoverPosition(ratio * 100);
    setHoverTime(ratio * safeDuration);

    if (isSeeking && videoRef.current) {
      const target = ratio * safeDuration;
      videoRef.current.currentTime = target;
      setCurrentTime(target);
    }
  };

  const handleProgressBarMouseLeave = () => {
    setHoverPosition(null);
    setHoverTime(null);
  };

  // Global drag listener for smooth seeking outside the bar
  useEffect(() => {
    const handleGlobalMouseMove = (e: MouseEvent) => {
      if (isSeeking && videoRef.current) {
        const target = calculateSeekTime(e.clientX);
        videoRef.current.currentTime = target;
        setCurrentTime(target);
      }
    };

    const handleGlobalMouseUp = () => {
      if (isSeeking) {
        setIsSeeking(false);
      }
    };

    if (isSeeking) {
      window.addEventListener('mousemove', handleGlobalMouseMove);
      window.addEventListener('mouseup', handleGlobalMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleGlobalMouseMove);
      window.removeEventListener('mouseup', handleGlobalMouseUp);
    };
  }, [isSeeking, calculateSeekTime]);

  // Volume & Mute
  const toggleMute = () => {
    if (!videoRef.current) return;
    const nextMuted = !isMuted;
    videoRef.current.muted = nextMuted;
    setIsMuted(nextMuted);
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    setVolume(val);
    if (videoRef.current) {
      videoRef.current.volume = val;
      videoRef.current.muted = val === 0;
      setIsMuted(val === 0);
    }
  };

  // Fullscreen
  const toggleFullscreen = async () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      try {
        await containerRef.current.requestFullscreen();
        setIsFullscreen(true);
      } catch (err) {
        console.warn('Fullscreen request failed:', err);
      }
    } else {
      try {
        await document.exitFullscreen();
        setIsFullscreen(false);
      } catch (err) {
        console.warn('Exit fullscreen failed:', err);
      }
    }
  };

  useEffect(() => {
    const onFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', onFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', onFullscreenChange);
  }, []);

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === ' ' || e.key === 'k') {
      e.preventDefault();
      togglePlayPause();
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      if (videoRef.current) {
        const next = Math.max(0, videoRef.current.currentTime - 5);
        videoRef.current.currentTime = next;
        setCurrentTime(next);
      }
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      if (videoRef.current) {
        const next = Math.min(safeDuration, videoRef.current.currentTime + 5);
        videoRef.current.currentTime = next;
        setCurrentTime(next);
      }
    } else if (e.key === 'm' || e.key === 'M') {
      e.preventDefault();
      toggleMute();
    } else if (e.key === 'f' || e.key === 'F') {
      e.preventDefault();
      toggleFullscreen();
    }
  };

  // Auto-hide controls when playing and inactive
  const handleMouseMoveContainer = () => {
    setShowControls(true);
    if (controlsTimeoutRef.current) clearTimeout(controlsTimeoutRef.current);
    if (isPlaying) {
      controlsTimeoutRef.current = window.setTimeout(() => {
        setShowControls(false);
      }, 2500);
    }
  };

  const handleMouseLeaveContainer = () => {
    if (isPlaying) {
      setShowControls(false);
    }
  };

  useEffect(() => {
    return () => {
      if (controlsTimeoutRef.current) clearTimeout(controlsTimeoutRef.current);
    };
  }, []);

  return (
    <div
      ref={containerRef}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      onMouseMove={handleMouseMoveContainer}
      onMouseLeave={handleMouseLeaveContainer}
      className="group relative aspect-video w-full overflow-hidden rounded-2xl bg-[#0f172a] shadow-inner select-none focus:outline-none"
    >
      {/* Video Element */}
      <video
        ref={videoRef}
        src={src}
        data-testid={testId}
        playsInline
        style={{
          transform: isMirrored ? 'scaleX(-1)' : 'none',
          WebkitTransform: isMirrored ? 'scaleX(-1)' : 'none',
        }}
        className={`h-full w-full object-contain transition-transform duration-300 ${
          isMirrored ? 'mirror' : ''
        }`}
        onLoadedMetadata={handleLoadedMetadata}
        onTimeUpdate={handleTimeUpdate}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onEnded={() => {
          setIsPlaying(false);
          setCurrentTime(safeDuration);
        }}
        onClick={togglePlayPause}
      />

      {/* Center Big Play Button (when paused) */}
      {!isPlaying && (
        <button
          type="button"
          onClick={togglePlayPause}
          aria-label="Play recording preview"
          className="absolute inset-0 m-auto flex h-16 w-16 items-center justify-center rounded-full bg-black/60 text-white backdrop-blur-md hover:bg-black/80 hover:scale-110 active:scale-95 transition shadow-2xl z-20 cursor-pointer"
        >
          <Play size={28} fill="currentColor" className="ml-1 text-[#f5c84b]" />
        </button>
      )}

      {/* Top Overlay Badge Bar */}
      <div
        className={`absolute top-3 left-3 right-3 flex items-center justify-between pointer-events-none transition-opacity duration-300 z-20 ${
          showControls || !isPlaying ? 'opacity-100' : 'opacity-0'
        }`}
      >
        <div className="flex items-center gap-2 rounded-full bg-black/60 border border-white/10 px-3 py-1 text-xs font-bold text-white backdrop-blur-md">
          <span className="h-2 w-2 rounded-full bg-[#277254]" />
          <span>Preview Recording</span>
        </div>

        {/* Mirror Mode Toggle Button */}
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onToggleMirror();
          }}
          data-testid="button-playback-toggle-mirror"
          title={isMirrored ? 'Switch to Normal View' : 'Switch to Mirrored View'}
          className="pointer-events-auto flex items-center gap-1.5 rounded-full bg-black/60 hover:bg-black/80 border border-white/15 px-3 py-1 text-xs font-semibold text-white backdrop-blur-md transition shadow cursor-pointer"
        >
          <FlipHorizontal size={14} className={isMirrored ? 'text-[#f5c84b]' : 'text-white/70'} />
          <span>{isMirrored ? 'Mirrored' : 'Normal'}</span>
        </button>
      </div>

      {/* Bottom Controls Bar */}
      <div
        className={`absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 via-black/60 to-transparent px-4 pb-3 pt-8 transition-opacity duration-300 z-20 ${
          showControls || !isPlaying ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
      >
        {/* Timeline Scrubber Container */}
        <div
          ref={progressBarRef}
          onMouseDown={handleProgressBarMouseDown}
          onMouseMove={handleProgressBarMouseMove}
          onMouseLeave={handleProgressBarMouseLeave}
          data-testid="video-player-timeline"
          className="group/timeline relative mb-2.5 flex h-4 w-full cursor-pointer items-center"
        >
          {/* Track background */}
          <div className="relative h-1.5 w-full rounded-full bg-white/25 group-hover/timeline:h-2 transition-all overflow-hidden">
            {/* Filled Progress */}
            <div
              data-testid="video-player-progress-bar"
              className="h-full rounded-full bg-gradient-to-r from-[#f5c84b] to-[#277254] transition-all duration-75"
              style={{ width: `${progressPercent}%` }}
            />
          </div>

          {/* Hover Scrub Preview Bar */}
          {hoverPosition !== null && (
            <div
              className="pointer-events-none absolute top-1.5 h-1.5 rounded-full bg-white/20 transition-all"
              style={{ width: `${hoverPosition}%` }}
            />
          )}

          {/* Scrub Thumb Knob */}
          <div
            className="pointer-events-none absolute h-3.5 w-3.5 -translate-x-1/2 rounded-full border-2 border-white bg-[#f5c84b] shadow-md transition-transform group-hover/timeline:scale-125"
            style={{ left: `${progressPercent}%` }}
          />

          {/* Hover Time Tooltip */}
          {hoverPosition !== null && hoverTime !== null && (
            <div
              className="pointer-events-none absolute -top-7 -translate-x-1/2 rounded bg-black/85 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-white shadow"
              style={{ left: `${hoverPosition}%` }}
            >
              {formatTimer(hoverTime)}
            </div>
          )}
        </div>

        {/* Action Controls Row */}
        <div className="flex items-center justify-between text-white text-xs">
          {/* Left Controls: Play/Pause, Rewind, Time */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={togglePlayPause}
              data-testid="button-playback-play-pause"
              className="grid h-8 w-8 place-items-center rounded-lg hover:bg-white/20 transition cursor-pointer"
              title={isPlaying ? 'Pause (Space)' : 'Play (Space)'}
            >
              {isPlaying ? (
                <Pause size={17} fill="currentColor" />
              ) : (
                <Play size={17} fill="currentColor" className="ml-0.5" />
              )}
            </button>

            <button
              type="button"
              onClick={handleSeekBack}
              title="Seek back 5s (Left Arrow)"
              className="grid h-8 w-8 place-items-center rounded-lg hover:bg-white/20 transition text-white/80 hover:text-white cursor-pointer"
            >
              <RotateCcw size={15} />
            </button>

            {/* Time Indicator: Current / Total Duration */}
            <div className="flex items-center gap-1 font-mono text-xs font-medium text-white/90">
              <span data-testid="playback-current-time">{formatTimer(currentTime)}</span>
              <span className="text-white/40">/</span>
              <span data-testid="playback-total-duration">{formatTimer(safeDuration)}</span>
            </div>
          </div>

          {/* Right Controls: Volume, Mirror, Fullscreen */}
          <div className="flex items-center gap-2.5">
            {/* Volume Control */}
            <div className="flex items-center gap-1.5 group/vol">
              <button
                type="button"
                onClick={toggleMute}
                title={isMuted ? 'Unmute (M)' : 'Mute (M)'}
                className="grid h-8 w-8 place-items-center rounded-lg hover:bg-white/20 transition cursor-pointer text-white/90"
              >
                {isMuted || volume === 0 ? <VolumeX size={17} /> : <Volume2 size={17} />}
              </button>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={isMuted ? 0 : volume}
                onChange={handleVolumeChange}
                aria-label="Volume slider"
                className="hidden w-16 h-1 accent-[#277254] bg-white/30 rounded-full cursor-pointer group-hover/vol:inline-block transition-all"
              />
            </div>

            {/* Fullscreen Button */}
            <button
              type="button"
              onClick={toggleFullscreen}
              title={isFullscreen ? 'Exit Fullscreen (F)' : 'Fullscreen (F)'}
              className="grid h-8 w-8 place-items-center rounded-lg hover:bg-white/20 transition cursor-pointer text-white/90"
            >
              {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
