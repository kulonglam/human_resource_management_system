import { useEffect, useMemo, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { canManageReports } from '../utils/permissions';
import '../styles/reports.css';

const REPORT_PAGE_SIZE = 25;

const UGX_FORMATTER = new Intl.NumberFormat('en-UG', {
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

function formatUGX(value) {
  return `UGX ${UGX_FORMATTER.format(Number(value) || 0)}`;
}

function formatDate(value) {
  if (!value) return '—';
  const date = new Date(`${value}T00:00:00`);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleDateString('en-UG', { day: '2-digit', month: 'short', year: 'numeric' });
}

function formatLabel(value) {
  if (value == null || value === '') return '—';
  return String(value)
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function StatCard({ title, value, icon = 'bi-graph-up', tone = 'green' }) {
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

const REPORT_TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'attendance', label: 'Attendance' },
  { id: 'leave', label: 'Leave' },
  { id: 'payroll', label: 'Payroll' },
  { id: 'performance', label: 'Performance' },
  { id: 'recruitment', label: 'Recruitment' },
];

function ReportTable({ rows, columns, caption }) {
  const [page, setPage] = useState(1);

  useEffect(() => {
    setPage(1);
  }, [rows]);

  const totalPages = Math.max(1, Math.ceil((rows?.length || 0) / REPORT_PAGE_SIZE));
  const pageRows = useMemo(() => {
    if (!rows?.length) return [];
    const start = (page - 1) * REPORT_PAGE_SIZE;
    return rows.slice(start, start + REPORT_PAGE_SIZE);
  }, [rows, page]);

  if (!rows?.length) {
    return (
      <div className="report-empty">
        <i className="bi bi-inbox" aria-hidden="true" />
        <p className="mb-1 fw-semibold">No records found</p>
        <p className="text-muted mb-0">Try changing the selected filters.</p>
      </div>
    );
  }
  return (
    <>
      <div className="table-responsive">
        <table className="table table-hover align-middle report-table mb-0">
          <caption className="visually-hidden">{caption}</caption>
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col.key} scope="col" className={col.className}>{col.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, idx) => (
              <tr key={row.id || idx}>
                {columns.map((col) => (
                  <td key={col.key} className={col.className}>
                    {col.render ? col.render(row[col.key], row) : (row[col.key] ?? '—')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length > REPORT_PAGE_SIZE && (
        <div className="d-flex justify-content-between align-items-center mt-3">
          <p className="text-muted small mb-0">
            Showing {(page - 1) * REPORT_PAGE_SIZE + 1}–{Math.min(page * REPORT_PAGE_SIZE, rows.length)} of {rows.length}
          </p>
          <div className="btn-group btn-group-sm">
            <button type="button" className="btn btn-outline-secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              Previous
            </button>
            <button type="button" className="btn btn-outline-secondary" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
              Next
            </button>
          </div>
        </div>
      )}
    </>
  );
}

export default function Reports() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [overview, setOverview] = useState(null);
  const [overviewLoading, setOverviewLoading] = useState(true);
  const [filters, setFilters] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState('');
  const [savedReports, setSavedReports] = useState([]);
  const [snapshots, setSnapshots] = useState([]);
  const [saveName, setSaveName] = useState('');
  const [snapshotBusy, setSnapshotBusy] = useState(false);
  const [scheduledReports, setScheduledReports] = useState([]);
  const [scheduleForm, setScheduleForm] = useState({
    name: '',
    frequency: 'monthly',
    export_format: 'xlsx',
    recipient_emails: '',
  });
  const [scheduleBusy, setScheduleBusy] = useState(false);

  const [form, setForm] = useState({
    date_range: 'this_month',
    start_date: '',
    end_date: '',
    department: '',
    attendance_status: '',
    leave_status: '',
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    leave_report_type: 'summary',
    performance_report_type: 'appraisal_summary',
    recruitment_report_type: 'job_summary',
    leave_type: '',
    rating: '',
    job_status: '',
  });

  useEffect(() => {
    api.getReportsAnalytics()
      .then(setOverview)
      .catch((err) => setError(err.message))
      .finally(() => setOverviewLoading(false));
    api.getReportFilters()
      .then(setFilters)
      .catch(() => setError('Report filters could not be loaded. Refresh the page and try again.'));
    api.getSavedReports()
      .then(setSavedReports)
      .catch(() => {});
    api.getReportSnapshots()
      .then(setSnapshots)
      .catch(() => {});
    api.getScheduledReports()
      .then(setScheduledReports)
      .catch(() => {});
  }, []);

  if (!canManageReports(user)) {
    return <Navigate to="/dashboard" replace />;
  }

  const buildReportParams = () => {
    const params = new URLSearchParams();
    const excluded = new Set([
      'leave_report_type',
      'performance_report_type',
      'recruitment_report_type',
      'attendance_status',
      'leave_status',
    ]);
    Object.entries(form).forEach(([key, val]) => {
      if (!excluded.has(key) && val !== '' && val != null) params.set(key, val);
    });
    if (activeTab === 'leave') params.set('report_type', form.leave_report_type);
    if (activeTab === 'performance') params.set('report_type', form.performance_report_type);
    if (activeTab === 'recruitment') params.set('report_type', form.recruitment_report_type);
    if (activeTab === 'attendance' && form.attendance_status) {
      params.set('status', form.attendance_status);
    }
    if (activeTab === 'leave' && form.leave_status) params.set('status', form.leave_status);
    return params;
  };

  const runReport = async () => {
    setLoading(true);
    setError('');
    setReportData(null);
    try {
      const params = buildReportParams();
      if (activeTab === 'attendance') {
        setReportData(await api.getReport('attendance', params.toString()));
      } else if (activeTab === 'leave') {
        setReportData(await api.getReport('leave', params.toString()));
      } else if (activeTab === 'payroll') {
        setReportData(await api.getReport('payroll', params.toString()));
      } else if (activeTab === 'performance') {
        setReportData(await api.getReport('performance', params.toString()));
      } else if (activeTab === 'recruitment') {
        setReportData(await api.getReport('recruitment', params.toString()));
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const exportReport = async (format) => {
    setExporting(format);
    setError('');
    try {
      const params = buildReportParams();
      if (activeTab === 'payroll') {
        await api.downloadPayroll(params.toString(), format);
      } else {
        await api.downloadReport(activeTab, params.toString(), format);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setExporting('');
    }
  };

  const saveCurrentReport = async () => {
    if (activeTab === 'overview' || !saveName.trim()) return;
    setError('');
    try {
      const saved = await api.createSavedReport({
        name: saveName.trim(),
        report_type: activeTab,
        filters: { ...form, activeTab },
        is_public: false,
      });
      setSavedReports((prev) => [saved, ...prev]);
      setSaveName('');
    } catch (err) {
      setError(err.message);
    }
  };

  const loadSavedReport = async (saved) => {
    setActiveTab(saved.report_type);
    setForm((prev) => ({ ...prev, ...(saved.filters || {}) }));
    setError('');
  };

  const saveSnapshot = async () => {
    if (!reportData || activeTab === 'overview') return;
    setSnapshotBusy(true);
    setError('');
    try {
      const snapshot = await api.createReportSnapshot({
        report_type: activeTab,
        title: `${activeTab} report ${new Date().toLocaleString('en-UG')}`,
        report_data: reportData,
        filters_used: { ...form, activeTab },
      });
      setSnapshots((prev) => [snapshot, ...prev]);
    } catch (err) {
      setError(err.message);
    } finally {
      setSnapshotBusy(false);
    }
  };

  const exportStatutory = async (returnType, exportFormat = 'csv') => {
    setExporting(returnType);
    setError('');
    try {
      await api.downloadStatutoryPayroll({
        month: form.month,
        year: form.year,
        return_type: returnType,
        export_format: exportFormat,
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setExporting('');
    }
  };

  const createScheduledReport = async () => {
    if (activeTab === 'overview' || !scheduleForm.name.trim()) return;
    setScheduleBusy(true);
    setError('');
    try {
      const emails = scheduleForm.recipient_emails
        .split(',')
        .map((e) => e.trim())
        .filter(Boolean);
      const scheduled = await api.createScheduledReport({
        name: scheduleForm.name.trim(),
        report_type: activeTab,
        filters: { ...form, activeTab },
        frequency: scheduleForm.frequency,
        export_format: scheduleForm.export_format,
        recipient_emails: emails,
        is_active: true,
      });
      setScheduledReports((prev) => [scheduled, ...prev]);
      setScheduleForm({ name: '', frequency: 'monthly', export_format: 'xlsx', recipient_emails: '' });
    } catch (err) {
      setError(err.message);
    } finally {
      setScheduleBusy(false);
    }
  };

  const runScheduledNow = async (id) => {
    setError('');
    try {
      await api.runScheduledReport(id);
    } catch (err) {
      setError(err.message);
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
            <select className="form-select form-select-sm" value={form.attendance_status}
              onChange={(e) => updateForm('attendance_status', e.target.value)}>
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
            <select className="form-select form-select-sm" value={form.leave_report_type}
              onChange={(e) => updateForm('leave_report_type', e.target.value)}>
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
            <select className="form-select form-select-sm" value={form.leave_status}
              onChange={(e) => updateForm('leave_status', e.target.value)}>
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
            <select className="form-select form-select-sm" value={form.performance_report_type}
              onChange={(e) => updateForm('performance_report_type', e.target.value)}>
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
            <select className="form-select form-select-sm" value={form.recruitment_report_type}
              onChange={(e) => updateForm('recruitment_report_type', e.target.value)}>
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
        <div className="col-md-3">
          <div className="d-flex gap-2">
          <button type="submit" className="btn btn-primary btn-sm w-100" disabled={loading}>
            {loading ? (
              <><span className="spinner-border spinner-border-sm me-1" aria-hidden="true" /> Loading</>
            ) : (
              <><i className="bi bi-funnel me-1" aria-hidden="true" /> Apply</>
            )}
          </button>
          <button
            type="button"
            className="btn btn-outline-secondary btn-sm"
            disabled={loading || Boolean(exporting)}
            onClick={() => exportReport('xlsx')}
            title="Export Microsoft Excel workbook"
          >
            {exporting === 'xlsx' ? <span className="spinner-border spinner-border-sm" /> : <i className="bi bi-file-earmark-excel" />}
            <span className="visually-hidden">Export Excel</span>
          </button>
          <button
            type="button"
            className="btn btn-outline-secondary btn-sm"
            disabled={loading || Boolean(exporting)}
            onClick={() => exportReport('csv')}
            title="Export CSV file"
          >
            {exporting === 'csv' ? <span className="spinner-border spinner-border-sm" /> : <i className="bi bi-filetype-csv" />}
            <span className="visually-hidden">Export CSV</span>
          </button>
          <button
            type="button"
            className="btn btn-outline-secondary btn-sm"
            disabled={loading || Boolean(exporting)}
            onClick={() => exportReport('pdf')}
            title="Export PDF report"
          >
            {exporting === 'pdf' ? <span className="spinner-border spinner-border-sm" /> : <i className="bi bi-file-earmark-pdf" />}
            <span className="visually-hidden">Export PDF</span>
          </button>
          {activeTab === 'payroll' && (
            <>
              <button
                type="button"
                className="btn btn-outline-primary btn-sm"
                disabled={loading || Boolean(exporting)}
                onClick={() => exportStatutory('paye')}
                title="Export PAYE statutory return"
              >
                PAYE
              </button>
              <button
                type="button"
                className="btn btn-outline-primary btn-sm"
                disabled={loading || Boolean(exporting)}
                onClick={() => exportStatutory('paye', 'ura')}
                title="Export URA portal PAYE format"
              >
                URA
              </button>
              <button
                type="button"
                className="btn btn-outline-primary btn-sm"
                disabled={loading || Boolean(exporting)}
                onClick={() => exportStatutory('nssf')}
                title="Export NSSF statutory return"
              >
                NSSF
              </button>
            </>
          )}
          </div>
        </div>
      )}
    </form>
  );

  const renderReportResults = () => {
    if (!reportData) return null;

    if (activeTab === 'attendance') {
      return (
        <>
          <div className="report-result-header">
            <div>
              <h2 className="h5 mb-1">Attendance detail</h2>
              <p className="text-muted mb-0">{reportData.period} · {reportData.total_records} records</p>
            </div>
          </div>
          {reportData.truncated && (
            <div className="alert alert-info py-2 small" role="status">
              Showing the first {reportData.shown_records} records. Export the report to include every record.
            </div>
          )}
          <ReportTable
            rows={reportData.records}
            caption={`Attendance records for ${reportData.period}`}
            columns={[
              { key: 'employee_name', label: 'Employee' },
              { key: 'date', label: 'Date', render: formatDate },
              { key: 'status', label: 'Status', render: (value) => <span className="report-status">{formatLabel(value)}</span> },
              { key: 'time_in', label: 'In' },
              { key: 'time_out', label: 'Out' },
            ]}
          />
        </>
      );
    }

    if (activeTab === 'leave') {
      const leaveColumns = reportData.type === 'Balance'
        ? [
            { key: 'employee_name', label: 'Employee' },
            { key: 'leave_type', label: 'Type', render: formatLabel },
            { key: 'total_days', label: 'Total', className: 'text-end' },
            { key: 'used_days', label: 'Used', className: 'text-end' },
            { key: 'pending_days', label: 'Pending', className: 'text-end' },
          ]
        : reportData.type === 'Detailed'
          ? [
              { key: 'employee_name', label: 'Employee' },
              { key: 'leave_type', label: 'Type', render: formatLabel },
              { key: 'start_date', label: 'Start', render: formatDate },
              { key: 'end_date', label: 'End', render: formatDate },
              { key: 'status', label: 'Status', render: (value) => <span className="report-status">{formatLabel(value)}</span> },
            ]
          : reportData.type === 'Pending'
            ? [
                { key: 'employee_name', label: 'Employee' },
                { key: 'leave_type', label: 'Type', render: formatLabel },
                { key: 'start_date', label: 'Start', render: formatDate },
                { key: 'end_date', label: 'End', render: formatDate },
                { key: 'applied_on', label: 'Applied', render: (value) => formatDate(String(value).slice(0, 10)) },
              ]
            : [
                { key: 'leave_type', label: 'Leave Type', render: formatLabel },
                { key: 'count', label: 'Count', className: 'text-end' },
              ];
      return (
        <>
          <div className="report-result-header">
            <div>
              <h2 className="h5 mb-1">{reportData.type} leave report</h2>
              <p className="text-muted mb-0">Reporting year {reportData.year}</p>
            </div>
          </div>
          <ReportTable
            rows={reportData.rows}
            caption={`${reportData.type} leave report for ${reportData.year}`}
            columns={leaveColumns}
          />
        </>
      );
    }

    if (activeTab === 'payroll') {
      return (
        <>
          <div className="report-result-header">
            <div>
              <h2 className="h5 mb-1">Payroll summary</h2>
              <p className="text-muted mb-0">{reportData.period} · {reportData.total_employees} employees</p>
            </div>
            <div className="report-total">
              <span>Total net payroll</span>
              <strong>{formatUGX(reportData.total_net)}</strong>
            </div>
          </div>
          <ReportTable
            rows={reportData.rows}
            caption={`Payroll report for ${reportData.period}, amounts in Uganda shillings`}
            columns={[
              { key: 'employee_name', label: 'Employee' },
              { key: 'basic_salary', label: 'Basic (UGX)', render: formatUGX, className: 'text-end text-nowrap' },
              { key: 'allowances', label: 'Allowances (UGX)', render: formatUGX, className: 'text-end text-nowrap' },
              { key: 'gross_salary', label: 'Gross (UGX)', render: formatUGX, className: 'text-end text-nowrap' },
              { key: 'tax', label: 'PAYE (UGX)', render: formatUGX, className: 'text-end text-nowrap' },
              { key: 'nssf_employee', label: 'NSSF 5% (UGX)', render: formatUGX, className: 'text-end text-nowrap' },
              { key: 'local_service_tax', label: 'LST (UGX)', render: formatUGX, className: 'text-end text-nowrap' },
              { key: 'deductions', label: 'Deductions (UGX)', render: formatUGX, className: 'text-end text-nowrap' },
              { key: 'net_salary', label: 'Net (UGX)', render: formatUGX, className: 'text-end text-nowrap fw-semibold' },
              { key: 'status', label: 'Status', render: formatLabel },
            ]}
          />
        </>
      );
    }

    if (activeTab === 'performance') {
      return (
        <>
          <div className="report-result-header">
            <div>
              <h2 className="h5 mb-1">{reportData.type}</h2>
              <p className="text-muted mb-0">
                {reportData.average_rating != null && `Average rating: ${reportData.average_rating}`}
                {reportData.average_progress != null && `Average progress: ${reportData.average_progress}%`}
              </p>
            </div>
          </div>
          <ReportTable
            rows={reportData.rows}
            caption={reportData.type}
            columns={
              reportData.type === 'Goal Progress'
                ? [
                    { key: 'status', label: 'Status', render: formatLabel },
                    { key: 'count', label: 'Count', className: 'text-end' },
                  ]
                : [
                    { key: 'overall_rating', label: 'Rating' },
                    { key: 'count', label: 'Count', className: 'text-end' },
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
            <div className="report-result-header"><h2 className="h5 mb-0">{reportData.type}</h2></div>
            <ReportTable
              rows={rows}
              caption={reportData.type}
              columns={[
                { key: 'status', label: 'Stage', render: formatLabel },
                { key: 'count', label: 'Count', className: 'text-end' },
              ]}
            />
          </>
        );
      }
      return (
        <>
          <div className="report-result-header"><h2 className="h5 mb-0">{reportData.type}</h2></div>
          {reportData.rows ? (
            <ReportTable
              rows={reportData.rows}
              caption={reportData.type}
              columns={[
                { key: 'status', label: 'Status', render: formatLabel },
                { key: 'count', label: 'Count', className: 'text-end' },
              ]}
            />
          ) : (
            <div className="row g-3">
              <div className="col-sm-4"><div className="report-summary-metric"><span>Total jobs</span><strong>{reportData.total_jobs}</strong></div></div>
              <div className="col-sm-4"><div className="report-summary-metric"><span>Open</span><strong>{reportData.open_positions}</strong></div></div>
              <div className="col-sm-4"><div className="report-summary-metric"><span>Closed</span><strong>{reportData.closed_positions}</strong></div></div>
            </div>
          )}
        </>
      );
    }

    return null;
  };

  return (
    <div className="reports-page">
      <header className="reports-header">
        <div>
          <p className="reports-eyebrow mb-1">Management intelligence</p>
          <h1 className="page-heading mb-1">
            <i className="bi bi-bar-chart-line" aria-hidden="true" /> Reports & Analytics
          </h1>
          <p className="text-muted mb-0">Review workforce performance and export decision-ready reports.</p>
        </div>
        <div className="reports-currency" aria-label="Report currency Uganda shillings">
          <span>Currency</span>
          <strong>UGX · Uganda Shilling</strong>
        </div>
      </header>

      <ul className="nav nav-tabs reports-tabs mb-4" role="tablist" aria-label="Report categories">
        {REPORT_TABS.map((tab) => (
          <li className="nav-item" role="presentation" key={tab.id}>
            <button
              type="button"
              className={`nav-link ${activeTab === tab.id ? 'active' : ''}`}
              role="tab"
              id={`report-tab-${tab.id}`}
              aria-selected={activeTab === tab.id}
              aria-controls={`report-panel-${tab.id}`}
              onClick={() => {
                setActiveTab(tab.id);
                setError('');
              }}
            >
              {tab.label}
            </button>
          </li>
        ))}
      </ul>

      {error && (
        <div className="alert alert-danger d-flex align-items-center gap-2" role="alert">
          <i className="bi bi-exclamation-triangle-fill" aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      <section
        role="tabpanel"
        id={`report-panel-${activeTab}`}
        aria-labelledby={`report-tab-${activeTab}`}
      >
      {activeTab === 'overview' ? (
        overviewLoading ? (
          <div className="report-loading" role="status">
            <div className="spinner-border text-primary" aria-hidden="true" />
            <span>Loading analytics…</span>
          </div>
        ) : !overview ? (
          <div className="report-empty">
            <i className="bi bi-cloud-slash" aria-hidden="true" />
            <p className="mb-0">Analytics are currently unavailable.</p>
          </div>
        ) : (
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
        )
      ) : (
        <>
          <div className="report-filter-panel">
            <div className="report-filter-title">
              <i className="bi bi-sliders" aria-hidden="true" />
              <span>Report filters</span>
            </div>
            {renderFilterForm()}
            <div className="row g-2 mt-3 align-items-end">
              <div className="col-md-4">
                <label className="form-label" htmlFor="save-report-name">Save this view</label>
                <input
                  id="save-report-name"
                  className="form-control"
                  placeholder="Report name"
                  value={saveName}
                  onChange={(e) => setSaveName(e.target.value)}
                />
              </div>
              <div className="col-md-2">
                <button type="button" className="btn btn-outline-primary w-100" onClick={saveCurrentReport} disabled={!saveName.trim()}>
                  Save
                </button>
              </div>
            </div>
            {savedReports.length > 0 && (
              <div className="mt-3">
                <p className="small text-muted mb-2">Saved reports</p>
                <div className="d-flex flex-wrap gap-2">
                  {savedReports.map((saved) => (
                    <button
                      key={saved.id}
                      type="button"
                      className="btn btn-sm btn-outline-secondary"
                      onClick={() => loadSavedReport(saved)}
                    >
                      {saved.name}
                    </button>
                  ))}
                </div>
              </div>
            )}
            <div className="row g-2 mt-3 align-items-end">
              <div className="col-md-auto">
                <button
                  type="button"
                  className="btn btn-outline-secondary btn-sm"
                  onClick={saveSnapshot}
                  disabled={!reportData || snapshotBusy}
                >
                  {snapshotBusy ? 'Saving snapshot…' : 'Save report snapshot'}
                </button>
              </div>
            </div>
            {snapshots.length > 0 && (
              <div className="mt-3">
                <p className="small text-muted mb-2">Recent snapshots</p>
                <div className="list-group list-group-flush">
                  {snapshots.slice(0, 8).map((snapshot) => (
                    <div key={snapshot.id} className="list-group-item px-0 py-2 d-flex justify-content-between gap-2">
                      <span className="small">{snapshot.title}</span>
                      <span className="text-muted small">
                        {new Date(snapshot.generated_at).toLocaleString('en-UG')}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div className="mt-4 pt-3 border-top">
              <p className="small fw-semibold mb-2">Scheduled email delivery</p>
              <div className="row g-2 align-items-end">
                <div className="col-md-3">
                  <label className="form-label small" htmlFor="schedule-name">Schedule name</label>
                  <input
                    id="schedule-name"
                    className="form-control form-control-sm"
                    value={scheduleForm.name}
                    onChange={(e) => setScheduleForm((prev) => ({ ...prev, name: e.target.value }))}
                    placeholder="Monthly payroll digest"
                  />
                </div>
                <div className="col-md-2">
                  <label className="form-label small" htmlFor="schedule-frequency">Frequency</label>
                  <select
                    id="schedule-frequency"
                    className="form-select form-select-sm"
                    value={scheduleForm.frequency}
                    onChange={(e) => setScheduleForm((prev) => ({ ...prev, frequency: e.target.value }))}
                  >
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                  </select>
                </div>
                <div className="col-md-2">
                  <label className="form-label small" htmlFor="schedule-format">Format</label>
                  <select
                    id="schedule-format"
                    className="form-select form-select-sm"
                    value={scheduleForm.export_format}
                    onChange={(e) => setScheduleForm((prev) => ({ ...prev, export_format: e.target.value }))}
                  >
                    <option value="xlsx">Excel</option>
                    <option value="csv">CSV</option>
                    <option value="pdf">PDF</option>
                  </select>
                </div>
                <div className="col-md-3">
                  <label className="form-label small" htmlFor="schedule-emails">Recipients</label>
                  <input
                    id="schedule-emails"
                    className="form-control form-control-sm"
                    value={scheduleForm.recipient_emails}
                    onChange={(e) => setScheduleForm((prev) => ({ ...prev, recipient_emails: e.target.value }))}
                    placeholder="hr@company.com, cfo@company.com"
                  />
                </div>
                <div className="col-md-2">
                  <button
                    type="button"
                    className="btn btn-outline-primary btn-sm w-100"
                    onClick={createScheduledReport}
                    disabled={scheduleBusy || !scheduleForm.name.trim()}
                  >
                    {scheduleBusy ? 'Saving…' : 'Schedule'}
                  </button>
                </div>
              </div>
              {scheduledReports.length > 0 && (
                <div className="mt-3">
                  <div className="list-group list-group-flush">
                    {scheduledReports.map((scheduled) => (
                      <div key={scheduled.id} className="list-group-item px-0 py-2 d-flex justify-content-between align-items-center gap-2">
                        <div className="small">
                          <strong>{scheduled.name}</strong>
                          <span className="text-muted"> · {scheduled.report_type_display} · {scheduled.frequency_display}</span>
                          {scheduled.last_run_at && (
                            <span className="text-muted d-block">Last run: {new Date(scheduled.last_run_at).toLocaleString('en-UG')}</span>
                          )}
                        </div>
                        <button
                          type="button"
                          className="btn btn-sm btn-outline-secondary"
                          onClick={() => runScheduledNow(scheduled.id)}
                        >
                          Run now
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
          {loading ? (
            <div className="report-loading" role="status">
              <div className="spinner-border text-primary" aria-hidden="true" />
              <span>Generating report…</span>
            </div>
          ) : reportData ? (
            <div className="card report-results"><div className="card-body">{renderReportResults()}</div></div>
          ) : null}
        </>
      )}
      </section>
    </div>
  );
}
