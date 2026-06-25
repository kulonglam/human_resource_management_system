import { useCallback, useEffect, useState } from 'react';
import { api } from '../../api/client';

const ROLES = [
  { value: 'recruiter', label: 'Recruiter' },
  { value: 'hiring_manager', label: 'Hiring Manager' },
  { value: 'interviewer', label: 'Interviewer' },
  { value: 'coordinator', label: 'Coordinator' },
];

export default function JobEnterpriseConfig({ jobId, canManage, onClose }) {
  const [tab, setTab] = useState('stages');
  const [stages, setStages] = useState([]);
  const [team, setTeam] = useState([]);
  const [criteria, setCriteria] = useState([]);
  const [users, setUsers] = useState([]);
  const [error, setError] = useState('');
  const [newMember, setNewMember] = useState({ user: '', role: 'recruiter' });
  const [newCriterion, setNewCriterion] = useState({ name: '', description: '' });

  const load = useCallback(async () => {
    try {
      const [stageRows, teamRows, critRows, userRows] = await Promise.all([
        api.list('pipeline-stages', `job=${jobId}`),
        api.list('hiring-team', `job=${jobId}`),
        api.list('scorecard-criteria', `job=${jobId}`),
        api.list('users').catch(() => []),
      ]);
      setStages(stageRows);
      setTeam(teamRows);
      setCriteria(critRows);
      setUsers(userRows);
    } catch (err) {
      setError(err.message);
    }
  }, [jobId]);

  useEffect(() => {
    load();
  }, [load]);

  const addMember = async () => {
    await api.create('hiring-team', { job: Number(jobId), user: Number(newMember.user), role: newMember.role });
    setNewMember({ user: '', role: 'recruiter' });
    load();
  };

  const addCriterion = async () => {
    await api.create('scorecard-criteria', {
      job: Number(jobId),
      name: newCriterion.name,
      description: newCriterion.description,
      order: criteria.length,
    });
    setNewCriterion({ name: '', description: '' });
    load();
  };

  return (
    <>
      <div className="modal show d-block" tabIndex="-1">
        <div className="modal-dialog modal-lg">
          <div className="modal-content">
            <div className="modal-header">
              <h5 className="modal-title">Enterprise job setup</h5>
              <button type="button" className="btn-close" onClick={onClose} />
            </div>
            <div className="modal-body">
              {error && <div className="alert alert-danger py-2">{error}</div>}
              <ul className="nav nav-tabs mb-3">
                {['stages', 'team', 'scorecard'].map((id) => (
                  <li className="nav-item" key={id}>
                    <button type="button" className={`nav-link ${tab === id ? 'active' : ''}`} onClick={() => setTab(id)}>
                      {id === 'stages' ? 'Pipeline' : id === 'team' ? 'Hiring team' : 'Scorecard'}
                    </button>
                  </li>
                ))}
              </ul>

              {tab === 'stages' && (
                <div className="table-responsive">
                  <table className="table table-sm">
                    <thead><tr><th>Order</th><th>Stage</th><th>Type</th></tr></thead>
                    <tbody>
                      {stages.map((s) => (
                        <tr key={s.id}><td>{s.order}</td><td>{s.label}</td><td>{s.stage_type}</td></tr>
                      ))}
                    </tbody>
                  </table>
                  <p className="small text-muted mb-0">Stages are configurable per job. Drag candidates on the pipeline when a job filter is active.</p>
                </div>
              )}

              {tab === 'team' && (
                <>
                  <ul className="list-group mb-3">
                    {team.map((m) => (
                      <li className="list-group-item d-flex justify-content-between" key={m.id}>
                        <span>{m.user_name} <span className="text-muted">({m.role.replace('_', ' ')})</span></span>
                      </li>
                    ))}
                    {!team.length && <li className="list-group-item text-muted">No team members yet.</li>}
                  </ul>
                  {canManage && (
                    <div className="row g-2">
                      <div className="col-md-6">
                        <select className="form-select form-select-sm" value={newMember.user} onChange={(e) => setNewMember({ ...newMember, user: e.target.value })}>
                          <option value="">Select user...</option>
                          {users.map((u) => <option key={u.id} value={u.id}>{u.username}</option>)}
                        </select>
                      </div>
                      <div className="col-md-4">
                        <select className="form-select form-select-sm" value={newMember.role} onChange={(e) => setNewMember({ ...newMember, role: e.target.value })}>
                          {ROLES.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
                        </select>
                      </div>
                      <div className="col-md-2">
                        <button type="button" className="btn btn-primary btn-sm w-100" disabled={!newMember.user} onClick={addMember}>Add</button>
                      </div>
                    </div>
                  )}
                </>
              )}

              {tab === 'scorecard' && (
                <>
                  <ul className="list-group mb-3">
                    {criteria.map((c) => (
                      <li className="list-group-item" key={c.id}>
                        <strong>{c.name}</strong>
                        {c.description && <div className="small text-muted">{c.description}</div>}
                      </li>
                    ))}
                    {!criteria.length && <li className="list-group-item text-muted">No criteria defined.</li>}
                  </ul>
                  {canManage && (
                    <div className="row g-2">
                      <div className="col-md-5">
                        <input className="form-control form-control-sm" placeholder="Criterion name" value={newCriterion.name} onChange={(e) => setNewCriterion({ ...newCriterion, name: e.target.value })} />
                      </div>
                      <div className="col-md-5">
                        <input className="form-control form-control-sm" placeholder="Description" value={newCriterion.description} onChange={(e) => setNewCriterion({ ...newCriterion, description: e.target.value })} />
                      </div>
                      <div className="col-md-2">
                        <button type="button" className="btn btn-primary btn-sm w-100" disabled={!newCriterion.name} onClick={addCriterion}>Add</button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-secondary" onClick={onClose}>Close</button>
            </div>
          </div>
        </div>
      </div>
      <div className="modal-backdrop show" />
    </>
  );
}
