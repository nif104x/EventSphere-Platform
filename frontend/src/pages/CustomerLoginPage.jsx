import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { loginCustomer } from '../api';
import { getCustomerAccessToken, getCustomerSession, setCustomerSession } from '../customerStorage';
import '../customer-login.css';

export default function CustomerLoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const s = getCustomerSession();
    const tok = (getCustomerAccessToken() || '').trim();
    if (s?.customer_id && tok && tok !== 'undefined' && tok !== 'null') {
      navigate('/customer', { replace: true });
    }
  }, [navigate]);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const { data } = await loginCustomer({ username, password });
      setCustomerSession({
        customer_id: data.customer_id,
        full_name: data.full_name,
        username: data.username,
        access_token: data.access_token,
      });
      navigate('/customer', { replace: true });
    } catch (err) {
      const msg = err.response?.data?.detail;
      setError(typeof msg === 'string' ? msg : 'Invalid credentials.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="es-cust-login">
      <div className="es-cust-login__card">
        <div className="es-cust-login__brand">
          <h1>EventSphere</h1>
          <span className="es-cust-login__badge">Customer portal</span>
          <p>Sign in to browse organizers and manage your bookings.</p>
        </div>

        <form onSubmit={onSubmit}>
          {error ? (
            <p className="es-cust-login__error" role="alert">
              {error}
            </p>
          ) : null}
          <div className="es-cust-login__field">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              name="username"
              type="text"
              autoComplete="username"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. alice_smith"
            />
          </div>
          <div className="es-cust-login__field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>
          <button type="submit" className="es-cust-login__submit" disabled={submitting}>
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <div className="es-cust-login__footer">
          <Link to="/">← Portal hub</Link>
        </div>
      </div>
    </div>
  );
}
