import { useEffect, useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { errorMessage } from '../utils/apiErrors';
import PublicFooter from '../components/PublicFooter';

export default function Register() {
  const { user, register } = useAuth();
  const navigate = useNavigate();
  const [roles, setRoles] = useState([]);
  const [form, setForm] = useState({
    username: '',
    email: '',
    role: '',
    password1: '',
    password2: '',
  });
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api.getAuthConfig()
      .then((data) => {
        if (!data.allow_registration) {
          navigate('/login', { replace: true });
          return;
        }
        api.getRoles().then(setRoles).catch(() => {});
      })
      .catch(() => navigate('/login', { replace: true }));
  }, [navigate]);

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (form.password1 !== form.password2) {
      setError('password2: Passwords do not match.');
      return;
    }
    if (form.password1.length < 8) {
      setError('password1: Password must be at least 8 characters.');
      return;
    }
    setSubmitting(true);
    try {
      await register({
        ...form,
        role: form.role ? Number(form.role) : null,
      });
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(errorMessage(err));
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
            Create an account to access your organization&apos;s workforce tools.
          </p>
          <ul className="auth-hero-points">
            <li>
              <i className="bi bi-check-circle-fill" aria-hidden="true" />
              <span>Role-based access for your team</span>
            </li>
            <li>
              <i className="bi bi-check-circle-fill" aria-hidden="true" />
              <span>Self-service leave and attendance</span>
            </li>
            <li>
              <i className="bi bi-check-circle-fill" aria-hidden="true" />
              <span>Secure sign-in for your organization</span>
            </li>
          </ul>
        </div>
      </section>

      <div className="auth-panel">
        <div className="auth-panel-card">
          <div className="card-body">
            <h2 className="auth-panel-title">Create account</h2>
            <p className="auth-panel-sub">Join FCA HRMIS with your work credentials.</p>

            {error && <div className="alert alert-danger" role="alert">{error}</div>}

            <form onSubmit={handleSubmit}>
              <div className="mb-3">
                <label className="form-label" htmlFor="register-username">Username</label>
                <input
                  id="register-username"
                  name="username"
                  className="form-control"
                  value={form.username}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="mb-3">
                <label className="form-label" htmlFor="register-email">Email</label>
                <input
                  id="register-email"
                  type="email"
                  name="email"
                  className="form-control"
                  value={form.email}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="mb-3">
                <label className="form-label" htmlFor="register-role">Role</label>
                <select
                  id="register-role"
                  name="role"
                  className="form-select"
                  value={form.role}
                  onChange={handleChange}
                >
                  <option value="">Select role</option>
                  {roles.map((role) => (
                    <option key={role.id} value={role.id}>
                      {role.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="mb-3">
                <label className="form-label" htmlFor="register-password1">Password</label>
                <input
                  id="register-password1"
                  type="password"
                  name="password1"
                  className="form-control"
                  value={form.password1}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="mb-3">
                <label className="form-label" htmlFor="register-password2">Confirm password</label>
                <input
                  id="register-password2"
                  type="password"
                  name="password2"
                  className="form-control"
                  value={form.password2}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="d-grid">
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? 'Creating account…' : 'Register'}
                </button>
              </div>
            </form>

            <p className="text-center mt-3 mb-0">
              Already have an account? <Link to="/login">Sign in</Link>
            </p>
          </div>
        </div>
      </div>
      <PublicFooter showLoginLink={false} />
    </div>
  );
}
