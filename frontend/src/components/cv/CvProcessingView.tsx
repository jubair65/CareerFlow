import { CheckCircle2, Circle } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';
import { useLocation } from 'wouter';
import { AppShell } from '../layout/AppShell';
import type { Notify } from '../dashboard/DashboardShared';
import { apiGetCurrentCV, apiGenerateCVFeedback } from '../../api/cv';

interface StepItem {
  label: string;
  threshold: number;
}

const CV_ANALYSIS_STEPS: StepItem[] = [
  { label: 'Reading your document', threshold: 25 },
  { label: 'Matching skills to your target role', threshold: 50 },
  { label: 'Checking structure and clarity', threshold: 75 },
  { label: 'Preparing your suggestions', threshold: 100 },
];

export interface CvProcessingViewProps {
  progress: number;
}

export function CvProcessingView({ progress }: CvProcessingViewProps) {
  const clampedProgress = Math.min(100, Math.max(0, Math.round(progress)));

  return (
    <div
      className="flex min-h-[72vh] flex-col items-center justify-center px-4 py-8"
      data-testid="cv-processing-container"
    >
      {/* Squircle Icon with 4-Point Star and Sparkle Dots */}
      <div
        className="grid h-16 w-16 place-items-center rounded-2xl bg-[#253142] shadow-sm transition-transform duration-300 hover:scale-105"
        data-testid="ai-analysis-icon"
      >
        <svg
          viewBox="0 0 24 24"
          className="h-8 w-8 text-[#f5c84b]"
          fill="currentColor"
          aria-hidden="true"
        >
          {/* 4-point star with smooth concave arcs */}
          <path d="M12 2C12 7.5 7.5 12 2 12C7.5 12 12 16.5 12 22C12 16.5 16.5 12 22 12C16.5 12 12 7.5 12 2Z" />
          {/* Top-right sparkle dot */}
          <circle cx="19.5" cy="4.5" r="1.5" />
          {/* Bottom-left sparkle dot */}
          <circle cx="4.5" cy="19.5" r="1.2" />
        </svg>
      </div>

      {/* Eyebrow */}
      <span className="mt-6 text-xs font-bold uppercase tracking-[.2em] text-[#9e8338]">
        AI ANALYSIS
      </span>

      {/* Title */}
      <h1 className="mt-2 text-center text-3xl font-extrabold tracking-tight text-[#253142] sm:text-4xl">
        Looking for the signal.
      </h1>

      {/* Subtitle */}
      <p className="mt-3 max-w-lg text-center text-sm leading-relaxed text-[#687382]">
        This takes a few moments. You can leave this tab open while we make the useful parts visible.
      </p>

      {/* Analysis Progress Card */}
      <div className="mt-10 w-full max-w-[540px] rounded-2xl border border-[#d9dbd1]/80 bg-white p-6 shadow-xs sm:p-7">
        {/* Card Header */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-bold text-[#253142]">Analysis progress</span>
          <span className="text-xs font-semibold text-[#687382]" data-testid="analysis-progress-percent">
            {clampedProgress}%
          </span>
        </div>

        {/* Progress Bar */}
        <div className="mt-3.5 h-2 w-full overflow-hidden rounded-full bg-[#f2f4ec]">
          <div
            className="h-full rounded-full bg-[#f5c84b] transition-all duration-300 ease-out"
            style={{ width: `${clampedProgress}%` }}
            data-testid="analysis-progress-bar"
          />
        </div>

        {/* Sequential Checklist */}
        <div className="mt-7 space-y-4" data-testid="analysis-checklist">
          {CV_ANALYSIS_STEPS.map((step) => {
            const isCompleted = clampedProgress >= step.threshold;
            return (
              <div key={step.label} className="flex items-center gap-3">
                {isCompleted ? (
                  <CheckCircle2
                    size={18}
                    className="shrink-0 text-[#277254] transition-colors duration-200"
                    data-testid={`step-done-${step.label.toLowerCase().replace(/\s+/g, '-')}`}
                  />
                ) : (
                  <Circle
                    size={18}
                    className="shrink-0 text-[#ccd0c6] transition-colors duration-200"
                    strokeWidth={1.8}
                    data-testid={`step-pending-${step.label.toLowerCase().replace(/\s+/g, '-')}`}
                  />
                )}
                <span
                  className={`text-sm transition-colors duration-200 ${
                    isCompleted ? 'font-semibold text-[#253142]' : 'font-normal text-[#687382]'
                  }`}
                >
                  {step.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/**
 * Standalone page for direct navigation to /student/cv/processing
 */
export function CvProcessingPage({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();
  const [progress, setProgress] = useState(10);
  const notifyRef = useRef(notify);
  notifyRef.current = notify;
  const setLocationRef = useRef(setLocation);
  setLocationRef.current = setLocation;

  useEffect(() => {
    let apiDone = false;
    let apiError: any = null;

    apiGetCurrentCV()
      .then((cv) => {
        if (!cv) {
          throw new Error('No active CV found. Please upload a CV first.');
        }
        return apiGenerateCVFeedback(cv.id);
      })
      .then(() => {
        apiDone = true;
      })
      .catch((err) => {
        apiError = err;
      });

    const progressTimer = setInterval(() => {
      if (isCancelled) return;

      if (apiError) {
        clearInterval(progressTimer);
        notifyRef.current(
          apiError?.response?.data?.error ||
            apiError?.response?.data?.detail ||
            apiError?.message ||
            'Failed to analyze CV. Please try again.',
          'error'
        );
        setLocationRef.current('/student/cv');
        return;
      }

      if (currentPct < 92) {
        currentPct += 1.5;
        setProgress(Math.round(currentPct));
      } else if (apiDone) {
        clearInterval(progressTimer);
        setProgress(100);
        setTimeout(() => {
          if (!isCancelled) {
            setLocationRef.current('/student/cv/results');
          }
        }, 700);
      }
    }, 50);

    return () => {
      isCancelled = true;
      clearInterval(progressTimer);
    };
  }, []);

  return (
    <AppShell role="student" notify={notify}>
      <CvProcessingView progress={progress} />
    </AppShell>
  );
}
