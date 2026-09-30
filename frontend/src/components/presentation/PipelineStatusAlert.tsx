import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  RotateCcw,
  CheckCircle2,
  Info,
  ChevronDown,
  ChevronUp,
  Activity,
  Terminal,
  ShieldAlert,
  Clock,
  Sparkles,
  RefreshCw,
} from 'lucide-react';
import {
  PresentationVideo,
  PipelineStatusData,
  PipelineExecutionLogData,
  apiRetryPresentationPipeline,
  apiGetPipelineStatus,
} from '../../api/presentation';

interface PipelineStatusAlertProps {
  video: PresentationVideo;
  onRetrySuccess?: (updatedVideo: PresentationVideo) => void;
  notify?: (type: 'success' | 'error' | 'info' | 'warning', message: string) => void;
}

export function PipelineStatusAlert({
  video,
  onRetrySuccess,
  notify,
}: PipelineStatusAlertProps) {
  const [isRetrying, setIsRetrying] = useState(false);
  const [showDiagnostics, setShowDiagnostics] = useState(false);
  const [telemetry, setTelemetry] = useState<PipelineStatusData | null>(null);
  const [isLoadingTelemetry, setIsLoadingTelemetry] = useState(false);

  const isFailed = video.status === 'FAILED';
  const isRetryingState = video.status === 'RETRYING';
  const isDegraded =
    video.status === 'PARTIALLY_COMPLETED' ||
    (video.presentation_score !== undefined &&
      video.presentation_score !== null &&
      !video.presentation_score.has_behavioral_data);

  // Load telemetry when expanding diagnostics or in degraded/failed state
  const fetchTelemetry = async () => {
    try {
      setIsLoadingTelemetry(true);
      const data = await apiGetPipelineStatus(video.id);
      setTelemetry(data);
    } catch (err: any) {
      // Non-fatal telemetry read
      console.warn('Could not fetch pipeline telemetry:', err);
    } finally {
      setIsLoadingTelemetry(false);
    }
  };

  useEffect(() => {
    if (isFailed || isDegraded || showDiagnostics) {
      fetchTelemetry();
    }
  }, [video.id, video.status, showDiagnostics]);

  const handleRetry = async () => {
    if (isRetrying) return;
    try {
      setIsRetrying(true);
      notify?.('info', 'Re-executing presentation pipeline with supervised retry...');
      const response = await apiRetryPresentationPipeline(video.id);
      notify?.('success', 'Pipeline analysis completed successfully!');
      if (onRetrySuccess && response.video) {
        onRetrySuccess(response.video);
      }
      fetchTelemetry();
    } catch (err: any) {
      const errMsg = err.response?.data?.error || err.message || 'Retry failed.';
      notify?.('error', `Pipeline retry encountered an error: ${errMsg}`);
    } finally {
      setIsRetrying(false);
    }
  };

  // If status is standard COMPLETED and not degraded, don't show intrusive banner
  if (!isFailed && !isRetryingState && !isDegraded) {
    return null;
  }

  return (
    <div
      data-testid="pipeline-status-container"
      className="space-y-3 transition-all duration-300"
    >
      {/* 1. FATAL PIPELINE FAILURE BANNER */}
      {isFailed && (
        <div
          data-testid="pipeline-failure-alert"
          className="rounded-2xl border border-[#fecaca] bg-[#fff5f5] p-5 shadow-sm text-[#7f1d1d]"
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#fee2e2] text-[#dc2626] shrink-0 mt-0.5">
                <AlertTriangle size={20} />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-bold text-[#991b1b]">
                    Analysis Pipeline Interrupted
                  </h4>
                  <span
                    data-testid="badge-pipeline-failed"
                    className="rounded-full bg-[#fca5a5]/30 px-2 py-0.5 text-[10px] font-black uppercase tracking-wider text-[#991b1b]"
                  >
                    Fault Caught (US-40)
                  </span>
                </div>
                <p className="mt-1 text-xs text-[#7f1d1d] leading-relaxed max-w-2xl">
                  A transient exception occurred during the speech or vision inference stage.
                  Your video is safely stored. You can trigger an automatic recovery re-run below.
                </p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                onClick={() => setShowDiagnostics((prev) => !prev)}
                data-testid="button-toggle-diagnostics"
                className="inline-flex items-center gap-1.5 rounded-xl border border-[#fca5a5] bg-white px-3 py-2 text-xs font-semibold text-[#7f1d1d] hover:bg-[#fee2e2] transition cursor-pointer"
              >
                <Terminal size={14} />
                <span>{showDiagnostics ? 'Hide Logs' : 'Diagnostics'}</span>
                {showDiagnostics ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>

              <button
                type="button"
                onClick={handleRetry}
                disabled={isRetrying}
                data-testid="button-pipeline-retry"
                className="inline-flex items-center gap-2 rounded-xl bg-[#dc2626] px-4 py-2 text-xs font-bold text-white hover:bg-[#b91c1c] transition shadow-sm disabled:opacity-50 cursor-pointer"
              >
                <RotateCcw size={14} className={isRetrying ? 'animate-spin' : ''} />
                <span>{isRetrying ? 'Retrying Pipeline...' : 'Retry Analysis'}</span>
              </button>
            </div>
          </div>

          {/* Diagnostic Trace Section */}
          {showDiagnostics && (
            <div
              data-testid="pipeline-diagnostics-drawer"
              className="mt-4 pt-4 border-t border-[#fecaca]/70 space-y-3"
            >
              <div className="flex items-center justify-between text-xs font-bold text-[#991b1b]">
                <span className="flex items-center gap-1.5">
                  <Activity size={14} /> Execution Log Telemetry
                </span>
                <button
                  type="button"
                  onClick={fetchTelemetry}
                  disabled={isLoadingTelemetry}
                  className="hover:underline flex items-center gap-1 text-[11px] font-medium"
                >
                  <RefreshCw size={11} className={isLoadingTelemetry ? 'animate-spin' : ''} />
                  Refresh Logs
                </button>
              </div>

              <div
                data-testid="pipeline-logs-list"
                className="max-h-48 overflow-y-auto rounded-xl bg-[#1e293b] p-3 text-left font-mono text-[11px] text-[#e2e8f0] space-y-1.5"
              >
                {telemetry && telemetry.logs && telemetry.logs.length > 0 ? (
                  telemetry.logs.map((log: PipelineExecutionLogData) => (
                    <div
                      key={log.id}
                      className="border-b border-slate-700/60 pb-1 last:border-0 last:pb-0"
                    >
                      <span className="text-slate-400">[{log.stage}]</span>{' '}
                      <span
                        className={
                          log.status === 'SUCCESS'
                            ? 'text-emerald-400'
                            : log.status === 'RETRY'
                            ? 'text-amber-400'
                            : log.status === 'DEGRADED'
                            ? 'text-yellow-300'
                            : 'text-rose-400'
                        }
                      >
                        {log.status}
                      </span>{' '}
                      <span className="text-slate-500">(attempt {log.attempt})</span>{' '}
                      {log.execution_time_ms > 0 && (
                        <span className="text-slate-400">{log.execution_time_ms}ms</span>
                      )}
                      {log.error_message && (
                        <div className="text-rose-300 pl-3 pt-0.5 truncate">
                          ↳ {log.error_message}
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="text-slate-400 italic">No execution log entries recorded yet.</div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 2. RETRYING STATE BANNER */}
      {isRetryingState && (
        <div
          data-testid="pipeline-retrying-badge"
          className="flex items-center justify-between rounded-2xl border border-[#fed7aa] bg-[#fffaf5] p-4 text-[#9a3412]"
        >
          <div className="flex items-center gap-3">
            <RotateCcw size={18} className="animate-spin text-[#ea580c] shrink-0" />
            <div>
              <p className="text-xs font-bold text-[#9a3412]">
                Pipeline Recovery In Progress...
              </p>
              <p className="text-[11px] text-[#c2410c]">
                Executing supervised retry with exponential backoff & jitter.
              </p>
            </div>
          </div>
          <span className="rounded-lg bg-[#ffedd5] px-2.5 py-1 text-[11px] font-bold text-[#c2410c]">
            Attempting Recovery
          </span>
        </div>
      )}

      {/* 3. GRACEFUL DEGRADATION NOTICE */}
      {isDegraded && !isFailed && (
        <div
          data-testid="pipeline-partial-alert"
          className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-2xl border border-[#fef3c7] bg-[#fffbeb] p-4 text-xs text-[#92400e]"
        >
          <div className="flex items-start gap-3">
            <ShieldAlert size={18} className="shrink-0 text-[#d97706] mt-0.5" />
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-[#92400e]">
                  Graceful Degradation Active (US-40)
                </span>
                <span className="rounded-full bg-[#fde68a] px-2 py-0.5 text-[10px] font-black uppercase text-[#854d0e]">
                  100% Speech Mode
                </span>
              </div>
              <p className="mt-0.5 text-[11px] text-[#78350f] leading-relaxed">
                {video.presentation_score?.notes ||
                  'Computer vision landmarks were obstructed or unreadable. Presentation evaluation was automatically preserved and scored 100% on vocal clarity and pacing.'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
            <button
              type="button"
              onClick={handleRetry}
              disabled={isRetrying}
              data-testid="button-pipeline-retry-degraded"
              className="inline-flex items-center gap-1.5 rounded-xl border border-[#d97706] bg-white px-3 py-1.5 text-xs font-bold text-[#b45309] hover:bg-[#fef3c7] transition cursor-pointer"
            >
              <RotateCcw size={13} className={isRetrying ? 'animate-spin' : ''} />
              <span>{isRetrying ? 'Retrying...' : 'Re-run Analysis'}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
