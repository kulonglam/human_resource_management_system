import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import ResourceManager from '../components/ResourceManager';
import RecruitmentPipeline, { RecruitmentMetrics } from '../components/recruitment/RecruitmentPipeline';
import RecruitmentAnalytics from '../components/recruitment/RecruitmentAnalytics';
import RecruitmentJobsPanel from '../components/recruitment/RecruitmentJobsPanel';
import RecruitmentCompliance from '../components/recruitment/RecruitmentCompliance';
import { recruitmentApplicationsTab } from '../config/hrModules';

const VIEWS = [
  { id: 'pipeline', label: 'Pipeline', icon: 'bi-kanban' },
  { id: 'jobs', label: 'Job Postings', icon: 'bi-briefcase' },
  { id: 'applications', label: 'Applications', icon: 'bi-file-earmark-person' },
];

function buildQuery(filters, debouncedQ) {
  const params = new URLSearchParams();
  if (filters.job) params.set('job', filters.job);
  if (filters.status) params.set('status', filters.status);
  if (debouncedQ) params.set('q', debouncedQ);
  return params.toString();
}

export default function Recruitment() {
  const { user } = useAuth();
  const [view, setView] = useState('pipeline');
  const [summary, setSummary] = useState(null);
  const [lookupOptions, setLookupOptions] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({ job: '', status: '', q: '' });
  const [debouncedQ, setDebouncedQ] = useState('');

  const canManage = Boolean(user?.is_admin || user?.is_manager);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQ(filters.q), 300);
    return () => clearTimeout(timer);
  }, [filters.q]);

  const loadSummary = useCallback(async () => {
    setError('');
    try {
      const data = await api.getRecruitmentSummary(buildQuery(filters, debouncedQ));
      setSummary(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [filters.job, filters.status, debouncedQ]);

  useEffect(() => {
    setLoading(true);
    loadSummary();
  }, [loadSummary]);

  useEffect(() => {
    async function loadLookups() {
      try {
        const [departments, jobs] = await Promise.all([
          api.list('departments'),
          api.list('jobs'),
        ]);
        setLookupOptions({
          department: departments.map((d) => ({ value: d.name, label: d.name })),
          job: jobs.map((j) => ({ value: j.id, label: j.title })),
        });
      } catch {
        /* optional */
      }
    }
    loadLookups();
  }, []);

  const jobOptions = summary?.jobs || [];

  return (
    <div className="recruitment-page">
      <div className="recruitment-hero">
        <div>
          <h4 className="page-heading mb-1">
            <i className="bi bi-briefcase" style={{ color: 'var(--fca-lime)' }} /> Recruitment
          </h4>
          <p className="text-muted mb-0">Pipeline, analytics, and hiring operations in one place.</p>
        </div>
        <div className="d-flex gap-2 flex-wrap">
          <Link to="/careers" className="btn btn-outline-primary btn-sm" target="_blank">
            <i className="bi bi-box-arrow-up-right me-1" /> Careers portal
          </Link>
        </div>
      </div>

      {loading && !summary ? (
        <div className="text-center py-4">
          <div className="spinner-border text-primary" role="status" />
        </div>
      ) : (
        <>
          <RecruitmentMetrics summary={summary} />
          <RecruitmentAnalytics summary={summary} />
          <RecruitmentCompliance />
        </>
      )}

      <ul className="nav nav-tabs recruitment-tabs mb-3">
        {VIEWS.map((tab) => (
          <li className="nav-item" key={tab.id}>
            <button
              type="button"
              className={`nav-link ${view === tab.id ? 'active' : ''}`}
              onClick={() => setView(tab.id)}
            >
              <i className={`bi ${tab.icon} me-1`} />
              {tab.label}
            </button>
          </li>
        ))}
      </ul>

      {error && <div className="alert alert-danger">{error}</div>}

      {view === 'pipeline' && summary && (
        <>
          <div className="recruitment-filters card mb-3">
            <div className="card-body py-3">
              <div className="row g-2 align-items-end">
                <div className="col-md-4">
                  <label className="form-label small mb-1">Search</label>
                  <input
                    type="search"
                    className="form-control form-control-sm"
                    placeholder="Name, email, or job title..."
                    value={filters.q}
                    onChange={(e) => setFilters((f) => ({ ...f, q: e.target.value }))}
                  />
                </div>
                <div className="col-md-3">
                  <label className="form-label small mb-1">Job</label>
                  <select
                    className="form-select form-select-sm"
                    value={filters.job}
                    onChange={(e) => setFilters((f) => ({ ...f, job: e.target.value }))}
                  >
                    <option value="">All jobs</option>
                    {jobOptions.map((j) => (
                      <option key={j.id} value={j.id}>{j.title}</option>
                    ))}
                  </select>
                </div>
                <div className="col-md-3">
                  <label className="form-label small mb-1">Status</label>
                  <select
                    className="form-select form-select-sm"
                    value={filters.status}
                    onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
                  >
                    <option value="">All statuses</option>
                    {['received', 'shortlisted', 'interviewed', 'hired', 'rejected'].map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>
                <div className="col-md-2">
                  <button
                    type="button"
                    className="btn btn-outline-secondary btn-sm w-100"
                    onClick={() => setFilters({ job: '', status: '', q: '' })}
                  >
                    Clear
                  </button>
                </div>
              </div>
            </div>
          </div>
          <RecruitmentPipeline
            pipeline={summary.pipeline}
            pipelineStages={summary.pipeline_stages}
            onRefresh={loadSummary}
            canManage={canManage}
          />
        </>
      )}

      {view === 'jobs' && (
        <RecruitmentJobsPanel canManage={canManage} onChanged={loadSummary} />
      )}

      {view === 'applications' && (
        <ResourceManager
          embedded
          tabs={[recruitmentApplicationsTab]}
          lookupOptions={lookupOptions}
          user={user}
        />
      )}
    </div>
  );
}
