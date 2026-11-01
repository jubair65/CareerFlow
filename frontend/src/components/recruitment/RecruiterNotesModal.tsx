import React, { useState, useEffect } from 'react';
import {
  X,
  MessageSquare,
  GitCommit,
  CheckCircle2,
  Clock,
  Send,
  Edit2,
  Trash2,
  AlertCircle,
  History,
  User,
  ChevronDown,
  ChevronUp,
  Loader2,
  Check,
} from 'lucide-react';
import {
  PipelineStage,
  CandidateNoteItem,
  CandidateStageHistoryItem,
  apiGetApplicationNotes,
  apiCreateApplicationNote,
  apiUpdateApplicationNote,
  apiDeleteApplicationNote,
  apiUpdateApplicationStage,
  apiGetApplicationStageHistory,
} from '../../api/recruitment';

export interface RecruiterNotesModalProps {
  isOpen: boolean;
  onClose: () => void;
  applicationId: number | null;
  candidateName: string;
  candidateEmail: string;
  roomTitle: string;
  currentStage?: PipelineStage;
  onStageUpdated?: (newStage: PipelineStage) => void;
  onNoteCountChanged?: (count: number) => void;
  notify?: (message: string, tone?: 'success' | 'info' | 'error') => void;
}

const STAGE_CONFIG: {
  key: PipelineStage;
  label: string;
  color: string;
  bgColor: string;
  borderColor: string;
}[] = [
  { key: 'APPLIED', label: 'Applied', color: 'text-slate-700 dark:text-slate-300', bgColor: 'bg-slate-100 dark:bg-slate-800', borderColor: 'border-slate-300 dark:border-slate-700' },
  { key: 'UNDER_REVIEW', label: 'Under Review', color: 'text-amber-700 dark:text-amber-300', bgColor: 'bg-amber-100 dark:bg-amber-950/50', borderColor: 'border-amber-300 dark:border-amber-800' },
  { key: 'SHORTLISTED', label: 'Shortlisted', color: 'text-emerald-700 dark:text-emerald-300', bgColor: 'bg-emerald-100 dark:bg-emerald-950/50', borderColor: 'border-emerald-300 dark:border-emerald-800' },
  { key: 'INTERVIEW_ROUND_1', label: 'Interview Round 1', color: 'text-blue-700 dark:text-blue-300', bgColor: 'bg-blue-100 dark:bg-blue-950/50', borderColor: 'border-blue-300 dark:border-blue-800' },
  { key: 'INTERVIEW_ROUND_2', label: 'Interview Round 2', color: 'text-indigo-700 dark:text-indigo-300', bgColor: 'bg-indigo-100 dark:bg-indigo-950/50', borderColor: 'border-indigo-300 dark:border-indigo-800' },
  { key: 'OFFERED', label: 'Offered', color: 'text-purple-700 dark:text-purple-300', bgColor: 'bg-purple-100 dark:bg-purple-950/50', borderColor: 'border-purple-300 dark:border-purple-800' },
  { key: 'HIRED', label: 'Hired', color: 'text-teal-700 dark:text-teal-300', bgColor: 'bg-teal-100 dark:bg-teal-950/50', borderColor: 'border-teal-300 dark:border-teal-800' },
  { key: 'REJECTED', label: 'Rejected', color: 'text-rose-700 dark:text-rose-300', bgColor: 'bg-rose-100 dark:bg-rose-950/50', borderColor: 'border-rose-300 dark:border-rose-800' },
];

