import { NavLink, Outlet, Link } from 'react-router-dom';
import { useState } from 'react';
import { CUSTOMERS, getCustomerId, setCustomerId } from '../customerStorage';

const linkClass = ({ isActive }) =>
  `org-sidebar__link${isActive ? ' org-sidebar__link--active' : ''}`;

export default function CustomerLayout() {
  const [customerId, setCust] = useState(getCustomerId);

  const onCustomerChange = (e) => {
    const v = e.target.value;
    setCustomerId(v);
    setCust(v);
  };

  return (
    <div className="org-shell">
      <aside className="org-sidebar" aria-label="Customer navigation">
        <div className="org-sidebar__brand">EventSphere</div>
        <div className="org-sidebar__badge">Customer</div>
        <nav className="org-sidebar__nav">
          <NavLink to="/" end className={linkClass}>
            Home
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
            <span className="org-sidebar__account-label">Acting as</span>
            <select
              className="org-sidebar__select"
              value={customerId}
              onChange={onCustomerChange}
              aria-label="Select customer"
            >
              {CUSTOMERS.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>
          <Link to="/organizer" className="org-sidebar__foot-link">
            Organizer portal →
          </Link>
        </div>
      </aside>
      <div className="org-main">
        <Outlet context={{ customerId }} key={customerId} />
      </div>
    </div>
  );
}
