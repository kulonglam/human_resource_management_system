import { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import ModulePage from './ModulePage';
import { leaveTabs } from '../config/hrModules';

function BalanceCards({ balances }) {
  if (!balances.length) return null;
  return (
    <div className="row g-3 mb-4">
      {balances.map((b) => (
        <div className="col-md-4" key={`${b.leave_type}-${b.year}`}>
          <div className="card border-0 shadow-sm h-100">
            <div className="card-body">
              <div className="text-muted small">{b.leave_type_display || b.leave_type}</div>
              <div className="fs-4 fw-semibold">{Number(b.available_days).toFixed(1)} days</div>
              <div className="small text-muted">
                Used {Number(b.used_days).toFixed(1)} · Pending {Number(b.pending_days).toFixed(1)} · Total {b.total_days}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function Leaves() {
  const { user } = useAuth();
  const [balances, setBalances] = useState([]);
  const isEmployee = user && !user.is_admin && !user.is_manager;

  const loadBalances = useCallback(() => {
    if (!isEmployee || !user?.linked_employee_id) return Promise.resolve();
    const year = new Date().getFullYear();
    return api.list('leave-balances', `employee=${user.linked_employee_id}&year=${year}`)
      .then(setBalances)
      .catch(() => setBalances([]));
  }, [isEmployee, user?.linked_employee_id]);

  useEffect(() => {
    loadBalances();
  }, [loadBalances]);

  return (
    <>
      {isEmployee && (
        <>
          <BalanceCards balances={balances} />
          {!user?.linked_employee_id && (
            <div className="alert alert-warning">
              Your user account is not linked to an employee record. Contact HR to apply for leave.
            </div>
          )}
        </>
      )}
      <ModulePage
        title="Leaves"
        icon="bi-calendar-x"
        tabs={leaveTabs}
        passUser
        onRecordsChanged={isEmployee ? loadBalances : undefined}
      />
    </>
  );
}
