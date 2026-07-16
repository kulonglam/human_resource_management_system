import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function OpsCenter() {
  const { user } = useAuth();
  const [ops, setOps] = useState(null);
  const [slos, setSlos] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user?.is_admin) return;
    Promise.all([api.getOpsStatus(), api.getSLOMetrics()])
      .then(([opsData, sloData]) => {
        setOps(opsData);
        setSlos(sloData);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [user]);

  if (!user?.is_admin) return <Navigate to="/dashboard" replace />;

  return (
    <div>
      <h1 className="page-heading mb-3">
        <i className="bi bi-hdd-rack" /> Operations Center
      </h1>
      <p className="text-muted mb-4">
        Background jobs, backups, SLO health, and incident runbooks.
      </p>

      {error && <div className="alert alert-danger">{error}</div>}
      {loading ? (
        <div className="text-center py-5"><div className="spinner-border text-primary" /></div>
      ) : (
        <div className="row g-3">
          <div className="col-lg-4">
            <div className="card h-100">
              <div className="card-body">
                <h6 className="card-title">Queue / jobs</h6>
                <ul className="list-unstyled small mb-0">
                  <li>Scheduled: {ops?.jobs?.scheduled ?? 0}</li>
                  <li>Success: {ops?.jobs?.success ?? 0}</li>
                  <li>Failed: {ops?.jobs?.failed ?? 0}</li>
                  <li>Queued: {ops?.jobs?.queued ?? 0}</li>
                </ul>
                <p className="small text-muted mt-3 mb-0">{ops?.worker_hint}</p>
              </div>
            </div>
          </div>
          <div className="col-lg-4">
            <div className="card h-100">
              <div className="card-body">
                <h6 className="card-title">SLO (current hour)</h6>
                {slos && (
                  <>
                    <p className="mb-1">Availability: <strong>{slos.availability_percent}%</strong></p>
                    <p className="mb-1">Avg latency: <strong>{slos.avg_latency_ms} ms</strong></p>
                    <p className="mb-1">Requests: {slos.requests} · 5xx: {slos.server_errors}</p>
                    <span className={`badge ${slos.within_slo ? 'bg-success' : 'bg-danger'}`}>
                      {slos.within_slo ? 'Within SLO' : 'SLO breached'}
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>
          <div className="col-lg-4">
            <div className="card h-100">
              <div className="card-body">
                <h6 className="card-title">Recent backups</h6>
                {(ops?.backups || []).length === 0 ? (
                  <p className="small text-muted mb-0">No local backups found.</p>
                ) : (
                  <ul className="list-unstyled small mb-0">
                    {ops.backups.slice(0, 5).map((b) => (
                      <li key={b.name}>{b.name}</li>
                    ))}
                  </ul>
                )}
                <p className="small text-muted mt-2 mb-0">
                  Restore: <code>python manage.py restore_database path --force</code>
                </p>
              </div>
            </div>
          </div>
          <div className="col-12">
            <div className="card">
              <div className="card-body">
                <h6 className="card-title">Runbooks</h6>
                <div className="row g-3">
                  {(ops?.runbooks || []).map((rb) => (
                    <div className="col-md-4" key={rb.id}>
                      <h6 className="small fw-semibold">{rb.title}</h6>
                      <ol className="small ps-3 mb-0">
                        {rb.checklist.map((step) => <li key={step}>{step}</li>)}
                      </ol>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
