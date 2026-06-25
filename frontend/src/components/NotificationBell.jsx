import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.listRaw('notifications');
      setItems(data.results || data);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const timer = setInterval(load, 60000);
    return () => clearInterval(timer);
  }, [load]);

  const unread = items.filter((n) => !n.is_read).length;

  const markRead = async (id) => {
    await api.update('notifications', id, { is_read: true });
    load();
  };

  const markAllRead = async () => {
    await api.collectionAction('notifications', 'mark_all_read', {});
    load();
  };

  return (
    <div className="dropdown">
      <button
        type="button"
        className="btn btn-link position-relative text-decoration-none"
        onClick={() => { setOpen((v) => !v); if (!open) load(); }}
        aria-label="Notifications"
      >
        <i className="bi bi-bell fs-5" />
        {unread > 0 && (
          <span className="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">
            {unread}
          </span>
        )}
      </button>

      {open && (
        <>
          <div className="notification-backdrop" onClick={() => setOpen(false)} aria-hidden="true" />
          <div className="notification-panel card shadow">
            <div className="card-header d-flex justify-content-between align-items-center py-2">
              <strong>Notifications</strong>
              {unread > 0 && (
                <button type="button" className="btn btn-link btn-sm" onClick={markAllRead}>
                  Mark all read
                </button>
              )}
            </div>
            <div className="list-group list-group-flush notification-list">
              {loading ? (
                <div className="p-3 text-center text-muted">Loading...</div>
              ) : items.length === 0 ? (
                <div className="p-3 text-muted">No notifications.</div>
              ) : (
                items.slice(0, 15).map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    className={`list-group-item list-group-item-action text-start ${item.is_read ? '' : 'fw-semibold'}`}
                    onClick={() => {
                      markRead(item.id);
                      if (item.link) setOpen(false);
                    }}
                  >
                    {item.link ? (
                      <Link to={item.link} className="text-decoration-none text-body stretched-link">
                        {item.title}
                      </Link>
                    ) : (
                      item.title
                    )}
                    <div className="small text-muted">{item.message}</div>
                    <div className="small text-muted">{new Date(item.created_at).toLocaleString()}</div>
                  </button>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
