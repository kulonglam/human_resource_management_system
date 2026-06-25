import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../api/client';

export default function CareerApply() {
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    cover_letter: '',
    eeo_gender: '',
    eeo_ethnicity: '',
  });
  const [resume, setResume] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    api.ensureCsrf().catch(() => {});
    api.getCareersJob(jobId)
      .then(setJob)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [jobId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      const formData = new FormData();
      Object.entries(form).forEach(([key, val]) => formData.append(key, val));
      if (resume) formData.append('resume', resume);
      await api.applyToCareersJob(jobId, formData);
      setSubmitted(true);
    } catch (err) {
      if (err.data && typeof err.data === 'object') {
        const messages = Object.entries(err.data)
          .map(([field, msgs]) => `${field}: ${Array.isArray(msgs) ? msgs.join(', ') : msgs}`)
          .join(' ');
        setError(messages || err.message);
      } else {
        setError(err.message);
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="careers-layout">
        <div className="text-center py-5">
          <div className="spinner-border text-primary" role="status" />
        </div>
      </div>
    );
  }

  if (error && !job) {
    return (
      <div className="careers-layout">
        <main className="careers-main">
          <div className="alert alert-danger">{error}</div>
          <Link to="/careers" className="btn btn-outline-primary btn-sm">Back to careers</Link>
        </main>
      </div>
    );
  }

  if (submitted) {
    return (
      <div className="careers-layout">
        <main className="careers-main careers-apply-success">
          <div className="card">
            <div className="card-body text-center py-5">
              <i className="bi bi-check-circle display-4 text-success mb-3" />
              <h2>Application submitted</h2>
              <p className="text-muted">Thank you for applying for <strong>{job.title}</strong>. Our team will review your application.</p>
              <Link to="/careers" className="btn btn-primary btn-sm">View other roles</Link>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="careers-layout">
      <header className="careers-header careers-header-compact">
        <div className="careers-header-inner">
          <Link to="/careers" className="careers-back"><i className="bi bi-arrow-left" /> All jobs</Link>
        </div>
      </header>

      <main className="careers-main">
        <div className="row g-4">
          <div className="col-lg-5">
            <div className="card">
              <div className="card-body">
                <span className="badge bg-primary mb-2">{job.department}</span>
                <h1 className="h3 mb-3">{job.title}</h1>
                <h6 className="text-muted text-uppercase small">About the role</h6>
                <p className="text-pre-wrap">{job.description}</p>
                <h6 className="text-muted text-uppercase small mt-3">Requirements</h6>
                <p className="text-pre-wrap">{job.requirements}</p>
                <p className="small text-muted mb-0">Apply by {job.deadline}</p>
              </div>
            </div>
          </div>

          <div className="col-lg-7">
            <div className="card">
              <div className="card-body">
                <h2 className="h5 mb-3">Submit your application</h2>
                {error && <div className="alert alert-danger py-2">{error}</div>}
                <form onSubmit={handleSubmit}>
                  <div className="row g-3">
                    <div className="col-md-6">
                      <label className="form-label">First name</label>
                      <input className="form-control" required value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
                    </div>
                    <div className="col-md-6">
                      <label className="form-label">Last name</label>
                      <input className="form-control" required value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
                    </div>
                    <div className="col-md-6">
                      <label className="form-label">Email</label>
                      <input type="email" className="form-control" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
                    </div>
                    <div className="col-md-6">
                      <label className="form-label">Phone</label>
                      <input className="form-control" required value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
                    </div>
                    <div className="col-12">
                      <label className="form-label">Cover letter</label>
                      <textarea className="form-control" rows={4} value={form.cover_letter} onChange={(e) => setForm({ ...form, cover_letter: e.target.value })} />
                    </div>
                    <div className="col-12">
                      <label className="form-label">Resume (PDF or Word)</label>
                      <input type="file" className="form-control" accept=".pdf,.doc,.docx" onChange={(e) => setResume(e.target.files[0] || null)} />
                    </div>
                    <div className="col-12">
                      <div className="card bg-light border-0">
                        <div className="card-body py-3">
                          <h6 className="small text-uppercase text-muted">Voluntary EEO self-identification (optional)</h6>
                          <div className="row g-2">
                            <div className="col-md-6">
                              <input className="form-control form-control-sm" placeholder="Gender (optional)" value={form.eeo_gender} onChange={(e) => setForm({ ...form, eeo_gender: e.target.value })} />
                            </div>
                            <div className="col-md-6">
                              <input className="form-control form-control-sm" placeholder="Ethnicity (optional)" value={form.eeo_ethnicity} onChange={(e) => setForm({ ...form, eeo_ethnicity: e.target.value })} />
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <button type="submit" className="btn btn-primary mt-3" disabled={submitting}>
                    {submitting ? 'Submitting...' : 'Submit application'}
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
