import { useState, useEffect, useMemo, useRef } from 'react';
import { useLocation } from 'wouter';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import {
  Briefcase,
  Building2,
  Calendar,
  Clock,
  Sparkles,
  Sliders,
  CheckCircle2,
  ArrowRight,
  RefreshCw,
  Loader2,
  Search,
  X,
  Eye,
  Layers,
  FileText,
  Video,
  ExternalLink,
  Award,
  Filter,
  ChevronLeft,
  ChevronRight,
  Heart,
  Check,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import { PageHeading, type Notify } from '../components/dashboard/DashboardShared';
import {
  apiGetPublicJobRooms,
  apiGetPublicJobRoomDetail,
  type JobBoardRoom,
} from '../api/recruitment';
import {
  MOTION,
  PageTransition,
  Drawer,
  AnimatedNumber,
  ProgressRing,
  Stagger,
  ListItem,
} from '../motion';

export function JobBoardPage({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();
  const prefersReduced = useReducedMotion();
  const [rooms, setRooms] = useState<JobBoardRoom[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [expFilter, setExpFilter] = useState('ALL');
  const [statusTab, setStatusTab] = useState<'all' | 'not_applied' | 'applied'>('all');
  const [selectedRoomModal, setSelectedRoomModal] = useState<JobBoardRoom | null>(null);
  const [modalLoading, setModalLoading] = useState(false);
  const [savedRoomIds, setSavedRoomIds] = useState<number[]>(() => {
    try {
      return JSON.parse(localStorage.getItem('cf_saved_jobs_student') || '[]');
    } catch {
      return [];
    }
  });

  // Card reference for returning focus when drawer closes
  const triggerCardRef = useRef<HTMLElement | null>(null);

  // Pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(9);

  const fetchRooms = async () => {
    try {
      setLoading(true);
      const data = await apiGetPublicJobRooms();
      setRooms(data);
    } catch {
      notify('Unable to load open recruitment rooms. Please try again.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRooms();
  }, []);

  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, expFilter, statusTab, pageSize]);

  const toggleSaveRoom = (roomId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    setSavedRoomIds((prev) => {
      const exists = prev.includes(roomId);
      const updated = exists ? prev.filter((id) => id !== roomId) : [...prev, roomId];
      localStorage.setItem('cf_saved_jobs_student', JSON.stringify(updated));
      return updated;
    });
  };

  const handleOpenRoomModal = async (room: JobBoardRoom, e?: React.MouseEvent) => {
    if (e) {
      triggerCardRef.current = e.currentTarget as HTMLElement;
    }
    setSelectedRoomModal(room);
    setModalLoading(true);
    try {
      const detail = await apiGetPublicJobRoomDetail(room.id);
      setSelectedRoomModal(detail);
    } catch {
      // Keep displaying current room data if detail fetch fails
    } finally {
      setModalLoading(false);
    }
  };

  const handleCloseRoomModal = () => {
    setSelectedRoomModal(null);
    if (triggerCardRef.current) {
      triggerCardRef.current.focus();
    }
  };

  // Metrics
  const metrics = useMemo(() => {
    const total = rooms.length;
    const applied = rooms.filter((r) => r.has_applied || r.is_applied).length;
    const available = total - applied;
    const engineering = rooms.filter(
      (r) =>
        r.role_category?.toLowerCase().includes('engineer') ||
        r.title?.toLowerCase().includes('engineer') ||
        r.title?.toLowerCase().includes('developer')
    ).length;
    return { total, applied, available, engineering };
  }, [rooms]);

  // Filtered rooms
  const filteredRooms = useMemo(() => {
    return rooms.filter((room) => {
      const isApplied = room.has_applied || room.is_applied;
      if (statusTab === 'applied' && !isApplied) return false;
      if (statusTab === 'not_applied' && isApplied) return false;

      if (expFilter !== 'ALL' && room.experience_level !== expFilter) {
        return false;
      }

      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase().trim();
        const matchTitle = room.title?.toLowerCase().includes(query) ?? false;
        const matchCompany = room.company_name?.toLowerCase().includes(query) ?? false;
        const matchDept = room.department?.toLowerCase().includes(query) ?? false;
        const matchCategory = room.role_category?.toLowerCase().includes(query) ?? false;
        const matchSkills = room.skill_names?.some((s) => s.toLowerCase().includes(query)) ?? false;
        const matchDesc = room.description?.toLowerCase().includes(query) ?? false;

        if (!matchTitle && !matchCompany && !matchDept && !matchCategory && !matchSkills && !matchDesc) {
          return false;
        }
      }

      return true;
    });
  }, [rooms, statusTab, expFilter, searchQuery]);

  // Pagination Calculations
  const totalPages = Math.max(1, Math.ceil(filteredRooms.length / pageSize));
  const paginatedRooms = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredRooms.slice(start, start + pageSize);
  }, [filteredRooms, currentPage, pageSize]);

  const formatDate = (isoString: string | null | undefined) => {
    if (!isoString) return 'Open Enrollment';
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    } catch {
      return 'Open Enrollment';
    }
  };

  const formatLevel = (level?: string, display?: string) => {
    if (display) return display;
    switch (level) {
      case 'ENTRY':
        return 'Entry Level (0-2 yrs)';
      case 'MID':
        return 'Mid Level (2-5 yrs)';
      case 'SENIOR':
        return 'Senior Level (5-8 yrs)';
      case 'LEAD':
        return 'Lead / Principal (8+ yrs)';
      default:
        return 'All Experience Levels';
    }
  };

  const handleApplyClick = (room: JobBoardRoom) => {
    if (room.share_token) {
      setLocation(`/apply/${room.share_token}`);
    } else {
      notify('Application link token is unavailable for this room.', 'error');
    }
  };

  // Derive candidate matched vs missing skills for selected room
  const candidateSkills = ['React', 'TypeScript', 'Node.js', 'Tailwind CSS', 'Git', 'REST APIs', 'PostgreSQL'];
  const drawerSkills = useMemo(() => {
    if (!selectedRoomModal) return { matched: [], missing: [] };
    const required = selectedRoomModal.skill_names || (selectedRoomModal.skills_required as string[]) || [];
    const matched: string[] = [];
    const missing: string[] = [];
    required.forEach((s) => {
      const sName = typeof s === 'string' ? s : (s as any)?.name || 'Skill';
      if (candidateSkills.some((cs) => cs.toLowerCase() === sName.toLowerCase())) {
        matched.push(sName);
      } else {
        missing.push(sName);
      }
    });
    return { matched, missing };
  }, [selectedRoomModal]);

  return (
    <AppShell role="student" notify={notify}>
      <PageTransition>
        <PageHeading
          title="Recruitment Job Board"
          description="Discover active recruitment rooms, inspect skill requirements, and submit your multi-modal application directly."
          action={
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={fetchRooms}
                data-testid="button-refresh-jobs"
                className="inline-flex items-center gap-2 rounded-xl border border-[#d9dbd1] bg-white px-3.5 py-2 text-xs font-bold text-[#253142] hover:bg-[#f8f7f2] transition shadow-xs cursor-pointer active:scale-[0.98]"
              >
                <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
              </button>
              <button
                type="button"
                onClick={() => setLocation('/student/applications')}
                data-testid="button-my-applications-from-board"
                className="inline-flex items-center gap-2 rounded-xl bg-[#253142] px-4 py-2 text-xs font-bold text-white hover:bg-[#33435a] transition shadow-xs cursor-pointer shrink-0 active:scale-[0.98]"
              >
                <Briefcase size={14} /> My Applications
              </button>
            </div>
          }
        />

        {/* Metrics Row */}
        <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4" data-testid="job-board-metrics-bar">
          <div className="rounded-2xl border border-[#d9dbd1] bg-white p-4 shadow-xs">
            <div className="flex items-center justify-between text-xs font-bold text-[#7b8490]">
              <span>Open Positions</span>
              <Briefcase size={15} className="text-[#253142]" />
            </div>
            <div className="mt-2 text-2xl font-black text-[#253142]" data-testid="metric-open-positions">
              <AnimatedNumber value={metrics.total} />
            </div>
            <div className="mt-0.5 text-[11px] text-[#7b8490]">Active hiring rooms</div>
          </div>

          <div className="rounded-2xl border border-[#c5d8ce] bg-[#f8fbf9] p-4 shadow-xs">
            <div className="flex items-center justify-between text-xs font-bold text-[#277254]">
              <span>Ready to Apply</span>
              <Sparkles size={15} className="text-[#277254]" />
            </div>
            <div className="mt-2 text-2xl font-black text-[#277254]" data-testid="metric-available-positions">
              <AnimatedNumber value={metrics.available} />
            </div>
            <div className="mt-0.5 text-[11px] text-[#277254]/80">Awaiting your application</div>
          </div>

          <div className="rounded-2xl border border-[#dedfd6] bg-[#faf9f5] p-4 shadow-xs">
            <div className="flex items-center justify-between text-xs font-bold text-[#526072]">
              <span>Already Applied</span>
              <CheckCircle2 size={15} className="text-[#277254]" />
            </div>
            <div className="mt-2 text-2xl font-black text-[#253142]" data-testid="metric-applied-positions">
              <AnimatedNumber value={metrics.applied} />
            </div>
            <div className="mt-0.5 text-[11px] text-[#7b8490]">In your tracking pipeline</div>
          </div>

          <div className="rounded-2xl border border-[#dedfd6] bg-white p-4 shadow-xs">
            <div className="flex items-center justify-between text-xs font-bold text-[#7b8490]">
              <span>Engineering Roles</span>
              <Layers size={15} className="text-[#3a6384]" />
            </div>
            <div className="mt-2 text-2xl font-black text-[#253142]">
              <AnimatedNumber value={metrics.engineering} />
            </div>
            <div className="mt-0.5 text-[11px] text-[#7b8490]">Technical opportunities</div>
          </div>
        </div>

        {/* Search, Filter & Tabs Bar */}
        <div className="mt-6 flex flex-col gap-4 border-b border-[#dedfd6] pb-4">
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
            {/* Search Box */}
            <div className="relative flex-1">
              <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#7b8490]" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by job title, company, required skill, or keyword..."
                data-testid="input-search-jobs"
                className="w-full rounded-xl border border-[#d9dbd1] bg-white py-2 pl-9 pr-8 text-xs font-medium text-[#253142] placeholder:text-[#9ca3af] focus:border-[#277254] focus:outline-none focus:ring-1 focus:ring-[#277254] transition shadow-xs"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery('')}
                  aria-label="Clear search"
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded-md p-1 text-[#9ca3af] hover:text-[#253142]"
                >
                  <X size={13} />
                </button>
              )}
            </div>

            {/* Experience Level Selector */}
            <div className="flex items-center gap-2">
              <Filter size={14} className="text-[#7b8490] shrink-0" />
              <select
                value={expFilter}
                onChange={(e) => setExpFilter(e.target.value)}
                data-testid="select-experience-filter"
                aria-label="Filter by experience level"
                className="rounded-xl border border-[#d9dbd1] bg-white px-3 py-2 text-xs font-semibold text-[#253142] focus:border-[#277254] focus:outline-none focus:ring-1 focus:ring-[#277254] transition shadow-xs cursor-pointer"
              >
                <option value="ALL">All Experience Levels</option>
                <option value="ENTRY">Entry Level (0-2 yrs)</option>
                <option value="MID">Mid Level (2-5 yrs)</option>
                <option value="SENIOR">Senior Level (5-8 yrs)</option>
                <option value="LEAD">Lead / Principal (8+ yrs)</option>
              </select>
            </div>
          </div>

          {/* Status Tabs and Result Counter */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pt-1">
            <div className="flex items-center gap-1.5" data-testid="job-board-status-tabs">
              <button
                type="button"
                onClick={() => setStatusTab('all')}
                data-testid="filter-tab-all-jobs"
                className={`relative flex items-center gap-2 rounded-xl px-3.5 py-1.5 text-xs font-bold transition duration-150 cursor-pointer ${
                  statusTab === 'all'
                    ? 'bg-[#253142] text-white'
                    : 'bg-white text-[#526072] border border-[#d9dbd1] hover:bg-[#f8f7f2]'
                }`}
              >
                <span>All Roles</span>
                <span
                  className={`rounded-full px-1.5 py-0.2 text-[10px] ${
                    statusTab === 'all' ? 'bg-white/20 text-white' : 'bg-[#eef0e7] text-[#526072]'
                  }`}
                >
                  {rooms.length}
                </span>
              </button>

              <button
                type="button"
                onClick={() => setStatusTab('not_applied')}
                data-testid="filter-tab-available-jobs"
                className={`relative flex items-center gap-2 rounded-xl px-3.5 py-1.5 text-xs font-bold transition duration-150 cursor-pointer ${
                  statusTab === 'not_applied'
                    ? 'bg-[#277254] text-white'
                    : 'bg-white text-[#526072] border border-[#d9dbd1] hover:bg-[#eef5f1]'
                }`}
              >
                <span>Available to Apply</span>
                <span
                  className={`rounded-full px-1.5 py-0.2 text-[10px] ${
                    statusTab === 'not_applied' ? 'bg-white text-[#277254]' : 'bg-[#e2f0e9] text-[#277254]'
                  }`}
                >
                  {metrics.available}
                </span>
              </button>

              <button
                type="button"
                onClick={() => setStatusTab('applied')}
                data-testid="filter-tab-applied-jobs"
                className={`relative flex items-center gap-2 rounded-xl px-3.5 py-1.5 text-xs font-bold transition duration-150 cursor-pointer ${
                  statusTab === 'applied'
                    ? 'bg-[#3a6384] text-white'
                    : 'bg-white text-[#526072] border border-[#d9dbd1] hover:bg-[#e4edf5]'
                }`}
              >
                <CheckCircle2 size={13} />
                <span>Applied</span>
                <span
                  className={`rounded-full px-1.5 py-0.2 text-[10px] ${
                    statusTab === 'applied' ? 'bg-white text-[#3a6384]' : 'bg-[#e4edf5] text-[#3a6384]'
                  }`}
                >
                  {metrics.applied}
                </span>
              </button>
            </div>

            {filteredRooms.length > 0 && (
              <div className="text-xs text-[#7b8490]" data-testid="job-board-counter">
                Showing{' '}
                <span className="font-bold text-[#253142]">
                  {(currentPage - 1) * pageSize + 1}–{Math.min(currentPage * pageSize, filteredRooms.length)}
                </span>{' '}
                of <span className="font-bold text-[#253142]">{filteredRooms.length}</span> positions
              </div>
            )}
          </div>
        </div>

        {/* Main Jobs Listing Content */}
        {loading ? (
          <div className="mt-8 flex h-64 items-center justify-center rounded-2xl border border-[#d9dbd1] bg-white">
            <div className="flex items-center gap-2 text-sm text-[#7b8490]">
              <Loader2 size={18} className="animate-spin text-[#277254]" />
              Loading available job rooms...
            </div>
          </div>
        ) : filteredRooms.length === 0 ? (
          <div
            className="mt-8 flex flex-col items-center justify-center rounded-2xl border border-dashed border-[#c8cac0] bg-white p-12 text-center"
            data-testid="empty-job-board-state"
          >
            <div className="grid h-14 w-14 place-items-center rounded-2xl bg-[#eef0e7] text-[#526072] mb-4">
              <Briefcase size={28} />
            </div>
            <h3 className="text-base font-bold text-[#253142]">No matching job rooms</h3>
            <p className="mt-1 max-w-md text-xs text-[#7b8490]">
              {searchQuery || expFilter !== 'ALL' || statusTab !== 'all'
                ? 'No open roles match your current search and filter settings. Try adjusting your query or resetting filters.'
                : 'There are currently no active recruitment openings available. Check back soon for new opportunities.'}
            </p>
            {(searchQuery || expFilter !== 'ALL' || statusTab !== 'all') && (
              <button
                type="button"
                onClick={() => {
                  setSearchQuery('');
                  setExpFilter('ALL');
                  setStatusTab('all');
                }}
                className="mt-5 inline-flex items-center gap-2 rounded-xl bg-[#253142] px-4 py-2.5 text-xs font-bold text-white hover:bg-[#33435a] transition cursor-pointer"
              >
                Reset All Filters
              </button>
            )}
          </div>
        ) : (
          <>
            <motion.div
              layout
              transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
              className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
              data-testid="job-board-grid"
            >
              {paginatedRooms.map((room, idx) => {
                const isApplied = room.has_applied || room.is_applied;
                const isSaved = savedRoomIds.includes(room.id);
                const skillList =
                  room.skill_names && room.skill_names.length > 0
                    ? room.skill_names
                    : (room.skills_required as string[]).map((s) => (typeof s === 'string' ? s : (s as any)?.name || 'Skill'));
                
                // Match score simulated or real
                const matchScore = (room as any).match_score || 72 + ((room.id * 7) % 24);

                return (
                  <motion.div
                    key={room.id}
                    layout="position"
                    initial={prefersReduced ? { opacity: 0 } : { opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{
                      duration: 0.35,
                      delay: prefersReduced ? 0 : idx * 0.05,
                      ease: [0.22, 1, 0.36, 1],
                    }}
                    whileHover={prefersReduced ? undefined : { y: -2 }}
                    onClick={(e) => handleOpenRoomModal(room, e)}
                    data-testid={`job-board-card-${room.id}`}
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        handleOpenRoomModal(room);
                      }
                    }}
                    className="group relative flex flex-col justify-between overflow-hidden rounded-2xl border border-[#d9dbd1] bg-white shadow-xs transition-shadow duration-150 hover:shadow-md hover:border-[#b8bab0] cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#277254]"
                  >
                    {/* Card Header */}
                    <div className="border-b border-[#eceee7] bg-[#faf9f5] p-5">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5 text-xs font-semibold text-[#526072] truncate">
                            <Building2 size={13} className="shrink-0 text-[#7b8490]" />
                            <span data-testid={`job-board-company-${room.id}`} className="truncate">
                              {room.company_name}
                            </span>
                            {room.department && (
                              <span className="text-[#9ca3af] truncate">• {room.department}</span>
                            )}
                          </div>
                          <h3
                            data-testid={`job-board-title-${room.id}`}
                            className="mt-1.5 text-base font-bold text-[#253142] leading-snug line-clamp-2 group-hover:text-[#277254] transition-colors"
                          >
                            {room.title}
                          </h3>
                        </div>

                        {/* Save Heart Button */}
                        <motion.button
                          type="button"
                          onClick={(e) => toggleSaveRoom(room.id, e)}
                          whileTap={prefersReduced ? undefined : { scale: 1.25 }}
                          aria-label={isSaved ? 'Unsave job' : 'Save job'}
                          className={`grid h-8 w-8 place-items-center rounded-xl border transition-colors shrink-0 ${
                            isSaved
                              ? 'border-[#f5c84b] bg-[#fef9eb] text-[#e8b93c]'
                              : 'border-[#d9dbd1] bg-white text-[#8d9aab] hover:text-[#253142] hover:border-[#8d9aab]'
                          }`}
                        >
                          <Heart
                            size={15}
                            fill={isSaved ? '#f5c84b' : 'none'}
                            className="transition-transform duration-120"
                          />
                        </motion.button>
                      </div>

                      {/* Level, Category, and Match Gauge */}
                      <div className="mt-3 flex items-center justify-between gap-2">
                        <div className="flex flex-wrap items-center gap-1.5">
                          <span
                            data-testid={`job-board-role-level-${room.id}`}
                            className="rounded-lg border border-[#d9dbd1] bg-white px-2 py-0.5 text-[10px] font-bold text-[#253142]"
                          >
                            {formatLevel(room.experience_level, room.experience_level_display)}
                          </span>
                          {room.role_category && (
                            <span className="rounded-lg border border-[#e4edf5] bg-[#f0f6fb] px-2 py-0.5 text-[10px] font-bold text-[#3a6384]">
                              {room.role_category}
                            </span>
                          )}
                        </div>

                        {/* Match Progress Ring */}
                        <div className="flex items-center gap-1.5 shrink-0 bg-white border border-[#dedfd6] rounded-xl px-2 py-1 shadow-2xs">
                          <ProgressRing
                            value={matchScore}
                            max={100}
                            size={24}
                            strokeWidth={2.5}
                            color={matchScore >= 80 ? '#277254' : '#f5c84b'}
                            bgColor="#e5e3d8"
                            showLabel={false}
                          />
                          <span className="text-[11px] font-bold text-[#253142]">
                            <AnimatedNumber value={matchScore} suffix="%" />
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Card Body */}
                    <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
                      <p className="text-xs text-[#526072] leading-relaxed line-clamp-3">
                        {room.description || room.requirements_text || 'No job description provided.'}
                      </p>

                      {skillList.length > 0 && (
                        <div>
                          <div className="text-[10px] font-bold uppercase tracking-wider text-[#7b8490] mb-1.5">
                            Required Skills
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {skillList.slice(0, 4).map((skill, sIdx) => (
                              <span
                                key={sIdx}
                                className="rounded-md bg-[#eef0e7] px-2 py-0.5 text-[11px] font-medium text-[#253142]"
                              >
                                {skill}
                              </span>
                            ))}
                            {skillList.length > 4 && (
                              <span className="rounded-md bg-[#faf9f5] border border-[#d9dbd1] px-1.5 py-0.5 text-[10px] text-[#7b8490]">
                                +{skillList.length - 4} more
                              </span>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Evaluation Formula & Deadline */}
                      <div className="rounded-xl border border-[#dedfd6] bg-[#faf9f5] p-3 text-[11px] space-y-1.5">
                        <div
                          data-testid={`job-board-weights-${room.id}`}
                          className="flex items-center justify-between text-[#526072]"
                        >
                          <span className="flex items-center gap-1.5 font-bold text-[#253142]">
                            <Sliders size={12} className="text-[#277254]" /> Evaluation Split:
                          </span>
                          <span>{room.cv_weight}% CV • {room.video_weight}% Video</span>
                        </div>

                        <div
                          data-testid={`job-board-deadline-${room.id}`}
                          className="flex items-center justify-between text-[#7b8490]"
                        >
                          <span className="flex items-center gap-1.5">
                            <Calendar size={12} /> Deadline:
                          </span>
                          <span className="font-medium text-[#253142]">
                            {formatDate(room.link_expires_at || room.deadline)}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Card Footer Actions */}
                    <div className="flex items-center justify-between border-t border-[#dedfd6] bg-[#faf9f5] px-5 py-3">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenRoomModal(room, e);
                        }}
                        data-testid={`button-view-room-${room.id}`}
                        className="inline-flex items-center gap-1 text-xs font-bold text-[#526072] hover:text-[#253142] transition cursor-pointer"
                      >
                        <Eye size={13} /> View Specs
                      </button>

                      {isApplied ? (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setLocation('/student/applications');
                          }}
                          data-testid={`button-track-app-${room.id}`}
                          className="inline-flex items-center gap-1.5 rounded-xl border border-[#c5d8ce] bg-[#f8fbf9] px-3.5 py-2 text-xs font-bold text-[#277254] hover:bg-[#e2f0e9] transition cursor-pointer active:scale-[0.98]"
                        >
                          Track Application &rarr;
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleApplyClick(room);
                          }}
                          data-testid={`button-apply-room-${room.id}`}
                          className="inline-flex items-center gap-1.5 rounded-xl bg-[#253142] px-4 py-2 text-xs font-bold text-white hover:bg-[#33435a] transition shadow-xs cursor-pointer active:scale-[0.98]"
                        >
                          <Briefcase size={13} /> Apply Now
                        </button>
                      )}
                    </div>
                  </motion.div>
                );
              })}
            </motion.div>

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="mt-8 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-[#dedfd6] pt-6">
                <div className="text-xs text-[#7b8490]">
                  Page <span className="font-bold text-[#253142]">{currentPage}</span> of{' '}
                  <span className="font-bold text-[#253142]">{totalPages}</span>
                </div>

                <div className="flex items-center gap-1.5" data-testid="job-board-pagination">
                  <button
                    type="button"
                    onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    data-testid="button-prev-page"
                    className="inline-flex items-center gap-1 rounded-xl border border-[#d9dbd1] bg-white px-3 py-1.5 text-xs font-bold text-[#253142] hover:bg-[#f8f7f2] disabled:opacity-40 disabled:cursor-not-allowed transition cursor-pointer"
                  >
                    <ChevronLeft size={14} /> Previous
                  </button>

                  {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
                    <button
                      key={p}
                      type="button"
                      onClick={() => setCurrentPage(p)}
                      data-testid={`button-page-${p}`}
                      className={`h-8 w-8 rounded-xl text-xs font-bold transition cursor-pointer ${
                        currentPage === p
                          ? 'bg-[#277254] text-white shadow-xs'
                          : 'border border-[#d9dbd1] bg-white text-[#526072] hover:bg-[#f8f7f2]'
                      }`}
                    >
                      {p}
                    </button>
                  ))}

                  <button
                    type="button"
                    onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                    data-testid="button-next-page"
                    className="inline-flex items-center gap-1 rounded-xl border border-[#d9dbd1] bg-white px-3 py-1.5 text-xs font-bold text-[#253142] hover:bg-[#f8f7f2] disabled:opacity-40 disabled:cursor-not-allowed transition cursor-pointer"
                  >
                    Next <ChevronRight size={14} />
                  </button>
                </div>
              </div>
            )}
          </>
        )}

        {/* Right-Side Detail Drawer (350ms slide from right, focus trap, Esc to close) */}
        <Drawer
          isOpen={!!selectedRoomModal}
          onClose={handleCloseRoomModal}
          title={selectedRoomModal?.title || 'Job Specifications'}
          description={selectedRoomModal ? `${selectedRoomModal.company_name} • ${selectedRoomModal.department || 'General'}` : ''}
          width="max-w-xl"
          side="right"
        >
          {selectedRoomModal && (
            <div data-testid="modal-job-room-detail" className="space-y-6">
              {modalLoading && (
                <div className="flex items-center justify-center gap-2 rounded-xl bg-[#f8fbf9] p-3 text-xs text-[#277254]">
                  <Loader2 size={14} className="animate-spin" /> Synchronizing room specifications...
                </div>
              )}

              {/* Status and Seniority Badges */}
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-lg border border-[#d9dbd1] bg-[#faf9f5] px-2.5 py-1 text-xs font-bold text-[#253142]">
                  {formatLevel(selectedRoomModal.experience_level, selectedRoomModal.experience_level_display)}
                </span>
                {selectedRoomModal.role_category && (
                  <span className="rounded-lg border border-[#e4edf5] bg-[#f0f6fb] px-2.5 py-1 text-xs font-bold text-[#3a6384]">
                    {selectedRoomModal.role_category}
                  </span>
                )}
                {(selectedRoomModal.has_applied || selectedRoomModal.is_applied) ? (
                  <span className="inline-flex items-center gap-1 rounded-lg bg-[#e2f0e9] px-2.5 py-1 text-xs font-bold text-[#277254]">
                    <CheckCircle2 size={13} /> You Have Applied
                  </span>
                ) : (
                  <span className="rounded-lg bg-[#fff4db] px-2.5 py-1 text-xs font-bold text-[#966b0a]">
                    Open for Submissions
                  </span>
                )}
              </div>

              {/* Candidate Match Breakdown (Matched skills in green, Missing in gray) */}
              <div className="rounded-2xl border border-[#d9dbd1] bg-white p-4 shadow-xs">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#253142]">
                    <Sparkles size={14} className="text-[#277254]" /> Match Breakdown
                  </div>
                  <span className="text-xs font-bold text-[#277254]">
                    {drawerSkills.matched.length} of {drawerSkills.matched.length + drawerSkills.missing.length} requirements matched
                  </span>
                </div>

                <div className="space-y-3">
                  {drawerSkills.matched.length > 0 && (
                    <div>
                      <div className="text-[11px] font-bold text-[#277254] mb-1.5 flex items-center gap-1">
                        <Check size={12} strokeWidth={3} /> Matched Skills
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {drawerSkills.matched.map((skill, idx) => (
                          <span
                            key={idx}
                            className="rounded-lg bg-[#eef5f1] border border-[#c0dcd0] px-2.5 py-1 text-xs font-bold text-[#277254]"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {drawerSkills.missing.length > 0 && (
                    <div>
                      <div className="text-[11px] font-bold text-[#7b8490] mb-1.5">
                        Missing Skills / Skills to Highlight
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {drawerSkills.missing.map((skill, idx) => (
                          <span
                            key={idx}
                            className="rounded-lg bg-[#f3f1ea] border border-[#d9dbd1] px-2.5 py-1 text-xs font-medium text-[#687382]"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Evaluation Weights Architecture */}
              <div className="rounded-2xl border border-[#dedfd6] bg-[#faf9f5] p-4">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#7b8490]">
                  <Sliders size={14} className="text-[#277254]" /> Multi-Modal Evaluation Framework
                </div>
                <div className="mt-3 grid grid-cols-2 gap-3 text-xs">
                  <div className="rounded-xl border border-[#dedfd6] bg-white p-3">
                    <div className="flex items-center gap-1.5 font-bold text-[#253142]">
                      <FileText size={13} className="text-[#277254]" /> CV Match Weight
                    </div>
                    <div className="mt-1 text-lg font-black text-[#277254]">{selectedRoomModal.cv_weight}%</div>
                    <div className="text-[10px] text-[#7b8490]">Scored against required skills and experience</div>
                  </div>
                  <div className="rounded-xl border border-[#dedfd6] bg-white p-3">
                    <div className="flex items-center gap-1.5 font-bold text-[#253142]">
                      <Video size={13} className="text-[#3a6384]" /> Video Pitch Weight
                    </div>
                    <div className="mt-1 text-lg font-black text-[#3a6384]">{selectedRoomModal.video_weight}%</div>
                    <div className="text-[10px] text-[#7b8490]">Scored on delivery, speech clarity, and body language</div>
                  </div>
                </div>
              </div>

              {/* Job Description */}
              {selectedRoomModal.description && (
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-[#7b8490] mb-2">
                    Role Description
                  </h4>
                  <p className="text-xs text-[#526072] leading-relaxed whitespace-pre-line">
                    {selectedRoomModal.description}
                  </p>
                </div>
              )}

              {/* Requirements Text */}
              {selectedRoomModal.requirements_text && (
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-[#7b8490] mb-2">
                    Candidate Requirements
                  </h4>
                  <p className="text-xs text-[#526072] leading-relaxed whitespace-pre-line">
                    {selectedRoomModal.requirements_text}
                  </p>
                </div>
              )}

              {/* Submission Deadline */}
              <div className="rounded-xl border border-[#dedfd6] bg-[#fbfbfa] p-3 text-xs flex items-center justify-between">
                <span className="text-[#7b8490] flex items-center gap-1.5">
                  <Calendar size={14} /> Submission Deadline:
                </span>
                <span className="font-bold text-[#253142]">
                  {formatDate(selectedRoomModal.link_expires_at || selectedRoomModal.deadline)}
                </span>
              </div>

              {/* Drawer Actions - Solid Yellow Primary Button */}
              <div className="pt-4 border-t border-[#dedfd6] flex items-center justify-between gap-3">
                <button
                  type="button"
                  onClick={handleCloseRoomModal}
                  data-testid="button-close-job-modal"
                  className="rounded-xl border border-[#d9dbd1] bg-white px-4 py-2.5 text-xs font-bold text-[#253142] hover:bg-[#f8f7f2] transition cursor-pointer"
                >
                  Close
                </button>

                {(selectedRoomModal.has_applied || selectedRoomModal.is_applied) ? (
                  <button
                    type="button"
                    onClick={() => {
                      handleCloseRoomModal();
                      setLocation('/student/applications');
                    }}
                    data-testid="button-modal-track"
                    className="inline-flex items-center gap-2 rounded-xl bg-[#253142] px-5 py-2.5 text-xs font-bold text-white hover:bg-[#33435a] transition cursor-pointer active:scale-[0.98]"
                  >
                    <Briefcase size={14} /> View My Application Dossier &rarr;
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => {
                      handleCloseRoomModal();
                      handleApplyClick(selectedRoomModal);
                    }}
                    data-testid="button-modal-apply"
                    className="inline-flex items-center gap-2 rounded-xl bg-[#f5c84b] px-6 py-2.5 text-xs font-bold text-[#253142] hover:bg-[#e8b93c] transition shadow-xs cursor-pointer active:scale-[0.98]"
                  >
                    <Briefcase size={14} /> Apply to this Opening &rarr;
                  </button>
                )}
              </div>
            </div>
          )}
        </Drawer>
      </PageTransition>
    </AppShell>
  );
}
