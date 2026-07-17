export default function ReportFilterForm({
  activeTab,
  form,
  filters,
  loading,
  exporting,
  onUpdateForm,
  onRunReport,
  onExportReport,
  onExportStatutory,
}) {
  return (
    <form
      className="row g-2 mb-3 align-items-end"
      onSubmit={(e) => { e.preventDefault(); onRunReport(); }}
    >
      {(activeTab === 'attendance') && (
        <>
          <div className="col-md-3">
            <label className="form-label" htmlFor="filter-date-range">Date Range</label>
            <select id="filter-date-range" className="form-select form-select-sm" value={form.date_range}
              onChange={(e) => onUpdateForm('date_range', e.target.value)}>
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
                <label className="form-label" htmlFor="filter-start-date">Start</label>
                <input id="filter-start-date" type="date" className="form-control form-control-sm" value={form.start_date}
                  onChange={(e) => onUpdateForm('start_date', e.target.value)} />
              </div>
              <div className="col-md-2">
                <label className="form-label" htmlFor="filter-end-date">End</label>
                <input id="filter-end-date" type="date" className="form-control form-control-sm" value={form.end_date}
                  onChange={(e) => onUpdateForm('end_date', e.target.value)} />
              </div>
            </>
          )}
          <div className="col-md-2">
            <label className="form-label" htmlFor="filter-attendance-status">Status</label>
            <select id="filter-attendance-status" className="form-select form-select-sm" value={form.attendance_status}
              onChange={(e) => onUpdateForm('attendance_status', e.target.value)}>
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
            <label className="form-label" htmlFor="filter-leave-report-type">Report Type</label>
            <select id="filter-leave-report-type" className="form-select form-select-sm" value={form.leave_report_type}
              onChange={(e) => onUpdateForm('leave_report_type', e.target.value)}>
              <option value="summary">Summary</option>
              <option value="detailed">Detailed</option>
              <option value="pending">Pending</option>
              <option value="balance">Balance</option>
            </select>
          </div>
          <div className="col-md-2">
            <label className="form-label" htmlFor="filter-leave-year">Year</label>
            <select id="filter-leave-year" className="form-select form-select-sm" value={form.year}
              onChange={(e) => onUpdateForm('year', e.target.value)}>
              {(filters?.years || [form.year]).map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>
          <div className="col-md-2">
            <label className="form-label" htmlFor="filter-leave-status">Status</label>
            <select id="filter-leave-status" className="form-select form-select-sm" value={form.leave_status}
              onChange={(e) => onUpdateForm('leave_status', e.target.value)}>
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
            <label className="form-label" htmlFor="filter-payroll-month">Month</label>
            <select id="filter-payroll-month" className="form-select form-select-sm" value={form.month}
              onChange={(e) => onUpdateForm('month', e.target.value)}>
              {(filters?.months || []).map((m) => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </div>
          <div className="col-md-2">
            <label className="form-label" htmlFor="filter-payroll-year">Year</label>
            <select id="filter-payroll-year" className="form-select form-select-sm" value={form.year}
              onChange={(e) => onUpdateForm('year', e.target.value)}>
              {(filters?.years || [form.year]).map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>
        </>
      )}

      {activeTab === 'performance' && (
        <div className="col-md-3">
          <label className="form-label" htmlFor="filter-performance-report-type">Report Type</label>
          <select id="filter-performance-report-type" className="form-select form-select-sm" value={form.performance_report_type}
            onChange={(e) => onUpdateForm('performance_report_type', e.target.value)}>
            <option value="appraisal_summary">Appraisal Summary</option>
            <option value="goal_progress">Goal Progress</option>
          </select>
        </div>
      )}

      {activeTab === 'recruitment' && (
        <>
          <div className="col-md-3">
            <label className="form-label" htmlFor="filter-recruitment-report-type">Report Type</label>
            <select id="filter-recruitment-report-type" className="form-select form-select-sm" value={form.recruitment_report_type}
              onChange={(e) => onUpdateForm('recruitment_report_type', e.target.value)}>
              <option value="job_summary">Job Summary</option>
              <option value="applicant_status">Applicant Status</option>
              <option value="hiring_funnel">Hiring Funnel</option>
            </select>
          </div>
          <div className="col-md-2">
            <label className="form-label" htmlFor="filter-job-status">Job Status</label>
            <select id="filter-job-status" className="form-select form-select-sm" value={form.job_status}
              onChange={(e) => onUpdateForm('job_status', e.target.value)}>
              <option value="">All</option>
              <option value="open">Open</option>
              <option value="closed">Closed</option>
            </select>
          </div>
        </>
      )}

      {activeTab !== 'overview' && filters?.departments && (
        <div className="col-md-3">
          <label className="form-label" htmlFor="filter-department">Department</label>
          <select id="filter-department" className="form-select form-select-sm" value={form.department}
            onChange={(e) => onUpdateForm('department', e.target.value)}>
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
              onClick={() => onExportReport('xlsx')}
              title="Export Microsoft Excel workbook"
            >
              {exporting === 'xlsx' ? <span className="spinner-border spinner-border-sm" aria-hidden="true" /> : <i className="bi bi-file-earmark-excel" aria-hidden="true" />}
              <span className="visually-hidden">Export Excel</span>
            </button>
            <button
              type="button"
              className="btn btn-outline-secondary btn-sm"
              disabled={loading || Boolean(exporting)}
              onClick={() => onExportReport('csv')}
              title="Export CSV file"
            >
              {exporting === 'csv' ? <span className="spinner-border spinner-border-sm" aria-hidden="true" /> : <i className="bi bi-filetype-csv" aria-hidden="true" />}
              <span className="visually-hidden">Export CSV</span>
            </button>
            <button
              type="button"
              className="btn btn-outline-secondary btn-sm"
              disabled={loading || Boolean(exporting)}
              onClick={() => onExportReport('pdf')}
              title="Export PDF report"
            >
              {exporting === 'pdf' ? <span className="spinner-border spinner-border-sm" aria-hidden="true" /> : <i className="bi bi-file-earmark-pdf" aria-hidden="true" />}
              <span className="visually-hidden">Export PDF</span>
            </button>
            {activeTab === 'payroll' && (
              <>
                <button
                  type="button"
                  className="btn btn-outline-primary btn-sm"
                  disabled={loading || Boolean(exporting)}
                  onClick={() => onExportStatutory('paye')}
                  title="Export PAYE statutory return"
                >
                  PAYE
                </button>
                <button
                  type="button"
                  className="btn btn-outline-primary btn-sm"
                  disabled={loading || Boolean(exporting)}
                  onClick={() => onExportStatutory('paye', 'ura')}
                  title="Export URA portal PAYE format"
                >
                  URA
                </button>
                <button
                  type="button"
                  className="btn btn-outline-primary btn-sm"
                  disabled={loading || Boolean(exporting)}
                  onClick={() => onExportStatutory('nssf')}
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
}
