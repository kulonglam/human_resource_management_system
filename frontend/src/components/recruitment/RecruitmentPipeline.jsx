import { useCallback, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../api/client';

const DEFAULT_COLUMNS = [
  { key: 'received', label: 'Received', icon: 'bi-inbox' },
  { key: 'shortlisted', label: 'Shortlisted', icon: 'bi-star' },
  { key: 'interviewed', label: 'Interviewed', icon: 'bi-person-video2' },
  { key: 'offer', label: 'Offer', icon: 'bi-envelope-paper' },
  { key: 'hired', label: 'Hired', icon: 'bi-check-circle' },
];

const ICONS = {
  received: 'bi-inbox',
  shortlisted: 'bi-star',
  interviewed: 'bi-person-video2',
  offer: 'bi-envelope-paper',
  hired: 'bi-check-circle',
};

function daysSince(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime();
  return Math.max(0, Math.floor(diff / (1000 * 60 * 60 * 24)));
}

function PipelineCard({ item, onDragStart }) {
  return (
    <div className="recruitment-card" draggable onDragStart={(e) => onDragStart(e, item)}>
      <Link to={`/recruitment/applications/${item.id}`} className="recruitment-card-name">{item.full_name}</Link>
      <div className="recruitment-card-job">{item.job_title}</div>
      <div className="recruitment-card-badges">
        {item.source && item.source !== 'manual' && (
          <span className="badge bg-light text-dark border">{item.source.replace(/_/g, ' ')}</span>
        )}
        {item.rating > 0 && (
          <span className="recruitment-card-rating">
            {[1, 2, 3, 4, 5].map((s) => (
              <i key={s} className={`bi bi-star${s <= item.rating ? '-fill' : ''}`} />
            ))}
          </span>
        )}
      </div>
      <div className="recruitment-card-meta">
        <span>{daysSince(item.applied_on)}d in pipeline</span>
        <span>{item.email}</span>
      </div>
    </div>
  );
}

export default function RecruitmentPipeline({ pipeline, pipelineStages, onRefresh, canManage }) {
  const [dragItem, setDragItem] = useState(null);
  const [busyId, setBusyId] = useState(null);
  const [error, setError] = useState('');

  const columns = (pipelineStages?.length ? pipelineStages : DEFAULT_COLUMNS)
    .filter((s) => s.stage_type !== 'rejected')
    .map((s) => ({
      key: s.key,
      id: s.id,
      label: s.label,
      stage_type: s.stage_type || 'active',
      icon: ICONS[s.key] || 'bi-circle',
    }));

  const byColumn = columns.reduce((acc, col) => {
    acc[col.key] = pipeline.filter((item) => (item.stage_key || item.status) === col.key);
    return acc;
  }, {});

  const rejected = pipeline.filter((item) => item.status === 'rejected' || item.stage_key === 'rejected');

  const handleDragStart = (e, item) => {
    if (!canManage) {
      e.preventDefault();
      return;
    }
    setDragItem(item);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDrop = async (col) => {
    if (!dragItem || !canManage) return;
    const fromKey = dragItem.stage_key || dragItem.status;
    if (fromKey === col.key) {
      setDragItem(null);
      return;
    }

    setError('');
    setBusyId(dragItem.id);
    try {
      if (col.stage_type === 'hired' || col.key === 'hired') {
        await api.action('applications', dragItem.id, 'approve', {});
      } else if (col.key === 'rejected') {
        await api.action('applications', dragItem.id, 'reject', {});
      } else if (col.id) {
        await api.moveApplicationStage(dragItem.id, col.id);
      } else {
        await api.update('applications', dragItem.id, { status: col.key });
      }
      onRefresh();
    } catch (err) {
      setError(err.data?.detail || err.message);
    } finally {
      setBusyId(null);
      setDragItem(null);
    }
  };

  const allowDrop = useCallback((e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  }, []);

  return (
    <div className="recruitment-pipeline">
      {error && <div className="alert alert-danger py-2">{error}</div>}
      {!canManage && (
        <div className="alert alert-light border small mb-3">
          Pipeline is read-only. Filter by job to use configurable stages. Managers can drag cards to update status.
        </div>
      )}
      <div className="recruitment-board" style={{ gridTemplateColumns: `repeat(${Math.min(columns.length, 5)}, minmax(200px, 1fr))` }}>
        {columns.map((col) => (
          <div
            key={col.key}
            className={`recruitment-column ${dragItem ? 'recruitment-column-drop' : ''}`}
            onDragOver={allowDrop}
            onDrop={() => handleDrop(col)}
          >
            <div className="recruitment-column-header">
              <i className={`bi ${col.icon}`} />
              <span>{col.label}</span>
              <span className="badge bg-secondary">{byColumn[col.key]?.length || 0}</span>
            </div>
            <div className="recruitment-column-body">
              {byColumn[col.key]?.map((item) => (
                <PipelineCard key={item.id} item={item} onDragStart={handleDragStart} />
              ))}
              {!byColumn[col.key]?.length && <div className="recruitment-column-empty">No candidates</div>}
            </div>
          </div>
        ))}
      </div>

      {rejected.length > 0 && (
        <div className="card mt-3">
          <div className="card-body">
            <h6 className="card-title mb-3"><i className="bi bi-x-circle text-danger me-1" />Rejected ({rejected.length})</h6>
            <div className="table-responsive">
              <table className="table table-sm mb-0">
                <thead><tr><th>Applicant</th><th>Job</th><th>Applied</th><th /></tr></thead>
                <tbody>
                  {rejected.map((item) => (
                    <tr key={item.id}>
                      <td>{item.full_name}</td>
                      <td>{item.job_title}</td>
                      <td>{new Date(item.applied_on).toLocaleDateString()}</td>
                      <td className="text-end">
                        <Link to={`/recruitment/applications/${item.id}`} className="btn btn-outline-secondary btn-sm">View</Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export function RecruitmentMetrics({ summary }) {
  if (!summary) return null;
  const { by_status: byStatus } = summary;
  const tiles = [
    { label: 'Open roles', value: summary.open_jobs, icon: 'bi-briefcase' },
    { label: 'Total applications', value: summary.total_applications, icon: 'bi-people' },
    { label: 'Awaiting review', value: summary.pending_review, icon: 'bi-inbox' },
    { label: 'In interview', value: byStatus?.interviewed ?? 0, icon: 'bi-person-video2' },
    { label: 'Avg. days in pipeline', value: summary.avg_days_in_pipeline, icon: 'bi-clock-history' },
  ];
  return (
    <div className="recruitment-metrics">
      {tiles.map((tile) => (
        <div className="recruitment-metric" key={tile.label}>
          <i className={`bi ${tile.icon}`} />
          <div>
            <div className="recruitment-metric-value">{tile.value}</div>
            <div className="recruitment-metric-label">{tile.label}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
