import { useState, type FormEvent } from 'react';
import { X, Building2, Briefcase, FileText, Sparkles, Loader2 } from 'lucide-react';
import { apiCreateRoom, type RecruitmentRoom } from '../../api/recruitment';

interface RoomCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRoomCreated: (newRoom: RecruitmentRoom) => void;
  notify?: (message: string, tone?: 'success' | 'info' | 'error') => void;
}

export function RoomCreateModal({
  isOpen,
  onClose,
  onRoomCreated,
  notify,
}: RoomCreateModalProps) {
  const [title, setTitle] = useState('');
  const [companyName, setCompanyName] = useState('CareerFlow Partner');
  const [department, setDepartment] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  if (!isOpen) return null;

  const validate = (): boolean => {
    const errs: Record<string, string> = {};
    if (!title.trim()) {
      errs.title = 'Job title is required.';
    } else if (title.trim().length < 3) {
      errs.title = 'Job title must be at least 3 characters.';
    }
    if (!companyName.trim()) {
      errs.companyName = 'Company name is required.';
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    setErrors({});

    try {
      const res = await apiCreateRoom({
        title: title.trim(),
        company_name: companyName.trim(),
        department: department.trim(),
        description: description.trim(),
      });

      notify?.(`Recruitment Room "${res.room.title}" created successfully!`, 'success');
      onRoomCreated(res.room);
      onClose();
      // Reset form
      setTitle('');
      setDepartment('');
      setDescription('');
    } catch (err: any) {
      const backendErrors = err?.response?.data;
      if (backendErrors && typeof backendErrors === 'object') {
        const mapped: Record<string, string> = {};
        if (backendErrors.title) mapped.title = Array.isArray(backendErrors.title) ? backendErrors.title[0] : backendErrors.title;
        if (backendErrors.company_name) mapped.companyName = Array.isArray(backendErrors.company_name) ? backendErrors.company_name[0] : backendErrors.company_name;
        if (backendErrors.detail) mapped.general = backendErrors.detail;
        setErrors(mapped);
      } else {
        setErrors({ general: 'Failed to create recruitment room. Please try again.' });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      data-testid="modal-create-room"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in duration-200"
    >
      <div className="relative w-full max-w-lg rounded-2xl bg-white border border-[#d9dbd1] shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#eef0e7] px-6 py-4 bg-[#fbfaf5]">
          <div className="flex items-center gap-2.5">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-[#277254] text-white">
              <Sparkles size={18} />
            </div>
            <div>
              <h2 className="text-base font-bold text-[#253142]">Create Recruitment Room</h2>
              <p className="text-xs text-[#7b8490]">US-18 • Define a hiring space for candidate evaluation</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            data-testid="button-close-room-modal"
            className="rounded-lg p-1.5 text-[#7b8490] hover:bg-[#eef0e7] hover:text-[#253142] transition"
          >
            <X size={18} />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {errors.general && (
            <div
              data-testid="alert-create-room-general-error"
              className="rounded-xl bg-[#f7e5e1] p-3 text-xs font-semibold text-[#a33d35] border border-[#f1d6d1]"
            >
              {errors.general}
            </div>
          )}

          {/* Job Title */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-[#253142] mb-1.5">
              Job Title <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-[#7b8490]">
                <Briefcase size={16} />
              </div>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Senior Full Stack Engineer"
                data-testid="input-room-title"
                className={`w-full rounded-xl border bg-[#fbfaf5] pl-9 pr-3.5 py-2.5 text-sm text-[#253142] placeholder:text-[#98a09c] focus:outline-none focus:ring-2 focus:ring-[#277254]/30 ${
                  errors.title ? 'border-[#b34a40]' : 'border-[#d9dbd1]'
                }`}
              />
            </div>
            {errors.title && (
              <p data-testid="error-room-title" className="mt-1 text-xs font-medium text-[#b34a40]">
                {errors.title}
              </p>
            )}
          </div>

          {/* Company Name */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-[#253142] mb-1.5">
              Company Name <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-[#7b8490]">
                <Building2 size={16} />
              </div>
              <input
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="e.g. Tech Corp"
                data-testid="input-room-company"
                className={`w-full rounded-xl border bg-[#fbfaf5] pl-9 pr-3.5 py-2.5 text-sm text-[#253142] placeholder:text-[#98a09c] focus:outline-none focus:ring-2 focus:ring-[#277254]/30 ${
                  errors.companyName ? 'border-[#b34a40]' : 'border-[#d9dbd1]'
                }`}
              />
            </div>
            {errors.companyName && (
              <p data-testid="error-room-company" className="mt-1 text-xs font-medium text-[#b34a40]">
                {errors.companyName}
              </p>
            )}
          </div>

          {/* Department (Optional) */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-[#253142] mb-1.5">
              Department / Team <span className="text-xs font-normal text-[#7b8490]">(Optional)</span>
            </label>
            <input
              type="text"
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              placeholder="e.g. AI & Engineering"
              data-testid="input-room-department"
              className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3.5 py-2.5 text-sm text-[#253142] placeholder:text-[#98a09c] focus:outline-none focus:ring-2 focus:ring-[#277254]/30"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-[#253142] mb-1.5">
              Job Description
            </label>
            <div className="relative">
              <textarea
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Provide a brief overview of key responsibilities and expectations..."
                data-testid="input-room-description"
                className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3.5 py-2.5 text-sm text-[#253142] placeholder:text-[#98a09c] focus:outline-none focus:ring-2 focus:ring-[#277254]/30"
              />
            </div>
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#eef0e7]">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              data-testid="button-cancel-create-room"
              className="rounded-xl px-4 py-2 text-xs font-semibold text-[#526072] hover:bg-[#eef0e7] transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              data-testid="button-submit-create-room"
              className="inline-flex items-center gap-2 rounded-xl bg-[#277254] px-5 py-2 text-xs font-bold text-white hover:bg-[#1f5b43] transition disabled:opacity-50 shadow-sm"
            >
              {loading ? (
                <>
                  <Loader2 size={15} className="animate-spin" />
                  Creating Room...
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
