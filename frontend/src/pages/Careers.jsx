import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';

export default function Careers() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.ensureCsrf().catch(() => {});
    api.getCareersJobs()
      .then(setJobs)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="careers-layout">
      <header className="careers-header">
        <div className="careers-header-inner">
          <div>
            <h1 className="careers-title">Join our team</h1>
            <p className="careers-subtitle">Explore open roles and apply in minutes.</p>
          </div>
          <Link to="/login" className="btn btn-outline-light btn-sm">Employee login</Link>
        </div>
      </header>

      <main className="careers-main">
        {loading && (
          <div className="text-center py-5">
            <div className="spinner-border text-primary" role="status" />
          </div>
        )}
        {error && <div className="alert alert-danger">{error}</div>}
        {!loading && !error && (
          <div className="careers-jobs-grid">
            {jobs.map((job) => (
              <article className="careers-job-card" key={job.id}>
                <div className="careers-job-card-head">
                  <h2>{job.title}</h2>
                  <span className="badge bg-primary">{job.department}</span>
                </div>
                <p className="careers-job-desc">{job.description}</p>
                <div className="careers-job-meta">
                  <span><i className="bi bi-calendar me-1" />Apply by {job.deadline}</span>
                  <span><i className="bi bi-clock me-1" />Posted {new Date(job.posted_on).toLocaleDateString()}</span>
                </div>
                <Link to={`/careers/${job.id}`} className="btn btn-primary btn-sm">
                  View & apply
                </Link>
              </article>
            ))}
            {!jobs.length && (
              <div className="text-center text-muted py-5">No open positions right now. Check back soon.</div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
