import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function EmployeeDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [employee, setEmployee] = useState(null);
  const [error, setError] = useState('');
  const [exporting, setExporting] = useState(false);
  const [exitReason, setExitReason] = useState('resignation');
  const [exitNotes, setExitNotes] = useState('');

  useEffect(() => {
    api.getEmployee(id)
      .then(setEmployee)
      .catch((err) => setError(err.message));
  }, [id]);

  const handleExport = async () => {
    setExporting(true);
    setError('');
    try {
      await api.downloadGdprExport(id);
    } catch (err) {
      setError(err.message || 'Export failed.');
    } finally {
      setExporting(false);
    }
  };

  const handleTerminate = async (e) => {
    e.preventDefault();
    if (!window.confirm(`Terminate ${employee.full_name}?`)) return;
    try {
      await api.terminateEmployee(id, { exit_reason: exitReason, exit_notes: exitNotes });
      navigate('/employees');
    } catch (err) {
      setError(err.data?.detail || err.message);
    }
  };

  if (error) return <div className="alert alert-danger">{error}</div>;
  if (!employee) {
    return (
      <div className="text-center py-5">
        <div className="spinner-border text-primary" role="status" />
      </div>
    );
  }

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4 className="page-heading">{employee.full_name}</h4>
        <div className="d-flex gap-2">
          {(user?.is_admin || user?.is_manager) && (
            <button
              type="button"
              className="btn btn-outline-secondary btn-sm"
              onClick={handleExport}
              disabled={exporting}
            >
              {exporting ? 'Exporting…' : 'GDPR Export'}
            </button>
          )}
          <Link to={`/employees/${id}/edit`} className="btn btn-primary btn-sm">
            Edit
          </Link>
          <Link to="/employees" className="btn btn-outline-secondary btn-sm">
            Back
          </Link>
        </div>
      </div>

      <div className="row">
        <div className="col-md-8">
          <div className="card mb-3">
            <div className="card-body">
              <h5 className="card-title">Personal Information</h5>
              <dl className="row mb-0">
                <dt className="col-sm-4">Email</dt>
                <dd className="col-sm-8">{employee.email}</dd>
                <dt className="col-sm-4">Mobile</dt>
                <dd className="col-sm-8">{employee.mobile}</dd>
                <dt className="col-sm-4">Gender</dt>
                <dd className="col-sm-8">{employee.gender}</dd>
                <dt className="col-sm-4">Date of Birth</dt>
                <dd className="col-sm-8">{employee.date_of_birth}</dd>
                <dt className="col-sm-4">Address</dt>
                <dd className="col-sm-8">{employee.address}</dd>
                <dt className="col-sm-4">Emergency Contact</dt>
                <dd className="col-sm-8">{employee.emergency_contact}</dd>
              </dl>
            </div>
          </div>

          <div className="card mb-3">
            <div className="card-body">
              <h5 className="card-title">Employment</h5>
              <dl className="row mb-0">
                <dt className="col-sm-4">Job Title</dt>
                <dd className="col-sm-8">{employee.job_title}</dd>
                <dt className="col-sm-4">Department</dt>
                <dd className="col-sm-8">{employee.department_name || '—'}</dd>
                <dt className="col-sm-4">Date Joined</dt>
                <dd className="col-sm-8">{employee.date_joined}</dd>
                <dt className="col-sm-4">Status</dt>
                <dd className="col-sm-8">
                  <span className={`badge bg-${employee.is_active ? 'success' : 'secondary'}`}>
                    {employee.is_active ? 'Active' : 'Inactive'}
                  </span>
                </dd>
              </dl>
            </div>
          </div>
        </div>

        {user?.is_admin && employee.is_active && (
          <div className="col-md-4">
            <div className="card border-danger">
              <div className="card-body">
                <h5 className="card-title text-danger">Terminate Employee</h5>
                <form onSubmit={handleTerminate}>
                  <div className="mb-3">
                    <label className="form-label">Exit Reason</label>
                    <select
                      className="form-select form-select-sm"
                      value={exitReason}
                      onChange={(e) => setExitReason(e.target.value)}
                    >
                      <option value="resignation">Resignation</option>
                      <option value="termination">Termination</option>
                      <option value="retirement">Retirement</option>
                      <option value="contract_end">Contract End</option>
                      <option value="medical">Medical Grounds</option>
                      <option value="redundancy">Redundancy</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Notes</label>
                    <textarea
                      className="form-control form-control-sm"
                      rows="3"
                      value={exitNotes}
                      onChange={(e) => setExitNotes(e.target.value)}
                    />
                  </div>
                  <button type="submit" className="btn btn-danger btn-sm" disabled={terminating}>
                    Terminate
                  </button>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
