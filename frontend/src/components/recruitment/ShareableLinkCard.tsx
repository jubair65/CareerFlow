import { useState, useEffect } from 'react';
import {
  Link2,
  Copy,
  Check,
  RefreshCw,
  Power,
  ExternalLink,
  ShieldCheck,
  AlertTriangle,
  Clock,
  X,
  Loader2,
  Sparkles,
  Info,
} from 'lucide-react';
import type { RecruitmentRoom } from '../../api/recruitment';
import {
  apiGetRoomShareLink,
  apiDeactivateRoomShareLink,
  apiActivateRoomShareLink,
  apiRegenerateRoomShareLink,
} from '../../api/recruitment';

interface ShareableLinkCardProps {
  room: RecruitmentRoom;
  onClose?: () => void;
  onRoomUpdated?: (updatedRoom: RecruitmentRoom) => void;
  notify?: (message: string, tone?: 'success' | 'info' | 'error') => void;
}

export function ShareableLinkCard({
  room,
  onClose,
  onRoomUpdated,
  notify,
}: ShareableLinkCardProps) {
  const [token, setToken] = useState<string>(room.share_token || '');
  const [isActive, setIsActive] = useState<boolean>(room.link_is_active ?? true);
  const [expiresAt, setExpiresAt] = useState<string | null>(room.link_expires_at ?? null);
  const [copied, setCopied] = useState<boolean>(false);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [showRegenConfirm, setShowRegenConfirm] = useState<boolean>(false);

  // Compute live full public URL
  const publicUrl = `${window.location.origin}/apply/${token}`;

  useEffect(() => {
    setToken(room.share_token || '');
    setIsActive(room.link_is_active ?? true);
    setExpiresAt(room.link_expires_at ?? null);
  }, [room]);

  // 1-Click Clipboard Copy
  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(publicUrl);
      setCopied(true);
      notify?.('Shareable application link copied to clipboard!', 'info');
      setTimeout(() => setCopied(false), 2500);
    } catch {
      notify?.('Failed to copy link to clipboard.', 'error');
    }
  };

  // Toggle Activate / Deactivate
  const handleToggleStatus = async () => {
    const nextAction = isActive ? 'deactivate' : 'activate';
    setLoadingAction(nextAction);
    try {
      const res = isActive
        ? await apiDeactivateRoomShareLink(room.id)
        : await apiActivateRoomShareLink(room.id);

      setIsActive(res.link.link_is_active);
      const updatedRoom: RecruitmentRoom = {
        ...room,
        link_is_active: res.link.link_is_active,
      };
      onRoomUpdated?.(updatedRoom);
      notify?.(
        res.link.link_is_active
          ? 'Application link activated! Candidates can now apply.'
          : 'Application link deactivated! Public access is now blocked.',
        res.link.link_is_active ? 'success' : 'info'
      );
    } catch {
      notify?.(`Failed to ${nextAction} application link.`, 'error');
    } finally {
      setLoadingAction(null);
    }
  };

  // Regenerate Token
  const handleRegenerate = async () => {
    setLoadingAction('regenerate');
    try {
      const res = await apiRegenerateRoomShareLink(room.id);
      setToken(res.link.share_token);
      setIsActive(res.link.link_is_active);
      setShowRegenConfirm(false);

      const updatedRoom: RecruitmentRoom = {
        ...room,
        share_token: res.link.share_token,
        link_is_active: res.link.link_is_active,
      };
      onRoomUpdated?.(updatedRoom);
      notify?.('New secure application link generated! Previous link has been invalidated.', 'success');
    } catch {
      notify?.('Failed to regenerate application link.', 'error');
    } finally {
      setLoadingAction(null);
    }
  };

  const handleOpenPreview = () => {
    window.open(`/apply/${token}`, '_blank');
  };

  return (
    <div
      data-testid="modal-shareable-link"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in overflow-y-auto"
    >
      <div
        className="relative w-full max-w-xl rounded-2xl bg-white border border-[#d9dbd1] shadow-2xl p-6 sm:p-7 space-y-6 my-8"
        data-testid="card-shareable-link"
      >
        {/* Header */}
        <div className="flex items-start justify-between border-b border-[#eef0e7] pb-4">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-2 rounded-full bg-[#e2f0e9] px-3 py-1 text-xs font-bold text-[#277254]">
              <Link2 size={13} />
              <span>US-21 • Candidate Application Portal Link</span>
            </div>
            <h2 className="text-xl font-black text-[#253142] tracking-tight">
              Shareable Job Application Link
            </h2>
            <p className="text-xs text-[#526072]">
              Hiring Room: <span className="font-semibold text-[#253142]">{room.title}</span> ({room.company_name})
            </p>
          </div>

          {onClose && (
            <button
              type="button"
              onClick={onClose}
              data-testid="button-close-shareable-link-modal"
              className="rounded-xl p-1.5 text-[#7b8490] hover:bg-[#eef0e7] hover:text-[#253142] transition"
              title="Close modal"
            >
              <X size={20} />
            </button>
          )}
        </div>

        {/* Status Banner */}
        <div
          data-testid="badge-link-status"
          className={`flex items-center justify-between rounded-xl p-3.5 border text-xs font-semibold ${
            isActive
              ? 'bg-[#edfdf4] border-[#bcf0da] text-[#03543f]'
              : 'bg-[#fdf2f2] border-[#f8b4b4] text-[#9b1c1c]'
          }`}
        >
          <div className="flex items-center gap-2">
            <div
              className={`h-2.5 w-2.5 rounded-full ${
                isActive ? 'bg-[#277254] animate-pulse' : 'bg-[#e02424]'
              }`}
            />
            <span>
              Link Status:{' '}
              <strong className="uppercase tracking-wider">
                {isActive ? 'Active (Accepting Applications)' : 'Deactivated (Access Blocked)'}
              </strong>
            </span>
          </div>

          <span className="text-[11px] opacity-80">
            {isActive ? 'Publicly Accessible' : 'HTTP 410 Gone'}
          </span>
        </div>

        {/* Link URL Box with Copy Button */}
        <div className="space-y-2">
          <label className="block text-xs font-bold text-[#253142] uppercase tracking-wider">
            Unique Candidate Application URL
          </label>
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <input
                type="text"
                readOnly
                value={publicUrl}
                data-testid="input-shareable-link-url"
                className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3.5 py-2.5 text-xs font-mono text-[#253142] select-all focus:outline-none focus:ring-2 focus:ring-[#277254]/30"
              />
            </div>

            <button
              type="button"
              onClick={handleCopyLink}
              data-testid="button-copy-shareable-link"
              className={`inline-flex items-center gap-1.5 rounded-xl px-4 py-2.5 text-xs font-bold transition shadow-xs ${
                copied
                  ? 'bg-[#277254] text-white'
                  : 'bg-[#253142] text-white hover:bg-[#1a2330]'
              }`}
            >
              {copied ? (
                <>
                  <Check size={14} />
                  <span>Copied!</span>
                </>
              ) : (
                <>
                  <Copy size={14} />
                  <span>Copy Link</span>
                </>
              )}
            </button>
          </div>
          <p className="text-[11px] text-[#7b8490] flex items-center gap-1.5 mt-1">
            <ShieldCheck size={13} className="text-[#277254] shrink-0" />
            <span>Uses cryptographic URL-safe token. Anyone with this link can view requirements and apply.</span>
          </p>
        </div>

        {/* Security & Action Controls */}
        <div className="space-y-3 rounded-2xl bg-[#fbfaf5] p-4 border border-[#eef0e7]">
          <span className="text-xs font-bold text-[#253142] uppercase tracking-wider block">
            Link Access Controls
          </span>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2.5">
            {/* Toggle Status */}
            <button
              type="button"
              onClick={handleToggleStatus}
              disabled={loadingAction !== null}
              data-testid="button-toggle-link-status"
              className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-xs font-bold transition border ${
                isActive
                  ? 'bg-white border-[#f8b4b4] text-[#9b1c1c] hover:bg-[#fdf2f2]'
                  : 'bg-[#277254] border-[#277254] text-white hover:bg-[#1f5c43]'
              }`}
            >
              {loadingAction === 'deactivate' || loadingAction === 'activate' ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <Power size={14} />
              )}
              <span>{isActive ? 'Deactivate Application Link' : 'Activate Application Link'}</span>
            </button>

            {/* Regenerate Link */}
            {!showRegenConfirm ? (
              <button
                type="button"
                onClick={() => setShowRegenConfirm(true)}
                disabled={loadingAction !== null}
                data-testid="button-regenerate-link"
                className="inline-flex items-center justify-center gap-1.5 rounded-xl border border-[#d9dbd1] bg-white px-3.5 py-2.5 text-xs font-semibold text-[#526072] hover:bg-[#f5f1e6] transition"
              >
                <RefreshCw size={13} />
                <span>Regenerate Token</span>
              </button>
            ) : (
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={handleRegenerate}
                  disabled={loadingAction === 'regenerate'}
                  data-testid="button-confirm-regenerate"
                  className="rounded-xl bg-[#b34a40] px-3 py-2 text-xs font-bold text-white hover:bg-[#923830] transition"
                >
                  {loadingAction === 'regenerate' ? 'Regenerating...' : 'Confirm'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowRegenConfirm(false)}
                  className="rounded-xl px-2.5 py-2 text-xs font-semibold text-[#526072] hover:bg-[#eef0e7]"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>

          {showRegenConfirm && (
            <div className="flex items-start gap-2 rounded-xl bg-[#fff8e6] border border-[#f5c84b]/60 p-3 text-xs text-[#8a6508]">
              <AlertTriangle size={15} className="shrink-0 mt-0.5 text-[#d97706]" />
              <span>
                Regenerating will instantly revoke the old link. Any applicants who have the old link will no longer be able to submit.
              </span>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between border-t border-[#eef0e7] pt-4 gap-3">
          <button
            type="button"
            onClick={handleOpenPreview}
            data-testid="button-preview-application-page"
            className="inline-flex items-center gap-1.5 rounded-xl border border-[#277254]/40 bg-[#e2f0e9]/50 px-3.5 py-2 text-xs font-bold text-[#277254] hover:bg-[#e2f0e9] transition"
          >
            <ExternalLink size={14} />
            <span>Open Public Application Page</span>
          </button>

          {onClose && (
            <button
              type="button"
              onClick={onClose}
              data-testid="button-done-shareable-link"
              className="rounded-xl bg-[#253142] px-5 py-2 text-xs font-bold text-white hover:bg-[#1a2330] transition"
            >
              Done
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
