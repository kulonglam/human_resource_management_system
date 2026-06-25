import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';

function OrgNode({ node, depth = 0 }) {
  return (
    <div className={`org-node ms-${Math.min(depth * 3, 5)}`}>
      <div className="card mb-2 border-start border-3 border-success">
        <div className="card-body py-2 px-3">
          <div className="fw-semibold">{node.name}</div>
          <div className="small text-muted">
            {node.location} · {node.employee_count} employee{node.employee_count === 1 ? '' : 's'}
          </div>
          {node.manager_name && (
            <div className="small">Manager: {node.manager_name}</div>
          )}
        </div>
      </div>
      {node.children?.map((child) => (
        <OrgNode key={child.id} node={child} depth={depth + 1} />
      ))}
    </div>
  );
}

export default function OrgChart() {
  const [chart, setChart] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getOrgChart()
      .then(setChart)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4 className="page-heading mb-0">
          <i className="bi bi-diagram-3" style={{ color: 'var(--fca-lime)' }} /> Organization Chart
        </h4>
        <Link to="/departments" className="btn btn-outline-primary btn-sm">Manage Departments</Link>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {loading ? (
        <div className="text-center py-5"><div className="spinner-border text-primary" role="status" /></div>
      ) : (
        <>
          <div className="row mb-3">
            <div className="col-md-4">
              <div className="card stat-card stat-card--green text-white">
                <div className="card-body">
                  <h6>Departments</h6>
                  <p className="fs-4 mb-0">{chart?.total_departments ?? 0}</p>
                </div>
              </div>
            </div>
            <div className="col-md-4">
              <div className="card stat-card stat-card--red text-white">
                <div className="card-body">
                  <h6>Unassigned employees</h6>
                  <p className="fs-4 mb-0">{chart?.unassigned_employees ?? 0}</p>
                </div>
              </div>
            </div>
          </div>

          {chart?.roots?.length ? (
            chart.roots.map((root) => <OrgNode key={root.id} node={root} />)
          ) : (
            <p className="text-muted">No departments configured yet.</p>
          )}
        </>
      )}
    </>
  );
}
