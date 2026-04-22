import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getDashboard, submitRating, markEventComplete } from '../api';
import { clearCustomerSession, getCustomerId } from '../customerStorage';
import { canMarkEventComplete, truthyApiFlag, isConfirmedEventStatus } from '../eventUi';

const formatDate = (d) => {
  if (d == null) return '';
  const s = typeof d === 'string' ? d : String(d);
  return s.slice(0, 10);
};

const DashboardPage = () => {
  const navigate = useNavigate();
  const customerId = getCustomerId();
  const [data, setData] = useState({ events: [], orders: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [ratingFor, setRatingFor] = useState(null);
  const [stars, setStars] = useState(5);
  const [comment, setComment] = useState('');
  const [saving, setSaving] = useState(false);
  const [completingId, setCompletingId] = useState(null);

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
          const st = err.response?.status;
          if (st === 401 || st === 403) {
            clearCustomerSession();
            navigate('/customer/login', { replace: true });
            return;
          }
          setError('Could not load dashboard. Is the API running?');
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [customerId, navigate]);

  const openRate = (event) => {
    setRatingFor(event);
    setStars(5);
    setComment('');
  };

  const markComplete = async (eventId) => {
    setCompletingId(eventId);
    try {
      await markEventComplete(eventId);
      const res = await getDashboard(customerId);
      setData(res.data);
    } catch (e) {
      console.error(e);
      const st = e.response?.status;
      if (st === 401 || st === 403) {
        clearCustomerSession();
        navigate('/customer/login', { replace: true });
        return;
      }
      const msg = e.response?.data?.detail || e.message || 'Could not mark event complete';
      alert(typeof msg === 'string' ? msg : JSON.stringify(msg));
    }
    setCompletingId(null);
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
  const rateableCount = data.events.filter((e) => truthyApiFlag(e.can_rate)).length;
  const markableCount = data.events.filter((e) => canMarkEventComplete(e)).length;

  return (
    <div className="page-wrap org-page dashboard-page es-page es-page--dashboard">
      <header className="page-header es-dash-header">
        <div>
          <h1 className="es-page-title">My dashboard</h1>
          <p className="muted">
            The vendor <strong>confirms</strong> your booking. <strong>You</strong> tap{' '}
            <strong>Mark event complete</strong> when the service is finished — only after that can{' '}
            <strong>you</strong> use <strong>Rate vendor</strong>. Full archive:{' '}
            <Link to="/customer/history">Events & ratings</Link>.
          </p>
        </div>
        <Link to="/customer/history" className="btn small">
          Full history
        </Link>
      </header>
      {error && <p className="error-banner">{error}</p>}

      {markableCount > 0 && (
        <p className="es-dash-callout" role="status">
          You have <strong>{markableCount}</strong> confirmed event{markableCount === 1 ? '' : 's'} — use{' '}
          <strong>Mark event complete</strong> under <strong>My events</strong> when the service is done, then you can
          rate the vendor.
        </p>
      )}

      <div className="es-dash-kpis" aria-label="Summary">
        <div className="es-dash-kpi">
          <div className="es-dash-kpi__label">Events</div>
          <div className="es-dash-kpi__value">{eventCount}</div>
        </div>
        <div className="es-dash-kpi">
          <div className="es-dash-kpi__label">Orders</div>
          <div className="es-dash-kpi__value">{orderCount}</div>
        </div>
        <div className="es-dash-kpi">
          <div className="es-dash-kpi__label">Mark complete</div>
          <div className="es-dash-kpi__value">{markableCount}</div>
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
          {data.events.length > 0 && markableCount === 0 && (
            <p className="muted es-dash-events__hint">
              <strong>Mark event complete</strong> appears when status is <strong>Confirmed</strong> (after the
              vendor accepts your booking). Pending = still waiting on the vendor.
            </p>
          )}
          {data.events.length === 0 ? (
            <p className="empty-state empty-state--tight">No events yet.</p>
          ) : (
            <ul className="dash-list">
              {data.events.map((event) => (
                <li key={event.id} className="dash-row">
                  <div>
                    <strong>{event.company_name}</strong> — {formatDate(event.event_date)} —{' '}
                    <span className="status-pill">{String(event.status)}</span>
                    {isConfirmedEventStatus(event.status) && (
                      <span className="muted"> · You can mark this complete when the service is finished.</span>
                    )}
                    {event.my_rating != null && (
                      <span className="muted"> · Your rating: ★ {Number(event.my_rating)}</span>
                    )}
                  </div>
                  <div className="dash-row__actions">
                    {canMarkEventComplete(event) && (
                      <button
                        type="button"
                        className="btn primary small"
                        disabled={completingId === event.id}
                        onClick={() => markComplete(event.id)}
                      >
                        {completingId === event.id ? 'Updating…' : 'Mark event complete'}
                      </button>
                    )}
                    <Link
                      to={`/customer/chat?eventId=${encodeURIComponent(event.id)}`}
                      className="btn small"
                    >
                      Message vendor
                    </Link>
                  </div>
                  {truthyApiFlag(event.can_rate) && (
                    <button type="button" className="btn primary small" onClick={() => openRate(event)}>
                      Rate vendor
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
