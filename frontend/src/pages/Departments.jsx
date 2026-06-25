import { useEffect, useState } from 'react';
import { api } from '../api/client';

function DepartmentModal({ department, onClose, onSaved }) {
  const isEdit = Boolean(department);
  const [form, setForm] = useState({
    name: department?.name || '',
    location: department?.location || '',
    history: department?.history || '',
    manager_name: department?.manager_name || '',
    manager_contact: department?.manager_contact || '',
  });
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      if (isEdit) {
        await api.updateDepartment(department.id, form);
      } else {
        await api.createDepartment(form);
      }
      onSaved();
      onClose();
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
    <>
      <div className="modal show d-block" tabIndex="-1">
        <div className="modal-dialog">
          <div className="modal-content">
            <form onSubmit={handleSubmit}>
              <div className="modal-header">
                <h5 className="modal-title">{isEdit ? 'Edit Department' : 'Add Department'}</h5>
                <button type="button" className="btn-close" onClick={onClose} />
              </div>
              <div className="modal-body">
                {error && <div className="alert alert-danger">{error}</div>}
                <div className="mb-3">
                  <label className="form-label">Name</label>
                  <input name="name" className="form-control" value={form.name} onChange={handleChange} required />
                </div>
                <div className="mb-3">
                  <label className="form-label">Location</label>
                  <input name="location" className="form-control" value={form.location} onChange={handleChange} required />
                </div>
                <div className="mb-3">
                  <label className="form-label">Manager Name</label>
                  <input name="manager_name" className="form-control" value={form.manager_name} onChange={handleChange} />
                </div>
                <div className="mb-3">
                  <label className="form-label">Manager Contact</label>
                  <input name="manager_contact" className="form-control" value={form.manager_contact} onChange={handleChange} />
                </div>
                <div className="mb-3">
                  <label className="form-label">History</label>
                  <textarea name="history" className="form-control" rows="4" value={form.history} onChange={handleChange} />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={onClose}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? 'Saving...' : 'Save'}
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

export default function Departments() {
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [modalDepartment, setModalDepartment] = useState(undefined);
  const [showModal, setShowModal] = useState(false);

  const loadDepartments = () => {
    setLoading(true);
    api.getDepartments()
      .then((data) => setDepartments(data.results || data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadDepartments();
  }, []);

  const openCreate = () => {
    setModalDepartment(null);
    setShowModal(true);
  };

  const openEdit = (department) => {
    setModalDepartment(department);
    setShowModal(true);
  };

  const handleDelete = async (department) => {
    if (!window.confirm(`Delete department "${department.name}"?`)) return;
    try {
      await api.deleteDepartment(department.id);
      loadDepartments();
    } catch (err) {
      setError(err.data?.detail || err.message);
    }
  };

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4 className="page-heading mb-0">
          <i className="bi bi-building" style={{ color: 'var(--fca-lime)' }} /> Departments
        </h4>
        <button type="button" className="btn btn-primary btn-sm" onClick={openCreate}>
          <i className="bi bi-plus-lg" /> Add Department
        </button>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="card">
        <div className="card-body p-0">
          {loading ? (
            <div className="text-center py-4">
              <div className="spinner-border text-primary" role="status" />
            </div>
          ) : (
            <table className="table table-hover mb-0 align-middle">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Location</th>
                  <th>Manager</th>
                  <th>Employees</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {departments.map((dept) => (
                  <tr key={dept.id}>
                    <td className="fw-semibold">{dept.name}</td>
                    <td>{dept.location}</td>
                    <td>{dept.manager_name || '—'}</td>
                    <td>{dept.employee_count}</td>
                    <td>
                      <button
                        type="button"
                        className="btn btn-outline-primary btn-sm me-1"
                        onClick={() => openEdit(dept)}
                      >
                        <i className="bi bi-pencil" />
                      </button>
                      <button
                        type="button"
                        className="btn btn-outline-danger btn-sm"
                        onClick={() => handleDelete(dept)}
                      >
                        <i className="bi bi-trash" />
                      </button>
                    </td>
                  </tr>
                ))}
                {!departments.length && (
                  <tr>
                    <td colSpan="5" className="text-center py-4 text-muted">
                      No departments found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {showModal && (
        <DepartmentModal
          department={modalDepartment}
          onClose={() => setShowModal(false)}
          onSaved={loadDepartments}
        />
      )}
    </>
  );
}
