import { useState, useEffect } from 'react';
import {
  Award,
  Sparkles,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Info,
  Mic,
  Eye,
  Activity,
  Smile,
  Zap,
  TrendingUp,
  Volume2
} from 'lucide-react';
import {
  apiGetPresentationScore,
  apiCalculatePresentationScore,
  type PresentationScoreData
} from '../../api/presentation';
import { type Notify } from '../dashboard/DashboardShared';

interface PresentationScoreCardProps {
  videoId: number;
  initialScore?: PresentationScoreData | null;
  onScoreUpdated?: (newScore: PresentationScoreData) => void;
  notify?: Notify;
}

export function PresentationScoreCard({
  videoId,
  initialScore,
  onScoreUpdated,
  notify
}: PresentationScoreCardProps) {
  const [score, setScore] = useState<PresentationScoreData | null>(initialScore || null);
  const [isLoading, setIsLoading] = useState(!initialScore);
  const [isRecalculating, setIsRecalculating] = useState(false);

  const fetchScore = async () => {
    setIsLoading(true);
    try {
      const data = await apiGetPresentationScore(videoId);
      setScore(data);
      if (data && onScoreUpdated) {
        onScoreUpdated(data);
      }
    } catch (err: any) {
      console.error('Failed to load presentation score:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (initialScore) {
      setScore(initialScore);
    } else {
      fetchScore();
    }
  }, [videoId, initialScore]);

  const handleRecalculate = async () => {
    setIsRecalculating(true);
    try {
      const updated = await apiCalculatePresentationScore(videoId);
      setScore(updated);
      if (onScoreUpdated) onScoreUpdated(updated);
      if (notify) notify('Presentation score calculated successfully!', 'success');
    } catch (err: any) {
      console.error('Failed to recalculate score:', err);
      if (notify) notify('Failed to calculate presentation score. Ensure speech or vision data exists.', 'error');
    } finally {
      setIsRecalculating(false);
    }
  };

  const getTierInfo = (overall: number) => {
    if (overall >= 85) {
      return {
        label: 'Excellent',
        color: '#277254',
        bg: 'bg-[#e2f0e9]',
        text: 'text-[#277254]',
        border: 'border-[#277254]/20',
        description: 'Outstanding executive presence. Strong pacing and poised delivery.'
      };
    } else if (overall >= 70) {
      return {
        label: 'Competent',
        color: '#d97706',
        bg: 'bg-[#fef3c7]',
        text: 'text-[#d97706]',
        border: 'border-[#d97706]/20',
        description: 'Solid performance with minor opportunities for pacing or posture polish.'
      };
    }
    return {
      label: 'Needs Practice',
      color: '#dc2626',
      bg: 'bg-[#fee2e2]',
      text: 'text-[#dc2626]',
      border: 'border-[#dc2626]/20',
      description: 'Focus on filler word reduction and maintaining direct camera contact.'
    };
  };

  if (isLoading) {
    return (
      <div
        data-testid="presentation-score-card-loading"
        className="rounded-2xl border border-[#d9dbd1] bg-white p-6 shadow-sm animate-pulse"
      >
        <div className="flex items-center justify-between pb-4 border-b border-[#ecefe7]">
          <div className="h-6 w-48 bg-[#e8eae3] rounded" />
          <div className="h-8 w-24 bg-[#e8eae3] rounded-lg" />
        </div>
        <div className="mt-6 flex flex-col md:flex-row items-center gap-6">
          <div className="h-32 w-32 rounded-full bg-[#e8eae3]" />
          <div className="flex-1 space-y-3 w-full">
            <div className="h-4 w-full bg-[#e8eae3] rounded" />
            <div className="h-4 w-3/4 bg-[#e8eae3] rounded" />
            <div className="h-4 w-1/2 bg-[#e8eae3] rounded" />
          </div>
        </div>
      </div>
    );
  }

  if (!score) {
    return (
      <div
        data-testid="presentation-score-card-empty"
        className="rounded-2xl border border-[#d9dbd1] bg-white p-6 shadow-sm text-center"
      >
        <div className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-[#f4f6ef] text-[#253142]">
          <Award size={24} />
        </div>
        <h4 className="mt-3 text-base font-bold text-[#253142]">No Presentation Score Calculated</h4>
        <p className="mt-1 text-xs text-[#687382] max-w-md mx-auto">
          Synthesize speech pacing and behavioral vision metrics into your composite 0–100 score.
        </p>
        <button
          type="button"
          onClick={handleRecalculate}
          disabled={isRecalculating}
          data-testid="button-recalculate-score"
          className="mt-4 inline-flex items-center gap-2 rounded-xl bg-[#253142] px-4 py-2 text-xs font-bold text-white hover:bg-[#33435a] transition disabled:opacity-50"
        >
          <RotateCcw size={14} className={isRecalculating ? 'animate-spin' : ''} />
          {isRecalculating ? 'Calculating Score...' : 'Calculate Score Now'}
        </button>
      </div>
    );
  }

  const tier = getTierInfo(score.overall_score);

  // SVG Circular Gauge calculation
  const radius = 48;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score.overall_score / 100) * circumference;

  return (
    <div
      data-testid="presentation-score-card"
      className="overflow-hidden rounded-2xl border border-[#d9dbd1] bg-white p-6 shadow-sm space-y-6"
    >
      {/* CARD HEADER */}
      <div
        data-testid="score-card-header"
        className="flex flex-wrap items-center justify-between gap-3 border-b border-[#ecefe7] pb-4"
      >
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#e2f0e9] text-[#277254]">
            <Award size={22} />
          </div>
          <div>
            <h3 className="text-base font-bold text-[#253142]">Presentation Scorecard</h3>
            <p className="text-xs text-[#687382]">
              Composite multi-modal evaluation of speech & behavioral poise
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleRecalculate}
            disabled={isRecalculating}
            data-testid="button-recalculate-score"
            className="inline-flex items-center gap-1.5 rounded-lg border border-[#d9dbd1] bg-white px-3 py-1.5 text-xs font-bold text-[#253142] hover:bg-[#f4f6ef] transition cursor-pointer disabled:opacity-50"
            title="Recalculate score from latest speech and vision metrics"
          >
            <RotateCcw size={13} className={isRecalculating ? 'animate-spin' : ''} />
            <span>{isRecalculating ? 'Calculating...' : 'Recalculate'}</span>
          </button>
        </div>
      </div>

      {/* GRACEFUL DEGRADATION NOTICE (US-40 Alignment) */}
      {!score.has_behavioral_data && (
        <div
          data-testid="degradation-warning-banner"
          className="flex items-start gap-2.5 rounded-xl border border-[#fef3c7] bg-[#fffbeb] p-3 text-xs text-[#92400e]"
        >
          <Info size={16} className="shrink-0 text-[#d97706] mt-0.5" />
          <div>
            <span className="font-bold">Partial Evaluation Mode: </span>
            {score.notes || 'Video quality was insufficient for facial tracking; score evaluated based 100% on speech delivery.'}
          </div>
        </div>
      )}

      {/* HERO SCORE METRIC SECTION */}
      <div className="grid gap-6 md:grid-cols-12 items-center bg-[#fafaf7] p-5 rounded-2xl border border-[#edebe4]">
        {/* Animated SVG Ring */}
        <div className="md:col-span-4 flex flex-col items-center justify-center">
          <div className="relative flex items-center justify-center">
            <svg className="h-32 w-32 -rotate-90 transform" viewBox="0 0 120 120">
              <circle
                cx="60"
                cy="60"
                r={radius}
                stroke="#e2e6dc"
                strokeWidth="10"
                fill="transparent"
              />
              <circle
                data-testid="overall-score-gauge"
                cx="60"
                cy="60"
                r={radius}
                stroke={tier.color}
                strokeWidth="10"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                fill="transparent"
                className="transition-all duration-1000 ease-out"
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center text-center">
              <span
                data-testid="overall-score-value"
                className="text-3xl font-black text-[#253142] tracking-tight"
              >
                {score.overall_score}
              </span>
              <span className="text-[10px] uppercase font-bold text-[#687382]">out of 100</span>
            </div>
          </div>

          <div className="mt-2">
            <span
              data-testid="badge-score-grade"
              className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold ${tier.bg} ${tier.text} border ${tier.border}`}
            >
              <Sparkles size={12} />
              {tier.label}
            </span>
          </div>
        </div>

        {/* Narrative & High-Level Breakdown */}
        <div className="md:col-span-8 space-y-3">
          <div>
            <h4 className="text-sm font-bold text-[#253142]">Evaluation Summary</h4>
            <p className="mt-1 text-xs text-[#526072] leading-relaxed">
              {tier.description}
            </p>
          </div>

          {/* Primary Split: Speech vs Behavioral */}
          <div className="grid grid-cols-2 gap-3 pt-2">
            {/* Speech Pillar */}
            <div
              data-testid="subscore-speech"
              className="rounded-xl border border-[#d9dbd1] bg-white p-3 shadow-xs"
            >
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="flex items-center gap-1.5 font-bold text-[#253142]">
                  <Mic size={14} className="text-[#277254]" /> Speech Delivery
                </span>
                <span className="font-extrabold text-[#277254]">{score.speech_score}/100</span>
              </div>
              <div className="h-2 w-full rounded-full bg-[#e8eae3] overflow-hidden">
                <div
                  className="h-full bg-[#277254] rounded-full transition-all duration-700"
                  style={{ width: `${score.speech_score}%` }}
                />
              </div>
              <span className="mt-1.5 block text-[10px] text-[#687382]">
                50% Weight • Pace & Filler Words
              </span>
            </div>

            {/* Behavioral Pillar */}
            <div
              data-testid="subscore-behavioral"
              className="rounded-xl border border-[#d9dbd1] bg-white p-3 shadow-xs"
            >
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="flex items-center gap-1.5 font-bold text-[#253142]">
                  <Eye size={14} className="text-[#3b82f6]" /> Behavioral Poise
                </span>
                <span className="font-extrabold text-[#3b82f6]">
                  {score.has_behavioral_data ? `${score.behavioral_score}/100` : 'N/A'}
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-[#e8eae3] overflow-hidden">
                <div
                  className="h-full bg-[#3b82f6] rounded-full transition-all duration-700"
                  style={{ width: `${score.has_behavioral_data ? score.behavioral_score : 0}%` }}
                />
              </div>
              <span className="mt-1.5 block text-[10px] text-[#687382]">
                50% Weight • Gaze, Posture & Face
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* DETAILED SUBSCORE BREAKDOWN GRID */}
      <div className="space-y-3">
        <h4 className="text-xs font-bold uppercase tracking-wider text-[#687382]">
          Subcategory Performance Diagnostics
        </h4>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {/* 1. Speaking Pace */}
          <div
            data-testid="subscore-pace"
            className="rounded-xl border border-[#e5e7df] bg-[#fafaf7] p-3.5 space-y-2"
          >
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-[#253142] flex items-center gap-1.5">
                <Volume2 size={14} className="text-[#277254]" /> Speaking Pace
              </span>
              <span className="font-bold text-[#253142]">{score.pace_score} pts</span>
            </div>
            <div className="h-1.5 w-full rounded-full bg-[#e5e7df] overflow-hidden">
              <div
                className="h-full bg-[#277254] rounded-full transition-all duration-500"
                style={{ width: `${score.pace_score}%` }}
              />
            </div>
            <p className="text-[11px] text-[#687382]">
              Benchmark: 130–160 Words Per Minute
            </p>
          </div>

          {/* 2. Filler Word Control */}
          <div
            data-testid="subscore-filler"
            className="rounded-xl border border-[#e5e7df] bg-[#fafaf7] p-3.5 space-y-2"
          >
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-[#253142] flex items-center gap-1.5">
                <Zap size={14} className="text-[#d97706]" /> Filler Word Control
              </span>
              <span className="font-bold text-[#253142]">{score.filler_score} pts</span>
            </div>
            <div className="h-1.5 w-full rounded-full bg-[#e5e7df] overflow-hidden">
              <div
                className="h-full bg-[#d97706] rounded-full transition-all duration-500"
                style={{ width: `${score.filler_score}%` }}
              />
            </div>
            <p className="text-[11px] text-[#687382]">
              -5 pts per occurrence ("um", "like", "uh")
            </p>
          </div>

          {/* 3. Eye Contact */}
          <div
            data-testid="subscore-eye-contact"
            className="rounded-xl border border-[#e5e7df] bg-[#fafaf7] p-3.5 space-y-2"
          >
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-[#253142] flex items-center gap-1.5">
                <Eye size={14} className="text-[#3b82f6]" /> Eye Contact Gaze
              </span>
              <span className="font-bold text-[#253142]">{score.eye_contact_score}%</span>
            </div>
            <div className="h-1.5 w-full rounded-full bg-[#e5e7df] overflow-hidden">
              <div
                className="h-full bg-[#3b82f6] rounded-full transition-all duration-500"
                style={{ width: `${score.eye_contact_score}%` }}
              />
            </div>
            <p className="text-[11px] text-[#687382]">
              Ratio of frames candidate focuses on lens
            </p>
          </div>

          {/* 4. Posture Stability */}
          <div
            data-testid="subscore-posture"
            className="rounded-xl border border-[#e5e7df] bg-[#fafaf7] p-3.5 space-y-2"
          >
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-[#253142] flex items-center gap-1.5">
                <Activity size={14} className="text-[#8b5cf6]" /> Posture Stability
              </span>
              <span className="font-bold text-[#253142]">{score.posture_score} pts</span>
            </div>
            <div className="h-1.5 w-full rounded-full bg-[#e5e7df] overflow-hidden">
              <div
                className="h-full bg-[#8b5cf6] rounded-full transition-all duration-500"
                style={{ width: `${score.posture_score}%` }}
              />
            </div>
            <p className="text-[11px] text-[#687382]">
              Shoulder horizontal alignment & steady posture
            </p>
          </div>

          {/* 5. Facial Engagement */}
          <div
            data-testid="subscore-engagement"
            className="rounded-xl border border-[#e5e7df] bg-[#fafaf7] p-3.5 space-y-2 sm:col-span-2 lg:col-span-2"
          >
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-[#253142] flex items-center gap-1.5">
                <Smile size={14} className="text-[#ec4899]" /> Facial Engagement & Energy
              </span>
              <span className="font-bold text-[#253142]">{score.engagement_score} pts</span>
            </div>
            <div className="h-1.5 w-full rounded-full bg-[#e5e7df] overflow-hidden">
              <div
                className="h-full bg-[#ec4899] rounded-full transition-all duration-500"
                style={{ width: `${score.engagement_score}%` }}
              />
            </div>
            <p className="text-[11px] text-[#687382]">
              Expressiveness, warmth, and attentive responsiveness
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
