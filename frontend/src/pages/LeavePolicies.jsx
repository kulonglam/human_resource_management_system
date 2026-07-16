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
  const [accrueBusy, setAccrueBusy] = useState(false);
  const [carryBusy, setCarryBusy] = useState(false);

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

  const runAccrue = async () => {
    setAccrueBusy(true);
    setError('');
    setMessage('');
    try {
      const result = await api.accrueLeaveBalances({ year: Number(syncYear) });
      setMessage(`Monthly accrual applied for ${result.updated} employee(s) in ${result.year}.`);
    } catch (err) {
      setError(err.data?.detail || err.message);
    } finally {
      setAccrueBusy(false);
    }
  };

  const runCarryForward = async () => {
    setCarryBusy(true);
    setError('');
    setMessage('');
    try {
      const fromYear = Number(syncYear) - 1;
      const result = await api.carryForwardLeave({ from_year: fromYear, to_year: Number(syncYear) });
      setMessage(`Carried forward leave for ${result.carried} employee(s) from ${fromYear} to ${syncYear}.`);
    } catch (err) {
      setError(err.data?.detail || err.message);
    } finally {
      setCarryBusy(false);
    }
  };

  const syncToolbar = (
    <div className="card mb-4">
      <div className="card-body">
        <h6 className="card-title mb-3">
          <i className="bi bi-arrow-repeat" /> Leave balance operations
        </h6>
        <p className="text-muted small mb-3">
          Sync policies to allocations, run monthly accrual, or carry forward unused annual leave into the selected year.
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
            <label className="form-label small">Employee (optional, sync only)</label>
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
          <div className="col-md-auto d-flex flex-wrap gap-2">
            <button type="button" className="btn btn-primary btn-sm" onClick={runSync} disabled={syncing}>
              {syncing ? 'Syncing…' : 'Sync policies'}
            </button>
            <button type="button" className="btn btn-outline-primary btn-sm" onClick={runAccrue} disabled={accrueBusy}>
              {accrueBusy ? 'Accruing…' : 'Monthly accrual'}
            </button>
            {user?.is_admin && (
              <button type="button" className="btn btn-outline-secondary btn-sm" onClick={runCarryForward} disabled={carryBusy}>
                {carryBusy ? 'Processing…' : 'Carry forward'}
              </button>
            )}
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
