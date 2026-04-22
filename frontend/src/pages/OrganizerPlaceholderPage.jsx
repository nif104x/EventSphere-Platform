import { Link } from 'react-router-dom';

export default function OrganizerPlaceholderPage({ title, pageClass = '' }) {
  const pageMods = ['org-page', 'org-placeholder-page', 'es-page', pageClass].filter(Boolean).join(' ');
  return (
    <div className={pageMods}>
      <div className="es-placeholder-layout">
        <h1 className="org-page__title es-placeholder-layout__title">{title}</h1>
        <div className="org-placeholder-box es-placeholder-layout__box">
          <p className="org-muted org-placeholder-box__text">
            This section is coming soon. You’ll be able to manage it from here once it launches.
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
