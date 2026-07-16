import { Navigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import { canViewPayroll } from '../utils/permissions';
import ModulePage from './ModulePage';
import { payrollTabs } from '../config/hrModules';

export default function Payroll() {
  const { user } = useAuth();
  const [exporting, setExporting] = useState('');
  const [error, setError] = useState('');
  const [recon, setRecon] = useState(null);
  const now = new Date();
  const month = now.getMonth() + 1;
  const year = now.getFullYear();

  useEffect(() => {
    if (!canViewPayroll(user)) return;
    api.getPayrollReconciliation({ month, year })
      .then(setRecon)
      .catch(() => setRecon(null));
  }, [user, month, year]);

  if (!canViewPayroll(user)) {
    return <Navigate to="/dashboard" replace />;
  }

  const downloadStatutory = async (returnType, exportFormat = 'csv') => {
    setExporting(`${returnType}-${exportFormat}`);
    setError('');
    try {
      await api.downloadStatutoryPayroll({
        month,
        year,
        return_type: returnType,
        export_format: exportFormat,
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setExporting('');
    }
  };

  const toolbar = (
    <>
      <div className="card mb-3">
        <div className="card-body">
          <h6 className="card-title mb-2">
            <i className="bi bi-file-earmark-spreadsheet" /> Statutory filing exports
          </h6>
          <p className="text-muted small mb-3">
            Download PAYE / NSSF / URA return files for {year}-{String(month).padStart(2, '0')} (UGX).
          </p>
          <div className="d-flex flex-wrap gap-2">
            <button type="button" className="btn btn-outline-primary btn-sm" disabled={Boolean(exporting)} onClick={() => downloadStatutory('paye')}>
              {exporting === 'paye-csv' ? 'Exporting…' : 'PAYE CSV'}
            </button>
            <button type="button" className="btn btn-outline-primary btn-sm" disabled={Boolean(exporting)} onClick={() => downloadStatutory('paye', 'ura')}>
              {exporting === 'paye-ura' ? 'Exporting…' : 'URA PAYE'}
            </button>
            <button type="button" className="btn btn-outline-primary btn-sm" disabled={Boolean(exporting)} onClick={() => downloadStatutory('nssf')}>
              {exporting === 'nssf-csv' ? 'Exporting…' : 'NSSF CSV'}
            </button>
          </div>
          {error && <div className="alert alert-danger mt-3 mb-0 py-2">{error}</div>}
        </div>
      </div>
      {recon && (
        <div className="card mb-4">
          <div className="card-body">
            <div className="d-flex justify-content-between align-items-start flex-wrap gap-2">
              <div>
                <h6 className="card-title mb-1">
                  <i className="bi bi-clipboard-check" /> Filing reconciliation
                </h6>
                <p className="small text-muted mb-0">Period {recon.period}</p>
              </div>
              <span className={`badge ${recon.ready_to_file ? 'bg-success' : 'bg-warning text-dark'}`}>
                {recon.ready_to_file ? 'Ready to file' : 'Issues found'}
              </span>
            </div>
            <div className="row g-2 mt-2 small">
              <div className="col-6 col-md-3">Employees: <strong>{recon.totals.employees}</strong></div>
              <div className="col-6 col-md-3">PAYE: <strong>UGX {Number(recon.totals.paye || 0).toLocaleString('en-UG')}</strong></div>
              <div className="col-6 col-md-3">NSSF emp: <strong>UGX {Number(recon.totals.nssf_employee || 0).toLocaleString('en-UG')}</strong></div>
              <div className="col-6 col-md-3">Missing TIN/NSSF: <strong>{recon.totals.missing_tin}/{recon.totals.missing_nssf}</strong></div>
            </div>
            {recon.issues?.length > 0 && (
              <ul className="small text-warning mt-2 mb-0">
                {recon.issues.slice(0, 5).map((issue) => (
                  <li key={`${issue.employee}-${issue.issue}`}>{issue.employee}: {issue.issue}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </>
  );

  return (
    <ModulePage
      title="Payroll"
      icon="bi-cash-coin"
      tabs={payrollTabs}
      headerExtra={toolbar}
      passUser
    />
  );
}
