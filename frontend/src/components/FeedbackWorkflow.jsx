import { useCallback, useEffect, useState } from 'react';
import { api } from '../api/client';
import { renderStatus } from '../config/shared';

const RATING_FIELDS = [
  { name: 'communication', label: 'Communication' },
  { name: 'leadership', label: 'Leadership' },
  { name: 'teamwork', label: 'Teamwork' },
  { name: 'reliability', label: 'Reliability' },
  { name: 'initiative', label: 'Initiative' },
  { name: 'problem_solving', label: 'Problem Solving' },
];

const GIVER_TYPES = [
  { value: 'manager', label: 'Manager' },
  { value: 'peer', label: 'Peer' },
  { value: 'direct_report', label: 'Direct Report' },
  { value: 'other', label: 'Other' },
];

const RATING_OPTIONS = [
  { value: 1, label: '1 - Strongly Disagree' },
  { value: 2, label: '2 - Disagree' },
  { value: 3, label: '3 - Neutral' },
  { value: 4, label: '4 - Agree' },
  { value: 5, label: '5 - Strongly Agree' },
];

export default function FeedbackWorkflow({ lookupOptions = {}, isManager = false }) {
  const [section, setSection] = useState('mine');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const [myData, setMyData] = useState({ requests: [], pending: 0, submitted: 0 });
  const [rounds, setRounds] = useState([]);
  const [selectedRound, setSelectedRound] = useState('');
  const [roundDetail, setRoundDetail] = useState(null);
  const [users, setUsers] = useState([]);
  const [bulkForm, setBulkForm] = useState({ recipient: '', feedback_giver: '', giver_type: 'peer' });

  const [submitTarget, setSubmitTarget] = useState(null);
  const [submitForm, setSubmitForm] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const [summaryEmployee, setSummaryEmployee] = useState('');
  const [summaryRound, setSummaryRound] = useState('');
  const [summaryData, setSummaryData] = useState(null);

  const loadMine = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setMyData(await api.getMyFeedbackRequests());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadRounds = useCallback(async () => {
    try {
      const data = await api.list('feedback-rounds');
      setRounds(data);
    } catch {
      /* optional for employees */
    }
  }, []);

  const loadUsers = useCallback(async () => {
    if (!isManager) return;
    try {
      const data = await api.getUsers();
      setUsers(data.results || data);
    } catch {
      /* admin/manager only */
    }
  }, [isManager]);

  useEffect(() => {
    loadMine();
    loadRounds();
    loadUsers();
  }, [loadMine, loadRounds, loadUsers]);

  const loadRoundDetail = async (roundId) => {
    if (!roundId) {
      setRoundDetail(null);
      return;
    }
    setLoading(true);
    setError('');
    try {
      setRoundDetail(await api.getFeedbackRoundDetail(roundId));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleBulkCreate = async (e) => {
    e.preventDefault();
    if (!selectedRound) return;
    setError('');
    try {
      const result = await api.createFeedbackRequests(selectedRound, [bulkForm]);
      setBulkForm({ recipient: '', feedback_giver: '', giver_type: 'peer' });
      await loadRoundDetail(selectedRound);
      setError('');
      alert(`${result.created} feedback request(s) created.`);
    } catch (err) {
      setError(err.data?.detail || err.message);
    }
  };

  const openSubmit = (req) => {
    setSubmitTarget(req);
    setSubmitForm({
      communication: 3,
      leadership: 3,
      teamwork: 3,
      reliability: 3,
      initiative: 3,
      problem_solving: 3,
      strengths: '',
      areas_for_improvement: '',
      additional_comments: '',
      is_anonymous: false,
    });
  };

  const handleSubmitFeedback = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      await api.submitFeedback(submitTarget.id, {
        ...submitForm,
        is_anonymous: Boolean(submitForm.is_anonymous),
      });
      setSubmitTarget(null);
      loadMine();
    } catch (err) {
      setError(err.data?.detail || err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const loadSummary = async () => {
    if (!summaryEmployee) return;
    setLoading(true);
    setError('');
    try {
      setSummaryData(await api.getEmployeeFeedbackSummary(summaryEmployee, summaryRound));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <ul className="nav nav-pills mb-3">
        <li className="nav-item">
          <button type="button" className={`nav-link ${section === 'mine' ? 'active' : ''}`} onClick={() => setSection('mine')}>
            My Requests
          </button>
        </li>
        {isManager && (
          <li className="nav-item">
            <button type="button" className={`nav-link ${section === 'rounds' ? 'active' : ''}`} onClick={() => setSection('rounds')}>
              Manage Rounds
            </button>
          </li>
        )}
        <li className="nav-item">
          <button type="button" className={`nav-link ${section === 'summary' ? 'active' : ''}`} onClick={() => setSection('summary')}>
            Employee Summary
          </button>
        </li>
      </ul>

      {error && <div className="alert alert-danger">{error}</div>}

      {section === 'mine' && (
        <>
          <div className="row mb-3">
            <div className="col-auto">
              <span className="badge bg-warning text-dark me-2">Pending: {myData.pending}</span>
              <span className="badge bg-success">Submitted: {myData.submitted}</span>
            </div>
          </div>
          {loading ? (
            <div className="text-center py-4"><div className="spinner-border text-primary" role="status" /></div>
          ) : (
            <div className="table-responsive card">
              <table className="table table-hover mb-0">
                <thead>
                  <tr>
                    <th>Round</th><th>Recipient</th><th>Type</th><th>Status</th><th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {myData.requests.map((req) => (
                    <tr key={req.id}>
                      <td>{req.round_name}</td>
                      <td>{req.recipient_name}</td>
                      <td>{req.giver_type}</td>
                      <td>{renderStatus(req.status)}</td>
                      <td>
                        {req.status === 'pending' && (
                          <button type="button" className="btn btn-primary btn-sm" onClick={() => openSubmit(req)}>
                            Submit Feedback
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                  {!myData.requests.length && (
                    <tr><td colSpan={5} className="text-center py-4 text-muted">No feedback requests assigned to you.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {section === 'rounds' && isManager && (
        <div className="row g-3">
          <div className="col-md-4">
            <div className="card">
              <div className="card-body">
                <label className="form-label">Select Round</label>
                <select
                  className="form-select form-select-sm mb-3"
                  value={selectedRound}
                  onChange={(e) => {
                    setSelectedRound(e.target.value);
                    loadRoundDetail(e.target.value);
                  }}
                >
                  <option value="">Choose round...</option>
                  {rounds.map((r) => (
                    <option key={r.id} value={r.id}>{r.name}</option>
                  ))}
                </select>
                {roundDetail?.stats && (
                  <div className="small text-muted">
                    <div>Total: {roundDetail.stats.total}</div>
                    <div>Pending: {roundDetail.stats.pending}</div>
                    <div>Submitted: {roundDetail.stats.submitted}</div>
                  </div>
                )}
              </div>
            </div>
            {selectedRound && (
              <form className="card mt-3" onSubmit={handleBulkCreate}>
                <div className="card-body">
                  <h6 className="card-title">Add Feedback Request</h6>
                  <div className="mb-2">
                    <label className="form-label">Recipient (Employee)</label>
                    <select className="form-select form-select-sm" value={bulkForm.recipient} required
                      onChange={(e) => setBulkForm((p) => ({ ...p, recipient: e.target.value }))}>
                      <option value="">Select...</option>
                      {(lookupOptions.employee || []).map((o) => (
                        <option key={o.value} value={o.value}>{o.label}</option>
                      ))}
                    </select>
                  </div>
                  <div className="mb-2">
                    <label className="form-label">Feedback Giver (User)</label>
                    <select className="form-select form-select-sm" value={bulkForm.feedback_giver} required
                      onChange={(e) => setBulkForm((p) => ({ ...p, feedback_giver: e.target.value }))}>
                      <option value="">Select...</option>
                      {users.map((u) => (
                        <option key={u.id} value={u.id}>{u.username}</option>
                      ))}
                    </select>
                  </div>
                  <div className="mb-3">
                    <label className="form-label">Relationship</label>
                    <select className="form-select form-select-sm" value={bulkForm.giver_type}
                      onChange={(e) => setBulkForm((p) => ({ ...p, giver_type: e.target.value }))}>
                      {GIVER_TYPES.map((t) => (
                        <option key={t.value} value={t.value}>{t.label}</option>
                      ))}
                    </select>
                  </div>
                  <button type="submit" className="btn btn-primary btn-sm w-100">Create Request</button>
                </div>
              </form>
            )}
          </div>
          <div className="col-md-8">
            {roundDetail?.requests && (
              <div className="table-responsive card">
                <table className="table table-sm mb-0">
                  <thead><tr><th>Recipient</th><th>Giver</th><th>Type</th><th>Status</th></tr></thead>
                  <tbody>
                    {roundDetail.requests.map((req) => (
                      <tr key={req.id}>
                        <td>{req.recipient_name}</td>
                        <td>{req.giver_username}</td>
                        <td>{req.giver_type}</td>
                        <td>{renderStatus(req.status)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {section === 'summary' && (
        <>
          <div className="row g-2 mb-3 align-items-end">
            <div className="col-md-4">
              <label className="form-label">Employee</label>
              <select className="form-select form-select-sm" value={summaryEmployee}
                onChange={(e) => setSummaryEmployee(e.target.value)}>
                <option value="">Select employee...</option>
                {(lookupOptions.employee || []).map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
            <div className="col-md-4">
              <label className="form-label">Round (optional)</label>
              <select className="form-select form-select-sm" value={summaryRound}
                onChange={(e) => setSummaryRound(e.target.value)}>
                <option value="">All rounds</option>
                {rounds.map((r) => (
                  <option key={r.id} value={r.id}>{r.name}</option>
                ))}
              </select>
            </div>
            <div className="col-md-4">
              <button type="button" className="btn btn-primary btn-sm" onClick={loadSummary} disabled={!summaryEmployee}>
                Load Summary
              </button>
            </div>
          </div>
          {summaryData && (
            <div className="card">
              <div className="card-body">
                <h5>{summaryData.employee.full_name}</h5>
                <p className="text-muted">{summaryData.response_count} submitted response(s)</p>
                <div className="row">
                  {RATING_FIELDS.map((f) => (
                    <div className="col-md-4 mb-2" key={f.name}>
                      <strong>{f.label}:</strong>{' '}
                      {summaryData.averages[f.name] ?? '—'} / 5
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {submitTarget && (
        <>
          <div className="modal show d-block" tabIndex="-1">
            <div className="modal-dialog modal-lg">
              <div className="modal-content">
                <form onSubmit={handleSubmitFeedback}>
                  <div className="modal-header">
                    <h5 className="modal-title">Feedback for {submitTarget.recipient_name}</h5>
                    <button type="button" className="btn-close" onClick={() => setSubmitTarget(null)} />
                  </div>
                  <div className="modal-body">
                    <div className="row">
                      {RATING_FIELDS.map((f) => (
                        <div className="col-md-6 mb-3" key={f.name}>
                          <label className="form-label">{f.label}</label>
                          <select className="form-select form-select-sm" value={submitForm[f.name]} required
                            onChange={(e) => setSubmitForm((p) => ({ ...p, [f.name]: Number(e.target.value) }))}>
                            {RATING_OPTIONS.map((o) => (
                              <option key={o.value} value={o.value}>{o.label}</option>
                            ))}
                          </select>
                        </div>
                      ))}
                      <div className="col-12 mb-3">
                        <label className="form-label">Strengths</label>
                        <textarea className="form-control form-control-sm" rows={2} value={submitForm.strengths}
                          onChange={(e) => setSubmitForm((p) => ({ ...p, strengths: e.target.value }))} />
                      </div>
                      <div className="col-12 mb-3">
                        <label className="form-label">Areas for Improvement</label>
                        <textarea className="form-control form-control-sm" rows={2} value={submitForm.areas_for_improvement}
                          onChange={(e) => setSubmitForm((p) => ({ ...p, areas_for_improvement: e.target.value }))} />
                      </div>
                      <div className="col-12">
                        <div className="form-check">
                          <input type="checkbox" className="form-check-input" id="anonCheck" checked={submitForm.is_anonymous}
                            onChange={(e) => setSubmitForm((p) => ({ ...p, is_anonymous: e.target.checked }))} />
                          <label className="form-check-label" htmlFor="anonCheck">Submit anonymously</label>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="modal-footer">
                    <button type="button" className="btn btn-secondary" onClick={() => setSubmitTarget(null)}>Cancel</button>
                    <button type="submit" className="btn btn-primary" disabled={submitting}>
                      {submitting ? 'Submitting...' : 'Submit Feedback'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
          <div className="modal-backdrop show" />
        </>
      )}
    </>
  );
}
