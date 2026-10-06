import { useState, useEffect } from 'react';
import { Plus, FolderOpen, Loader2 } from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import { PageHeading, type Notify } from '../components/dashboard/DashboardShared';
import { RoomList } from '../components/recruitment/RoomList';
import { RoomCreateModal } from '../components/recruitment/RoomCreateModal';
import { apiGetRooms, type RecruitmentRoom } from '../api/recruitment';

export function RecruitmentRoomsPage({ notify }: { notify: Notify }) {
  const [rooms, setRooms] = useState<RecruitmentRoom[]>([]);
  const [loading, setLoading] = useState(true);
  const [createModalOpen, setCreateModalOpen] = useState(false);

  const fetchRooms = async () => {
    try {
      setLoading(true);
      const data = await apiGetRooms();
      setRooms(data);
    } catch {
      notify('Failed to load recruitment rooms.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRooms();
  }, []);

  const handleRoomCreated = (newRoom: RecruitmentRoom) => {
    setRooms((prev) => [newRoom, ...prev]);
  };

  const handleRoomUpdated = (updatedRoom: RecruitmentRoom) => {
    setRooms((prev) =>
      prev.map((r) => (r.id === updatedRoom.id ? updatedRoom : r))
    );
  };

  const handleRoomDeleted = (deletedRoomId: number) => {
    setRooms((prev) => prev.filter((r) => r.id !== deletedRoomId));
  };

  return (
    <AppShell role="hr" notify={notify}>
      <PageHeading
        eyebrow="HR Hiring Portal • US-18 Room Management"
        title="Recruitment Rooms"
        description="Create and manage job-specific hiring rooms, evaluation criteria, and candidate application links."
        action={
          <button
            type="button"
            onClick={() => setCreateModalOpen(true)}
            data-testid="button-create-room-page"
            className="inline-flex items-center gap-2 rounded-xl bg-[#277254] px-4 py-2.5 text-sm font-bold text-white hover:bg-[#1f5b43] transition shadow-xs"
          >
            <Plus size={16} /> Create Room
          </button>
        }
      />

      {loading ? (
        <div className="flex h-64 items-center justify-center rounded-2xl bg-white border border-[#d9dbd1]">
          <div className="flex items-center gap-2 text-sm text-[#7b8490]">
            <Loader2 size={18} className="animate-spin text-[#277254]" />
            Loading recruitment rooms...
          </div>
        </div>
      ) : (
        <RoomList
          rooms={rooms}
          onOpenCreateModal={() => setCreateModalOpen(true)}
          onRoomUpdated={handleRoomUpdated}
          onRoomDeleted={handleRoomDeleted}
          notify={notify}
        />
      )}

      {/* Creation Modal */}
      <RoomCreateModal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onRoomCreated={handleRoomCreated}
        notify={notify}
      />
    </AppShell>
  );
}
