import { useState, useEffect, useMemo } from 'react';
import { useRoute, useLocation } from 'wouter';
import {
  Building2,
  Briefcase,
  Layers,
  FileText,
  Video,
  Sliders,
  CheckCircle2,
  AlertCircle,
  Clock,
  Send,
  Loader2,
  Upload,
  ArrowRight,
  Shield,
  HelpCircle,
} from 'lucide-react';
import { apiGetPublicRoomByToken, apiSubmitApplication, type PublicRoomDetails } from '../api/recruitment';
import { apiGetCandidateProfile, getStoredUser } from '../api/auth';
export function PublicApplicationPage({
  notify,
}: {
  notify?: (message: string, tone?: 'success' | 'info' | 'error') => void;
}) {
  const [, params] = useRoute('/apply/:token');
  const token = params?.token || '';
  const [, setLocation] = useLocation();

  const [room, setRoom] = useState<PublicRoomDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorStatus, setErrorStatus] = useState<{
    code: string;
    message: string;
    title?: string;
    company?: string;
  } | null>(null);

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [cvFile, setCvFile] = useState<File | null>(null);
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  // US-45: Live Countdown Timer & State Management
  const [now, setNow] = useState<Date>(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setNow(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const deadlineDate = room?.application_deadline ? new Date(room.application_deadline) : null;
  const isExpired = deadlineDate ? now.getTime() > deadlineDate.getTime() : false;
  const msRemaining = deadlineDate ? deadlineDate.getTime() - now.getTime() : null;

  const isUrgent = msRemaining !== null && msRemaining > 0 && msRemaining < 24 * 60 * 60 * 1000;

  const remainingFormatted = useMemo(() => {
    if (msRemaining === null || msRemaining <= 0) return null;
    const totalSecs = Math.floor(msRemaining / 1000);
    const days = Math.floor(totalSecs / 86400);
    const hours = Math.floor((totalSecs % 86400) / 3600);
    const minutes = Math.floor((totalSecs % 3600) / 60);
    const seconds = totalSecs % 60;
    if (days > 0) {
      return `${days}d ${hours}h ${minutes}m`;
    }
    return `${hours}h ${minutes}m ${seconds}s`;
  }, [msRemaining]);

  const isRoomOpen = (room?.status === 'OPEN' || room?.status === 'ACTIVE') && !isExpired;
  const isRoomPaused = room?.status === 'PAUSED';
  const isRoomClosed = room?.status === 'CLOSED' || isExpired;
  const isRoomDraft = room?.status === 'DRAFT';

  useEffect(() => {
    if (!token) {
      setErrorStatus({
        code: 'NO_TOKEN',
        message: 'No application token was provided in the link.',
      });
      setLoading(false);
      return;
    }

    const fetchPublicRoom = async () => {
      try {
        setLoading(true);
        const data = await apiGetPublicRoomByToken(token);
        setRoom(data);
        setErrorStatus(null);
      } catch (err: any) {
        const resData = err?.response?.data;
        const statusCode = err?.response?.status;
        setErrorStatus({
          code: resData?.code || (statusCode === 404 ? 'LINK_NOT_FOUND' : 'LINK_INACTIVE'),
          message:
            resData?.error ||
            'This application link is currently inactive or invalid. Please contact the hiring organization.',
          title: resData?.room_title,
          company: resData?.company_name,
        });
      } finally {
        setLoading(false);
      }
    };

    fetchPublicRoom();
  }, [token]);

  // US-42-T5: Autofill candidate profile data into room application flow
  useEffect(() => {
    const loadProfileAutofill = async () => {
      try {
        const stored = getStoredUser();
        if (stored?.full_name && !fullName) {
          setFullName(stored.full_name);
        }
        if (stored?.email && !email) {
          setEmail(stored.email);
        }
        const profileData = await apiGetCandidateProfile();
        if (profileData?.full_name) {
          setFullName(profileData.full_name);
        }
        if (profileData?.email) {
          setEmail(profileData.email);
        }
      } catch {
        // Visitor not logged in or profile not set: manual input allowed
      }
    };
    loadProfileAutofill();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#f5f1e6] flex items-center justify-center p-4">
        <div className="flex items-center gap-3 bg-white p-6 rounded-2xl border border-[#d9dbd1] shadow-lg">
          <Loader2 size={24} className="animate-spin text-[#277254]" />
          <span className="text-sm font-semibold text-[#253142]">Loading job application details...</span>
        </div>
      </div>
    );
  }

  // Inactive, Expired, or Invalid Link State
  if (errorStatus || !room) {
    return (
      <div className="min-h-screen bg-[#f5f1e6] flex flex-col justify-between p-4 sm:p-8" data-testid="page-link-error">
        {/* Top Header */}
        <header className="max-w-4xl mx-auto w-full flex items-center justify-between pb-6">
          <div className="flex items-center gap-2.5">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-[#253142] text-[#f5c84b]">
              <Briefcase size={18} />
            </div>
            <span className="text-lg font-black text-[#253142]">CareerFlow</span>
          </div>
        </header>

        {/* Error Card */}
        <main className="max-w-xl mx-auto w-full my-auto">
          <div
            data-testid="card-link-error"
            className="rounded-3xl bg-white border border-[#d9dbd1] shadow-xl p-8 sm:p-10 text-center space-y-5"
          >
            <div className="mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-[#fdf2f2] text-[#9b1c1c] border border-[#f8b4b4]">
              <AlertCircle size={32} />
            </div>

            <div className="space-y-2">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-[#fdf2f2] px-3 py-1 text-xs font-bold text-[#9b1c1c]">
                Status Code: {errorStatus?.code || '410 GONE'}
              </span>
              <h1 className="text-2xl font-black text-[#253142]">
                {errorStatus?.code === 'DEADLINE_PASSED'
                  ? 'Application Deadline Has Passed'
                  : errorStatus?.code === 'ROOM_PAUSED'
                  ? 'Applications Temporarily Paused'
                  : errorStatus?.code === 'ROOM_CLOSED'
                  ? 'Recruitment Room Closed'
                  : errorStatus?.code === 'ROOM_DRAFT'
                  ? 'Recruitment Room Not Yet Published'
                  : 'Application Link Inactive or Expired'}
              </h1>
              <p className="text-sm text-[#526072] leading-relaxed max-w-md mx-auto">
                {errorStatus?.message}
              </p>
            </div>

            {errorStatus?.title && (
              <div className="rounded-xl bg-[#fbfaf5] p-3 text-xs text-[#526072] border border-[#eef0e7]">
                Position:{' '}
                <strong className="text-[#253142]">{errorStatus.title}</strong>{' '}
                {errorStatus.company && `at ${errorStatus.company}`}
              </div>
            )}

            <div className="pt-4 border-t border-[#eef0e7] text-xs text-[#7b8490]">
              If you were invited to apply for this opening, please contact the recruiter or HR team for an updated link.
            </div>
          </div>
        </main>

        <footer className="text-center text-xs text-[#7b8490] py-4">
          Powered by CareerFlow Recruitment Platform
        </footer>
      </div>
    );
  }

  // Active Job Application Page
  return (
    <div className="min-h-screen bg-[#f5f1e6] flex flex-col justify-between p-4 sm:p-8" data-testid="page-public-application">
      {/* Top Navigation / Brand */}
      <header className="max-w-5xl mx-auto w-full flex items-center justify-between pb-6">
        <div className="flex items-center gap-2.5">
          <div className="grid h-9 w-9 place-items-center rounded-xl bg-[#253142] text-[#f5c84b]">
            <Briefcase size={18} />
          </div>
          <div>
            <span className="text-lg font-black text-[#253142]">CareerFlow</span>
            <span className="text-[10px] text-[#7b8490] block leading-none">Applicant Portal</span>
          </div>
        </div>

        <div
          data-testid="public-room-status-badge"
          className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-bold border ${
            isRoomOpen
              ? 'bg-[#edfdf4] text-[#03543f] border-[#bcf0da]'
              : isRoomPaused
              ? 'bg-[#fef3c7] text-[#92400e] border-[#fde68a]'
              : isRoomClosed
              ? 'bg-[#fee2e2] text-[#991b1b] border-[#fca5a5]'
              : 'bg-[#f1f3f5] text-[#526072] border-[#d9dbd1]'
          }`}
        >
          <span
            className={`h-2 w-2 rounded-full ${
              isRoomOpen
                ? 'bg-[#277254] animate-pulse'
                : isRoomPaused
                ? 'bg-[#d97706]'
                : isRoomClosed
                ? 'bg-[#dc2626]'
                : 'bg-[#687382]'
            }`}
          />
          <span>
            {isRoomOpen
              ? 'Accepting Applications'
              : isRoomPaused
              ? 'Applications Paused'
              : isRoomClosed
              ? 'Applications Closed'
              : 'Draft Room'}
          </span>
        </div>
      </header>

      {/* Main Opening Content */}
      <main className="max-w-5xl mx-auto w-full grid gap-8 lg:grid-cols-[1.2fr_.8fr] my-4">
        {/* Left Column: Job Details & Criteria */}
        <div className="space-y-6">
          {/* Hero Banner */}
          <div className="rounded-3xl bg-white border border-[#d9dbd1] p-6 sm:p-8 shadow-sm space-y-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold text-[#7b8490]">
                <Building2 size={14} />
                <span>{room.company_name}</span>
                {room.department && <span>• {room.department}</span>}
              </div>

              <h1 className="text-2xl sm:text-3xl font-black text-[#253142] tracking-tight" data-testid="public-room-title">
                {room.title}
              </h1>

              <div className="flex flex-wrap items-center gap-2 pt-1">
                {room.role_category && (
                  <span className="inline-flex items-center rounded-lg bg-[#f1f3f5] px-2.5 py-1 text-xs font-bold text-[#526072]">
                    {room.role_category}
                  </span>
                )}
                {room.experience_level && (
                  <span className="inline-flex items-center rounded-lg bg-[#f5f1e6] px-2.5 py-1 text-xs font-bold text-[#253142]">
                    {room.experience_level_display || room.experience_level} Level
                  </span>
                )}
              </div>
            </div>

            {/* Description */}
            <div className="space-y-2 pt-2 border-t border-[#eef0e7]">
              <h3 className="text-xs font-bold uppercase tracking-wider text-[#7b8490]">About the Role</h3>
              <p className="text-sm text-[#526072] leading-relaxed whitespace-pre-line">
                {room.description || 'No detailed job description provided.'}
              </p>
            </div>

            {/* Requirements Text */}
            {room.requirements_text && (
              <div className="space-y-2 pt-2 border-t border-[#eef0e7]">
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#7b8490]">Key Requirements</h3>
                <p className="text-sm text-[#526072] leading-relaxed whitespace-pre-line">
                  {room.requirements_text}
                </p>
              </div>
            )}

            {/* Required Skills Chips */}
            {room.skill_names && room.skill_names.length > 0 && (
              <div className="space-y-2 pt-2 border-t border-[#eef0e7]">
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#7b8490]">Required Skills</h3>
                <div className="flex flex-wrap gap-1.5" data-testid="public-room-skills">
                  {room.skill_names.map((skill, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center rounded-lg bg-[#e2f0e9] border border-[#c4e3d3] px-2.5 py-1 text-xs font-bold text-[#1f5b43]"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* US-45: Application Deadline & Live Countdown Card */}
            {room.application_deadline && (
              <div
                data-testid="public-room-deadline-card"
                className={`mt-4 rounded-2xl p-4 border transition ${
                  isExpired
                    ? 'bg-[#fdf2f2] border-[#f8b4b4] text-[#991b1b]'
                    : isUrgent
                    ? 'bg-[#fffbeb] border-[#fde68a] text-[#92400e]'
                    : 'bg-[#fbfaf5] border-[#eef0e7] text-[#253142]'
                }`}
              >
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-2">
                    <Clock size={16} className={isExpired ? 'text-[#991b1b]' : isUrgent ? 'text-[#d97706]' : 'text-[#277254]'} />
                    <span className="text-xs font-bold uppercase tracking-wider">
                      {isExpired ? 'Application Deadline Expired' : 'Application Deadline'}
                    </span>
                  </div>
                  <span
                    data-testid="public-room-deadline"
                    className="text-xs font-bold font-mono"
                  >
                    {new Date(room.application_deadline).toLocaleString([], {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </div>

                {/* Urgency countdown indicator */}
                {isUrgent && !isExpired && remainingFormatted && (
                  <div
                    data-testid="public-deadline-urgency-banner"
                    className="mt-2.5 flex items-center gap-2 rounded-xl bg-[#fef3c7] px-3.5 py-2 text-xs font-bold text-[#b45309] border border-[#fde68a]"
                  >
                    <span>⚡ Applications Close Soon:</span>
                    <span className="font-mono">{remainingFormatted} remaining</span>
                  </div>
                )}

                {/* Expired warning indicator */}
                {isExpired && (
                  <div
                    data-testid="public-deadline-passed-alert"
                    className="mt-2.5 flex items-center gap-2 rounded-xl bg-[#fee2e2] px-3.5 py-2 text-xs font-bold text-[#b91c1c] border border-[#fca5a5]"
                  >
                    <AlertCircle size={14} className="shrink-0" />
                    <span>The deadline has passed. Submissions are no longer accepted for this opening.</span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Evaluation Formula Card (US-20 Weighting Exposure) */}
          <div className="rounded-3xl bg-white border border-[#d9dbd1] p-6 shadow-sm space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-[#253142] uppercase tracking-wider">
              <Sliders size={14} className="text-[#277254]" />
              <span>Evaluation Criteria & Scoring Weights</span>
            </div>
            <p className="text-xs text-[#687382]">
              Applications for this position are evaluated based on both your CV credentials and your video presentation delivery:
            </p>

            <div className="grid grid-cols-2 gap-3 pt-2">
              <div className="rounded-2xl bg-[#edfdf4] border border-[#bcf0da] p-3.5 space-y-1">
                <div className="flex items-center gap-1.5 text-xs font-bold text-[#03543f]">
                  <FileText size={15} />
                  <span>CV Match Score</span>
                </div>
                <div className="text-2xl font-black text-[#277254]" data-testid="public-cv-weight">
                  {room.cv_weight}%
                </div>
                <p className="text-[10px] text-[#526072]">Skills, experience relevance & education</p>
              </div>

              <div className="rounded-2xl bg-[#eef2ff] border border-[#c7d2fe] p-3.5 space-y-1">
                <div className="flex items-center gap-1.5 text-xs font-bold text-[#3730a3]">
                  <Video size={15} />
                  <span>Video Presentation</span>
                </div>
                <div className="text-2xl font-black text-[#4f46e5]" data-testid="public-video-weight">
                  {room.video_weight}%
                </div>
                <p className="text-[10px] text-[#526072]">Communication clarity, pacing & delivery</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Application Submission Layout (US-22 Integration Ready) */}
        <div className="space-y-6">
          <div className="rounded-3xl bg-white border border-[#d9dbd1] p-6 sm:p-7 shadow-sm space-y-5">
            <div className="space-y-1 border-b border-[#eef0e7] pb-4">
              <h2 className="text-xl font-black text-[#253142]">Apply for this Position</h2>
              <p className="text-xs text-[#7b8490]">
                Submit your profile, CV, and recorded video presentation to complete your application.
              </p>
            </div>

            {/* US-45: Status Notice Banner */}
            {!isRoomOpen && (
              <div
                data-testid={isRoomPaused ? 'alert-room-paused' : isRoomClosed ? 'alert-room-closed' : 'alert-room-draft'}
                className={`rounded-2xl p-4 text-xs font-semibold flex items-center gap-2.5 border ${
                  isRoomPaused
                    ? 'bg-[#fffbeb] border-[#fde68a] text-[#92400e]'
                    : isRoomClosed
                    ? 'bg-[#fdf2f2] border-[#f8b4b4] text-[#991b1b]'
                    : 'bg-[#f1f3f5] border-[#d9dbd1] text-[#526072]'
                }`}
              >
                <AlertCircle size={16} className="shrink-0" />
                <span>
                  {isRoomPaused
                    ? 'Applications for this position are temporarily paused by the hiring team. Submissions are currently disabled.'
                    : isRoomClosed
                    ? 'Applications for this opening are closed. Submissions can no longer be accepted.'
                    : 'This recruitment room is in draft mode. Applications are not currently open.'}
                </span>
              </div>
            )}

            <form
              onSubmit={async (e) => {
                e.preventDefault();
                if (!isRoomOpen) {
                  notify?.('Submissions are closed or paused for this room.', 'error');
                  return;
                }
                if (!cvFile || !videoFile) {
                  notify?.('Please upload both a CV and a Video Presentation.', 'error');
                  return;
                }
                try {
                  setSubmitting(true);
                  const formData = new FormData();
                  formData.append('full_name', fullName);
                  formData.append('email', email);
                  formData.append('cv_file', cvFile);
                  formData.append('video_file', videoFile);
                  
                  await apiSubmitApplication(token, formData);
                  setSubmitted(true);
                  notify?.('Application submitted successfully!', 'success');
                } catch (err: any) {
                  const errorMsg = err.response?.data?.error || 'Failed to submit application. Please try again.';
                  notify?.(errorMsg, 'error');
                } finally {
                  setSubmitting(false);
                }
              }}
              className="space-y-4"
            >
              {submitted ? (
                <div className="rounded-2xl bg-[#edfdf4] border border-[#bcf0da] p-8 text-center space-y-4">
                  <div className="mx-auto grid h-16 w-16 place-items-center rounded-full bg-[#c4e3d3] text-[#277254]">
                    <CheckCircle2 size={32} />
                  </div>
                  <div>
                    <h3 className="text-xl font-black text-[#03543f]">Application Received</h3>
                    <p className="text-sm text-[#277254] mt-2">
                      Thank you for applying! Your profile, CV, and video presentation are now being processed by our AI pipeline. The hiring team will be in touch shortly.
                    </p>
                  </div>
                </div>
              ) : (
                <>
                  <div>
                    <label className="block text-xs font-bold text-[#253142] mb-1">Full Name</label>
                    <input
                      type="text"
                      required
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="e.g. Alex Johnson"
                      data-testid="input-candidate-name"
                      className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3.5 py-2.5 text-xs text-[#253142] focus:outline-none focus:ring-2 focus:ring-[#277254]/30"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-[#253142] mb-1">Email Address</label>
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="alex.johnson@example.com"
                      data-testid="input-candidate-email"
                      className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3.5 py-2.5 text-xs text-[#253142] focus:outline-none focus:ring-2 focus:ring-[#277254]/30"
                    />
                  </div>

                  {/* CV Upload Dropzone */}
                  <div>
                    <label className="block text-xs font-bold text-[#253142] mb-1">CV / Resume (PDF or DOCX)</label>
                    <div className="relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-[#d9dbd1] bg-[#fbfaf5] p-5 text-center hover:border-[#277254] transition cursor-pointer">
                      <input 
                        type="file" 
                        accept=".pdf,.docx" 
                        onChange={(e) => setCvFile(e.target.files?.[0] || null)}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        required
                      />
                      {cvFile ? (
                        <>
                          <FileText size={22} className="text-[#277254] mb-1.5" />
                          <span className="text-xs font-bold text-[#253142]">{cvFile.name}</span>
                          <span className="text-[10px] text-[#7b8490] mt-0.5">{(cvFile.size / 1024 / 1024).toFixed(2)} MB</span>
                        </>
                      ) : (
                        <>
                          <Upload size={22} className="text-[#277254] mb-1.5" />
                          <span className="text-xs font-bold text-[#253142]">Upload CV Document</span>
                          <span className="text-[10px] text-[#7b8490] mt-0.5">PDF or DOCX up to 10MB</span>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Video Presentation Dropzone */}
                  <div>
                    <label className="block text-xs font-bold text-[#253142] mb-1">Video Presentation (MP4 or WebM)</label>
                    <div className="relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-[#d9dbd1] bg-[#fbfaf5] p-5 text-center hover:border-[#4f46e5] transition cursor-pointer">
                      <input 
                        type="file" 
                        accept=".mp4,.webm,.mov" 
                        onChange={(e) => setVideoFile(e.target.files?.[0] || null)}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        required
                      />
                      {videoFile ? (
                        <>
                          <Video size={22} className="text-[#4f46e5] mb-1.5" />
                          <span className="text-xs font-bold text-[#253142]">{videoFile.name}</span>
                          <span className="text-[10px] text-[#7b8490] mt-0.5">{(videoFile.size / 1024 / 1024).toFixed(2)} MB</span>
                        </>
                      ) : (
                        <>
                          <Video size={22} className="text-[#4f46e5] mb-1.5" />
                          <span className="text-xs font-bold text-[#253142]">Upload or Record Video</span>
                          <span className="text-[10px] text-[#7b8490] mt-0.5">MP4 or WebM presentation clip</span>
                        </>
                      )}
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={submitting || !isRoomOpen}
                    data-testid="button-submit-application"
                    className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-[#277254] py-3 text-xs font-bold text-white shadow-md hover:bg-[#1f5b43] transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {submitting ? (
                      <>
                        <Loader2 size={15} className="animate-spin" />
                        <span>Submitting Application...</span>
                      </>
                    ) : !isRoomOpen ? (
                      <span>
                        {isRoomPaused
                          ? 'Applications Paused'
                          : isRoomClosed
                          ? 'Applications Closed'
                          : 'Submissions Disabled'}
                      </span>
                    ) : (
                      <>
                        <span>Submit Candidate Application</span>
                        <ArrowRight size={15} />
                      </>
                    )}
                  </button>
                </>
              )}
            </form>
          </div>
        </div>
      </main>

      <footer className="text-center text-xs text-[#7b8490] py-4">
        Powered by CareerFlow Recruitment Platform • Secure Candidate Application
      </footer>
    </div>
  );
}
