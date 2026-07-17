function formatRemaining(seconds) {
  if (!seconds || seconds <= 0) return 'expired';
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  if (mins >= 60) {
    const hours = Math.floor(mins / 60);
    const remMins = mins % 60;
    return `${hours}h ${remMins}m`;
  }
  if (mins > 0) return `${mins}m ${secs}s`;
  return `${secs}s`;
}

function formatWhen(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return String(iso);
  }
}

function levelBadge(level) {
  if (level === 'error') return 'bg-danger';
  if (level === 'warning') return 'bg-warning text-dark';
  return 'bg-secondary';
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

export default function OpsAlertsCard({ alerts }) {
  const active = asArray(alerts?.active);
  const cooldowns = asArray(alerts?.cooldowns);
  const recent = asArray(alerts?.recent);

  return (
    <div className="col-12">
      <div className="card">
        <div className="card-body">
          <div className="d-flex flex-wrap justify-content-between align-items-start gap-2 mb-3">
            <div>
              <h6 className="card-title mb-1">
                <i className="bi bi-bell" aria-hidden="true" /> Alert status
              </h6>
              <p className="small text-muted mb-0">
                Active breaches and recent emissions (cooldown {alerts?.cooldown_minutes ?? 30} min).
              </p>
            </div>
            <div className="d-flex gap-2">
              <span className={`badge ${(alerts?.breach_count || 0) > 0 ? 'bg-danger' : 'bg-success'}`}>
                {alerts?.breach_count || 0} active
              </span>
              <span className="badge bg-secondary">
                {alerts?.cooldown_active_count || 0} in cooldown
              </span>
            </div>
          </div>

          {active.length === 0 ? (
            <div className="alert alert-success py-2 small mb-3" role="status">
              No active health, SLO, or DR breaches right now.
            </div>
          ) : (
            <div className="mb-3">
              <p className="small fw-semibold mb-2">Active breaches</p>
              <ul className="list-group list-group-flush border rounded mb-0">
                {active.map((alert) => (
                  <li key={alert.key || alert.title} className="list-group-item px-3 py-2">
                    <div className="d-flex justify-content-between gap-2 align-items-start">
                      <div>
                        <span className={`badge me-2 ${levelBadge(alert.level)}`}>{alert.level || 'info'}</span>
                        <strong className="small">{alert.title || alert.key}</strong>
                        <p className="small text-muted mb-0 mt-1">{alert.message}</p>
                      </div>
                      <code className="small text-nowrap">{alert.key}</code>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {cooldowns.length > 0 && (
            <div className="mb-3">
              <p className="small fw-semibold mb-2">Cooldownoldown / breach keys</p>
              <div className="table-responsive">
                <table className="table table-sm align-middle mb-0">
                  <caption className="visually-hidden">Alert cooldown status</caption>
                  <thead>
                    <tr>
                      <th scope="col">Key</th>
                      <th scope="col">Breaching</th>
                      <th scope="col">Cooldownoldown</th>
                      <th scope="col">Last emitted</th>
                      <th scope="col">Remaining</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cooldowns.map((row) => (
                      <tr key={row.key}>
                        <td><code>{row.key}</code></td>
                        <td>
                          {row.breaching ? (
                            <span className="badge bg-danger">yes</span>
                          ) : (
                            <span className="badge bg-light text-dark border">no</span>
                          )}
                        </td>
                        <td>
                          {row.active ? (
                            <span className="badge bg-info text-dark">active</span>
                          ) : (
                            <span className="badge bg-light text-dark border">clear</span>
                          )}
                        </td>
                        <td className="small">{formatWhen(row.last_emitted_at)}</td>
                        <td className="small">{row.active ? formatRemaining(row.remaining_seconds) : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <p className="small fw-semibold mb-2">Recent emissions</p>
          {recent.length === 0 ? (
            <p className="small text-muted mb-0">No alerts emitted yet in this cache window.</p>
          ) : (
            <div className="table-responsive">
              <table className="table table-sm align-middle mb-0">
                <caption className="visually-hidden">Recent ops alert emissions</caption>
                <thead>
                  <tr>
                    <th scope="col">When</th>
                    <th scope="col">Level</th>
                    <th scope="col">Alert</th>
                    <th scope="col">Outcome</th>
                  </tr>
                </thead>
                <tbody>
                  {recent.slice(0, 12).map((entry, idx) => (
                    <tr key={`${entry.key || 'alert'}-${entry.at || idx}-${idx}`}>
                      <td className="small text-nowrap">{formatWhen(entry.at)}</td>
                      <td><span className={`badge ${levelBadge(entry.level)}`}>{entry.level || 'info'}</span></td>
                      <td>
                        <div className="small fw-semibold">{entry.title || entry.key}</div>
                        <div className="small text-muted">{entry.message}</div>
                      </td>
                      <td>
                        <span className={`badge ${entry.outcome === 'emitted' ? 'bg-primary' : 'bg-secondary'}`}>
                          {entry.outcome || 'emitted'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
