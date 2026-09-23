import { apiClient, getStoredTokens } from './auth';

export interface CandidateCV {
  id: number;
  original_filename: string;
  file_size: number;
  file_type: string;
  is_active: boolean;
  uploaded_at: string;
  updated_at: string;
  file_url: string;
}

export interface CVUploadResponse {
  message: string;
  cv: CandidateCV;
}

export interface CurrentCVResponse {
  cv: CandidateCV | null;
}

/**
 * Upload a candidate's CV (PDF or DOCX, max 10MB) with optional upload progress tracking.
 */
export async function apiUploadCV(
  file: File,
  onProgress?: (percentCompleted: number) => void
): Promise<CVUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<CVUploadResponse>('/cv/upload/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percent);
      }
    },
  });

  return response.data;
}

/**
 * Fetch the currently active CV for the logged-in candidate.
 */
export async function apiGetCurrentCV(): Promise<CandidateCV | null> {
  const response = await apiClient.get<CurrentCVResponse>('/cv/current/');
  return response.data.cv;
}

/**
 * Fetch historical list of all CVs uploaded by the candidate.
 */
export async function apiGetCVHistory(): Promise<CandidateCV[]> {
  const response = await apiClient.get<CandidateCV[]>('/cv/history/');
  return response.data;
}

export interface SignalFormatting {
  score: number;
  weight: string;
  word_count: number;
  detected_sections: string[];
  missing_sections: string[];
  has_dense_paragraphs: boolean;
}

export interface SignalKeyword {
  score: number;
  weight: string;
  skills_count: number;
  action_verbs_count: number;
  action_verbs_found: string[];
}

export interface SignalClarity {
  score: number;
  weight: string;
  metrics_count: number;
  metric_samples: string[];
  bullet_count: number;
}

export interface SignalRecord {
  score: number;
  weight: string;
  records_count: number;
}

export interface SignalBreakdown {
  formatting?: SignalFormatting;
  keyword_strength?: SignalKeyword;
  clarity_impact?: SignalClarity;
  experience?: SignalRecord;
  education?: SignalRecord;
}

export interface CVFeedback {
  id: number;
  cv: number;
  candidate_email: string;
  original_filename: string;
  overall_score: number;
  formatting_score: number;
  clarity_score: number;
  keyword_strength_score: number;
  experience_score: number;
  education_score: number;
  suggestions: string[];
  signal_breakdown: SignalBreakdown;
  extracted_skills: string[];
  created_at: string;
  updated_at: string;
}

export interface CurrentCVFeedbackResponse {
  cv_id?: number;
  feedback: CVFeedback | null;
  message?: string;
}

export interface GenerateFeedbackResponse {
  message: string;
  feedback: CVFeedback;
}

/**
 * Fetch automated CV feedback for current active CV of the logged in student (US-08).
 */
export async function apiGetCurrentCVFeedback(): Promise<CVFeedback | null> {
  const response = await apiClient.get<CurrentCVFeedbackResponse>('/cv/current/feedback/');
  return response.data.feedback;
}

/**
 * Fetch automated CV feedback by specific CV ID.
 */
export async function apiGetCVFeedback(cvId: number): Promise<CVFeedback> {
  const response = await apiClient.get<CVFeedback>(`/cv/${cvId}/feedback/`);
  return response.data;
}

/**
 * Trigger CV feedback generation or recalculation for a specific CV ID.
 */
export async function apiGenerateCVFeedback(cvId: number): Promise<CVFeedback> {
  const response = await apiClient.post<GenerateFeedbackResponse>(`/cv/${cvId}/generate-feedback/`);
  return response.data.feedback;
}

/**
 * Returns a file URL with authentication token attached as query param,
 * enabling direct browser viewing and downloading (e.g. in new tabs).
 */
export function getAuthenticatedFileUrl(fileUrl?: string | null): string {
  if (!fileUrl) return '';
  const { access } = getStoredTokens();
  if (!access) return fileUrl;
  const separator = fileUrl.includes('?') ? '&' : '?';
  return `${fileUrl}${separator}token=${encodeURIComponent(access)}`;
}

export interface CategoryScores {
  domain_craft?: number;
  collaboration?: number;
  leadership?: number;
  accessibility?: number;
  [key: string]: number | undefined;
}

export interface CVJobMatch {
  id: number;
  cv: number;
  candidate_name?: string;
  candidate_email?: string;
  original_filename?: string;
  job_title: string;
  company: string;
  job_description: string;
  match_score: number;
  keyword_coverage: number;
  category_scores: CategoryScores;
  skills_matched: string[];
  skills_missing: string[];
  strengths: string[];
  gaps: string[];
  recommendations: string[];
  created_at: string;
  updated_at: string;
}

export interface JobMatchRequest {
  job_title?: string;
  company?: string;
  job_description?: string;
  required_skills?: string[];
  job_id?: number | null;
}

export interface MatchComputeResponse {
  message: string;
  match: CVJobMatch;
}

export interface CurrentMatchResponse {
  match: CVJobMatch | null;
  message?: string;
}

/**
 * Compute semantic similarity score between candidate's active CV and target job brief (US-09).
 */
export async function apiMatchCVWithJob(data: JobMatchRequest): Promise<CVJobMatch> {
  const response = await apiClient.post<MatchComputeResponse>('/cv/match/', data);
  return response.data.match;
}

/**
 * Fetch candidate's active CV latest job match result (US-09).
 */
export async function apiGetCurrentCVJobMatch(): Promise<CVJobMatch | null> {
  const response = await apiClient.get<CurrentMatchResponse>('/cv/match/current/');
  return response.data.match;
}

/**
 * Retrieve candidate CV match scores across applicants for HR manager view (US-09-T6).
 */
export async function apiGetHRMatches(): Promise<CVJobMatch[]> {
  const response = await apiClient.get<CVJobMatch[]>('/cv/hr/matches/');
  return response.data;
}


