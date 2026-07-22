import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import SettingsBackLink from '../components/SettingsBackLink';

export default function AuditLogs() {
  const { user } = useAuth();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!user?.is_admin) return;
    api.listRaw('audit-logs')
      .then((data) => setLogs(data.results || data))
      .catch((err) => setError(err.data?.detail || 'Failed to load audit logs.'))
      .finally(() => setLoading(false));
  }, [user]);

  if (!user?.is_admin) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div>
      <SettingsBackLink />
    <div className="card">
      <div className="card-body">
        <h5 className="card-title d-flex justify-content-between align-items-center flex-wrap gap-2">
          <span><i className="bi bi-journal-text" /> Audit Log</span>
          <span className="d-flex gap-2">
            <button
              type="button"
              className="btn btn-outline-secondary btn-sm"
              onClick={() => api.downloadAuditLog('csv')}
            >
              Export CSV
            </button>
            <button
              type="button"
              className="btn btn-outline-secondary btn-sm"
              onClick={() => api.downloadAuditLog('xlsx')}
            >
              Export Excel
            </button>
          </span>
        </h5>

        {error && <div className="alert alert-danger">{error}</div>}

        {loading ? (
          <div className="text-center py-4">
            <div className="spinner-border text-primary" role="status">
              <span className="visually-hidden">Loading...</span>
            </div>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="table table-sm table-hover align-middle">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>User</th>
                  <th>Action</th>
                  <th>Model</th>
                  <th>Object</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-muted text-center">No audit entries yet.</td>
                  </tr>
                ) : (
                  logs.map((log) => (
                    <tr key={log.id}>
                      <td className="text-nowrap">{new Date(log.timestamp).toLocaleString()}</td>
                      <td>{log.username || '—'}</td>
                      <td><span className="badge bg-secondary">{log.action}</span></td>
                      <td>{log.model_name}</td>
                      <td>{log.object_description || log.object_id || '—'}</td>
                      <td className="small text-muted">{log.details || '—'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
    </div>
  );
}
