import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import { useState } from 'react';
import HomePage from './pages/HomePage';
import BookingPage from './pages/BookingPage';
import DashboardPage from './pages/DashboardPage';
import OrganizerDashboardPage from './pages/OrganizerDashboardPage';
import { CUSTOMERS, getCustomerId, setCustomerId } from './customerStorage';

function App() {
  const [customerId, setCust] = useState(getCustomerId);

  const onCustomerChange = (e) => {
    const v = e.target.value;
    setCustomerId(v);
    setCust(v);
  };

  return (
    <Router>
      <header className="app-nav">
        <div className="app-nav__inner">
          <Link to="/" className="app-nav__brand">
            EventSphere
          </Link>
          <nav className="app-nav__links">
            <Link to="/">Home</Link>
            <Link to="/dashboard">Customer dashboard</Link>
            <Link to="/organizer">Organizer dashboard</Link>
          </nav>
          <label className="app-nav__customer">
            <span>Customer</span>
            <select value={customerId} onChange={onCustomerChange}>
              {CUSTOMERS.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label}
                </option>
              ))}
            </select>
          </label>
        </div>
      </header>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/book" element={<BookingPage key={customerId} />} />
          <Route path="/dashboard" element={<DashboardPage key={customerId} />} />
          <Route path="/organizer" element={<OrganizerDashboardPage />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>
    </Router>
  );
}

export default App;
