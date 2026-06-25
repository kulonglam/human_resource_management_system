import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { renderStatus } from '../config/shared';
import ApplicationInterviews from '../components/recruitment/ApplicationInterviews';
import ApplicationNotes from '../components/recruitment/ApplicationNotes';
import ApplicationOffers from '../components/recruitment/ApplicationOffers';
import ApplicationScorecards from '../components/recruitment/ApplicationScorecards';
import HireOnboardingPanel from '../components/recruitment/HireOnboardingPanel';
import ResumePreview from '../components/recruitment/ResumePreview';

const STATUS_STEPS = ['received', 'shortlisted', 'interviewed', 'hired'];

const SOURCE_LABELS = {
  careers_portal: 'Careers portal',
  referral: 'Referral',
  linkedin: 'LinkedIn',
  agency: 'Agency',
  manual: 'Manual',
  other: 'Other',
};

function StarRating({ value, onChange, readonly }) {
  return (
    <div className="recruitment-rating">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          className={`recruitment-star ${star <= (value || 0) ? 'active' : ''}`}
          disabled={readonly}
          onClick={() => onChange?.(star)}
          aria-label={`Rate ${star}`}
        >
          <i className="bi bi-star-fill" />
        </button>
      ))}
    </div>
  );
}

function Timeline({ application, approvalStatus }) {
  const currentIdx = STATUS_STEPS.indexOf(application.status);

  return (
    <div className="recruitment-timeline">
      <h6 className="text-muted text-uppercase small mb-3">Application progress</h6>
      <ul className="list-unstyled mb-0">
        {STATUS_STEPS.map((step, idx) => {
          const done = application.status === 'rejected'
            ? idx <= currentIdx && currentIdx >= 0
            : idx <= currentIdx;
          const active = application.status === step;
          return (
            <li key={step} className={`recruitment-timeline-step ${done ? 'done' : ''} ${active ? 'active' : ''}`}>
              <span className="recruitment-timeline-dot" />
              <div>
                <div className="fw-semibold text-capitalize">{step}</div>
                {active && application.status !== 'rejected' && (
                  <div className="small text-muted">Current stage</div>
                )}
              </div>
            </li>
          );
        })}
        {application.status === 'rejected' && (
          <li className="recruitment-timeline-step done active">
            <span className="recruitment-timeline-dot bg-danger" />
            <div>
              <div className="fw-semibold text-danger">Rejected</div>
            </div>
          </li>
        )}
      </ul>

      {approvalStatus && (
        <div className="mt-4">
          <h6 className="text-muted text-uppercase small mb-2">Approval workflow</h6>
          <div className="small mb-2">
            <span className="badge bg-secondary me-1">{approvalStatus.workflow}</span>
            <span className={`badge bg-${approvalStatus.status === 'approved' ? 'success' : approvalStatus.status === 'rejected' ? 'danger' : 'warning'}`}>
              {approvalStatus.status}
            </span>
          </div>
          {approvalStatus.decisions?.map((d) => (
            <div className="small border-bottom py-2" key={`${d.step_order}-${d.decided_at}`}>
              <strong>{d.step_label}</strong> — {d.decision}
              {d.comment && <div className="text-muted">{d.comment}</div>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ApplicationDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [application, setApplication] = useState(null);
  const [error, setError] = useState('');
  const [actionError, setActionError] = useState('');
  const [comment, setComment] = useState('');
  const [busy, setBusy] = useState(false);

  const canManage = Boolean(user?.is_admin || user?.is_manager);

  const load = useCallback(async () => {
    setError('');
    try {
      const data = await api.get('applications', id);
      setApplication(data);
    } catch (err) {
      setError(err.message);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  const runAction = async (action) => {
    setActionError('');
    setBusy(true);
    try {
      const payload = action === 'reject' ? { reason: comment, comment } : { comment };
      await api.action('applications', id, action, payload);
      setComment('');
      await load();
    } catch (err) {
      setActionError(err.data?.detail || err.message);
    } finally {
      setBusy(false);
    }
  };

  const advanceStatus = async (status) => {
    setActionError('');
    setBusy(true);
    try {
      await api.update('applications', id, { status });
      await load();
    } catch (err) {
      setActionError(err.data?.detail || err.message);
    } finally {
      setBusy(false);
    }
  };

  const setRating = async (rating) => {
    if (!canManage) return;
    try {
      await api.update('applications', id, { rating });
      await load();
    } catch (err) {
      setActionError(err.data?.detail || err.message);
    }
  };

  if (error) return <div className="alert alert-danger">{error}</div>;
  if (!application) {
    return (
      <div className="text-center py-5">
        <div className="spinner-border text-primary" role="status" />
      </div>
    );
  }

  const terminal = ['hired', 'rejected'].includes(application.status);

  return (
    <>
      <div className="recruitment-app-header">
        <div>
          <h4 className="page-heading mb-1">{application.full_name}</h4>
          <p className="text-muted mb-2">
            Applied for <Link to={`/recruitment/jobs/${application.job}`}>{application.job_title}</Link>
          </p>
          <div className="d-flex align-items-center flex-wrap gap-2">
            {renderStatus(application.status)}
            <span className="badge bg-light text-dark border">
              {SOURCE_LABELS[application.source] || application.source_display || 'Manual'}
            </span>
            <span className="small text-muted">
              Applied {new Date(application.applied_on).toLocaleString()}
            </span>
          </div>
          <div className="mt-2">
            <span className="small text-muted me-2">Candidate rating</span>
            <StarRating value={application.rating} onChange={setRating} readonly={!canManage} />
          </div>
        </div>
        <Link to="/recruitment" className="btn btn-outline-secondary btn-sm">Back to recruitment</Link>
      </div>

      <div className="row g-3">
        <div className="col-lg-8">
          <div className="card mb-3">
            <div className="card-body">
              <h5 className="card-title">Contact</h5>
              <dl className="row mb-0">
                <div className="col-md-6">
                  <dt className="text-muted small">Email</dt>
                  <dd><a href={`mailto:${application.email}`}>{application.email}</a></dd>
                </div>
                <div className="col-md-6">
                  <dt className="text-muted small">Phone</dt>
                  <dd>{application.phone || '—'}</dd>
                </div>
              </dl>
            </div>
          </div>

          <ApplicationInterviews applicationId={id} canManage={canManage} onChanged={load} />
          <ApplicationScorecards applicationId={id} jobId={application.job} />
          <ApplicationOffers applicationId={id} canManage={canManage} />
          <HireOnboardingPanel application={application} canManage={canManage} />
          <ApplicationNotes applicationId={id} canManage={canManage} />

          <div className="card mb-3">
            <div className="card-body">
              <h5 className="card-title">Cover letter</h5>
              <p className="mb-0 text-pre-wrap">{application.cover_letter || 'No cover letter provided.'}</p>
            </div>
          </div>

          <div className="card mb-3">
            <div className="card-body">
              <div className="d-flex justify-content-between align-items-center mb-3">
                <h5 className="card-title mb-0">Resume</h5>
                {application.resume_url && (
                  <a href={application.resume_url} target="_blank" rel="noreferrer" className="btn btn-outline-primary btn-sm">
                    Open in new tab
                  </a>
                )}
              </div>
              {application.resume_url ? (
                <ResumePreview url={application.resume_url} />
              ) : (
                <p className="text-muted mb-0">No resume uploaded.</p>
              )}
            </div>
          </div>
        </div>

        <div className="col-lg-4">
          <div className="card mb-3">
            <div className="card-body">
              <Timeline application={application} approvalStatus={application.approval_status} />
            </div>
          </div>

          {canManage && !terminal && (
            <div className="card">
              <div className="card-body">
                <h5 className="card-title">Actions</h5>
                <textarea
                  className="form-control form-control-sm mb-3"
                  rows={2}
                  placeholder="Comment or rejection reason (optional)"
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  disabled={busy}
                />
                {actionError && <div className="alert alert-danger py-2 small">{actionError}</div>}
                <div className="d-grid gap-2">
                  {application.status === 'received' && (
                    <button type="button" className="btn btn-outline-info btn-sm" disabled={busy} onClick={() => advanceStatus('shortlisted')}>
                      Mark shortlisted
                    </button>
                  )}
                  {application.status === 'shortlisted' && (
                    <button type="button" className="btn btn-outline-info btn-sm" disabled={busy} onClick={() => advanceStatus('interviewed')}>
                      Mark interviewed
                    </button>
                  )}
                  <button type="button" className="btn btn-success btn-sm" disabled={busy} onClick={() => runAction('approve')}>
                    {application.status === 'interviewed' ? 'Hire candidate' : 'Advance (approval)'}
                  </button>
                  <button type="button" className="btn btn-outline-danger btn-sm" disabled={busy} onClick={() => runAction('reject')}>
                    Reject
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
