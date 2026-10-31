import { useState, useMemo, useRef, useEffect } from 'react';
import {
  FolderOpen,
  Plus,
  Search,
  Copy,
  Check,
  Edit2,
  Trash2,
  PauseCircle,
  PlayCircle,
  Calendar,
  Building2,
  Sliders,
  X,
  Loader2,
  Tag,
  Link2,
  Award,
  Trophy,
  MoreVertical,
  Star,
  FileDown,
  Clock,
  AlertTriangle,
} from 'lucide-react';
import type { RecruitmentRoom } from '../../api/recruitment';
import {
  apiUpdateRoom,
  apiDeleteRoom,
  apiDownloadRoomSummaryPdf,
  triggerPdfDownload,
  apiUpdateRoomStatus,
  apiUpdateRoomDeadline,
} from '../../api/recruitment';
import { JobRequirementsForm } from './JobRequirementsForm';
import { WeightingConfigCard } from './WeightingConfigCard';
import { ShareableLinkCard } from './ShareableLinkCard';
import { RoomCvScoresModal } from './RoomCvScoresModal';
import { RankedApplicantsModal } from './RankedApplicantsModal';
import { ShortlistConfigModal } from './ShortlistConfigModal';



interface RoomListProps {
  rooms: RecruitmentRoom[];
  onOpenCreateModal: () => void;
  onRoomUpdated: (updatedRoom: RecruitmentRoom) => void;
  onRoomDeleted: (deletedRoomId: number) => void;
  notify?: (message: string, tone?: 'success' | 'info' | 'error') => void;
}

