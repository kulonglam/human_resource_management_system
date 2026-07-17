export default function OpsRunbooksPanel({ runbooks }) {
  const items = Array.isArray(runbooks) ? runbooks : [];

  return (
    <div className="col-12">
      <div className="card">
        <div className="card-body">
          <h6 className="card-title">Runbooks</h6>
          {items.length === 0 ? (
            <p className="small text-muted mb-0">No runbooks available.</p>
          ) : (
            <div className="row g-3">
              {items.map((rb) => (
                <div className="col-md-4" key={rb.id || rb.title}>
                  <h6 className="small fw-semibold">{rb.title}</h6>
                  <ol className="small ps-3 mb-0">
                    {(Array.isArray(rb.checklist) ? rb.checklist : []).map((step) => (
                      <li key={step}>{step}</li>
                    ))}
                  </ol>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
