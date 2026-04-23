import { Link } from 'react-router-dom';
import { getBackendOrigin } from '../backendOrigin';

/**
 * Organizer tools that still live on the FastAPI host (cookie session + forms).
 * This page links there instead of showing a dead “coming soon” shell.
 */
export default function OrganizerBridgePage({ title, path, pageClass = '' }) {
  const origin = getBackendOrigin();
  const href = `${origin}${path.startsWith('/') ? path : `/${path}`}`;

  const pageMods = ['org-page', 'org-placeholder-page', 'es-page', pageClass].filter(Boolean).join(' ');

  const blurb =
    title === 'Messages'
      ? 'Open your customer threads on the API server. Use the same organizer account you use for the Jinja login so your session cookie applies.'
      : 'Create listings, images, and add-ons on the API server. Your organizer session from the Jinja login is required.';

  return (
    <div className={pageMods}>
      <div className="es-placeholder-layout">
        <h1 className="org-page__title es-placeholder-layout__title">{title}</h1>
        <div className="org-placeholder-box es-placeholder-layout__box">
          <p className="org-muted org-placeholder-box__text">{blurb}</p>
          <p style={{ marginTop: '1rem' }}>
            <a href={href} className="org-btn org-btn--primary org-btn--link" rel="noopener noreferrer">
              Open {title} on API server ↗
            </a>
          </p>
          <p className="org-muted" style={{ marginTop: '1rem', fontSize: '0.85rem' }}>
            If the page asks you to sign in, use{' '}
            <a href={`${origin}/organizer/login`} rel="noopener noreferrer">
              organizer login
            </a>{' '}
            first, then return here and open the link again.
          </p>
        </div>
      </div>
      <p className="org-placeholder-back">
        <Link to="/organizer" className="org-link-back">
          ← Back to dashboard
        </Link>
      </p>
    </div>
  );
}
