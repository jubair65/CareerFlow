import { useState, useEffect } from 'react';
import {
  Sliders,
  FileText,
  Video,
  Sparkles,
  Save,
  RotateCcw,
  AlertCircle,
  CheckCircle2,
  HelpCircle,
  Calculator,
  X,
  Loader2,
  Layers,
} from 'lucide-react';
import type { RecruitmentRoom } from '../../api/recruitment';
import { apiUpdateRoomWeighting } from '../../api/recruitment';

interface WeightingConfigCardProps {
  room: RecruitmentRoom;
  onClose?: () => void;
  onWeightingSaved?: (updatedRoom: RecruitmentRoom) => void;
  notify?: (message: string, tone?: 'success' | 'info' | 'error') => void;
}

interface PresetOption {
  label: string;
  cv: number;
  video: number;
  description: string;
  icon: string;
}

const PRESETS: PresetOption[] = [
  {
    label: 'Balanced',
    cv: 50,
    video: 50,
    description: 'Equal split between credentials & presentation',
    icon: '⚖️',
  },
  {
    label: 'CV Focused',
    cv: 70,
    video: 30,
    description: 'Emphasis on verified skills & past work',
    icon: '📄',
  },
  {
    label: 'Video Focused',
    cv: 30,
    video: 70,
    description: 'Emphasis on verbal communication & delivery',
    icon: '🎥',
  },
  {
    label: 'Technical Depth',
    cv: 80,
    video: 20,
    description: 'Core developer / data engineering roles',
    icon: '💻',
  },
  {
    label: 'Client Facing',
    cv: 20,
    video: 80,
    description: 'Sales, consulting & presentation heavy roles',
    icon: '🗣️',
  },
];

