import { useEffect, useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const { user, login, verifyMfa } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [mfaCode, setMfaCode] = useState('');
  const [mfaToken, setMfaToken] = useState('');
  const [mfaStep, setMfaStep] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [allowRegistration, setAllowRegistration] = useState(false);
  const [ssoProviders, setSsoProviders] = useState([]);

  useEffect(() => {
    api.getAuthConfig()
      .then((data) => setAllowRegistration(Boolean(data.allow_registration)))
      .catch(() => setAllowRegistration(false));
    api.getSsoConfig()
      .then((data) => setSsoProviders(data.providers || []))
      .catch(() => setSsoProviders([]));

    const params = new URLSearchParams(window.location.search);
    if (params.get('sso_error')) {
      setError(`SSO login failed: ${params.get('sso_error').replace(/_/g, ' ')}`);
    }
    if (params.get('mfa_required') === '1' && params.get('mfa_token')) {
      setMfaToken(params.get('mfa_token'));
      setMfaStep(true);
    }
    if (params.get('mfa_setup_required') === '1') {
      setError('Please complete MFA setup after signing in.');
    }
  }, []);

  if (user) {
    if (user.mfa_setup_required) {
      return <Navigate to="/settings/security" replace />;
    }
    return <Navigate to="/dashboard" replace />;
  }

  const redirectAfterLogin = (me) => {
    if (me.mfa_setup_required) {
      navigate('/settings/security', { replace: true });
      return;
    }
    const redirectTo = location.state?.from?.pathname || '/dashboard';
    navigate(redirectTo, { replace: true });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const result = await login(username, password);
      if (result.mfa_required) {
        setMfaToken(result.mfa_token);
        setMfaStep(true);
        return;
      }
      redirectAfterLogin(result);
    } catch (err) {
      const message =
        err.data?.non_field_errors?.[0] ||
        err.data?.detail ||
        'Invalid username or password.';
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleMfaSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const me = await verifyMfa(mfaToken, mfaCode);
      redirectAfterLogin(me);
    } catch (err) {
      setError(err.data?.detail || 'Invalid verification code.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="card shadow" style={{ width: '100%', maxWidth: 480 }}>
        <div className="card-body p-4">
          <h4 className="card-title text-center mb-4">
            <i className="bi bi-person-lock" /> HRMIS Login
          </h4>

          {error && <div className="alert alert-danger" role="alert">{error}</div>}

          {!mfaStep ? (
            <form onSubmit={handleSubmit}>
              <div className="mb-3">
                <label className="form-label" htmlFor="login-username">Username</label>
                <input
                  type="text"
                  id="login-username"
                  className="form-control"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Username"
                  required
                />
              </div>

              <div className="mb-3">
                <label className="form-label" htmlFor="login-password">Password</label>
                <div className="position-relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    id="login-password"
                    className="form-control"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Password"
                    required
                    style={{ paddingRight: '2.5rem' }}
                  />
                  <button
                    type="button"
                    className="btn btn-link position-absolute end-0 top-50 translate-middle-y"
                    onClick={() => setShowPassword((v) => !v)}
                    style={{ zIndex: 10 }}
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    <i className={`bi ${showPassword ? 'bi-eye-slash' : 'bi-eye'}`} aria-hidden="true" />
                  </button>
                </div>
              </div>

              <div className="d-grid">
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  <i className="bi bi-box-arrow-in-right" /> {submitting ? 'Signing in...' : 'Login'}
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleMfaSubmit}>
              <p className="text-muted">
                Enter the 6-digit code from your authenticator app.
              </p>
              <div className="mb-3">
                <label className="form-label" htmlFor="login-mfa-code">Verification code</label>
                <input
                  type="text"
                  id="login-mfa-code"
                  className="form-control"
                  value={mfaCode}
                  onChange={(e) => setMfaCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="000000"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  required
                />
              </div>
              <div className="d-grid gap-2">
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? 'Verifying...' : 'Verify'}
                </button>
                <button
                  type="button"
                  className="btn btn-outline-secondary"
                  onClick={() => {
                    setMfaStep(false);
                    setMfaCode('');
                    setMfaToken('');
                  }}
                >
                  Back
                </button>
              </div>
            </form>
          )}

          {allowRegistration && !mfaStep && (
            <p className="text-center mt-3 mb-0">
              No account? <Link to="/register">Register</Link>
            </p>
          )}

          {ssoProviders.length > 0 && !mfaStep && (
            <div className="mt-4">
              <div className="text-center text-muted small mb-2">Or continue with</div>
              <div className="d-grid gap-2">
                {ssoProviders.map((provider) => (
                  <button
                    key={provider.id}
                    type="button"
                    className="btn btn-outline-secondary"
                    onClick={async () => {
                      try {
                        const { authorization_url: url } = await api.startSso(provider.id);
                        window.location.href = url;
                      } catch (err) {
                        setError(err.message || 'Unable to start SSO login.');
                      }
                    }}
                  >
                    <i className={`bi ${provider.id === 'microsoft' ? 'bi-microsoft' : 'bi-google'}`} />{' '}
                    Sign in with {provider.name}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
