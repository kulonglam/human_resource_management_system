import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';

function defaultLabel(key) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function FormField({ field, value, onChange, options = {}, existingUrl }) {
  const { name, label, type = 'text', required, choices, step, accept } = field;
  const common = {
    name,
    className: 'form-control form-control-sm',
    value: type === 'file' ? undefined : (value ?? ''),
    onChange,
    required: type === 'file' ? required && !existingUrl : required,
  };

  if (type === 'file') {
    return (
      <div className="mb-3">
        <label className="form-label">{label || defaultLabel(name)}</label>
        {existingUrl && (
          <div className="mb-1">
            <a href={existingUrl} target="_blank" rel="noreferrer">View current file</a>
          </div>
        )}
        <input type="file" accept={accept} className="form-control form-control-sm" name={name} onChange={onChange} />
      </div>
    );
  }

  if (type === 'select') {
    const opts = choices || options[name] || [];
    return (
      <div className="mb-3">
        <label className="form-label">{label || defaultLabel(name)}</label>
        <select {...common} className="form-select form-select-sm">
          <option value="">Select...</option>
          {opts.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
    );
  }

  if (type === 'textarea') {
    return (
      <div className="mb-3">
        <label className="form-label">{label || defaultLabel(name)}</label>
        <textarea {...common} className="form-control form-control-sm" rows={3} />
      </div>
    );
  }

  return (
    <div className="mb-3">
      <label className="form-label">{label || defaultLabel(name)}</label>
      <input type={type} step={step} {...common} />
    </div>
  );
}

export default function ResourceManager({
  title,
  icon,
  tabs,
  lookupOptions = {},
}) {
  const [activeTab, setActiveTab] = useState(tabs[0]?.id);
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({});
  const [files, setFiles] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const tab = tabs.find((t) => t.id === activeTab) || tabs[0];

  const load = useCallback(async () => {
    if (!tab) return;
    setLoading(true);
    setError('');
    try {
      const data = await api.list(tab.endpoint, tab.query || '');
      setRows(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [tab]);

  useEffect(() => {
    load();
  }, [load]);

  const openCreate = () => {
    const initial = {};
    tab.formFields?.forEach((f) => {
      initial[f.name] = f.default ?? '';
    });
    setForm(initial);
    setFiles({});
    setEditing(null);
    setShowModal(true);
  };

  const openEdit = (row) => {
    const initial = {};
    tab.formFields?.forEach((f) => {
      if (f.type !== 'file') {
        initial[f.name] = row[f.name] ?? '';
      }
    });
    setForm(initial);
    setFiles({});
    setEditing(row);
    setShowModal(true);
  };

  const handleChange = (e) => {
    const { name, value, type, files: inputFiles } = e.target;
    if (type === 'file') {
      setFiles((prev) => ({ ...prev, [name]: inputFiles[0] || null }));
      return;
    }
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const buildPayload = () => {
    const hasFiles = tab.formFields?.some((f) => f.type === 'file' && files[f.name]);
    if (!hasFiles) {
      const payload = { ...form };
      tab.formFields?.forEach((f) => {
        if (f.type === 'number' && payload[f.name] !== '') {
          payload[f.name] = Number(payload[f.name]);
        }
        if (f.type === 'select' && payload[f.name] !== '') {
          payload[f.name] = /^\d+$/.test(String(payload[f.name]))
            ? Number(payload[f.name])
            : payload[f.name];
        }
      });
      return payload;
    }

    const formData = new FormData();
    tab.formFields?.forEach((f) => {
      if (f.type === 'file') {
        if (files[f.name]) formData.append(f.name, files[f.name]);
        return;
      }
      let val = form[f.name];
      if (f.type === 'number' && val !== '') val = Number(val);
      if (f.type === 'select' && val !== '' && /^\d+$/.test(String(val))) val = Number(val);
      if (val !== '' && val != null) formData.append(f.name, val);
    });
    return formData;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      const payload = buildPayload();
      if (editing) {
        await api.update(tab.endpoint, editing.id, payload);
      } else {
        await api.create(tab.endpoint, payload);
      }
      setShowModal(false);
      load();
    } catch (err) {
      const messages = Object.entries(err.data || {})
        .map(([field, msgs]) => `${field}: ${Array.isArray(msgs) ? msgs.join(', ') : msgs}`)
        .join(' ');
      setError(messages || err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (row) => {
    if (!window.confirm(`Delete this record?`)) return;
    try {
      await api.remove(tab.endpoint, row.id);
      load();
    } catch (err) {
      setError(err.data?.detail || err.message);
    }
  };

  const runAction = async (row, action) => {
    if (action.method === 'GET') {
      window.open(`/api/v1/${tab.endpoint}/${row.id}/${action.name}/`, '_blank');
      return;
    }
    try {
      await api.action(tab.endpoint, row.id, action.name, action.payload || {});
      load();
    } catch (err) {
      setError(err.data?.detail || err.message);
    }
  };

  const columns = tab.columns || (rows[0] ? Object.keys(rows[0]).slice(0, 6) : []);

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4 className="page-heading mb-0">
          {icon && <i className={`bi ${icon}`} style={{ color: 'var(--fca-lime)' }} />} {title}
        </h4>
        {tab.canCreate !== false && tab.formFields?.length > 0 && (
          <button type="button" className="btn btn-primary btn-sm" onClick={openCreate}>
            <i className="bi bi-plus-lg" /> Add
          </button>
        )}
      </div>

      {tabs.length > 1 && (
        <ul className="nav nav-tabs mb-3">
          {tabs.map((t) => (
            <li className="nav-item" key={t.id}>
              <button
                type="button"
                className={`nav-link ${activeTab === t.id ? 'active' : ''}`}
                onClick={() => setActiveTab(t.id)}
              >
                {t.label}
              </button>
            </li>
          ))}
        </ul>
      )}

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="card">
        <div className="card-body p-0">
          {loading ? (
            <div className="text-center py-4">
              <div className="spinner-border text-primary" role="status" />
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-hover mb-0 align-middle">
                <thead>
                  <tr>
                    {columns.map((col) => (
                      <th key={col.key || col}>{typeof col === 'string' ? defaultLabel(col) : col.label}</th>
                    ))}
                    {(tab.formFields?.length || tab.rowActions?.length || tab.detailPath) && <th>Actions</th>}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.id}>
                      {columns.map((col) => {
                        const key = col.key || col;
                        const val = col.render ? col.render(row) : row[key];
                        return <td key={key}>{val ?? '—'}</td>;
                      })}
                      {(tab.formFields?.length || tab.rowActions?.length || tab.detailPath) && (
                        <td className="text-nowrap">
                          {tab.detailPath && (
                            <Link
                              to={`${tab.detailPath}/${row.id}`}
                              className="btn btn-outline-secondary btn-sm me-1"
                            >
                              <i className="bi bi-eye" />
                            </Link>
                          )}
                          {tab.formFields?.length > 0 && (
                            <button
                              type="button"
                              className="btn btn-outline-primary btn-sm me-1"
                              onClick={() => openEdit(row)}
                            >
                              <i className="bi bi-pencil" />
                            </button>
                          )}
                          {tab.canDelete !== false && tab.formFields?.length > 0 && (
                            <button
                              type="button"
                              className="btn btn-outline-danger btn-sm me-1"
                              onClick={() => handleDelete(row)}
                            >
                              <i className="bi bi-trash" />
                            </button>
                          )}
                          {tab.rowActions?.map((action) =>
                            (!action.show || action.show(row)) ? (
                              <button
                                key={action.name}
                                type="button"
                                className={`btn btn-sm me-1 btn-${action.variant || 'outline-secondary'}`}
                                onClick={() => runAction(row, action)}
                              >
                                {action.label}
                              </button>
                            ) : null
                          )}
                        </td>
                      )}
                    </tr>
                  ))}
                  {!rows.length && (
                    <tr>
                      <td colSpan={columns.length + (tab.formFields?.length || tab.rowActions?.length || tab.detailPath ? 1 : 0)} className="text-center py-4 text-muted">
                        No records found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {showModal && (
        <>
          <div className="modal show d-block" tabIndex="-1">
            <div className="modal-dialog modal-lg">
              <div className="modal-content">
                <form onSubmit={handleSubmit}>
                  <div className="modal-header">
                    <h5 className="modal-title">{editing ? 'Edit' : 'Add'} {tab.label}</h5>
                    <button type="button" className="btn-close" onClick={() => setShowModal(false)} />
                  </div>
                  <div className="modal-body">
                    <div className="row">
                      {tab.formFields?.map((field) => (
                        <div className={field.fullWidth ? 'col-12' : 'col-md-6'} key={field.name}>
                          <FormField
                            field={field}
                            value={form[field.name]}
                            onChange={handleChange}
                            options={lookupOptions}
                            existingUrl={
                              field.type === 'file' && editing
                                ? editing[`${field.name}_url`] || editing[field.name]
                                : null
                            }
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="modal-footer">
                    <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                      Cancel
                    </button>
                    <button type="submit" className="btn btn-primary" disabled={submitting}>
                      {submitting ? 'Saving...' : 'Save'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
          <div className="modal-backdrop show" />
        </>
      )}
    </>
  );
}
