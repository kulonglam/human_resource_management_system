import { useCallback, useEffect, useState } from 'react';
import { api } from '../../api/client';

const STATUS_OPTIONS = [
  { value: 'scheduled', label: 'Scheduled' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
  { value: 'no_show', label: 'No show' },
];

export default function ApplicationInterviews({ applicationId, canManage, onChanged }) {
  const [interviews, setInterviews] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    scheduled_at: '',
    duration_minutes: 60,
    location: '',
    interviewer_name: '',
    notes: '',
  });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.list('interviews', `application=${applicationId}`);
      setInterviews(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [applicationId]);

  useEffect(() => {
    load();
  }, [load]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      await api.create('interviews', {
        application: Number(applicationId),
        ...form,
        duration_minutes: Number(form.duration_minutes),
      });
      setForm({ scheduled_at: '', duration_minutes: 60, location: '', interviewer_name: '', notes: '' });
      setShowForm(false);
      load();
      onChanged?.();
    } catch (err) {
      setError(err.data?.detail || err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const updateStatus = async (interview, status) => {
    try {
      await api.update('interviews', interview.id, { status });
      load();
    } catch (err) {
      setError(err.data?.detail || err.message);
    }
  };

  return (
    <div className="card mb-3">
      <div className="card-body">
        <div className="d-flex justify-content-between align-items-center mb-3">
          <h5 className="card-title mb-0">Interviews</h5>
          {canManage && (
            <button type="button" className="btn btn-outline-primary btn-sm" onClick={() => setShowForm(!showForm)}>
              {showForm ? 'Cancel' : 'Schedule'}
            </button>
          )}
        </div>

        {error && <div className="alert alert-danger py-2 small">{error}</div>}

        {showForm && canManage && (
          <form className="recruitment-interview-form mb-3" onSubmit={handleSubmit}>
            <div className="row g-2">
              <div className="col-md-6">
                <label className="form-label small">Date & time</label>
                <input type="datetime-local" className="form-control form-control-sm" required value={form.scheduled_at} onChange={(e) => setForm({ ...form, scheduled_at: e.target.value })} />
              </div>
              <div className="col-md-3">
                <label className="form-label small">Duration (min)</label>
                <input type="number" className="form-control form-control-sm" min={15} step={15} value={form.duration_minutes} onChange={(e) => setForm({ ...form, duration_minutes: e.target.value })} />
              </div>
              <div className="col-md-3">
                <label className="form-label small">Interviewer</label>
                <input className="form-control form-control-sm" value={form.interviewer_name} onChange={(e) => setForm({ ...form, interviewer_name: e.target.value })} />
              </div>
              <div className="col-12">
                <label className="form-label small">Location / video link</label>
                <input className="form-control form-control-sm" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} placeholder="Zoom link or meeting room" />
              </div>
              <div className="col-12">
                <label className="form-label small">Notes</label>
                <textarea className="form-control form-control-sm" rows={2} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
              </div>
            </div>
            <button type="submit" className="btn btn-primary btn-sm mt-2" disabled={submitting}>
              {submitting ? 'Scheduling...' : 'Schedule interview'}
            </button>
          </form>
        )}

        {loading ? (
          <div className="spinner-border spinner-border-sm text-primary" role="status" />
        ) : interviews.length === 0 ? (
          <p className="text-muted small mb-0">No interviews scheduled.</p>
        ) : (
          <div className="recruitment-interviews-list">
            {interviews.map((iv) => (
              <div className="recruitment-interview" key={iv.id}>
                <div className="d-flex justify-content-between align-items-start gap-2">
                  <div>
                    <div className="fw-semibold">{new Date(iv.scheduled_at).toLocaleString()}</div>
                    <div className="small text-muted">
                      {iv.duration_minutes} min
                      {iv.interviewer_name && ` · ${iv.interviewer_name}`}
                    </div>
                    {iv.location && <div className="small"><i className="bi bi-geo-alt me-1" />{iv.location}</div>}
                    {iv.notes && <p className="small mb-0 mt-1 text-pre-wrap">{iv.notes}</p>}
                  </div>
                  <span className={`badge bg-${iv.status === 'completed' ? 'success' : iv.status === 'cancelled' ? 'secondary' : iv.status === 'no_show' ? 'danger' : 'warning'}`}>
                    {iv.status_display || iv.status}
                  </span>
                </div>
                {canManage && iv.status === 'scheduled' && (
                  <div className="d-flex gap-1 mt-2 flex-wrap">
                    <a href={`/api/v1/interviews/${iv.id}/calendar.ics`} className="btn btn-outline-info btn-sm" download>
                      <i className="bi bi-calendar-plus me-1" />Calendar (.ics)
                    </a>
                    {STATUS_OPTIONS.filter((o) => o.value !== 'scheduled').map((opt) => (
                      <button key={opt.value} type="button" className="btn btn-outline-secondary btn-sm" onClick={() => updateStatus(iv, opt.value)}>
                        {opt.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
