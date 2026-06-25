import { Link } from 'react-router-dom';
import ActivityPanel from '../components/dashboard/ActivityPanel';
import AttentionBanner from '../components/dashboard/AttentionBanner';
import DashboardHero from '../components/dashboard/DashboardHero';
import ExecutiveBrief from '../components/dashboard/ExecutiveBrief';
import PendingPanel from '../components/dashboard/PendingPanel';
import RecruitmentFunnel from '../components/dashboard/RecruitmentFunnel';
import SimpleBarChart from '../components/dashboard/SimpleBarChart';
import TrendLineChart from '../components/dashboard/TrendLineChart';

function handlePrintDashboard() {
  window.print();
}

function MetricTile({ label, value, linkTo, icon }) {
  return (
    <div className="col-md-6 col-lg-3">
      <Link to={linkTo} className="dashboard-metric-tile">
        <i className={`bi ${icon}`} />
        <div>
          <div className="dashboard-metric-value">{value}</div>
          <div className="dashboard-metric-label">{label}</div>
        </div>
      </Link>
    </div>
  );
}

function LeaveBalanceCard({ balance }) {
  const pctUsed = balance.total_days
    ? Math.min(100, (balance.used_days / balance.total_days) * 100)
    : 0;

  return (
    <div className="col-md-6">
      <div className="dashboard-leave-card">
        <div className="d-flex justify-content-between align-items-start mb-2">
          <h6 className="mb-0">{balance.leave_type_display}</h6>
          <span className="badge bg-light text-dark">{balance.available_days.toFixed(1)} left</span>
        </div>
        <div className="dashboard-leave-progress">
          <div className="dashboard-leave-progress-fill" style={{ width: `${pctUsed}%` }} />
        </div>
        <div className="dashboard-leave-stats">
          <span>Used {balance.used_days.toFixed(1)}</span>
          <span>Pending {balance.pending_days.toFixed(1)}</span>
          <span>Total {balance.total_days}</span>
        </div>
      </div>
    </div>
  );
}

