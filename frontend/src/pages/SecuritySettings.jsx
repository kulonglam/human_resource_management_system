import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function SecuritySettings() {
  const { user, refreshUser } = useAuth();
  const [setup, setSetup] = useState(null);
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user?.is_admin && !user.mfa_enabled) {
      api.getMfaSetup()
        .then(setSetup)
        .catch((err) => setError(err.data?.detail || 'Unable to load MFA setup.'));
    }
  }, [user]);

  if (!user?.is_admin) {
    return <Navigate to="/dashboard" replace />;
  }

  if (user.mfa_enabled) {
    return (
      <div className="card">
        <div className="card-body">
          <h5 className="card-title">
            <i className="bi bi-shield-lock" /> Security Settings
          </h5>
          <div className="alert alert-success mb-0">
            Multi-factor authentication is enabled for your account.
          </div>
        </div>
      </div>
    );
  }

  const handleEnable = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);
    try {
      await api.enableMfa(code);
      await refreshUser();
      setSuccess('MFA enabled successfully. You will need your authenticator app on future logins.');
      setSetup(null);
    } catch (err) {
      setError(err.data?.detail || 'Invalid verification code.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <div className="card-body">
        <h5 className="card-title">
          <i className="bi bi-shield-lock" /> Enable Multi-Factor Authentication
        </h5>

        {user.mfa_setup_required && (
          <div className="alert alert-warning">
            Admin accounts must enable MFA before using the system.
          </div>
        )}

        {error && <div className="alert alert-danger">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        {setup && !success && (
          <>
            <p>
              Scan this secret in Google Authenticator, Microsoft Authenticator, or a compatible TOTP app.
            </p>
            <div className="mb-3">
              <label className="form-label">Secret key</label>
              <input type="text" className="form-control font-monospace" readOnly value={setup.secret} />
            </div>
            <p className="small text-muted text-break">{setup.provisioning_uri}</p>

            <form onSubmit={handleEnable}>
              <div className="mb-3">
                <label className="form-label">Enter code from app</label>
                <input
                  type="text"
                  className="form-control"
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="000000"
                  required
                />
              </div>
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? 'Enabling...' : 'Enable MFA'}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
