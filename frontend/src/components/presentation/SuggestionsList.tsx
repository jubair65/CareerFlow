import { useState, useEffect } from 'react';
import {
  Sparkles,
  CheckCircle2,
  Zap,
  Clock,
  Copy,
  Check,
  RefreshCw,
  Lightbulb,
  Target,
  Quote,
  Flame,
  Volume2,
  Eye,
  UserCheck,
  AlertCircle
} from 'lucide-react';
import {
  apiGetPresentationSuggestions,
  apiGeneratePresentationSuggestions,
  type PresentationFeedbackData,
  type ImprovementItem
} from '../../api/presentation';
import type { Notify } from '../dashboard/DashboardShared';

interface SuggestionsListProps {
  videoId: number;
  initialFeedback?: PresentationFeedbackData | null;
  notify?: Notify;
}

export function SuggestionsList({ videoId, initialFeedback, notify }: SuggestionsListProps) {
  const [feedback, setFeedback] = useState<PresentationFeedbackData | null>(initialFeedback || null);
  const [isLoading, setIsLoading] = useState(!initialFeedback);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const fetchSuggestions = async () => {
      if (!videoId) return;
      setIsLoading(true);
      try {
        const data = await apiGetPresentationSuggestions(videoId);
        if (isMounted && data) {
          setFeedback(data);
        }
      } catch (err: any) {
        console.error('Failed to load AI suggestions:', err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    if (!initialFeedback) {
      fetchSuggestions();
    } else {
      setFeedback(initialFeedback);
      setIsLoading(false);
    }

    return () => {
      isMounted = false;
    };
  }, [videoId, initialFeedback]);

  const handleRefresh = async () => {
    if (isRefreshing || !videoId) return;
    setIsRefreshing(true);
    try {
      const data = await apiGeneratePresentationSuggestions(videoId);
      setFeedback(data);
      if (notify) {
        notify('AI improvement suggestions refreshed with latest analysis!', 'success');
      }
    } catch (err: any) {
      console.error('Failed to regenerate coaching feedback:', err);
      if (notify) {
        notify('Failed to regenerate feedback. Please try again.', 'error');
      }
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleCopy = () => {
    if (!feedback) return;
    const strengthsText = feedback.strengths.map((s) => `• ${s}`).join('\n');
    const drillsText = feedback.improvements
      .map((imp) => `• [${imp.category}] ${imp.observation}\n  Drill: ${imp.actionable_drill}`)
      .join('\n\n');

    const fullText = `=== AI PRESENTATION COACHING SUMMARY ===\n${feedback.summary}\n\n=== KEY STRENGTHS ===\n${strengthsText}\n\n=== TARGETED DRILLS ===\n${drillsText}\n\n=== PRACTICE TIP ===\n${feedback.practice_tip}`;

    navigator.clipboard.writeText(fullText).then(() => {
      setCopied(true);
      if (notify) {
        notify('Coaching feedback and action drills copied to clipboard!', 'info');
      }
      setTimeout(() => setCopied(false), 2500);
    });
  };

  const getCategoryIcon = (category: string) => {
    const cat = category.toLowerCase();
    if (cat.includes('pace') || cat.includes('speed') || cat.includes('wpm')) {
      return <Clock size={15} className="text-[#d97706]" />;
    }
    if (cat.includes('filler') || cat.includes('vocal') || cat.includes('voice')) {
      return <Volume2 size={15} className="text-[#a33d35]" />;
    }
    if (cat.includes('eye') || cat.includes('gaze') || cat.includes('camera')) {
      return <Eye size={15} className="text-[#2563eb]" />;
    }
    if (cat.includes('posture') || cat.includes('shoulder') || cat.includes('stance')) {
      return <UserCheck size={15} className="text-[#7c3aed]" />;
    }
    return <Target size={15} className="text-[#277254]" />;
  };

  const getCategoryBadgeClass = (category: string) => {
    const cat = category.toLowerCase();
    if (cat.includes('pace') || cat.includes('speed')) {
      return 'bg-[#fef3c7] text-[#92400e] border-[#fde68a]';
    }
    if (cat.includes('filler')) {
      return 'bg-[#fee2e2] text-[#991b1b] border-[#fecaca]';
    }
    if (cat.includes('eye')) {
      return 'bg-[#dbeafe] text-[#1e40af] border-[#bfdbfe]';
    }
    if (cat.includes('posture')) {
      return 'bg-[#f3e8ff] text-[#6b21a8] border-[#e9d5ff]';
    }
    return 'bg-[#e2f0e9] text-[#1b533d] border-[#c2e2d4]';
  };

  if (isLoading) {
    return (
      <div
        data-testid="container-presentation-suggestions-loading"
        className="rounded-2xl border border-[#d9dbd1] bg-white p-6 shadow-sm animate-pulse space-y-4"
      >
        <div className="flex items-center justify-between">
          <div className="h-6 w-48 rounded-lg bg-[#ecefe7]" />
          <div className="h-8 w-24 rounded-lg bg-[#ecefe7]" />
        </div>
        <div className="h-16 rounded-xl bg-[#f5f7f2]" />
        <div className="space-y-3 pt-2">
          <div className="h-20 rounded-xl bg-[#f5f7f2]" />
          <div className="h-20 rounded-xl bg-[#f5f7f2]" />
        </div>
      </div>
    );
  }

  if (!feedback) {
    return (
      <div
        data-testid="container-presentation-suggestions-empty"
        className="rounded-2xl border border-dashed border-[#d9dbd1] bg-[#fbfaf5] p-8 text-center"
      >
        <div className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-[#ecefe7] text-[#526072] mb-3">
          <Lightbulb size={24} />
        </div>
        <h4 className="text-base font-bold text-[#253142]">No Suggestions Generated Yet</h4>
        <p className="mt-1 text-xs text-[#687382] max-w-md mx-auto">
          Generate personalized feedback powered by Google Gemini to unlock actionable drills for your speaking cadence and body language.
        </p>
        <button
          type="button"
          onClick={handleRefresh}
          disabled={isRefreshing}
          data-testid="button-generate-first-feedback"
          className="mt-4 inline-flex items-center gap-2 rounded-xl bg-[#277254] px-4 py-2 text-xs font-bold text-white hover:bg-[#1f5b43] transition shadow-sm"
        >
          {isRefreshing ? (
            <>
              <RefreshCw size={14} className="animate-spin" /> Generating Coaching Drills...
            </>
          ) : (
            <>
              <Sparkles size={14} /> Generate AI Feedback
            </>
          )}
        </button>
      </div>
    );
  }

  return (
    <div
      data-testid="container-presentation-suggestions"
      className="space-y-6 rounded-2xl border border-[#d9dbd1] bg-white p-6 shadow-sm"
    >
      {/* HEADER SECTION */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#ecefe7] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-tr from-[#277254] to-[#3ca37c] text-white shadow-xs">
              <Sparkles size={15} />
            </div>
            <h3 className="text-lg font-bold text-[#253142]">AI Executive Speech Coach</h3>
            <span
              data-testid="badge-gemini-model"
              className="inline-flex items-center gap-1 rounded-md border border-[#c2e2d4] bg-[#eaf4ef] px-2 py-0.5 text-[10px] font-extrabold uppercase tracking-wider text-[#1e5c43]"
            >
              <Sparkles size={11} className="text-[#277254]" /> Powered by Gemini AI
            </span>
          </div>
          <p className="mt-1 text-xs text-[#687382]">
            Personalized, diagnostic recommendations and structured 2-minute drills synthesized from your audio & posture telemetry.
          </p>
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          <button
            type="button"
            onClick={handleCopy}
            data-testid="button-copy-feedback"
            className="inline-flex items-center gap-1.5 rounded-xl border border-[#d9dbd1] bg-white px-3 py-1.5 text-xs font-bold text-[#253142] hover:bg-[#fbfaf5] transition shadow-2xs"
            title="Copy all suggestions and drills to clipboard"
          >
            {copied ? (
              <>
                <Check size={14} className="text-[#277254]" />
                <span className="text-[#277254]">Copied!</span>
              </>
            ) : (
              <>
                <Copy size={14} className="text-[#687382]" />
                <span>Copy Drills</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={handleRefresh}
            disabled={isRefreshing}
            data-testid="button-regenerate-feedback"
            className="inline-flex items-center gap-1.5 rounded-xl bg-[#253142] px-3.5 py-1.5 text-xs font-bold text-[#faf7ef] hover:bg-[#33435a] transition disabled:opacity-60 shadow-2xs"
          >
            <RefreshCw size={13} className={isRefreshing ? 'animate-spin' : ''} />
            <span>{isRefreshing ? 'Analyzing...' : 'Refresh'}</span>
          </button>
        </div>
      </div>

      {/* EXECUTIVE SUMMARY */}
      <div
        data-testid="card-executive-summary"
        className="rounded-xl border border-[#dce9e1] bg-gradient-to-r from-[#f4f9f6] to-[#edf6f1] p-4.5"
      >
        <div className="flex items-start gap-3">
          <div className="grid h-8 w-8 place-items-center rounded-lg bg-[#277254] text-white shrink-0 mt-0.5 shadow-2xs">
            <Target size={16} />
          </div>
          <div>
            <span className="text-[11px] font-extrabold uppercase tracking-wider text-[#1e5c43]">
              Executive Takeaway
            </span>
            <p
              data-testid="text-suggestions-summary"
              className="mt-0.5 text-sm font-medium text-[#1e3a2f] leading-relaxed"
            >
              {feedback.summary}
            </p>
          </div>
        </div>
      </div>

      {/* 2-COLUMN GRID: STRENGTHS & PRACTICE TIP */}
      <div className="grid gap-5 md:grid-cols-2">
        {/* STRENGTHS */}
        <div className="rounded-xl border border-[#ecefe7] bg-[#fbfaf5] p-4.5 space-y-3">
          <div className="flex items-center gap-2">
            <span className="flex h-2 w-2 rounded-full bg-[#277254]" />
            <h4 className="text-xs font-extrabold uppercase tracking-wider text-[#253142]">
              Demonstrated Strengths
            </h4>
          </div>

          <div data-testid="list-strengths" className="space-y-2">
            {feedback.strengths.map((str, idx) => (
              <div
                key={idx}
                data-testid={`strength-item-${idx}`}
                className="flex items-start gap-2.5 rounded-lg border border-[#e2e8df] bg-white p-2.5 text-xs text-[#253142] shadow-2xs"
              >
                <CheckCircle2 size={16} className="text-[#277254] shrink-0 mt-0.5" />
                <span className="leading-snug font-medium">{str}</span>
              </div>
            ))}
          </div>
        </div>

        {/* PRACTICE SCRIPT TIP */}
        <div
          data-testid="card-practice-tip"
          className="rounded-xl border border-[#ecefe7] bg-[#fbfaf5] p-4.5 space-y-3 flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center gap-2">
              <span className="flex h-2 w-2 rounded-full bg-[#d97706]" />
              <h4 className="text-xs font-extrabold uppercase tracking-wider text-[#253142]">
                Pacing & Phrasing Cue
              </h4>
            </div>

            <div className="mt-3 relative rounded-xl border border-[#fde68a] bg-[#fffbeb] p-3.5 shadow-2xs">
              <Quote size={20} className="text-[#f59e0b] opacity-30 absolute top-2 right-2" />
              <p
                data-testid="text-practice-tip"
                className="text-xs font-medium italic text-[#78350f] leading-relaxed pr-5"
              >
                "{feedback.practice_tip}"
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-[11px] text-[#687382] border-t border-[#ecefe7] pt-2.5">
            <Zap size={13} className="text-[#d97706]" />
            <span>Apply deliberate 1-second silent pauses to highlight your core impact statements.</span>
          </div>
        </div>
      </div>

      {/* CRITICAL IMPROVEMENTS & ACTIONABLE DRILLS */}
      <div className="space-y-3.5 pt-1">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-5 w-1 rounded-full bg-[#a33d35]" />
            <h4 className="text-xs font-extrabold uppercase tracking-wider text-[#253142]">
              Targeted Improvement Drills
            </h4>
          </div>
          <span className="text-[11px] font-semibold text-[#687382]">
            {feedback.improvements.length} Actionable {feedback.improvements.length === 1 ? 'Focus Area' : 'Focus Areas'}
          </span>
        </div>

        <div data-testid="list-improvements" className="grid gap-3.5">
          {feedback.improvements.map((imp: ImprovementItem, idx: number) => (
            <div
              key={idx}
              data-testid={`improvement-card-${idx}`}
              className="overflow-hidden rounded-xl border border-[#d9dbd1] bg-white shadow-2xs transition hover:border-[#b8bdad]"
            >
              {/* Card Header with Category & Observation */}
              <div className="p-4 border-b border-[#ecefe7] bg-[#ffffff]">
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                  <span
                    data-testid={`badge-category-${idx}`}
                    className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-0.5 text-xs font-bold ${getCategoryBadgeClass(
                      imp.category
                    )}`}
                  >
                    {getCategoryIcon(imp.category)}
                    <span>{imp.category}</span>
                  </span>

                  <span className="text-[10px] font-bold text-[#8c96a3] uppercase tracking-wider">
                    Diagnostic Telemetry
                  </span>
                </div>

                <p
                  data-testid={`text-observation-${idx}`}
                  className="text-xs font-medium text-[#3b4754] leading-relaxed"
                >
                  {imp.observation}
                </p>
              </div>

              {/* Actionable Drill Callout Box */}
              <div
                data-testid={`card-drill-${idx}`}
                className="bg-[#fcfaf5] p-3.5 border-l-4 border-l-[#277254] flex items-start gap-3"
              >
                <div className="grid h-6 w-6 place-items-center rounded-md bg-[#277254] text-white shrink-0 mt-0.5">
                  <Zap size={13} />
                </div>
                <div className="space-y-0.5">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[11px] font-extrabold uppercase tracking-wide text-[#277254]">
                      2-Minute Practice Drill
                    </span>
                    <span className="rounded bg-[#e2f0e9] px-1.5 py-0.2 text-[9px] font-bold text-[#1b533d]">
                      Daily Routine
                    </span>
                  </div>
                  <p
                    data-testid={`text-drill-${idx}`}
                    className="text-xs font-semibold text-[#253142] leading-snug"
                  >
                    {imp.actionable_drill}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
