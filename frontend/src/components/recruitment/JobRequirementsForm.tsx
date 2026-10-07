import { useState, useEffect, type FormEvent, type KeyboardEvent } from 'react';
import {
  X,
  Sparkles,
  Tag,
  Plus,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Briefcase,
  Layers,
  FileText,
  Loader2,
  Zap,
} from 'lucide-react';
import type {
  RecruitmentRoom,
  SkillItem,
  RoomRequirementsPayload,
} from '../../api/recruitment';
import {
  apiGetRoomRequirements,
  apiUpdateRoomRequirements,
} from '../../api/recruitment';

interface JobRequirementsFormProps {
  room: RecruitmentRoom | null;
  isOpen: boolean;
  onClose: () => void;
  onRoomUpdated: (updatedRoom: RecruitmentRoom) => void;
  notify?: (message: string, tone?: 'success' | 'info' | 'error') => void;
}

const PRESET_SUGGESTIONS = [
  'Python',
  'TypeScript',
  'React',
  'Docker',
  'AWS',
  'PostgreSQL',
  'Node.js',
  'Kubernetes',
  'GraphQL',
  'FastAPI',
  'SQL',
  'Git',
];

const EXPERIENCE_LEVELS: { value: 'ENTRY' | 'MID' | 'SENIOR' | 'LEAD'; label: string; sub: string }[] = [
  { value: 'ENTRY', label: 'Entry Level', sub: '0–2 years' },
  { value: 'MID', label: 'Mid-Level', sub: '2–5 years' },
  { value: 'SENIOR', label: 'Senior', sub: '5–8 years' },
  { value: 'LEAD', label: 'Lead / Principal', sub: '8+ years' },
];

