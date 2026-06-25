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

export default function Documents() {
  const { user } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [category, setCategory] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [form, setForm] = useState({ title: '', category: 'policy', description: '', file: null });

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
      await api.createForm('documents', payload);
      setForm({ title: '', category: 'policy', description: '', file: null });
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
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
                    <th>Version</th>
                    <th>Uploaded</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {documents.map((doc) => (
                    <tr key={doc.id}>
                      <td>{doc.title}</td>
                      <td>{doc.category_display}</td>
                      <td>{doc.employee_name || 'Company-wide'}</td>
                      <td>v{doc.version}</td>
                      <td>{new Date(doc.created_at).toLocaleDateString()}</td>
                      <td>
                        {doc.file_url && (
                          <a href={doc.file_url} className="btn btn-sm btn-outline-primary" target="_blank" rel="noreferrer">
                            Download
                          </a>
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
