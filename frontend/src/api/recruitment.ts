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
  shortlist_strategy?: 'NONE' | 'MIN_SCORE' | 'TOP_N' | 'COMBINED';
  shortlist_strategy_display?: string;
  shortlist_min_score?: number | null;
  shortlist_top_n?: number | null;
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

export interface ApplicationSubmissionResponse {
  message: string;
  application_id: number;
}

/**
 * Submit candidate application (US-22).
 */
export async function apiSubmitApplication(
  token: string,
  formData: FormData
): Promise<ApplicationSubmissionResponse> {
  const response = await apiClient.post<ApplicationSubmissionResponse>(
    `/recruitment/apply/${token}/submit/`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data;
}

// ==========================================
// US-10: Applicant CV Match Scores APIs
// ==========================================

export interface ApplicantCvScoreItem {
  application_id: number;
  candidate_id: number;
  candidate_name: string;
  candidate_email: string;
  cv_id: number | null;
  cv_filename: string | null;
  cv_file_url: string | null;
  has_cv: boolean;
  has_score: boolean;
  match_score: number | null;
  keyword_coverage: number;
  category_scores: {
    domain_craft?: number;
    collaboration?: number;
    leadership?: number;
    accessibility?: number;
    [key: string]: number | undefined;
  };
  skills_matched: string[];
  skills_missing: string[];
  strengths: string[];
  gaps: string[];
  recommendations: string[];
  applied_at: string;
  status: string;
  // US-23: Calculated scores
  final_score?: number | null;
  cv_score?: number | null;
  video_score?: number | null;
  is_partial_score?: boolean;
  score_calculated_at?: string | null;
}

export interface RoomCvScoresResponse {
  room_id: number;
  room_title: string;
  company_name: string;
  department: string;
  total_applicants: number;
  scored_applicants: number;
  average_cv_score: number | null;
  highest_cv_score: number | null;
  lowest_cv_score: number | null;
  results: ApplicantCvScoreItem[];
}

/**
 * US-10-T2: Fetch applicants' CV Match Scores for a specific Room.
 */
export async function apiGetRoomCvScores(
  roomId: number | string,
  params?: { search?: string; min_score?: number }
): Promise<RoomCvScoresResponse> {
  const queryParts: string[] = [];
  if (params?.search) {
    queryParts.push(`search=${encodeURIComponent(params.search)}`);
  }
  if (params?.min_score !== undefined) {
    queryParts.push(`min_score=${params.min_score}`);
  }
  const queryString = queryParts.length > 0 ? `?${queryParts.join('&')}` : '';
  const response = await apiClient.get<RoomCvScoresResponse>(
    `/recruitment/rooms/${roomId}/cv-scores/${queryString}`
  );
  return response.data;
}

/**
 * US-10-T4: Fetch detailed CV score and skill breakdown for a single applicant in a room.
 */
export async function apiGetApplicantCvScoreDetail(
  roomId: number | string,
  applicationId: number | string
): Promise<ApplicantCvScoreItem> {
  const response = await apiClient.get<ApplicantCvScoreItem>(
    `/recruitment/rooms/${roomId}/cv-scores/${applicationId}/`
  );
  return response.data;
}

// ==========================================
// US-23: Final Applicant Score Calculation APIs
// ==========================================

export interface CalculateScoresResponse {
  message: string;
  room_id: number;
  weights_used: {
    cv_weight: number;
    video_weight: number;
  };
  processed_count: number;
  updated_count: number;
}

/**
 * US-23-T5: Batch recalculate Final Applicant Scores for all candidates in a Room.
 */
export async function apiCalculateRoomScores(
  roomId: number | string
): Promise<CalculateScoresResponse> {
  const response = await apiClient.post<CalculateScoresResponse>(
    `/recruitment/rooms/${roomId}/calculate-scores/`
  );
  return response.data;
}

// ==========================================
// US-24: Applicant Ranking APIs
// ==========================================

export interface RankedApplicantItem {
  rank: number;
  badge: 'GOLD' | 'SILVER' | 'BRONZE' | 'STANDARD';
  application_id: number;
  candidate_id: number;
  candidate_name: string;
  candidate_email: string;
  final_score: number;
  score_tier: 'TIER_HIGH' | 'TIER_MEDIUM' | 'TIER_LOW' | 'TIER_PENDING';
  cv_score: number | null;
  video_score: number | null;
  is_partial_score: boolean;
  score_calculated_at: string | null;
  status: string;
  applied_at: string;
}

export interface UnrankedApplicantItem {
  application_id: number;
  candidate_id: number;
  candidate_name: string;
  candidate_email: string;
  final_score: null;
  score_tier: 'TIER_PENDING';
  cv_score: number | null;
  video_score: number | null;
  is_partial_score: boolean;
  status: string;
  applied_at: string;
  pending_reason: string;
}

export interface RankedApplicantsResponse {
  room_id: number;
  room_title: string;
  company_name: string;
  department: string;
  cv_weight: number;
  video_weight: number;
  total_applicants: number;
  ranked_count: number;
  unranked_count: number;
  results: RankedApplicantItem[];
  unranked: UnrankedApplicantItem[];
}

export interface RankedApplicantsQueryParams {
  min_score?: number;
  max_score?: number;
  search?: string;
  status?: string;
  ordering?: string;
  include_unranked?: boolean;
}

/**
 * US-24-T2: Fetch ranked applicant leaderboard for a Room.
 */
export async function apiGetRankedApplicants(
  roomId: number | string,
  params?: RankedApplicantsQueryParams
): Promise<RankedApplicantsResponse> {
  const queryParts: string[] = [];
  if (params?.min_score !== undefined) {
    queryParts.push(`min_score=${params.min_score}`);
  }
  if (params?.max_score !== undefined) {
    queryParts.push(`max_score=${params.max_score}`);
  }
  if (params?.search) {
    queryParts.push(`search=${encodeURIComponent(params.search)}`);
  }
  if (params?.status) {
    queryParts.push(`status=${encodeURIComponent(params.status)}`);
  }
  if (params?.ordering) {
    queryParts.push(`ordering=${encodeURIComponent(params.ordering)}`);
  }
  if (params?.include_unranked !== undefined) {
    queryParts.push(`include_unranked=${params.include_unranked}`);
  }
  const queryString = queryParts.length > 0 ? `?${queryParts.join('&')}` : '';
  const response = await apiClient.get<RankedApplicantsResponse>(
    `/recruitment/rooms/${roomId}/ranked-applicants/${queryString}`
  );
  return response.data;
}

// ==========================================
// US-25: Automatic Candidate Shortlisting APIs
// ==========================================

export type ShortlistStrategyType = 'NONE' | 'MIN_SCORE' | 'TOP_N' | 'COMBINED';

export interface RoomShortlistCriteriaPayload {
  shortlist_strategy: ShortlistStrategyType;
  shortlist_min_score?: number | null;
  shortlist_top_n?: number | null;
}

export interface RoomShortlistCriteriaResponse {
  room_id: number;
  title: string;
  company_name: string;
  criteria: {
    id: number;
    title: string;
    company_name: string;
    shortlist_strategy: ShortlistStrategyType;
    shortlist_strategy_display: string;
    shortlist_min_score: number | null;
    shortlist_top_n: number | null;
    updated_at: string;
  };
  shortlisted_count: number;
  total_applicants: number;
}

export interface ShortlistedApplicantItem {
  application_id: number;
  candidate_id: number;
  candidate_name: string;
  candidate_email: string;
  rank: number | null;
  final_score: number | null;
  cv_score: number | null;
  video_score: number | null;
  is_shortlisted: boolean;
  shortlist_reason: string;
  shortlisted_at: string | null;
}

export interface RoomShortlistResponse {
  room_id: number;
  room_title: string;
  strategy: ShortlistStrategyType;
  min_score: number | null;
  top_n: number | null;
  total_applicants: number;
  shortlisted_count: number;
  non_shortlisted_count: number;
  shortlisted_applicants: ShortlistedApplicantItem[];
  all_applicants: ShortlistedApplicantItem[];
}

/**
 * US-25-T2: Fetch current shortlisting criteria and summary for a Room.
 */
export async function apiGetRoomShortlistCriteria(
  roomId: number | string
): Promise<RoomShortlistCriteriaResponse> {
  const response = await apiClient.get<RoomShortlistCriteriaResponse>(
    `/recruitment/rooms/${roomId}/shortlist-criteria/`
  );
  return response.data;
}

/**
 * US-25-T2: Configure shortlisting criteria (min score, top N, combined) for a Room.
 */
export async function apiUpdateRoomShortlistCriteria(
  roomId: number | string,
  payload: RoomShortlistCriteriaPayload
): Promise<{ message: string; criteria: any; shortlist_summary: any }> {
  const response = await apiClient.patch<{ message: string; criteria: any; shortlist_summary: any }>(
    `/recruitment/rooms/${roomId}/shortlist-criteria/`,
    payload
  );
  return response.data;
}

/**
 * US-25-T3: Explicitly re-evaluate automatic candidate shortlisting for a Room.
 */
export async function apiEvaluateRoomShortlist(
  roomId: number | string
): Promise<{ message: string; evaluation: RoomShortlistResponse }> {
  const response = await apiClient.post<{ message: string; evaluation: RoomShortlistResponse }>(
    `/recruitment/rooms/${roomId}/shortlist-evaluate/`
  );
  return response.data;
}

/**
 * US-25-T4: Retrieve shortlisted applicants and full shortlist results for a Room.
 */
export async function apiGetShortlistedApplicants(
  roomId: number | string,
  includeAll: boolean = true
): Promise<RoomShortlistResponse> {
  const response = await apiClient.get<RoomShortlistResponse>(
    `/recruitment/rooms/${roomId}/shortlisted-applicants/?include_all=${includeAll}`
  );
  return response.data;
}


// ============================================================================
// US-26: HR Candidate Review of AI Results & Human Decision APIs
// ============================================================================

export type HrDecisionType = 'UNDECIDED' | 'CONFIRMED' | 'OVERRIDDEN' | 'REJECTED' | 'ON_HOLD';

export interface CandidateReviewCvSummary {
  has_cv: boolean;
  cv_filename: string | null;
  cv_score: number | null;
  skills_matched: string[];
  skills_missing: string[];
  match_score: number | null;
  keyword_coverage?: number;
}

export interface CandidateReviewVideoSummary {
  has_video: boolean;
  video_score: number | null;
  grade_label: string;
  speech_score: number | null;
  visual_score: number | null;
  filler_words_count: number;
  wpm: number;
  summary: string;
  strengths: string[];
  improvements: { category?: string; observation?: string; actionable_drill?: string }[];
}

export interface CandidateReviewDetail {
  application_id: number;
  room_id: number;
  room_title: string;
  candidate_id: number;
  candidate_name: string;
  candidate_email: string;
  status: string;
  applied_at: string;
  final_score: number | null;
  cv_score: number | null;
  video_score: number | null;
  cv_weight: number;
  video_weight: number;
  is_partial_score: boolean;
  score_calculated_at: string | null;
  is_shortlisted: boolean;
  shortlist_reason: string;
  shortlisted_at: string | null;
  ai_recommendation: 'RECOMMENDED_SHORTLIST' | 'NOT_RECOMMENDED';
  ai_recommendation_label: string;
  ai_disclaimer: string;
  cv_summary: CandidateReviewCvSummary;
  video_summary: CandidateReviewVideoSummary;
  hr_decision: HrDecisionType;
  hr_decision_display: string;
  hr_decision_notes: string;
  hr_decided_by_email: string | null;
  hr_decided_by_name: string | null;
  hr_decided_at: string | null;
}

export interface CandidateDecisionPayload {
  decision: 'CONFIRMED' | 'OVERRIDDEN' | 'REJECTED' | 'ON_HOLD';
  notes?: string;
}

export interface CandidateDecisionResponse {
  application_id: number;
  hr_decision: string;
  hr_decision_display: string;
  hr_decision_notes: string;
  hr_decided_by: string;
  hr_decided_at: string;
  is_shortlisted: boolean;
  message: string;
}

/**
 * US-26-T2: Fetch complete candidate review details (CV, video, AI recommendation, and HR decision history).
 */
export async function apiGetCandidateReviewDetail(
  applicationId: number | string
): Promise<CandidateReviewDetail> {
  const response = await apiClient.get<CandidateReviewDetail>(
    `/recruitment/applications/${applicationId}/review/`
  );
  return response.data;
}

/**
 * US-26-T3: Submit authoritative HR hiring decision (Confirm, Override, Reject, Hold).
 */
export async function apiSubmitCandidateDecision(
  applicationId: number | string,
  payload: CandidateDecisionPayload
): Promise<CandidateDecisionResponse> {
  const response = await apiClient.post<CandidateDecisionResponse>(
    `/recruitment/applications/${applicationId}/decision/`,
    payload
  );
  return response.data;
}

// ============================================================================
// US-27: Explainable Applicant Score Breakdown & Transparency
// ============================================================================

export interface ScoreComponentContribution {
  name: string;
  is_available: boolean;
  raw_score: number | null;
  weight_percentage: number;
  points_contributed: number | null;
  max_points_possible: number;
  percentage_of_total: number | null;
  missing_reason?: string | null;
  sub_metrics?: Record<string, any>;
}

export interface ApplicantScoreBreakdown {
  application_id: number;
  candidate_id: number;
  candidate_name: string;
  candidate_email: string;
  room_id: number;
  room_title: string;
  final_score: number | null;
  is_partial_score: boolean;
  score_calculated_at: string | null;
  cv_weight: number;
  video_weight: number;
  formula_display: string;
  missing_components_explanation?: string | null;
  cv_component: ScoreComponentContribution;
  video_component: ScoreComponentContribution;
}

/**
 * US-27-T4: Fetch explainable score breakdown and mathematical point contributions.
 */
export async function apiGetApplicantScoreBreakdown(
  applicationId: number | string
): Promise<ApplicantScoreBreakdown> {
  const response = await apiClient.get<ApplicantScoreBreakdown>(
    `/recruitment/applications/${applicationId}/score-breakdown/`
  );
  return response.data;
}

// ============================================================================
// US-28: Side-by-Side Applicant Comparison
// ============================================================================

export interface ApplicantComparisonItem {
  application_id: number;
  candidate_id: number;
  candidate_name: string;
  email: string;
  avatar_initials: string;
  final_score: number | null;
  score_tier: string;
  is_partial_score: boolean;
  cv_score: number | null;
  video_score: number | null;
  matched_skills: string[];
  missing_skills: string[];
  keyword_coverage: number;
  wpm: number;
  eye_contact_percent: number | null;
  posture_score: number | null;
  filler_words_count: number;
  speech_score: number | null;
  visual_score: number | null;
  is_shortlisted: boolean;
  shortlist_reason: string;
  hr_decision: string;
  hr_decision_display: string;
  applied_at: string;
  best_in: string[];
}

export interface ApplicantComparisonResponse {
  room_id: number;
  room_title: string;
  company_name: string;
  cv_weight: number;
  video_weight: number;
  comparison_count: number;
  highest_final_score: number | null;
  average_final_score: number | null;
  applicants: ApplicantComparisonItem[];
}

/**
 * US-28-T2: Fetch side-by-side comparison for 2 to 4 candidates in a room.
 */
export async function apiCompareApplicants(
  roomId: number | string,
  applicationIds: number[]
): Promise<ApplicantComparisonResponse> {
  const response = await apiClient.post<ApplicantComparisonResponse>(
    `/recruitment/rooms/${roomId}/compare-applicants/`,
    { application_ids: applicationIds }
  );
  return response.data;
}

// ============================================================================
// US-29: Agency Client Company Management Types & APIs
// ============================================================================

export interface ClientCompany {
  id: number;
  agency_id: number;
  agency_name: string;
  agency_email: string;
  name: string;
  industry: string;
  contact_person: string;
  contact_email: string;
  phone?: string;
  website?: string;
  notes?: string;
  is_active: boolean;
  rooms_count: number;
  created_at: string;
  updated_at: string;
}

export interface ClientCompanyCreatePayload {
  name: string;
  industry: string;
  contact_person: string;
  contact_email: string;
  phone?: string;
  website?: string;
  notes?: string;
}

export interface ClientCompanyUpdatePayload {
  name?: string;
  industry?: string;
  contact_person?: string;
  contact_email?: string;
  phone?: string;
  website?: string;
  notes?: string;
  is_active?: boolean;
}

export interface AgencyClientStats {
  total_clients: number;
  active_clients: number;
  deactivated_clients: number;
  associated_rooms: number;
}

export interface ToggleActiveResponse {
  message: string;
  is_active: boolean;
  client: ClientCompany;
}

/**
 * US-29-T2: Fetch list of client companies for the authenticated Agency Admin.
 */
export async function apiGetAgencyClients(params?: {
  q?: string;
  industry?: string;
  status?: string;
}): Promise<ClientCompany[]> {
  const response = await apiClient.get<ClientCompany[]>('/recruitment/agency/clients/', {
    params,
  });
  return response.data;
}

/**
 * US-29-T2: Fetch single client company details.
 */
export async function apiGetAgencyClient(id: number | string): Promise<ClientCompany> {
  const response = await apiClient.get<ClientCompany>(`/recruitment/agency/clients/${id}/`);
  return response.data;
}

/**
 * US-29-T2: Create a new client company.
 */
export async function apiCreateAgencyClient(
  payload: ClientCompanyCreatePayload
): Promise<ClientCompany> {
  const response = await apiClient.post<ClientCompany>('/recruitment/agency/clients/', payload);
  return response.data;
}

/**
 * US-29-T2: Update an existing client company.
 */
export async function apiUpdateAgencyClient(
  id: number | string,
  payload: ClientCompanyUpdatePayload
): Promise<ClientCompany> {
  const response = await apiClient.patch<ClientCompany>(`/recruitment/agency/clients/${id}/`, payload);
  return response.data;
}

/**
 * US-29-T5: Toggle client company between Active and Deactivated.
 */
export async function apiToggleClientActive(
  id: number | string
): Promise<ToggleActiveResponse> {
  const response = await apiClient.post<ToggleActiveResponse>(
    `/recruitment/agency/clients/${id}/toggle-active/`
  );
  return response.data;
}

/**
 * US-29-T5: Delete a client company.
 */
export async function apiDeleteAgencyClient(id: number | string): Promise<void> {
  await apiClient.delete(`/recruitment/agency/clients/${id}/`);
}

/**
 * US-29-T4: Fetch high-level agency dashboard summary metrics.
 */
export async function apiGetAgencyClientStats(): Promise<AgencyClientStats> {
  const response = await apiClient.get<AgencyClientStats>(
    '/recruitment/agency/clients/summary-stats/'
  );
  return response.data;
}





