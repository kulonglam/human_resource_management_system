import { useEffect, useState } from 'react';
import { api } from '../../api/client';

export default function RecruitmentCompliance() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getRecruitmentEEOReport()
      .then(setReport)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="spinner-border spinner-border-sm text-primary" role="status" />;
  }

  if (!report) return null;

  const sections = [
    { key: 'gender', title: 'Gender' },
    { key: 'ethnicity', title: 'Ethnicity' },
    { key: 'veteran_status', title: 'Veteran status' },
    { key: 'disability_status', title: 'Disability status' },
  ];

  return (
    <div className="card mb-4">
      <div className="card-body">
        <h5 className="card-title">EEO compliance report</h5>
        <p className="small text-muted">{report.disclaimer}</p>
        <p className="mb-3"><strong>{report.total_with_eeo_data}</strong> applications with voluntary EEO data</p>
        <div className="row g-3">
          {sections.map(({ key, title }) => (
            <div className="col-md-6" key={key}>
              <h6 className="small text-uppercase text-muted">{title}</h6>
              <ul className="list-group list-group-flush small">
                {(report[key] || []).map((row) => (
                  <li className="list-group-item d-flex justify-content-between px-0" key={row[key] || 'blank'}>
                    <span>{row[key] || 'Not specified'}</span>
                    <strong>{row.count}</strong>
                  </li>
                ))}
                {!report[key]?.length && <li className="list-group-item px-0 text-muted">No data</li>}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
