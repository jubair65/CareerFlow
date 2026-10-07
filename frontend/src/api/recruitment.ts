import { apiClient } from './auth';

export interface SkillItem {
  name: string;
  importance?: 'REQUIRED' | 'PREFERRED';
  category?: string;
}

export interface RecruitmentRoom {
  id: number;
  title: string;
  company_name: string;
  department: string;
  role_category?: string;
  experience_level?: 'ENTRY' | 'MID' | 'SENIOR' | 'LEAD';
  experience_level_display?: string;
  description: string;
  status: 'ACTIVE' | 'PAUSED' | 'CLOSED';
  requirements_text: string;
  skills_required: (string | SkillItem)[];
  cv_weight: number;
  video_weight: number;
  share_token: string;
  share_url: string;
  link_is_active: boolean;
  link_expires_at: string | null;
  created_by: number;
  created_by_name: string;
  created_by_email: string;
  created_at: string;
  updated_at: string;
}

export interface CreateRoomPayload {
  title: string;
  company_name: string;
  department?: string;
  description?: string;
}

export interface UpdateRoomPayload {
  title?: string;
  company_name?: string;
  department?: string;
  description?: string;
  status?: 'ACTIVE' | 'PAUSED' | 'CLOSED';
}

export interface RoomRequirementsPayload {
  role_category?: string;
  experience_level?: 'ENTRY' | 'MID' | 'SENIOR' | 'LEAD';
  requirements_text?: string;
  skills_required: (string | SkillItem)[];
}

export interface RoomRequirementsResponse {
  message: string;
  room: RecruitmentRoom;
  requirements: {
    id: number;
    title: string;
    role_category: string;
    experience_level: 'ENTRY' | 'MID' | 'SENIOR' | 'LEAD';
    requirements_text: string;
    skills_required: SkillItem[];
    updated_at: string;
  };
}

export interface RoomRequirementsDetailResponse {
  room_id: number;
  title: string;
  company_name: string;
  requirements: {
    id: number;
    title: string;
    role_category: string;
    experience_level: 'ENTRY' | 'MID' | 'SENIOR' | 'LEAD';
    requirements_text: string;
    skills_required: SkillItem[];
    updated_at: string;
  };
  skill_names: string[];
}

export interface RoomApiResponse {
  message: string;
  room: RecruitmentRoom;
}

/**
 * Fetch all rooms created by the currently logged-in HR manager.
 */
export async function apiGetRooms(): Promise<RecruitmentRoom[]> {
  const response = await apiClient.get<RecruitmentRoom[]>('/recruitment/rooms/');
  return response.data;
}

/**
 * Fetch a single room by its ID.
 */
export async function apiGetRoomDetail(id: number | string): Promise<RecruitmentRoom> {
  const response = await apiClient.get<RecruitmentRoom>(`/recruitment/rooms/${id}/`);
  return response.data;
}

/**
 * Create a new recruitment room (US-18-T2).
 */
export async function apiCreateRoom(payload: CreateRoomPayload): Promise<RoomApiResponse> {
  const response = await apiClient.post<RoomApiResponse>('/recruitment/rooms/', payload);
  return response.data;
}

/**
 * Update an existing room (title, description, status).
 */
export async function apiUpdateRoom(id: number | string, payload: UpdateRoomPayload): Promise<RoomApiResponse> {
  const response = await apiClient.patch<RoomApiResponse>(`/recruitment/rooms/${id}/`, payload);
  return response.data;
}

/**
 * Delete a room by its ID.
 */
export async function apiDeleteRoom(id: number | string): Promise<void> {
  await apiClient.delete(`/recruitment/rooms/${id}/`);
}

/**
 * Fetch requirements and skills for a room (US-19-T2).
 */
export async function apiGetRoomRequirements(id: number | string): Promise<RoomRequirementsDetailResponse> {
  const response = await apiClient.get<RoomRequirementsDetailResponse>(`/recruitment/rooms/${id}/requirements/`);
  return response.data;
}

/**
 * Update requirements and skills for a room (US-19-T2).
 */
export async function apiUpdateRoomRequirements(
  id: number | string,
  payload: RoomRequirementsPayload
): Promise<RoomRequirementsResponse> {
  const response = await apiClient.patch<RoomRequirementsResponse>(
    `/recruitment/rooms/${id}/requirements/`,
    payload
  );
  return response.data;
}

