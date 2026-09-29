import { apiClient } from './auth';

export interface PresentationVideo {
  id: number;
  original_filename: string;
  file: string;
  file_url: string;
  raw_file_size: number;
  compressed_file_size: number;
  formatted_raw_size: string;
  formatted_compressed_size: string;
  compression_savings_percent: number;
  file_type: string;
  duration_seconds: number;
  is_active: boolean;
  status:
    | 'UPLOADED'
    | 'COMPRESSING'
    | 'READY_FOR_ANALYSIS'
    | 'PROCESSING_SPEECH'
    | 'PROCESSING_VISION'
    | 'SCORING'
    | 'COMPLETED'
    | 'FAILED';
  uploaded_at: string;
}

export interface VideoUploadResponse {
  message: string;
  video: PresentationVideo;
}

/**
 * Upload candidate presentation video (max 250MB, mp4/webm/mov)
 * with real-time upload progress tracking.
 */
export async function apiUploadPresentationVideo(
  file: File | Blob,
  fileName?: string,
  onProgress?: (percent: number) => void
): Promise<VideoUploadResponse> {
  const formData = new FormData();
  if (file instanceof File) {
    formData.append('file', file);
  } else {
    formData.append('file', file, fileName || 'webcam_recording.webm');
  }

  const response = await apiClient.post<VideoUploadResponse>('/presentation/upload/', formData, {
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
 * Fetch the currently active presentation video for the student.
 */
export async function apiGetActivePresentationVideo(): Promise<PresentationVideo | null> {
  try {
    const response = await apiClient.get<PresentationVideo>('/presentation/active/');
    return response.data;
  } catch (error: any) {
    if (error.response?.status === 404) {
      return null;
    }
    throw error;
  }
}

/**
 * Fetch video history for the candidate.
 */
export async function apiGetPresentationVideoHistory(): Promise<PresentationVideo[]> {
  const response = await apiClient.get<PresentationVideo[]>('/presentation/history/');
  return response.data;
}

/**
 * Delete a presentation video by ID.
 */
export async function apiDeletePresentationVideo(id: number): Promise<void> {
  await apiClient.delete(`/presentation/${id}/`);
}