export function WeightingConfigCard({
  room,
  onClose,
  onWeightingSaved,
  notify,
}: WeightingConfigCardProps) {
  const [cvWeight, setCvWeight] = useState<number>(room.cv_weight ?? 50);
  const [videoWeight, setVideoWeight] = useState<number>(room.video_weight ?? 50);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Simulation test scores
  const [simCvScore, setSimCvScore] = useState<number>(85);
  const [simVideoScore, setSimVideoScore] = useState<number>(75);

  useEffect(() => {
    setCvWeight(room.cv_weight ?? 50);
    setVideoWeight(room.video_weight ?? 50);
  }, [room]);

  const isSumValid = cvWeight + videoWeight === 100;
  const isDirty = cvWeight !== (room.cv_weight ?? 50) || videoWeight !== (room.video_weight ?? 50);

  // Linked Slider Handler for CV
  const handleCvChange = (newCv: number) => {
    const clampedCv = Math.min(100, Math.max(0, Math.round(newCv)));
    setCvWeight(clampedCv);
    setVideoWeight(100 - clampedCv);
    setErrorMessage(null);
    setSuccessMessage(null);
  };

  // Linked Slider Handler for Video
  const handleVideoChange = (newVideo: number) => {
    const clampedVideo = Math.min(100, Math.max(0, Math.round(newVideo)));
    setVideoWeight(clampedVideo);
    setCvWeight(100 - clampedVideo);
    setErrorMessage(null);
    setSuccessMessage(null);
  };

  // Preset Selection
  const applyPreset = (preset: PresetOption) => {
    setCvWeight(preset.cv);
    setVideoWeight(preset.video);
    setErrorMessage(null);
    setSuccessMessage(null);
  };

  // Reset to original values
  const handleReset = () => {
    setCvWeight(room.cv_weight ?? 50);
    setVideoWeight(room.video_weight ?? 50);
    setErrorMessage(null);
    setSuccessMessage(null);
  };

  // Save changes to API
  const handleSave = async () => {
    if (!isSumValid) {
      setErrorMessage(`Weights must sum to exactly 100% (currently ${cvWeight + videoWeight}%).`);
      return;
    }

    setIsSaving(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const response = await apiUpdateRoomWeighting(room.id, {
        cv_weight: cvWeight,
        video_weight: videoWeight,
      });

      setSuccessMessage('Evaluation weighting updated successfully!');
      notify?.('Evaluation weighting updated successfully!', 'success');
      onWeightingSaved?.(response.room);
    } catch (err: any) {
      const msg =
        err?.response?.data?.weights ||
        err?.response?.data?.message ||
        'Failed to update evaluation weighting. Please check your inputs.';
      setErrorMessage(typeof msg === 'string' ? msg : JSON.stringify(msg));
      notify?.('Failed to save evaluation weighting.', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  // Calculated Simulated Final Score
  const simulatedFinalScore = ((simCvScore * cvWeight) + (simVideoScore * videoWeight)) / 100;

  return (
    <div
      data-testid="weighting-config-modal"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in overflow-y-auto"
    >
      <div
        className="relative w-full max-w-2xl rounded-2xl bg-white border border-[#d9dbd1] shadow-2xl p-6 sm:p-7 space-y-6 my-8"
        data-testid="weighting-config-card"
      >
        {/* Header */}
        <div className="flex items-start justify-between border-b border-[#eef0e7] pb-4">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-2 rounded-full bg-[#e2f0e9] px-3 py-1 text-xs font-bold text-[#277254]">
              <Sliders size={13} />
              <span>US-20 • Evaluation Formula Configuration</span>
            </div>
            <h2 className="text-xl font-black text-[#253142] tracking-tight">
              CV vs. Video Evaluation Weighting
            </h2>
            <p className="text-xs text-[#526072]">
              Configuring room: <span className="font-semibold text-[#253142]">{room.title}</span> ({room.company_name})
            </p>
          </div>

          {onClose && (
            <button
              type="button"
              onClick={onClose}
              data-testid="button-close-weighting-modal"
              className="rounded-xl p-1.5 text-[#7b8490] hover:bg-[#eef0e7] hover:text-[#253142] transition"
              title="Close modal"
            >
              <X size={20} />
            </button>
          )}
        </div>

        {/* Status Alerts */}
        {errorMessage && (
          <div
            data-testid="alert-weighting-error"
            className="flex items-center gap-2.5 rounded-xl bg-[#fdf2f2] border border-[#f8b4b4] p-3.5 text-xs text-[#9b1c1c]"
          >
            <AlertCircle size={16} className="shrink-0" />
            <span className="font-semibold">{errorMessage}</span>
          </div>
        )}

        {successMessage && (
          <div
            data-testid="alert-weighting-success"
            className="flex items-center gap-2.5 rounded-xl bg-[#edfdf4] border border-[#bcf0da] p-3.5 text-xs text-[#03543f]"
          >
            <CheckCircle2 size={16} className="shrink-0" />
            <span className="font-semibold">{successMessage}</span>
          </div>
        )}

        {/* Quick Presets */}
        <div className="space-y-2.5">
          <label className="block text-xs font-bold text-[#253142] uppercase tracking-wider">
            Quick Recommendation Presets
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {PRESETS.map((preset) => {
              const isSelected = cvWeight === preset.cv && videoWeight === preset.video;
              return (
                <button
                  key={preset.label}
                  type="button"
                  onClick={() => applyPreset(preset)}
                  data-testid={`preset-button-${preset.cv}-${preset.video}`}
                  className={`flex flex-col text-left p-3 rounded-xl border transition-all text-xs ${
                    isSelected
                      ? 'bg-[#277254]/10 border-[#277254] text-[#277254] font-bold shadow-xs'
                      : 'bg-[#fbfaf5] border-[#eef0e7] text-[#526072] hover:border-[#277254]/50 hover:bg-white'
                  }`}
                >
                  <div className="flex items-center justify-between w-full mb-1">
                    <span className="text-sm">{preset.icon}</span>
                    <span
                      className={`text-[11px] font-bold px-1.5 py-0.5 rounded-md ${
                        isSelected ? 'bg-[#277254] text-white' : 'bg-[#eef0e7] text-[#526072]'
                      }`}
                    >
                      {preset.cv}% / {preset.video}%
                    </span>
                  </div>
                  <span className="font-bold text-[#253142]">{preset.label}</span>
                  <span className="text-[10px] text-[#7b8490] leading-tight line-clamp-1 mt-0.5">
                    {preset.description}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Dual Linked Sliders */}
        <div className="space-y-5 rounded-2xl bg-[#fbfaf5] p-4 sm:p-5 border border-[#eef0e7]">
          {/* CV Weight Slider Control */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#277254] text-white shadow-xs">
                  <FileText size={15} />
                </div>
                <div>
                  <span className="text-xs font-bold text-[#253142]">CV Match Weight</span>
                  <p className="text-[10px] text-[#7b8490]">Semantic skills & experience relevance</p>
                </div>
              </div>

              <div className="flex items-center gap-1.5">
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={cvWeight}
                  onChange={(e) => handleCvChange(Number(e.target.value))}
                  data-testid="input-cv-weight-number"
                  className="w-16 rounded-lg border border-[#d9dbd1] bg-white px-2 py-1 text-center text-sm font-bold text-[#277254] focus:border-[#277254] focus:outline-none"
                />
                <span className="text-xs font-bold text-[#277254]">%</span>
              </div>
            </div>

            <input
              type="range"
              min="0"
              max="100"
              step="1"
              value={cvWeight}
              onChange={(e) => handleCvChange(Number(e.target.value))}
              data-testid="slider-cv-weight"
              className="w-full accent-[#277254] cursor-pointer h-2 bg-[#eef0e7] rounded-lg appearance-none"
            />
          </div>

          {/* Video Weight Slider Control */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#4f46e5] text-white shadow-xs">
                  <Video size={15} />
                </div>
                <div>
                  <span className="text-xs font-bold text-[#253142]">Video Presentation Weight</span>
                  <p className="text-[10px] text-[#7b8490]">Speech clarity, pacing & behavioral traits</p>
                </div>
              </div>

              <div className="flex items-center gap-1.5">
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={videoWeight}
                  onChange={(e) => handleVideoChange(Number(e.target.value))}
                  data-testid="input-video-weight-number"
                  className="w-16 rounded-lg border border-[#d9dbd1] bg-white px-2 py-1 text-center text-sm font-bold text-[#4f46e5] focus:border-[#4f46e5] focus:outline-none"
                />
                <span className="text-xs font-bold text-[#4f46e5]">%</span>
              </div>
            </div>

            <input
              type="range"
              min="0"
              max="100"
              step="1"
              value={videoWeight}
              onChange={(e) => handleVideoChange(Number(e.target.value))}
              data-testid="slider-video-weight"
              className="w-full accent-[#4f46e5] cursor-pointer h-2 bg-[#eef0e7] rounded-lg appearance-none"
            />
          </div>

          {/* Visual Dual-Color Split Bar */}
          <div className="space-y-1.5 pt-2">
            <div className="flex items-center justify-between text-[11px] font-bold text-[#526072]">
              <span className="flex items-center gap-1 text-[#277254]">
                <span className="h-2 w-2 rounded-full bg-[#277254]"></span>
                CV: {cvWeight}%
              </span>
              <span className="text-xs font-black text-[#253142]">
                Total: {cvWeight + videoWeight}%
              </span>
              <span className="flex items-center gap-1 text-[#4f46e5]">
                <span className="h-2 w-2 rounded-full bg-[#4f46e5]"></span>
                Video: {videoWeight}%
              </span>
            </div>

            <div
              className="h-3 w-full overflow-hidden rounded-full bg-[#eef0e7] flex"
              data-testid="weighting-distribution-bar"
            >
              <div
                style={{ width: `${cvWeight}%` }}
                className="bg-[#277254] transition-all duration-300"
                title={`CV Weight: ${cvWeight}%`}
              />
              <div
                style={{ width: `${videoWeight}%` }}
                className="bg-[#4f46e5] transition-all duration-300"
                title={`Video Weight: ${videoWeight}%`}
              />
            </div>
          </div>
        </div>

        {/* Live Score Simulation Preview */}
        <div className="rounded-2xl border border-[#e2e8f0] bg-[#f8fafc] p-4 space-y-3">
          <div className="flex items-center gap-2 text-xs font-bold text-[#334155]">
            <Calculator size={14} className="text-[#4f46e5]" />
            <span>Interactive Score Calculator Preview</span>
          </div>

          <p className="text-[11px] text-[#64748b]">
            Simulate how a candidate scoring below would be ranked under this weighting formula:
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div className="rounded-xl bg-white border border-[#e2e8f0] p-2.5">
              <label className="text-[10px] font-bold text-[#64748b] block mb-1">
                Candidate CV Score
              </label>
              <div className="flex items-center gap-1">
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={simCvScore}
                  onChange={(e) => setSimCvScore(Math.min(100, Math.max(0, Number(e.target.value))))}
                  data-testid="input-sim-cv-score"
                  className="w-14 font-bold text-sm text-[#277254] border border-[#e2e8f0] rounded px-1.5 py-0.5"
                />
                <span className="text-xs font-semibold text-[#64748b]">/ 100</span>
              </div>
            </div>

            <div className="rounded-xl bg-white border border-[#e2e8f0] p-2.5">
              <label className="text-[10px] font-bold text-[#64748b] block mb-1">
                Candidate Video Score
              </label>
              <div className="flex items-center gap-1">
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={simVideoScore}
                  onChange={(e) => setSimVideoScore(Math.min(100, Math.max(0, Number(e.target.value))))}
                  data-testid="input-sim-video-score"
                  className="w-14 font-bold text-sm text-[#4f46e5] border border-[#e2e8f0] rounded px-1.5 py-0.5"
                />
                <span className="text-xs font-semibold text-[#64748b]">/ 100</span>
              </div>
            </div>

            <div className="col-span-2 sm:col-span-1 rounded-xl bg-[#277254]/10 border border-[#277254]/30 p-2.5 flex flex-col justify-center">
              <span className="text-[10px] font-bold text-[#277254] block">Final Weighted Score</span>
              <div className="flex items-baseline gap-1" data-testid="simulated-final-score">
                <span className="text-lg font-black text-[#277254]">
                  {simulatedFinalScore.toFixed(1)}%
                </span>
              </div>
            </div>
          </div>

          <div className="text-[10px] text-[#64748b] font-mono bg-white/80 p-2 rounded-lg border border-[#e2e8f0]">
            Formula: ({simCvScore} × {cvWeight}%) + ({simVideoScore} × {videoWeight}%) ={' '}
            <span className="font-bold text-[#277254]">{simulatedFinalScore.toFixed(1)}%</span>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between border-t border-[#eef0e7] pt-4 gap-3">
          <button
            type="button"
            onClick={handleReset}
            disabled={!isDirty || isSaving}
            data-testid="button-reset-weighting"
            className="inline-flex items-center gap-1.5 rounded-xl border border-[#d9dbd1] bg-white px-3.5 py-2 text-xs font-semibold text-[#526072] hover:bg-[#fbfaf5] disabled:opacity-50 transition"
          >
            <RotateCcw size={14} />
            <span>Reset to Saved</span>
          </button>

          <div className="flex items-center gap-2">
            {onClose && (
              <button
                type="button"
                onClick={onClose}
                data-testid="button-cancel-weighting"
                className="rounded-xl px-4 py-2 text-xs font-semibold text-[#526072] hover:bg-[#eef0e7] transition"
              >
                Cancel
              </button>
            )}

            <button
              type="button"
              onClick={handleSave}
              disabled={isSaving || !isSumValid || !isDirty}
              data-testid="button-save-weighting"
              className="inline-flex items-center gap-2 rounded-xl bg-[#277254] px-5 py-2.5 text-xs font-bold text-white shadow-md hover:bg-[#1f5c43] disabled:opacity-50 transition"
            >
              {isSaving ? (
                <>
                  <Loader2 size={15} className="animate-spin" />
                  <span>Saving Weighting...</span>
                </>
              ) : (
                <>
                  <Save size={15} />
                  <span>Save Weighting</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
