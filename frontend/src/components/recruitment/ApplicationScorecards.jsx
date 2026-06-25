import { useCallback, useEffect, useState } from 'react';
import { api } from '../../api/client';
import { useAuth } from '../../context/AuthContext';

const RECOMMENDATIONS = [
  { value: 'strong_yes', label: 'Strong Yes' },
  { value: 'yes', label: 'Yes' },
  { value: 'neutral', label: 'Neutral' },
  { value: 'no', label: 'No' },
  { value: 'strong_no', label: 'Strong No' },
];

export default function ApplicationScorecards({ applicationId, jobId }) {
  const { user } = useAuth();
  const [scorecards, setScorecards] = useState([]);
  const [criteria, setCriteria] = useState([]);
  const [form, setForm] = useState({ overall_recommendation: 'yes', summary: '', ratings: {} });
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const [sc, crit] = await Promise.all([
      api.list('scorecards', `application=${applicationId}`),
      api.list('scorecard-criteria', `job=${jobId}`),
    ]);
    setScorecards(sc);
    setCriteria(crit);
    const ratings = {};
    crit.forEach((c) => { ratings[c.id] = 3; });
    setForm((f) => ({ ...f, ratings }));
  }, [applicationId, jobId]);

  useEffect(() => {
    load();
  }, [load]);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.create('scorecards', {
        application: Number(applicationId),
        overall_recommendation: form.overall_recommendation,
        summary: form.summary,
        ratings: criteria.map((c) => ({
          criterion: c.id,
          score: Number(form.ratings[c.id] || 3),
          comment: '',
        })),
      });
      load();
    } finally {
      setBusy(false);
    }
  };

  const mine = scorecards.find((s) => s.reviewer === user?.id);

  return (
    <div className="card mb-3">
      <div className="card-body">
        <h5 className="card-title">Interview scorecards</h5>
        {scorecards.map((sc) => (
          <div className="recruitment-scorecard-review mb-3" key={sc.id}>
            <div className="d-flex justify-content-between">
              <strong>{sc.reviewer_name}</strong>
              <span className="badge bg-info">{sc.recommendation_display}</span>
            </div>
            {sc.summary && <p className="small mb-1">{sc.summary}</p>}
            <ul className="small mb-0">
              {sc.ratings?.map((r) => (
                <li key={r.id}>{r.criterion_name}: {r.score}/5</li>
              ))}
            </ul>
          </div>
        ))}
        {!mine && criteria.length > 0 && (
          <form onSubmit={submit} className="border-top pt-3">
            <p className="small text-muted">Submit your evaluation</p>
            {criteria.map((c) => (
              <div className="mb-2" key={c.id}>
                <label className="form-label small mb-0">{c.name}</label>
                <input type="range" min={1} max={5} className="form-range" value={form.ratings[c.id] || 3} onChange={(e) => setForm({ ...form, ratings: { ...form.ratings, [c.id]: e.target.value } })} />
              </div>
            ))}
            <select className="form-select form-select-sm mb-2" value={form.overall_recommendation} onChange={(e) => setForm({ ...form, overall_recommendation: e.target.value })}>
              {RECOMMENDATIONS.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
            </select>
            <textarea className="form-control form-control-sm mb-2" rows={2} placeholder="Summary" value={form.summary} onChange={(e) => setForm({ ...form, summary: e.target.value })} />
            <button type="submit" className="btn btn-primary btn-sm" disabled={busy}>Submit scorecard</button>
          </form>
        )}
        {!criteria.length && <p className="text-muted small mb-0">Define scorecard criteria in job enterprise setup.</p>}
      </div>
    </div>
  );
}
