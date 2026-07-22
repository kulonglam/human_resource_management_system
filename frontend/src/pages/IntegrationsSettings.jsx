import { useCallback, useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import ConfirmModal from '../components/ConfirmModal';
import SettingsBackLink from '../components/SettingsBackLink';

function DeliveryLogTable({ deliveries, loading, onSelectPayload }) {
  if (loading) {
    return (
      <div className="text-center py-3">
        <div className="spinner-border spinner-border-sm text-primary" role="status" />
      </div>
    );
  }
  if (!deliveries.length) {
    return <p className="text-muted small mb-0">No deliveries recorded yet.</p>;
  }
  return (
    <div className="table-responsive">
      <table className="table table-sm table-hover mb-0 align-middle">
        <thead>
          <tr>
            <th>Time</th>
            <th>Webhook</th>
            <th>Event</th>
            <th>Status</th>
            <th>Details</th>
          </tr>
        </thead>
        <tbody>
          {deliveries.map((row) => (
            <tr key={row.id}>
              <td className="text-nowrap small">{new Date(row.delivered_at).toLocaleString()}</td>
              <td>{row.endpoint_name}</td>
              <td><code className="small">{row.event}</code></td>
              <td>
                <span className={`badge bg-${row.success ? 'success' : 'danger'}`}>
                  {row.status_code ?? 'ERR'}
                </span>
              </td>
              <td className="small">
                {row.error_message ? (
                  <span className="text-danger text-truncate d-inline-block" style={{ maxWidth: 180 }} title={row.error_message}>
                    {row.error_message}
                  </span>
                ) : (
                  <button type="button" className="btn btn-link btn-sm p-0" onClick={() => onSelectPayload(row)}>
                    View payload
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function WorkflowSteps({ workflow }) {
  return (
    <div className="border rounded p-3 mb-3">
      <div className="d-flex justify-content-between align-items-start mb-2">
        <div>
          <strong>{workflow.name}</strong>
          <span className="badge bg-secondary ms-2">{workflow.workflow_type}</span>
          {workflow.is_default && <span className="badge bg-info ms-1">Default</span>}
        </div>
      </div>
      <ol className="mb-0 small ps-3">
        {(workflow.steps || []).map((step) => (
          <li key={step.id}>
            {step.label} <span className="text-muted">({step.approver_type})</span>
          </li>
        ))}
      </ol>
      {(workflow.extra_step_min_days || workflow.extra_step_min_amount) && (
        <div className="small text-muted mt-2">
          {workflow.extra_step_min_days != null && (
            <span className="me-3">HR step when leave ≥ {workflow.extra_step_min_days} days</span>
          )}
          {workflow.extra_step_min_amount != null && (
            <span>HR step when expense ≥ {Number(workflow.extra_step_min_amount).toLocaleString()}</span>
          )}
        </div>
      )}
    </div>
  );
}

export default function IntegrationsSettings() {
  const { user } = useAuth();
  const [apiKeys, setApiKeys] = useState([]);
  const [webhooks, setWebhooks] = useState([]);
  const [events, setEvents] = useState([]);
  const [deliveries, setDeliveries] = useState([]);
  const [workflows, setWorkflows] = useState([]);
  const [deliveryFilter, setDeliveryFilter] = useState({ endpoint: '', success: '' });
  const [selectedPayload, setSelectedPayload] = useState(null);
  const [loadingDeliveries, setLoadingDeliveries] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [createdKey, setCreatedKey] = useState('');
  const [webhookForm, setWebhookForm] = useState({ name: '', url: '', events: [] });
  const [error, setError] = useState('');
  const [webhookToDelete, setWebhookToDelete] = useState(null);
  const [deletingWebhook, setDeletingWebhook] = useState(false);

  const loadDeliveries = useCallback(async () => {
    setLoadingDeliveries(true);
    try {
      const params = new URLSearchParams();
      if (deliveryFilter.endpoint) params.set('endpoint', deliveryFilter.endpoint);
      if (deliveryFilter.success) params.set('success', deliveryFilter.success);
      params.set('limit', '100');
      const data = await api.getWebhookDeliveryLog(params.toString());
      setDeliveries(data);
    } catch (err) {
      setError(err.message);
      setDeliveries([]);
    } finally {
      setLoadingDeliveries(false);
    }
  }, [deliveryFilter]);

  const load = async () => {
    const [keys, hooks, ev, wf] = await Promise.all([
      api.listRaw('api-keys').then((d) => d.results || d),
      api.listRaw('webhooks').then((d) => d.results || d),
      api.getWebhookEvents(),
      api.getApprovalWorkflows().then((d) => d.results || d),
    ]);
    setApiKeys(keys);
    setWebhooks(hooks);
    setEvents(ev.events || []);
    setWorkflows(wf);
  };

  useEffect(() => {
    if (user?.is_admin) {
      load().catch((err) => setError(err.message));
    }
  }, [user]);

  useEffect(() => {
    if (user?.is_admin) loadDeliveries();
  }, [user, loadDeliveries]);

  if (!user?.is_admin) return <Navigate to="/dashboard" replace />;

  const createKey = async (e) => {
    e.preventDefault();
    setError('');
    setCreatedKey('');
    try {
      const data = await api.create('api-keys', { name: newKeyName });
      setCreatedKey(data.api_key);
      setNewKeyName('');
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  const createWebhook = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await api.create('webhooks', webhookForm);
      setWebhookForm({ name: '', url: '', events: [] });
      load();
      loadDeliveries();
    } catch (err) {
      setError(err.message);
    }
  };

  const toggleWebhookActive = async (hook) => {
    try {
      await api.update('webhooks', hook.id, { is_active: !hook.is_active });
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  const confirmDeleteWebhook = async () => {
    if (!webhookToDelete) return;
    setDeletingWebhook(true);
    try {
      await api.remove('webhooks', webhookToDelete.id);
      setWebhookToDelete(null);
      load();
      loadDeliveries();
    } catch (err) {
      setError(err.message);
    } finally {
      setDeletingWebhook(false);
    }
  };

  const toggleEvent = (event) => {
    setWebhookForm((prev) => ({
      ...prev,
      events: prev.events.includes(event)
        ? prev.events.filter((e) => e !== event)
        : [...prev.events, event],
    }));
  };

  return (
    <>
      <SettingsBackLink />
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4 className="page-heading mb-0">
          <i className="bi bi-plug" style={{ color: 'var(--fca-lime)' }} /> Integrations
        </h4>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="card mb-4">
        <div className="card-body">
          <h6>API Keys</h6>
          <p className="text-muted small">Use header: <code>Authorization: Api-Key &lt;your-key&gt;</code></p>
          {createdKey && (
            <div className="alert alert-warning">
              Copy this key now — it won&apos;t be shown again:<br />
              <code>{createdKey}</code>
            </div>
          )}
          <form className="row g-2 mb-3" onSubmit={createKey}>
            <div className="col-md-6">
              <input className="form-control form-control-sm" placeholder="Key name" value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)} required />
            </div>
            <div className="col-md-3">
              <button type="submit" className="btn btn-primary btn-sm w-100">Generate Key</button>
            </div>
          </form>
          <ul className="list-group list-group-flush">
            {apiKeys.map((key) => (
              <li key={key.id} className="list-group-item px-0 d-flex justify-content-between">
                <span>{key.name} <code>{key.prefix}…</code></span>
                <span className="text-muted small">{key.is_active ? 'Active' : 'Inactive'}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="card mb-4">
        <div className="card-body">
          <h6>Webhooks</h6>
          <form className="mb-3" onSubmit={createWebhook}>
            <div className="row g-2 mb-2">
              <div className="col-md-4">
                <input className="form-control form-control-sm" placeholder="Name" value={webhookForm.name}
                  onChange={(e) => setWebhookForm({ ...webhookForm, name: e.target.value })} required />
              </div>
              <div className="col-md-5">
                <input className="form-control form-control-sm" placeholder="https://..." value={webhookForm.url}
                  onChange={(e) => setWebhookForm({ ...webhookForm, url: e.target.value })} required />
              </div>
              <div className="col-md-3">
                <button type="submit" className="btn btn-primary btn-sm w-100">Add Webhook</button>
              </div>
            </div>
            <div className="d-flex flex-wrap gap-2">
              {events.map((event) => (
                <label key={event} className="form-check-label small border rounded px-2 py-1">
                  <input type="checkbox" className="form-check-input me-1"
                    checked={webhookForm.events.includes(event)}
                    onChange={() => toggleEvent(event)} />
                  {event}
                </label>
              ))}
            </div>
          </form>
          <ul className="list-group list-group-flush">
            {webhooks.map((hook) => (
              <li key={hook.id} className="list-group-item px-0">
                <div className="d-flex justify-content-between align-items-start gap-2 flex-wrap">
                  <div>
                    <strong>{hook.name}</strong>
                    <span className={`badge ms-2 bg-${hook.is_active ? 'success' : 'secondary'}`}>
                      {hook.is_active ? 'Active' : 'Inactive'}
                    </span>
                    <div className="small text-muted">{hook.url}</div>
                    <div className="small text-muted">{(hook.events || []).join(', ') || 'No events'}</div>
                  </div>
                  <div className="d-flex gap-1">
                    <button type="button" className="btn btn-outline-secondary btn-sm"
                      onClick={() => setDeliveryFilter({ endpoint: String(hook.id), success: '' })}>
                      Deliveries
                    </button>
                    <button type="button" className="btn btn-outline-secondary btn-sm"
                      onClick={() => toggleWebhookActive(hook)}>
                      {hook.is_active ? 'Disable' : 'Enable'}
                    </button>
                    <button type="button" className="btn btn-outline-danger btn-sm"
                      onClick={() => setWebhookToDelete(hook)}>
                      Delete
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="card mb-4">
        <div className="card-body">
          <div className="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
            <h6 className="mb-0">Delivery log</h6>
            <div className="d-flex gap-2">
              <select className="form-select form-select-sm" style={{ width: 'auto' }}
                value={deliveryFilter.endpoint}
                onChange={(e) => setDeliveryFilter((f) => ({ ...f, endpoint: e.target.value }))}>
                <option value="">All webhooks</option>
                {webhooks.map((hook) => (
                  <option key={hook.id} value={hook.id}>{hook.name}</option>
                ))}
              </select>
              <select className="form-select form-select-sm" style={{ width: 'auto' }}
                value={deliveryFilter.success}
                onChange={(e) => setDeliveryFilter((f) => ({ ...f, success: e.target.value }))}>
                <option value="">All statuses</option>
                <option value="1">Success only</option>
                <option value="0">Failed only</option>
              </select>
              <button type="button" className="btn btn-outline-primary btn-sm" onClick={loadDeliveries}>
                Refresh
              </button>
            </div>
          </div>
          <DeliveryLogTable
            deliveries={deliveries}
            loading={loadingDeliveries}
            onSelectPayload={setSelectedPayload}
          />
        </div>
      </div>

      <div className="card">
        <div className="card-body">
          <h6>Approval workflows</h6>
          <p className="text-muted small mb-3">
            Read-only view of active approval chains. Edit via Django admin or run <code>seed_workflows</code> to reset defaults.
          </p>
          {workflows.map((workflow) => (
            <WorkflowSteps key={workflow.id} workflow={workflow} />
          ))}
          {!workflows.length && <p className="text-muted small mb-0">No workflows configured.</p>}
        </div>
      </div>

      {selectedPayload && (
        <>
          <div className="modal show d-block" tabIndex="-1">
            <div className="modal-dialog modal-lg">
              <div className="modal-content">
                <div className="modal-header">
                  <h5 className="modal-title">Webhook payload — {selectedPayload.event}</h5>
                  <button type="button" className="btn-close" onClick={() => setSelectedPayload(null)} />
                </div>
                <div className="modal-body">
                  <pre className="bg-light p-3 rounded small mb-0" style={{ maxHeight: 400, overflow: 'auto' }}>
                    {JSON.stringify(selectedPayload.payload, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          </div>
          <div className="modal-backdrop show" />
        </>
      )}

      <ConfirmModal
        open={Boolean(webhookToDelete)}
        title="Delete webhook"
        message={
          webhookToDelete
            ? `Delete webhook "${webhookToDelete.name}"? This cannot be undone.`
            : ''
        }
        confirmLabel="Delete"
        confirmVariant="danger"
        busy={deletingWebhook}
        onCancel={() => !deletingWebhook && setWebhookToDelete(null)}
        onConfirm={confirmDeleteWebhook}
      />
    </>
  );
}
