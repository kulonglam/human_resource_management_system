export default function OpsJobsCard({ ops }) {
  return (
    <div className="col-lg-4">
      <div className="card h-100">
        <div className="card-body">
          <h6 className="card-title">Queue / jobs</h6>
          <ul className="list-unstyled small mb-0">
            <li>Scheduled: {ops?.jobs?.scheduled ?? 0}</li>
            <li>Success: {ops?.jobs?.success ?? 0}</li>
            <li>Failed: {ops?.jobs?.failed ?? 0}</li>
            <li>Queued: {ops?.jobs?.queued ?? 0}</li>
          </ul>
          <p className="small text-muted mt-3 mb-0">{ops?.worker_hint}</p>
        </div>
      </div>
    </div>
  );
}
