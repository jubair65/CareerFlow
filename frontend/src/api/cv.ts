import { apiClient } from './auth';

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
