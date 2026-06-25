import { Link } from 'react-router-dom';

const STAT_VARIANTS = {
  green: 'stat-card--green text-white',
  lime: 'stat-card--lime',
  sage: 'stat-card--sage text-white',
  red: 'stat-card--red text-white',
  dark: 'stat-card--dark text-white',
};

function StatCard({ title, value, variant = 'green', linkTo, linkLabel = 'View All' }) {
  return (
    <div className="col-md-3">
      <div className={`card mb-3 stat-card ${STAT_VARIANTS[variant]}`}>
        <div className="card-body">
          <h5 className="card-title">{title}</h5>
          <p className="card-text fs-5">{value}</p>
          {linkTo && (
            <Link to={linkTo} className="btn btn-light btn-sm">
              {linkLabel}
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}

function LeaveBalanceCard({ balance }) {
  const borderColor =
    balance.available_days > 0
      ? 'var(--fca-lime)'
      : balance.available_days === 0
        ? 'var(--fca-lime-light)'
        : 'var(--fca-red)';

  return (
    <div className="col-md-6 col-lg-4">
      <div className="card mb-3 leave-card" style={{ borderLeftColor: borderColor }}>
        <div className="card-body">
          <h5 className="card-title">{balance.leave_type_display}</h5>
          <div className="row g-3">
            {[
              ['Used', balance.used_days.toFixed(1)],
              ['Pending', balance.pending_days.toFixed(1)],
              ['Available', balance.available_days.toFixed(1)],
              ['Total', balance.total_days],
            ].map(([label, val]) => (
              <div className="col-6" key={label}>
                <div className="text-center p-2 leave-stat rounded">
                  <small className="text-muted d-block">{label}</small>
                  <strong className="fs-5">{val}</strong>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function SectionTitle({ icon, children }) {
  return (
    <h4 className="section-heading mb-3">
      <i className={`bi ${icon}`} />
      {children}
    </h4>
  );
}

function RoleHighlights({ highlights }) {
  if (!highlights?.length) return null;
  return (
    <div className="row mt-4">
      <div className="col-12"><SectionTitle icon="bi-speedometer2">Quick Actions</SectionTitle></div>
      {highlights.map((item) => (
        <StatCard key={item.label} title={item.label} value={item.value} variant="lime" linkTo={item.link} />
      ))}
    </div>
  );
}

function EmployeeDashboard({ data }) {
  return (
    <>
      <RoleHighlights highlights={data.highlights} />
      {data.user_leave_balances?.length > 0 && (
        <div className="row mt-4">
          <div className="col-12"><SectionTitle icon="bi-calendar-check">Your Leave Balance</SectionTitle></div>
          {data.user_leave_balances.map((balance) => (
            <LeaveBalanceCard key={balance.leave_type} balance={balance} />
          ))}
        </div>
      )}
      <div className="row mt-4">
        <StatCard title="Active Courses" value={data.active_courses} variant="sage" linkTo="/training" />
        <StatCard title="Active Goals" value={`${data.active_goals}/${data.total_goals}`} variant="green" linkTo="/performance" />
      </div>
    </>
  );
}

function ManagerDashboard({ data }) {
  return (
    <>
      <RoleHighlights highlights={data.highlights} />
      {data.dept_leave_summary && (
        <div className="row mt-4">
          <div className="col-12"><SectionTitle icon="bi-building">Department Leave Summary</SectionTitle></div>
          <StatCard title="Total Used" value={`${data.dept_leave_summary.total_used.toFixed(1)} days`} variant="green" />
          <StatCard title="Pending Approval" value={`${data.dept_leave_summary.total_pending.toFixed(1)} days`} variant="red" />
          <StatCard title="Available" value={`${data.dept_leave_summary.total_available.toFixed(1)} days`} variant="lime" />
          <StatCard title="Employees" value={data.dept_leave_summary.employee_count} variant="sage" />
        </div>
      )}
      <div className="row mt-4">
        <StatCard title="Pending Leaves" value={data.pending_leaves} variant="red" linkTo="/leaves" />
        <StatCard title="Open Jobs" value={data.open_jobs} variant="dark" linkTo="/recruitment" />
      </div>
    </>
  );
}

function HRDashboard({ data }) {
  const exec = data.exec_summary || {};
  return (
    <>
      <RoleHighlights highlights={data.highlights} />
      <div className="row mt-4">
        <div className="col-12"><SectionTitle icon="bi-graph-up">Executive Summary</SectionTitle></div>
        <StatCard title="Headcount" value={exec.headcount ?? data.total_employees} variant="green" linkTo="/employees" />
        <StatCard title="New Joiners (30d)" value={exec.new_joiners_30d ?? 0} variant="lime" />
        <StatCard title="Monthly Payroll (Net)" value={Number(exec.monthly_payroll_net || 0).toLocaleString()} variant="sage" linkTo="/payroll" />
        <StatCard title="Open Positions" value={exec.open_positions ?? data.open_jobs} variant="dark" linkTo="/recruitment" />
        <StatCard title="Pending Applications" value={exec.pending_applications ?? 0} variant="red" linkTo="/recruitment" />
        <StatCard title="Pending Expenses" value={exec.pending_expenses ?? 0} variant="red" linkTo="/expenses" />
      </div>

      <div className="row mt-4">
        <StatCard title="Employees" value={data.total_employees} variant="green" linkTo="/employees" />
        <StatCard title="Departments" value={data.total_departments} variant="lime" linkTo="/org-chart" />
        <StatCard title="Pending Leaves" value={data.pending_leaves} variant="red" linkTo="/leaves" />
        <StatCard title="Pending Approvals" value={data.pending_approvals ?? 0} variant="dark" linkTo="/leaves" />
      </div>

      {data.all_leave_summary && (
        <div className="row mt-4">
          <div className="col-12"><SectionTitle icon="bi-graph-up">Organization Leave Summary</SectionTitle></div>
          <StatCard title="Total Allocated" value={`${data.all_leave_summary.total_allocated.toFixed(1)} days`} variant="green" />
          <StatCard title="Total Used" value={`${data.all_leave_summary.total_used.toFixed(1)} days`} variant="red" />
          <StatCard title="Pending Approval" value={`${data.all_leave_summary.total_pending.toFixed(1)} days`} variant="dark" />
          <StatCard title="Available" value={`${data.all_leave_summary.total_available.toFixed(1)} days`} variant="lime" />
        </div>
      )}

      <div className="row mt-4">
        <div className="col-12"><SectionTitle icon="bi-graph-up-arrow">Performance Management</SectionTitle></div>
        <StatCard title="Active Goals" value={`${data.active_goals}/${data.total_goals}`} variant="sage" linkTo="/performance" />
        <StatCard title="Appraisals" value={data.total_appraisals} variant="green" linkTo="/performance" />
      </div>

      <div className="row mt-4">
        <div className="col-12"><SectionTitle icon="bi-book">Training & Development</SectionTitle></div>
        <StatCard title="Active Courses" value={data.active_courses} variant="lime" linkTo="/training" />
        <StatCard title="Upcoming Courses" value={data.upcoming_courses} variant="green" linkTo="/training" />
        <StatCard title="Employees Trained" value={data.total_employees_trained} variant="sage" linkTo="/training" />
        <StatCard title="Expiring Certs" value={data.expiring_certifications} variant="red" linkTo="/training" />
        <StatCard title="Active Plans" value={data.active_development_plans} variant="dark" linkTo="/training" />
      </div>
    </>
  );
}

export default function Dashboard({ data, user }) {
  const role = data.dashboard_role || (user?.is_admin ? 'hr' : user?.is_manager ? 'manager' : 'employee');
  const roleLabel = { employee: 'Employee', manager: 'Manager', hr: 'HR / Executive' }[role] || role;

  return (
    <>
      <h2 className="page-heading">Welcome, {user?.first_name || user?.username}</h2>
      <p className="page-subheading">Dashboard: {roleLabel}</p>

      {role === 'employee' && <EmployeeDashboard data={data} />}
      {role === 'manager' && <ManagerDashboard data={data} />}
      {role === 'hr' && <HRDashboard data={data} />}
    </>
  );
}
