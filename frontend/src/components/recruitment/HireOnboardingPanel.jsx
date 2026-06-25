import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../api/client';

export default function HireOnboardingPanel({ application, canManage }) {
  const [onboarding, setOnboarding] = useState(null);
  const [form, setForm] = useState({
    date_of_birth: '',
    gender: 'Other',
    address: '',
    emergency_contact: '',
    department: '',
    account_number: '',
    bank: '',
  });
  const [departments, setDepartments] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    const rows = await api.list('hire-onboarding', `application=${application.id}`).catch(() => []);
    const record = rows.find((r) => r.application === application.id) || rows[0];
    setOnboarding(record || null);
    const depts = await api.list('departments');
    setDepartments(depts);
  }, [application.id]);

  useEffect(() => {
    if (application.onboarding_status || application.status === 'hired') {
      load();
    }
  }, [application, load]);

  if (!onboarding) {
    return application.status === 'hired' ? (
      <div className="alert alert-light border small">Onboarding record will appear after hire is finalized.</div>
    ) : null;
  }

  const complete = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      const result = await api.completeOnboarding(onboarding.id, form);
      setOnboarding(result.onboarding);
    } catch (err) {
      setError(err.data?.detail || err.message);
    } finally {
      setBusy(false);
    }
  };

  if (onboarding.status === 'completed' && onboarding.employee) {
    return (
      <div className="card mb-3 border-success">
        <div className="card-body">
          <h5 className="card-title text-success"><i className="bi bi-check-circle me-1" />Onboarding complete</h5>
          <p className="mb-2">Employee record created.</p>
          <Link to={`/employees/${onboarding.employee}`} className="btn btn-outline-primary btn-sm">View employee</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="card mb-3">
      <div className="card-body">
        <h5 className="card-title">Hire onboarding</h5>
        <p className="small text-muted">Complete employee profile to finish hire-to-onboard.</p>
        {error && <div className="alert alert-danger py-2 small">{error}</div>}
        {canManage && (
          <form onSubmit={complete}>
            <div className="row g-2">
              <div className="col-md-4">
                <label className="form-label small">Date of birth</label>
                <input type="date" className="form-control form-control-sm" required value={form.date_of_birth} onChange={(e) => setForm({ ...form, date_of_birth: e.target.value })} />
              </div>
              <div className="col-md-4">
                <label className="form-label small">Gender</label>
                <select className="form-select form-select-sm" value={form.gender} onChange={(e) => setForm({ ...form, gender: e.target.value })}>
                  <option>Male</option><option>Female</option><option>Other</option>
                </select>
              </div>
              <div className="col-md-4">
                <label className="form-label small">Department</label>
                <select className="form-select form-select-sm" required value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })}>
                  <option value="">Select...</option>
                  {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select>
              </div>
              <div className="col-md-6">
                <label className="form-label small">Address</label>
                <input className="form-control form-control-sm" required value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
              </div>
              <div className="col-md-6">
                <label className="form-label small">Emergency contact</label>
                <input className="form-control form-control-sm" required value={form.emergency_contact} onChange={(e) => setForm({ ...form, emergency_contact: e.target.value })} />
              </div>
              <div className="col-md-6">
                <label className="form-label small">Account number</label>
                <input className="form-control form-control-sm" required value={form.account_number} onChange={(e) => setForm({ ...form, account_number: e.target.value })} />
              </div>
              <div className="col-md-6">
                <label className="form-label small">Bank</label>
                <input className="form-control form-control-sm" required value={form.bank} onChange={(e) => setForm({ ...form, bank: e.target.value })} />
              </div>
            </div>
            <button type="submit" className="btn btn-success btn-sm mt-3" disabled={busy}>
              {busy ? 'Creating employee...' : 'Complete onboarding'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
