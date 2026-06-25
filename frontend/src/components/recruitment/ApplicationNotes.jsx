import { useCallback, useEffect, useState } from 'react';
import { api } from '../../api/client';

export default function ApplicationNotes({ applicationId, canManage }) {
  const [notes, setNotes] = useState([]);
  const [body, setBody] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.list('application-notes', `application=${applicationId}`);
      setNotes(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [applicationId]);

  useEffect(() => {
    load();
  }, [load]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!body.trim()) return;
    setSubmitting(true);
    setError('');
    try {
      await api.create('application-notes', { application: Number(applicationId), body: body.trim() });
      setBody('');
      load();
    } catch (err) {
      setError(err.data?.detail || err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="card mb-3">
      <div className="card-body">
        <h5 className="card-title">Recruiter notes</h5>
        {loading ? (
          <div className="spinner-border spinner-border-sm text-primary" role="status" />
        ) : (
          <>
            {notes.length === 0 && <p className="text-muted small">No notes yet.</p>}
            <div className="recruitment-notes-list mb-3">
              {notes.map((note) => (
                <div className="recruitment-note" key={note.id}>
                  <div className="recruitment-note-meta">
                    <strong>{note.author_name || 'Team'}</strong>
                    <span>{new Date(note.created_at).toLocaleString()}</span>
                  </div>
                  <p className="mb-0 text-pre-wrap">{note.body}</p>
                </div>
              ))}
            </div>
            {canManage && (
              <form onSubmit={handleSubmit}>
                {error && <div className="alert alert-danger py-2 small">{error}</div>}
                <textarea
                  className="form-control form-control-sm mb-2"
                  rows={3}
                  placeholder="Add a private note for the hiring team..."
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                />
                <button type="submit" className="btn btn-primary btn-sm" disabled={submitting || !body.trim()}>
                  {submitting ? 'Saving...' : 'Add note'}
                </button>
              </form>
            )}
          </>
        )}
      </div>
    </div>
  );
}
