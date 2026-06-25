import { Link } from 'react-router-dom';

const SEVERITY_CLASS = {
  critical: 'dashboard-attention--critical',
  warning: 'dashboard-attention--warning',
  info: 'dashboard-attention--info',
};

export default function AttentionBanner({ items = [] }) {
  if (!items.length) {
    return (
      <div className="dashboard-attention dashboard-attention--clear">
        <i className="bi bi-check-circle-fill" />
        <span>All clear — no urgent items require executive attention.</span>
      </div>
    );
  }

  return (
    <div className="dashboard-attention-list">
      {items.map((item) => (
        <Link
          key={item.message}
          to={item.link || '/dashboard'}
          className={`dashboard-attention ${SEVERITY_CLASS[item.severity] || SEVERITY_CLASS.info}`}
        >
          <i className={`bi ${item.icon || 'bi-exclamation-circle'}`} />
          <span>{item.message}</span>
          <i className="bi bi-chevron-right ms-auto" />
        </Link>
      ))}
    </div>
  );
}
