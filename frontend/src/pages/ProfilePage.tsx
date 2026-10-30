import { useState, useEffect, useRef } from 'react';
import { useLocation } from 'wouter';
import {
  UserRound,
  Mail,
  ShieldCheck,
  Building2,
  Calendar,
  KeyRound,
  LogOut,
  CheckCircle2,
  Lock,
  Phone,
  Linkedin,
  Github,
  Briefcase,
  FileText,
  Camera,
  Loader2,
  Save,
  RotateCcw,
  ExternalLink,
  AlertCircle,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import { PageHeading, type Notify } from '../components/dashboard/DashboardShared';
import {
  apiGetCandidateProfile,
  apiUpdateCandidateProfile,
  getStoredUser,
  storeUser,
  apiLogout,
} from '../api/auth';

export function ProfilePage({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [profile, setProfile] = useState<any>(null);

  // Editable Form State
  const [fullName, setFullName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [linkedinUrl, setLinkedinUrl] = useState('');
  const [githubUrl, setGithubUrl] = useState('');
  const [targetRole, setTargetRole] = useState('');
  const [bio, setBio] = useState('');
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);

  // Field-level validation errors
  const [errors, setErrors] = useState<Record<string, string>>({});

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const data = await apiGetCandidateProfile();
      setProfile(data);
      setFullName(data.full_name || '');
      setPhoneNumber(data.phone_number || '');
      setLinkedinUrl(data.linkedin_url || '');
      setGithubUrl(data.github_url || '');
      setTargetRole(data.target_role || '');
      setBio(data.bio || '');
      if (data.avatar_url) {
        setAvatarPreview(data.avatar_url);
      }
    } catch (err: any) {
      notify?.('Failed to load profile details.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const storedUser = getStoredUser() || {};
  const rawRole = profile?.role || storedUser?.role || 'STUDENT';
  const effectiveRole =
    rawRole === 'HR_MANAGER' || rawRole === 'hr'
      ? 'hr'
      : rawRole === 'AGENCY_ADMIN' || rawRole === 'agency'
      ? 'agency'
      : 'student';

  const email = profile?.email || storedUser?.email || 'user@example.com';
  const displayName = fullName || profile?.full_name || email.split('@')[0];
  const initials = displayName
    .split(' ')
    .filter(Boolean)
    .map((n: string) => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase() || 'U';

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        notify?.('Image size must be less than 5MB.', 'error');
        return;
      }
      setAvatarFile(file);
      const previewUrl = URL.createObjectURL(file);
      setAvatarPreview(previewUrl);
    }
  };

  const validate = () => {
    const errs: Record<string, string> = {};

    if (phoneNumber.trim()) {
      const digitsOnly = phoneNumber.replace(/\D/g, '');
      if (digitsOnly.length < 7 || digitsOnly.length > 15) {
        errs.phone_number = 'Enter a valid phone number with 7 to 15 digits.';
      }
    }

    if (linkedinUrl.trim()) {
      let url = linkedinUrl.trim().toLowerCase();
      if (!url.startsWith('http://') && !url.startsWith('https://')) {
        url = `https://${url}`;
      }
      try {
        const parsed = new URL(url);
        if (!parsed.hostname.includes('linkedin.com')) {
          errs.linkedin_url = 'Please provide a valid LinkedIn URL (e.g. https://linkedin.com/in/username).';
        }
      } catch {
        errs.linkedin_url = 'Please enter a valid URL.';
      }
    }

    if (githubUrl.trim()) {
      let url = githubUrl.trim().toLowerCase();
      if (!url.startsWith('http://') && !url.startsWith('https://')) {
        url = `https://${url}`;
      }
      try {
        const parsed = new URL(url);
        if (!parsed.hostname.includes('github.com')) {
          errs.github_url = 'Please provide a valid GitHub URL (e.g. https://github.com/username).';
        }
      } catch {
        errs.github_url = 'Please enter a valid URL.';
      }
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) {
      notify?.('Please correct the highlighted form errors.', 'error');
      return;
    }

    try {
      setSaving(true);
      const formData = new FormData();
      formData.append('full_name', fullName.trim());
      formData.append('phone_number', phoneNumber.trim());
      formData.append('linkedin_url', linkedinUrl.trim());
      formData.append('github_url', githubUrl.trim());
      formData.append('target_role', targetRole.trim());
      formData.append('bio', bio.trim());
      if (avatarFile) {
        formData.append('avatar', avatarFile);
      }

      const res = await apiUpdateCandidateProfile(formData);
      const updated = res.profile || res;
      setProfile(updated);
      setErrors({});

      // Sync local storage user full_name so navbar / header update
      const curr = getStoredUser() || {};
      storeUser({
        ...curr,
        full_name: updated.full_name,
        target_role: updated.target_role,
      });

      notify?.('Profile updated successfully!', 'success');
    } catch (err: any) {
      const serverErrors = err?.response?.data?.errors;
      if (serverErrors && typeof serverErrors === 'object') {
        const mappedErrs: Record<string, string> = {};
        for (const [k, v] of Object.entries(serverErrors)) {
          mappedErrs[k] = Array.isArray(v) ? (v[0] as string) : String(v);
        }
        setErrors(mappedErrs);
      }
      const msg = err?.response?.data?.error || 'Failed to update profile. Please check inputs.';
      notify?.(msg, 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    if (profile) {
      setFullName(profile.full_name || '');
      setPhoneNumber(profile.phone_number || '');
      setLinkedinUrl(profile.linkedin_url || '');
      setGithubUrl(profile.github_url || '');
      setTargetRole(profile.target_role || '');
      setBio(profile.bio || '');
      setAvatarFile(null);
      setAvatarPreview(profile.avatar_url || null);
      setErrors({});
      notify?.('Profile form changes reset.', 'info');
    }
  };

  const handleLogout = async () => {
    try {
      await apiLogout();
    } catch {
      // Continue client cleanup
    }
    localStorage.removeItem('careerflow-session');
    localStorage.removeItem('careerflow-user');
    notify?.('Successfully signed out.', 'info');
    setLocation('/login');
  };

  return (
    <AppShell role={effectiveRole} notify={notify}>
      <PageHeading
        eyebrow="Candidate Self-Service • US-42"
        title="Candidate Profile & Career Objectives"
        description="Maintain your professional contact information, target job specialization, and social links to automatically streamline all hiring room applications."
        action={
          <button
            type="button"
            onClick={handleLogout}
            data-testid="button-profile-logout"
            className="inline-flex items-center gap-2 rounded-xl border border-[#d9dbd1] bg-white px-4 py-2 text-xs font-bold text-[#a33d35] hover:bg-[#f7e5e1] transition shadow-xs cursor-pointer"
          >
            <LogOut size={14} /> Log out
          </button>
        }
      />

      {loading ? (
        <div className="mt-8 flex items-center justify-center p-12 bg-white rounded-3xl border border-[#d9dbd1]">
          <Loader2 size={28} className="animate-spin text-[#277254]" />
          <span className="ml-3 text-sm font-semibold text-[#253142]">Loading your profile details...</span>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="mt-6 grid gap-6 lg:grid-cols-[1fr_2fr]" data-testid="profile-container">
          {/* Left Column: Avatar & Identity Card */}
          <div className="space-y-6">
            <div className="rounded-3xl border border-[#d9dbd1] bg-white p-6 shadow-xs text-center space-y-4">
              {/* Avatar Preview with Change Button */}
              <div className="relative mx-auto w-28 h-28">
                {avatarPreview ? (
                  <img
                    src={avatarPreview}
                    alt={displayName}
                    data-testid="profile-avatar-img"
                    className="h-28 w-28 rounded-full object-cover border-2 border-[#277254] shadow-sm"
                  />
                ) : (
                  <div
                    data-testid="profile-avatar-fallback"
                    className="grid h-28 w-28 place-items-center rounded-full bg-[#f5c84b] text-3xl font-black text-[#253142] shadow-sm"
                  >
                    {initials}
                  </div>
                )}
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  title="Upload profile picture"
                  data-testid="button-upload-avatar"
                  className="absolute bottom-0 right-0 grid h-9 w-9 place-items-center rounded-full bg-[#277254] text-white shadow-md hover:bg-[#1f5b43] transition cursor-pointer border-2 border-white"
                >
                  <Camera size={16} />
                </button>
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleAvatarChange}
                  accept="image/png,image/jpeg,image/webp"
                  data-testid="input-profile-avatar"
                  className="hidden"
                />
              </div>

              <div>
                <h2 className="text-lg font-bold text-[#253142]" data-testid="profile-display-name">
                  {displayName}
                </h2>
                <p className="text-xs text-[#7b8490]" data-testid="profile-display-email">
                  {email}
                </p>
                {targetRole && (
                  <div className="mt-2 inline-flex items-center gap-1.5 rounded-full bg-[#eef4f0] border border-[#cbe0d3] px-3 py-0.5 text-[11px] font-bold text-[#277254]">
                    <Briefcase size={12} />
                    <span>{targetRole}</span>
                  </div>
                )}
              </div>

              <div className="pt-2 border-t border-[#eceee7] text-left space-y-2.5 text-xs text-[#526072]">
                <div className="flex justify-between items-center">
                  <span className="text-[#7b8490]">Workspace Role:</span>
                  <span className="inline-flex items-center gap-1 font-bold text-[#253142] capitalize">
                    <ShieldCheck size={14} className="text-[#277254]" />
                    {profile?.role_display || rawRole.replace('_', ' ')}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[#7b8490]">Account Status:</span>
                  <span className="font-bold text-[#277254] flex items-center gap-1">
                    <CheckCircle2 size={13} /> Active
                  </span>
                </div>
                {profile?.updated_at && (
                  <div className="flex justify-between items-center">
                    <span className="text-[#7b8490]">Last Updated:</span>
                    <span className="text-[#526072]">{new Date(profile.updated_at).toLocaleDateString()}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Quick Links Card */}
            <div className="rounded-3xl border border-[#d9dbd1] bg-white p-6 shadow-xs space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-[#7b8490]">Quick Links</h3>
              <div className="space-y-2 text-xs">
                {linkedinUrl ? (
                  <a
                    href={linkedinUrl.startsWith('http') ? linkedinUrl : `https://${linkedinUrl}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-between rounded-xl border border-[#e5e7eb] bg-[#faf9f5] px-3 py-2 text-[#0a66c2] hover:bg-[#eef2f8] transition font-semibold"
                  >
                    <span className="flex items-center gap-2">
                      <Linkedin size={15} /> LinkedIn Profile
                    </span>
                    <ExternalLink size={13} />
                  </a>
                ) : (
                  <div className="text-[#7b8490] italic text-xs">No LinkedIn link provided yet.</div>
                )}

                {githubUrl ? (
                  <a
                    href={githubUrl.startsWith('http') ? githubUrl : `https://${githubUrl}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-between rounded-xl border border-[#e5e7eb] bg-[#faf9f5] px-3 py-2 text-[#24292e] hover:bg-[#f0f1f3] transition font-semibold"
                  >
                    <span className="flex items-center gap-2">
                      <Github size={15} /> GitHub Profile
                    </span>
                    <ExternalLink size={13} />
                  </a>
                ) : (
                  <div className="text-[#7b8490] italic text-xs">No GitHub link provided yet.</div>
                )}
              </div>
            </div>

            {/* Password & Security Card */}
            <div className="rounded-3xl border border-[#d9dbd1] bg-white p-6 shadow-xs space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-[#7b8490] flex items-center gap-1.5">
                <Lock size={14} className="text-[#3a6384]" /> Account Security
              </h3>
              <p className="text-xs text-[#7b8490]">
                Password protected via PBKDF2 encryption. Request a time-limited reset code anytime.
              </p>
              <button
                type="button"
                onClick={() => setLocation('/forgot-password')}
                data-testid="button-profile-reset-pwd"
                className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-[#253142] px-3 py-2 text-xs font-bold text-white hover:bg-[#33435a] transition cursor-pointer"
              >
                <KeyRound size={14} /> Reset Password
              </button>
            </div>
          </div>

          {/* Right Column: Editable Profile Information Form */}
          <div className="space-y-6">
            <div className="rounded-3xl border border-[#d9dbd1] bg-white p-6 sm:p-8 shadow-xs space-y-6">
              <div className="border-b border-[#eceee7] pb-4 flex items-center justify-between flex-wrap gap-2">
                <div>
                  <h3 className="text-base font-bold text-[#253142] flex items-center gap-2">
                    <UserRound size={18} className="text-[#277254]" /> Personal & Contact Details
                  </h3>
                  <p className="text-xs text-[#7b8490] mt-0.5">
                    These values will be automatically populated into your room applications.
                  </p>
                </div>
                <div className="text-[11px] font-semibold text-[#7b8490] bg-[#faf9f5] border border-[#e5e7eb] px-2.5 py-1 rounded-lg">
                  Auto-sync active
                </div>
              </div>

              {/* Form Grid */}
              <div className="grid gap-4 sm:grid-cols-2">
                {/* Full Name */}
                <div className="sm:col-span-2">
                  <label className="block text-xs font-bold text-[#253142] mb-1.5">
                    Full Name <span className="text-[#a33d35]">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Alex Johnson"
                    data-testid="input-profile-fullname"
                    className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3.5 py-2.5 text-xs text-[#253142] focus:outline-none focus:ring-2 focus:ring-[#277254]/30"
                  />
                  {errors.full_name && (
                    <p className="mt-1 text-[11px] text-[#a33d35] flex items-center gap-1 font-medium">
                      <AlertCircle size={12} /> {errors.full_name}
                    </p>
                  )}
                </div>

                {/* Email Address (Read-only) */}
                <div>
                  <label className="block text-xs font-bold text-[#7b8490] mb-1.5">
                    Email Address (Account Identifier)
                  </label>
                  <div className="flex items-center rounded-xl border border-[#e5e7eb] bg-[#f3f4f6] px-3.5 py-2.5 text-xs text-[#6b7280]">
                    <Mail size={14} className="mr-2 text-[#9ca3af]" />
                    <span>{email}</span>
                  </div>
                  <p className="mt-1 text-[10px] text-[#9ca3af]">Linked to your login credentials.</p>
                </div>

                {/* Phone Number */}
                <div>
                  <label className="block text-xs font-bold text-[#253142] mb-1.5">
                    Phone Number
                  </label>
                  <div className="relative">
                    <Phone size={14} className="absolute left-3.5 top-3 text-[#7b8490]" />
                    <input
                      type="text"
                      value={phoneNumber}
                      onChange={(e) => setPhoneNumber(e.target.value)}
                      placeholder="+1 (555) 234-5678"
                      data-testid="input-profile-phone"
                      className={`w-full rounded-xl border ${
                        errors.phone_number ? 'border-[#a33d35] bg-[#fff5f5]' : 'border-[#d9dbd1] bg-[#fbfaf5]'
                      } pl-9 pr-3.5 py-2.5 text-xs text-[#253142] focus:outline-none focus:ring-2 focus:ring-[#277254]/30`}
                    />
                  </div>
                  {errors.phone_number ? (
                    <p className="mt-1 text-[11px] text-[#a33d35] flex items-center gap-1 font-medium">
                      <AlertCircle size={12} /> {errors.phone_number}
                    </p>
                  ) : (
                    <p className="mt-1 text-[10px] text-[#7b8490]">Include country code (e.g. +1 555-0199).</p>
                  )}
                </div>

                {/* Target Job Role */}
                <div className="sm:col-span-2">
                  <label className="block text-xs font-bold text-[#253142] mb-1.5">
                    Target Job Role / Specialization
                  </label>
                  <div className="relative">
                    <Briefcase size={14} className="absolute left-3.5 top-3 text-[#7b8490]" />
                    <input
                      type="text"
                      value={targetRole}
                      onChange={(e) => setTargetRole(e.target.value)}
                      placeholder="e.g. Senior Full Stack Engineer, AI Research Fellow"
                      data-testid="input-profile-target-role"
                      className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] pl-9 pr-3.5 py-2.5 text-xs text-[#253142] focus:outline-none focus:ring-2 focus:ring-[#277254]/30"
                    />
                  </div>
                  {errors.target_role && (
                    <p className="mt-1 text-[11px] text-[#a33d35] flex items-center gap-1 font-medium">
                      <AlertCircle size={12} /> {errors.target_role}
                    </p>
                  )}
                </div>

                {/* LinkedIn URL */}
                <div>
                  <label className="block text-xs font-bold text-[#253142] mb-1.5">
                    LinkedIn Profile URL
                  </label>
                  <div className="relative">
                    <Linkedin size={14} className="absolute left-3.5 top-3 text-[#0a66c2]" />
                    <input
                      type="text"
                      value={linkedinUrl}
                      onChange={(e) => setLinkedinUrl(e.target.value)}
                      placeholder="https://linkedin.com/in/username"
                      data-testid="input-profile-linkedin"
                      className={`w-full rounded-xl border ${
                        errors.linkedin_url ? 'border-[#a33d35] bg-[#fff5f5]' : 'border-[#d9dbd1] bg-[#fbfaf5]'
                      } pl-9 pr-3.5 py-2.5 text-xs text-[#253142] focus:outline-none focus:ring-2 focus:ring-[#277254]/30`}
                    />
                  </div>
                  {errors.linkedin_url && (
                    <p className="mt-1 text-[11px] text-[#a33d35] flex items-center gap-1 font-medium">
                      <AlertCircle size={12} /> {errors.linkedin_url}
                    </p>
                  )}
                </div>

                {/* GitHub URL */}
                <div>
                  <label className="block text-xs font-bold text-[#253142] mb-1.5">
                    GitHub Profile URL
                  </label>
                  <div className="relative">
                    <Github size={14} className="absolute left-3.5 top-3 text-[#24292e]" />
                    <input
                      type="text"
                      value={githubUrl}
                      onChange={(e) => setGithubUrl(e.target.value)}
                      placeholder="https://github.com/username"
                      data-testid="input-profile-github"
                      className={`w-full rounded-xl border ${
                        errors.github_url ? 'border-[#a33d35] bg-[#fff5f5]' : 'border-[#d9dbd1] bg-[#fbfaf5]'
                      } pl-9 pr-3.5 py-2.5 text-xs text-[#253142] focus:outline-none focus:ring-2 focus:ring-[#277254]/30`}
                    />
                  </div>
                  {errors.github_url && (
                    <p className="mt-1 text-[11px] text-[#a33d35] flex items-center gap-1 font-medium">
                      <AlertCircle size={12} /> {errors.github_url}
                    </p>
                  )}
                </div>

                {/* Bio / Career Objective */}
                <div className="sm:col-span-2">
                  <label className="block text-xs font-bold text-[#253142] mb-1.5">
                    Professional Summary / Candidate Bio
                  </label>
                  <textarea
                    rows={4}
                    value={bio}
                    onChange={(e) => setBio(e.target.value)}
                    placeholder="Briefly describe your background, technical proficiencies, key accomplishments, and career aspirations..."
                    data-testid="input-profile-bio"
                    className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3.5 py-2.5 text-xs text-[#253142] focus:outline-none focus:ring-2 focus:ring-[#277254]/30 leading-relaxed"
                  />
                  {errors.bio && (
                    <p className="mt-1 text-[11px] text-[#a33d35] flex items-center gap-1 font-medium">
                      <AlertCircle size={12} /> {errors.bio}
                    </p>
                  )}
                </div>
              </div>

              {/* Form Action Buttons */}
              <div className="flex items-center justify-end gap-3 pt-4 border-t border-[#eceee7]">
                <button
                  type="button"
                  onClick={handleReset}
                  disabled={saving}
                  data-testid="button-profile-reset"
                  className="inline-flex items-center gap-1.5 rounded-xl border border-[#d9dbd1] bg-white px-4 py-2.5 text-xs font-bold text-[#526072] hover:bg-[#f8f7f2] transition cursor-pointer"
                >
                  <RotateCcw size={14} /> Reset
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  data-testid="button-profile-save"
                  className="inline-flex items-center gap-2 rounded-xl bg-[#277254] px-6 py-2.5 text-xs font-bold text-white hover:bg-[#1f5b43] transition shadow-xs cursor-pointer disabled:opacity-50"
                >
                  {saving ? (
                    <>
                      <Loader2 size={14} className="animate-spin" />
                      <span>Saving Profile...</span>
                    </>
                  ) : (
                    <>
                      <Save size={14} />
                      <span>Save Changes</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </form>
      )}
    </AppShell>
  );
}