export interface RoomWeightingPayload {
  cv_weight: number;
  video_weight: number;
}

export interface RoomWeightingDetailResponse {
  room_id: number;
  title: string;
  company_name: string;
  cv_weight: number;
  video_weight: number;
  weighting: {
    id: number;
    title: string;
    company_name: string;
    cv_weight: number;
    video_weight: number;
    updated_at: string;
  };
}

export interface RoomWeightingResponse {
  message: string;
  room: RecruitmentRoom;
  weighting: {
    id: number;
    title: string;
    company_name: string;
    cv_weight: number;
    video_weight: number;
    updated_at: string;
  };
}

/**
 * Fetch evaluation weighting for a room (US-20-T2).
 */
export async function apiGetRoomWeighting(id: number | string): Promise<RoomWeightingDetailResponse> {
  const response = await apiClient.get<RoomWeightingDetailResponse>(`/recruitment/rooms/${id}/weighting/`);
  return response.data;
}

/**
 * Update evaluation weighting for a room (US-20-T2).
 */
export async function apiUpdateRoomWeighting(
  id: number | string,
  payload: RoomWeightingPayload
): Promise<RoomWeightingResponse> {
  const response = await apiClient.patch<RoomWeightingResponse>(
    `/recruitment/rooms/${id}/weighting/`,
    payload
  );
  return response.data;
}

// ==========================================
// US-21: Shareable Application Link APIs
// ==========================================

export interface RoomShareLinkData {
  id: number;
  title: string;
  company_name: string;
  share_token: string;
  share_url: string;
  link_is_active: boolean;
  link_expires_at: string | null;
  is_expired: boolean;
  status: 'ACTIVE' | 'PAUSED' | 'CLOSED';
  updated_at: string;
}

export interface RoomShareLinkResponse {
  message: string;
  link: RoomShareLinkData;
}

export interface PublicRoomDetails {
  id: number;
  title: string;
  company_name: string;
  department: string;
  role_category?: string;
  experience_level?: 'ENTRY' | 'MID' | 'SENIOR' | 'LEAD';
  experience_level_display?: string;
  description: string;
  requirements_text: string;
  skills_required: (string | SkillItem)[];
  skill_names: string[];
  cv_weight: number;
  video_weight: number;
  share_token: string;
  share_url: string;
  link_is_active: boolean;
  link_expires_at: string | null;
  status: 'ACTIVE' | 'PAUSED' | 'CLOSED';
  created_at: string;
}

/**
 * Retrieve or generate share link information for a room (US-21-T2).
 */
export async function apiGetRoomShareLink(roomId: number | string): Promise<RoomShareLinkResponse> {
  const response = await apiClient.get<RoomShareLinkResponse>(`/recruitment/rooms/${roomId}/link/`);
  return response.data;
}

/**
 * Deactivate a room share link, preventing public submissions (US-21-T5).
 */
export async function apiDeactivateRoomShareLink(roomId: number | string): Promise<RoomShareLinkResponse> {
  const response = await apiClient.post<RoomShareLinkResponse>(`/recruitment/rooms/${roomId}/link/deactivate/`);
  return response.data;
}

/**
 * Reactivate a room share link (US-21-T5).
 */
export async function apiActivateRoomShareLink(roomId: number | string): Promise<RoomShareLinkResponse> {
  const response = await apiClient.post<RoomShareLinkResponse>(`/recruitment/rooms/${roomId}/link/activate/`);
  return response.data;
}

/**
 * Regenerate a new secure token, invalidating the previous link (US-21-T5).
 */
export async function apiRegenerateRoomShareLink(roomId: number | string): Promise<RoomShareLinkResponse> {
  const response = await apiClient.post<RoomShareLinkResponse>(`/recruitment/rooms/${roomId}/link/regenerate/`);
  return response.data;
}

/**
 * Resolve a public application token without authentication (US-21-T3).
 */
export async function apiGetPublicRoomByToken(token: string): Promise<PublicRoomDetails> {
  const response = await apiClient.get<PublicRoomDetails>(`/recruitment/apply/${token}/`);
  return response.data;
}



