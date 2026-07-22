function asArray(value) {
  return Array.isArray(value) ? value : [];
}

export default function OpsUsageCard({ usage }) {
  const data = usage && typeof usage === 'object' ? usage : {};
  const topPaths = asArray(data.top_paths);

  return (
    <div className="col-12 col-lg-6">
      <div className="card h-100 border-0 shadow-sm">
        <div className="card-body">
          <h2 className="h5 mb-3">
            <i className="bi bi-graph-up-arrow me-2" aria-hidden="true" />
            Usage / cost signals
          </h2>
          <p className="text-muted small mb-3">
            {data.note || 'Daily API request totals for capacity planning.'}
          </p>
          <dl className="row mb-3">
            <dt className="col-6">Window</dt>
            <dd className="col-6">{data.window || 'current_day'}</dd>
            <dt className="col-6">Total requests</dt>
            <dd className="col-6">{data.total_requests ?? 0}</dd>
          </dl>
          {topPaths.length === 0 ? (
            <p className="text-muted small mb-0">No path samples yet for this day.</p>
          ) : (
            <ul className="list-unstyled mb-0 small">
              {topPaths.slice(0, 8).map((row) => (
                <li key={row.path} className="d-flex justify-content-between border-bottom py-1">
                  <code className="text-truncate me-2">{row.path}</code>
                  <span>{row.requests}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