export function RecruiterNotesModal({
  isOpen,
  onClose,
  applicationId,
  candidateName,
  candidateEmail,
  roomTitle,
  currentStage = 'APPLIED',
  onStageUpdated,
  onNoteCountChanged,
  notify,
}: RecruiterNotesModalProps) {
  // State
  const [stage, setStage] = useState<PipelineStage>(currentStage);
  const [selectedStage, setSelectedStage] = useState<PipelineStage>(currentStage);
  const [stageNote, setStageNote] = useState('');
  const [notifyCandidate, setNotifyCandidate] = useState(true);
  const [updatingStage, setUpdatingStage] = useState(false);

  const [notes, setNotes] = useState<CandidateNoteItem[]>([]);
  const [loadingNotes, setLoadingNotes] = useState(false);
  const [newNoteContent, setNewNoteContent] = useState('');
  const [submittingNote, setSubmittingNote] = useState(false);

  const [editingNoteId, setEditingNoteId] = useState<number | null>(null);
  const [editingContent, setEditingContent] = useState('');
  const [savingEdit, setSavingEdit] = useState(false);

  const [history, setHistory] = useState<CandidateStageHistoryItem[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Sync current stage on open
  useEffect(() => {
    if (isOpen && applicationId) {
      setStage(currentStage);
      setSelectedStage(currentStage);
      setStageNote('');
      setNewNoteContent('');
      setEditingNoteId(null);
      loadNotes();
      loadHistory();
    }
  }, [isOpen, applicationId, currentStage]);

  const loadNotes = async () => {
    if (!applicationId) return;
    try {
      setLoadingNotes(true);
      const res = await apiGetApplicationNotes(applicationId);
      setNotes(res);
      if (onNoteCountChanged) {
        onNoteCountChanged(res.length);
      }
    } catch (err: any) {
      console.error('Failed to load notes', err);
      if (notify) notify('Failed to load recruiter notes.', 'error');
    } finally {
      setLoadingNotes(false);
    }
  };

  const loadHistory = async () => {
    if (!applicationId) return;
    try {
      setLoadingHistory(true);
      const res = await apiGetApplicationStageHistory(applicationId);
      setHistory(res);
    } catch (err: any) {
      console.error('Failed to load stage history', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleUpdateStage = async () => {
    if (!applicationId) return;
    try {
      setUpdatingStage(true);
      const res = await apiUpdateApplicationStage(
        applicationId,
        selectedStage,
        stageNote,
        notifyCandidate
      );
      setStage(res.stage);
      setStageNote('');
      if (onStageUpdated) {
        onStageUpdated(res.stage);
      }
      if (notify) {
        notify(`Candidate stage updated to ${res.stage_display}.`, 'success');
      }
      loadHistory();
    } catch (err: any) {
      console.error('Failed to update stage', err);
      if (notify) notify('Failed to update candidate stage.', 'error');
    } finally {
      setUpdatingStage(false);
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!applicationId || !newNoteContent.trim()) return;
    try {
      setSubmittingNote(true);
      const res = await apiCreateApplicationNote(applicationId, newNoteContent.trim());
      const updated = [res, ...notes];
      setNotes(updated);
      setNewNoteContent('');
      if (onNoteCountChanged) {
        onNoteCountChanged(updated.length);
      }
      if (notify) notify('Recruiter note added successfully.', 'success');
    } catch (err: any) {
      console.error('Failed to create note', err);
      if (notify) notify('Failed to add recruiter note.', 'error');
    } finally {
      setSubmittingNote(false);
    }
  };

  const handleSaveEdit = async (noteId: number) => {
    if (!applicationId || !editingContent.trim()) return;
    try {
      setSavingEdit(true);
      const res = await apiUpdateApplicationNote(applicationId, noteId, editingContent.trim());
      setNotes(notes.map((n) => (n.id === noteId ? res : n)));
      setEditingNoteId(null);
      setEditingContent('');
      if (notify) notify('Note updated.', 'success');
    } catch (err: any) {
      console.error('Failed to edit note', err);
      if (notify) notify('Failed to edit note.', 'error');
    } finally {
      setSavingEdit(false);
    }
  };

  const handleDeleteNote = async (noteId: number) => {
    if (!applicationId) return;
    if (!window.confirm('Are you sure you want to delete this internal recruiter note?')) return;
    try {
      await apiDeleteApplicationNote(applicationId, noteId);
      const updated = notes.filter((n) => n.id !== noteId);
      setNotes(updated);
      if (onNoteCountChanged) {
        onNoteCountChanged(updated.length);
      }
      if (notify) notify('Note deleted.', 'info');
    } catch (err: any) {
      console.error('Failed to delete note', err);
      if (notify) notify('Failed to delete note.', 'error');
    }
  };

  if (!isOpen || !applicationId) return null;

  const currentStageMeta =
    STAGE_CONFIG.find((s) => s.key === stage) || STAGE_CONFIG[0];

  return (
    <div
      data-testid="modal-recruiter-notes"
      className="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-xs flex items-center justify-center p-3 sm:p-5"
    >
      <div className="relative w-full max-w-3xl bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-800 overflow-hidden flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="flex items-start justify-between p-5 border-b border-gray-200 dark:border-gray-800 bg-gray-50/70 dark:bg-gray-850/60">
          <div>
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-300">
                <MessageSquare className="w-5 h-5" />
              </span>
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                Recruiter Evaluation & Pipeline Notes
              </h3>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Candidate:{' '}
              <span
                data-testid="text-modal-candidate-name"
                className="font-semibold text-gray-800 dark:text-gray-200"
              >
                {candidateName}
              </span>{' '}
              ({candidateEmail}) &bull; Position: <span className="font-medium">{roomTitle}</span>
            </p>
          </div>
          <button
            type="button"
            data-testid="button-close-recruiter-notes"
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Body */}
        <div className="p-5 overflow-y-auto space-y-6 flex-1 text-sm">
          {/* Section 1: Pipeline Stage Progression (AC-2, AC-5) */}
          <div
            data-testid="section-stage-progression"
            className="p-4 rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/40 space-y-4"
          >
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-2">
                <GitCommit className="w-4 h-4 text-indigo-500" />
                <h4 className="font-semibold text-gray-900 dark:text-white text-xs uppercase tracking-wider">
                  Interview Stage Progression
                </h4>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500 dark:text-gray-400">Current Stage:</span>
                <span
                  data-testid="badge-current-stage"
                  className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${currentStageMeta.color} ${currentStageMeta.bgColor} ${currentStageMeta.borderColor}`}
                >
                  {currentStageMeta.label}
                </span>
              </div>
            </div>

            {/* Stepper overview */}
            <div className="grid grid-cols-4 sm:grid-cols-8 gap-1.5 pt-1">
              {STAGE_CONFIG.map((s, idx) => {
                const isCurrent = s.key === stage;
                const isPassed =
                  STAGE_CONFIG.findIndex((c) => c.key === stage) >= idx &&
                  stage !== 'REJECTED';
                return (
                  <div
                    key={s.key}
                    className={`flex flex-col items-center text-center p-1.5 rounded-lg border text-[11px] transition ${
                      isCurrent
                        ? `${s.bgColor} ${s.borderColor} ${s.color} font-bold ring-2 ring-indigo-500/30`
                        : isPassed
                        ? 'bg-emerald-50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-900 text-emerald-700 dark:text-emerald-400'
                        : 'bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-800 text-gray-400'
                    }`}
                  >
                    <span className="text-[10px] opacity-70">#{idx + 1}</span>
                    <span className="truncate w-full font-medium leading-tight mt-0.5">
                      {s.label}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Stage Update Controls */}
            <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 pt-2">
              <div className="sm:col-span-5">
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Transition to Stage
                </label>
                <select
                  data-testid="select-candidate-stage"
                  value={selectedStage}
                  onChange={(e) => setSelectedStage(e.target.value as PipelineStage)}
                  className="w-full px-3 py-2 text-xs rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                >
                  {STAGE_CONFIG.map((s) => (
                    <option key={s.key} value={s.key}>
                      {s.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="sm:col-span-7">
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Transition Context / Reason (Optional)
                </label>
                <input
                  type="text"
                  data-testid="input-stage-note"
                  value={stageNote}
                  onChange={(e) => setStageNote(e.target.value)}
                  placeholder="e.g. Cleared round 1 technical screen"
                  className="w-full px-3 py-2 text-xs rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center gap-2 cursor-pointer text-xs text-gray-600 dark:text-gray-400">
                <input
                  type="checkbox"
                  data-testid="checkbox-notify-candidate"
                  checked={notifyCandidate}
                  onChange={(e) => setNotifyCandidate(e.target.checked)}
                  className="rounded text-indigo-600 focus:ring-indigo-500"
                />
                <span>Notify candidate via in-app dashboard notification (AC-5)</span>
              </label>

              <button
                type="button"
                data-testid="button-update-stage"
                onClick={handleUpdateStage}
                disabled={updatingStage || selectedStage === stage && !stageNote}
                className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs transition disabled:opacity-50 flex items-center gap-1.5"
              >
                {updatingStage ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Check className="w-3.5 h-3.5" />
                )}
                <span>Update Stage</span>
              </button>
            </div>

            {/* Toggle Stage History */}
            <div className="pt-2 border-t border-gray-200 dark:border-gray-800">
              <button
                type="button"
                data-testid="button-toggle-stage-history"
                onClick={() => setShowHistory(!showHistory)}
                className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1 font-medium"
              >
                <History className="w-3.5 h-3.5" />
                <span>
                  {showHistory ? 'Hide Stage Audit History' : `View Stage Audit History (${history.length})`}
                </span>
                {showHistory ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              </button>

              {showHistory && (
                <div data-testid="section-stage-history" className="mt-3 space-y-2">
                  {loadingHistory ? (
                    <div className="text-center py-2 text-xs text-gray-400">Loading history...</div>
                  ) : history.length === 0 ? (
                    <div className="text-xs text-gray-400 italic py-1">No stage transitions recorded yet.</div>
                  ) : (
                    history.map((h) => (
                      <div
                        key={h.id}
                        className="text-xs p-2 rounded-lg bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 flex items-start justify-between gap-2"
                      >
                        <div>
                          <div className="font-semibold text-gray-800 dark:text-gray-200">
                            {h.from_stage_display || 'Initial'} &rarr; {h.to_stage_display}
                          </div>
                          {h.notes && (
                            <p className="text-gray-600 dark:text-gray-400 text-[11px] mt-0.5">
                              &ldquo;{h.notes}&rdquo;
                            </p>
                          )}
                          <p className="text-[10px] text-gray-400 mt-0.5">
                            Updated by: {h.updated_by_name}
                          </p>
                        </div>
                        <span className="text-[10px] text-gray-400 whitespace-nowrap">
                          {new Date(h.created_at).toLocaleString()}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Section 2: Internal Recruiter Notes Stream (AC-1, AC-3, AC-4) */}
          <div data-testid="section-recruiter-notes" className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-blue-500" />
                <h4 className="font-semibold text-gray-900 dark:text-white text-xs uppercase tracking-wider">
                  Internal Recruiter Notes ({notes.length})
                </h4>
              </div>
              <span className="text-[11px] text-amber-600 dark:text-amber-400 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                Strictly private to hiring team (AC-4)
              </span>
            </div>

            {/* Add Note Form */}
            <form onSubmit={handleAddNote} className="space-y-2">
              <textarea
                data-testid="input-new-note"
                rows={3}
                value={newNoteContent}
                onChange={(e) => setNewNoteContent(e.target.value)}
                placeholder="Write an internal evaluation note, interview observations, or next steps..."
                className="w-full px-3 py-2 text-xs rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 resize-none"
              />
              <div className="flex justify-end">
                <button
                  type="submit"
                  data-testid="button-add-note"
                  disabled={submittingNote || !newNoteContent.trim()}
                  className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition disabled:opacity-50 flex items-center gap-1.5"
                >
                  {submittingNote ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Send className="w-3.5 h-3.5" />
                  )}
                  <span>Post Note</span>
                </button>
              </div>
            </form>

            {/* Notes List */}
            <div data-testid="list-recruiter-notes" className="space-y-3 pt-2">
              {loadingNotes ? (
                <div className="text-center py-6 text-xs text-gray-400 flex items-center justify-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                  <span>Loading evaluation notes...</span>
                </div>
              ) : notes.length === 0 ? (
                <div className="text-center py-8 border-2 border-dashed border-gray-200 dark:border-gray-800 rounded-xl">
                  <MessageSquare className="w-8 h-8 text-gray-300 dark:text-gray-700 mx-auto mb-2" />
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    No recruiter evaluation notes yet.
                  </p>
                  <p className="text-[11px] text-gray-400">
                    Use the box above to record confidential candidate feedback.
                  </p>
                </div>
              ) : (
                notes.map((note) => (
                  <div
                    key={note.id}
                    data-testid={`card-recruiter-note-${note.id}`}
                    className="p-3.5 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-800/80 shadow-xs space-y-2"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span className="p-1 rounded-full bg-blue-50 dark:bg-blue-900/40 text-blue-600 dark:text-blue-300">
                          <User className="w-3.5 h-3.5" />
                        </span>
                        <span
                          data-testid={`text-note-author-${note.id}`}
                          className="font-semibold text-gray-900 dark:text-white"
                        >
                          {note.author_name}
                        </span>
                        <span className="text-[11px] text-gray-400">&bull; {note.author_email}</span>
                        {note.is_edited && (
                          <span
                            data-testid={`badge-note-edited-${note.id}`}
                            className="px-1.5 py-0.2 rounded text-[10px] font-medium bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-800"
                          >
                            edited
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] text-gray-400 flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {new Date(note.created_at).toLocaleString()}
                        </span>
                        <button
                          type="button"
                          data-testid={`button-edit-note-${note.id}`}
                          onClick={() => {
                            setEditingNoteId(note.id);
                            setEditingContent(note.content);
                          }}
                          className="p-1 rounded text-gray-400 hover:text-blue-600 hover:bg-gray-100 dark:hover:bg-gray-700 transition"
                          title="Edit Note"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          data-testid={`button-delete-note-${note.id}`}
                          onClick={() => handleDeleteNote(note.id)}
                          className="p-1 rounded text-gray-400 hover:text-rose-600 hover:bg-gray-100 dark:hover:bg-gray-700 transition"
                          title="Delete Note"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    {editingNoteId === note.id ? (
                      <div className="space-y-2 pt-1">
                        <textarea
                          data-testid={`input-edit-note-${note.id}`}
                          rows={3}
                          value={editingContent}
                          onChange={(e) => setEditingContent(e.target.value)}
                          className="w-full px-3 py-2 text-xs rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                        />
                        <div className="flex justify-end gap-2">
                          <button
                            type="button"
                            data-testid={`button-cancel-edit-note-${note.id}`}
                            onClick={() => {
                              setEditingNoteId(null);
                              setEditingContent('');
                            }}
                            className="px-2.5 py-1 text-xs text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition"
                          >
                            Cancel
                          </button>
                          <button
                            type="button"
                            data-testid={`button-save-edit-note-${note.id}`}
                            onClick={() => handleSaveEdit(note.id)}
                            disabled={savingEdit || !editingContent.trim()}
                            className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-semibold transition disabled:opacity-50"
                          >
                            {savingEdit ? 'Saving...' : 'Save'}
                          </button>
                        </div>
                      </div>
                    ) : (
                      <p
                        data-testid={`text-note-content-${note.id}`}
                        className="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed"
                      >
                        {note.content}
                      </p>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-800 bg-gray-50/70 dark:bg-gray-850/60 flex justify-end">
          <button
            type="button"
            data-testid="button-modal-done"
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-gray-200 dark:bg-gray-800 hover:bg-gray-300 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 font-semibold text-xs transition"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}

