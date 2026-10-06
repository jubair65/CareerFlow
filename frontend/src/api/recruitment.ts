import { apiClient } from './auth';

export interface RecruitmentRoom {
  id: number;
  title: string;
  company_name: string;
  department: string;
  description: string;
  status: 'ACTIVE' | 'PAUSED' | 'CLOSED';
  requirements_text: string;
  skills_required: string[];
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
