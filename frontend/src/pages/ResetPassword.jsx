import { useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { api } from '../api/client';
import { errorMessage } from '../utils/apiErrors';
import PublicFooter from '../components/PublicFooter';

export default function ResetPassword() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const uid = useMemo(() => params.get('uid') || '', [params]);
  const token = useMemo(() => params.get('token') || '', [params]);

  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [done, setDone] = useState(false);

  const linkMissing = !uid || !token;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (password !== passwordConfirm) {
      setError('Passwords do not match.');
      return;
    }
    setSubmitting(true);
    try {
      await api.confirmPasswordReset({
        uid,
        token,
        password,
        password_confirm: passwordConfirm,
      });
      setDone(true);
      setTimeout(() => navigate('/login', { replace: true }), 1500);
    } catch (err) {
      setError(errorMessage(err) || 'Unable to reset password.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <section className="auth-hero" aria-label="FCA HRMIS">
        <div className="auth-hero-inner">
          <p className="auth-hero-eyebrow">Workforce platform</p>
          <h1 className="auth-hero-brand">
            FCA <span>HRMIS</span>
          </h1>
          <p className="auth-hero-line">
            Choose a strong new password to regain access to your account.
          </p>
        </div>
      </section>

      <div className="auth-panel">
        <div className="auth-panel-card">
          <div className="card-body">
            <h2 className="auth-panel-title">Reset password</h2>
            <p className="auth-panel-sub">
              {linkMissing
                ? 'This reset link is incomplete. Request a new one from the sign-in page.'
                : 'Enter and confirm your new password.'}
            </p>

            {error && <div className="alert alert-danger" role="alert">{error}</div>}
            {done && (
              <div className="alert alert-success" role="status">
                Password updated. Redirecting to sign in…
              </div>
            )}

            {!linkMissing && !done && (
              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label className="form-label" htmlFor="reset-password">New password</label>
                  <div className="position-relative">
                    <input
                      id="reset-password"
                      type={showPassword ? 'text' : 'password'}
                      className="form-control"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      autoComplete="new-password"
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
                <div className="mb-3">
                  <label className="form-label" htmlFor="reset-password-confirm">Confirm password</label>
                  <input
                    id="reset-password-confirm"
                    type={showPassword ? 'text' : 'password'}
                    className="form-control"
                    value={passwordConfirm}
                    onChange={(e) => setPasswordConfirm(e.target.value)}
                    autoComplete="new-password"
                    required
                  />
                </div>
                <div className="d-grid gap-2">
                  <button type="submit" className="btn btn-primary" disabled={submitting}>
                    {submitting ? 'Updating…' : 'Update password'}
                  </button>
                  <Link to="/login" className="btn btn-outline-secondary">
                    Back to sign in
                  </Link>
                </div>
              </form>
            )}

            {linkMissing && (
              <div className="d-grid">
                <Link to="/forgot-password" className="btn btn-primary">
                  Request a new reset link
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
      <PublicFooter showLoginLink={false} />
    </div>
  );
}
