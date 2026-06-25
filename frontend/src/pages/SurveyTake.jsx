import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api } from '../api/client';

export default function SurveyTake() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [survey, setSurvey] = useState(null);
  const [answers, setAnswers] = useState({});
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api.get('surveys', id)
      .then((data) => {
        setSurvey(data);
        const initial = {};
        (data.questions || []).forEach((q) => {
          initial[q.id] = q.question_type === 'rating' ? 3 : '';
        });
        setAnswers(initial);
      })
      .catch((err) => setError(err.message));
  }, [id]);

  const setAnswer = (questionId, value) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      const payload = (survey.questions || []).map((q) => {
        const val = answers[q.id];
        const base = { question_id: q.id };
        if (q.question_type === 'rating') {
          return { ...base, response_rating: Number(val) };
        }
        if (q.question_type === 'text') {
          return { ...base, response_text: val || '' };
        }
        return { ...base, response_selected: val || '' };
      });
      await api.submitSurvey(id, payload);
      navigate('/surveys');
    } catch (err) {
      setError(err.data?.detail || err.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (error && !survey) return <div className="alert alert-danger">{error}</div>;
  if (!survey) {
    return (
      <div className="text-center py-5">
        <div className="spinner-border text-primary" role="status" />
      </div>
    );
  }

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4 className="page-heading mb-0">{survey.title}</h4>
        <Link to="/surveys" className="btn btn-outline-secondary btn-sm">Back</Link>
      </div>

      {survey.description && <p className="text-muted">{survey.description}</p>}
      {error && <div className="alert alert-danger">{error}</div>}

      <form className="card" onSubmit={handleSubmit}>
        <div className="card-body">
          {(survey.questions || []).map((q, idx) => (
            <div key={q.id} className="mb-4">
              <label className="form-label">
                {idx + 1}. {q.question_text}
                {q.is_required && <span className="text-danger"> *</span>}
              </label>

              {q.question_type === 'text' && (
                <textarea
                  className="form-control form-control-sm"
                  rows={3}
                  required={q.is_required}
                  value={answers[q.id] || ''}
                  onChange={(e) => setAnswer(q.id, e.target.value)}
                />
              )}

              {q.question_type === 'rating' && (
                <select
                  className="form-select form-select-sm"
                  required={q.is_required}
                  value={answers[q.id] || 3}
                  onChange={(e) => setAnswer(q.id, e.target.value)}
                >
                  {[1, 2, 3, 4, 5].map((n) => (
                    <option key={n} value={n}>{n}</option>
                  ))}
                </select>
              )}

              {(q.question_type === 'multiple_choice' || q.question_type === 'checkbox') && (
                <select
                  className="form-select form-select-sm"
                  required={q.is_required}
                  value={answers[q.id] || ''}
                  onChange={(e) => setAnswer(q.id, e.target.value)}
                >
                  <option value="">Select...</option>
                  {(q.options || '').split(',').map((opt) => opt.trim()).filter(Boolean).map((opt) => (
                    <option key={opt} value={opt}>{opt}</option>
                  ))}
                </select>
              )}
            </div>
          ))}

          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? 'Submitting...' : 'Submit Survey'}
          </button>
        </div>
      </form>
    </>
  );
}
