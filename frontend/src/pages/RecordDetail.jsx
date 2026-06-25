import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../api/client';
import { DETAIL_CONFIGS } from '../config/detailConfigs';

function FieldGrid({ fields, record }) {
  return (
    <dl className="row mb-0">
      {fields.map((field) => {
        const raw = record[field.key];
        const value = field.render ? field.render(raw, record) : (raw ?? '—');
        return (
          <div key={field.key} className={field.fullWidth ? 'col-12' : 'col-md-6'}>
            <dt className="text-muted small">{field.label}</dt>
            <dd className="mb-3">
              {value}{field.suffix && value !== '—' ? field.suffix : ''}
            </dd>
          </div>
        );
      })}
    </dl>
  );
}

export default function RecordDetail({ configKey }) {
  const { id } = useParams();
  const config = DETAIL_CONFIGS[configKey];
  const [record, setRecord] = useState(null);
  const [related, setRelated] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!config) return;
    setError('');
    api.get(config.endpoint, id)
      .then((data) => {
        setRecord(data);
        if (config.related) {
          const q = `${config.related.queryKey}=${id}`;
          return api.list(config.related.endpoint, q).then(setRelated);
        }
        return null;
      })
      .catch((err) => setError(err.message));
  }, [config, id]);

  if (!config) return <div className="alert alert-danger">Unknown detail type.</div>;
  if (error) return <div className="alert alert-danger">{error}</div>;
  if (!record) {
    return (
      <div className="text-center py-5">
        <div className="spinner-border text-primary" role="status" />
      </div>
    );
  }

  const title = record[config.titleKey] || 'Record Detail';
  const subtitle = config.subtitleKey ? record[config.subtitleKey] : null;

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h4 className="page-heading mb-1">{title}</h4>
          {subtitle && <p className="text-muted mb-0">{subtitle}</p>}
        </div>
        <Link to={config.backPath} className="btn btn-outline-secondary btn-sm">Back</Link>
      </div>

      {config.sections.map((section) => (
        <div className="card mb-3" key={section.title}>
          <div className="card-body">
            <h5 className="card-title">{section.title}</h5>
            <FieldGrid fields={section.fields} record={record} />
          </div>
        </div>
      ))}

      {config.related && (
        <div className="card">
          <div className="card-body p-0">
            <div className="card-body border-bottom">
              <h5 className="card-title mb-0">{config.related.title}</h5>
            </div>
            <div className="table-responsive">
              <table className="table table-hover mb-0">
                <thead>
                  <tr>
                    {config.related.columns.map((col) => (
                      <th key={col.key}>{col.label}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {related.map((row) => (
                    <tr key={row.id}>
                      {config.related.columns.map((col, colIdx) => (
                        <td key={col.key}>
                          {colIdx === 0 && config.related.detailPath ? (
                            <Link to={`${config.related.detailPath}/${row.id}`}>
                              {row[col.key] ?? '—'}
                            </Link>
                          ) : (
                            row[col.key] ?? '—'
                          )}
                        </td>
                      ))}
                    </tr>
                  ))}
                  {!related.length && (
                    <tr>
                      <td colSpan={config.related.columns.length} className="text-center py-4 text-muted">
                        No related records.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
