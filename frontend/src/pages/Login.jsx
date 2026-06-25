import { useEffect, useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [allowRegistration, setAllowRegistration] = useState(false);

  useEffect(() => {
    api.getAuthConfig()
      .then((data) => setAllowRegistration(Boolean(data.allow_registration)))
      .catch(() => setAllowRegistration(false));
  }, []);

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await login(username, password);
      const redirectTo = location.state?.from?.pathname || '/dashboard';
      navigate(redirectTo, { replace: true });
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

  return (
    <div className="auth-page">
      <div className="card shadow" style={{ width: '100%', maxWidth: 480 }}>
        <div className="card-body p-4">
          <h4 className="card-title text-center mb-4">
            <i className="bi bi-person-lock" /> HRMIS Login
          </h4>

          {error && <div className="alert alert-danger">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label className="form-label">Username</label>
              <input
                type="text"
                className="form-control"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Username"
                required
              />
            </div>

            <div className="mb-3">
              <label className="form-label">Password</label>
              <div className="position-relative">
                <input
                  type={showPassword ? 'text' : 'password'}
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
                >
                  <i className={`bi ${showPassword ? 'bi-eye-slash' : 'bi-eye'}`} />
                </button>
              </div>
            </div>

            <div className="d-grid">
              <button type="submit" className="btn btn-primary" disabled={submitting}>
                <i className="bi bi-box-arrow-in-right" /> {submitting ? 'Signing in...' : 'Login'}
              </button>
            </div>
          </form>

          {allowRegistration && (
            <p className="text-center mt-3 mb-0">
              No account? <Link to="/register">Register</Link>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
