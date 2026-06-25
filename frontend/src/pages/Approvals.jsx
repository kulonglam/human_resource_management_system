import { useCallback, useEffect, useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

const TYPE_LABELS = {
  leave: 'Leave',
  expense: 'Expense',
  recruitment: 'Recruitment',
};

const TYPE_ICONS = {
  leave: 'bi-calendar-x',
  expense: 'bi-receipt',
  recruitment: 'bi-briefcase',
};

function ApprovalRow({ item, onDecided, busyId }) {
  const [comment, setComment] = useState('');
  const [error, setError] = useState('');
  const isBusy = busyId === item.id;

  const run = async (action) => {
    setError('');
    try {
      await api.approvalAction(item.id, action, comment);
      setComment('');
      onDecided();
    } catch (err) {
      setError(err.data?.detail || err.message);
    }
  };

  return (
    <tr>
      <td>
        <span className="badge bg-secondary me-1">{TYPE_LABELS[item.workflow_type] || item.workflow_type}</span>
        <div className="fw-semibold">{item.summary}</div>
        <div className="small text-muted">{item.workflow_name}</div>
      </td>
      <td>{item.current_step || '—'}</td>
      <td>{item.submitted_by_name || '—'}</td>
      <td>{new Date(item.submitted_at).toLocaleString()}</td>
      <td>
        <input
          type="text"
          className="form-control form-control-sm mb-2"
          placeholder="Comment (optional)"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          disabled={isBusy}
        />
        {error && <div className="small text-danger mb-2">{error}</div>}
        <div className="d-flex flex-wrap gap-1">
          <button
            type="button"
            className="btn btn-success btn-sm"
            disabled={isBusy}
            onClick={() => run('approve')}
          >
            Approve
          </button>
          <button
            type="button"
            className="btn btn-outline-danger btn-sm"
            disabled={isBusy}
            onClick={() => run('reject')}
          >
            Reject
          </button>
          {item.detail_link && (
            <Link to={item.detail_link} className="btn btn-outline-secondary btn-sm">
              View
            </Link>
          )}
        </div>
      </td>
    </tr>
  );
}

export default function Approvals() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [scope, setScope] = useState('mine');
  const [busyId, setBusyId] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams({ status: 'pending', scope });
      const data = await api.getApprovalRequests(params.toString());
      setItems(data.results || data);
    } catch (err) {
      setError(err.message);
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [scope]);

  useEffect(() => {
    if (user?.is_admin || user?.is_manager) load();
  }, [user, load]);

  if (!user?.is_admin && !user?.is_manager) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleDecided = async (id) => {
    setBusyId(id);
    await load();
    setBusyId(null);
  };

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
        <h4 className="page-heading mb-0">
          <i className="bi bi-inbox" style={{ color: 'var(--fca-lime)' }} /> Approval Inbox
        </h4>
        <div className="d-flex gap-2 align-items-center">
          {user?.is_admin && (
            <select
              className="form-select form-select-sm"
              value={scope}
              onChange={(e) => setScope(e.target.value)}
              style={{ width: 'auto' }}
            >
              <option value="mine">Assigned to me</option>
              <option value="all">All pending (org)</option>
            </select>
          )}
          <button type="button" className="btn btn-outline-primary btn-sm" onClick={load} disabled={loading}>
            Refresh
          </button>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {loading ? (
        <div className="text-center py-5">
          <div className="spinner-border text-primary" role="status" />
        </div>
      ) : items.length === 0 ? (
        <div className="card">
          <div className="card-body text-center py-5 text-muted">
            <i className="bi bi-check2-circle fs-1 d-block mb-2" />
            No pending approvals — you are all caught up.
          </div>
        </div>
      ) : (
        <>
          <div className="row g-3 mb-4">
            {['leave', 'expense', 'recruitment'].map((type) => {
              const count = items.filter((i) => i.workflow_type === type).length;
              if (!count) return null;
              return (
                <div className="col-md-4" key={type}>
                  <div className="card border-0 shadow-sm">
                    <div className="card-body py-3 d-flex align-items-center gap-3">
                      <i className={`bi ${TYPE_ICONS[type]} fs-4`} style={{ color: 'var(--fca-lime)' }} />
                      <div>
                        <div className="fw-semibold">{TYPE_LABELS[type]}</div>
                        <div className="small text-muted">{count} pending</div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="card">
            <div className="table-responsive">
              <table className="table table-hover mb-0 align-middle">
                <thead>
                  <tr>
                    <th>Request</th>
                    <th>Current step</th>
                    <th>Submitted by</th>
                    <th>Submitted</th>
                    <th style={{ minWidth: 220 }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <ApprovalRow
                      key={item.id}
                      item={item}
                      busyId={busyId}
                      onDecided={() => handleDecided(item.id)}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </>
  );
}
