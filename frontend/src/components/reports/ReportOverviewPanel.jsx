import StatCard from './StatCard';

export default function ReportOverviewPanel({ overview, loading }) {
  if (loading) {
    return (
      <div className="report-loading" role="status">
        <div className="spinner-border text-primary" aria-hidden="true" />
        <span>Loading analytics…</span>
      </div>
    );
  }
  if (!overview) {
    return (
      <div className="report-empty">
        <i className="bi bi-cloud-slash" aria-hidden="true" />
        <p className="mb-0">Analytics are currently unavailable.</p>
      </div>
    );
  }
  return (
    <div className="row g-3">
      <StatCard title="Total employees" value={overview.total_employees} icon="bi-people" />
      <StatCard title="New joiners (30 days)" value={overview.new_joiners} icon="bi-person-plus" tone="lime" />
      <StatCard title="Present today" value={overview.present_today} icon="bi-person-check" tone="sage" />
      <StatCard title="Absent today" value={overview.absent_today} icon="bi-person-x" tone="red" />
      <StatCard title="Late today" value={overview.late_today} icon="bi-clock-history" />
      <StatCard title="Pending leaves" value={overview.pending_leaves} icon="bi-calendar2-week" tone="red" />
      <StatCard title="Leaves used (YTD)" value={overview.leaves_used_this_year} icon="bi-calendar2-check" />
      <StatCard title="Open positions" value={overview.open_positions} icon="bi-briefcase" tone="lime" />
      <StatCard title="Pending applications" value={overview.pending_applications} icon="bi-file-earmark-person" tone="sage" />
      <StatCard title="Active goals" value={overview.active_goals} icon="bi-bullseye" />
      <StatCard title="Appraisals due" value={overview.appraisals_due} icon="bi-clipboard2-data" tone="red" />
    </div>
  );
}
