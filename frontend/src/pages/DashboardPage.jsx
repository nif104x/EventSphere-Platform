import { useState, useEffect, useMemo, useCallback } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { getDashboard, submitRating, markEventComplete } from '../api';
import { clearCustomerSession, getCustomerId } from '../customerStorage';
import { canMarkEventComplete, truthyApiFlag, isConfirmedEventStatus } from '../eventUi';
import { getSortedDashboardSlices } from '../customerPayableOrders';

const formatDate = (d) => {
  if (d == null) return '';
  const s = typeof d === 'string' ? d : String(d);
  return s.slice(0, 10);
};

const DashboardPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const customerId = getCustomerId();
  const [data, setData] = useState({ events: [], orders: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [bookingPlacedBanner, setBookingPlacedBanner] = useState(false);
  const [ratingFor, setRatingFor] = useState(null);
  const [stars, setStars] = useState(5);
  const [comment, setComment] = useState('');
  const [saving, setSaving] = useState(false);
  const [completingId, setCompletingId] = useState(null);

  useEffect(() => {
    if (location.state?.bookingPlaced) {
      setBookingPlacedBanner(true);
      navigate(location.pathname, { replace: true, state: {} });
    }
  }, [location.state, location.pathname, navigate]);

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

  const { sortedEvents, sortedOrders, payableOrders, awaitingVendorOrders } = useMemo(
    () => getSortedDashboardSlices(data),
    [data],
  );

  const payableGrandTotal = useMemo(
    () => payableOrders.reduce((sum, o) => sum + Number(o.final_total_price || 0), 0),
    [payableOrders],
  );

  const goToPayment = useCallback(() => {
    const lines = payableOrders.map((o) => ({
      order_id: o.id,
      event_id: o.event_id,
      amount: Number(o.final_total_price || 0),
      company_name: o.company_name,
    }));
    navigate('/customer/payment', { state: { lines, grandTotal: payableGrandTotal } });
  }, [navigate, payableOrders, payableGrandTotal]);

  if (loading) {
    return (
      <div className="page-wrap org-page es-page es-page--dashboard org-muted">Loading dashboard…</div>
    );
  }

  const eventCount = sortedEvents.length;
  const orderCount = sortedOrders.length;
  const rateableCount = sortedEvents.filter((e) => truthyApiFlag(e.can_rate)).length;
  const markableCount = sortedEvents.filter((e) => canMarkEventComplete(e)).length;

  return (
    <div className="page-wrap org-page dashboard-page es-page es-page--dashboard">
      <header className="page-header es-dash-header">
        <div>
          <h1 className="es-page-title">My dashboard</h1>
          <p className="muted">
            The vendor <strong>confirms</strong> your booking first; then <strong>you pay</strong> from{' '}
            <strong>My orders</strong>. After payment, <strong>Mark event complete</strong> when the service is
            finished — only then can you <strong>Rate vendor</strong>. Full archive:{' '}
            <Link to="/customer/history">Events & ratings</Link>.
          </p>
        </div>
        <Link to="/customer/history" className="btn small">
          Full history
        </Link>
      </header>
      {error && <p className="error-banner">{error}</p>}

      {bookingPlacedBanner && (
        <p className="es-dash-callout es-dash-callout--success" role="status">
          Booking request submitted. Status stays <strong>Pending</strong> until each organizer confirms — then use{' '}
          <strong>Pay now</strong> below.
        </p>
      )}

      {payableOrders.length > 0 && (
        <p className="es-dash-callout" role="status">
          You have <strong>{payableOrders.length}</strong> unpaid order{payableOrders.length === 1 ? '' : 's'} ready for
          payment.
          <Link to="/customer/orders-due" className="btn small es-dash-callout__btn">
            View list
          </Link>
          <button type="button" className="btn primary small es-dash-callout__btn" onClick={goToPayment}>
            Pay now
          </button>
        </p>
      )}

      {awaitingVendorOrders.length > 0 && payableOrders.length === 0 && (
        <p className="muted es-dash-callout" role="status">
          {awaitingVendorOrders.length} order{awaitingVendorOrders.length === 1 ? '' : 's'} awaiting organizer
          confirmation before you can pay.
        </p>
      )}

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
          <p className="muted es-dash-table-caption">Newest orders first.</p>
          {sortedOrders.length === 0 ? (
            <p className="empty-state empty-state--tight">No orders yet.</p>
          ) : (
            <div className="es-customer-table-wrap">
              <table className="es-customer-table">
                <thead>
                  <tr>
                    <th scope="col">Order</th>
                    <th scope="col">Event</th>
                    <th scope="col">Vendor</th>
                    <th scope="col">Service</th>
                    <th scope="col">Amount</th>
                    <th scope="col">Payment</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedOrders.map((order) => (
                    <tr key={order.id}>
                      <td data-label="Order">
                        <code>{order.id}</code>
                      </td>
                      <td data-label="Event">
                        <code>{order.event_id}</code>
                      </td>
                      <td data-label="Vendor">{order.company_name}</td>
                      <td data-label="Service">{order.title}</td>
                      <td data-label="Amount">${Number(order.final_total_price).toFixed(2)}</td>
                      <td data-label="Payment">{String(order.payment_status)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="dash-panel es-dash-events">
          <h2>My events</h2>
          <p className="muted es-dash-table-caption">Newest event dates first.</p>
          {sortedEvents.length > 0 && markableCount === 0 && (
            <p className="muted es-dash-events__hint">
              <strong>Pay</strong> after status is <strong>Confirmed</strong>. <strong>Mark event complete</strong>{' '}
              appears once the booking is confirmed <em>and</em> paid. <strong>Pending</strong> = waiting on the
              vendor.
            </p>
          )}
          {sortedEvents.length === 0 ? (
            <p className="empty-state empty-state--tight">No events yet.</p>
          ) : (
            <div className="es-customer-table-wrap">
              <table className="es-customer-table">
                <thead>
                  <tr>
                    <th scope="col">Vendor</th>
                    <th scope="col">Event date</th>
                    <th scope="col">Event ID</th>
                    <th scope="col">Status</th>
                    <th scope="col">Notes</th>
                    <th scope="col">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedEvents.map((event) => (
                    <tr key={event.id}>
                      <td data-label="Vendor">
                        <strong>{event.company_name}</strong>
                      </td>
                      <td data-label="Date">{formatDate(event.event_date)}</td>
                      <td data-label="Event ID">
                        <code>{event.id}</code>
                      </td>
                      <td data-label="Status">
                        <span className="status-pill">{String(event.status)}</span>
                      </td>
                      <td data-label="Notes" className="es-dash-notes-cell">
                        {isConfirmedEventStatus(event.status) && canMarkEventComplete(event) && (
                          <span className="muted">Ready to mark complete when the service is finished.</span>
                        )}
                        {isConfirmedEventStatus(event.status) && !canMarkEventComplete(event) && (
                          <span className="muted">Pay in My orders, then mark complete when finished.</span>
                        )}
                        {event.my_rating != null && (
                          <span className="muted">Your rating: ★ {Number(event.my_rating)}</span>
                        )}
                      </td>
                      <td data-label="Actions">
                        <div className="es-dash-actions-cell">
                          {canMarkEventComplete(event) && (
                            <button
                              type="button"
                              className="btn primary small"
                              disabled={completingId === event.id}
                              onClick={() => markComplete(event.id)}
                            >
                              {completingId === event.id ? 'Updating…' : 'Mark complete'}
                            </button>
                          )}
                          <Link
                            to={`/customer/chat?eventId=${encodeURIComponent(event.id)}`}
                            className="btn small"
                          >
                            Message
                          </Link>
                          {truthyApiFlag(event.can_rate) && (
                            <button type="button" className="btn primary small" onClick={() => openRate(event)}>
                              Rate
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
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