export function JobRequirementsForm({
  room,
  isOpen,
  onClose,
  onRoomUpdated,
  notify,
}: JobRequirementsFormProps) {
  const [roleCategory, setRoleCategory] = useState('Engineering');
  const [experienceLevel, setExperienceLevel] = useState<'ENTRY' | 'MID' | 'SENIOR' | 'LEAD'>('MID');
  const [requirementsText, setRequirementsText] = useState('');
  const [skills, setSkills] = useState<string[]>([]);
  const [newSkillInput, setNewSkillInput] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [loadingInitial, setLoadingInitial] = useState(false);

  // Initialize or load fresh requirements on room change / modal open
  useEffect(() => {
    if (!room || !isOpen) return;

    setRoleCategory(room.role_category || 'Engineering');
    setExperienceLevel(room.experience_level || 'MID');
    setRequirementsText(room.requirements_text || '');
    setValidationError(null);
    setNewSkillInput('');

    // Normalize existing skills from room model
    const normalized: string[] = [];
    if (Array.isArray(room.skills_required)) {
      for (const item of room.skills_required) {
        if (typeof item === 'string' && item.trim()) {
          normalized.push(item.trim());
        } else if (item && typeof item === 'object' && 'name' in item && item.name) {
          normalized.push(String(item.name).trim());
        }
      }
    }
    setSkills(normalized);

    // Fetch freshest data from backend API
    const loadFresh = async () => {
      try {
        setLoadingInitial(true);
        const data = await apiGetRoomRequirements(room.id);
        if (data.requirements) {
          setRoleCategory(data.requirements.role_category || 'Engineering');
          setExperienceLevel(data.requirements.experience_level || 'MID');
          setRequirementsText(data.requirements.requirements_text || '');
        }
        if (data.skill_names && data.skill_names.length > 0) {
          setSkills(data.skill_names);
        }
      } catch {
        // Fall back to room object already populated
      } finally {
        setLoadingInitial(false);
      }
    };

    loadFresh();
  }, [room, isOpen]);

  if (!isOpen || !room) return null;

  const handleAddSkill = (skillToAdd?: string) => {
    const raw = (skillToAdd !== undefined ? skillToAdd : newSkillInput).trim();
    if (!raw) {
      setValidationError('Please type a skill name before adding.');
      return;
    }

    if (raw.length < 2) {
      setValidationError('Skill name must be at least 2 characters long.');
      return;
    }

    if (raw.length > 60) {
      setValidationError('Skill name cannot exceed 60 characters.');
      return;
    }

    const lowerCaseRaw = raw.toLowerCase();
    const alreadyExists = skills.some((s) => s.toLowerCase() === lowerCaseRaw);

    if (alreadyExists) {
      setValidationError(`Skill "${raw}" is already added.`);
      return;
    }

    setSkills((prev) => [...prev, raw]);
    setNewSkillInput('');
    setValidationError(null);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddSkill();
    }
  };

  const handleRemoveSkill = (skillToRemove: string) => {
    setSkills((prev) => prev.filter((s) => s.toLowerCase() !== skillToRemove.toLowerCase()));
    if (validationError && validationError.includes(skillToRemove)) {
      setValidationError(null);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (skills.length === 0) {
      setValidationError('At least one required skill must be defined.');
      return;
    }

    setSaving(true);
    setValidationError(null);

    const payload: RoomRequirementsPayload = {
      role_category: roleCategory.trim() || 'Engineering',
      experience_level: experienceLevel,
      requirements_text: requirementsText.trim(),
      skills_required: skills.map((name) => ({
        name,
        importance: 'REQUIRED',
        category: roleCategory,
      })),
    };

    try {
      const res = await apiUpdateRoomRequirements(room.id, payload);
      notify?.('Job role and required skills updated successfully!', 'success');
      onRoomUpdated(res.room);
      onClose();
    } catch (err: any) {
      const respData = err?.response?.data;
      if (respData) {
        if (respData.skills_required) {
          const msg = Array.isArray(respData.skills_required)
            ? respData.skills_required[0]
            : respData.skills_required;
          setValidationError(msg);
        } else if (respData.detail) {
          setValidationError(respData.detail);
        } else {
          setValidationError('Failed to update job requirements. Please check input values.');
        }
      } else {
        setValidationError('Network error while updating requirements.');
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      data-testid="modal-job-requirements"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in duration-200 overflow-y-auto"
    >
      <div className="relative w-full max-w-2xl rounded-2xl bg-white border border-[#d9dbd1] shadow-2xl overflow-hidden my-8">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#eef0e7] px-6 py-4 bg-[#fbfaf5]">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#277254] text-white shadow-xs">
              <Sparkles size={20} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-[#253142]">Configure Job Role & Skills</h2>
                <span className="rounded-md bg-[#e2f0e9] px-2 py-0.5 text-[10px] font-extrabold uppercase tracking-wide text-[#277254]">
                  US-19
                </span>
              </div>
              <p className="text-xs text-[#7b8490]">
                {room.title} • <span className="font-semibold text-[#526072]">{room.company_name}</span>
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            data-testid="button-close-requirements-modal"
            className="rounded-lg p-1.5 text-[#7b8490] hover:bg-[#eef0e7] hover:text-[#253142] transition"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {loadingInitial && (
            <div className="flex items-center gap-2 text-xs text-[#7b8490] bg-[#fbfaf5] p-2.5 rounded-xl border border-[#eef0e7]">
              <Loader2 size={14} className="animate-spin text-[#277254]" />
              Synchronizing room requirements from server...
            </div>
          )}

          {/* Role Category & Seniority Level */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-[#253142] mb-1.5 flex items-center gap-1.5">
                <Briefcase size={13} className="text-[#277254]" />
                Role Category
              </label>
              <input
                type="text"
                value={roleCategory}
                onChange={(e) => setRoleCategory(e.target.value)}
                placeholder="e.g. Engineering, Design, Product"
                data-testid="input-role-category"
                className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3.5 py-2 text-xs text-[#253142] placeholder:text-[#98a09c] focus:outline-none focus:ring-2 focus:ring-[#277254]/30"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-[#253142] mb-1.5 flex items-center gap-1.5">
                <Layers size={13} className="text-[#277254]" />
                Target Experience Level
              </label>
              <select
                value={experienceLevel}
                onChange={(e) => setExperienceLevel(e.target.value as any)}
                data-testid="select-experience-level"
                className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3.5 py-2 text-xs font-medium text-[#253142] focus:outline-none focus:ring-2 focus:ring-[#277254]/30"
              >
                {EXPERIENCE_LEVELS.map((lvl) => (
                  <option key={lvl.value} value={lvl.value}>
                    {lvl.label} ({lvl.sub})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Interactive Skills Builder */}
          <div className="rounded-2xl border border-[#d9dbd1] bg-[#fbfaf5] p-4 space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-[#253142] flex items-center gap-1.5">
                <Tag size={14} className="text-[#277254]" />
                Required Skills & Tech Stack ({skills.length})
                <span className="text-[11px] font-normal text-[#7b8490]">
                  (Min. 1 skill required for semantic CV matching)
                </span>
              </label>
            </div>

            {/* Input & Add Button */}
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <input
                  type="text"
                  value={newSkillInput}
                  onChange={(e) => {
                    setNewSkillInput(e.target.value);
                    if (validationError) setValidationError(null);
                  }}
                  onKeyDown={handleKeyDown}
                  placeholder="Type a skill (e.g. Python, Docker, React) and press Enter..."
                  data-testid="input-skill-tag"
                  className="w-full rounded-xl border border-[#d9dbd1] bg-white px-3.5 py-2 text-xs text-[#253142] placeholder:text-[#98a09c] focus:outline-none focus:ring-2 focus:ring-[#277254]/30"
                />
              </div>
              <button
                type="button"
                onClick={() => handleAddSkill()}
                data-testid="button-add-skill"
                className="inline-flex items-center gap-1.5 rounded-xl bg-[#253142] px-3.5 py-2 text-xs font-bold text-white hover:bg-[#1a2330] transition shadow-xs"
              >
                <Plus size={14} /> Add Skill
              </button>
            </div>

            {/* Validation Error Banner */}
            {validationError && (
              <div
                data-testid="error-skills-validation"
                className="flex items-center gap-2 rounded-xl bg-[#fef2f2] border border-[#fecaca] p-2.5 text-xs font-medium text-[#b91c1c] animate-in fade-in duration-150"
              >
                <AlertCircle size={14} className="shrink-0" />
                <span>{validationError}</span>
              </div>
            )}

            {/* Active Skill Tag Pills Container */}
            <div
              data-testid="container-skill-tags"
              className="min-h-12 rounded-xl border border-[#eef0e7] bg-white p-3 flex flex-wrap items-center gap-2"
            >
              {skills.length === 0 ? (
                <span className="text-xs text-[#98a09c] italic">
                  No skills added yet. Type a skill name above or click quick suggestions below.
                </span>
              ) : (
                skills.map((skill) => {
                  const safeSlug = skill.toLowerCase().trim().replace(/[^a-z0-9]/g, '-');
                  return (
                    <span
                      key={skill}
                      className="inline-flex items-center gap-1.5 rounded-lg bg-[#e2f0e9] border border-[#c4e3d3] px-2.5 py-1 text-xs font-semibold text-[#1f5b43] transition hover:bg-[#d5ebd0]"
                    >
                      <span>{skill}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveSkill(skill)}
                        title={`Remove ${skill}`}
                        data-testid={`button-remove-skill-${skill.toLowerCase()}`}
                        aria-label={`Remove ${skill}`}
                        className="rounded-sm p-0.5 hover:bg-[#c4e3d3] text-[#277254] hover:text-[#b34a40] transition"
                      >
                        <X size={12} />
                      </button>
                    </span>
                  );
                })
              )}
            </div>

            {/* Quick Suggestions Chips */}
            <div className="pt-1">
              <span className="text-[11px] font-semibold text-[#7b8490] flex items-center gap-1 mb-1.5">
                <Zap size={11} className="text-[#277254]" /> Quick suggestions:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {PRESET_SUGGESTIONS.map((preset) => {
                  const isAdded = skills.some((s) => s.toLowerCase() === preset.toLowerCase());
                  return (
                    <button
                      key={preset}
                      type="button"
                      disabled={isAdded}
                      onClick={() => handleAddSkill(preset)}
                      className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-medium transition ${
                        isAdded
                          ? 'bg-[#eef0e7] text-[#98a09c] cursor-not-allowed opacity-60'
                          : 'bg-white border border-[#d9dbd1] text-[#526072] hover:border-[#277254] hover:text-[#277254] hover:bg-[#f5fbf7]'
                      }`}
                    >
                      {isAdded ? <CheckCircle2 size={10} className="text-[#277254]" /> : <Plus size={10} />}
                      {preset}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Detailed Requirements Text */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-bold text-[#253142] flex items-center gap-1.5">
                <FileText size={13} className="text-[#277254]" />
                Detailed Requirements & Scope
              </label>
              <span className="text-[11px] text-[#98a09c]">
                {requirementsText.length} / 10,000 chars
              </span>
            </div>
            <textarea
              rows={4}
              value={requirementsText}
              onChange={(e) => setRequirementsText(e.target.value)}
              placeholder="Outline specific responsibilities, mandatory qualifications, education background, or domain experience for candidate evaluation..."
              data-testid="textarea-requirements-text"
              maxLength={10000}
              className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3.5 py-2.5 text-xs text-[#253142] placeholder:text-[#98a09c] focus:outline-none focus:ring-2 focus:ring-[#277254]/30 leading-relaxed"
            />
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-[#eef0e7]">
            <button
              type="button"
              onClick={onClose}
              disabled={saving}
              className="rounded-xl border border-[#d9dbd1] bg-white px-4 py-2 text-xs font-bold text-[#526072] hover:bg-[#fbfaf5] transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              data-testid="button-save-requirements"
              className="inline-flex items-center gap-2 rounded-xl bg-[#277254] px-5 py-2 text-xs font-bold text-white hover:bg-[#1f5b43] transition shadow-xs disabled:opacity-50"
            >
              {saving ? (
                <>
                  <Loader2 size={14} className="animate-spin" /> Saving Requirements...
                </>
              ) : (
                <>
                  <CheckCircle2 size={14} /> Save Requirements
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
