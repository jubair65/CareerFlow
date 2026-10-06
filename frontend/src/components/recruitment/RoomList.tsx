import { useState, useMemo } from 'react';
import {
  FolderOpen,
  Plus,
  Search,
  ExternalLink,
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
} from 'lucide-react';
import type { RecruitmentRoom } from '../../api/recruitment';
import { apiUpdateRoom, apiDeleteRoom } from '../../api/recruitment';

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
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'ACTIVE' | 'PAUSED' | 'CLOSED'>('ALL');
  const [copiedId, setCopiedId] = useState<number | null>(null);

  // Edit Modal State
  const [editingRoom, setEditingRoom] = useState<RecruitmentRoom | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editCompany, setEditCompany] = useState('');
  const [editDept, setEditDept] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [editStatus, setEditStatus] = useState<'ACTIVE' | 'PAUSED' | 'CLOSED'>('ACTIVE');
  const [savingEdit, setSavingEdit] = useState(false);

  const filteredRooms = useMemo(() => {
    return rooms.filter((r) => {
      const matchSearch =
        r.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.company_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.department?.toLowerCase().includes(searchTerm.toLowerCase());
      const matchStatus = statusFilter === 'ALL' || r.status === statusFilter;
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

  const handleToggleStatus = async (room: RecruitmentRoom) => {
    const nextStatus = room.status === 'ACTIVE' ? 'PAUSED' : 'ACTIVE';
    try {
      const res = await apiUpdateRoom(room.id, { status: nextStatus });
      onRoomUpdated(res.room);
      notify?.(`Room "${room.title}" is now ${nextStatus.toLowerCase()}.`, 'success');
    } catch {
      notify?.(`Failed to update room status.`, 'error');
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
    setEditStatus(room.status);
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
    <div className="space-y-5" data-testid="section-recruitment-rooms">
      {/* Top Filter & Search Controls */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-white p-4 rounded-2xl border border-[#d9dbd1] shadow-xs">
        <div className="relative w-full sm:w-80">
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

        <div className="flex items-center gap-2 w-full sm:w-auto justify-between sm:justify-end">
          <div className="flex items-center gap-1 bg-[#f5f1e6] p-1 rounded-xl">
            {(['ALL', 'ACTIVE', 'PAUSED', 'CLOSED'] as const).map((st) => (
              <button
                key={st}
                type="button"
                onClick={() => setStatusFilter(st)}
                data-testid={`filter-status-${st.toLowerCase()}`}
                className={`rounded-lg px-2.5 py-1 text-xs font-bold transition ${
                  statusFilter === st
                    ? 'bg-[#253142] text-white'
                    : 'text-[#687382] hover:text-[#253142]'
                }`}
              >
                {st === 'ALL' ? 'All' : st}
              </button>
            ))}
          </div>

          <button
            type="button"
            onClick={onOpenCreateModal}
            data-testid="button-create-room-header"
            className="inline-flex items-center gap-2 rounded-xl bg-[#277254] px-4 py-2 text-xs font-bold text-white hover:bg-[#1f5b43] transition shadow-xs"
          >
            <Plus size={15} /> Create Room
          </button>
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
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" data-testid="grid-recruitment-rooms">
        {filteredRooms.map((room) => (
          <div
            key={room.id}
            data-testid={`card-room-${room.id}`}
            className="flex flex-col justify-between rounded-2xl bg-white border border-[#d9dbd1] p-5 shadow-xs hover:border-[#277254]/40 hover:shadow-md transition duration-200"
          >
            <div>
              {/* Card Header: Company, Title & Status */}
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-[#7b8490]">
                    <Building2 size={13} />
                    <span>{room.company_name}</span>
                    {room.department && (
                      <span className="text-[11px] text-[#9aabb5]">• {room.department}</span>
                    )}
                  </div>
                  <h3
                    data-testid={`room-title-${room.id}`}
                    className="mt-1 text-base font-bold text-[#253142] line-clamp-1"
                  >
                    {room.title}
                  </h3>
                </div>
                <span
                  data-testid={`room-status-${room.id}`}
                  className={`inline-flex items-center rounded-lg px-2 py-0.5 text-[11px] font-bold uppercase tracking-wider ${
                    room.status === 'ACTIVE'
                      ? 'bg-[#e2f0e9] text-[#277254]'
                      : room.status === 'PAUSED'
                      ? 'bg-[#fef3c7] text-[#92400e]'
                      : 'bg-[#f1f3f5] text-[#687382]'
                  }`}
                >
                  {room.status}
                </span>
              </div>

              {/* Description Snippet */}
              <p className="mt-3 text-xs text-[#687382] line-clamp-2 leading-relaxed">
                {room.description || 'No job description provided.'}
              </p>

              {/* Evaluation Weights Indicator */}
              <div className="mt-4 flex items-center justify-between rounded-xl bg-[#fbfaf5] p-2.5 border border-[#eef0e7] text-xs">
                <div className="flex items-center gap-1.5 text-[#526072] font-medium">
                  <Sliders size={13} className="text-[#277254]" />
                  <span>Evaluation Weights:</span>
                </div>
                <div className="font-bold text-[#253142]">
                  CV {room.cv_weight || 50}% / Video {room.video_weight || 50}%
                </div>
              </div>

              {/* Date Metadata */}
              <div className="mt-3 flex items-center gap-1.5 text-[11px] text-[#98a09c]">
                <Calendar size={12} />
                <span>Created {new Date(room.created_at).toLocaleDateString()}</span>
              </div>
            </div>

            {/* Bottom Actions */}
            <div className="mt-5 pt-3 border-t border-[#eef0e7] flex items-center justify-between gap-2">
              <button
                type="button"
                onClick={() => handleCopyLink(room)}
                data-testid={`button-copy-room-link-${room.id}`}
                className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-[#277254] hover:bg-[#e2f0e9] transition"
              >
                {copiedId === room.id ? (
                  <>
                    <Check size={14} className="text-[#277254]" />
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy size={14} />
                    <span>Copy Link</span>
                  </>
                )}
              </button>

              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => handleToggleStatus(room)}
                  title={room.status === 'ACTIVE' ? 'Pause room' : 'Activate room'}
                  data-testid={`button-toggle-status-${room.id}`}
                  className="rounded-lg p-1.5 text-[#7b8490] hover:bg-[#eef0e7] hover:text-[#253142] transition"
                >
                  {room.status === 'ACTIVE' ? <PauseCircle size={16} /> : <PlayCircle size={16} />}
                </button>
                <button
                  type="button"
                  onClick={() => openEditModal(room)}
                  title="Edit Room"
                  data-testid={`button-edit-room-${room.id}`}
                  className="rounded-lg p-1.5 text-[#7b8490] hover:bg-[#eef0e7] hover:text-[#253142] transition"
                >
                  <Edit2 size={16} />
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(room)}
                  title="Delete Room"
                  data-testid={`button-delete-room-${room.id}`}
                  className="rounded-lg p-1.5 text-[#b34a40] hover:bg-[#f7e5e1] transition"
                >
                  <Trash2 size={16} />
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
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="PAUSED">PAUSED</option>
                  <option value="CLOSED">CLOSED</option>
                </select>
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
    </div>
  );
}
