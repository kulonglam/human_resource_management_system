import { useEffect, useState } from 'react';
import { api } from '../api/client';

function StatCard({ title, value, color = 'green' }) {
  return (
    <div className="col-md-4 col-lg-3">
      <div className={`card mb-3 stat-card stat-card--${color} text-white`}>
        <div className="card-body">
          <h6 className="card-title">{title}</h6>
          <p className="card-text fs-4 mb-0">{value}</p>
        </div>
      </div>
    </div>
  );
}

const REPORT_TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'attendance', label: 'Attendance' },
  { id: 'leave', label: 'Leave' },
  { id: 'payroll', label: 'Payroll' },
  { id: 'performance', label: 'Performance' },
  { id: 'recruitment', label: 'Recruitment' },
];

function ReportTable({ rows, columns }) {
  if (!rows?.length) {
    return <p className="text-muted mb-0">No records for the selected filters.</p>;
  }
  return (
    <div className="table-responsive">
      <table className="table table-sm table-hover mb-0">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key}>{col.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={row.id || idx}>
              {columns.map((col) => (
                <td key={col.key}>{row[col.key] ?? '—'}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function Reports() {
  const [activeTab, setActiveTab] = useState('overview');
  const [overview, setOverview] = useState(null);
  const [filters, setFilters] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const [form, setForm] = useState({
    date_range: 'this_month',
    start_date: '',
    end_date: '',
    department: '',
    status: '',
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    report_type: '',
    leave_type: '',
    rating: '',
    job_status: '',
  });

  useEffect(() => {
    api.getReportsAnalytics().then(setOverview).catch((err) => setError(err.message));
    api.getReportFilters().then(setFilters).catch(() => {});
  }, []);

  const runReport = async () => {
    setLoading(true);
    setError('');
    setReportData(null);
    try {
      const params = new URLSearchParams();
      Object.entries(form).forEach(([key, val]) => {
        if (val !== '' && val != null) params.set(key, val);
      });
      if (activeTab === 'attendance') {
        setReportData(await api.getReport('attendance', params.toString()));
      } else if (activeTab === 'leave') {
        params.set('report_type', form.report_type || 'summary');
        setReportData(await api.getReport('leave', params.toString()));
      } else if (activeTab === 'payroll') {
        setReportData(await api.getReport('payroll', params.toString()));
      } else if (activeTab === 'performance') {
        params.set('report_type', form.report_type || 'appraisal_summary');
        setReportData(await api.getReport('performance', params.toString()));
      } else if (activeTab === 'recruitment') {
        params.set('report_type', form.report_type || 'job_summary');
        setReportData(await api.getReport('recruitment', params.toString()));
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab !== 'overview') {
      runReport();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  const updateForm = (name, value) => setForm((prev) => ({ ...prev, [name]: value }));

  const renderFilterForm = () => (
    <form
      className="row g-2 mb-3 align-items-end"
      onSubmit={(e) => { e.preventDefault(); runReport(); }}
    >
      {(activeTab === 'attendance') && (
        <>
          <div className="col-md-3">
            <label className="form-label">Date Range</label>
            <select className="form-select form-select-sm" value={form.date_range}
              onChange={(e) => updateForm('date_range', e.target.value)}>
              <option value="this_month">This Month</option>
              <option value="last_month">Last Month</option>
              <option value="this_quarter">This Quarter</option>
              <option value="this_year">This Year</option>
              <option value="custom">Custom</option>
            </select>
          </div>
          {form.date_range === 'custom' && (
            <>
              <div className="col-md-2">
                <label className="form-label">Start</label>
                <input type="date" className="form-control form-control-sm" value={form.start_date}
                  onChange={(e) => updateForm('start_date', e.target.value)} />
              </div>
              <div className="col-md-2">
                <label className="form-label">End</label>
                <input type="date" className="form-control form-control-sm" value={form.end_date}
                  onChange={(e) => updateForm('end_date', e.target.value)} />
              </div>
            </>
          )}
          <div className="col-md-2">
            <label className="form-label">Status</label>
            <select className="form-select form-select-sm" value={form.status}
              onChange={(e) => updateForm('status', e.target.value)}>
              <option value="">All</option>
              <option value="present">Present</option>
              <option value="absent">Absent</option>
              <option value="late">Late</option>
            </select>
          </div>
        </>
      )}

      {activeTab === 'leave' && (
        <>
          <div className="col-md-3">
            <label className="form-label">Report Type</label>
            <select className="form-select form-select-sm" value={form.report_type || 'summary'}
              onChange={(e) => updateForm('report_type', e.target.value)}>
              <option value="summary">Summary</option>
              <option value="detailed">Detailed</option>
              <option value="pending">Pending</option>
              <option value="balance">Balance</option>
            </select>
          </div>
          <div className="col-md-2">
            <label className="form-label">Year</label>
            <select className="form-select form-select-sm" value={form.year}
              onChange={(e) => updateForm('year', e.target.value)}>
              {(filters?.years || [form.year]).map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>
          <div className="col-md-2">
            <label className="form-label">Status</label>
            <select className="form-select form-select-sm" value={form.status}
              onChange={(e) => updateForm('status', e.target.value)}>
              <option value="">All</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
        </>
      )}

      {activeTab === 'payroll' && (
        <>
          <div className="col-md-2">
            <label className="form-label">Month</label>
            <select className="form-select form-select-sm" value={form.month}
              onChange={(e) => updateForm('month', e.target.value)}>
              {(filters?.months || []).map((m) => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </div>
          <div className="col-md-2">
            <label className="form-label">Year</label>
            <select className="form-select form-select-sm" value={form.year}
              onChange={(e) => updateForm('year', e.target.value)}>
              {(filters?.years || [form.year]).map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>
        </>
      )}

      {activeTab === 'performance' && (
        <>
          <div className="col-md-3">
            <label className="form-label">Report Type</label>
            <select className="form-select form-select-sm" value={form.report_type || 'appraisal_summary'}
              onChange={(e) => updateForm('report_type', e.target.value)}>
              <option value="appraisal_summary">Appraisal Summary</option>
              <option value="goal_progress">Goal Progress</option>
            </select>
          </div>
        </>
      )}

      {activeTab === 'recruitment' && (
        <>
          <div className="col-md-3">
            <label className="form-label">Report Type</label>
            <select className="form-select form-select-sm" value={form.report_type || 'job_summary'}
              onChange={(e) => updateForm('report_type', e.target.value)}>
              <option value="job_summary">Job Summary</option>
              <option value="applicant_status">Applicant Status</option>
              <option value="hiring_funnel">Hiring Funnel</option>
            </select>
          </div>
          <div className="col-md-2">
            <label className="form-label">Job Status</label>
            <select className="form-select form-select-sm" value={form.job_status}
              onChange={(e) => updateForm('job_status', e.target.value)}>
              <option value="">All</option>
              <option value="open">Open</option>
              <option value="closed">Closed</option>
            </select>
          </div>
        </>
      )}

      {activeTab !== 'overview' && filters?.departments && (
        <div className="col-md-3">
          <label className="form-label">Department</label>
          <select className="form-select form-select-sm" value={form.department}
            onChange={(e) => updateForm('department', e.target.value)}>
            <option value="">All Departments</option>
            {filters.departments.map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
        </div>
      )}

      {activeTab !== 'overview' && (
        <div className="col-md-2">
          <button type="submit" className="btn btn-primary btn-sm w-100" disabled={loading}>
            {loading ? 'Loading...' : 'Apply Filters'}
          </button>
        </div>
      )}
    </form>
  );

  const renderReportResults = () => {
    if (!reportData) return null;

    if (activeTab === 'attendance') {
      return (
        <>
          <p className="text-muted">{reportData.period} · {reportData.total_records} records</p>
          <ReportTable
            rows={reportData.records}
            columns={[
              { key: 'employee_name', label: 'Employee' },
              { key: 'date', label: 'Date' },
              { key: 'status', label: 'Status' },
              { key: 'time_in', label: 'In' },
              { key: 'time_out', label: 'Out' },
            ]}
          />
        </>
      );
    }

    if (activeTab === 'leave') {
      return (
        <>
          <p className="text-muted">{reportData.type} · {reportData.year}</p>
          <ReportTable
            rows={reportData.rows}
            columns={
              reportData.type === 'Balance'
                ? [
                    { key: 'employee_name', label: 'Employee' },
                    { key: 'leave_type', label: 'Type' },
                    { key: 'total_days', label: 'Total' },
                    { key: 'used_days', label: 'Used' },
                    { key: 'pending_days', label: 'Pending' },
                  ]
                : reportData.type === 'Detailed'
                  ? [
                      { key: 'employee_name', label: 'Employee' },
                      { key: 'leave_type', label: 'Type' },
                      { key: 'start_date', label: 'Start' },
                      { key: 'end_date', label: 'End' },
                      { key: 'status', label: 'Status' },
                    ]
                  : [
                      { key: 'leave_type', label: 'Leave Type' },
                      { key: 'count', label: 'Count' },
                    ]
            }
          />
        </>
      );
    }

    if (activeTab === 'payroll') {
      return (
        <>
          <p className="text-muted">
            {reportData.period} · {reportData.total_employees} employees ·
            Net: {Number(reportData.total_net).toLocaleString()}
          </p>
          <ReportTable
            rows={reportData.rows}
            columns={[
              { key: 'employee_name', label: 'Employee' },
              { key: 'basic_salary', label: 'Basic' },
              { key: 'allowances', label: 'Allowances' },
              { key: 'deductions', label: 'Deductions' },
              { key: 'net_salary', label: 'Net' },
            ]}
          />
        </>
      );
    }

    if (activeTab === 'performance') {
      return (
        <>
          <p className="text-muted">
            {reportData.type}
            {reportData.average_rating != null && ` · Avg rating: ${reportData.average_rating}`}
            {reportData.average_progress != null && ` · Avg progress: ${reportData.average_progress}%`}
          </p>
          <ReportTable
            rows={reportData.rows}
            columns={
              reportData.type === 'Goal Progress'
                ? [
                    { key: 'status', label: 'Status' },
                    { key: 'count', label: 'Count' },
                  ]
                : [
                    { key: 'overall_rating', label: 'Rating' },
                    { key: 'count', label: 'Count' },
                  ]
            }
          />
        </>
      );
    }

    if (activeTab === 'recruitment') {
      if (reportData.funnel) {
        const rows = Object.entries(reportData.funnel).map(([status, count]) => ({ status, count }));
        return (
          <>
            <p className="text-muted">{reportData.type}</p>
            <ReportTable rows={rows} columns={[{ key: 'status', label: 'Stage' }, { key: 'count', label: 'Count' }]} />
          </>
        );
      }
      return (
        <>
          <p className="text-muted">{reportData.type}</p>
          {reportData.rows ? (
            <ReportTable
              rows={reportData.rows}
              columns={[{ key: 'status', label: 'Status' }, { key: 'count', label: 'Count' }]}
            />
          ) : (
            <ul className="list-unstyled mb-0">
              <li>Total jobs: {reportData.total_jobs}</li>
              <li>Open: {reportData.open_positions}</li>
              <li>Closed: {reportData.closed_positions}</li>
            </ul>
          )}
        </>
      );
    }

    return null;
  };

  return (
    <>
      <h4 className="page-heading mb-4">
        <i className="bi bi-bar-chart" style={{ color: 'var(--fca-lime)' }} /> Reports & Analytics
      </h4>

      <ul className="nav nav-tabs mb-3">
        {REPORT_TABS.map((tab) => (
          <li className="nav-item" key={tab.id}>
            <button
              type="button"
              className={`nav-link ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          </li>
        ))}
      </ul>

      {error && <div className="alert alert-danger">{error}</div>}

      {activeTab === 'overview' ? (
        !overview ? (
          <div className="text-center py-5"><div className="spinner-border text-primary" role="status" /></div>
        ) : (
          <div className="row">
            <StatCard title="Total Employees" value={overview.total_employees} />
            <StatCard title="New Joiners (30d)" value={overview.new_joiners} color="lime" />
            <StatCard title="Present Today" value={overview.present_today} color="sage" />
            <StatCard title="Absent Today" value={overview.absent_today} color="red" />
            <StatCard title="Late Today" value={overview.late_today} color="dark" />
            <StatCard title="Pending Leaves" value={overview.pending_leaves} color="red" />
            <StatCard title="Leaves Used (YTD)" value={overview.leaves_used_this_year} />
            <StatCard title="Open Positions" value={overview.open_positions} color="lime" />
            <StatCard title="Pending Applications" value={overview.pending_applications} color="sage" />
            <StatCard title="Active Goals" value={overview.active_goals} />
            <StatCard title="Appraisals Due" value={overview.appraisals_due} color="red" />
          </div>
        )
      ) : (
        <>
          {renderFilterForm()}
          {loading ? (
            <div className="text-center py-4"><div className="spinner-border text-primary" role="status" /></div>
          ) : (
            <div className="card"><div className="card-body">{renderReportResults()}</div></div>
          )}
        </>
      )}
    </>
  );
}
