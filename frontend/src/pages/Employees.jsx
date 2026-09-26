import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { canManageHr } from '../utils/permissions';

function EmployeeAvatar({ employee }) {
  if (employee.photo_url) {
    return (
      <img
        src={employee.photo_url}
        alt={employee.full_name}
        className="rounded-circle"
        width="38"
        height="38"
        style={{ objectFit: 'cover' }}
      />
    );
  }

  return (
    <span
      className="d-inline-flex align-items-center justify-content-center bg-secondary text-white rounded-circle"
      style={{ width: 38, height: 38 }}
    >
      {employee.first_name?.[0]}
      {employee.last_name?.[0]}
    </span>
  );
}

export default function Employees() {
  const { user } = useAuth();
  const [employees, setEmployees] = useState([]);
  const [query, setQuery] = useState('');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    api.getEmployees(search)
      .then((data) => setEmployees(data.results || data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [search]);

  const handleSearch = (e) => {
    e.preventDefault();
    setSearch(query);
  };

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4 className="page-heading mb-0">
          <i className="bi bi-people-fill" style={{ color: 'var(--fca-lime)' }} /> Employees
        </h4>
        {user?.is_admin && (
          <Link to="/employees/new" className="btn btn-primary btn-sm">
            <i className="bi bi-person-plus-fill" /> Add Employee
          </Link>
        )}
      </div>

      <form onSubmit={handleSearch} className="mb-3 d-flex gap-2" style={{ maxWidth: 480 }}>
        <input
          type="text"
          className="form-control form-control-sm"
          placeholder="Search by ID, name, title, department…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button className="btn btn-primary btn-sm">
          <i className="bi bi-search" />
        </button>
        {search && (
          <button
            type="button"
            className="btn btn-outline-secondary btn-sm"
            onClick={() => {
              setQuery('');
              setSearch('');
            }}
          >
            Clear
          </button>
        )}
      </form>

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
                  <th>Photo</th>
                  <th>Employee ID</th>
                  <th>Name</th>
                  <th>Job Title</th>
                  <th>Department</th>
                  <th>Email</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {employees.map((emp) => (
                  <tr key={emp.id}>
                    <td>
                      <EmployeeAvatar employee={emp} />
                    </td>
                    <td>
                      <code className="small">{emp.employee_number || '—'}</code>
                    </td>
                    <td className="fw-semibold">{emp.full_name}</td>
                    <td>{emp.job_title}</td>
                    <td>{emp.department_name || '—'}</td>
                    <td>
                      <a href={`mailto:${emp.email}`}>{emp.email}</a>
                    </td>
                    <td>
                      <span className={`badge bg-${emp.is_active ? 'success' : 'secondary'}`}>
                        {emp.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <Link to={`/employees/${emp.id}`} className="btn btn-outline-info btn-sm me-1">
                        <i className="bi bi-eye" />
                      </Link>
                      {canManageHr(user) && (
                        <Link to={`/employees/${emp.id}/edit`} className="btn btn-outline-primary btn-sm">
                          <i className="bi bi-pencil" />
                        </Link>
                      )}
                    </td>
                  </tr>
                ))}
                {!employees.length && (
                  <tr>
                    <td colSpan="8" className="text-center py-4 text-muted">
                      No employees found{search ? ` for "${search}"` : ''}.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </>
  );
}
