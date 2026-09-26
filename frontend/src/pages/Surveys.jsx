import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import ResourceManager from '../components/ResourceManager';
import { useAuth } from '../context/AuthContext';
import { surveyManageTabs, surveyQuestionTab } from '../config/opsModules';
import { canManageHr } from '../utils/permissions';

export default function Surveys() {
  const { user } = useAuth();
  const canManage = canManageHr(user);
  const [section, setSection] = useState(canManage ? 'manage' : 'take');
  const [lookupOptions, setLookupOptions] = useState({});
  const [available, setAvailable] = useState([]);
  const [questionSurveyFilter, setQuestionSurveyFilter] = useState('');
  const [resultsSurvey, setResultsSurvey] = useState('');
  const [resultsData, setResultsData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      try {
        const surveys = await api.list('surveys');
        setLookupOptions({
          survey: surveys.map((s) => ({ value: s.id, label: s.title })),
        });
        setAvailable(await api.getAvailableSurveys());
      } catch {
        /* optional */
      }
    }
    load();
  }, []);

  const loadResults = async () => {
    if (!resultsSurvey) return;
    setLoading(true);
    setError('');
    try {
      setResultsData(await api.getSurveyResults(resultsSurvey));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const questionTab = {
    ...surveyQuestionTab,
    query: questionSurveyFilter ? `survey=${questionSurveyFilter}` : '',
    canCreate: Boolean(questionSurveyFilter),
  };

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4 className="page-heading mb-0">
          <i className="bi bi-clipboard-data" style={{ color: 'var(--fca-lime)' }} /> Surveys
        </h4>
      </div>

      <ul className="nav nav-tabs mb-3">
        {[
          canManage && { id: 'manage', label: 'Manage Surveys' },
          canManage && { id: 'questions', label: 'Questions' },
          { id: 'take', label: 'Take Survey' },
          canManage && { id: 'results', label: 'Results' },
        ].filter(Boolean).map((tab) => (
          <li className="nav-item" key={tab.id}>
            <button
              type="button"
              className={`nav-link ${section === tab.id ? 'active' : ''}`}
              onClick={() => setSection(tab.id)}
            >
              {tab.label}
            </button>
          </li>
        ))}
      </ul>

      {error && <div className="alert alert-danger">{error}</div>}

      {canManage && section === 'manage' && (
        <ResourceManager title="" icon="" tabs={surveyManageTabs} lookupOptions={lookupOptions} />
      )}

      {canManage && section === 'questions' && (
        <>
          <div className="row mb-3">
            <div className="col-md-4">
              <label className="form-label">Filter by Survey</label>
              <select
                className="form-select form-select-sm"
                value={questionSurveyFilter}
                onChange={(e) => setQuestionSurveyFilter(e.target.value)}
              >
                <option value="">All surveys</option>
                {(lookupOptions.survey || []).map((s) => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
            </div>
          </div>
          <ResourceManager
            key={questionSurveyFilter}
            title=""
            tabs={[questionTab]}
            lookupOptions={lookupOptions}
          />
        </>
      )}

      {section === 'take' && (
        <div className="card">
          <div className="card-body">
            <h5 className="card-title">Available Surveys</h5>
            {!available.length ? (
              <p className="text-muted mb-0">No active surveys at this time.</p>
            ) : (
              <ul className="list-group list-group-flush">
                {available.map((survey) => (
                  <li key={survey.id} className="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                      <strong>{survey.title}</strong>
                      <div className="small text-muted">
                        {survey.start_date} — {survey.end_date}
                      </div>
                    </div>
                    <Link to={`/surveys/${survey.id}/take`} className="btn btn-primary btn-sm">
                      Take Survey
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}

      {canManage && section === 'results' && (
        <>
          <div className="row g-2 mb-3 align-items-end">
            <div className="col-md-4">
              <label className="form-label">Survey</label>
              <select
                className="form-select form-select-sm"
                value={resultsSurvey}
                onChange={(e) => setResultsSurvey(e.target.value)}
              >
                <option value="">Select survey...</option>
                {(lookupOptions.survey || []).map((s) => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
            </div>
            <div className="col-md-2">
              <button type="button" className="btn btn-primary btn-sm w-100" onClick={loadResults} disabled={!resultsSurvey || loading}>
                {loading ? 'Loading...' : 'Load Results'}
              </button>
            </div>
          </div>
          {resultsData && (
            <div className="card">
              <div className="card-body">
                <h5>{resultsData.survey.title}</h5>
                <p className="text-muted">{resultsData.total_responders} respondent(s)</p>
                {resultsData.questions.map((q) => (
                  <div key={q.question_id} className="mb-4 border-bottom pb-3">
                    <h6>{q.question_text}</h6>
                    <p className="small text-muted">{q.total_responses} response(s)</p>
                    {q.question_type === 'rating' && (
                      <p>Average rating: <strong>{q.average_rating}</strong> / 5</p>
                    )}
                    {q.text_responses?.length > 0 && (
                      <ul className="small mb-0">
                        {q.text_responses.map((t, i) => <li key={i}>{t || '—'}</li>)}
                      </ul>
                    )}
                    {q.selected_responses?.length > 0 && (
                      <ul className="small mb-0">
                        {q.selected_responses.map((t, i) => <li key={i}>{t || '—'}</li>)}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </>
  );
}
