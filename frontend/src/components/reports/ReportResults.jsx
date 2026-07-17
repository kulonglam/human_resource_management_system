import ReportTable from './ReportTable';
import { formatDate, formatLabel, formatUGX } from '../../utils/reportFormatters';

export default function ReportResults({ activeTab, reportData }) {
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
}
