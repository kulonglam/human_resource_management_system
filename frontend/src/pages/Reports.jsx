import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { canManageReports } from '../utils/permissions';
import ReportFilterForm from '../components/reports/ReportFilterForm';
import ReportOverviewPanel from '../components/reports/ReportOverviewPanel';
import ReportResults from '../components/reports/ReportResults';
import ReportSchedulingPanel from '../components/reports/ReportSchedulingPanel';
import { REPORT_TABS } from '../utils/reportFormatters';
import '../styles/reports.css';

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

  const updateScheduleForm = (name, value) =>
    setScheduleForm((prev) => ({ ...prev, [name]: value }));

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
          <ReportOverviewPanel overview={overview} loading={overviewLoading} />
        ) : (
          <>
            <div className="report-filter-panel">
              <div className="report-filter-title">
                <i className="bi bi-sliders" aria-hidden="true" />
                <span>Report filters</span>
              </div>
              <ReportFilterForm
                activeTab={activeTab}
                form={form}
                filters={filters}
                loading={loading}
                exporting={exporting}
                onUpdateForm={updateForm}
                onRunReport={runReport}
                onExportReport={exportReport}
                onExportStatutory={exportStatutory}
              />
              <ReportSchedulingPanel
                saveName={saveName}
                onSaveNameChange={setSaveName}
                onSaveCurrentReport={saveCurrentReport}
                savedReports={savedReports}
                onLoadSavedReport={loadSavedReport}
                reportData={reportData}
                snapshotBusy={snapshotBusy}
                onSaveSnapshot={saveSnapshot}
                snapshots={snapshots}
                scheduleForm={scheduleForm}
                onScheduleFormChange={updateScheduleForm}
                scheduleBusy={scheduleBusy}
                onCreateScheduledReport={createScheduledReport}
                scheduledReports={scheduledReports}
                onRunScheduledNow={runScheduledNow}
              />
            </div>
            {loading ? (
              <div className="report-loading" role="status">
                <div className="spinner-border text-primary" aria-hidden="true" />
                <span>Generating report…</span>
              </div>
            ) : reportData ? (
              <div className="card report-results">
                <div className="card-body">
                  <ReportResults activeTab={activeTab} reportData={reportData} />
                </div>
              </div>
            ) : null}
          </>
        )}
      </section>
    </div>
  );
}
