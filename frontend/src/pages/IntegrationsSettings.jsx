import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function IntegrationsSettings() {
  const { user } = useAuth();
  const [apiKeys, setApiKeys] = useState([]);
  const [webhooks, setWebhooks] = useState([]);
  const [events, setEvents] = useState([]);
  const [newKeyName, setNewKeyName] = useState('');
  const [createdKey, setCreatedKey] = useState('');
  const [webhookForm, setWebhookForm] = useState({ name: '', url: '', events: [] });
  const [error, setError] = useState('');

  const load = async () => {
    const [keys, hooks, ev] = await Promise.all([
      api.listRaw('api-keys').then((d) => d.results || d),
      api.listRaw('webhooks').then((d) => d.results || d),
      api.getWebhookEvents(),
    ]);
    setApiKeys(keys);
    setWebhooks(hooks);
    setEvents(ev.events || []);
  };

  useEffect(() => {
    if (user?.is_admin) load().catch((err) => setError(err.message));
  }, [user]);

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
    } catch (err) {
      setError(err.message);
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
    <div className="card">
      <div className="card-body">
        <h5 className="card-title"><i className="bi bi-plug" /> Integrations</h5>
        {error && <div className="alert alert-danger">{error}</div>}

        <h6 className="mt-3">API Keys</h6>
        <p className="text-muted small">Use header: <code>Authorization: Api-Key &lt;your-key&gt;</code></p>
        {createdKey && (
          <div className="alert alert-warning">
            Copy this key now — it won&apos;t be shown again:<br />
            <code>{createdKey}</code>
          </div>
        )}
        <form className="row g-2 mb-3" onSubmit={createKey}>
          <div className="col-md-6">
            <input className="form-control" placeholder="Key name" value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)} required />
          </div>
          <div className="col-md-3">
            <button type="submit" className="btn btn-primary w-100">Generate Key</button>
          </div>
        </form>
        <ul className="list-group mb-4">
          {apiKeys.map((key) => (
            <li key={key.id} className="list-group-item d-flex justify-content-between">
              <span>{key.name} <code>{key.prefix}…</code></span>
              <span className="text-muted small">{key.is_active ? 'Active' : 'Inactive'}</span>
            </li>
          ))}
        </ul>

        <h6>Webhooks</h6>
        <form className="mb-3" onSubmit={createWebhook}>
          <div className="row g-2 mb-2">
            <div className="col-md-4">
              <input className="form-control" placeholder="Name" value={webhookForm.name}
                onChange={(e) => setWebhookForm({ ...webhookForm, name: e.target.value })} required />
            </div>
            <div className="col-md-5">
              <input className="form-control" placeholder="https://..." value={webhookForm.url}
                onChange={(e) => setWebhookForm({ ...webhookForm, url: e.target.value })} required />
            </div>
            <div className="col-md-3">
              <button type="submit" className="btn btn-primary w-100">Add Webhook</button>
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
        <ul className="list-group">
          {webhooks.map((hook) => (
            <li key={hook.id} className="list-group-item">
              <strong>{hook.name}</strong> — {hook.url}
              <div className="small text-muted">{(hook.events || []).join(', ') || 'No events'}</div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
