import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../api/client';

import JobEnterpriseConfig from './JobEnterpriseConfig';

function JobFormModal({ job, departments, onClose, onSaved }) {
  const [form, setForm] = useState({
    title: job?.title || '',
    department: job?.department || '',
    description: job?.description || '',
    requirements: job?.requirements || '',
    deadline: job?.deadline || '',
    is_open: job?.is_open ?? true,
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      if (job) {
        await api.update('jobs', job.id, form);
      } else {
        await api.create('jobs', form);
      }
      onSaved();
      onClose();
    } catch (err) {
      setError(err.data?.detail || err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <div className="modal show d-block" tabIndex="-1">
        <div className="modal-dialog modal-lg">
          <div className="modal-content">
            <form onSubmit={handleSubmit}>
              <div className="modal-header">
                <h5 className="modal-title">{job ? 'Edit' : 'New'} job posting</h5>
                <button type="button" className="btn-close" onClick={onClose} />
              </div>
              <div className="modal-body">
                {error && <div className="alert alert-danger py-2">{error}</div>}
                <div className="row g-3">
                  <div className="col-md-8">
                    <label className="form-label">Title</label>
                    <input className="form-control form-control-sm" required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
                  </div>
                  <div className="col-md-4">
                    <label className="form-label">Department</label>
                    <select className="form-select form-select-sm" required value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })}>
                      <option value="">Select...</option>
                      {departments.map((d) => (
                        <option key={d.value} value={d.value}>{d.label}</option>
                      ))}
                    </select>
                  </div>
                  <div className="col-md-6">
                    <label className="form-label">Deadline</label>
                    <input type="date" className="form-control form-control-sm" required value={form.deadline} onChange={(e) => setForm({ ...form, deadline: e.target.value })} />
                  </div>
                  <div className="col-md-6 d-flex align-items-end">
                    <div className="form-check">
                      <input type="checkbox" className="form-check-input" id="job-open" checked={form.is_open} onChange={(e) => setForm({ ...form, is_open: e.target.checked })} />
                      <label className="form-check-label" htmlFor="job-open">Open for applications</label>
                    </div>
                  </div>
                  <div className="col-12">
                    <label className="form-label">Description</label>
                    <textarea className="form-control form-control-sm" rows={3} required value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
                  </div>
                  <div className="col-12">
                    <label className="form-label">Requirements</label>
                    <textarea className="form-control form-control-sm" rows={3} required value={form.requirements} onChange={(e) => setForm({ ...form, requirements: e.target.value })} />
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>{submitting ? 'Saving...' : 'Save'}</button>
              </div>
            </form>
          </div>
        </div>
      </div>
      <div className="modal-backdrop show" />
    </>
  );
}

export default function RecruitmentJobsPanel({ canManage, onChanged }) {
  const [jobs, setJobs] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(null);
  const [enterpriseJobId, setEnterpriseJobId] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [jobRows, deptRows] = await Promise.all([
        api.list('jobs'),
        api.list('departments'),
      ]);
      setJobs(jobRows);
      setDepartments(deptRows.map((d) => ({ value: d.name, label: d.name })));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleSaved = () => {
    load();
    onChanged?.();
  };

  const copyCareersLink = (jobId) => {
    const url = `${window.location.origin}/careers/${jobId}`;
    navigator.clipboard.writeText(url);
  };

  if (loading) {
    return (
      <div className="text-center py-4">
        <div className="spinner-border text-primary" role="status" />
      </div>
    );
  }

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <p className="text-muted small mb-0">Manage postings and share public apply links.</p>
        {canManage && (
          <button type="button" className="btn btn-primary btn-sm" onClick={() => setModal({})}>
            <i className="bi bi-plus-lg" /> New job
          </button>
        )}
      </div>

      <div className="recruitment-jobs-grid">
        {jobs.map((job) => (
          <div className={`recruitment-job-card ${job.is_open ? '' : 'recruitment-job-card-closed'}`} key={job.id}>
            <div className="recruitment-job-card-head">
              <div>
                <h6 className="mb-1">{job.title}</h6>
                <div className="text-muted small">{job.department}</div>
              </div>
              <span className={`badge ${job.is_open ? 'bg-success' : 'bg-secondary'}`}>
                {job.is_open ? 'Open' : 'Closed'}
              </span>
            </div>
            <p className="recruitment-job-card-desc">{job.description}</p>
            <div className="recruitment-job-card-meta">
              <span><i className="bi bi-people me-1" />{job.application_count} applicants</span>
              <span><i className="bi bi-calendar me-1" />Deadline {job.deadline}</span>
            </div>
            <div className="recruitment-job-card-actions">
              <Link to={`/recruitment/jobs/${job.id}`} className="btn btn-outline-secondary btn-sm">Details</Link>
              <Link to={`/careers/${job.id}`} className="btn btn-outline-primary btn-sm" target="_blank">Public page</Link>
              {job.is_open && (
                <button type="button" className="btn btn-outline-info btn-sm" onClick={() => copyCareersLink(job.id)}>
                  Copy link
                </button>
              )}
              {canManage && (
                <>
                  <button type="button" className="btn btn-outline-dark btn-sm" onClick={() => setEnterpriseJobId(job.id)}>
                    Enterprise setup
                  </button>
                  <button type="button" className="btn btn-outline-primary btn-sm" onClick={() => setModal(job)}>
                    Edit
                  </button>
                </>
              )}
            </div>
          </div>
        ))}
        {!jobs.length && (
          <div className="text-center text-muted py-5">No job postings yet.</div>
        )}
      </div>

      {modal && (
        <JobFormModal
          job={modal.id ? modal : null}
          departments={departments}
          onClose={() => setModal(null)}
          onSaved={handleSaved}
        />
      )}
      {enterpriseJobId && (
        <JobEnterpriseConfig
          jobId={enterpriseJobId}
          canManage={canManage}
          onClose={() => setEnterpriseJobId(null)}
        />
      )}
    </>
  );
}
