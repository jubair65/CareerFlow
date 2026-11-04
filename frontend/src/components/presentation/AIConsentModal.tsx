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
      <div className="relative w-full max-w-2xl max-h-[90vh] flex flex-col rounded-2xl bg-white shadow-2xl border border-[#d9dbd1] overflow-hidden">
        {/* Header */}
        <div className="flex items-start justify-between px-6 pt-6 pb-4 border-b border-[#ecefe7] bg-[#fbfaf5]">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-11 h-11 rounded-2xl bg-[#277254] text-white shadow-xs">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-[#e2f0e9] text-[#277254] border border-[#b8d8c7]">
                  Ethical AI Disclosure
                </span>
                <span
                  data-testid="badge-policy-version"
                  className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-[#eef0e7] text-[#253142]"
                >
                  Version {policy?.version || '1.0'}
                </span>
              </div>
              <h2
                id="ai-consent-title"
                data-testid="text-ai-consent-title"
                className="text-lg font-bold text-[#253142] mt-0.5"
              >
                AI Biometric & Presentation Evaluation Privacy Notice
              </h2>
            </div>
          </div>
          <button
            type="button"
            onClick={readOnlyNotice ? onClose : handleDecline}
            data-testid="button-close-ai-consent-modal"
            className="p-1.5 rounded-xl text-[#687382] hover:text-[#253142] hover:bg-[#f4f6ef] transition cursor-pointer"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body - Scrollable */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5 text-sm text-[#526072]">
          {/* Executive Notice Box */}
          <div className="p-4 rounded-2xl bg-[#f4f6ef] border border-[#d9dbd1] flex items-start gap-3">
            <Shield className="w-5 h-5 text-[#277254] flex-shrink-0 mt-0.5" />
            <div className="text-xs space-y-1">
              <p className="font-bold text-[#253142]">
                EU AI Act & GDPR Article 9 Compliance Statement
              </p>
              <p className="text-[#526072] leading-relaxed">
                CareerFlow is committed to transparent and ethical artificial intelligence in hiring. Before recording or uploading your presentation, we require your explicit consent to analyze your vocal telemetry, facial orientation, and presentation posture.
              </p>
            </div>
          </div>

          {/* Core Feature Breakdown Cards */}
          <div className="space-y-3">
            {/* Audio Telemetry */}
            <div className="p-4 rounded-2xl bg-[#fbfaf5] border border-[#d9dbd1] space-y-1.5">
              <div className="flex items-center gap-2 font-bold text-xs text-[#253142]">
                <Mic className="w-4 h-4 text-[#277254]" />
                <span>1. Audio & Speech Telemetry</span>
              </div>
              <p className="text-xs text-[#687382] leading-relaxed">
                Acoustic speech signals are processed to evaluate speaking pace (words per minute), pause intervals, articulation clarity, vocal energy, and filler word frequency. Raw audio is evaluated through private, sandboxed speech models and is never shared with external advertisers.
              </p>
            </div>

            {/* Facial Telemetry & Posture */}
            <div className="p-4 rounded-2xl bg-[#fbfaf5] border border-[#d9dbd1] space-y-1.5">
              <div className="flex items-center gap-2 font-bold text-xs text-[#253142]">
                <Camera className="w-4 h-4 text-[#277254]" />
                <span>2. Facial Telemetry & Posture Tracking</span>
              </div>
              <p className="text-xs text-[#687382] leading-relaxed">
                Computer vision models detect head pose orientation, eye contact engagement percentage, and upper-body posture alignment during delivery. We do <strong className="text-[#253142]">NOT</strong> perform 1:N facial identity verification, nor do we construct persistent facial biometric signature templates.
              </p>
            </div>

            {/* Human Oversight */}
            <div className="p-4 rounded-2xl bg-[#fbfaf5] border border-[#d9dbd1] space-y-1.5">
              <div className="flex items-center gap-2 font-bold text-xs text-[#253142]">
                <Users className="w-4 h-4 text-[#9a7922]" />
                <span>3. Human-in-the-Loop & Anti-Discrimination</span>
              </div>
              <p className="text-xs text-[#687382] leading-relaxed">
                AI evaluation scores are objective screening and developmental aids. Final hiring and shortlisting decisions remain solely under human recruiter control. No candidate is rejected solely by an automated algorithm.
              </p>
            </div>

            {/* Data Retention & Storage */}
            <div className="p-4 rounded-2xl bg-[#fbfaf5] border border-[#d9dbd1] space-y-1.5">
              <div className="flex items-center gap-2 font-bold text-xs text-[#253142]">
                <Database className="w-4 h-4 text-[#277254]" />
                <span>4. Data Retention & Automated Purge Policy</span>
              </div>
              <p className="text-xs text-[#687382] leading-relaxed">
                Uploaded and recorded videos are encrypted at rest. Practice sessions can be deleted on-demand with physical media unlinking. In accordance with automated retention rules, temporary staging artifacts and expired takes are systematically purged.
              </p>
            </div>
          </div>

          {/* Agreement Checkbox Section */}
          {!readOnlyNotice ? (
            <div className="pt-2">
              <label
                className="flex items-start gap-3 p-3.5 rounded-2xl bg-[#f4f6ef] border border-[#d9dbd1] cursor-pointer select-none transition hover:bg-[#edf0e6]"
              >
                <input
                  type="checkbox"
                  data-testid="checkbox-ai-consent-agree"
                  checked={agreed}
                  onChange={(e) => setAgreed(e.target.checked)}
                  className="mt-0.5 w-4 h-4 rounded text-[#277254] focus:ring-[#277254] cursor-pointer"
                />
                <span className="text-xs font-semibold text-[#253142] leading-snug">
                  I have read, understood, and explicitly agree to the AI audio and video biometric analysis of my presentation for job evaluation and practice feedback in compliance with ethical AI standards.
                </span>
              </label>
            </div>
          ) : (
            <div className="p-3 rounded-xl bg-[#f4f6ef] text-xs text-[#526072] border border-[#d9dbd1]">
              You are viewing the active policy notice. Your consent status is already active.
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-[#ecefe7] bg-[#fbfaf5] flex items-center justify-between gap-3">
          <button
            type="button"
            onClick={handleDecline}
            disabled={submitting}
            data-testid="button-ai-consent-decline"
            className="px-4 py-2 rounded-xl text-xs font-semibold text-[#687382] hover:bg-[#ecefe7] hover:text-[#253142] transition disabled:opacity-50 cursor-pointer"
          >
            {readOnlyNotice ? 'Close Notice' : 'Decline & Cancel'}
          </button>

          {!readOnlyNotice && (
            <button
              type="button"
              onClick={handleAgree}
              disabled={!agreed || submitting}
              data-testid="button-ai-consent-agree"
              className="px-5 py-2 rounded-xl bg-[#277254] hover:bg-[#1f5c43] text-white text-xs font-bold shadow-xs transition disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2 cursor-pointer"
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

