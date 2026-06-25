import { Link } from 'react-router-dom';

const TYPE_ICONS = {
  leave: 'bi-calendar-x',
  expense: 'bi-receipt',
  recruitment: 'bi-briefcase',
  approval: 'bi-inbox',
};

function formatWhen(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

export default function PendingPanel({ items = [], role }) {
  const title = role === 'employee' ? 'Your pending requests' : 'Needs your action';
  const emptyMessage = role === 'employee'
    ? 'No pending leave requests.'
    : 'Nothing awaiting approval — you are all caught up.';

  return (
    <div className="dashboard-panel h-100">
      <div className="dashboard-panel-header">
        <h5 className="mb-0">
          <i className="bi bi-inbox" /> {title}
        </h5>
        {(role === 'hr' || role === 'manager') && (
          <Link to="/approvals" className="small">View all</Link>
        )}
      </div>

      {items.length === 0 ? (
        <div className="dashboard-panel-empty">
          <i className="bi bi-check2-circle" />
          <p>{emptyMessage}</p>
        </div>
      ) : (
        <ul className="dashboard-pending-list">
          {items.map((item) => (
            <li key={`${item.type}-${item.id}`}>
              <Link to={item.link || '/approvals'} className="dashboard-pending-item">
                <span className="dashboard-pending-icon">
                  <i className={`bi ${TYPE_ICONS[item.type] || 'bi-dot'}`} />
                </span>
                <span className="dashboard-pending-body">
                  <strong>{item.title}</strong>
                  <span>{item.summary}</span>
                </span>
                {item.submitted_at && (
                  <span className="dashboard-pending-date">{formatWhen(item.submitted_at)}</span>
                )}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
