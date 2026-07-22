import { Link } from 'react-router-dom';

export default function SettingsBackLink() {
  return (
    <div className="mb-3">
      <Link to="/settings" className="text-decoration-none">
        <i className="bi bi-arrow-left me-1" aria-hidden="true" />
        Back to Settings
      </Link>
    </div>
  );
}
