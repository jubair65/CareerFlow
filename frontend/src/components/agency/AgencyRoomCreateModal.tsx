import { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import {
  X,
  Building2,
  BriefcaseBusiness,
  Layers,
  Sparkles,
  Loader2,
  AlertCircle,
  ExternalLink,
  Percent,
} from 'lucide-react';
import {
  apiGetAgencyClients,
  apiCreateAgencyRoom,
  type ClientCompany,
  type RecruitmentRoom,
} from '../../api/recruitment';
import type { Notify } from '../dashboard/DashboardShared';

interface AgencyRoomCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRoomCreated: (room: RecruitmentRoom) => void;
  notify: Notify;
  initialClientId?: number;
}

export function AgencyRoomCreateModal({
  isOpen,
  onClose,
  onRoomCreated,
  notify,
  initialClientId,
}: AgencyRoomCreateModalProps) {
  const [clients, setClients] = useState<ClientCompany[]>([]);
  const [clientsLoading, setClientsLoading] = useState(true);

  // Form State
  const [selectedClientId, setSelectedClientId] = useState<number | ''>(initialClientId || '');
  const [title, setTitle] = useState('');
  const [department, setDepartment] = useState('');
  const [roleCategory, setRoleCategory] = useState('Engineering');
  const [experienceLevel, setExperienceLevel] = useState<'ENTRY' | 'MID' | 'SENIOR' | 'LEAD'>('MID');
  const [description, setDescription] = useState('');
  const [cvWeight, setCvWeight] = useState(50);
  const [videoWeight, setVideoWeight] = useState(50);

  // Validation & Submission
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    if (isOpen) {
      setClientsLoading(true);
      apiGetAgencyClients({ status: 'active' })
        .then((data) => {
          setClients(data);
          if (initialClientId) {
            setSelectedClientId(initialClientId);
          } else if (data.length > 0 && !selectedClientId) {
            setSelectedClientId(data[0].id);
          }
        })
        .catch(() => {
          notify('Failed to load active client companies.', 'error');
        })
        .finally(() => {
          setClientsLoading(false);
        });
    }
  }, [isOpen, initialClientId]);

  if (!isOpen) return null;

  const selectedClient = clients.find((c) => c.id === Number(selectedClientId));

  const handleCvWeightChange = (val: number) => {
    const clamped = Math.max(0, Math.min(100, val));
    setCvWeight(clamped);
    setVideoWeight(100 - clamped);
  };

  const handleVideoWeightChange = (val: number) => {
    const clamped = Math.max(0, Math.min(100, val));
    setVideoWeight(clamped);
    setCvWeight(100 - clamped);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setErrorMessage('');

    if (!selectedClientId) {
      setErrorMessage('Please select a client company.');
      return;
    }

    const trimmedTitle = title.trim();
    if (!trimmedTitle) {
      setErrorMessage('Job title is required.');
      return;
    }
    if (trimmedTitle.length < 3) {
      setErrorMessage('Job title must be at least 3 characters long.');
      return;
    }

    if (cvWeight + videoWeight !== 100) {
      setErrorMessage('CV weight and Video weight must total exactly 100%.');
      return;
    }

    try {
      setSubmitting(true);
      const res = await apiCreateAgencyRoom({
        client_company: Number(selectedClientId),
        title: trimmedTitle,
        department: department.trim() || undefined,
        role_category: roleCategory,
        experience_level: experienceLevel,
        description: description.trim() || undefined,
        cv_weight: cvWeight,
        video_weight: videoWeight,
      });

      notify(`Recruitment room "${trimmedTitle}" created successfully for ${selectedClient?.name || 'client'}!`, 'success');
      onRoomCreated(res.room);
      onClose();
    } catch (err: any) {
      const respData = err?.response?.data;
      if (respData) {
        if (typeof respData === 'string') {
          setErrorMessage(respData);
        } else if (respData.client_company) {
          setErrorMessage(Array.isArray(respData.client_company) ? respData.client_company[0] : respData.client_company);
        } else if (respData.title) {
          setErrorMessage(Array.isArray(respData.title) ? respData.title[0] : respData.title);
        } else if (respData.weights) {
          setErrorMessage(respData.weights);
        } else if (respData.message) {
          setErrorMessage(respData.message);
        } else {
          setErrorMessage('Failed to create recruitment room. Please check input values.');
        }
      } else {
        setErrorMessage('Failed to create recruitment room. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      data-testid="modal-agency-create-room"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs overflow-y-auto"
    >
      <div className="relative w-full max-w-xl rounded-2xl bg-white p-6 shadow-2xl border border-[#d9dbd1] my-8 animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-[#eef0e7] pb-4">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#e2f0e9] text-[#277254]">
              <Building2 size={20} />
            </div>
            <div>
              <h3 className="text-lg font-bold text-[#253142]" data-testid="heading-agency-create-room">
                Create Client Recruitment Room
              </h3>
              <p className="text-xs text-[#7b8490]">
                Configure recruitment criteria and shareable link on behalf of your client company.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            data-testid="button-close-agency-create-room"
            className="rounded-lg p-1.5 text-[#7b8490] hover:bg-[#eef0e7] hover:text-[#253142] transition"
          >
            <X size={18} />
          </button>
        </div>

        {/* Error banner */}
        {errorMessage && (
          <div
            role="alert"
            data-testid="alert-agency-create-room-error"
            className="mt-4 flex items-center gap-2 rounded-xl bg-[#f7e5e1] px-4 py-2.5 text-xs font-semibold text-[#a33d35]"
          >
            <AlertCircle size={15} className="shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          {/* Client Company Selector */}
          <div>
            <label
              htmlFor="agency-client-selector"
              className="block text-xs font-bold uppercase tracking-wider text-[#526072] mb-1.5"
            >
              Client Company <span className="text-[#a33d35]">*</span>
            </label>
            {clientsLoading ? (
              <div className="flex items-center gap-2 rounded-xl border border-[#d9dbd1] bg-[#fafaf7] px-3.5 py-2.5 text-xs text-[#7b8490]">
                <Loader2 size={14} className="animate-spin text-[#277254]" /> Loading client companies...
              </div>
            ) : clients.length === 0 ? (
              <div
                data-testid="banner-no-clients"
                className="rounded-xl border border-[#f5c84b] bg-[#fbf5e6] p-3 text-xs text-[#735118]"
              >
                <div className="flex items-center gap-2 font-bold">
                  <AlertCircle size={15} /> No active client companies found.
                </div>
                <p className="mt-1">
                  You need at least one active client company before creating a Room.
                </p>
                <a
                  href="/agency/clients"
                  className="mt-2 inline-flex items-center gap-1 font-bold text-[#277254] hover:underline"
                >
                  Manage Client Companies <ExternalLink size={12} />
                </a>
              </div>
            ) : (
              <>
                <select
                  id="agency-client-selector"
                  data-testid="select-agency-client-company"
                  value={selectedClientId}
                  onChange={(e) => setSelectedClientId(Number(e.target.value))}
                  className="w-full rounded-xl border border-[#d9dbd1] bg-white px-3.5 py-2.5 text-sm font-semibold text-[#253142] focus:border-[#277254] focus:outline-hidden focus:ring-2 focus:ring-[#277254]/20 transition"
                  required
                >
                  <option value="" disabled>
                    -- Select Client Company --
                  </option>
                  {clients.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.industry})
                    </option>
                  ))}
                </select>
                {selectedClient && (
                  <div
                    data-testid="client-info-badge"
                    className="mt-2 flex items-center justify-between rounded-lg bg-[#fafaf7] px-3 py-1.5 text-xs text-[#526072] border border-[#eef0e7]"
                  >
                    <span>
                      <strong>Industry:</strong> {selectedClient.industry}
                    </span>
                    <span>
                      <strong>Contact:</strong> {selectedClient.contact_person} ({selectedClient.contact_email})
                    </span>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Job Title */}
          <div>
            <label
              htmlFor="agency-room-title"
              className="block text-xs font-bold uppercase tracking-wider text-[#526072] mb-1.5"
            >
              Job Title <span className="text-[#a33d35]">*</span>
            </label>
            <input
              id="agency-room-title"
              type="text"
              data-testid="input-agency-room-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Senior Frontend Engineer, Financial Analyst"
              className="w-full rounded-xl border border-[#d9dbd1] bg-white px-3.5 py-2.5 text-sm font-medium text-[#253142] placeholder-[#7b8490]/60 focus:border-[#277254] focus:outline-hidden focus:ring-2 focus:ring-[#277254]/20 transition"
              required
            />
          </div>

          {/* Department & Role Category (2-col) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label
                htmlFor="agency-room-dept"
                className="block text-xs font-bold uppercase tracking-wider text-[#526072] mb-1.5"
              >
                Department
              </label>
              <input
                id="agency-room-dept"
                type="text"
                data-testid="input-agency-room-dept"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                placeholder="e.g. Tech, Finance, Ops"
                className="w-full rounded-xl border border-[#d9dbd1] bg-white px-3.5 py-2.5 text-sm font-medium text-[#253142] placeholder-[#7b8490]/60 focus:border-[#277254] focus:outline-hidden focus:ring-2 focus:ring-[#277254]/20 transition"
              />
            </div>

            <div>
              <label
                htmlFor="agency-room-category"
                className="block text-xs font-bold uppercase tracking-wider text-[#526072] mb-1.5"
              >
                Role Category
              </label>
              <select
                id="agency-room-category"
                data-testid="select-agency-room-category"
                value={roleCategory}
                onChange={(e) => setRoleCategory(e.target.value)}
                className="w-full rounded-xl border border-[#d9dbd1] bg-white px-3.5 py-2.5 text-sm font-semibold text-[#253142] focus:border-[#277254] focus:outline-hidden focus:ring-2 focus:ring-[#277254]/20 transition"
              >
                <option value="Engineering">Engineering</option>
                <option value="Design & UI">Design & UI</option>
                <option value="Product & Strategy">Product & Strategy</option>
                <option value="Data & Analytics">Data & Analytics</option>
                <option value="Marketing">Marketing</option>
                <option value="Sales">Sales</option>
                <option value="Operations">Operations</option>
              </select>
            </div>
          </div>

          {/* Seniority Level */}
          <div>
            <label
              htmlFor="agency-room-level"
              className="block text-xs font-bold uppercase tracking-wider text-[#526072] mb-1.5"
            >
              Seniority / Experience Level
            </label>
            <select
              id="agency-room-level"
              data-testid="select-agency-room-level"
              value={experienceLevel}
              onChange={(e) => setExperienceLevel(e.target.value as any)}
              className="w-full rounded-xl border border-[#d9dbd1] bg-white px-3.5 py-2.5 text-sm font-semibold text-[#253142] focus:border-[#277254] focus:outline-hidden focus:ring-2 focus:ring-[#277254]/20 transition"
            >
              <option value="ENTRY">Entry Level (0-2 years)</option>
              <option value="MID">Mid Level (2-5 years)</option>
              <option value="SENIOR">Senior Level (5-8 years)</option>
              <option value="LEAD">Lead / Principal (8+ years)</option>
            </select>
          </div>

          {/* Description */}
          <div>
            <label
              htmlFor="agency-room-desc"
              className="block text-xs font-bold uppercase tracking-wider text-[#526072] mb-1.5"
            >
              Job Overview & Criteria
            </label>
            <textarea
              id="agency-room-desc"
              data-testid="textarea-agency-room-desc"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Outline role responsibilities and key client expectations..."
              className="w-full rounded-xl border border-[#d9dbd1] bg-white px-3.5 py-2 text-sm font-medium text-[#253142] placeholder-[#7b8490]/60 focus:border-[#277254] focus:outline-hidden focus:ring-2 focus:ring-[#277254]/20 transition"
            />
          </div>

          {/* Weighting configuration preview */}
          <div className="rounded-xl border border-[#eef0e7] bg-[#fafaf7] p-3.5">
            <div className="flex items-center justify-between text-xs font-bold text-[#253142] mb-2">
              <span className="flex items-center gap-1.5">
                <Percent size={14} className="text-[#277254]" /> Candidate Evaluation Weighting
              </span>
              <span className="text-[#277254]">{cvWeight}% CV / {videoWeight}% Video</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  value={cvWeight}
                  onChange={(e) => handleCvWeightChange(Number(e.target.value))}
                  data-testid="slider-agency-room-cv-weight"
                  className="w-full accent-[#277254]"
                />
              </div>
            </div>
            <div className="mt-1 flex justify-between text-[11px] text-[#7b8490]">
              <span>CV Match: {cvWeight}%</span>
              <span>Video Presentation: {videoWeight}%</span>
            </div>
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-[#eef0e7]">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              data-testid="button-cancel-agency-create-room"
              className="rounded-xl border border-[#d9dbd1] px-4 py-2.5 text-xs font-bold text-[#526072] hover:bg-[#eef0e7] transition disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || clients.length === 0}
              data-testid="button-submit-agency-create-room"
              className="inline-flex items-center gap-2 rounded-xl bg-[#277254] px-5 py-2.5 text-xs font-bold text-white hover:bg-[#1f5b43] transition shadow-xs disabled:cursor-not-allowed disabled:opacity-50"
            >
              {submitting ? (
                <>
                  <Loader2 size={14} className="animate-spin" /> Creating Room...
                </>
              ) : (
                'Create Room'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
