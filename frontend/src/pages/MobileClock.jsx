import { useEffect, useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import {
  clearQueuedPunches,
  enqueuePunch,
  listQueuedPunches,
  makeClientPunchId,
} from '../utils/offlinePunchQueue';

export default function MobileClock() {
  const { user } = useAuth();
  const [online, setOnline] = useState(typeof navigator !== 'undefined' ? navigator.onLine : true);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [queueCount, setQueueCount] = useState(0);
  const [busy, setBusy] = useState(false);

  async function refreshQueue() {
    const items = await listQueuedPunches();
    setQueueCount(items.length);
  }

  async function flushQueue() {
    const items = await listQueuedPunches();
    if (!items.length) return;
    try {
      const result = await api.syncMobilePunches(items);
      const done = (result.results || [])
        .filter((row) => row.applied || row.client_punch_id)
        .map((row) => row.client_punch_id)
        .filter(Boolean);
      await clearQueuedPunches(done);
      await refreshQueue();
      setStatus(`Synced ${done.length} offline punch(es).`);
    } catch (err) {
      setError(err.message || 'Sync failed — punches stay queued.');
    }
  }

  useEffect(() => {
    const onOnline = () => {
      setOnline(true);
      flushQueue();
    };
    const onOffline = () => setOnline(false);
    window.addEventListener('online', onOnline);
    window.addEventListener('offline', onOffline);
    refreshQueue();
    if (navigator.onLine) flushQueue();
    return () => {
      window.removeEventListener('online', onOnline);
      window.removeEventListener('offline', onOffline);
    };
  }, []);

  if (!user) return <Navigate to="/login" replace />;

  async function punch(punchType) {
    setBusy(true);
    setError('');
    setStatus('');
    const payload = {
      punch_type: punchType,
      punched_at: new Date().toISOString(),
      client_punch_id: makeClientPunchId(),
    };
    try {
      if (!navigator.onLine) {
        await enqueuePunch(payload);
        await refreshQueue();
        setStatus(`Offline: ${punchType === 'out' ? 'clock-out' : 'clock-in'} queued.`);
        return;
      }
      await api.mobilePunch(payload);
      setStatus(`Recorded ${punchType === 'out' ? 'clock-out' : 'clock-in'}.`);
      await flushQueue();
    } catch (err) {
      await enqueuePunch(payload);
      await refreshQueue();
      setError(err.message || 'Network error — punch queued offline.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mobile-clock min-vh-100 d-flex flex-column" style={{ background: '#0f172a', color: '#e2e8f0' }}>
      <header className="p-3 d-flex justify-content-between align-items-center border-bottom border-secondary">
        <div>
          <div className="fw-semibold">HRMIS Mobile</div>
          <div className="small text-secondary">{user.username}</div>
        </div>
        <span className={`badge ${online ? 'bg-success' : 'bg-warning text-dark'}`}>
          {online ? 'Online' : 'Offline'}
        </span>
      </header>

      <main className="flex-grow-1 d-flex flex-column justify-content-center align-items-center gap-3 p-4">
        <p className="text-center text-secondary mb-2">
          Clock in or out. Punches queue on this device when offline and sync when you reconnect.
        </p>
        <button
          type="button"
          className="btn btn-lg btn-info w-100"
          disabled={busy}
          onClick={() => punch('in')}
        >
          Clock in
        </button>
        <button
          type="button"
          className="btn btn-lg btn-outline-light w-100"
          disabled={busy}
          onClick={() => punch('out')}
        >
          Clock out
        </button>
        {queueCount > 0 && (
          <button type="button" className="btn btn-sm btn-secondary" disabled={busy || !online} onClick={flushQueue}>
            Sync {queueCount} queued punch{queueCount === 1 ? '' : 'es'}
          </button>
        )}
        {status && <div className="alert alert-success w-100 mb-0" role="status">{status}</div>}
        {error && <div className="alert alert-warning w-100 mb-0" role="alert">{error}</div>}
      </main>

      <footer className="p-3 text-center small text-secondary">
        <Link to="/dashboard" className="link-light">Full app</Link>
        {' · '}
        English only · Install from browser for home-screen use
      </footer>
    </div>
  );
}
