import { Link } from 'react-router-dom';

const YEAR = new Date().getFullYear();

/**
 * Minimal footer for public surfaces only (auth, careers, privacy).
 * Not used inside the authenticated app shell.
 */
export default function PublicFooter({ tone = 'light', showLoginLink = true }) {
  return (
    <footer className={`public-footer public-footer--${tone}`} role="contentinfo">
      <div className="public-footer-inner">
        <p className="public-footer-copy mb-0">
          © {YEAR}  HRMIS
        </p>
        <nav className="public-footer-nav" aria-label="Legal and support">
          <Link to="/privacy">Privacy</Link>
          <a href="mailto:hr@hrmis.local?subject=FCA%20HRMIS%20support">Support</a>
          {showLoginLink && <Link to="/login">Employee login</Link>}
        </nav>
      </div>
    </footer>
  );
}
