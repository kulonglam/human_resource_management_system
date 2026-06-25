import { Link } from 'react-router-dom';

function formatWhen(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function ActivityPanel({ items = [] }) {
  if (!items.length) {
    return (
      <div className="dashboard-panel h-100">
        <div className="dashboard-panel-header">
          <h5 className="mb-0">
            <i className="bi bi-activity" /> Recent activity
          </h5>
        </div>
        <div className="dashboard-panel-empty">
          <i className="bi bi-journal-text" />
          <p>Audit activity appears here for HR administrators.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-panel h-100">
      <div className="dashboard-panel-header">
        <h5 className="mb-0">
          <i className="bi bi-activity" /> Recent activity
        </h5>
        <Link to="/audit-logs" className="small">Audit log</Link>
      </div>
      <ul className="dashboard-activity-list">
        {items.map((item) => (
          <li key={item.id}>
            <div className="dashboard-activity-item">
              <span className={`dashboard-activity-badge dashboard-activity-badge--${item.action}`}>
                {item.action}
              </span>
              <div className="dashboard-activity-body">
                <strong>{item.model_name}</strong>
                <span>{item.description}</span>
                <small>{item.username} · {formatWhen(item.timestamp)}</small>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
