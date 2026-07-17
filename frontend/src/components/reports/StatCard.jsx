export default function StatCard({ title, value, icon = 'bi-graph-up', tone = 'green' }) {
  return (
    <div className="col-md-4 col-lg-3">
      <div className={`report-stat-card report-stat-card--${tone}`}>
        <div className="report-stat-icon" aria-hidden="true"><i className={`bi ${icon}`} /></div>
        <div>
          <p className="report-stat-value mb-1">{value}</p>
          <h2 className="report-stat-label mb-0">{title}</h2>
        </div>
      </div>
    </div>
  );
}
