import { Link } from 'react-router-dom';
import { getBackendOrigin } from '../backendOrigin';
import '../landing.css';

function IconCustomer() {
  return (
    <svg className="es-landing__nav-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
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
    <svg className="es-landing__nav-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
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
    <svg className="es-landing__nav-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
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
      <header className="es-landing__topbar" role="banner">
        <div className="es-landing__topbar-inner">
          <Link className="es-landing__logo" to="/" aria-label="EventSphere — home">
            <span className="es-landing__logo-word es-landing__logo-word--event">Event</span>
            <span className="es-landing__logo-word es-landing__logo-word--sphere">Sphere</span>
          </Link>

          <div className="es-landing__topbar-actions">
            <p id="landing-nav-label" className="es-landing__nav-heading">
              Sign in to your role
            </p>
            <nav className="es-landing__nav" aria-labelledby="landing-nav-label">
              <Link className="es-landing__nav-link es-landing__nav-link--customer" to="/customer">
                <IconCustomer />
                <span className="es-landing__nav-link-text">Customer</span>
                <span className="es-landing__nav-link-hint">Browse &amp; book</span>
              </Link>
              <a
                className="es-landing__nav-link es-landing__nav-link--organizer"
                href={organizerUrl}
                rel="noopener noreferrer"
                title="Opens organizer sign-in in this browser tab"
                aria-label="Organizer: open sign-in"
              >
                <IconOrganizer />
                <span className="es-landing__nav-link-text">Organizer</span>
                <span className="es-landing__nav-link-hint">Dashboard</span>
              </a>
              <a
                className="es-landing__nav-link es-landing__nav-link--admin"
                href={adminUrl}
                rel="noopener noreferrer"
                title="Opens admin tools in this browser tab"
                aria-label="Admin: open admin tools"
              >
                <IconAdmin />
                <span className="es-landing__nav-link-text">Admin</span>
                <span className="es-landing__nav-link-hint">Operations</span>
              </a>
            </nav>
          </div>

          <a className="es-landing__topbar-skip" href="#landing-main">
            Skip to main content
          </a>
        </div>
      </header>

      <main id="landing-main" className="es-landing__main">
        <section className="es-landing__hero" aria-labelledby="landing-title">
          <div className="es-landing__hero-bg" aria-hidden="true">
            <span className="es-landing__hero-orb es-landing__hero-orb--a" />
            <span className="es-landing__hero-orb es-landing__hero-orb--b" />
            <span className="es-landing__hero-orb es-landing__hero-orb--c" />
          </div>
          <div className="es-landing__hero-shell">
            <div className="es-landing__hero-inner">
              <div className="es-landing__hero-copy">
              <p className="es-landing__eyebrow">Event marketplace</p>
              <h1 id="landing-title">Everything your events need—in one place</h1>
              <p className="es-landing__lead">
                Customers discover organizers and complete bookings. Organizers run listings and fulfillment. Admins
                keep the marketplace healthy—each experience is tailored to the job.
              </p>
              <ul className="es-landing__hero-points">
                <li>Guided booking flow with clear pricing</li>
                <li>Each person signs in to their own space—no mixed screens</li>
                <li>Organizer and admin tools connect to the same bookings you manage here</li>
              </ul>
              <div className="es-landing__callout" role="note">
                <span className="es-landing__callout-icon" aria-hidden="true">
                  ↗
                </span>
                <p className="es-landing__callout-text">
                  <strong>Next step:</strong> choose <strong>Customer</strong>, <strong>Organizer</strong>, or{' '}
                  <strong>Admin</strong> in the bar above. Organizer and Admin open on your organization's sign-in page;
                  customers stay on this site.
                </p>
              </div>
              </div>
              <div className="es-landing__hero-aside" aria-hidden="true">
              <div className="es-landing__bento">
                <div className="es-landing__bento-cell es-landing__bento-cell--wide">
                  <span className="es-landing__bento-label">Bookings</span>
                  <span className="es-landing__bento-stat">Live</span>
                </div>
                <div className="es-landing__bento-cell">
                  <span className="es-landing__bento-label">Roles</span>
                  <span className="es-landing__bento-stat">3</span>
                </div>
                <div className="es-landing__bento-cell">
                  <span className="es-landing__bento-label">Payments</span>
                  <span className="es-landing__bento-stat">Online</span>
                </div>
                <div className="es-landing__bento-cell es-landing__bento-cell--accent">
                  <span className="es-landing__bento-label">One platform</span>
                  <span className="es-landing__bento-stat es-landing__bento-stat--lg">EventSphere</span>
                </div>
              </div>
              </div>
            </div>
          </div>
        </section>

        <div className="es-landing__panels-wrap">
          <div className="es-landing__panels-bg" aria-hidden="true" />
          <section className="es-landing__panels" aria-labelledby="panels-title">
            <header className="es-landing__panels-head">
            <h2 id="panels-title" className="es-landing__panels-title">
              Built for clarity
            </h2>
            <p className="es-landing__panels-sub">
              Three clear experiences—so everyone sees what matters to them, without digging through the wrong screens.
            </p>
            </header>
            <div className="es-landing__panel-grid">
            <article className="es-landing__info-panel es-landing__info-panel--customer">
              <span className="es-landing__panel-num" aria-hidden="true">
                01
              </span>
              <h3>Customers</h3>
              <p>
                Browse organizers, compare services, and pay securely—with clear updates from your first request through
                to confirmation.
              </p>
            </article>
            <article className="es-landing__info-panel es-landing__info-panel--organizer">
              <span className="es-landing__panel-num" aria-hidden="true">
                02
              </span>
              <h3>Organizers</h3>
              <p>
                A dedicated workspace for listings, bookings, and day-to-day work—always in step with what your
                customers see and book.
              </p>
            </article>
            <article className="es-landing__info-panel es-landing__info-panel--admin">
              <span className="es-landing__panel-num" aria-hidden="true">
                03
              </span>
              <h3>Admins</h3>
              <p>
                Tools for listings, orders, and accounts—built for your operations team, separate from customer and
                organizer day-to-day screens.
              </p>
            </article>
            </div>
          </section>
        </div>
      </main>

      <footer className="es-landing__footer" role="contentinfo">
        <ul className="es-landing__trust-list" aria-label="Platform highlights">
          <li className="es-landing__trust-chip">Secure online payments</li>
          <li className="es-landing__trust-chip">Private sign-in for customers</li>
          <li className="es-landing__trust-chip">Organizer and admin on their own sign-in pages</li>
        </ul>
        <p className="es-landing__footer-copy">© {new Date().getFullYear()} EventSphere. All rights reserved.</p>
      </footer>
    </div>
  );
}
