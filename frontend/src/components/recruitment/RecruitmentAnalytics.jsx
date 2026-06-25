export default function RecruitmentAnalytics({ summary }) {
  if (!summary?.funnel?.length) return null;

  const maxCount = Math.max(...summary.funnel.map((s) => s.count), 1);

  return (
    <div className="recruitment-analytics card mb-4">
      <div className="card-body">
        <div className="d-flex justify-content-between align-items-start flex-wrap gap-2 mb-3">
          <div>
            <h5 className="mb-1">Hiring funnel</h5>
            <p className="text-muted small mb-0">
              {summary.avg_time_to_hire > 0
                ? `Avg. time to hire: ${summary.avg_time_to_hire} days`
                : 'Time-to-hire appears once candidates are hired'}
            </p>
          </div>
          {summary.by_source && Object.keys(summary.by_source).length > 0 && (
            <div className="recruitment-sources">
              {Object.entries(summary.by_source).map(([key, count]) => (
                <span key={key} className="badge bg-light text-dark border me-1 mb-1">
                  {key.replace(/_/g, ' ')}: {count}
                </span>
              ))}
            </div>
          )}
        </div>
        <div className="recruitment-funnel-stages">
          {summary.funnel.map((stage) => (
            <div className="recruitment-funnel-stage" key={stage.key}>
              <div className="recruitment-funnel-stage-head">
                <span>{stage.label}</span>
                <strong>{stage.count}</strong>
              </div>
              <div className="recruitment-funnel-bar-track">
                <div
                  className="recruitment-funnel-bar-fill"
                  style={{ width: `${Math.max(8, (stage.count / maxCount) * 100)}%` }}
                />
              </div>
              {stage.conversion_pct > 0 && stage.key !== 'received' && (
                <div className="recruitment-funnel-conversion">{stage.conversion_pct}% conversion</div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
