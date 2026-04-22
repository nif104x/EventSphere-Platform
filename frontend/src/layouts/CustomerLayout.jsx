import { NavLink, Outlet, Link, useNavigate } from 'react-router-dom';
import { getCustomerSession, clearCustomerSession } from '../customerStorage';

const linkClass = ({ isActive }) =>
  `org-sidebar__link${isActive ? ' org-sidebar__link--active' : ''}`;

/** Jinja chatbot on FastAPI (cookie session), not the React SPA. */
const CUSTOMER_CHATBOT_HREF = (() => {
  const explicit = import.meta.env.VITE_CHATBOT_URL;
  if (explicit) return String(explicit).replace(/\/$/, '');
  const apiBase = import.meta.env.VITE_API_BASE;
  if (apiBase && /^https?:\/\//i.test(String(apiBase))) {
    try {
      const u = new URL(String(apiBase).replace(/\/$/, ''));
      return `${u.origin}/customer/chatbot`;
    } catch {
      /* fall through */
    }
  }
  return 'http://127.0.0.1:8000/customer/chatbot';
})();

export default function CustomerLayout() {
  const navigate = useNavigate();
  const session = getCustomerSession();

  const onSignOut = () => {
    clearCustomerSession();
    navigate('/customer/login', { replace: true });
  };

  return (
    <div className="org-shell org-shell--customer">
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
          <NavLink to="/customer/history" className={linkClass}>
            Events & ratings
          </NavLink>
          <NavLink to="/customer/chat" className={linkClass}>
            Messages
          </NavLink>
          <a
            href={CUSTOMER_CHATBOT_HREF}
            className="org-sidebar__link"
            target="_blank"
            rel="noopener noreferrer"
          >
            Chatbot
          </a>
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
        </div>
      </aside>
      <div className="org-main">
        <Outlet />
      </div>
    </div>
  );
}
