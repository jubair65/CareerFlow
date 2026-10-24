import { useState, useEffect, useMemo } from 'react';
import {
  Building2,
  Plus,
  Search,
  Filter,
  MoreVertical,
  Edit,
  Power,
  Globe,
  Mail,
  Phone,
  FileText,
  FolderOpen,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  X,
  ExternalLink,
  Users,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import { PageHeading, StatCard, Badge, type Notify } from '../components/dashboard/DashboardShared';
import {
  apiGetAgencyClients,
  apiCreateAgencyClient,
  apiUpdateAgencyClient,
  apiToggleClientActive,
  apiGetAgencyClientStats,
  type ClientCompany,
  type ClientCompanyCreatePayload,
  type AgencyClientStats,
} from '../api/recruitment';

const INDUSTRY_OPTIONS = [
  'All Industries',
  'Technology & Software',
  'Finance & Banking',
  'Healthcare & Biotech',
  'E-Commerce & Retail',
  'Consulting & Services',
  'Manufacturing & Logistics',
  'Education & EdTech',
  'Media & Entertainment',
  'Other',
];

interface FormErrors {
  name?: string;
  industry?: string;
  contact_person?: string;
  contact_email?: string;
  website?: string;
  general?: string;
}

export function AgencyClientManagementPage({ notify }: { notify: Notify }) {
  const [clients, setClients] = useState<ClientCompany[]>([]);
  const [stats, setStats] = useState<AgencyClientStats>({
    total_clients: 0,
    active_clients: 0,
    deactivated_clients: 0,
    associated_rooms: 0,
  });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIndustry, setSelectedIndustry] = useState('All Industries');
  const [selectedStatus, setSelectedStatus] = useState<'all' | 'active' | 'deactivated'>('all');

  // Modal States
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [editingClient, setEditingClient] = useState<ClientCompany | null>(null);
  const [toggleConfirmClient, setToggleConfirmClient] = useState<ClientCompany | null>(null);

  // Form State
  const [formData, setFormData] = useState<ClientCompanyCreatePayload>({
    name: '',
    industry: 'Technology & Software',
    contact_person: '',
    contact_email: '',
    phone: '',
    website: '',
    notes: '',
  });
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [submitting, setSubmitting] = useState(false);

  // Fetch Clients and Stats
  const fetchData = async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    else setRefreshing(true);

    try {
      const [clientsData, statsData] = await Promise.all([
        apiGetAgencyClients(),
        apiGetAgencyClientStats(),
      ]);
      setClients(clientsData);
      setStats(statsData);
    } catch (err: any) {
      notify(
        err?.response?.data?.detail || 'Failed to load agency client companies.',
        'error'
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Filtered Client List
  const filteredClients = useMemo(() => {
    return clients.filter((client) => {
      // Search matching name, industry, contact person, email
      const q = searchQuery.toLowerCase().trim();
      const matchesSearch =
        !q ||
        client.name.toLowerCase().includes(q) ||
        client.industry.toLowerCase().includes(q) ||
        client.contact_person.toLowerCase().includes(q) ||
        client.contact_email.toLowerCase().includes(q);

      // Industry matching
      const matchesIndustry =
        selectedIndustry === 'All Industries' ||
        client.industry.toLowerCase() === selectedIndustry.toLowerCase();

      // Status matching
      const matchesStatus =
        selectedStatus === 'all' ||
        (selectedStatus === 'active' && client.is_active) ||
        (selectedStatus === 'deactivated' && !client.is_active);

      return matchesSearch && matchesIndustry && matchesStatus;
    });
  }, [clients, searchQuery, selectedIndustry, selectedStatus]);

  // Handle Open Create Modal
  const handleOpenAddModal = () => {
    setFormData({
      name: '',
      industry: 'Technology & Software',
      contact_person: '',
      contact_email: '',
      phone: '',
      website: '',
      notes: '',
    });
    setFormErrors({});
    setIsAddModalOpen(true);
  };

  // Handle Open Edit Modal
  const handleOpenEditModal = (client: ClientCompany) => {
    setEditingClient(client);
    setFormData({
      name: client.name,
      industry: client.industry,
      contact_person: client.contact_person,
      contact_email: client.contact_email,
      phone: client.phone || '',
      website: client.website || '',
      notes: client.notes || '',
    });
    setFormErrors({});
  };

  // Validate Form
  const validateForm = (): boolean => {
    const errors: FormErrors = {};

    if (!formData.name.trim()) {
      errors.name = 'Company name is required.';
    } else if (formData.name.trim().length < 2) {
      errors.name = 'Company name must be at least 2 characters.';
    }

    if (!formData.industry.trim()) {
      errors.industry = 'Industry selection is required.';
    }

    if (!formData.contact_person.trim()) {
      errors.contact_person = 'Contact person name is required.';
    }

    if (!formData.contact_email.trim()) {
      errors.contact_email = 'Contact email is required.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.contact_email.trim())) {
      errors.contact_email = 'Please provide a valid email address.';
    }

    if (formData.website && formData.website.trim()) {
      const url = formData.website.trim();
      if (!url.startsWith('http://') && !url.startsWith('https://')) {
        errors.website = 'Website URL must begin with http:// or https://';
      }
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Handle Submit Form (Create or Edit)
  const handleSubmitForm = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setSubmitting(true);
    setFormErrors({});

    try {
      if (editingClient) {
        // Edit Mode
        const updated = await apiUpdateAgencyClient(editingClient.id, formData);
        setClients((prev) =>
          prev.map((c) => (c.id === updated.id ? updated : c))
        );
        notify(`Client company "${updated.name}" updated successfully.`, 'success');
        setEditingClient(null);
      } else {
        // Create Mode
        const created = await apiCreateAgencyClient(formData);
        setClients((prev) => [created, ...prev]);
        setStats((prev) => ({
          ...prev,
          total_clients: prev.total_clients + 1,
          active_clients: prev.active_clients + 1,
        }));
        notify(`Client company "${created.name}" added to agency portfolio.`, 'success');
        setIsAddModalOpen(false);
      }
    } catch (err: any) {
      const backendErrors = err?.response?.data;
      if (typeof backendErrors === 'object' && backendErrors !== null) {
        const formatted: FormErrors = {};
        if (backendErrors.name) {
          formatted.name = Array.isArray(backendErrors.name)
            ? backendErrors.name[0]
            : backendErrors.name;
        }
        if (backendErrors.contact_email) {
          formatted.contact_email = Array.isArray(backendErrors.contact_email)
            ? backendErrors.contact_email[0]
            : backendErrors.contact_email;
        }
        if (backendErrors.detail) {
          formatted.general = backendErrors.detail;
        }
        setFormErrors(formatted);
      } else {
        setFormErrors({ general: 'An unexpected error occurred while saving.' });
      }
    } finally {
      setSubmitting(false);
    }
  };

  // Handle Toggle Active Confirmation
  const handleConfirmToggleActive = async () => {
    if (!toggleConfirmClient) return;

    try {
      const res = await apiToggleClientActive(toggleConfirmClient.id);
      setClients((prev) =>
        prev.map((c) => (c.id === toggleConfirmClient.id ? res.client : c))
      );
      setStats((prev) => {
        const delta = res.is_active ? 1 : -1;
        return {
          ...prev,
          active_clients: prev.active_clients + delta,
          deactivated_clients: prev.deactivated_clients - delta,
        };
      });
      notify(res.message, 'success');
    } catch (err: any) {
      notify(
        err?.response?.data?.detail || 'Failed to change client status.',
        'error'
      );
    } finally {
      setToggleConfirmClient(null);
    }
  };

  return (
    <AppShell role="agency" notify={notify}>
      <PageHeading
        eyebrow="Recruitment Agency Portfolio"
        title="Client Companies"
        description="Manage multi-tenant client organizations, contact representatives, and active recruitment openings."
        action={
          <div className="flex items-center gap-2.5">
            <button
              type="button"
              onClick={() => fetchData(true)}
              disabled={refreshing}
              className="inline-flex items-center gap-1.5 rounded-xl border border-[#d9dbd1] bg-white px-3.5 py-2.5 text-xs font-bold text-[#253142] hover:bg-[#fbfaf5] transition shadow-sm disabled:opacity-50"
              title="Refresh Client List"
            >
              <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </button>
            <button
              type="button"
              onClick={handleOpenAddModal}
              data-testid="button-add-client"
              className="inline-flex items-center gap-2 rounded-xl bg-[#277254] px-4 py-2.5 text-sm font-bold text-white hover:bg-[#1f5b43] transition shadow-sm"
            >
              <Plus size={16} /> Add client company
            </button>
          </div>
        }
      />

      {/* KPI Metric Cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div data-testid="stat-total-clients">
          <StatCard
            label="Total clients"
            value={String(stats.total_clients)}
            detail="Registered client portfolio"
            icon={Building2}
            accent="yellow"
          />
        </div>
        <div data-testid="stat-active-clients">
          <StatCard
            label="Active clients"
            value={String(stats.active_clients)}
            detail="Eligible for new room creation"
            icon={CheckCircle2}
            accent="green"
          />
        </div>
        <div data-testid="stat-deactivated-clients">
          <StatCard
            label="Deactivated clients"
            value={String(stats.deactivated_clients)}
            detail="Archived client accounts"
            icon={XCircle}
            accent="coral"
          />
        </div>
        <div data-testid="stat-associated-rooms">
          <StatCard
            label="Associated rooms"
            value={String(stats.associated_rooms)}
            detail="Recruitment rooms linked"
            icon={FolderOpen}
            accent="blue"
          />
        </div>
      </div>

      {/* Search, Filter & Action Bar */}
      <div className="mt-6 rounded-2xl border border-[#d9dbd1] bg-white p-4 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          {/* Search Box */}
          <div className="relative flex-1">
            <Search
              size={18}
              className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#7b8490]"
            />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by company name, contact person, or email..."
              data-testid="input-search-clients"
              className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] py-2.5 pl-10 pr-4 text-sm text-[#253142] placeholder-[#7b8490] focus:border-[#277254] focus:bg-white focus:outline-none"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-[#7b8490] hover:text-[#253142]"
              >
                Clear
              </button>
            )}
          </div>

          {/* Filters */}
          <div className="flex flex-wrap items-center gap-2.5">
            {/* Industry Filter */}
            <div className="flex items-center gap-1.5 text-xs text-[#526072]">
              <Filter size={14} className="text-[#7b8490]" />
              <select
                value={selectedIndustry}
                onChange={(e) => setSelectedIndustry(e.target.value)}
                data-testid="select-filter-industry"
                className="rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3 py-2 text-xs font-semibold text-[#253142] focus:border-[#277254] focus:outline-none"
              >
                {INDUY_OPTIONS_MAPPED(INDUSTRY_OPTIONS)}
              </select>
            </div>

            {/* Status Tabs */}
            <div
              className="flex rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] p-1 text-xs font-semibold"
              data-testid="select-filter-status"
            >
              <button
                type="button"
                onClick={() => setSelectedStatus('all')}
                className={`rounded-lg px-3 py-1 transition ${
                  selectedStatus === 'all'
                    ? 'bg-white text-[#253142] shadow-sm font-bold'
                    : 'text-[#7b8490] hover:text-[#253142]'
                }`}
              >
                All ({clients.length})
              </button>
              <button
                type="button"
                onClick={() => setSelectedStatus('active')}
                className={`rounded-lg px-3 py-1 transition ${
                  selectedStatus === 'active'
                    ? 'bg-white text-[#277254] shadow-sm font-bold'
                    : 'text-[#7b8490] hover:text-[#277254]'
                }`}
              >
                Active ({clients.filter((c) => c.is_active).length})
              </button>
              <button
                type="button"
                onClick={() => setSelectedStatus('deactivated')}
                className={`rounded-lg px-3 py-1 transition ${
                  selectedStatus === 'deactivated'
                    ? 'bg-white text-[#a33d35] shadow-sm font-bold'
                    : 'text-[#7b8490] hover:text-[#a33d35]'
                }`}
              >
                Deactivated ({clients.filter((c) => !c.is_active).length})
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area: Client Cards & Table */}
      <div className="mt-5">
        {loading ? (
          <div className="flex flex-col items-center justify-center rounded-2xl border border-[#d9dbd1] bg-white py-16 text-center shadow-sm">
            <div className="h-9 w-9 animate-spin rounded-full border-4 border-[#277254] border-t-transparent" />
            <p className="mt-4 text-sm font-semibold text-[#526072]">
              Loading client companies...
            </p>
          </div>
        ) : filteredClients.length === 0 ? (
          <div className="rounded-2xl border border-[#d9dbd1] bg-white p-12 text-center shadow-sm">
            <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-[#e4edf5] text-[#3a6384]">
              <Building2 size={28} />
            </div>
            <h3 className="mt-4 font-bold text-[#253142] text-lg">
              {clients.length === 0
                ? 'No client companies yet'
                : 'No client companies match your search'}
            </h3>
            <p className="mx-auto mt-2 max-w-md text-sm text-[#7b8490]">
              {clients.length === 0
                ? 'Get started by registering your client organizations to create custom recruitment rooms, manage pipelines, and forward shortlisted candidates.'
                : 'Try adjusting your search query, selecting a different industry, or clearing status filters.'}
            </p>
            <div className="mt-6 flex justify-center gap-3">
              {clients.length === 0 ? (
                <button
                  type="button"
                  onClick={handleOpenAddModal}
                  className="inline-flex items-center gap-2 rounded-xl bg-[#277254] px-4 py-2.5 text-sm font-bold text-white hover:bg-[#1f5b43] transition shadow-sm"
                >
                  <Plus size={16} /> Register your first client
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => {
                    setSearchQuery('');
                    setSelectedIndustry('All Industries');
                    setSelectedStatus('all');
                  }}
                  className="rounded-xl border border-[#d9dbd1] bg-white px-4 py-2 text-sm font-semibold text-[#253142] hover:bg-[#fbfaf5]"
                >
                  Reset all filters
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {filteredClients.map((client) => (
              <div
                key={client.id}
                data-testid={`client-card-${client.id}`}
                className={`flex flex-col justify-between rounded-2xl border bg-white p-5 shadow-sm transition hover:shadow-md ${
                  client.is_active
                    ? 'border-[#d9dbd1]'
                    : 'border-[#ebd9d7] bg-[#fdfbfb]'
                }`}
              >
                <div>
                  {/* Card Header */}
                  <div className="flex items-start justify-between gap-3 border-b border-[#eef0e7] pb-3">
                    <div className="flex items-center gap-3">
                      <div
                        className={`grid h-11 w-11 shrink-0 place-items-center rounded-xl font-bold text-base ${
                          client.is_active
                            ? 'bg-[#e4edf5] text-[#2a557a]'
                            : 'bg-[#f7e5e1] text-[#a33d35]'
                        }`}
                      >
                        <Building2 size={22} />
                      </div>
                      <div>
                        <h3 className="font-bold text-[#253142] text-base leading-tight">
                          {client.name}
                        </h3>
                        <span className="mt-1 inline-block text-xs font-semibold text-[#7b8490]">
                          {client.industry}
                        </span>
                      </div>
                    </div>
                    <div>
                      {client.is_active ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-[#e2f0e9] px-2.5 py-0.5 text-[11px] font-bold text-[#277254]">
                          <span className="h-1.5 w-1.5 rounded-full bg-[#277254]" />
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded-full bg-[#f7e5e1] px-2.5 py-0.5 text-[11px] font-bold text-[#a33d35]">
                          <span className="h-1.5 w-1.5 rounded-full bg-[#a33d35]" />
                          Deactivated
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Contact Info */}
                  <div className="mt-4 space-y-2 text-xs text-[#526072]">
                    <div className="flex items-center gap-2">
                      <Users size={14} className="text-[#7b8490] shrink-0" />
                      <span className="font-medium text-[#253142]">
                        {client.contact_person}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <Mail size={14} className="text-[#7b8490] shrink-0" />
                      <a
                        href={`mailto:${client.contact_email}`}
                        className="truncate text-[#277254] hover:underline"
                        title={client.contact_email}
                      >
                        {client.contact_email}
                      </a>
                    </div>

                    {client.phone && (
                      <div className="flex items-center gap-2">
                        <Phone size={14} className="text-[#7b8490] shrink-0" />
                        <span>{client.phone}</span>
                      </div>
                    )}

                    {client.website && (
                      <div className="flex items-center gap-2">
                        <Globe size={14} className="text-[#7b8490] shrink-0" />
                        <a
                          href={client.website}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 truncate text-[#3a6384] hover:underline"
                        >
                          {client.website.replace(/^https?:\/\//, '')}
                          <ExternalLink size={10} />
                        </a>
                      </div>
                    )}

                    {client.notes && (
                      <div className="mt-3 rounded-xl bg-[#fbfaf5] p-2.5 text-[11px] text-[#687382] line-clamp-2">
                        {client.notes}
                      </div>
                    )}
                  </div>
                </div>

                {/* Card Footer & Action Buttons */}
                <div className="mt-5 pt-3 border-t border-[#eef0e7] flex items-center justify-between">
                  <div className="flex items-center gap-1.5 text-xs text-[#7b8490]">
                    <FolderOpen size={14} />
                    <span className="font-semibold text-[#253142]">
                      {client.rooms_count || 0}
                    </span>{' '}
                    room{client.rooms_count === 1 ? '' : 's'}
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => handleOpenEditModal(client)}
                      data-testid={`button-edit-client-${client.id}`}
                      className="inline-flex items-center gap-1 rounded-lg border border-[#d9dbd1] bg-white px-2.5 py-1.5 text-xs font-semibold text-[#253142] hover:bg-[#fbfaf5] transition"
                    >
                      <Edit size={12} /> Edit
                    </button>

                    <button
                      type="button"
                      onClick={() => setToggleConfirmClient(client)}
                      data-testid={`button-toggle-client-${client.id}`}
                      className={`inline-flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-semibold transition ${
                        client.is_active
                          ? 'border border-[#ebd9d7] bg-[#fdf6f5] text-[#a33d35] hover:bg-[#faeae7]'
                          : 'border border-[#c6e5d3] bg-[#f0f8f4] text-[#277254] hover:bg-[#e2f2e9]'
                      }`}
                      title={client.is_active ? 'Deactivate Client' : 'Reactivate Client'}
                    >
                      <Power size={12} />
                      {client.is_active ? 'Deactivate' : 'Reactivate'}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ==================================================================== */}
      {/* ADD / EDIT CLIENT COMPANY MODAL */}
      {/* ==================================================================== */}
      {(isAddModalOpen || editingClient) && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 overflow-y-auto"
          data-testid="modal-client-form"
        >
          <div className="relative w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl border border-[#d9dbd1] my-8">
            <button
              type="button"
              onClick={() => {
                setIsAddModalOpen(false);
                setEditingClient(null);
              }}
              data-testid="button-cancel-client"
              className="absolute right-5 top-5 text-[#7b8490] hover:text-[#253142]"
            >
              <X size={20} />
            </button>

            <div className="flex items-center gap-3 border-b border-[#eef0e7] pb-4">
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#e4edf5] text-[#2a557a]">
                <Building2 size={20} />
              </div>
              <div>
                <h3 className="font-bold text-[#253142] text-lg">
                  {editingClient ? 'Edit Client Company' : 'Add New Client Company'}
                </h3>
                <p className="text-xs text-[#7b8490]">
                  {editingClient
                    ? 'Update client details and primary contact representative.'
                    : 'Register a client organization to start managing recruitment on their behalf.'}
                </p>
              </div>
            </div>

            {formErrors.general && (
              <div className="mt-4 rounded-xl border border-[#ebd9d7] bg-[#fdf6f5] p-3 text-xs font-semibold text-[#a33d35] flex items-center gap-2">
                <AlertTriangle size={15} />
                {formErrors.general}
              </div>
            )}

            <form onSubmit={handleSubmitForm} noValidate className="mt-5 space-y-4">
              {/* Company Name */}
              <div>
                <label className="block text-xs font-bold text-[#253142] mb-1">
                  Company Name <span className="text-[#a33d35]">*</span>
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. Acme Corporation, TechNova Ltd."
                  data-testid="input-client-name"
                  className={`w-full rounded-xl border px-3.5 py-2.5 text-sm text-[#253142] placeholder-[#a6afbb] focus:outline-none ${
                    formErrors.name
                      ? 'border-[#a33d35] bg-[#fffbfb]'
                      : 'border-[#d9dbd1] bg-[#fbfaf5] focus:border-[#277254] focus:bg-white'
                  }`}
                />
                {formErrors.name && (
                  <p className="mt-1 text-xs text-[#a33d35] font-medium">
                    {formErrors.name}
                  </p>
                )}
              </div>

              {/* Industry */}
              <div>
                <label className="block text-xs font-bold text-[#253142] mb-1">
                  Industry Sector <span className="text-[#a33d35]">*</span>
                </label>
                <select
                  value={formData.industry}
                  onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                  data-testid="input-client-industry"
                  className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3.5 py-2.5 text-sm text-[#253142] focus:border-[#277254] focus:bg-white focus:outline-none"
                >
                  {INDUSTRY_OPTIONS.filter((i) => i !== 'All Industries').map((ind) => (
                    <option key={ind} value={ind}>
                      {ind}
                    </option>
                  ))}
                </select>
                {formErrors.industry && (
                  <p className="mt-1 text-xs text-[#a33d35] font-medium">
                    {formErrors.industry}
                  </p>
                )}
              </div>

              {/* Contact Person & Email */}
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-bold text-[#253142] mb-1">
                    Contact Person <span className="text-[#a33d35]">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.contact_person}
                    onChange={(e) =>
                      setFormData({ ...formData, contact_person: e.target.value })
                    }
                    placeholder="e.g. Alice Smith"
                    data-testid="input-client-contact-person"
                    className={`w-full rounded-xl border px-3.5 py-2.5 text-sm text-[#253142] placeholder-[#a6afbb] focus:outline-none ${
                      formErrors.contact_person
                        ? 'border-[#a33d35] bg-[#fffbfb]'
                        : 'border-[#d9dbd1] bg-[#fbfaf5] focus:border-[#277254] focus:bg-white'
                    }`}
                  />
                  {formErrors.contact_person && (
                    <p className="mt-1 text-xs text-[#a33d35] font-medium">
                      {formErrors.contact_person}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-bold text-[#253142] mb-1">
                    Contact Email <span className="text-[#a33d35]">*</span>
                  </label>
                  <input
                    type="email"
                    value={formData.contact_email}
                    onChange={(e) =>
                      setFormData({ ...formData, contact_email: e.target.value })
                    }
                    placeholder="e.g. hr@client.com"
                    data-testid="input-client-contact-email"
                    className={`w-full rounded-xl border px-3.5 py-2.5 text-sm text-[#253142] placeholder-[#a6afbb] focus:outline-none ${
                      formErrors.contact_email
                        ? 'border-[#a33d35] bg-[#fffbfb]'
                        : 'border-[#d9dbd1] bg-[#fbfaf5] focus:border-[#277254] focus:bg-white'
                    }`}
                  />
                  {formErrors.contact_email && (
                    <p className="mt-1 text-xs text-[#a33d35] font-medium">
                      {formErrors.contact_email}
                    </p>
                  )}
                </div>
              </div>

              {/* Phone & Website */}
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-bold text-[#253142] mb-1">
                    Phone Number (Optional)
                  </label>
                  <input
                    type="text"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    placeholder="+1 (555) 012-3456"
                    data-testid="input-client-phone"
                    className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3.5 py-2.5 text-sm text-[#253142] placeholder-[#a6afbb] focus:border-[#277254] focus:bg-white focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-[#253142] mb-1">
                    Website URL (Optional)
                  </label>
                  <input
                    type="url"
                    value={formData.website}
                    onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                    placeholder="https://company.example.com"
                    data-testid="input-client-website"
                    className={`w-full rounded-xl border px-3.5 py-2.5 text-sm text-[#253142] placeholder-[#a6afbb] focus:outline-none ${
                      formErrors.website
                        ? 'border-[#a33d35] bg-[#fffbfb]'
                        : 'border-[#d9dbd1] bg-[#fbfaf5] focus:border-[#277254] focus:bg-white'
                    }`}
                  />
                  {formErrors.website && (
                    <p className="mt-1 text-xs text-[#a33d35] font-medium">
                      {formErrors.website}
                    </p>
                  )}
                </div>
              </div>

              {/* Notes */}
              <div>
                <label className="block text-xs font-bold text-[#253142] mb-1">
                  Internal Notes (Optional)
                </label>
                <textarea
                  rows={3}
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="Key hiring requirements, SLAs, contract terms, or special preferences..."
                  data-testid="input-client-notes"
                  className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3.5 py-2.5 text-sm text-[#253142] placeholder-[#a6afbb] focus:border-[#277254] focus:bg-white focus:outline-none"
                />
              </div>

              {/* Action Buttons */}
              <div className="mt-6 flex items-center justify-end gap-3 pt-3 border-t border-[#eef0e7]">
                <button
                  type="button"
                  onClick={() => {
                    setIsAddModalOpen(false);
                    setEditingClient(null);
                  }}
                  className="rounded-xl border border-[#d9dbd1] bg-white px-4 py-2.5 text-sm font-semibold text-[#526072] hover:bg-[#fbfaf5] transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  data-testid="button-submit-client"
                  className="inline-flex items-center gap-2 rounded-xl bg-[#277254] px-5 py-2.5 text-sm font-bold text-white hover:bg-[#1f5b43] transition disabled:opacity-50 shadow-sm"
                >
                  {submitting ? 'Saving...' : editingClient ? 'Save Changes' : 'Create Client'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* DEACTIVATION / REACTIVATION CONFIRMATION MODAL */}
      {/* ==================================================================== */}
      {toggleConfirmClient && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
          data-testid="modal-confirm-toggle"
        >
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl border border-[#d9dbd1]">
            <div className="flex items-center gap-3 text-[#a33d35]">
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#f7e5e1]">
                <Power size={20} />
              </div>
              <h3 className="font-bold text-[#253142] text-lg">
                {toggleConfirmClient.is_active
                  ? 'Deactivate Client Company?'
                  : 'Reactivate Client Company?'}
              </h3>
            </div>

            <p className="mt-3 text-sm text-[#526072] leading-relaxed">
              {toggleConfirmClient.is_active ? (
                <>
                  Are you sure you want to deactivate{' '}
                  <strong className="text-[#253142]">
                    {toggleConfirmClient.name}
                  </strong>
                  ? Deactivating this company will hide it from new recruitment room
                  creation while preserving all past candidate applications, scores,
                  and audit histories intact.
                </>
              ) : (
                <>
                  Are you sure you want to reactivate{' '}
                  <strong className="text-[#253142]">
                    {toggleConfirmClient.name}
                  </strong>
                  ? This client will immediately become available again for opening new
                  recruitment rooms and candidate pipelines.
                </>
              )}
            </p>

            <div className="mt-6 flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => setToggleConfirmClient(null)}
                className="rounded-xl border border-[#d9dbd1] bg-white px-4 py-2.5 text-sm font-semibold text-[#526072] hover:bg-[#fbfaf5] transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmToggleActive}
                data-testid="button-confirm-toggle"
                className={`rounded-xl px-5 py-2.5 text-sm font-bold text-white transition shadow-sm ${
                  toggleConfirmClient.is_active
                    ? 'bg-[#a33d35] hover:bg-[#852f28]'
                    : 'bg-[#277254] hover:bg-[#1f5b43]'
                }`}
              >
                {toggleConfirmClient.is_active
                  ? 'Yes, Deactivate Client'
                  : 'Yes, Reactivate Client'}
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}

function INDUY_OPTIONS_MAPPED(opts: string[]) {
  return opts.map((opt) => (
    <option key={opt} value={opt}>
      {opt}
    </option>
  ));
}
