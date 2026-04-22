import { Link } from 'react-router-dom';
import { getBackendOrigin } from '../backendOrigin';
import '../landing.css';

export default function LandingPage() {
  const api = getBackendOrigin();
  const organizerUrl = `${api}/organizer/login`;
  const adminUrl = `${api}/admin/ui`;

  return (
    <div className="es-landing">
      <header className="es-landing__topbar">
        <span className="es-landing__logo">EventSphere</span>
      </header>

      <main className="es-landing__main">
        <section className="es-landing__hero" aria-labelledby="landing-title">
          <h1 id="landing-title">Plan events in one place</h1>
          <p className="es-landing__lead">
            Book vendors as a customer, run your listings as an organizer, or oversee the platform as an
            admin—each role has its own entry below.
          </p>
        </section>

        <nav className="es-landing__portals" aria-label="Sign-in options">
          <Link className="es-landing__portal" to="/customer">
            <span className="es-landing__portal-title">Customer</span>
            <p className="es-landing__portal-desc">Find organizers, plan your event, and sign in when you are ready.</p>
            <span className="es-landing__portal-cta">Continue</span>
          </Link>

          <a className="es-landing__portal" href={organizerUrl} rel="noopener noreferrer">
            <span className="es-landing__portal-title">Organizer</span>
            <p className="es-landing__portal-desc">Log in to manage gigs, bookings, and messages for your business.</p>
            <span className="es-landing__portal-cta">Open organizer</span>
          </a>

          <a className="es-landing__portal" href={adminUrl} rel="noopener noreferrer">
            <span className="es-landing__portal-title">Admin</span>
            <p className="es-landing__portal-desc">Review listings, orders, and accounts for the whole marketplace.</p>
            <span className="es-landing__portal-cta">Open admin</span>
          </a>
        </nav>
      </main>

      <footer className="es-landing__footer">© EventSphere</footer>
    </div>
  );
}
