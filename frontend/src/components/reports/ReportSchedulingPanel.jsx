export default function ReportSchedulingPanel({
  saveName,
  onSaveNameChange,
  onSaveCurrentReport,
  savedReports,
  onLoadSavedReport,
  reportData,
  snapshotBusy,
  onSaveSnapshot,
  snapshots,
  scheduleForm,
  onScheduleFormChange,
  scheduleBusy,
  onCreateScheduledReport,
  scheduledReports,
  onRunScheduledNow,
}) {
  return (
    <>
      <div className="row g-2 mt-3 align-items-end">
        <div className="col-md-4">
          <label className="form-label" htmlFor="save-report-name">Save this view</label>
          <input
            id="save-report-name"
            className="form-control"
            placeholder="Report name"
            value={saveName}
            onChange={(e) => onSaveNameChange(e.target.value)}
          />
        </div>
        <div className="col-md-2">
          <button type="button" className="btn btn-outline-primary w-100" onClick={onSaveCurrentReport} disabled={!saveName.trim()}>
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
                onClick={() => onLoadSavedReport(saved)}
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
            onClick={onSaveSnapshot}
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
              onChange={(e) => onScheduleFormChange('name', e.target.value)}
              placeholder="Monthly payroll digest"
            />
          </div>
          <div className="col-md-2">
            <label className="form-label small" htmlFor="schedule-frequency">Frequency</label>
            <select
              id="schedule-frequency"
              className="form-select form-select-sm"
              value={scheduleForm.frequency}
              onChange={(e) => onScheduleFormChange('frequency', e.target.value)}
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
              onChange={(e) => onScheduleFormChange('export_format', e.target.value)}
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
              onChange={(e) => onScheduleFormChange('recipient_emails', e.target.value)}
              placeholder="hr@company.com, cfo@company.com"
            />
          </div>
          <div className="col-md-2">
            <button
              type="button"
              className="btn btn-outline-primary btn-sm w-100"
              onClick={onCreateScheduledReport}
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
                    onClick={() => onRunScheduledNow(scheduled.id)}
                  >
                    Run now
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
