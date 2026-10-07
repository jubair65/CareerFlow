import { useState, useEffect } from 'react';
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
import { apiGetPublicRoomByToken, type PublicRoomDetails } from '../api/recruitment';

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
                Application Link Inactive or Expired
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

        <div className="inline-flex items-center gap-2 rounded-full bg-[#edfdf4] px-3 py-1 text-xs font-bold text-[#03543f] border border-[#bcf0da]">
          <span className="h-2 w-2 rounded-full bg-[#277254] animate-pulse" />
          <span>Accepting Applications</span>
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

            <form
              onSubmit={(e) => {
                e.preventDefault();
                notify?.('Submission will be available in US-22 (Candidate Submission Flow).', 'info');
              }}
              className="space-y-4"
            >
              <div>
                <label className="block text-xs font-bold text-[#253142] mb-1">Full Name</label>
                <input
                  type="text"
                  required
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
                  placeholder="alex.johnson@example.com"
                  data-testid="input-candidate-email"
                  className="w-full rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] px-3.5 py-2.5 text-xs text-[#253142] focus:outline-none focus:ring-2 focus:ring-[#277254]/30"
                />
              </div>

              {/* CV Upload Dropzone */}
              <div>
                <label className="block text-xs font-bold text-[#253142] mb-1">CV / Resume (PDF or DOCX)</label>
                <div className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-[#d9dbd1] bg-[#fbfaf5] p-5 text-center hover:border-[#277254] transition cursor-pointer">
                  <Upload size={22} className="text-[#277254] mb-1.5" />
                  <span className="text-xs font-bold text-[#253142]">Upload CV Document</span>
                  <span className="text-[10px] text-[#7b8490] mt-0.5">PDF or DOCX up to 10MB</span>
                </div>
              </div>

              {/* Video Presentation Dropzone */}
              <div>
                <label className="block text-xs font-bold text-[#253142] mb-1">Video Presentation (MP4 or WebM)</label>
                <div className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-[#d9dbd1] bg-[#fbfaf5] p-5 text-center hover:border-[#4f46e5] transition cursor-pointer">
                  <Video size={22} className="text-[#4f46e5] mb-1.5" />
                  <span className="text-xs font-bold text-[#253142]">Upload or Record Video</span>
                  <span className="text-[10px] text-[#7b8490] mt-0.5">MP4 or WebM presentation clip</span>
                </div>
              </div>

              <button
                type="submit"
                data-testid="button-submit-application"
                className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-[#277254] py-3 text-xs font-bold text-white shadow-md hover:bg-[#1f5b43] transition"
              >
                <span>Submit Candidate Application</span>
                <ArrowRight size={15} />
              </button>
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
