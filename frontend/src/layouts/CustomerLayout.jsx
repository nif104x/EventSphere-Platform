import { NavLink, Outlet, Link, useNavigate } from 'react-router-dom';
import { getBackendOrigin } from '../backendOrigin';
import { getCustomerSession, clearCustomerSession } from '../customerStorage';

const linkClass = ({ isActive }) =>
  `org-sidebar__link${isActive ? ' org-sidebar__link--active' : ''}`;

export default function CustomerLayout() {
  const navigate = useNavigate();
  const session = getCustomerSession();

  const onSignOut = () => {
    clearCustomerSession();
    navigate('/customer/login', { replace: true });
  };

  return (
    <div className="org-shell">
      <aside className="org-sidebar" aria-label="Customer navigation">
        <div className="org-sidebar__brand">EventSphere</div>
        <div className="org-sidebar__badge">Customer</div>
        <nav className="org-sidebar__nav">
          <NavLink to="/customer" end className={linkClass}>
            Customer home
          </NavLink>
          <NavLink to="/book" className={linkClass}>
            Book
          </NavLink>
          <NavLink to="/dashboard" className={linkClass}>
            My dashboard
          </NavLink>
        </nav>
        <div className="org-sidebar__foot">
          <div className="org-sidebar__account">
            <span className="org-sidebar__account-label">Signed in as</span>
            <div className="org-sidebar__account-name" title={session?.username}>
              {session?.full_name || session?.username || 'Customer'}
            </div>
          </div>
          <button type="button" className="org-sidebar__foot-link org-sidebar__foot-btn" onClick={onSignOut}>
            Sign out
          </button>
          <Link to="/" className="org-sidebar__foot-link">
            ← Portal hub
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
