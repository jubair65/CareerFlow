import React, { useState, useEffect } from 'react';
import {
  Shield,
  ShieldCheck,
  Mic,
  Camera,
  Database,
  Users,
  Lock,
  X,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  ExternalLink,
} from 'lucide-react';
import {
  apiRecordAIConsent,
  apiGetAIConsentPolicy,
  type AIConsentPolicy,
} from '../../api/consent';

interface AIConsentModalProps {
  isOpen: boolean;
  onAgree?: (consentToken: string) => void;
  onDecline?: () => void;
  onClose: () => void;
  email?: string;
  readOnlyNotice?: boolean;
  notify?: (message: string, tone?: 'success' | 'info' | 'error') => void;
}

export const AIConsentModal: React.FC<AIConsentModalProps> = ({
  isOpen,
  onAgree,
  onDecline,
  onClose,
  email,
  readOnlyNotice = false,
  notify,
}) => {
  const [agreed, setAgreed] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [policy, setPolicy] = useState<AIConsentPolicy | null>(null);
  const [loadingPolicy, setLoadingPolicy] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setAgreed(false);
      loadPolicy();
    }
  }, [isOpen]);

  const loadPolicy = async () => {
    try {
      setLoadingPolicy(true);
      const res = await apiGetAIConsentPolicy();
      setPolicy(res);
    } catch (err) {
      console.error('Failed to load AI consent policy', err);
    } finally {
      setLoadingPolicy(false);
    }
  };

  if (!isOpen) return null;

  const handleAgree = async () => {
    if (!agreed && !readOnlyNotice) return;
    try {
      setSubmitting(true);
      const res = await apiRecordAIConsent(true, email, policy?.version || 'v1.0');
      if (notify) {
        notify('AI Biometric and Evaluation Consent accepted.', 'success');
      }
      if (onAgree) {
        onAgree(res.consent_token);
      }
      onClose();
    } catch (err: any) {
      console.error('Failed to record consent', err);
      if (notify) {
        notify('Failed to save consent agreement. Please try again.', 'error');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleDecline = async () => {
    try {
      setSubmitting(true);
      await apiRecordAIConsent(false, email, policy?.version || 'v1.0');
      if (notify) {
        notify('AI analysis consent was declined. Video capture is paused.', 'info');
      }
      if (onDecline) {
        onDecline();
      }
      onClose();
    } catch (err: any) {
      console.error('Failed to record refusal', err);
      if (onDecline) onDecline();
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200"
      data-testid="modal-ai-consent"
      role="dialog"
      aria-modal="true"
      aria-labelledby="ai-consent-title"
    >
      <div className="relative w-full max-w-2xl max-h-[90vh] flex flex-col rounded-3xl bg-white dark:bg-gray-900 shadow-2xl border border-gray-100 dark:border-gray-800 overflow-hidden">
        {/* Header */}
        <div className="flex items-start justify-between px-6 pt-6 pb-4 border-b border-gray-100 dark:border-gray-800 bg-gradient-to-r from-emerald-50/50 via-teal-50/30 to-indigo-50/40 dark:from-emerald-950/20 dark:via-teal-950/10 dark:to-indigo-950/20">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-11 h-11 rounded-2xl bg-emerald-600 text-white shadow-md shadow-emerald-600/20">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-900/60 text-emerald-800 dark:text-emerald-300">
                  Ethical AI Disclosure
                </span>
                <span
                  data-testid="badge-policy-version"
                  className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300"
                >
                  Version {policy?.version || '1.0'}
                </span>
              </div>
              <h2
                id="ai-consent-title"
                data-testid="text-ai-consent-title"
                className="text-lg font-black text-gray-900 dark:text-white mt-0.5"
              >
                AI Biometric & Presentation Evaluation Privacy Notice
              </h2>
            </div>
          </div>
          <button
            type="button"
            onClick={readOnlyNotice ? onClose : handleDecline}
            data-testid="button-close-ai-consent-modal"
            className="p-1.5 rounded-xl text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body - Scrollable */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5 text-sm text-gray-700 dark:text-gray-300">
          {/* Executive Notice Box */}
          <div className="p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60 flex items-start gap-3">
            <Shield className="w-5 h-5 text-emerald-600 dark:text-emerald-400 flex-shrink-0 mt-0.5" />
            <div className="text-xs space-y-1">
              <p className="font-bold text-emerald-900 dark:text-emerald-200">
                EU AI Act & GDPR Article 9 Compliance Statement
              </p>
              <p className="text-emerald-800 dark:text-emerald-300/90 leading-relaxed">
                CareerFlow is committed to transparent and ethical artificial intelligence in hiring. Before recording or uploading your presentation, we require your explicit consent to analyze your vocal telemetry, facial orientation, and presentation posture.
              </p>
            </div>
          </div>

          {/* Core Feature Breakdown Cards */}
          <div className="space-y-3">
            {/* Audio Telemetry */}
            <div className="p-4 rounded-2xl bg-gray-50 dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700/60 space-y-1.5">
              <div className="flex items-center gap-2 font-bold text-xs text-gray-900 dark:text-white">
                <Mic className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                <span>1. Audio & Speech Telemetry</span>
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
                Acoustic speech signals are processed to evaluate speaking pace (words per minute), pause intervals, articulation clarity, vocal energy, and filler word frequency. Raw audio is evaluated through private, sandboxed speech models and is never shared with external advertisers.
              </p>
            </div>

            {/* Facial Telemetry & Posture */}
            <div className="p-4 rounded-2xl bg-gray-50 dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700/60 space-y-1.5">
              <div className="flex items-center gap-2 font-bold text-xs text-gray-900 dark:text-white">
                <Camera className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                <span>2. Facial Telemetry & Posture Tracking</span>
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
                Computer vision models detect head pose orientation, eye contact engagement percentage, and upper-body posture alignment during delivery. We do <strong className="text-gray-900 dark:text-gray-200">NOT</strong> perform 1:N facial identity verification, nor do we construct persistent facial biometric signature templates.
              </p>
            </div>

            {/* Human Oversight */}
            <div className="p-4 rounded-2xl bg-gray-50 dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700/60 space-y-1.5">
              <div className="flex items-center gap-2 font-bold text-xs text-gray-900 dark:text-white">
                <Users className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                <span>3. Human-in-the-Loop & Anti-Discrimination</span>
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
                AI evaluation scores are objective screening and developmental aids. Final hiring and shortlisting decisions remain solely under human recruiter control. No candidate is rejected solely by an automated algorithm.
              </p>
            </div>

            {/* Data Retention & Storage */}
            <div className="p-4 rounded-2xl bg-gray-50 dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700/60 space-y-1.5">
              <div className="flex items-center gap-2 font-bold text-xs text-gray-900 dark:text-white">
                <Database className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                <span>4. Data Retention & Automated Purge Policy</span>
              </div>
              <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
                Uploaded and recorded videos are encrypted at rest. Practice sessions can be deleted on-demand with physical media unlinking (US-44). In accordance with automated retention rules (US-49), temporary staging artifacts and expired takes are systematically purged.
              </p>
            </div>
          </div>

          {/* Agreement Checkbox Section */}
          {!readOnlyNotice ? (
            <div className="pt-2">
              <label
                className="flex items-start gap-3 p-3.5 rounded-2xl bg-indigo-50/60 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-800 cursor-pointer select-none transition hover:bg-indigo-50"
              >
                <input
                  type="checkbox"
                  data-testid="checkbox-ai-consent-agree"
                  checked={agreed}
                  onChange={(e) => setAgreed(e.target.checked)}
                  className="mt-0.5 w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                />
                <span className="text-xs font-semibold text-gray-800 dark:text-gray-200 leading-snug">
                  I have read, understood, and explicitly agree to the AI audio and video biometric analysis of my presentation for job evaluation and practice feedback in compliance with ethical AI standards.
                </span>
              </label>
            </div>
          ) : (
            <div className="p-3 rounded-xl bg-gray-100 dark:bg-gray-800 text-xs text-gray-600 dark:text-gray-400">
              You are viewing the active policy notice. Your consent status is already active.
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-900/50 flex items-center justify-between gap-3">
          <button
            type="button"
            onClick={handleDecline}
            disabled={submitting}
            data-testid="button-ai-consent-decline"
            className="px-4 py-2 rounded-xl text-xs font-semibold text-gray-700 dark:text-gray-300 hover:bg-gray-200/70 dark:hover:bg-gray-800 transition disabled:opacity-50"
          >
            {readOnlyNotice ? 'Close Notice' : 'Decline & Cancel'}
          </button>

          {!readOnlyNotice && (
            <button
              type="button"
              onClick={handleAgree}
              disabled={!agreed || submitting}
              data-testid="button-ai-consent-agree"
              className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-600/20 transition disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Recording Consent...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>I Agree & Continue</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
export default AIConsentModal;