function ExecutiveDashboard({ data, user }) {
  const analytics = data.exec_analytics || {};
  const snapshot = data.workforce_snapshot || {};

  return (
    <>
      <DashboardHero
        user={user}
        role="hr"
        asOf={data.as_of}
        kpis={data.hero_kpis || []}
        onPrint={handlePrintDashboard}
      />

      <AttentionBanner items={data.attention_items || []} />
      <ExecutiveBrief text={data.exec_brief} />

      <div className="row g-4 mb-4 dashboard-print-section">
        <div className="col-lg-6">
          <div className="dashboard-panel h-100">
            <TrendLineChart series={analytics.headcount_trend} color="#004924" />
          </div>
        </div>
        <div className="col-lg-6">
          <div className="dashboard-panel h-100">
            <TrendLineChart series={analytics.payroll_trend} isCurrency color="#7fa491" />
          </div>
        </div>
      </div>

      <div className="row g-4 mb-4">
        <div className="col-lg-4">
          <div className="dashboard-panel h-100">
            <RecruitmentFunnel funnel={analytics.recruitment_funnel} />
          </div>
        </div>
        <div className="col-lg-4">
          <div className="dashboard-panel h-100">
            <TrendLineChart series={analytics.leave_trend} color="#a3d147" />
          </div>
        </div>
        <div className="col-lg-4">
          <PendingPanel items={data.pending_items || []} role="hr" />
        </div>
      </div>

      <div className="row g-4 mb-4">
        <div className="col-lg-5">
          <ActivityPanel items={data.recent_activity || []} />
        </div>
        <div className="col-lg-7">
          <div className="dashboard-panel">
            <div className="dashboard-panel-header">
              <h5 className="mb-0"><i className="bi bi-grid-3x3-gap" /> Workforce snapshot</h5>
              <Link to="/reports" className="small">Full reports</Link>
            </div>
            <div className="row g-3">
              <MetricTile label="Open positions" value={data.exec_summary?.open_positions ?? data.open_jobs} linkTo="/recruitment" icon="bi-briefcase" />
              <MetricTile label="Pending applications" value={data.exec_summary?.pending_applications ?? 0} linkTo="/recruitment" icon="bi-file-earmark-person" />
              <MetricTile label="Pending expenses" value={data.exec_summary?.pending_expenses ?? 0} linkTo="/expenses" icon="bi-receipt" />
              <MetricTile label="Departments" value={data.total_departments} linkTo="/org-chart" icon="bi-diagram-3" />
              <MetricTile label="Active goals" value={`${snapshot.active_goals}/${snapshot.total_goals}`} linkTo="/performance" icon="bi-bullseye" />
              <MetricTile label="Appraisals" value={snapshot.total_appraisals} linkTo="/performance" icon="bi-clipboard-check" />
              <MetricTile label="Active courses" value={snapshot.active_courses} linkTo="/training" icon="bi-book" />
              <MetricTile label="Expiring certs" value={snapshot.expiring_certifications} linkTo="/training" icon="bi-award" />
            </div>
            {snapshot.leave_allocated != null && (
              <div className="dashboard-snapshot-leave mt-3 pt-3 border-top">
                <div className="row g-3">
                  <MetricTile label="Leave allocated" value={`${snapshot.leave_allocated.toFixed(1)}d`} linkTo="/leave-policies" icon="bi-collection" />
                  <MetricTile label="Leave used" value={`${snapshot.leave_used.toFixed(1)}d`} linkTo="/leaves" icon="bi-calendar-check" />
                  <MetricTile label="Leave available" value={`${snapshot.leave_available.toFixed(1)}d`} linkTo="/leaves" icon="bi-calendar-plus" />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

function ManagerDashboard({ data, user }) {
  const analytics = data.exec_analytics || {};

  return (
    <>
      <DashboardHero user={user} role="manager" asOf={data.as_of} kpis={data.hero_kpis || []} />
      <AttentionBanner items={data.attention_items || []} />

      <div className="row g-4 mb-4">
        <div className="col-lg-8">
          <div className="dashboard-panel h-100">
            <SimpleBarChart chart={data.chart} />
          </div>
        </div>
        <div className="col-lg-4">
          <PendingPanel items={data.pending_items || []} role="manager" />
        </div>
      </div>

      <div className="row g-4">
        <div className="col-lg-6">
          {data.dept_leave_summary && (
            <div className="dashboard-panel">
              <div className="dashboard-panel-header">
                <h5 className="mb-0"><i className="bi bi-building" /> Department snapshot</h5>
                <Link to="/employees" className="small">View team</Link>
              </div>
              <div className="row g-3">
                <MetricTile label="Team members" value={data.dept_leave_summary.employee_count} linkTo="/employees" icon="bi-people" />
                <MetricTile label="Leave used" value={`${data.dept_leave_summary.total_used.toFixed(1)}d`} linkTo="/leaves" icon="bi-calendar-check" />
                <MetricTile label="Pending leave" value={`${data.dept_leave_summary.total_pending.toFixed(1)}d`} linkTo="/leaves" icon="bi-hourglass-split" />
                <MetricTile label="Available" value={`${data.dept_leave_summary.total_available.toFixed(1)}d`} linkTo="/leaves" icon="bi-calendar-plus" />
              </div>
            </div>
          )}
        </div>
        <div className="col-lg-6">
          {analytics.leave_trend && (
            <div className="dashboard-panel h-100">
              <TrendLineChart series={analytics.leave_trend} color="#004924" />
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function EmployeeDashboard({ data, user }) {
  return (
    <>
      <DashboardHero user={user} role="employee" asOf={data.as_of} kpis={data.hero_kpis || []} />
      <AttentionBanner items={data.attention_items || []} />

      <div className="row g-4 mb-4">
        <div className="col-lg-8">
          <div className="dashboard-panel h-100">
            <SimpleBarChart chart={data.chart} />
          </div>
        </div>
        <div className="col-lg-4">
          <PendingPanel items={data.pending_items || []} role="employee" />
        </div>
      </div>

      <div className="row g-4">
        <div className="col-lg-7">
          {data.user_leave_balances?.length > 0 && (
            <div className="dashboard-panel">
              <div className="dashboard-panel-header">
                <h5 className="mb-0"><i className="bi bi-calendar-check" /> Leave balances</h5>
                <Link to="/leaves" className="small">Manage leave</Link>
              </div>
              <div className="row g-3">
                {data.user_leave_balances.map((balance) => (
                  <LeaveBalanceCard key={balance.leave_type} balance={balance} />
                ))}
              </div>
            </div>
          )}
        </div>
        <div className="col-lg-5">
          <div className="dashboard-panel h-100">
            <div className="dashboard-panel-header">
              <h5 className="mb-0"><i className="bi bi-lightning" /> Quick links</h5>
            </div>
            <div className="dashboard-quick-links">
              {(data.highlights || []).map((item) => (
                <Link key={item.label} to={item.link} className="dashboard-quick-link">
                  <span>{item.label}</span>
                  <strong>{item.value}</strong>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default function Dashboard({ data, user }) {
  const role = data.dashboard_role || (user?.is_admin ? 'hr' : user?.is_manager ? 'manager' : 'employee');

  return (
    <div className="dashboard-page" id="dashboard-print-root">
      {role === 'hr' && <ExecutiveDashboard data={data} user={user} />}
      {role === 'manager' && <ManagerDashboard data={data} user={user} />}
      {role === 'employee' && <EmployeeDashboard data={data} user={user} />}
    </div>
  );
}
