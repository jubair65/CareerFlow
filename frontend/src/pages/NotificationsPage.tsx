import { useState, useEffect } from 'react';
import { useLocation } from 'wouter';
import {
  Bell,
  Check,
  CheckCircle2,
  FileText,
  Video,
  Info,
  AlertTriangle,
  Trash2,
  ExternalLink,
  ArrowLeft,
} from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import type { Notify } from '../components/dashboard/DashboardShared';
import {
  apiGetNotifications,
  apiMarkNotificationAsRead,
  apiMarkAllNotificationsAsRead,
  apiDeleteNotification,
  type NotificationItem,
} from '../api/notifications';

interface NotificationsPageProps {
  notify?: Notify;
}

export function NotificationsPage({ notify }: NotificationsPageProps) {
  const [, setLocation] = useLocation();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');
  const [isLoading, setIsLoading] = useState(true);

  const fetchNotifications = async () => {
    try {
      setIsLoading(true);
      const data = await apiGetNotifications();
      setNotifications(data.notifications || []);
      setUnreadCount(data.unread_count || 0);
    } catch (err: any) {
      notify?.(err?.response?.data?.error || 'Failed to load notifications', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  const handleMarkAsRead = async (id: number) => {
    try {
      await apiMarkNotificationAsRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
      notify?.('Notification marked as read', 'success');
    } catch {
      notify?.('Failed to update notification', 'error');
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await apiMarkAllNotificationsAsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
      notify?.('All notifications marked as read', 'success');
    } catch {
      notify?.('Failed to mark all as read', 'error');
    }
  };

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await apiDeleteNotification(id);
      setNotifications((prev) => prev.filter((n) => n.id !== id));
      notify?.('Notification removed', 'info');
    } catch {
      notify?.('Failed to delete notification', 'error');
    }
  };

  const handleItemClick = async (notif: NotificationItem) => {
    if (!notif.is_read) {
      await handleMarkAsRead(notif.id);
    }
    if (notif.link_url) {
      setLocation(notif.link_url);
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'CV_ANALYSIS_COMPLETE':
        return (
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#dce8e1] text-[#277254]">
            <FileText size={20} />
          </div>
        );
      case 'PRESENTATION_ANALYSIS_COMPLETE':
        return (
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#e5ebf5] text-[#253142]">
            <Video size={20} />
          </div>
        );
      case 'APPLICATION_STATUS':
        return (
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#fff4ca] text-[#7b6217]">
            <CheckCircle2 size={20} />
          </div>
        );
      case 'WARNING':
        return (
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#fee4e2] text-[#d92d20]">
            <AlertTriangle size={20} />
          </div>
        );
      default:
        return (
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#f5f1e6] text-[#526072]">
            <Info size={20} />
          </div>
        );
    }
  };

  const filteredNotifications = notifications.filter((n) =>
    filter === 'unread' ? !n.is_read : true
  );

  return (
    <AppShell activeNav="/notifications" notify={notify || (() => {})}>
      <div className="mx-auto max-w-4xl space-y-6">
        {/* Top Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold tracking-tight text-[#253142]">
                Notifications Center
              </h1>
              {unreadCount > 0 && (
                <span className="rounded-full bg-[#ee7564] px-2.5 py-0.5 text-xs font-bold text-white">
                  {unreadCount} unread
                </span>
              )}
            </div>
            <p className="mt-1 text-sm text-[#7b8490]">
              Stay updated on your AI CV parsing, video evaluations, and recruitment activity.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {unreadCount > 0 && (
              <button
                type="button"
                onClick={handleMarkAllRead}
                data-testid="button-mark-all-read-page"
                className="inline-flex items-center gap-1.5 rounded-xl border border-[#d9dbd1] bg-white px-3.5 py-2 text-xs font-semibold text-[#253142] shadow-sm hover:bg-[#faf7ef] transition-colors"
              >
                <Check size={14} className="text-[#277254]" />
                Mark all as read
              </button>
            )}
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-2 border-b border-[#d9dbd1] pb-3">
          <button
            type="button"
            onClick={() => setFilter('all')}
            className={`rounded-lg px-3 py-1.5 text-xs font-bold transition-colors ${
              filter === 'all'
                ? 'bg-[#253142] text-white'
                : 'text-[#6e7887] hover:bg-[#faf7ef]'
            }`}
          >
            All ({notifications.length})
          </button>
          <button
            type="button"
            onClick={() => setFilter('unread')}
            className={`rounded-lg px-3 py-1.5 text-xs font-bold transition-colors ${
              filter === 'unread'
                ? 'bg-[#253142] text-white'
                : 'text-[#6e7887] hover:bg-[#faf7ef]'
            }`}
          >
            Unread ({unreadCount})
          </button>
        </div>

        {/* Notification Cards */}
        {isLoading ? (
          <div className="flex h-48 items-center justify-center">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#253142] border-t-transparent" />
          </div>
        ) : filteredNotifications.length === 0 ? (
          <div
            data-testid="notifications-empty-state"
            className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-[#d9dbd1] bg-white p-12 text-center"
          >
            <div className="mb-4 grid h-12 w-12 place-items-center rounded-full bg-[#f5f1e6] text-[#7b8490]">
              <Bell size={24} />
            </div>
            <h3 className="text-base font-bold text-[#253142]">No notifications found</h3>
            <p className="mt-1 text-xs text-[#8a929c]">
              {filter === 'unread'
                ? "You don't have any unread notifications."
                : 'All system and AI analysis notifications will appear here.'}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredNotifications.map((notif) => (
              <div
                key={notif.id}
                onClick={() => handleItemClick(notif)}
                data-testid={`notification-card-${notif.id}`}
                className={`group relative flex cursor-pointer items-start justify-between gap-4 rounded-2xl border p-4 shadow-sm transition-all hover:border-[#253142]/30 hover:shadow-md ${
                  !notif.is_read
                    ? 'border-[#c2dbcd] bg-[#fbfaf5]'
                    : 'border-[#eef0e7] bg-white'
                }`}
              >
                <div className="flex items-start gap-4">
                  {getNotificationIcon(notif.notification_type)}
                  <div>
                    <div className="flex items-center gap-2">
                      <h4
                        className={`text-sm ${
                          !notif.is_read
                            ? 'font-bold text-[#253142]'
                            : 'font-semibold text-[#526072]'
                        }`}
                      >
                        {notif.title}
                      </h4>
                      {!notif.is_read && (
                        <span className="h-2 w-2 rounded-full bg-[#ee7564]" />
                      )}
                    </div>
                    <p className="mt-1 text-xs text-[#6e7887] leading-relaxed">
                      {notif.message}
                    </p>
                    <div className="mt-3 flex items-center gap-4 text-[11px] text-[#8a929c]">
                      <span>{new Date(notif.created_at).toLocaleString()}</span>
                      {notif.link_url && (
                        <span className="flex items-center gap-1 font-semibold text-[#277254]">
                          View details <ExternalLink size={11} />
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  {!notif.is_read && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleMarkAsRead(notif.id);
                      }}
                      title="Mark as read"
                      className="rounded-lg p-1.5 text-[#6e7887] hover:bg-[#eef0e7] hover:text-[#253142]"
                    >
                      <Check size={16} />
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={(e) => handleDelete(notif.id, e)}
                    title="Delete"
                    className="rounded-lg p-1.5 text-[#6e7887] hover:bg-[#fee4e2] hover:text-[#d92d20]"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}

