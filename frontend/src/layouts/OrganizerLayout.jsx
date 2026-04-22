import { NavLink, Outlet, Link } from 'react-router-dom';
import { getBackendOrigin } from '../backendOrigin';

const linkClass = ({ isActive }) =>
  `org-sidebar__link${isActive ? ' org-sidebar__link--active' : ''}`;

export default function OrganizerLayout() {
  return (
    <div className="org-shell">
      <aside className="org-sidebar" aria-label="Organizer navigation">
        <div className="org-sidebar__brand">EventSphere</div>
        <div className="org-sidebar__badge">Organizer</div>
        <nav className="org-sidebar__nav">
          <NavLink to="/organizer" end className={linkClass}>
            Dashboard
          </NavLink>
          <NavLink to="/organizer/create-gig" className={linkClass}>
            Create Gig
          </NavLink>
          <NavLink to="/organizer/messages" className={linkClass}>
            Messages
          </NavLink>
        </nav>
        <div className="org-sidebar__foot">
          <Link to="/customer" className="org-sidebar__foot-link">
            ← Customer app
          </Link>
          <Link to="/" className="org-sidebar__foot-link">
            Portal hub
          </Link>
          <a
            href={`${getBackendOrigin()}/organizer/login`}
            className="org-sidebar__foot-link"
            rel="noopener noreferrer"
          >
            Organizer (Jinja) ↗
          </a>
        </div>
      </aside>
      <div className="org-main">
        <Outlet />
      </div>
    </div>
  );
}
