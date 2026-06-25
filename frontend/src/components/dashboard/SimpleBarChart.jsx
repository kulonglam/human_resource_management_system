export default function SimpleBarChart({ chart }) {
  if (!chart?.points?.length) {
    return (
      <div className="dashboard-empty-chart text-muted text-center py-5">
        <i className="bi bi-bar-chart-line fs-2 d-block mb-2" />
        No chart data available yet.
      </div>
    );
  }

  const maxValue = Math.max(
    ...chart.points.map((p) => Math.max(p.value, p.max || 0)),
    1,
  );

  return (
    <div className="dashboard-chart">
      <div className="dashboard-chart-header mb-3">
        <h5 className="mb-1">{chart.title}</h5>
        {chart.subtitle && <p className="text-muted small mb-0">{chart.subtitle}</p>}
      </div>

      <div className="dashboard-chart-bars">
        {chart.points.map((point) => {
          const barMax = point.max || maxValue;
          const heightPct = barMax ? Math.max(8, (point.value / barMax) * 100) : 8;
          return (
            <div className="dashboard-chart-bar-col" key={point.label}>
              <div className="dashboard-chart-bar-track">
                <div
                  className="dashboard-chart-bar-fill"
                  style={{ height: `${heightPct}%` }}
                  title={`${point.label}: ${point.value}`}
                />
              </div>
              <div className="dashboard-chart-bar-value">{point.value}</div>
              <div className="dashboard-chart-bar-label">{point.label}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
