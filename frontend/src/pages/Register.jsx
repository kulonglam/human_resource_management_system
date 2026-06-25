import { useEffect, useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

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
    api.getRoles().then(setRoles).catch(() => {});
  }, []);

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await register({
        ...form,
        role: form.role ? Number(form.role) : null,
      });
      navigate('/dashboard', { replace: true });
    } catch (err) {
      const messages = Object.entries(err.data || {})
        .map(([field, msgs]) => `${field}: ${Array.isArray(msgs) ? msgs.join(', ') : msgs}`)
        .join(' ');
      setError(messages || err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="card shadow" style={{ width: '100%', maxWidth: 520 }}>
        <div className="card-body p-4">
          <h4 className="card-title text-center mb-4">
            <i className="bi bi-person-plus" /> Create Account
          </h4>

          {error && <div className="alert alert-danger">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label className="form-label">Username</label>
              <input
                name="username"
                className="form-control"
                value={form.username}
                onChange={handleChange}
                required
              />
            </div>
            <div className="mb-3">
              <label className="form-label">Email</label>
              <input
                type="email"
                name="email"
                className="form-control"
                value={form.email}
                onChange={handleChange}
                required
              />
            </div>
            <div className="mb-3">
              <label className="form-label">Role</label>
              <select name="role" className="form-select" value={form.role} onChange={handleChange}>
                <option value="">Select role</option>
                {roles.map((role) => (
                  <option key={role.id} value={role.id}>
                    {role.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="mb-3">
              <label className="form-label">Password</label>
              <input
                type="password"
                name="password1"
                className="form-control"
                value={form.password1}
                onChange={handleChange}
                required
              />
            </div>
            <div className="mb-3">
              <label className="form-label">Confirm Password</label>
              <input
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
                {submitting ? 'Creating account...' : 'Register'}
              </button>
            </div>
          </form>

          <p className="text-center mt-3 mb-0">
            Already have an account? <Link to="/login">Login</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
