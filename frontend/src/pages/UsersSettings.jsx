import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { ALL_PERMISSIONS, PERMISSION_LABELS } from '../utils/permissions';
import { errorMessage } from '../utils/apiErrors';

const EMPTY_FORM = {
  username: '',
  email: '',
  first_name: '',
  last_name: '',
  role: '',
  password: '',
};

function UserModal({ user, roles, departments, onClose, onSaved }) {
  const isEdit = Boolean(user);
  const [form, setForm] = useState(
    isEdit
      ? {
          email: user.email || '',
          first_name: user.first_name || '',
          last_name: user.last_name || '',
          role: user.role || '',
          managed_department: user.managed_department || '',
          is_active: user.is_active !== false,
        }
      : { ...EMPTY_FORM, managed_department: '' },
  );
  const selectedRole = roles.find((r) => String(r.id) === String(form.role));
  const isManagerRole = selectedRole?.name === 'manager';
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const payload = { ...form };
      if (isEdit) {
        if (payload.role === '') payload.role = null;
        if (!payload.managed_department) payload.managed_department = null;
        await api.updateUser(user.id, payload);
      } else {
        await api.createUser(payload);
      }
      onSaved();
      onClose();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <div className="modal show d-block" tabIndex="-1">
        <div className="modal-dialog">
          <div className="modal-content">
            <form onSubmit={handleSubmit}>
              <div className="modal-header">
                <h5 className="modal-title">{isEdit ? 'Edit user' : 'Create user'}</h5>
                <button type="button" className="btn-close" onClick={onClose} />
              </div>
              <div className="modal-body">
                {error && <div className="alert alert-danger">{error}</div>}
                {!isEdit && (
                  <div className="mb-3">
                    <label className="form-label">Username</label>
                    <input name="username" className="form-control" value={form.username} onChange={handleChange} required />
                  </div>
                )}
                <div className="mb-3">
                  <label className="form-label">Email</label>
                  <input name="email" type="email" className="form-control" value={form.email} onChange={handleChange} required />
                </div>
                <div className="row">
                  <div className="col-md-6 mb-3">
                    <label className="form-label">First name</label>
                    <input name="first_name" className="form-control" value={form.first_name} onChange={handleChange} />
                  </div>
                  <div className="col-md-6 mb-3">
                    <label className="form-label">Last name</label>
                    <input name="last_name" className="form-control" value={form.last_name} onChange={handleChange} />
                  </div>
                </div>
                <div className="mb-3">
                  <label className="form-label">Role</label>
                  <select name="role" className="form-select" value={form.role} onChange={handleChange} required={!isEdit}>
                    <option value="">Select role…</option>
                    {roles.map((role) => (
                      <option key={role.id} value={role.id}>{role.name}</option>
                    ))}
                  </select>
                </div>
                {isManagerRole && (
                  <div className="mb-3">
                    <label className="form-label">Managed department</label>
                    <select
                      name="managed_department"
                      className="form-select"
                      value={form.managed_department}
                      onChange={handleChange}
                    >
                      <option value="">None (use linked employee profile)</option>
                      {departments.map((dept) => (
                        <option key={dept.id} value={dept.id}>{dept.name}</option>
                      ))}
                    </select>
                    <div className="form-text">Scopes manager access when no employee profile is linked.</div>
                  </div>
                )}
                {!isEdit && (
                  <div className="mb-3">
                    <label className="form-label">Password</label>
                    <input name="password" type="password" className="form-control" value={form.password} onChange={handleChange} required minLength={8} />
                  </div>
                )}
                {isEdit && (
                  <div className="form-check">
                    <input
                      className="form-check-input"
                      type="checkbox"
                      name="is_active"
                      id="userActive"
                      checked={form.is_active}
                      onChange={handleChange}
                    />
                    <label className="form-check-label" htmlFor="userActive">Account active</label>
                  </div>
                )}
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? 'Saving…' : 'Save'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
      <div className="modal-backdrop show" />
    </>
  );
}

