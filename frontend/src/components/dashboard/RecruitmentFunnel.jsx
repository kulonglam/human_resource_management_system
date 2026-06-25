import { Link } from 'react-router-dom';

export default function RecruitmentFunnel({ funnel }) {
  if (!funnel?.stages?.length) return null;

  const maxCount = Math.max(...funnel.stages.map((s) => s.count), 1);

  return (
    <div className="dashboard-funnel">
      <div className="dashboard-panel-header">
        <div>
          <h5 className="mb-1">{funnel.title}</h5>
          <p className="text-muted small mb-0">
            {funnel.total_applications} applications · {funnel.open_positions} open roles
          </p>
        </div>
        <Link to="/recruitment" className="small">View pipeline</Link>
      </div>
      <div className="dashboard-funnel-stages">
        {funnel.stages.map((stage) => (
          <div className="dashboard-funnel-stage" key={stage.key}>
            <div className="dashboard-funnel-stage-head">
              <span>{stage.label}</span>
              <strong>{stage.count}</strong>
            </div>
            <div className="dashboard-funnel-bar-track">
              <div
                className="dashboard-funnel-bar-fill"
                style={{ width: `${Math.max(6, (stage.count / maxCount) * 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
