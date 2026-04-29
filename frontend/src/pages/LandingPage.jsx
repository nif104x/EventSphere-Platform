import { Link } from 'react-router-dom';
import { getBackendOrigin } from '../backendOrigin';
import '../landing.css';

function IconCustomer() {
  return (
    <svg className="es-landing__portal-icon-svg" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M12 11a4 4 0 1 0-4-4 4 4 0 0 0 4 4Zm0 2c-4.42 0-8 2.24-8 5v1h16v-1c0-2.76-3.58-5-8-5Z"
        fill="currentColor"
        opacity="0.9"
      />
    </svg>
  );
}

function IconOrganizer() {
  return (
    <svg className="es-landing__portal-icon-svg" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2Z"
        fill="currentColor"
        opacity="0.9"
      />
    </svg>
  );
}

function IconAdmin() {
  return (
    <svg className="es-landing__portal-icon-svg" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M12 1 3 5v6c0 5 3.9 9.4 9 10.5 5.1-1.1 9-5.5 9-10.5V5l-9-4Zm-1 6h2v6h-2V7Zm0 8h2v2h-2v-2Z"
        fill="currentColor"
        opacity="0.9"
      />
    </svg>
  );
}

export default function LandingPage() {
  const api = getBackendOrigin();
  const organizerUrl = `${api}/organizer/login`;
  const adminUrl = `${api}/admin/ui`;

  return (
    <div className="es-landing">
      <header className="es-landing__topbar">
        <Link className="es-landing__logo" to="/">
          <span className="es-landing__logo-mark" aria-hidden="true" />
          EventSphere
        </Link>
        <a className="es-landing__topbar-skip" href="#portals">
          Jump to portals
        </a>
      </header>

      <main className="es-landing__main">
        <section className="es-landing__hero" aria-labelledby="landing-title">
          <div className="es-landing__hero-inner">
            <div className="es-landing__hero-copy">
              <p className="es-landing__eyebrow">Event marketplace</p>
              <h1 id="landing-title">Everything your event stack needs—under one roof</h1>
              <p className="es-landing__lead">
                Customers discover organizers and complete bookings. Organizers run listings and fulfillment.
                Admins keep the marketplace healthy—each experience is tailored to the job.
              </p>
              <ul className="es-landing__hero-points">
                <li>Guided booking flow with clear pricing</li>
                <li>Role-based entry—no mixed dashboards</li>
                <li>Hosted organizer &amp; admin tools on your API</li>
              </ul>
            </div>
            <div className="es-landing__hero-visual" aria-hidden="true">
              <div className="es-landing__hero-glow" />
              <div className="es-landing__hero-mock">
                <div className="es-landing__hero-mock-card es-landing__hero-mock-card--back" />
                <div className="es-landing__hero-mock-card es-landing__hero-mock-card--front">
                  <span className="es-landing__hero-mock-line" />
                  <span className="es-landing__hero-mock-line es-landing__hero-mock-line--short" />
                  <span className="es-landing__hero-mock-pill" />
                </div>
              </div>
            </div>
          </div>
        </section>

        <div id="portals" className="es-landing__portals-block">
          <p className="es-landing__section-kicker">Get started</p>
          <h2 className="es-landing__section-title">Choose your portal</h2>
          <p className="es-landing__section-sub">Same platform—three tailored experiences.</p>

          <nav className="es-landing__portals" aria-label="Sign-in options">
          <Link className="es-landing__portal" to="/customer">
            <span className="es-landing__portal-icon" aria-hidden="true">
              <IconCustomer />
            </span>
            <span className="es-landing__portal-title">Customer</span>
            <p className="es-landing__portal-desc">
              Browse organizers, compare services, and check out when you are ready—without leaving the app.
            </p>
            <span className="es-landing__portal-cta">
              Continue
              <span className="es-landing__portal-arrow" aria-hidden="true">
                →
              </span>
            </span>
          </Link>

          <a
            className="es-landing__portal"
            href={organizerUrl}
            rel="noopener noreferrer"
            aria-label="Organizer: open login on the API server"
          >
            <span className="es-landing__portal-icon" aria-hidden="true">
              <IconOrganizer />
            </span>
            <span className="es-landing__portal-title">Organizer</span>
            <p className="es-landing__portal-desc">
              Open the hosted dashboard to manage listings, bookings, and day-to-day operations for your team.
            </p>
            <span className="es-landing__portal-cta">
              Open login
              <span className="es-landing__portal-arrow" aria-hidden="true">
                ↗
              </span>
            </span>
          </a>

          <a
            className="es-landing__portal"
            href={adminUrl}
            rel="noopener noreferrer"
            aria-label="Admin: open console on the API server"
          >
            <span className="es-landing__portal-icon" aria-hidden="true">
              <IconAdmin />
            </span>
            <span className="es-landing__portal-title">Admin</span>
            <p className="es-landing__portal-desc">
              Review listings, orders, and accounts from the admin console—built for operators, not end users.
            </p>
            <span className="es-landing__portal-cta">
              Open console
              <span className="es-landing__portal-arrow" aria-hidden="true">
                ↗
              </span>
            </span>
          </a>
          </nav>
        </div>
      </main>

      <footer className="es-landing__footer">
        <div className="es-landing__trust" aria-label="Platform highlights">
          <span className="es-landing__trust-item">Secure payments via Stripe</span>
          <span className="es-landing__trust-dot" aria-hidden="true" />
          <span className="es-landing__trust-item">JWT-protected customer API</span>
          <span className="es-landing__trust-dot" aria-hidden="true" />
          <span className="es-landing__trust-item">Separate organizer &amp; admin hosts</span>
        </div>
        <p className="es-landing__footer-copy">© {new Date().getFullYear()} EventSphere. All rights reserved.</p>
      </footer>
    </div>
  );
}
