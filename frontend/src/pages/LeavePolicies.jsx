import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import ModulePage from './ModulePage';
import { leavePolicyTabs } from '../config/opsModules';

export default function LeavePolicies() {
  const { user } = useAuth();
  const [syncYear, setSyncYear] = useState(new Date().getFullYear());
  const [syncEmployee, setSyncEmployee] = useState('');
  const [employees, setEmployees] = useState([]);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    api.list('employees').then(setEmployees).catch(() => setEmployees([]));
  }, []);

  if (!user?.is_admin && !user?.is_manager) {
    return <Navigate to="/dashboard" replace />;
  }

  const runSync = async () => {
    setSyncing(true);
    setError('');
    setMessage('');
    try {
      const payload = { year: Number(syncYear) };
      if (syncEmployee) payload.employee = Number(syncEmployee);
      const result = await api.syncLeavePolicies(payload);
      if (result.employee) {
        setMessage(`Synced ${result.synced} allocation(s) for employee #${result.employee}.`);
      } else {
        setMessage(
          `Synced policies for ${result.employees} employee(s) — ${result.allocations} allocation(s) updated.`,
        );
      }
    } catch (err) {
      setError(err.data?.detail || err.message);
    } finally {
      setSyncing(false);
    }
  };

  const syncToolbar = (
    <div className="card mb-4">
      <div className="card-body">
        <h6 className="card-title mb-3">
          <i className="bi bi-arrow-repeat" /> Sync leave policies to balances
        </h6>
        <p className="text-muted small mb-3">
          Applies active leave policies to employee allocations and updates leave balances for the selected year.
          Leave employee blank to sync all active employees.
        </p>
        <div className="row g-2 align-items-end">
          <div className="col-md-2">
            <label className="form-label small">Year</label>
            <input
              type="number"
              className="form-control form-control-sm"
              value={syncYear}
              onChange={(e) => setSyncYear(e.target.value)}
            />
          </div>
          <div className="col-md-4">
            <label className="form-label small">Employee (optional)</label>
            <select
              className="form-select form-select-sm"
              value={syncEmployee}
              onChange={(e) => setSyncEmployee(e.target.value)}
            >
              <option value="">All active employees</option>
              {employees.map((emp) => (
                <option key={emp.id} value={emp.id}>{emp.full_name}</option>
              ))}
            </select>
          </div>
          <div className="col-md-auto">
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={runSync}
              disabled={syncing}
            >
              {syncing ? 'Syncing…' : 'Sync policies'}
            </button>
          </div>
        </div>
        {message && <div className="alert alert-success mt-3 mb-0 py-2">{message}</div>}
        {error && <div className="alert alert-danger mt-3 mb-0 py-2">{error}</div>}
      </div>
    </div>
  );

  return (
    <ModulePage
      title="Leave Policies"
      icon="bi-file-earmark-text"
      tabs={leavePolicyTabs}
      headerExtra={syncToolbar}
      passUser
    />
  );
}
