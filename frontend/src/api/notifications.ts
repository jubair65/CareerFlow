import { apiClient } from './auth';

export interface NotificationItem {
  id: number;
  title: string;
  message: string;
  link_url: string;
  notification_type:
    | 'INFO'
    | 'SUCCESS'
    | 'WARNING'
    | 'ERROR'
    | 'CV_ANALYSIS_COMPLETE'
    | 'PRESENTATION_ANALYSIS_COMPLETE'
    | 'APPLICATION_STATUS'
    | string;
  is_read: boolean;
  created_at: string;
}

export interface NotificationListResponse {
  unread_count: number;
  notifications: NotificationItem[];
}

/**
 * US-34: Fetch notifications and unread count for current user
 */
export async function apiGetNotifications(): Promise<NotificationListResponse> {
  const response = await apiClient.get<NotificationListResponse>('/notifications/');
  return response.data;
}

/**
 * US-34: Mark a single notification as read
 */
export async function apiMarkNotificationAsRead(
  id: number
): Promise<{ message: string; notification: NotificationItem }> {
  const response = await apiClient.post<{ message: string; notification: NotificationItem }>(
    `/notifications/${id}/read/`
  );
  return response.data;
}

/**
 * US-34: Mark all unread notifications as read
 */
export async function apiMarkAllNotificationsAsRead(): Promise<{
  message: string;
  updated_count: number;
}> {
  const response = await apiClient.post<{ message: string; updated_count: number }>(
    '/notifications/mark-all-read/'
  );
  return response.data;
}

/**
 * US-34: Delete a notification
 */
export async function apiDeleteNotification(
  id: number
): Promise<{ message: string }> {
  const response = await apiClient.delete<{ message: string }>(
    `/notifications/${id}/`
  );
  return response.data;
}

export const NOTIFICATIONS_UPDATED_EVENT = 'careerflow:notifications-updated';

export function notifyNotificationsUpdated(unreadCount?: number) {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(
      new CustomEvent(NOTIFICATIONS_UPDATED_EVENT, { detail: { unreadCount } })
    );
  }
}

export function onNotificationsUpdated(callback: (unreadCount?: number) => void) {
  if (typeof window === 'undefined') return () => {};
  const handler = (event: Event) => {
    const customEvent = event as CustomEvent<{ unreadCount?: number }>;
    callback(customEvent.detail?.unreadCount);
  };
  window.addEventListener(NOTIFICATIONS_UPDATED_EVENT, handler);
  return () => window.removeEventListener(NOTIFICATIONS_UPDATED_EVENT, handler);
}
