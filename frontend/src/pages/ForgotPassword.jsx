import { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import PublicFooter from '../components/PublicFooter';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [done, setDone] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await api.requestPasswordReset({ email: email.trim() });
      setDone(true);
    } catch (err) {
      setError(err.message || 'Unable to send reset instructions.');
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
            Reset your password securely using the email on your account.
          </p>
        </div>
      </section>

      <div className="auth-panel">
        <div className="auth-panel-card">
          <div className="card-body">
            <h2 className="auth-panel-title">Forgot password</h2>
            <p className="auth-panel-sub">
              Enter your account email and we will send reset instructions if it matches a user.
            </p>

            {error && <div className="alert alert-danger" role="alert">{error}</div>}

            {done ? (
              <div className="alert alert-success" role="status">
                If an account matches that email, password reset instructions have been sent.
                Check your inbox (and console email in local development).
              </div>
            ) : (
              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label className="form-label" htmlFor="forgot-email">Email</label>
                  <input
                    id="forgot-email"
                    type="email"
                    className="form-control"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@company.com"
                    autoComplete="email"
                    required
                  />
                </div>
                <div className="d-grid gap-2">
                  <button type="submit" className="btn btn-primary" disabled={submitting}>
                    {submitting ? 'Sending…' : 'Send reset link'}
                  </button>
                  <Link to="/login" className="btn btn-outline-secondary">
                    Back to sign in
                  </Link>
                </div>
              </form>
            )}

            {done && (
              <p className="text-center mt-3 mb-0">
                <Link to="/login">Back to sign in</Link>
              </p>
            )}
          </div>
        </div>
      </div>
      <PublicFooter showLoginLink={false} />
    </div>
  );
}
