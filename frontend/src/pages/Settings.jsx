import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const ACCOUNT_LINKS = [
  {
    to: '/settings/security',
    icon: 'bi-shield-lock',
    title: 'Security',
    description: 'MFA setup and personal data export (GDPR).',
  },
];

const ADMIN_LINKS = [
  {
    to: '/settings/users',
    icon: 'bi-people-fill',
    title: 'Users',
    description: 'Accounts, roles, and access for your organization.',
  },
  {
    to: '/settings/ops',
    icon: 'bi-hdd-rack',
    title: 'Operations',
    description: 'Jobs, backups, SLOs, alerts, and runbooks.',
  },
  {
    to: '/settings/integrations',
    icon: 'bi-plug',
    title: 'Integrations',
    description: 'API keys, webhooks, and external connections.',
  },
  {
    to: '/settings/compliance',
    icon: 'bi-shield-check',
    title: 'Compliance',
    description: 'Retention, erasure, evidence packs, and vulnerability SLAs.',
  },
  {
    to: '/settings/sensitive-access',
    icon: 'bi-shield-exclamation',
    title: 'Sensitive access',
    description: 'Who viewed masked payroll and PII fields.',
  },
  {
    to: '/audit-logs',
    icon: 'bi-journal-text',
    title: 'Audit log',
    description: 'System activity history for administrators.',
  },
];

function SettingsCard({ to, icon, title, description }) {
  return (
    <div className="col-md-6 col-xl-4">
      <Link to={to} className="card h-100 text-decoration-none text-reset settings-card">
        <div className="card-body p-4">
          <h2 className="h5 card-title mb-2">
            <i className={`bi ${icon} me-2`} aria-hidden="true" />
            {title}
          </h2>
          <p className="card-text text-muted small mb-0">{description}</p>
        </div>
      </Link>
    </div>
  );
}

export default function Settings() {
  const { user } = useAuth();
  const isAdmin = Boolean(user?.is_admin);

  return (
    <div className="page-shell">
      <header className="page-header">
        <div className="page-header-main">
          <p className="page-eyebrow">Workspace</p>
          <h1 className="page-heading">
            <i className="bi bi-gear" aria-hidden="true" /> Settings
          </h1>
          <p className="page-subheading">
            {isAdmin
              ? 'Configure security, users, operations, and compliance for this organization.'
              : 'Manage your account security and privacy options.'}
          </p>
        </div>
      </header>

      <section className="mb-4" aria-labelledby="settings-account-heading">
        <h2 id="settings-account-heading" className="page-eyebrow mb-3">
          Account
        </h2>
        <div className="row g-3">
          {ACCOUNT_LINKS.map((link) => (
            <SettingsCard key={link.to} {...link} />
          ))}
        </div>
      </section>

      {isAdmin && (
        <section aria-labelledby="settings-admin-heading">
          <h2 id="settings-admin-heading" className="page-eyebrow mb-3">
            Administration
          </h2>
          <div className="row g-3">
            {ADMIN_LINKS.map((link) => (
              <SettingsCard key={link.to} {...link} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
