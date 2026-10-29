import { useState, useEffect, useRef } from 'react';
import { useLocation } from 'wouter';
import {
  Bell,
  Check,
  CheckCircle2,
  FileText,
  Video,
  Info,
  AlertTriangle,
  X,
  ExternalLink,
} from 'lucide-react';
import {
  apiGetNotifications,
  apiMarkNotificationAsRead,
  apiMarkAllNotificationsAsRead,
  type NotificationItem,
} from '../../api/notifications';

interface NotificationCenterProps {
  onNotificationClick?: (linkUrl: string) => void;
}

function formatRelativeTime(dateString: string): string {
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);

    if (diffSec < 60) return 'Just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    if (diffHour < 24) return `${diffHour}h ago`;
    if (diffDay === 1) return 'Yesterday';
    if (diffDay < 7) return `${diffDay}d ago`;
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  } catch {
    return '';
  }
}

export function NotificationCenter({ onNotificationClick }: NotificationCenterProps) {
  const [, setLocation] = useLocation();
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(false);
  const popoverRef = useRef<HTMLDivElement>(null);

  const fetchNotifications = async () => {
    try {
      const data = await apiGetNotifications();
      setNotifications(data.notifications || []);
      setUnreadCount(data.unread_count || 0);
    } catch {
      // Silently ignore network or unauthorized errors in polling
    }
  };

  useEffect(() => {
    fetchNotifications();
    // Poll every 30 seconds
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  // Handle outside click to close popover
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (popoverRef.current && !popoverRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleToggle = () => {
    if (!isOpen) {
      fetchNotifications();
    }
    setIsOpen(!isOpen);
  };

  const handleItemClick = async (notif: NotificationItem) => {
    if (!notif.is_read) {
      try {
        await apiMarkNotificationAsRead(notif.id);
        setNotifications((prev) =>
          prev.map((item) => (item.id === notif.id ? { ...item, is_read: true } : item))
        );
        setUnreadCount((prev) => Math.max(0, prev - 1));
      } catch {
        // Continue even if mark as read fails
      }
    }

    setIsOpen(false);

    if (notif.link_url) {
      if (onNotificationClick) {
        onNotificationClick(notif.link_url);
      } else {
        setLocation(notif.link_url);
      }
    }
  };

  const handleMarkAllRead = async () => {
    try {
      setIsLoading(true);
      await apiMarkAllNotificationsAsRead();
      setNotifications((prev) => prev.map((item) => ({ ...item, is_read: true })));
      setUnreadCount(0);
    } catch {
      // Ignore
    } finally {
      setIsLoading(false);
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'CV_ANALYSIS_COMPLETE':
        return (
          <div className="grid h-8 w-8 place-items-center rounded-xl bg-[#dce8e1] text-[#277254]">
            <FileText size={16} />
          </div>
        );
      case 'PRESENTATION_ANALYSIS_COMPLETE':
        return (
          <div className="grid h-8 w-8 place-items-center rounded-xl bg-[#e5ebf5] text-[#253142]">
            <Video size={16} />
          </div>
        );
      case 'APPLICATION_STATUS':
        return (
          <div className="grid h-8 w-8 place-items-center rounded-xl bg-[#fff4ca] text-[#7b6217]">
            <CheckCircle2 size={16} />
          </div>
        );
      case 'WARNING':
        return (
          <div className="grid h-8 w-8 place-items-center rounded-xl bg-[#fee4e2] text-[#d92d20]">
            <AlertTriangle size={16} />
          </div>
        );
      default:
        return (
          <div className="grid h-8 w-8 place-items-center rounded-xl bg-[#f5f1e6] text-[#526072]">
            <Info size={16} />
          </div>
        );
    }
  };

  return (
    <div className="relative inline-block text-left" ref={popoverRef}>
      {/* Bell Trigger Button */}
      <button
        type="button"
        onClick={handleToggle}
        data-testid="button-header-notifications"
        aria-label="View notifications"
        aria-expanded={isOpen}
        className="relative rounded-xl p-2 text-[#526072] transition-colors hover:bg-[#eef0e7] focus:outline-none"
      >
        <Bell size={18} />
        {unreadCount > 0 && (
          <span
            data-testid="notification-bell-badge"
            className="absolute -top-0.5 -right-0.5 grid min-h-4 min-w-4 place-items-center rounded-full bg-[#ee7564] px-1 text-[10px] font-bold text-white shadow-sm ring-2 ring-white"
          >
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown Popover */}
      {isOpen && (
        <div
          data-testid="notification-popover"
          className="absolute right-0 mt-2 w-80 sm:w-96 rounded-2xl bg-white p-0 shadow-2xl ring-1 ring-black/5 z-50 border border-[#d9dbd1] overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-[#eef0e7] px-4 py-3 bg-[#faf7ef]">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-[#253142]">Notifications</h3>
              {unreadCount > 0 && (
                <span className="rounded-full bg-[#ee7564]/10 px-2 py-0.5 text-xs font-semibold text-[#ee7564]">
                  {unreadCount} unread
                </span>
              )}
            </div>
            {unreadCount > 0 && (
              <button
                type="button"
                onClick={handleMarkAllRead}
                disabled={isLoading}
                data-testid="button-mark-all-read"
                className="flex items-center gap-1 text-xs font-semibold text-[#277254] hover:text-[#1e5841] disabled:opacity-50 transition-colors"
              >
                <Check size={13} />
                Mark all read
              </button>
            )}
          </div>

          {/* List */}
          <div className="max-h-[360px] overflow-y-auto divide-y divide-[#f2f4ea]">
            {notifications.length === 0 ? (
              <div
                data-testid="notification-empty-state"
                className="px-6 py-10 text-center text-[#7b8490]"
              >
                <div className="mx-auto mb-3 grid h-10 w-10 place-items-center rounded-full bg-[#f5f1e6] text-[#8a929c]">
                  <Bell size={20} />
                </div>
                <p className="text-sm font-semibold text-[#253142]">No notifications yet</p>
                <p className="mt-1 text-xs text-[#8a929c]">
                  We&apos;ll notify you when your CV or presentation video analysis is complete.
                </p>
              </div>
            ) : (
              notifications.map((notif) => (
                <button
                  key={notif.id}
                  type="button"
                  onClick={() => handleItemClick(notif)}
                  data-testid={`notification-item-${notif.id}`}
                  className={`flex w-full items-start gap-3 p-3.5 text-left transition-colors hover:bg-[#faf7ef] ${
                    !notif.is_read ? 'bg-[#fbfaf5]' : 'bg-white'
                  }`}
                >
                  <div className="flex-shrink-0 pt-0.5">{getNotificationIcon(notif.notification_type)}</div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-1">
                      <p
                        className={`text-xs truncate ${
                          !notif.is_read ? 'font-bold text-[#253142]' : 'font-semibold text-[#526072]'
                        }`}
                      >
                        {notif.title}
                      </p>
                      <span className="flex-shrink-0 text-[10px] text-[#8a929c]">
                        {formatRelativeTime(notif.created_at)}
                      </span>
                    </div>
                    <p className="mt-0.5 text-xs text-[#6e7887] line-clamp-2 leading-relaxed">
                      {notif.message}
                    </p>
                    {notif.link_url && (
                      <span className="mt-1.5 inline-flex items-center gap-1 text-[11px] font-semibold text-[#277254]">
                        View details <ExternalLink size={10} />
                      </span>
                    )}
                  </div>
                  {!notif.is_read && (
                    <span
                      data-testid="notification-unread-dot"
                      className="mt-1.5 h-2 w-2 flex-shrink-0 rounded-full bg-[#ee7564]"
                    />
                  )}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

