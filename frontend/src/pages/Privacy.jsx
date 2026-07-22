import { Link } from 'react-router-dom';
import PublicFooter from '../components/PublicFooter';

export default function Privacy() {
  return (
    <div className="public-legal-page">
      <header className="public-legal-header">
        <div className="public-legal-header-inner">
          <Link to="/login" className="public-legal-brand">
            FCA HRMIS
          </Link>
          <Link to="/login" className="btn btn-outline-light btn-sm">Sign in</Link>
        </div>
      </header>

      <main className="public-legal-main">
        <p className="page-eyebrow">Legal</p>
        <h1 className="page-heading">Privacy notice</h1>
        <p className="page-subheading mb-4">
          How this single-organization HRMIS handles workforce personal data.
        </p>

        <div className="surface-card public-legal-body">
          <h2 className="h5 text-primary">Who this applies to</h2>
          <p>
            FCA HRMIS is operated for one employer. It processes personal data of employees,
            managers, administrators, and job applicants as needed to run HR operations.
          </p>

          <h2 className="h5 text-primary">Data we process</h2>
          <p>
            Depending on your role, this may include identity and contact details, employment
            records, attendance and leave, payroll and statutory fields, recruitment materials,
            performance and training records, and security logs (for example sign-in and audit
            events).
          </p>

          <h2 className="h5 text-primary">Why we process it</h2>
          <p>
            Data is used to manage employment, pay, leave, compliance, access control, and
            related workforce administration. Processing is limited to what the organization
            needs to operate the system securely and lawfully.
          </p>

          <h2 className="h5 text-primary">Access and retention</h2>
          <p>
            Access is role-based. Sensitive fields may be masked or logged when viewed.
            Retention and erasure follow organization policies configured in Compliance settings
            (where enabled).
          </p>

          <h2 className="h5 text-primary">Your requests</h2>
          <p>
            Employees can use in-app privacy tools where available (for example personal data
            export under Settings → Security). For other privacy questions, contact your HR
            administrator or{' '}
            <a href="mailto:hr@hrmis.local?subject=Privacy%20request">hr@hrmis.local</a>.
          </p>

          <p className="text-muted small mb-0">
            This notice is an application summary, not legal advice. Your organization may publish
            a fuller policy.
          </p>
        </div>
      </main>

      <PublicFooter />
    </div>
  );
}
