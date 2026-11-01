import { apiClient } from './auth';

export interface AIConsentPolicySection {
  id: string;
  title: string;
  icon: string;
  details: string;
}

export interface AIConsentPolicy {
  version: string;
  effective_date: string;
  title: string;
  summary: string;
  sections: AIConsentPolicySection[];
}

export interface AIConsentStatusResponse {
  has_consented: boolean;
  policy_version: string;
  consent_token?: string | null;
  consented_at?: string | null;
}

export interface AIConsentRecordResponse {
  status: 'recorded' | 'refused';
  agreed: boolean;
  message: string;
  policy_version: string;
  consent_token: string;
  timestamp: string;
}

const STORAGE_KEY = 'careerflow_ai_consent_token';

export function getStoredAIConsentToken(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

export function setStoredAIConsentToken(token: string): void {
  try {
    localStorage.setItem(STORAGE_KEY, token);
  } catch (e) {
    console.error('Failed to store AI consent token', e);
  }
}

export function clearStoredAIConsentToken(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (e) {
    console.error('Failed to clear AI consent token', e);
  }
}

export async function apiGetAIConsentPolicy(): Promise<AIConsentPolicy> {
  const res = await apiClient.get<AIConsentPolicy>('/core/ai-consent/policy/');
  return res.data;
}

export async function apiGetAIConsentStatus(token?: string): Promise<AIConsentStatusResponse> {
  const activeToken = token || getStoredAIConsentToken();
  const headers = activeToken ? { 'X-AI-Consent-Token': activeToken } : {};
  const res = await apiClient.get<AIConsentStatusResponse>('/core/ai-consent/status/', { headers });
  return res.data;
}

export async function apiRecordAIConsent(
  agreed: boolean,
  email?: string,
  policyVersion: string = 'v1.0'
): Promise<AIConsentRecordResponse> {
  const res = await apiClient.post<AIConsentRecordResponse>('/core/ai-consent/', {
    agreed,
    email,
    policy_version: policyVersion,
    consent_type: 'BIOMETRIC_EVALUATION',
  });
  if (res.data.agreed && res.data.consent_token) {
    setStoredAIConsentToken(res.data.consent_token);
  } else if (!res.data.agreed) {
    clearStoredAIConsentToken();
  }
  return res.data;
}

