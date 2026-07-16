import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

const CATEGORIES = [
  { value: '', label: 'All categories' },
  { value: 'contract', label: 'Employment Contract' },
  { value: 'policy', label: 'HR Policy' },
  { value: 'offer_letter', label: 'Offer Letter' },
  { value: 'certificate', label: 'Certificate' },
  { value: 'other', label: 'Other' },
];

function formatDate(value) {
  if (!value) return '—';
  return new Date(`${value}T00:00:00`).toLocaleDateString('en-UG');
}

export default function Documents() {
  const { user } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [category, setCategory] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [form, setForm] = useState({
    title: '', category: 'policy', description: '', file: null,
    requires_acknowledgement: false, expires_at: '', legal_hold: false,
  });

  const canUpload = user?.is_admin || user?.is_manager;

  const load = async () => {
    setLoading(true);
    try {
      const q = category ? `category=${category}` : '';
      setDocuments(await api.list('documents', q));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [category]);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!form.file) return;
    setUploading(true);
    setError('');
    try {
      const payload = new FormData();
      payload.append('title', form.title);
      payload.append('category', form.category);
      payload.append('description', form.description);
      payload.append('file', form.file);
      payload.append('requires_acknowledgement', form.requires_acknowledgement ? 'true' : 'false');
      if (form.expires_at) payload.append('expires_at', form.expires_at);
      if (canUpload) payload.append('legal_hold', form.legal_hold ? 'true' : 'false');
      await api.createForm('documents', payload);
      setForm({
        title: '', category: 'policy', description: '', file: null,
        requires_acknowledgement: false, expires_at: '', legal_hold: false,
      });
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleAcknowledge = async (docId) => {
    setError('');
    try {
      await api.acknowledgeDocument(docId);
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <>
      <h4 className="page-heading mb-4">
        <i className="bi bi-folder2-open" style={{ color: 'var(--fca-lime)' }} /> Documents
      </h4>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="row g-3 mb-4">
        <div className="col-md-4">
          <label className="form-label">Filter by category</label>
          <select className="form-select" value={category} onChange={(e) => setCategory(e.target.value)}>
            {CATEGORIES.map((c) => (
              <option key={c.value || 'all'} value={c.value}>{c.label}</option>
            ))}
          </select>
        </div>
      </div>

      {canUpload && (
        <div className="card mb-4">
          <div className="card-body">
            <h6 className="card-title">Upload document</h6>
            <form onSubmit={handleUpload} className="row g-2">
              <div className="col-md-4">
                <input className="form-control" placeholder="Title" required value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })} />
              </div>
              <div className="col-md-3">
                <select className="form-select" value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}>
                  {CATEGORIES.filter((c) => c.value).map((c) => (
                    <option key={c.value} value={c.value}>{c.label}</option>
                  ))}
                </select>
              </div>
              <div className="col-md-3">
                <input type="file" className="form-control" required
                  onChange={(e) => setForm({ ...form, file: e.target.files?.[0] || null })} />
              </div>
              <div className="col-md-2">
                <button type="submit" className="btn btn-primary w-100" disabled={uploading}>
                  {uploading ? 'Uploading...' : 'Upload'}
                </button>
              </div>
              <div className="col-md-3">
                <input type="date" className="form-control" value={form.expires_at}
                  onChange={(e) => setForm({ ...form, expires_at: e.target.value })} />
                <small className="text-muted">Expiry date (optional)</small>
              </div>
              <div className="col-md-3 d-flex align-items-center">
                <div className="form-check">
                  <input className="form-check-input" type="checkbox" id="requires-ack"
                    checked={form.requires_acknowledgement}
                    onChange={(e) => setForm({ ...form, requires_acknowledgement: e.target.checked })} />
                  <label className="form-check-label" htmlFor="requires-ack">Requires acknowledgement</label>
                </div>
              </div>
              {canUpload && (
                <div className="col-md-3 d-flex align-items-center">
                  <div className="form-check">
                    <input className="form-check-input" type="checkbox" id="legal-hold"
                      checked={form.legal_hold}
                      onChange={(e) => setForm({ ...form, legal_hold: e.target.checked })} />
                    <label className="form-check-label" htmlFor="legal-hold">Legal hold</label>
                  </div>
                </div>
              )}
              <div className="col-12">
                <input className="form-control" placeholder="Description (optional)" value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })} />
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-body">
          {loading ? (
            <div className="text-center py-4"><div className="spinner-border text-primary" role="status" /></div>
          ) : documents.length === 0 ? (
            <p className="text-muted mb-0">No documents found.</p>
          ) : (
            <div className="table-responsive">
              <table className="table table-hover align-middle">
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Category</th>
                    <th>Employee</th>
                    <th>Expires</th>
                    <th>Acknowledgement</th>
                    <th>Uploaded</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {documents.map((doc) => (
                    <tr key={doc.id}>
                      <td>{doc.title}{doc.legal_hold ? ' (Legal hold)' : ''}</td>
                      <td>{doc.category_display}</td>
                      <td>{doc.employee_name || 'Company-wide'}</td>
                      <td>{formatDate(doc.expires_at)}</td>
                      <td>
                        {doc.requires_acknowledgement
                          ? (doc.acknowledged ? 'Acknowledged' : 'Pending')
                          : '—'}
                      </td>
                      <td>{new Date(doc.created_at).toLocaleDateString()}</td>
                      <td className="text-nowrap">
                        {doc.file_url && (
                          <a href={doc.file_url} className="btn btn-sm btn-outline-primary me-1" target="_blank" rel="noreferrer">
                            Download
                          </a>
                        )}
                        {doc.requires_acknowledgement && !doc.acknowledged && (
                          <button type="button" className="btn btn-sm btn-success" onClick={() => handleAcknowledge(doc.id)}>
                            Acknowledge
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
