import { useState, useEffect } from 'react';
import {
  Send,
  Building2,
  Mail,
  UserCheck,
  Star,
  CheckCircle2,
  AlertCircle,
  X,
  FileText,
  Clock,
  Sparkles,
} from 'lucide-react';
import {
  apiForwardShortlist,
  type AgencyCrossClientApplicant,
  type ClientCompany,
} from '../../api/recruitment';
import type { Notify } from '../dashboard/DashboardShared';

interface ForwardCandidatesModalProps {
  isOpen?: boolean;
  candidates: AgencyCrossClientApplicant[];
  clients: ClientCompany[];
  onClose: () => void;
  onForwardSuccess: (applicationIds: number[], clientName: string) => void;
  notify?: Notify;
}

export function ForwardCandidatesModal({
  isOpen = true,
  candidates,
  clients,
  onClose,
  onForwardSuccess,
  notify,
}: ForwardCandidatesModalProps) {
  if (isOpen === false) return null;

  // Determine if all selected candidates belong to the same client company
  const clientCompanyIds = Array.from(new Set(candidates.map((c) => c.client_company_id).filter(Boolean)));
  const clientCompanyNames = Array.from(new Set(candidates.map((c) => c.client_company_name).filter(Boolean)));
  const isCrossClient = clientCompanyIds.length > 1;
  const clientCompanyId = candidates.length > 0 ? candidates[0].client_company_id : null;
  const sameClient = !isCrossClient && candidates.length > 0;

  const initialClient = !isCrossClient
    ? (clientCompanyId ? clients.find((c) => c.id === clientCompanyId) : null) || clients[0] || null
    : null;

  const [selectedClientId, setSelectedClientId] = useState<number>(initialClient?.id || 0);
  const [recipientEmail, setRecipientEmail] = useState<string>(initialClient?.contact_email || '');
  const [recipientName, setRecipientName] = useState<string>(initialClient?.contact_person || '');
  const [notes, setNotes] = useState<string>(
    'Attached are the top shortlisted candidate profiles from our multi-modal AI evaluation round for your team review.'
  );
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Update contact fields when client selection changes
  const handleClientChange = (clientId: number) => {
    setSelectedClientId(clientId);
    const client = clients.find((c) => c.id === clientId);
    if (client) {
      setRecipientEmail(client.contact_email || '');
      setRecipientName(client.contact_person || '');
    }
  };

  // Synchronize client and recipient when candidates or clients change
  useEffect(() => {
    if (!isCrossClient && candidates.length > 0) {
      const cId = candidates[0].client_company_id;
      const client = clients.find((c) => c.id === cId) || clients[0];
      if (client) {
        setSelectedClientId(client.id);
        setRecipientEmail(client.contact_email || '');
        setRecipientName(client.contact_person || '');
      }
    } else if (clients.length > 0 && !selectedClientId) {
      setSelectedClientId(clients[0].id);
      setRecipientEmail(clients[0].contact_email || '');
      setRecipientName(clients[0].contact_person || '');
    }
  }, [candidates, clients, isCrossClient]);

  // Support ESC key to close modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Cannot forward if no candidates selected
    if (candidates.length === 0) {
      setError('Please select at least one candidate application to forward.');
      return;
    }

    // US-32 / Bonny UI review: Prevent submitting candidates from multiple client companies
    if (isCrossClient) {
      const errMsg = `Cannot forward candidates from multiple client companies (${clientCompanyNames.join(', ')}). All candidates in a forward batch must belong to the same client company.`;
      setError(errMsg);
      if (notify) {
        notify(errMsg, 'error');
      }
      return;
    }

    if (!selectedClientId) {
      setError('Please select a target client company.');
      return;
    }

    if (!recipientEmail.trim() || !recipientEmail.includes('@')) {
      setError('Please provide a valid recipient contact email.');
      return;
    }

    // Verify all candidates are shortlisted
    const unshortlisted = candidates.filter((c) => !c.is_shortlisted);
    if (unshortlisted.length > 0) {
      setError(
        `Only shortlisted candidates can be forwarded. ${unshortlisted[0].candidate_name} is not shortlisted.`
      );
      return;
    }

    try {
      setSubmitting(true);
      const applicationIds = candidates.map((c) => c.id);
      const response = await apiForwardShortlist({
        client_id: selectedClientId,
        application_ids: applicationIds,
        recipient_email: recipientEmail.trim(),
        recipient_name: recipientName.trim(),
        notes: notes.trim(),
      });

      const client = clients.find((c) => c.id === selectedClientId);
      const clientName = client?.name || 'Client';

      if (notify) {
        notify(response.message || `Successfully forwarded candidate profiles to ${clientName}!`, 'success');
      }

      onForwardSuccess(applicationIds, clientName);
      onClose();
    } catch (err: any) {
      const errMsg =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        'Failed to forward candidates to client. Please check your network and parameters.';
      setError(errMsg);
      if (notify) {
        notify(errMsg, 'error');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      data-testid="modal-forward-candidates"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs overflow-y-auto"
    >
      <div className="relative w-full max-w-xl rounded-2xl bg-white p-6 shadow-2xl border border-[#d9dbd1] my-8 animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-[#eef0e7] pb-4">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#e2f0e9] text-[#277254]">
              <Send size={20} />
            </div>
            <div>
              <h3 className="text-lg font-bold text-[#253142]" data-testid="heading-forward-candidates">
                Forward Shortlisted Candidates to Client
              </h3>
              <p className="text-xs text-[#7b8490]">
                Dispatch candidate dossiers with objective AI scores directly to client representatives.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            data-testid="button-close-forward-modal"
            className="rounded-lg p-1.5 text-[#7b8490] hover:bg-[#eef0e7] hover:text-[#253142] transition cursor-pointer"
          >
            <X size={18} />
          </button>
        </div>

        {/* Cross-Client Warning Alert */}
        {isCrossClient && (
          <div
            data-testid="alert-cross-client-error"
            className="mt-4 flex items-start gap-2.5 rounded-xl bg-[#fff1f0] p-3 text-xs text-[#cf1322] border border-[#ffa39e]"
          >
            <AlertCircle size={16} className="shrink-0 mt-0.5 text-[#cf1322]" />
            <div>
              <div className="font-bold">Multiple Client Companies Selected</div>
              <p className="mt-0.5 text-[11px] text-[#526072]">
                Selected candidates belong to different client companies: <strong>{clientCompanyNames.join(', ')}</strong>.
                Candidate dossiers must be forwarded to a single client company at a time. Please close this modal and select candidates for only one client company.
              </p>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div
            data-testid="alert-forward-error"
            className="mt-4 flex items-start gap-2.5 rounded-xl bg-[#f7e5e1] p-3 text-xs text-[#a33d35] border border-[#f1d6d1]"
          >
            <AlertCircle size={16} className="shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          {/* Client Company Selection */}
          <div>
            <label className="block text-xs font-bold text-[#526072] mb-1">
              Target Client Company <span className="text-red-500">*</span>
            </label>
            <select
              data-testid="select-forward-client"
              value={selectedClientId}
              onChange={(e) => handleClientChange(Number(e.target.value))}
              disabled={isCrossClient || (sameClient && candidates.length > 0)}
              className="w-full rounded-xl border border-[#d9dbd1] bg-white px-3.5 py-2.5 text-xs font-semibold text-[#253142] focus:border-[#277254] focus:outline-hidden focus:ring-2 focus:ring-[#277254]/20 transition disabled:bg-[#f6f6f3] disabled:text-[#526072] cursor-pointer"
            >
              {isCrossClient && (
                <option value={0}>-- Multiple Client Companies (Cannot Submit) --</option>
              )}
              {clients.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.industry})
                </option>
              ))}
            </select>
            {sameClient && (
              <p className="mt-1 text-[11px] text-[#7b8490]">
                Auto-assigned to client company based on selected candidate applications.
              </p>
            )}
            {isCrossClient && (
              <p className="mt-1 text-[11px] text-[#cf1322] font-semibold">
                Disabled because candidates from multiple clients ({clientCompanyNames.join(', ')}) are selected.
              </p>
            )}
          </div>

          {/* Recipient Details */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-[#526072] mb-1">
                Recipient Contact Email <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <Mail size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#7b8490]" />
                <input
                  type="email"
                  required
                  data-testid="input-recipient-email"
                  value={recipientEmail}
                  onChange={(e) => setRecipientEmail(e.target.value)}
                  placeholder="contact@client.com"
                  className="w-full rounded-xl border border-[#d9dbd1] bg-white pl-9 pr-3 py-2 text-xs font-medium text-[#253142] focus:border-[#277254] focus:outline-hidden focus:ring-2 focus:ring-[#277254]/20 transition"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-[#526072] mb-1">
                Recipient Contact Person
              </label>
              <div className="relative">
                <UserCheck size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#7b8490]" />
                <input
                  type="text"
                  data-testid="input-recipient-name"
                  value={recipientName}
                  onChange={(e) => setRecipientName(e.target.value)}
                  placeholder="Sarah Jenkins"
                  className="w-full rounded-xl border border-[#d9dbd1] bg-white pl-9 pr-3 py-2 text-xs font-medium text-[#253142] focus:border-[#277254] focus:outline-hidden focus:ring-2 focus:ring-[#277254]/20 transition"
                />
              </div>
            </div>
          </div>

          {/* Selected Candidates Dossier Preview */}
          <div>
            <label className="block text-xs font-bold text-[#526072] mb-1.5 flex items-center justify-between">
              <span>Candidates Included in Dossier ({candidates.length})</span>
              {candidates.length > 0 && (
                <span className="text-[11px] text-[#277254] font-semibold flex items-center gap-1">
                  <CheckCircle2 size={12} /> All verified shortlisted
                </span>
              )}
            </label>

            <div
              data-testid="container-forward-candidates-list"
              className="max-h-48 overflow-y-auto space-y-2 rounded-xl border border-[#eef0e7] bg-[#fafaf7] p-2.5"
            >
              {candidates.length === 0 ? (
                <div className="py-6 text-center text-xs text-[#7b8490]">
                  No candidates selected. Please close this modal and select shortlisted candidates using the checkboxes.
                </div>
              ) : (
                candidates.map((cand) => (
                  <div
                    key={cand.id}
                    data-testid={`forward-candidate-item-${cand.id}`}
                    className="flex items-center justify-between gap-3 rounded-lg bg-white p-2.5 border border-[#eef0e7] shadow-2xs text-xs"
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="grid h-7 w-7 place-items-center rounded-md bg-[#e2f0e9] text-[#277254] font-bold text-xs shrink-0">
                        {(cand.candidate_name || 'C')
                          .split(' ')
                          .map((n) => n[0])
                          .slice(0, 2)
                          .join('')}
                      </div>
                      <div className="min-w-0">
                        <div className="font-bold text-[#253142] truncate">
                          {cand.candidate_name}
                        </div>
                        <div className="text-[11px] text-[#7b8490] truncate">
                          {cand.client_company_name} • {cand.room_title} • {cand.candidate_email}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <div className="text-right">
                        <span className="inline-block px-2 py-0.5 rounded-md bg-[#e2f0e9] text-[#277254] font-bold text-[11px]">
                          {cand.final_score !== null ? `${Math.round(cand.final_score)}%` : 'N/A'} Final
                        </span>
                      </div>
                      <span className="inline-flex items-center gap-0.5 rounded-md bg-[#fff1c9] px-1.5 py-0.5 text-[10px] font-bold text-[#8a6a16]">
                        <Star size={10} className="fill-[#8a6a16]" /> Shortlisted
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Agency Cover Notes / Message */}
          <div>
            <label className="block text-xs font-bold text-[#526072] mb-1">
              Agency Cover Note to Client
            </label>
            <textarea
              rows={3}
              data-testid="input-forward-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add key highlights or notes for the client hiring panel..."
              className="w-full rounded-xl border border-[#d9dbd1] bg-white p-3 text-xs font-medium text-[#253142] focus:border-[#277254] focus:outline-hidden focus:ring-2 focus:ring-[#277254]/20 transition"
            />
          </div>

          {/* Modal Actions */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#eef0e7]">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              data-testid="button-cancel-forward"
              className="rounded-xl border border-[#d9dbd1] bg-white px-4 py-2 text-xs font-bold text-[#526072] hover:bg-[#eef0e7] transition cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || candidates.length === 0 || isCrossClient || !recipientEmail.trim()}
              data-testid="button-submit-forward"
              title={
                candidates.length === 0
                  ? 'Please select at least 1 candidate to forward'
                  : isCrossClient
                  ? 'Cannot forward candidates from multiple client companies'
                  : !recipientEmail.trim()
                  ? 'Please provide recipient email'
                  : undefined
              }
              className="inline-flex items-center gap-2 rounded-xl bg-[#277254] px-5 py-2 text-xs font-bold text-white shadow-xs hover:bg-[#205e45] transition disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              {submitting ? (
                <>
                  <Clock size={14} className="animate-spin" /> Forwarding Dossiers...
                </>
              ) : (
                <>
                  <Send size={14} /> Forward {candidates.length} Candidate{candidates.length === 1 ? '' : 's'}
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
