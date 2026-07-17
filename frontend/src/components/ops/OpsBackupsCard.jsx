export default function OpsBackupsCard({ ops }) {
  return (
    <div className="col-lg-4">
      <div className="card h-100">
        <div className="card-body">
          <h6 className="card-title">Recent backups</h6>
          {(ops?.backups || []).length === 0 ? (
            <p className="small text-muted mb-0">No local backups found.</p>
          ) : (
            <ul className="list-unstyled small mb-0">
              {ops.backups.slice(0, 5).map((b) => (
                <li key={b.name}>{b.name}</li>
              ))}
            </ul>
          )}
          <p className="small text-muted mt-2 mb-1">
            Retention: keep {ops?.backup_retention?.keep_count ?? 14} newest
            {ops?.backup_retention?.keep_days
              ? `, drop after ${ops.backup_retention.keep_days} days`
              : ''}
          </p>
          <p className="small text-muted mb-0">
            Restore: <code>python manage.py restore_database path --force</code>
          </p>
        </div>
      </div>
    </div>
  );
}
