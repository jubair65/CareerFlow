import { useState, useEffect, useMemo } from 'react';
import {
  FolderOpen,
  Plus,
  Building2,
  Users,
  Search,
  Filter,
  Layers,
  Copy,
  Check,
  ExternalLink,
  SlidersHorizontal,
  FileText,
  AlertCircle,
  Loader2,
  ChevronDown,
  ChevronRight,
  Sparkles,
  Link as LinkIcon,
  Globe,
  Lock,
  RefreshCw,
  Star,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import { PageHeading, StatCard, type Notify } from '../components/dashboard/DashboardShared';
import {
  apiGetAgencyRoomsGrouped,
  apiGetAgencyRoomStats,
  apiGetAgencyClients,
  apiUpdateAgencyRoom,
  apiToggleAgencyRoomLink,
  type AgencyClientGroupedRooms,
  type AgencyRoomStats,
  type RecruitmentRoom,
  type ClientCompany,
} from '../api/recruitment';
import { AgencyRoomCreateModal } from '../components/agency/AgencyRoomCreateModal';
import { JobRequirementsForm } from '../components/recruitment/JobRequirementsForm';
import { WeightingConfigCard } from '../components/recruitment/WeightingConfigCard';
import { ShortlistConfigModal } from '../components/recruitment/ShortlistConfigModal';

export function AgencyRoomsPage({ notify }: { notify: Notify }) {
  // Data state
  const [groupedClients, setGroupedClients] = useState<AgencyClientGroupedRooms[]>([]);
  const [clients, setClients] = useState<ClientCompany[]>([]);
  const [stats, setStats] = useState<AgencyRoomStats>({
    total_rooms: 0,
    active_rooms: 0,
    clients_with_rooms: 0,
    total_applicants: 0,
  });
  const [loading, setLoading] = useState(true);

  // Filters
  const [selectedClientId, setSelectedClientId] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [collapsedClients, setCollapsedClients] = useState<Record<number, boolean>>({});

  // Modals state
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [createInitialClientId, setCreateInitialClientId] = useState<number | undefined>(undefined);
  const [requirementsModalRoom, setRequirementsModalRoom] = useState<RecruitmentRoom | null>(null);
  const [weightingModalRoom, setWeightingModalRoom] = useState<RecruitmentRoom | null>(null);
  const [shortlistModalRoom, setShortlistModalRoom] = useState<RecruitmentRoom | null>(null);

  // Link copy feedback
  const [copiedRoomId, setCopiedRoomId] = useState<number | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [groupedData, statsData, clientsData] = await Promise.all([
        apiGetAgencyRoomsGrouped(),
        apiGetAgencyRoomStats(),
        apiGetAgencyClients({ status: 'active' }),
      ]);
      setGroupedClients(groupedData);
      setStats(statsData);
      setClients(clientsData);
    } catch {
      notify('Failed to load agency recruitment rooms.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Filtered grouped clients
  const filteredGroups = useMemo(() => {
    return groupedClients
      .filter((group) => {
        if (selectedClientId !== 'all' && String(group.client_id) !== selectedClientId) {
          return false;
        }
        return true;
      })
      .map((group) => {
        const filteredRooms = group.rooms.filter((room) => {
          if (selectedStatus !== 'all' && room.status !== selectedStatus) {
            return false;
          }
          if (searchQuery.trim()) {
            const q = searchQuery.toLowerCase();
            const matchesTitle = room.title.toLowerCase().includes(q);
            const matchesDept = (room.department || '').toLowerCase().includes(q);
            const matchesCategory = (room.role_category || '').toLowerCase().includes(q);
            const matchesClient = group.client_name.toLowerCase().includes(q);
            if (!matchesTitle && !matchesDept && !matchesCategory && !matchesClient) {
              return false;
            }
          }
          return true;
        });

        return {
          ...group,
          rooms: filteredRooms,
        };
      })
      .filter((group) => {
        // If searching or filtering by status, hide client groups that have 0 matching rooms
        if (searchQuery.trim() || selectedStatus !== 'all') {
          return group.rooms.length > 0;
        }
        return true;
      });
  }, [groupedClients, selectedClientId, selectedStatus, searchQuery]);

  const totalVisibleRooms = useMemo(() => {
    return filteredGroups.reduce((acc, g) => acc + g.rooms.length, 0);
  }, [filteredGroups]);

  const toggleClientCollapse = (clientId: number) => {
    setCollapsedClients((prev) => ({
      ...prev,
      [clientId]: !prev[clientId],
    }));
  };

  const handleOpenCreateForClient = (clientId?: number) => {
    setCreateInitialClientId(clientId);
    setCreateModalOpen(true);
  };

  const handleRoomCreated = (newRoom: RecruitmentRoom) => {
    fetchData();
  };

  const handleRoomUpdated = (updatedRoom: RecruitmentRoom) => {
    setGroupedClients((prev) =>
      prev.map((g) => ({
        ...g,
        rooms: g.rooms.map((r) => (r.id === updatedRoom.id ? updatedRoom : r)),
      }))
    );
  };

  const handleCopyShareLink = (room: RecruitmentRoom) => {
    const origin = window.location.origin;
    const fullUrl = `${origin}/apply/${room.share_token}`;
    navigator.clipboard
      .writeText(fullUrl)
      .then(() => {
        setCopiedRoomId(room.id);
        notify('Application link copied to clipboard!', 'success');
        window.setTimeout(() => setCopiedRoomId(null), 2500);
      })
      .catch(() => {
        notify('Failed to copy link. Please copy manually.', 'error');
      });
  };

  const handleToggleRoomStatus = async (room: RecruitmentRoom, newStatus: 'ACTIVE' | 'PAUSED' | 'CLOSED') => {
    try {
      const res = await apiUpdateAgencyRoom(room.id, { status: newStatus });
      handleRoomUpdated(res.room);
      notify(`Room status updated to ${newStatus}.`, 'success');
    } catch {
      notify('Failed to update room status.', 'error');
    }
  };

  const handleToggleLinkActive = async (room: RecruitmentRoom) => {
    try {
      const nextActive = !room.link_is_active;
      const res = await apiToggleAgencyRoomLink(room.id, nextActive);
      const updated = {
        ...room,
        link_is_active: res.link.link_is_active,
      };
      handleRoomUpdated(updated);
      notify(
        `Application link ${nextActive ? 'activated' : 'deactivated'} successfully.`,
        nextActive ? 'success' : 'info'
      );
    } catch {
      notify('Failed to toggle application link status.', 'error');
    }
  };

  return (
    <AppShell role="agency" notify={notify}>
      <div data-testid="page-agency-rooms" className="space-y-6">
        {/* Page Heading */}
        <PageHeading
          eyebrow="Recruitment Agency • US-30 Client Room Management"
          title="Client Recruitment Rooms"
          description="Create, configure, and manage job openings and candidate application links on behalf of your client companies."
          action={
            <button
              type="button"
              onClick={() => handleOpenCreateForClient()}
              data-testid="button-agency-create-room-page"
              className="inline-flex items-center gap-2 rounded-xl bg-[#277254] px-4 py-2.5 text-sm font-bold text-white hover:bg-[#1f5b43] transition shadow-xs shrink-0"
            >
              <Plus size={16} /> Create Room
            </button>
          }
        />

        {/* 4 Metric KPI Cards */}
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard
            label="Total Rooms"
            value={String(stats.total_rooms)}
            detail="Configured across clients"
            icon={FolderOpen}
            accent="blue"
          />
          <StatCard
            label="Active Openings"
            value={String(stats.active_rooms)}
            detail="Accepting candidate applications"
            icon={Sparkles}
            accent="green"
          />
          <StatCard
            label="Managed Clients"
            value={String(stats.clients_with_rooms)}
            detail="With active rooms"
            icon={Building2}
            accent="yellow"
          />
          <StatCard
            label="Total Candidates"
            value={String(stats.total_applicants)}
            detail="Applied via agency links"
            icon={Users}
            accent="coral"
          />
        </div>

        {/* Filters and Controls Toolbar */}
        <div className="rounded-2xl border border-[#d9dbd1] bg-white p-4 shadow-xs space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-center">
            {/* Search */}
            <div className="sm:col-span-5 relative">
              <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#7b8490]" />
              <input
                type="text"
                data-testid="input-search-rooms"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search rooms by title, department, or client..."
                className="w-full rounded-xl border border-[#d9dbd1] bg-white pl-9 pr-3.5 py-2 text-xs font-medium text-[#253142] placeholder-[#7b8490]/60 focus:border-[#277254] focus:outline-hidden focus:ring-2 focus:ring-[#277254]/20 transition"
              />
            </div>

            {/* Client Filter */}
            <div className="sm:col-span-4">
              <select
                data-testid="select-client-filter"
                value={selectedClientId}
                onChange={(e) => setSelectedClientId(e.target.value)}
                className="w-full rounded-xl border border-[#d9dbd1] bg-white px-3 py-2 text-xs font-semibold text-[#253142] focus:border-[#277254] focus:outline-hidden focus:ring-2 focus:ring-[#277254]/20 transition"
              >
                <option value="all">All Client Companies ({clients.length})</option>
                {clients.map((c) => (
                  <option key={c.id} value={String(c.id)}>
                    {c.name} ({c.industry})
                  </option>
                ))}
              </select>
            </div>

            {/* Status Filter */}
            <div className="sm:col-span-3">
              <select
                data-testid="select-status-filter"
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="w-full rounded-xl border border-[#d9dbd1] bg-white px-3 py-2 text-xs font-semibold text-[#253142] focus:border-[#277254] focus:outline-hidden focus:ring-2 focus:ring-[#277254]/20 transition"
              >
                <option value="all">All Statuses</option>
                <option value="ACTIVE">Active</option>
                <option value="PAUSED">Paused</option>
                <option value="CLOSED">Closed</option>
              </select>
            </div>
          </div>

          <div className="flex items-center justify-between text-xs text-[#7b8490] pt-2 border-t border-[#eef0e7]">
            <span data-testid="text-rooms-count">
              Showing <strong>{totalVisibleRooms}</strong> rooms across <strong>{filteredGroups.length}</strong> client companies
            </span>
            <button
              type="button"
              onClick={fetchData}
              data-testid="button-refresh-rooms"
              className="inline-flex items-center gap-1.5 font-semibold text-[#277254] hover:underline"
            >
              <RefreshCw size={13} className={loading ? 'animate-spin' : ''} /> Refresh
            </button>
          </div>
        </div>

        {/* Grouped Client Rooms View (AC#6) */}
        {loading ? (
          <div className="flex h-64 items-center justify-center rounded-2xl bg-white border border-[#d9dbd1]">
            <div className="flex items-center gap-2 text-sm text-[#7b8490]">
              <Loader2 size={18} className="animate-spin text-[#277254]" />
              Loading client recruitment rooms...
            </div>
          </div>
        ) : filteredGroups.length === 0 ? (
          <div
            data-testid="banner-empty-rooms"
            className="rounded-2xl border border-[#d9dbd1] bg-white p-12 text-center shadow-xs"
          >
            <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-[#eef0e7] text-[#526072]">
              <FolderOpen size={28} />
            </div>
            <h3 className="mt-4 text-base font-bold text-[#253142]">No recruitment rooms found</h3>
            <p className="mx-auto mt-1 max-w-sm text-xs text-[#7b8490]">
              {searchQuery || selectedClientId !== 'all' || selectedStatus !== 'all'
                ? 'Try adjusting your filters or search keywords.'
                : 'Start by creating your first recruitment opening for one of your client companies.'}
            </p>
            <button
              type="button"
              onClick={() => handleOpenCreateForClient()}
              data-testid="button-create-first-room"
              className="mt-5 inline-flex items-center gap-2 rounded-xl bg-[#277254] px-4 py-2.5 text-xs font-bold text-white hover:bg-[#1f5b43] transition shadow-xs"
            >
              <Plus size={15} /> Create First Room
            </button>
          </div>
        ) : (
          <div className="space-y-6" data-testid="list-client-room-groups">
            {filteredGroups.map((group) => {
              const isCollapsed = collapsedClients[group.client_id];

              return (
                <div
                  key={group.client_id}
                  data-testid={`card-client-group-${group.client_id}`}
                  className="rounded-2xl border border-[#d9dbd1] bg-white shadow-xs overflow-hidden"
                >
                  {/* Client Header */}
                  <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#eef0e7] bg-[#fafaf7] px-5 py-3.5">
                    <button
                      type="button"
                      onClick={() => toggleClientCollapse(group.client_id)}
                      data-testid={`button-toggle-collapse-${group.client_id}`}
                      className="flex items-center gap-2.5 text-left group"
                    >
                      <div className="grid h-8 w-8 place-items-center rounded-lg bg-[#e2f0e9] text-[#277254]">
                        <Building2 size={16} />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-bold text-sm text-[#253142] group-hover:text-[#277254] transition">
                            {group.client_name}
                          </h3>
                          <span className="rounded-md bg-[#eef0e7] px-2 py-0.5 text-[10px] font-bold text-[#526072]">
                            {group.industry}
                          </span>
                          {!group.is_active && (
                            <span className="rounded-md bg-[#f7e5e1] px-2 py-0.5 text-[10px] font-bold text-[#a33d35]">
                              Deactivated
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-[#7b8490]">
                          Contact: {group.contact_person} • {group.contact_email}
                        </p>
                      </div>
                      {isCollapsed ? (
                        <ChevronRight size={16} className="text-[#7b8490] ml-2" />
                      ) : (
                        <ChevronDown size={16} className="text-[#7b8490] ml-2" />
                      )}
                    </button>

                    <div className="flex items-center gap-2">
                      <span
                        data-testid={`badge-rooms-count-${group.client_id}`}
                        className="rounded-full bg-white px-2.5 py-1 text-xs font-bold text-[#277254] border border-[#d9dbd1]"
                      >
                        {group.rooms.length} {group.rooms.length === 1 ? 'Room' : 'Rooms'}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleOpenCreateForClient(group.client_id)}
                        data-testid={`button-add-room-for-client-${group.client_id}`}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-[#d9dbd1] bg-white px-2.5 py-1 text-xs font-bold text-[#253142] hover:bg-[#eef0e7] hover:border-[#253142] transition"
                      >
                        <Plus size={13} /> Add Room
                      </button>
                    </div>
                  </div>

                  {/* Rooms Grid for this Client */}
                  {!isCollapsed && (
                    <div className="p-5">
                      {group.rooms.length === 0 ? (
                        <div
                          data-testid={`client-no-rooms-${group.client_id}`}
                          className="rounded-xl border border-dashed border-[#d9dbd1] p-6 text-center text-xs text-[#7b8490]"
                        >
                          No active recruitment rooms for {group.client_name}.
                          <div className="mt-2">
                            <button
                              type="button"
                              onClick={() => handleOpenCreateForClient(group.client_id)}
                              className="font-bold text-[#277254] hover:underline"
                            >
                              + Create a room for this client
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                          {group.rooms.map((room) => {
                            const origin = window.location.origin;
                            const shareUrl = `${origin}/apply/${room.share_token}`;
                            const isCopied = copiedRoomId === room.id;

                            return (
                              <div
                                key={room.id}
                                data-testid={`card-room-${room.id}`}
                                className="flex flex-col justify-between rounded-xl border border-[#d9dbd1] bg-white p-4 shadow-2xs hover:shadow-sm hover:border-[#277254]/50 transition duration-150"
                              >
                                <div>
                                  {/* Status & Level Badges */}
                                  <div className="flex items-center justify-between gap-2 mb-2.5">
                                    <span
                                      data-testid={`room-status-${room.id}`}
                                      className={`rounded-md px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                                        room.status === 'ACTIVE'
                                          ? 'bg-[#e2f0e9] text-[#277254]'
                                          : room.status === 'PAUSED'
                                          ? 'bg-[#fbf5e6] text-[#735118]'
                                          : 'bg-[#f7e5e1] text-[#a33d35]'
                                      }`}
                                    >
                                      {room.status}
                                    </span>
                                    <span
                                      data-testid={`room-level-${room.id}`}
                                      className="rounded-md bg-[#eef0e7] px-2 py-0.5 text-[10px] font-semibold text-[#526072]"
                                    >
                                      {room.experience_level_display || room.experience_level}
                                    </span>
                                  </div>

                                  {/* Title & Department */}
                                  <h4
                                    data-testid={`room-title-${room.id}`}
                                    className="font-bold text-sm text-[#253142] line-clamp-1"
                                  >
                                    {room.title}
                                  </h4>
                                  <p className="text-[11px] text-[#7b8490] mt-0.5">
                                    {room.department ? `${room.department} • ` : ''}
                                    {room.role_category || 'General'}
                                  </p>

                                  {/* Evaluation Weights Pill */}
                                  <div className="mt-3 flex items-center justify-between rounded-lg bg-[#fafaf7] px-2.5 py-1.5 text-[11px] text-[#526072] border border-[#eef0e7]">
                                    <span className="font-semibold">Weights:</span>
                                    <span data-testid={`room-weights-${room.id}`} className="font-bold text-[#277254]">
                                      {room.cv_weight}% CV / {room.video_weight}% Video
                                    </span>
                                  </div>

                                  {/* Shareable Link Box */}
                                  <div className="mt-3 rounded-lg border border-[#eef0e7] bg-[#fafaf7] p-2">
                                    <div className="flex items-center justify-between text-[11px] text-[#526072] mb-1">
                                      <span className="flex items-center gap-1 font-semibold">
                                        <LinkIcon size={11} className="text-[#277254]" /> Application Link
                                      </span>
                                      <button
                                        type="button"
                                        onClick={() => handleToggleLinkActive(room)}
                                        data-testid={`button-toggle-link-${room.id}`}
                                        className={`text-[10px] font-bold ${
                                          room.link_is_active
                                            ? 'text-[#277254] hover:underline'
                                            : 'text-[#a33d35] hover:underline'
                                        }`}
                                      >
                                        {room.link_is_active ? 'Active' : 'Disabled'}
                                      </button>
                                    </div>
                                    <div className="flex items-center gap-1.5">
                                      <input
                                        type="text"
                                        readOnly
                                        value={shareUrl}
                                        data-testid={`input-room-link-${room.id}`}
                                        className="w-full bg-white rounded border border-[#d9dbd1] px-2 py-1 text-[10px] font-mono text-[#526072] truncate"
                                      />
                                      <button
                                        type="button"
                                        onClick={() => handleCopyShareLink(room)}
                                        data-testid={`button-copy-link-${room.id}`}
                                        title="Copy link"
                                        className={`shrink-0 rounded p-1 transition ${
                                          isCopied
                                            ? 'bg-[#e2f0e9] text-[#277254]'
                                            : 'bg-white border border-[#d9dbd1] text-[#526072] hover:bg-[#eef0e7]'
                                        }`}
                                      >
                                        {isCopied ? <Check size={13} /> : <Copy size={13} />}
                                      </button>
                                    </div>
                                  </div>
                                </div>

                                {/* Room Action Buttons */}
                                <div className="mt-4 pt-3 border-t border-[#eef0e7] flex items-center justify-between gap-1.5">
                                  <div className="flex items-center gap-1.5">
                                    <button
                                      type="button"
                                      onClick={() => setRequirementsModalRoom(room)}
                                      data-testid={`button-config-reqs-${room.id}`}
                                      className="inline-flex items-center gap-1 rounded-lg border border-[#d9dbd1] bg-white px-2 py-1 text-[11px] font-bold text-[#253142] hover:bg-[#eef0e7] transition"
                                      title="Configure criteria & skills"
                                    >
                                      <FileText size={12} className="text-[#277254]" /> Criteria
                                    </button>
                                    <button
                                      type="button"
                                      onClick={() => setWeightingModalRoom(room)}
                                      data-testid={`button-config-weights-${room.id}`}
                                      className="inline-flex items-center gap-1 rounded-lg border border-[#d9dbd1] bg-white px-2 py-1 text-[11px] font-bold text-[#253142] hover:bg-[#eef0e7] transition"
                                      title="Configure CV/Video weighting"
                                    >
                                      <SlidersHorizontal size={12} className="text-[#277254]" /> Weights
                                    </button>
                                    <button
                                      type="button"
                                      onClick={() => setShortlistModalRoom(room)}
                                      data-testid={`button-config-shortlist-${room.id}`}
                                      className="inline-flex items-center gap-1 rounded-lg border border-[#d9dbd1] bg-white px-2 py-1 text-[11px] font-bold text-[#253142] hover:bg-[#eef0e7] transition cursor-pointer"
                                      title="Configure automatic shortlisting rules"
                                    >
                                      <Star size={12} className="text-[#8a6a16]" /> Shortlist
                                    </button>
                                  </div>

                                  {/* Quick Status Select */}
                                  <select
                                    data-testid={`select-room-status-${room.id}`}
                                    value={room.status}
                                    onChange={(e) => handleToggleRoomStatus(room, e.target.value as any)}
                                    className="rounded-lg border border-[#d9dbd1] bg-white px-1.5 py-1 text-[10px] font-semibold text-[#526072] focus:border-[#277254] focus:outline-hidden"
                                  >
                                    <option value="ACTIVE">Active</option>
                                    <option value="PAUSED">Paused</option>
                                    <option value="CLOSED">Closed</option>
                                  </select>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Modal: Agency Room Creation */}
        <AgencyRoomCreateModal
          isOpen={createModalOpen}
          onClose={() => setCreateModalOpen(false)}
          onRoomCreated={handleRoomCreated}
          notify={notify}
          initialClientId={createInitialClientId}
        />

        {/* Modal: Job Requirements (US-30-T3 Reuse) */}
        {requirementsModalRoom && (
          <JobRequirementsForm
            room={requirementsModalRoom}
            isOpen={Boolean(requirementsModalRoom)}
            onClose={() => setRequirementsModalRoom(null)}
            onRoomUpdated={handleRoomUpdated}
            notify={notify}
          />
        )}

        {/* Modal: Shortlist Configuration (US-25 Reuse) */}
        {shortlistModalRoom && (
          <ShortlistConfigModal
            isOpen={Boolean(shortlistModalRoom)}
            onClose={() => setShortlistModalRoom(null)}
            room={shortlistModalRoom}
            onShortlistUpdated={() => {
              fetchData();
              setShortlistModalRoom(null);
            }}
            notify={notify}
          />
        )}

        {/* Modal: Weighting Config (US-30-T3 Reuse) */}
        {weightingModalRoom && (
          <div
            role="dialog"
            aria-modal="true"
            data-testid="modal-agency-weighting-config"
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs overflow-y-auto"
          >
            <div className="relative w-full max-w-xl my-8">
              <WeightingConfigCard
                room={weightingModalRoom}
                onClose={() => setWeightingModalRoom(null)}
                onWeightingSaved={(updatedRoom) => {
                  handleRoomUpdated(updatedRoom);
                  setWeightingModalRoom(null);
                }}
                notify={notify}
              />
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
