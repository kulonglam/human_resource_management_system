import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function ComplianceSettings() {
  const { user } = useAuth();
  const [policies, setPolicies] = useState([]);
  const [preview, setPreview] = useState([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [erasureEmail, setErasureEmail] = useState('');
  const [erasureId, setErasureId] = useState('');
  const [erasing, setErasing] = useState(false);

  const load = () => {
    setLoading(true);
    Promise.all([api.getRetentionPolicies(), api.getRetentionPreview()])
      .then(([policyData, previewData]) => {
        setPolicies(policyData.results || policyData);
        setPreview(previewData);
      })
      .catch((err) => setError(err.data?.detail || 'Failed to load compliance settings.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (user?.is_admin) load();
  }, [user]);

  if (!user?.is_admin) {
    return <Navigate to="/dashboard" replace />;
  }

  const handlePolicyChange = async (policy, field, value) => {
    setError('');
    try {
      await api.updateRetentionPolicy(policy.id, { [field]: value });
      load();
      setSuccess('Retention policy updated.');
    } catch (err) {
      setError(err.data?.detail || 'Update failed.');
    }
  };

  const handleRunRetention = async (dryRun) => {
    setRunning(true);
    setError('');
    setSuccess('');
    try {
      const result = await api.runRetentionPolicies(dryRun);
      load();
      const label = dryRun ? 'Dry run complete' : 'Retention purge complete';
      setSuccess(`${label}: ${result.total_purged} record(s) eligible or purged.`);
    } catch (err) {
      setError(err.data?.detail || 'Retention run failed.');
    } finally {
      setRunning(false);
    }
  };

  const handleErasure = async (e) => {
    e.preventDefault();
    if (!window.confirm(`Anonymize all personal data for employee #${erasureId}? This cannot be undone.`)) {
      return;
    }
    setErasing(true);
    setError('');
    setSuccess('');
    try {
      await api.requestGDPRErasure(erasureId, erasureEmail);
      setSuccess(`Employee #${erasureId} personal data anonymized.`);
      setErasureEmail('');
      setErasureId('');
    } catch (err) {
      setError(err.data?.detail || 'Erasure failed.');
    } finally {
      setErasing(false);
    }
  };

  return (
    <div className="card">
      <div className="card-body">
        <h5 className="card-title">
          <i className="bi bi-shield-check" /> Compliance & Data Retention
        </h5>
        <p className="text-muted">
          Configure how long operational records are kept and manage GDPR erasure requests.
        </p>

        {error && <div className="alert alert-danger">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        {loading ? (
          <div className="text-center py-4">
            <div className="spinner-border text-primary" role="status" />
          </div>
        ) : (
          <>
            <h6 className="mt-4">Retention policies</h6>
            <div className="table-responsive mb-3">
              <table className="table table-sm align-middle">
                <thead>
                  <tr>
                    <th>Category</th>
                    <th>Retention (days)</th>
                    <th>Active</th>
                    <th>Eligible now</th>
                    <th>Last run</th>
                  </tr>
                </thead>
                <tbody>
                  {policies.map((policy) => {
                    const previewRow = preview.find((p) => p.category === policy.category);
                    return (
                      <tr key={policy.id}>
                        <td>
                          <strong>{policy.category_label}</strong>
                          {policy.description && (
                            <div className="small text-muted">{policy.description}</div>
                          )}
                        </td>
                        <td style={{ maxWidth: 120 }}>
                          <input
                            type="number"
                            min={1}
                            className="form-control form-control-sm"
                            value={policy.retention_days}
                            onChange={(e) =>
                              handlePolicyChange(policy, 'retention_days', Number(e.target.value))
                            }
                          />
                        </td>
                        <td>
                          <div className="form-check form-switch">
                            <input
                              className="form-check-input"
                              type="checkbox"
                              checked={policy.is_active}
                              onChange={(e) =>
                                handlePolicyChange(policy, 'is_active', e.target.checked)
                              }
                            />
                          </div>
                        </td>
                        <td>{previewRow?.eligible_count ?? '—'}</td>
                        <td className="small text-muted">
                          {policy.last_run_at
                            ? `${new Date(policy.last_run_at).toLocaleString()} (${policy.last_purged_count} purged)`
                            : 'Never'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="d-flex gap-2 mb-4">
              <button
                type="button"
                className="btn btn-outline-secondary btn-sm"
                disabled={running}
                onClick={() => handleRunRetention(true)}
              >
                Preview purge
              </button>
              <button
                type="button"
                className="btn btn-warning btn-sm"
                disabled={running}
                onClick={() => handleRunRetention(false)}
              >
                {running ? 'Running…' : 'Run retention purge'}
              </button>
            </div>

            <h6>GDPR right to erasure</h6>
            <p className="small text-muted">
              Anonymizes employee PII and deactivates the linked user account. Employment records are retained in anonymized form.
            </p>
            <form className="row g-2 align-items-end" onSubmit={handleErasure}>
              <div className="col-md-3">
                <label className="form-label">Employee ID</label>
                <input
                  type="number"
                  className="form-control form-control-sm"
                  value={erasureId}
                  onChange={(e) => setErasureId(e.target.value)}
                  required
                />
              </div>
              <div className="col-md-5">
                <label className="form-label">Confirm employee email</label>
                <input
                  type="email"
                  className="form-control form-control-sm"
                  value={erasureEmail}
                  onChange={(e) => setErasureEmail(e.target.value)}
                  placeholder="employee@example.com"
                  required
                />
              </div>
              <div className="col-md-4">
                <button type="submit" className="btn btn-danger btn-sm" disabled={erasing}>
                  {erasing ? 'Processing…' : 'Anonymize employee data'}
                </button>
              </div>
            </form>

            <p className="small text-muted mt-3 mb-0">
              Schedule automated purges with{' '}
              <code>python manage.py apply_retention_policies</code> (e.g. nightly cron).
            </p>
          </>
        )}
      </div>
    </div>
  );
}
