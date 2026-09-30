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
  speech_analysis?: SpeechAnalysisData | null;
  behavioral_analysis?: BehavioralAnalysisData | null;
  presentation_score?: PresentationScoreData | null;
}

export interface PresentationScoreData {
  id: number;
  video: number;
  overall_score: number;
  speech_score: number;
  behavioral_score: number;
  pace_score: number;
  filler_score: number;
  eye_contact_score: number;
  posture_score: number;
  engagement_score: number;
  has_behavioral_data: boolean;
  notes: string;
  grade_label: 'Excellent' | 'Competent' | 'Needs Practice';
  grade_color: string;
  calculated_at: string;
}

export interface SpeechAnalysisData {
  id: number;
  transcript: string;
  words_per_minute: number;
  filler_word_count: number;
  filler_words_breakdown: Record<string, number>;
  clarity_score: number;
  duration_seconds: number;
  processed_at: string;
}

export interface BehavioralAnalysisData {
  id: number;
  eye_contact_score: number;
  posture_score: number;
  engagement_score: number;
  frame_metrics: any;
  processed_at: string;
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

/**
 * Get speech analysis for a video.
 */
export async function apiGetSpeechAnalysis(videoId: number): Promise<SpeechAnalysisData | null> {
  try {
    const response = await apiClient.get<SpeechAnalysisData>(`/presentation/${videoId}/speech/`);
    return response.data;
  } catch (error: any) {
    if (error.response?.status === 404) return null;
    throw error;
  }
}

/**
 * Trigger speech analysis on a video.
 */
export async function apiTriggerSpeechAnalysis(videoId: number): Promise<SpeechAnalysisData> {
  const response = await apiClient.post<{ message: string; speech_analysis: SpeechAnalysisData } | SpeechAnalysisData>(
    `/presentation/${videoId}/speech/`
  );
  return 'speech_analysis' in response.data ? response.data.speech_analysis : response.data;
}

/**
 * Get behavioral analysis for a video.
 */
export async function apiGetBehavioralAnalysis(videoId: number): Promise<BehavioralAnalysisData | null> {
  try {
    const response = await apiClient.get<BehavioralAnalysisData>(`/presentation/${videoId}/behavioral/`);
    return response.data;
  } catch (error: any) {
    if (error.response?.status === 404) return null;
    throw error;
  }
}

/**
 * Trigger behavioral analysis on a video.
 */
export async function apiTriggerBehavioralAnalysis(videoId: number): Promise<BehavioralAnalysisData> {
  const response = await apiClient.post<{ message: string; behavioral_analysis: BehavioralAnalysisData } | BehavioralAnalysisData>(
    `/presentation/${videoId}/behavioral/`
  );
  return 'behavioral_analysis' in response.data ? response.data.behavioral_analysis : response.data;
}

/**
 * Get composite presentation score for a video (US-14).
 */
export async function apiGetPresentationScore(videoId: number): Promise<PresentationScoreData | null> {
  try {
    const response = await apiClient.get<PresentationScoreData>(`/presentation/${videoId}/score/`);
    return response.data;
  } catch (error: any) {
    if (error.response?.status === 404) return null;
    throw error;
  }
}

/**
 * Calculate or recalculate composite presentation score for a video (US-14).
 */
export async function apiCalculatePresentationScore(videoId: number): Promise<PresentationScoreData> {
  const response = await apiClient.post<{ message: string; presentation_score: PresentationScoreData }>(
    `/presentation/${videoId}/score/`
  );
  return response.data.presentation_score;
}
