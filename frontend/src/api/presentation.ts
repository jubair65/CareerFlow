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
    | 'RETRYING'
    | 'PARTIALLY_COMPLETED'
    | 'COMPLETED'
    | 'FAILED';
  uploaded_at: string;
  speech_analysis?: SpeechAnalysisData | null;
  behavioral_analysis?: BehavioralAnalysisData | null;
  presentation_score?: PresentationScoreData | null;
  ai_feedback?: PresentationFeedbackData | null;
  execution_logs?: PipelineExecutionLogData[];
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

export interface ImprovementItem {
  category: string;
  observation: string;
  actionable_drill: string;
}

export interface PresentationFeedbackData {
  id: number;
  video: number;
  summary: string;
  strengths: string[];
  improvements: ImprovementItem[];
  practice_tip: string;
  created_at: string;
}

/**
 * Fetch AI improvement suggestions for a video (US-15).
 */
export async function apiGetPresentationSuggestions(videoId: number): Promise<PresentationFeedbackData | null> {
  try {
    const response = await apiClient.get<PresentationFeedbackData>(`/presentation/${videoId}/suggestions/`);
    return response.data;
  } catch (error: any) {
    if (error.response?.status === 404) return null;
    throw error;
  }
}

/**
 * Trigger generation or refresh of AI improvement suggestions (US-15).
 */
export async function apiGeneratePresentationSuggestions(videoId: number): Promise<PresentationFeedbackData> {
  const response = await apiClient.post<{ message: string; ai_feedback: PresentationFeedbackData } | PresentationFeedbackData>(
    `/presentation/${videoId}/suggestions/`
  );
  return 'ai_feedback' in response.data ? response.data.ai_feedback : response.data;
}

export interface PipelineExecutionLogData {
  id: number;
  video: number;
  stage: string;
  status: 'SUCCESS' | 'RETRY' | 'DEGRADED' | 'FAILED';
  attempt: number;
  error_message: string;
  details: Record<string, any>;
  execution_time_ms: number;
  created_at: string;
}

export interface PipelineStatusData {
  video_id: number;
  status: string;
  is_degraded: boolean;
  degradation_note: string;
  has_speech: boolean;
  has_behavioral: boolean;
  has_score: boolean;
  has_feedback: boolean;
  logs: PipelineExecutionLogData[];
}

export interface PipelineRetryResponse {
  message: string;
  result: {
    success: boolean;
    video_id: number;
    status: string;
    stages_completed: string[];
    degraded: boolean;
    error?: string | null;
    duration_ms?: number;
  };
  video: PresentationVideo;
}

/**
 * Manually trigger pipeline retry with supervised resilience (US-40).
 */
export async function apiRetryPresentationPipeline(videoId: number): Promise<PipelineRetryResponse> {
  const response = await apiClient.post<PipelineRetryResponse>(`/presentation/${videoId}/retry/`);
  return response.data;
}

/**
 * Fetch real-time pipeline status and telemetry (US-40).
 */
export async function apiGetPipelineStatus(videoId: number): Promise<PipelineStatusData> {
  const response = await apiClient.get<PipelineStatusData>(`/presentation/${videoId}/status/`);
  return response.data;
}

/**
 * Fetch chronological pipeline execution logs (US-40).
 */
export async function apiGetPipelineLogs(videoId: number): Promise<PipelineExecutionLogData[]> {
  const response = await apiClient.get<PipelineExecutionLogData[]>(`/presentation/${videoId}/logs/`);
  return response.data;
}

