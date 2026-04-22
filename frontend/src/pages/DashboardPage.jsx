import { useState, useEffect } from 'react';
import { getDashboard, submitRating } from '../api';
import { getCustomerId } from '../customerStorage';

const formatDate = (d) => {
  if (d == null) return '';
  const s = typeof d === 'string' ? d : String(d);
  return s.slice(0, 10);
};

const DashboardPage = () => {
  const customerId = getCustomerId();
  const [data, setData] = useState({ events: [], orders: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [ratingFor, setRatingFor] = useState(null);
  const [stars, setStars] = useState(5);
  const [comment, setComment] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- loading gate for initial fetch
    setLoading(true);
    setError(null);
    getDashboard(customerId)
      .then((res) => {
        if (!cancelled) {
          setData(res.data);
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error(err);
        if (!cancelled) {
          setError('Could not load dashboard. Is the API running?');
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [customerId]);

  const openRate = (event) => {
    setRatingFor(event);
    setStars(5);
    setComment('');
  };

  const submitRate = async () => {
    if (!ratingFor) return;
    setSaving(true);
    try {
      await submitRating(ratingFor.id, {
        customer_id: customerId,
        rating: stars,
        comment: comment.trim() || null,
      });
      setRatingFor(null);
      const res = await getDashboard(customerId);
      setData(res.data);
    } catch (e) {
      console.error(e);
      const msg = e.response?.data?.detail || e.message || 'Failed to submit rating';
      alert(typeof msg === 'string' ? msg : JSON.stringify(msg));
    }
    setSaving(false);
  };

  if (loading) {
    return (
      <div className="page-wrap org-page es-page es-page--dashboard org-muted">Loading dashboard…</div>
    );
  }

  const eventCount = data.events.length;
  const orderCount = data.orders.length;
  const rateableCount = data.events.filter(
    (e) => e.can_rate === true || e.can_rate === 'true'
  ).length;

  return (
    <div className="page-wrap org-page dashboard-page es-page es-page--dashboard">
      <header className="page-header">
        <h1 className="es-page-title">My dashboard</h1>
        <p className="muted">Viewing data for customer ID: {customerId}</p>
      </header>
      {error && <p className="error-banner">{error}</p>}

      <div className="es-dash-kpis" aria-label="Summary">
        <div className="es-dash-kpi">
          <div className="es-dash-kpi__label">Events</div>
          <div className="es-dash-kpi__value">{eventCount}</div>
        </div>
        <div className="es-dash-kpi">
          <div className="es-dash-kpi__label">Orders</div>
          <div className="es-dash-kpi__value">{orderCount}</div>
        </div>
        <div className="es-dash-kpi es-dash-kpi--accent">
          <div className="es-dash-kpi__label">Ready to rate</div>
          <div className="es-dash-kpi__value">{rateableCount}</div>
        </div>
      </div>

      <div className="es-dash-stack">
        <section className="dash-panel es-dash-orders es-dash-panel--compact">
          <h2>My orders</h2>
          {data.orders.length === 0 ? (
            <p className="empty-state empty-state--tight">No orders yet.</p>
          ) : (
            <ul className="dash-list dash-list--inline">
              {data.orders.map((order) => (
                <li key={order.id} className="dash-row">
                  <span>
                    {order.company_name}: {order.title} — ${Number(order.final_total_price).toFixed(2)} (
                    {order.payment_status})
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="dash-panel es-dash-events">
          <h2>My events</h2>
          {data.events.length === 0 ? (
            <p className="empty-state empty-state--tight">No events yet.</p>
          ) : (
            <ul className="dash-list">
              {data.events.map((event) => (
                <li key={event.id} className="dash-row">
                  <div>
                    <strong>{event.company_name}</strong> — {formatDate(event.event_date)} —{' '}
                    <span className="status-pill">{String(event.status)}</span>
                    {event.my_rating != null && (
                      <span className="muted"> · Your rating: ★ {Number(event.my_rating)}</span>
                    )}
                  </div>
                  {(event.can_rate === true || event.can_rate === 'true') && (
                    <button type="button" className="btn primary small" onClick={() => openRate(event)}>
                      Rate organizer
                    </button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      {ratingFor && (
        <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="rate-title">
          <div className="modal">
            <h2 id="rate-title">Rate {ratingFor.company_name}</h2>
            <p className="muted">Event {ratingFor.id}</p>
            <div className="field">
              <label htmlFor="stars">Rating (1–5)</label>
              <select id="stars" value={stars} onChange={(e) => setStars(Number(e.target.value))}>
                {[1, 2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>
                    {n} — {n === 1 ? 'Poor' : n === 5 ? 'Excellent' : '…'}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="comment">Comment (optional)</label>
              <textarea
                id="comment"
                rows={3}
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="How was the experience?"
              />
            </div>
            <div className="modal-actions">
              <button type="button" className="btn" onClick={() => setRatingFor(null)} disabled={saving}>
                Cancel
              </button>
              <button type="button" className="btn primary" onClick={submitRate} disabled={saving}>
                {saving ? 'Saving…' : 'Submit rating'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardPage;