export function RoomList({
  rooms,
  onOpenCreateModal,
  onRoomUpdated,
  onRoomDeleted,
  notify,
}: RoomListProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'OPEN' | 'PAUSED' | 'CLOSED' | 'DRAFT'>('ALL');
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [openMenuId, setOpenMenuId] = useState<number | null>(null);
  const [downloadingRoomId, setDownloadingRoomId] = useState<number | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  // US-45: Quick Deadline Modal State
  const [deadlineModalRoom, setDeadlineModalRoom] = useState<RecruitmentRoom | null>(null);
  const [quickDeadlineValue, setQuickDeadlineValue] = useState('');
  const [savingDeadline, setSavingDeadline] = useState(false);

  const handleDownloadRoomPdf = async (room: RecruitmentRoom) => {
    try {
      setDownloadingRoomId(room.id);
      const blob = await apiDownloadRoomSummaryPdf(room.id);
      const titleClean = room.title.replace(/\s+/g, '_');
      triggerPdfDownload(blob, `CareerFlow_Room_${room.id}_${titleClean}_Summary_Report.pdf`);
      if (notify) notify('Room Summary PDF downloaded successfully.', 'success');
    } catch {
      if (notify) notify('Failed to download room summary PDF report.', 'error');
    } finally {
      setDownloadingRoomId(null);
    }
  };

  // Close three-dot menu on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpenMenuId(null);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Edit Modal State
  const [editingRoom, setEditingRoom] = useState<RecruitmentRoom | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editCompany, setEditCompany] = useState('');
  const [editDept, setEditDept] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [editStatus, setEditStatus] = useState<'DRAFT' | 'OPEN' | 'ACTIVE' | 'PAUSED' | 'CLOSED'>('OPEN');
  const [editDeadline, setEditDeadline] = useState('');
  const [savingEdit, setSavingEdit] = useState(false);

  // US-19 Job Requirements Modal State
  const [requirementsRoom, setRequirementsRoom] = useState<RecruitmentRoom | null>(null);

  // US-20 Weighting Configuration Modal State
  const [weightingRoom, setWeightingRoom] = useState<RecruitmentRoom | null>(null);

  // US-21 Shareable Application Link Modal State
  const [shareLinkRoom, setShareLinkRoom] = useState<RecruitmentRoom | null>(null);

  // US-10 Applicant CV Match Scores Modal State
  const [cvScoresRoom, setCvScoresRoom] = useState<RecruitmentRoom | null>(null);

  // US-24 Applicant Rankings & Leaderboard Modal State
  const [rankedRoom, setRankedRoom] = useState<RecruitmentRoom | null>(null);

  // US-25 Automatic Shortlisting Modal State
  const [shortlistRoom, setShortlistRoom] = useState<RecruitmentRoom | null>(null);


  const getRoomSkillNames = (room: RecruitmentRoom): string[] => {
    if (!room.skills_required || !Array.isArray(room.skills_required)) return [];
    return room.skills_required
      .map((item) => (typeof item === 'string' ? item : item?.name))
      .filter(Boolean) as string[];
  };

  const filteredRooms = useMemo(() => {
    return rooms.filter((r) => {
      const matchSearch =
        r.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.company_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.department?.toLowerCase().includes(searchTerm.toLowerCase());
      let matchStatus = true;
      if (statusFilter === 'OPEN') {
        matchStatus = r.status === 'OPEN' || r.status === 'ACTIVE';
      } else if (statusFilter !== 'ALL') {
        matchStatus = r.status === statusFilter;
      }
      return matchSearch && matchStatus;
    });
  }, [rooms, searchTerm, statusFilter]);

  const handleCopyLink = (room: RecruitmentRoom) => {
    const fullUrl = `${window.location.origin}/apply/${room.share_token}`;
    navigator.clipboard.writeText(fullUrl);
    setCopiedId(room.id);
    notify?.(`Application link copied to clipboard!`, 'info');
    setTimeout(() => setCopiedId(null), 2500);
  };

  // US-45 AC-5: Toggle status / manual reopen
  const handleToggleStatus = async (room: RecruitmentRoom) => {
    const isCurrentlyOpen = room.status === 'OPEN' || room.status === 'ACTIVE';
    const nextStatus = isCurrentlyOpen ? 'PAUSED' : 'OPEN';
    try {
      const res = await apiUpdateRoomStatus(room.id, nextStatus);
      onRoomUpdated(res.room);
      const actionMsg = nextStatus === 'OPEN' ? 'reopened/activated' : 'paused';
      notify?.(`Room "${room.title}" is now ${actionMsg}.`, 'success');
    } catch {
      notify?.(`Failed to update room status.`, 'error');
    }
  };

  const handleSetStatus = async (room: RecruitmentRoom, targetStatus: 'DRAFT' | 'OPEN' | 'PAUSED' | 'CLOSED') => {
    try {
      const res = await apiUpdateRoomStatus(room.id, targetStatus);
      onRoomUpdated(res.room);
      notify?.(`Room "${room.title}" status updated to ${targetStatus.toLowerCase()}.`, 'success');
    } catch {
      notify?.(`Failed to update room status.`, 'error');
    }
  };

  const openDeadlineModal = (room: RecruitmentRoom) => {
    setDeadlineModalRoom(room);
    if (room.application_deadline) {
      const d = new Date(room.application_deadline);
      const pad = (n: number) => n.toString().padStart(2, '0');
      setQuickDeadlineValue(
        `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
      );
    } else {
      setQuickDeadlineValue('');
    }
  };

  const handleSaveQuickDeadline = async () => {
    if (!deadlineModalRoom) return;
    try {
      setSavingDeadline(true);
      const isoVal = quickDeadlineValue ? new Date(quickDeadlineValue).toISOString() : null;
      const res = await apiUpdateRoomDeadline(deadlineModalRoom.id, isoVal);
      onRoomUpdated(res.room);
      notify?.('Application deadline updated successfully!', 'success');
      setDeadlineModalRoom(null);
    } catch {
      notify?.('Failed to update application deadline.', 'error');
    } finally {
      setSavingDeadline(false);
    }
  };

  const handleClearDeadline = async () => {
    if (!deadlineModalRoom) return;
    try {
      setSavingDeadline(true);
      const res = await apiUpdateRoomDeadline(deadlineModalRoom.id, null);
      onRoomUpdated(res.room);
      notify?.('Application deadline cleared.', 'info');
      setDeadlineModalRoom(null);
    } catch {
      notify?.('Failed to clear application deadline.', 'error');
    } finally {
      setSavingDeadline(false);
    }
  };

  const handleDelete = async (room: RecruitmentRoom) => {
    if (!window.confirm(`Are you sure you want to delete room "${room.title}"?`)) return;
    try {
      await apiDeleteRoom(room.id);
      onRoomDeleted(room.id);
      notify?.(`Room "${room.title}" deleted.`, 'info');
    } catch {
      notify?.(`Failed to delete room.`, 'error');
    }
  };

  const openEditModal = (room: RecruitmentRoom) => {
    setEditingRoom(room);
    setEditTitle(room.title);
    setEditCompany(room.company_name);
    setEditDept(room.department || '');
    setEditDesc(room.description || '');
    setEditStatus(room.status === 'ACTIVE' ? 'OPEN' : room.status);
    if (room.application_deadline) {
      const d = new Date(room.application_deadline);
      const pad = (n: number) => n.toString().padStart(2, '0');
      setEditDeadline(
        `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
      );
    } else {
      setEditDeadline('');
    }
  };

  const handleSaveEdit = async () => {
    if (!editingRoom) return;
    if (!editTitle.trim() || !editCompany.trim()) {
      notify?.('Title and Company name are required.', 'error');
      return;
    }
    setSavingEdit(true);
    try {
      const res = await apiUpdateRoom(editingRoom.id, {
        title: editTitle.trim(),
        company_name: editCompany.trim(),
        department: editDept.trim(),
        description: editDesc.trim(),
        status: editStatus,
        application_deadline: editDeadline ? new Date(editDeadline).toISOString() : null,
      });
      onRoomUpdated(res.room);
      notify?.('Room details updated successfully!', 'success');
      setEditingRoom(null);
    } catch {
      notify?.('Failed to update room.', 'error');
    } finally {
      setSavingEdit(false);
    }
  };

  return (
    <div className="space-y-5 min-w-0 w-full max-w-full" data-testid="section-recruitment-rooms">
      {/* Top Filter & Search Controls */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white p-4 rounded-2xl border border-[#d9dbd1] shadow-xs min-w-0 w-full">
        <div className="relative w-full sm:flex-1 sm:max-w-md min-w-0">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#7b8490]" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search rooms by title or company..."
            data-testid="input-search-rooms"
            className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] pl-9 pr-3.5 py-2 text-xs text-[#253142] placeholder:text-[#98a09c] focus:outline-none focus:ring-2 focus:ring-[#277254]/30"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto justify-start sm:justify-end min-w-0">
          <div className="flex items-center gap-1 bg-[#f5f1e6] p-1 rounded-xl shrink-0 overflow-x-auto max-w-full">
            {[
              { id: 'ALL' as const, label: 'All', testId: 'filter-status-all' },
              { id: 'OPEN' as const, label: 'Open', testId: 'filter-status-open' },
              { id: 'PAUSED' as const, label: 'Paused', testId: 'filter-status-paused' },
              { id: 'CLOSED' as const, label: 'Closed', testId: 'filter-status-closed' },
              { id: 'DRAFT' as const, label: 'Draft', testId: 'filter-status-draft' },
            ].map(({ id, label, testId }) => (
              <button
                key={id}
                type="button"
                onClick={() => setStatusFilter(id)}
                data-testid={testId}
                className={`rounded-lg px-2.5 py-1 text-xs font-bold transition whitespace-nowrap ${
                  statusFilter === id
                    ? 'bg-[#253142] text-white shadow-2xs'
                    : 'text-[#687382] hover:text-[#253142]'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Empty State */}
      {filteredRooms.length === 0 && (
        <div
          data-testid="card-no-rooms-empty"
          className="flex flex-col items-center justify-center p-12 bg-white rounded-2xl border border-dashed border-[#d9dbd1] text-center"
        >
          <div className="grid h-14 w-14 place-items-center rounded-2xl bg-[#f5f1e6] text-[#277254] mb-3">
            <FolderOpen size={28} />
          </div>
          <h3 className="text-base font-bold text-[#253142]">No Recruitment Rooms Found</h3>
          <p className="mt-1 max-w-sm text-xs text-[#7b8490] leading-5">
            {searchTerm || statusFilter !== 'ALL'
              ? 'No rooms match your search query or status filter. Try resetting your filter.'
              : 'Create your first recruitment room to begin collecting candidate applications and configuring AI scoring criteria.'}
          </p>
          <button
            type="button"
            onClick={onOpenCreateModal}
            data-testid="button-create-room-empty"
            className="mt-4 inline-flex items-center gap-2 rounded-xl bg-[#277254] px-4 py-2 text-xs font-bold text-white hover:bg-[#1f5b43] transition"
          >
            <Plus size={15} /> Create First Room
          </button>
        </div>
      )}

      {/* Grid of Rooms */}
      <div className="room-grid" data-testid="grid-recruitment-rooms">
        {filteredRooms.map((room) => (
          <div
            key={room.id}
            data-testid={`card-room-${room.id}`}
            className="room-card"
          >
            <div className="flex-1 min-w-0">
              {/* 1. Card Header: Company, Title & Status */}
              <div className="flex items-start justify-between gap-2.5 min-w-0">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-[#7b8490] min-w-0">
                    <Building2 size={13} className="shrink-0" />
                    <span className="truncate" title={room.company_name}>{room.company_name}</span>
                    {room.department && (
                      <span className="text-[11px] text-[#9aabb5] shrink-0 truncate" title={room.department}>
                        • {room.department}
                      </span>
                    )}
                  </div>
                  {/* 2. Job Title */}
                  <h3
                    data-testid={`room-title-${room.id}`}
                    className="mt-1 text-base font-bold text-[#253142] line-clamp-2 leading-snug break-words"
                    title={room.title}
                  >
                    {room.title}
                  </h3>
                </div>
                <span
                  data-testid={`room-status-${room.id}`}
                  className={`shrink-0 inline-flex items-center rounded-lg px-2 py-0.5 text-[11px] font-bold uppercase tracking-wider whitespace-nowrap ${
                    room.status === 'ACTIVE' || room.status === 'OPEN'
                      ? 'bg-[#e2f0e9] text-[#277254]'
                      : room.status === 'PAUSED'
                      ? 'bg-[#fef3c7] text-[#92400e]'
                      : room.status === 'CLOSED'
                      ? 'bg-[#fee2e2] text-[#991b1b]'
                      : 'bg-[#f1f3f5] text-[#687382]'
                  }`}
                >
                  {room.status === 'ACTIVE' ? 'OPEN' : room.status}
                </span>
              </div>

              {/* 3. Role Category & Seniority Badges */}
              {(room.role_category || room.experience_level) && (
                <div className="mt-2.5 flex flex-wrap items-center gap-1.5 min-w-0">
                  {room.role_category && (
                    <span className="inline-flex items-center rounded-md bg-[#f1f3f5] px-2 py-0.5 text-[10px] font-bold text-[#526072] max-w-full truncate">
                      {room.role_category}
                    </span>
                  )}
                  {room.experience_level && (
                    <span className="inline-flex items-center rounded-md bg-[#f5f1e6] px-2 py-0.5 text-[10px] font-bold text-[#253142] max-w-full truncate">
                      {room.experience_level}
                    </span>
                  )}
                </div>
              )}

              {/* 4. Description Snippet */}
              <p className="mt-3 text-xs text-[#687382] line-clamp-2 leading-relaxed break-words">
                {room.description || 'No job description provided.'}
              </p>

              {/* 5. Required Skills & Tag Pill Display (US-19) */}
              <div className="mt-3.5 rounded-xl bg-[#fbfaf5] p-2.5 border border-[#eef0e7] min-w-0">
                <div className="flex items-center justify-between mb-1.5 min-w-0 gap-1">
                  <span className="text-[11px] font-bold text-[#526072] flex items-center gap-1 shrink-0">
                    <Tag size={12} className="text-[#277254]" /> Required Skills:
                  </span>
                  <button
                    type="button"
                    onClick={() => setRequirementsRoom(room)}
                    data-testid={`button-configure-requirements-${room.id}`}
                    className="text-[11px] font-bold text-[#277254] hover:text-[#1f5b43] hover:underline transition shrink-0"
                  >
                    Configure
                  </button>
                </div>
                <div
                  data-testid={`room-skills-list-${room.id}`}
                  className="flex flex-wrap gap-1 min-h-[22px] min-w-0"
                >
                  {getRoomSkillNames(room).length > 0 ? (
                    <>
                      {getRoomSkillNames(room).slice(0, 4).map((sk, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center rounded-md bg-[#e2f0e9] border border-[#c4e3d3] px-2 py-0.5 text-[10px] font-semibold text-[#1f5b43] max-w-full truncate"
                        >
                          {sk}
                        </span>
                      ))}
                      {getRoomSkillNames(room).length > 4 && (
                        <span className="inline-flex items-center rounded-md bg-[#f1f3f5] px-1.5 py-0.5 text-[10px] font-medium text-[#687382] shrink-0">
                          +{getRoomSkillNames(room).length - 4} more
                        </span>
                      )}
                    </>
                  ) : (
                    <span className="text-[11px] text-[#98a09c] italic">No skills defined yet</span>
                  )}
                </div>
              </div>

              {/* 6. Evaluation Weights (US-20) */}
              <button
                type="button"
                onClick={() => setWeightingRoom(room)}
                data-testid={`badge-weighting-config-${room.id}`}
                className="mt-3.5 w-full rounded-xl bg-[#fbfaf5] p-2.5 border border-[#eef0e7] text-xs hover:border-[#277254] hover:bg-[#e2f0e9]/30 transition group text-left min-w-0"
                title="Click to configure evaluation weighting formula"
              >
                <div className="flex items-center justify-between mb-1.5 min-w-0">
                  <div className="flex items-center gap-1.5 text-[#526072] font-bold group-hover:text-[#277254]">
                    <Sliders size={12} className="text-[#277254] shrink-0" />
                    <span>Evaluation Weights</span>
                  </div>
                  <Edit2 size={11} className="text-[#7b8490] opacity-0 group-hover:opacity-100 transition shrink-0" />
                </div>
                <div className="flex items-center justify-between gap-1.5 flex-wrap min-w-0">
                  <div className="flex items-center gap-1.5 flex-wrap min-w-0">
                    <span className="inline-flex items-center gap-1 rounded-md bg-[#e2f0e9] border border-[#c4e3d3] px-2 py-0.5 text-[10px] font-bold text-[#1f5b43] whitespace-nowrap">
                      CV · {room.cv_weight ?? 50}%
                    </span>
                    <span className="inline-flex items-center gap-1 rounded-md bg-[#f0f4ff] border border-[#c5d5f7] px-2 py-0.5 text-[10px] font-bold text-[#3b4fa0] whitespace-nowrap">
                      Video · {room.video_weight ?? 50}%
                    </span>
                  </div>
                  <span className="text-[10px] text-[#98a09c] shrink-0 font-medium">
                    {(room.cv_weight ?? 50) + (room.video_weight ?? 50)}% total
                  </span>
                </div>
              </button>

              {/* US-45: Application Deadline & Expiration Display */}
              <div
                data-testid={`room-deadline-card-${room.id}`}
                className="mt-3.5 rounded-xl bg-[#fbfaf5] p-2.5 border border-[#eef0e7] min-w-0"
              >
                <div className="flex items-center justify-between mb-1 min-w-0 gap-1">
                  <span className="text-[11px] font-bold text-[#526072] flex items-center gap-1 shrink-0">
                    <Clock size={12} className="text-[#277254]" /> Application Deadline:
                  </span>
                  <button
                    type="button"
                    onClick={() => openDeadlineModal(room)}
                    data-testid={`button-set-deadline-${room.id}`}
                    className="text-[11px] font-bold text-[#277254] hover:text-[#1f5b43] hover:underline transition shrink-0"
                  >
                    {room.application_deadline ? 'Edit' : 'Set Deadline'}
                  </button>
                </div>
                <div className="flex items-center justify-between gap-1 text-xs">
                  {room.application_deadline ? (
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span
                        data-testid={`room-deadline-value-${room.id}`}
                        className="font-semibold text-[#253142]"
                      >
                        {new Date(room.application_deadline).toLocaleString([], {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                      {room.is_past_deadline ? (
                        <span
                          data-testid={`room-deadline-expired-badge-${room.id}`}
                          className="inline-flex items-center gap-1 rounded-md bg-[#fee2e2] border border-[#fca5a5] px-1.5 py-0.5 text-[10px] font-bold text-[#991b1b]"
                        >
                          <AlertTriangle size={10} /> Expired
                        </span>
                      ) : (
                        <span className="inline-flex items-center rounded-md bg-[#e2f0e9] border border-[#c4e3d3] px-1.5 py-0.5 text-[10px] font-bold text-[#1f5b43]">
                          Active
                        </span>
                      )}
                    </div>
                  ) : (
                    <span
                      data-testid={`room-deadline-value-${room.id}`}
                      className="text-[11px] text-[#98a09c] italic"
                    >
                      No deadline set (Open indefinitely)
                    </span>
                  )}
                </div>
              </div>

              {/* 7. Creation Date & Options Dropdown */}
              <div className="mt-3.5 flex items-center justify-between gap-2 text-[11px] text-[#98a09c] min-w-0">
                <div className="flex items-center gap-1.5 shrink-0">
                  <Calendar size={12} className="shrink-0" />
                  <span>Created {new Date(room.created_at).toLocaleDateString()}</span>
                </div>

                <div className="flex items-center gap-1 shrink-0">
                  {/* Quick Status Toggle Button */}
                  <button
                    type="button"
                    onClick={() => handleToggleStatus(room)}
                    title={
                      room.status === 'ACTIVE' || room.status === 'OPEN'
                        ? 'Pause room'
                        : 'Reopen / Open room'
                    }
                    data-testid={`button-toggle-status-${room.id}`}
                    className="rounded-lg p-1 text-[#7b8490] hover:bg-[#eef0e7] hover:text-[#253142] transition"
                  >
                    {room.status === 'ACTIVE' || room.status === 'OPEN' ? (
                      <PauseCircle size={15} className="text-[#92400e]" />
                    ) : (
                      <PlayCircle size={15} className="text-[#277254]" />
                    )}
                  </button>

                  <div className="relative shrink-0" ref={openMenuId === room.id ? menuRef : undefined}>
                    <button
                      type="button"
                      aria-label="More actions"
                      data-testid={`button-more-actions-${room.id}`}
                      onClick={() => setOpenMenuId(openMenuId === room.id ? null : room.id)}
                      className="inline-flex items-center gap-1 rounded-lg px-1.5 py-1 text-xs font-semibold text-[#687382] hover:bg-[#eef0e7] hover:text-[#253142] transition"
                      title="More room options"
                    >
                      <MoreVertical size={14} />
                    </button>

                  {openMenuId === room.id && (
                    <div
                      className="absolute right-0 bottom-full mb-1.5 z-30 w-52 rounded-xl border border-[#d9dbd1] bg-white shadow-xl py-1 animate-in fade-in slide-in-from-bottom-2"
                      data-testid={`menu-more-actions-${room.id}`}
                    >
                      {/* US-45: Lifecycle State Actions */}
                      {room.status === 'ACTIVE' || room.status === 'OPEN' ? (
                        <>
                          <button
                            type="button"
                            onClick={() => { handleSetStatus(room, 'PAUSED'); setOpenMenuId(null); }}
                            data-testid={`button-pause-room-${room.id}`}
                            className="flex w-full items-center gap-2.5 px-3.5 py-2 text-xs font-semibold text-[#92400e] hover:bg-[#fef3c7] transition"
                          >
                            <PauseCircle size={14} className="text-[#92400e]" />
                            Pause Applications
                          </button>
                          <button
                            type="button"
                            onClick={() => { handleSetStatus(room, 'CLOSED'); setOpenMenuId(null); }}
                            data-testid={`button-close-room-${room.id}`}
                            className="flex w-full items-center gap-2.5 px-3.5 py-2 text-xs font-semibold text-[#991b1b] hover:bg-[#fee2e2] transition"
                          >
                            <X size={14} className="text-[#991b1b]" />
                            Close Room
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            type="button"
                            onClick={() => { handleSetStatus(room, 'OPEN'); setOpenMenuId(null); }}
                            data-testid={`button-reopen-room-${room.id}`}
                            className="flex w-full items-center gap-2.5 px-3.5 py-2 text-xs font-semibold text-[#277254] hover:bg-[#e2f0e9] transition"
                          >
                            <PlayCircle size={14} className="text-[#277254]" />
                            Reopen / Open Room
                          </button>
                          {room.status !== 'CLOSED' && (
                            <button
                              type="button"
                              onClick={() => { handleSetStatus(room, 'CLOSED'); setOpenMenuId(null); }}
                              data-testid={`button-close-room-${room.id}`}
                              className="flex w-full items-center gap-2.5 px-3.5 py-2 text-xs font-semibold text-[#991b1b] hover:bg-[#fee2e2] transition"
                            >
                              <X size={14} className="text-[#991b1b]" />
                              Close Room
                            </button>
                          )}
                        </>
                      )}

                      {/* Set Deadline */}
                      <button
                        type="button"
                        onClick={() => { openDeadlineModal(room); setOpenMenuId(null); }}
                        data-testid={`button-action-set-deadline-${room.id}`}
                        className="flex w-full items-center gap-2.5 px-3.5 py-2 text-xs font-semibold text-[#526072] hover:bg-[#f5f1e6] hover:text-[#253142] transition"
                      >
                        <Clock size={14} className="text-[#277254]" />
                        Set Application Deadline
                      </button>

                      {/* Configure Skills */}
                      <button
                        type="button"
                        onClick={() => { setRequirementsRoom(room); setOpenMenuId(null); }}
                        data-testid={`button-action-requirements-${room.id}`}
                        className="flex w-full items-center gap-2.5 px-3.5 py-2 text-xs font-semibold text-[#526072] hover:bg-[#f5f1e6] hover:text-[#253142] transition"
                      >
                        <Tag size={14} className="text-[#277254]" />
                        Configure Skills
                      </button>

                      {/* Evaluation Weights */}
                      <button
                        type="button"
                        onClick={() => { setWeightingRoom(room); setOpenMenuId(null); }}
                        data-testid={`button-action-weighting-${room.id}`}
                        className="flex w-full items-center gap-2.5 px-3.5 py-2 text-xs font-semibold text-[#526072] hover:bg-[#f5f1e6] hover:text-[#253142] transition"
                      >
                        <Sliders size={14} className="text-[#277254]" />
                        Evaluation Weights
                      </button>

                      {/* Shareable Link */}
                      <button
                        type="button"
                        onClick={() => { setShareLinkRoom(room); setOpenMenuId(null); }}
                        data-testid={`button-action-share-link-${room.id}`}
                        className="flex w-full items-center gap-2.5 px-3.5 py-2 text-xs font-semibold text-[#526072] hover:bg-[#f5f1e6] hover:text-[#253142] transition"
                      >
                        <Link2 size={14} className="text-[#277254]" />
                        Manage Share Link
                      </button>

                      {/* Configure Shortlisting (US-25) */}
                      <button
                        type="button"
                        onClick={() => { setShortlistRoom(room); setOpenMenuId(null); }}
                        data-testid={`button-action-shortlist-menu-${room.id}`}
                        className="flex w-full items-center gap-2.5 px-3.5 py-2 text-xs font-semibold text-[#526072] hover:bg-[#f5f1e6] hover:text-[#253142] transition"
                      >
                        <Star size={14} className="text-[#277254]" />
                        Shortlisting Rules
                      </button>

                      {/* Download Room Summary PDF (US-33) */}
                      <button
                        type="button"
                        onClick={() => { handleDownloadRoomPdf(room); setOpenMenuId(null); }}
                        data-testid={`button-download-room-pdf-${room.id}`}
                        disabled={downloadingRoomId === room.id}
                        className="flex w-full items-center gap-2.5 px-3.5 py-2 text-xs font-semibold text-[#526072] hover:bg-[#f5f1e6] hover:text-[#253142] transition disabled:opacity-50"
                      >
                        {downloadingRoomId === room.id ? (
                          <Loader2 size={14} className="animate-spin text-[#277254]" />
                        ) : (
                          <FileDown size={14} className="text-[#277254]" />
                        )}
                        {downloadingRoomId === room.id ? 'Exporting PDF...' : 'Download Room Report'}
                      </button>

                      <div className="my-1 border-t border-[#eef0e7]" />

                      {/* Edit */}
                      <button
                        type="button"
                        onClick={() => { openEditModal(room); setOpenMenuId(null); }}
                        data-testid={`button-edit-room-${room.id}`}
                        className="flex w-full items-center gap-2.5 px-3.5 py-2 text-xs font-semibold text-[#526072] hover:bg-[#f5f1e6] hover:text-[#253142] transition"
                      >
                        <Edit2 size={14} className="text-[#526072]" />
                        Edit Room
                      </button>

                      {/* Delete */}
                      <button
                        type="button"
                        onClick={() => { handleDelete(room); setOpenMenuId(null); }}
                        data-testid={`button-delete-room-${room.id}`}
                        className="flex w-full items-center gap-2.5 px-3.5 py-2 text-xs font-semibold text-[#b34a40] hover:bg-[#f7e5e1] transition"
                      >
                        <Trash2 size={14} />
                        Delete Room
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
            </div>

            {/* 8. Action Buttons Footer */}
            <div className="mt-4 pt-3.5 border-t border-[#eef0e7] w-full min-w-0">
              <div
                className="room-card__actions"
                data-testid={`card-actions-${room.id}`}
              >
                {/* 1) Copy Link */}
                <button
                  type="button"
                  onClick={() => handleCopyLink(room)}
                  data-testid={`button-copy-room-link-${room.id}`}
                  title="Copy application link"
                  className="inline-flex items-center justify-center gap-1.5 rounded-xl border border-[#c4e3d3] bg-[#f5fbf8] px-2 py-2 text-xs font-semibold text-[#1f5b43] hover:bg-[#e2f0e9] hover:border-[#a7d7c1] transition shadow-2xs min-w-0 w-full min-h-[36px]"
                >
                  {copiedId === room.id ? (
                    <>
                      <Check size={13} className="shrink-0 text-[#277254]" />
                      <span className="truncate">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy size={13} className="shrink-0 text-[#277254]" />
                      <span className="truncate">Copy Link</span>
                    </>
                  )}
                </button>

                {/* 2) CV Scores */}
                <button
                  type="button"
                  onClick={() => setCvScoresRoom(room)}
                  title="View Applicant CV Match Scores"
                  data-testid={`button-action-cv-scores-${room.id}`}
                  className="inline-flex items-center justify-center gap-1.5 rounded-xl border border-[#a7d7c1] bg-[#e2f0e9] px-2 py-2 text-xs font-bold text-[#1f5b43] hover:bg-[#d0e8dc] transition shadow-2xs min-w-0 w-full min-h-[36px]"
                >
                  <Award size={13} className="shrink-0" />
                  <span className="truncate">CV Scores</span>
                </button>

                {/* 3) Rankings */}
                <button
                  type="button"
                  onClick={() => setRankedRoom(room)}
                  title="View Applicant Leaderboard & Rankings"
                  data-testid={`button-action-ranking-${room.id}`}
                  className="inline-flex items-center justify-center gap-1.5 rounded-xl border border-[#fde68a] bg-[#fef3c7] px-2 py-2 text-xs font-bold text-[#92400e] hover:bg-[#fde68a] transition shadow-2xs min-w-0 w-full min-h-[36px]"
                >
                  <Trophy size={13} className="shrink-0 text-[#d97706]" />
                  <span className="truncate">Rankings</span>
                </button>

                {/* 4) Shortlist */}
                <button
                  type="button"
                  onClick={() => setShortlistRoom(room)}
                  title="Configure & View Candidate Shortlist (US-25)"
                  data-testid={`button-action-shortlist-${room.id}`}
                  className="inline-flex items-center justify-center gap-1.5 rounded-xl border border-[#a7d7c1] bg-[#e2f0e9] px-2 py-2 text-xs font-bold text-[#1f5b43] hover:bg-[#d0e8dc] transition shadow-2xs min-w-0 w-full min-h-[36px]"
                >
                  <Star size={13} className="shrink-0 fill-[#1f5b43] text-[#1f5b43]" />
                  <span className="truncate">Shortlist</span>
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Edit Room Modal */}
      {editingRoom && (
        <div
          role="dialog"
          aria-modal="true"
          data-testid="modal-edit-room"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in"
        >
          <div className="relative w-full max-w-lg rounded-2xl bg-white border border-[#d9dbd1] shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-[#eef0e7] pb-3">
              <h3 className="text-base font-bold text-[#253142]">Edit Recruitment Room</h3>
              <button
                type="button"
                onClick={() => setEditingRoom(null)}
                data-testid="button-close-edit-modal"
                className="rounded-lg p-1 text-[#7b8490] hover:bg-[#eef0e7]"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-bold text-[#253142] mb-1">Job Title</label>
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  data-testid="input-edit-room-title"
                  className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3.5 py-2 text-sm text-[#253142] focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-[#253142] mb-1">Company Name</label>
                <input
                  type="text"
                  value={editCompany}
                  onChange={(e) => setEditCompany(e.target.value)}
                  data-testid="input-edit-room-company"
                  className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3.5 py-2 text-sm text-[#253142] focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-[#253142] mb-1">Status</label>
                <select
                  value={editStatus}
                  onChange={(e) => setEditStatus(e.target.value as any)}
                  data-testid="select-edit-room-status"
                  className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3 py-2 text-xs text-[#253142] font-semibold"
                >
                  <option value="OPEN">OPEN</option>
                  <option value="PAUSED">PAUSED</option>
                  <option value="CLOSED">CLOSED</option>
                  <option value="DRAFT">DRAFT</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-[#253142] mb-1">Application Deadline</label>
                <input
                  type="datetime-local"
                  value={editDeadline}
                  onChange={(e) => setEditDeadline(e.target.value)}
                  data-testid="input-edit-room-deadline"
                  className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3.5 py-2 text-sm text-[#253142] focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-[#253142] mb-1">Description</label>
                <textarea
                  rows={3}
                  value={editDesc}
                  onChange={(e) => setEditDesc(e.target.value)}
                  data-testid="input-edit-room-description"
                  className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3.5 py-2 text-sm text-[#253142] focus:outline-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-[#eef0e7]">
              <button
                type="button"
                onClick={() => setEditingRoom(null)}
                data-testid="button-cancel-edit-room"
                className="rounded-xl px-4 py-2 text-xs font-semibold text-[#526072] hover:bg-[#eef0e7]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveEdit}
                disabled={savingEdit}
                data-testid="button-save-edit-room"
                className="inline-flex items-center gap-1.5 rounded-xl bg-[#277254] px-4 py-2 text-xs font-bold text-white hover:bg-[#1f5b43] transition disabled:opacity-50"
              >
                {savingEdit && <Loader2 size={14} className="animate-spin" />}
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Quick Deadline Modal (US-45) */}
      {deadlineModalRoom && (
        <div
          role="dialog"
          aria-modal="true"
          data-testid="modal-set-deadline"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in"
        >
          <div className="relative w-full max-w-md rounded-2xl bg-white border border-[#d9dbd1] shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-[#eef0e7] pb-3">
              <div className="flex items-center gap-2">
                <Clock size={18} className="text-[#277254]" />
                <h3 className="text-base font-bold text-[#253142]">Set Application Deadline</h3>
              </div>
              <button
                type="button"
                onClick={() => setDeadlineModalRoom(null)}
                data-testid="button-cancel-deadline"
                className="rounded-lg p-1 text-[#7b8490] hover:bg-[#eef0e7]"
              >
                <X size={18} />
              </button>
            </div>

            <p className="text-xs text-[#687382]">
              Set an expiration date and time for candidates submitting applications to{' '}
              <strong className="text-[#253142]">{deadlineModalRoom.title}</strong>. Submissions will be automatically blocked once this deadline passes.
            </p>

            <div className="space-y-2">
              <label className="block text-xs font-bold text-[#253142]">Deadline Date & Time</label>
              <input
                type="datetime-local"
                value={quickDeadlineValue}
                onChange={(e) => setQuickDeadlineValue(e.target.value)}
                data-testid="input-room-deadline"
                className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3.5 py-2.5 text-sm text-[#253142] focus:outline-none focus:ring-2 focus:ring-[#277254]/30"
              />
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-[#eef0e7]">
              <div>
                {deadlineModalRoom.application_deadline && (
                  <button
                    type="button"
                    onClick={handleClearDeadline}
                    disabled={savingDeadline}
                    data-testid="button-clear-deadline"
                    className="rounded-xl px-3 py-2 text-xs font-semibold text-[#b34a40] hover:bg-[#f7e5e1] transition disabled:opacity-50"
                  >
                    Clear Deadline
                  </button>
                )}
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setDeadlineModalRoom(null)}
                  data-testid="button-close-deadline-modal"
                  className="rounded-xl px-4 py-2 text-xs font-semibold text-[#526072] hover:bg-[#eef0e7]"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSaveQuickDeadline}
                  disabled={savingDeadline}
                  data-testid="button-save-deadline"
                  className="inline-flex items-center gap-1.5 rounded-xl bg-[#277254] px-4 py-2 text-xs font-bold text-white hover:bg-[#1f5b43] transition disabled:opacity-50"
                >
                  {savingDeadline && <Loader2 size={14} className="animate-spin" />}
                  Save Deadline
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Job Role & Requirements Modal (US-19) */}
      <JobRequirementsForm
        room={requirementsRoom}
        isOpen={!!requirementsRoom}
        onClose={() => setRequirementsRoom(null)}
        onRoomUpdated={(updated) => {
          onRoomUpdated(updated);
          setRequirementsRoom(null);
        }}
        notify={notify}
      />

      {/* Evaluation Weighting Modal (US-20) */}
      {weightingRoom && (
        <WeightingConfigCard
          room={weightingRoom}
          onClose={() => setWeightingRoom(null)}
          onWeightingSaved={(updated) => {
            onRoomUpdated(updated);
            setWeightingRoom(null);
          }}
          notify={notify}
        />
      )}

      {/* Shareable Application Link Modal (US-21) */}
      {shareLinkRoom && (
        <ShareableLinkCard
          room={shareLinkRoom}
          onClose={() => setShareLinkRoom(null)}
          onRoomUpdated={(updated) => {
            onRoomUpdated(updated);
            setShareLinkRoom(updated);
          }}
          notify={notify}
        />
      )}

      {/* Applicant CV Match Scores Modal (US-10) */}
      {cvScoresRoom && (
        <RoomCvScoresModal
          isOpen={Boolean(cvScoresRoom)}
          onClose={() => setCvScoresRoom(null)}
          room={cvScoresRoom}
          notify={notify}
        />
      )}

      {/* Applicant Leaderboard & Rankings Modal (US-24) */}
      {rankedRoom && (
        <RankedApplicantsModal
          isOpen={Boolean(rankedRoom)}
          onClose={() => setRankedRoom(null)}
          room={rankedRoom}
          notify={notify}
        />
      )}

      {/* Automatic Shortlisting Modal (US-25) */}
      {shortlistRoom && (
        <ShortlistConfigModal
          isOpen={Boolean(shortlistRoom)}
          onClose={() => setShortlistRoom(null)}
          room={shortlistRoom}
          onShortlistSaved={(updated) => {
            onRoomUpdated(updated);
            setShortlistRoom(updated);
          }}
          notify={notify}
        />
      )}
    </div>
  );
}


