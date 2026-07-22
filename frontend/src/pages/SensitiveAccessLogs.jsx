import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import SettingsBackLink from '../components/SettingsBackLink';

export default function SensitiveAccessLogs() {
  const { user } = useAuth();
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.getSensitiveAccessLogs()
      .then(setRows)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (!user?.is_admin) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div>
      <SettingsBackLink />
      <h1 className="page-heading mb-3">
        <i className="bi bi-shield-exclamation" /> Sensitive Data Access Log
      </h1>
      <p className="text-muted mb-4">
        Audit trail of when administrators or authorized managers viewed encrypted employee PII.
      </p>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="card">
        <div className="card-body p-0">
          {loading ? (
            <div className="text-center py-4">
              <div className="spinner-border text-primary" role="status" />
            </div>
          ) : rows.length === 0 ? (
            <p className="text-muted p-4 mb-0">No sensitive access events recorded yet.</p>
          ) : (
            <div className="table-responsive">
              <table className="table table-hover mb-0 align-middle">
                <thead>
                  <tr>
                    <th>When</th>
                    <th>User</th>
                    <th>Employee</th>
                    <th>Fields</th>
                    <th>IP</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.id}>
                      <td className="text-nowrap small">
                        {new Date(row.accessed_at).toLocaleString('en-UG')}
                      </td>
                      <td>{row.username || '—'}</td>
                      <td>{row.employee_name || row.employee}</td>
                      <td className="small">{(row.fields_accessed || []).join(', ')}</td>
                      <td className="small text-muted">{row.ip_address || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