function RolePermissionsPanel({ roles, onSaved }) {
  const [selectedRoleId, setSelectedRoleId] = useState('');
  const [permissions, setPermissions] = useState([]);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const editableRoles = roles.filter((role) => role.name !== 'admin');

  useEffect(() => {
    const role = editableRoles.find((r) => String(r.id) === String(selectedRoleId));
    if (role) {
      setPermissions(role.permissions?.length ? role.permissions : []);
    }
  }, [selectedRoleId, roles]);

  const togglePermission = (perm) => {
    setPermissions((prev) => (
      prev.includes(perm) ? prev.filter((p) => p !== perm) : [...prev, perm]
    ));
  };

  const savePermissions = async () => {
    if (!selectedRoleId) return;
    setSaving(true);
    setError('');
    setMessage('');
    try {
      await api.updateRole(selectedRoleId, { permissions });
      setMessage('Role permissions updated.');
      onSaved();
    } catch (err) {
      setError(err.data?.detail || err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="card mt-4">
      <div className="card-body">
        <h6 className="card-title mb-3">
          <i className="bi bi-shield-check" /> Role permissions
        </h6>
        <div className="row g-3">
          <div className="col-md-4">
            <label className="form-label small">Role</label>
            <select
              className="form-select form-select-sm"
              value={selectedRoleId}
              onChange={(e) => setSelectedRoleId(e.target.value)}
            >
              <option value="">Select role…</option>
              {editableRoles.map((role) => (
                <option key={role.id} value={role.id}>{role.name}</option>
              ))}
            </select>
          </div>
          <div className="col-md-8">
            {selectedRoleId ? (
              <div className="d-flex flex-wrap gap-3">
                {ALL_PERMISSIONS.map((perm) => (
                  <div className="form-check" key={perm}>
                    <input
                      className="form-check-input"
                      type="checkbox"
                      id={`perm-${perm}`}
                      checked={permissions.includes(perm)}
                      onChange={() => togglePermission(perm)}
                    />
                    <label className="form-check-label small" htmlFor={`perm-${perm}`}>
                      {PERMISSION_LABELS[perm]}
                    </label>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-muted small mb-0">Select a role to edit granular permissions.</p>
            )}
          </div>
        </div>
        {selectedRoleId && (
          <button type="button" className="btn btn-primary btn-sm mt-3" onClick={savePermissions} disabled={saving}>
            {saving ? 'Saving…' : 'Save permissions'}
          </button>
        )}
        {message && <div className="alert alert-success mt-3 mb-0 py-2">{message}</div>}
        {error && <div className="alert alert-danger mt-3 mb-0 py-2">{error}</div>}
      </div>
    </div>
  );
}

export default function UsersSettings() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [includeInactive, setIncludeInactive] = useState(false);
  const [modalUser, setModalUser] = useState(undefined);
  const [showModal, setShowModal] = useState(false);

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const params = includeInactive ? 'include_inactive=1' : '';
      const [userData, roleData, deptData] = await Promise.all([
        api.listRaw('users', params),
        api.getRoles(),
        api.getDepartments(),
      ]);
      setUsers(userData.results || userData);
      setRoles(roleData.results || roleData);
      setDepartments(deptData);
    } catch (err) {
      setError(err.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (currentUser?.is_admin) load();
  }, [currentUser, includeInactive]);

  if (!currentUser?.is_admin) return <Navigate to="/dashboard" replace />;

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
        <h4 className="page-heading mb-0">
          <i className="bi bi-people-fill" style={{ color: 'var(--fca-lime)' }} /> User Management
        </h4>
        <div className="d-flex gap-2 align-items-center">
          <div className="form-check form-switch mb-0">
            <input
              className="form-check-input"
              type="checkbox"
              id="showInactive"
              checked={includeInactive}
              onChange={(e) => setIncludeInactive(e.target.checked)}
            />
            <label className="form-check-label small" htmlFor="showInactive">Show inactive</label>
          </div>
          <button type="button" className="btn btn-primary btn-sm" onClick={() => { setModalUser(null); setShowModal(true); }}>
            <i className="bi bi-person-plus" /> Create user
          </button>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="card">
        <div className="card-body p-0">
          {loading ? (
            <div className="text-center py-5">
              <div className="spinner-border text-primary" role="status" />
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-hover mb-0 align-middle">
                <thead>
                  <tr>
                    <th>Username</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Employee link</th>
                    <th>MFA</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} className={!u.is_active ? 'text-muted' : undefined}>
                      <td className="fw-semibold">{u.username}</td>
                      <td>{[u.first_name, u.last_name].filter(Boolean).join(' ') || '—'}</td>
                      <td>{u.email}</td>
                      <td><span className="badge bg-secondary">{u.role_name || '—'}</span></td>
                      <td>{u.linked_employee_name || '—'}</td>
                      <td>{u.mfa_enabled ? 'Enabled' : u.mfa_setup_required ? 'Setup required' : '—'}</td>
                      <td>
                        <span className={`badge bg-${u.is_active ? 'success' : 'secondary'}`}>
                          {u.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td>
                        <button
                          type="button"
                          className="btn btn-outline-primary btn-sm"
                          onClick={() => { setModalUser(u); setShowModal(true); }}
                        >
                          <i className="bi bi-pencil" />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {!users.length && (
                    <tr>
                      <td colSpan="8" className="text-center py-4 text-muted">No users found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {showModal && (
        <UserModal
          user={modalUser}
          roles={roles}
          departments={departments}
          onClose={() => setShowModal(false)}
          onSaved={load}
        />
      )}

      <RolePermissionsPanel roles={roles} onSaved={load} />
    </>
  );
}
