import { Link } from 'react-router-dom';
import DeltaBadge from './DeltaBadge';

function formatAsOf(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

const ROLE_LABELS = {
  employee: 'Employee',
  manager: 'Manager',
  hr: 'Executive / HR',
};

export default function DashboardHero({ user, role, asOf, kpis = [], onPrint }) {
  const displayName = user?.first_name || user?.username;
  const isExecutive = role === 'hr';

  return (
    <div className={`dashboard-hero mb-4 ${isExecutive ? 'dashboard-hero--executive' : ''}`}>
      <div className="dashboard-hero-main">
        <div>
          <p className="dashboard-hero-eyebrow mb-1">
            {isExecutive ? 'Executive command center' : 'Overview'}
          </p>
          <h2 className="dashboard-hero-title mb-2">Welcome back, {displayName}</h2>
          <div className="dashboard-hero-meta">
            <span className="dashboard-role-badge">{ROLE_LABELS[role] || role}</span>
            {asOf && <span className="dashboard-as-of">Updated {formatAsOf(asOf)}</span>}
          </div>
        </div>
        {onPrint && (
          <button type="button" className="btn btn-light btn-sm dashboard-print-btn" onClick={onPrint}>
            <i className="bi bi-file-earmark-pdf" /> Export PDF
          </button>
        )}
      </div>

      {kpis.length > 0 && (
        <div className="dashboard-kpi-row">
          {kpis.map((kpi) => (
            <Link key={kpi.label} to={kpi.link || '/dashboard'} className="dashboard-kpi-card">
              <div className="dashboard-kpi-icon">
                <i className={`bi ${kpi.icon}`} />
              </div>
              <div className="dashboard-kpi-body">
                <div className="dashboard-kpi-value">{kpi.value}</div>
                <div className="dashboard-kpi-label">{kpi.label}</div>
                {kpi.delta && <DeltaBadge delta={kpi.delta} invert={kpi.label.includes('Pending')} />}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
