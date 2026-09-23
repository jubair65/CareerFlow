import { useState, useEffect, useRef } from 'react';
import type { DragEvent, ChangeEvent } from 'react';
import { useLocation } from 'wouter';
import {
  FileText,
  Upload,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  FileCheck,
  Clock,
  HardDrive,
  Download,
  History,
  Sparkles,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import {
  PageHeading,
  Badge,
  type Notify,
} from '../components/dashboard/DashboardShared';
import {
  apiGetCurrentCV,
  apiUploadCV,
  apiGetCVHistory,
  getAuthenticatedFileUrl,
  type CandidateCV,
} from '../api/cv';

const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB
const ALLOWED_EXTENSIONS = ['.pdf', '.docx'];

function formatBytes(bytes: number, decimals = 1) {
  if (!bytes) return '0 B';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

function formatDate(dateStr: string) {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateStr;
  }
}

export function CvStudio({ notify }: { notify: Notify }) {
  const [, setLocation] = useLocation();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [currentCv, setCurrentCv] = useState<CandidateCV | null>(null);
  const [cvHistory, setCvHistory] = useState<CandidateCV[]>([]);
  const [loading, setLoading] = useState(true);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Fetch current CV and history
  const loadCvData = async () => {
    try {
      setLoading(true);
      const [current, history] = await Promise.all([
        apiGetCurrentCV().catch(() => null),
        apiGetCVHistory().catch(() => []),
      ]);
      setCurrentCv(current);
      setCvHistory(history);
    } catch (err: any) {
      // Fallback
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCvData();
  }, []);

  const validateAndSetFile = (file: File) => {
    setValidationError(null);

    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      const msg = `Unsupported file format '${ext}'. Only PDF (.pdf) and DOCX (.docx) documents are supported.`;
      setValidationError(msg);
      notify(msg, 'error');
      return;
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      const msg = `File size exceeds 10 MB limit (${(file.size / (1024 * 1024)).toFixed(1)} MB).`;
      setValidationError(msg);
      notify(msg, 'error');
      return;
    }

    setSelectedFile(file);
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      validateAndSetFile(file);
    }
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      validateAndSetFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      notify('Please select a PDF or DOCX file to upload.', 'error');
      return;
    }

    try {
      setUploading(true);
      setUploadProgress(0);

      const res = await apiUploadCV(selectedFile, (pct) => {
        setUploadProgress(pct);
      });

      notify('CV uploaded successfully.', 'success');
      setCurrentCv(res.cv);
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      // Refresh history
      apiGetCVHistory().then((h) => setCvHistory(h)).catch(() => {});
    } catch (err: any) {
      const msg =
        err?.response?.data?.file?.[0] ||
        err?.response?.data?.detail ||
        err?.response?.data?.error ||
        err?.response?.data?.non_field_errors?.[0] ||
        err?.message ||
        'Failed to upload CV. Please try again.';
      setValidationError(msg);
      notify(msg, 'error');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  return (
    <AppShell role="student" notify={notify}>
      <PageHeading
        eyebrow="Candidate Studio"
        title="CV Studio & Document Vault"
        description="Upload and manage your CV in PDF or DOCX format. Keep your profile up to date for instant role matching and analysis."
      />

      <div className="grid gap-6 lg:grid-cols-[1.1fr_.9fr]">
        {/* Left Column: Current Active CV */}
        <section className="cf-card rounded-2xl bg-white p-6 border border-[#d9dbd1] shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-[#eef0e7] pb-4">
              <div className="flex items-center gap-3">
                <div className="grid h-11 w-11 place-items-center rounded-xl bg-[#e2f0e9] text-[#277254]">
                  <FileText size={22} />
                </div>
                <div>
                  <h2 className="font-bold text-[#253142] text-lg">Active CV Document</h2>
                  <p className="text-xs text-[#7b8490]">Your primary CV used for applications & scoring</p>
                </div>
              </div>
              {currentCv ? (
                <Badge tone="good">Active</Badge>
              ) : (
                <Badge tone="warn">No CV Uploaded</Badge>
              )}
            </div>

            {loading ? (
              <div className="py-14 text-center">
                <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-[#277254] border-t-transparent" />
                <p className="mt-3 text-xs font-semibold text-[#7b8490]">Loading CV vault...</p>
              </div>
            ) : currentCv ? (
              <div className="mt-6 space-y-4">
                <div className="rounded-xl border border-[#d9dbd1] bg-[#fbfaf5] p-5">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <FileCheck size={18} className="text-[#277254] shrink-0" />
                        <h3 className="truncate font-bold text-base text-[#253142]" data-testid="text-current-cv-name">
                          {currentCv.original_filename}
                        </h3>
                      </div>
                      <div className="mt-3 grid grid-cols-2 gap-3 text-xs text-[#687382]">
                        <div className="flex items-center gap-1.5">
                          <Clock size={14} className="text-[#9aa2a9]" />
                          <span>Uploaded: {formatDate(currentCv.uploaded_at)}</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <HardDrive size={14} className="text-[#9aa2a9]" />
                          <span>Size: {formatBytes(currentCv.file_size)} ({currentCv.file_type.toUpperCase()})</span>
                        </div>
                      </div>
                    </div>
                    {currentCv.file_url && (
                      <a
                        href={getAuthenticatedFileUrl(currentCv.file_url)}
                        target="_blank"
                        rel="noreferrer"
                        data-testid="link-download-cv"
                        className="inline-flex items-center gap-1.5 rounded-lg border border-[#ccd0c6] bg-white px-3 py-1.5 text-xs font-bold text-[#253142] hover:bg-[#fffaf0] transition shadow-2xs shrink-0"
                      >
                        <Download size={13} /> View
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-12 text-center" data-testid="empty-cv-state">
                <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-[#f4f2e9] text-[#7b8490]">
                  <Upload size={24} />
                </div>
                <h3 className="mt-4 font-bold text-base text-[#253142]">No CV uploaded yet</h3>
                <p className="mx-auto mt-2 max-w-sm text-xs leading-5 text-[#7b8490]">
                  Upload your CV in PDF or DOCX format using the upload panel to activate automated scoring and job matching.
                </p>
              </div>
            )}
          </div>

          <div className="mt-6 pt-4 border-t border-[#eef0e7] flex items-center justify-between">
            <span className="text-xs text-[#7b8490]">
              {currentCv ? 'Ready for AI scoring & feedback' : 'Step 1 of 4 in profile completion'}
            </span>
            <button
              type="button"
              onClick={() => setLocation('/student/cv/results')}
              data-testid="button-view-cv-suggestions"
              disabled={!currentCv}
              className="inline-flex items-center gap-2 rounded-xl bg-[#253142] px-4 py-2.5 text-xs font-bold text-[#faf7ef] hover:bg-[#33435a] transition disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Analyze CV & View Score <Sparkles size={14} className="text-[#f5c84b]" />
            </button>
          </div>
        </section>


        {/* Right Column: Upload / Re-upload Dropzone */}
        <section className="rounded-2xl bg-[#253142] p-6 text-[#faf7ef] shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-[.13em] text-[#aab5c0]">
                {currentCv ? 'Version Replacement' : 'New Ingestion'}
              </span>
              <Upload className="text-[#f5c84b]" size={22} />
            </div>

            <h2 className="cf-display mt-5 text-2xl font-bold">
              {currentCv ? 'Upload a newer version' : 'Upload your CV'}
            </h2>
            <p className="mt-2 text-xs leading-5 text-[#bfc8d0]">
              PDF or DOCX documents up to 10 MB. Re-uploading automatically marks your newest file as the active version.
            </p>

            {/* Dropzone */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              data-testid="cv-dropzone"
              className={`mt-6 cursor-pointer rounded-2xl border-2 border-dashed p-6 text-center transition ${
                dragOver
                  ? 'border-[#f5c84b] bg-[#314154]'
                  : selectedFile
                  ? 'border-[#277254] bg-[#2d3e35]'
                  : 'border-[#47576b] bg-[#2d3b4e] hover:border-[#f5c84b] hover:bg-[#314154]'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx"
                className="hidden"
                data-testid="input-cv-file"
                onChange={handleFileChange}
              />

              <div className="mx-auto grid h-11 w-11 place-items-center rounded-xl bg-[#253142] text-[#f5c84b]">
                <FileText size={20} />
              </div>

              {selectedFile ? (
                <div className="mt-3">
                  <div className="truncate text-sm font-bold text-[#faf7ef]" data-testid="selected-filename">
                    {selectedFile.name}
                  </div>
                  <div className="mt-1 text-xs text-[#84c49f] font-semibold">
                    {formatBytes(selectedFile.size)} • Ready to upload
                  </div>
                </div>
              ) : (
                <div className="mt-3">
                  <div className="text-sm font-bold text-[#faf7ef]">
                    Click to browse or drop file here
                  </div>
                  <div className="mt-1 text-xs text-[#9daaba]">
                    Supports PDF (.pdf) and Word (.docx) up to 10 MB
                  </div>
                </div>
              )}
            </div>

            {/* Validation Error Banner */}
            {validationError && (
              <div
                data-testid="upload-error-message"
                className="mt-4 flex items-center gap-2 rounded-xl bg-[#f7e5e1] p-3 text-xs font-semibold text-[#a33d35]"
              >
                <AlertCircle size={16} className="shrink-0" />
                <span>{validationError}</span>
              </div>
            )}

            {/* Upload Progress Bar */}
            {uploading && (
              <div className="mt-5 space-y-2" data-testid="upload-progress-container">
                <div className="flex justify-between text-xs font-bold">
                  <span className="text-[#bfc8d0]">Uploading CV document...</span>
                  <span className="text-[#f5c84b]">{uploadProgress}%</span>
                </div>
                <div className="cf-progress h-2 w-full overflow-hidden rounded-full bg-[#394b5e]">
                  <div
                    className="h-full bg-[#f5c84b] transition-all duration-200"
                    style={{ width: `${uploadProgress}%` }}
                    data-testid="upload-progress-bar"
                  />
                </div>
              </div>
            )}
          </div>

          <div className="mt-6">
            <button
              type="button"
              disabled={!selectedFile || uploading}
              onClick={handleUpload}
              data-testid="button-upload-cv"
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#f5c84b] px-4 py-3 text-sm font-bold text-[#253142] transition hover:bg-[#ffd969] disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {uploading ? (
                <>
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-[#253142] border-t-transparent" />
                  Uploading CV ({uploadProgress}%)
                </>
              ) : (
                <>
                  {currentCv ? 'Upload newer version' : 'Upload CV'} <ArrowRight size={16} />
                </>
              )}
            </button>
          </div>
        </section>
      </div>

      {/* Historical Versions Table */}
      {cvHistory.length > 0 && (
        <section className="mt-8 cf-card rounded-2xl bg-white p-6 border border-[#d9dbd1] shadow-sm">
          <div className="flex items-center gap-2 pb-4 border-b border-[#eef0e7]">
            <History size={18} className="text-[#526072]" />
            <h2 className="font-bold text-[#253142] text-base">Version History & Audit Log</h2>
            <span className="ml-auto text-xs text-[#7b8490]">{cvHistory.length} total uploads</span>
          </div>

          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-xs" data-testid="table-cv-history">
              <thead>
                <tr className="border-b border-[#eef0e7] text-[#7b8490] font-semibold">
                  <th className="pb-3">Filename</th>
                  <th className="pb-3">Type</th>
                  <th className="pb-3">Size</th>
                  <th className="pb-3">Uploaded Date</th>
                  <th className="pb-3">Status</th>
                  <th className="pb-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f4f2e9]">
                {cvHistory.map((item) => (
                  <tr key={item.id} className="text-[#253142]">
                    <td className="py-3 font-semibold flex items-center gap-2">
                      <FileText size={15} className="text-[#526072]" />
                      <span className="truncate max-w-[220px]">{item.original_filename}</span>
                    </td>
                    <td className="py-3 uppercase font-mono">{item.file_type}</td>
                    <td className="py-3">{formatBytes(item.file_size)}</td>
                    <td className="py-3 text-[#687382]">{formatDate(item.uploaded_at)}</td>
                    <td className="py-3">
                      {item.is_active ? (
                        <Badge tone="good">Active</Badge>
                      ) : (
                        <Badge tone="neutral">Archived</Badge>
                      )}
                    </td>
                    <td className="py-3 text-right">
                      {item.file_url && (
                        <a
                          href={getAuthenticatedFileUrl(item.file_url)}
                          target="_blank"
                          rel="noreferrer"
                          className="font-bold text-[#277254] hover:underline"
                        >
                          View
                        </a>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

    </AppShell>
  );
}
