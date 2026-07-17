export default function OpsSLOCard({ slos }) {
  return (
    <div className="col-lg-4">
      <div className="card h-100">
        <div className="card-body">
          <h6 className="card-title">SLO (current hour)</h6>
          {slos && (
            <>
              <p className="mb-1">Availability: <strong>{slos.availability_percent}%</strong></p>
              <p className="mb-1">Avg latency: <strong>{slos.avg_latency_ms} ms</strong></p>
              <p className="mb-1">Requests: {slos.requests} · 5xx: {slos.server_errors}</p>
              <span className={`badge ${slos.within_slo ? 'bg-success' : 'bg-danger'}`}>
                {slos.within_slo ? 'Within SLO' : 'SLO breached'}
              </span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
