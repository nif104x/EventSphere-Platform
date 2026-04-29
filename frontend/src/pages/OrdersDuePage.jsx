import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getDashboard } from '../api';
import { clearCustomerSession, getCustomerId } from '../customerStorage';
import { getSortedDashboardSlices } from '../customerPayableOrders';

const formatDate = (d) => {
  if (d == null) return '';
  const s = typeof d === 'string' ? d : String(d);
  return s.slice(0, 10);
};

export default function OrdersDuePage() {
  const navigate = useNavigate();
  const customerId = getCustomerId();
  const [data, setData] = useState({ events: [], orders: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    getDashboard(customerId)
      .then((res) => {
        setData(res.data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        const st = err.response?.status;
        if (st === 401 || st === 403) {
          clearCustomerSession();
          navigate('/customer/login', { replace: true });
          return;
        }
        setError('Could not load orders. Is the API running?');
        setLoading(false);
      });
  }, [customerId, navigate]);

  useEffect(() => {
    load();
  }, [load]);

  const { payableOrders, eventsById } = useMemo(() => getSortedDashboardSlices(data), [data]);

  const grandTotal = useMemo(
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
    navigate('/customer/payment', { state: { lines, grandTotal } });
  }, [navigate, payableOrders, grandTotal]);

  if (loading) {
    return (
      <div className="page-wrap org-page es-page es-page--orders-due org-muted">Loading payments due…</div>
    );
  }

  return (
    <div className="page-wrap org-page es-page es-page--orders-due">
      <header className="page-header es-dash-header">
        <div>
          <h1 className="es-page-title">Payments due</h1>
          <p className="muted">
            These bookings are <strong>Confirmed</strong> by the organizer but still <strong>unpaid</strong>. Pay here,
            then return to <Link to="/dashboard">My dashboard</Link> to track the event.
          </p>
        </div>
        <Link to="/dashboard" className="btn small">
          My dashboard
        </Link>
      </header>

      {error && <p className="error-banner">{error}</p>}

      {payableOrders.length > 0 && (
        <p className="es-dash-callout" role="status">
          Total due: <strong>${grandTotal.toFixed(2)}</strong> across {payableOrders.length} order
          {payableOrders.length === 1 ? '' : 's'}.
          <button type="button" className="btn primary small es-dash-callout__btn" onClick={goToPayment}>
            Pay with Stripe
          </button>
        </p>
      )}

      <section className="dash-panel">
        <h2>Confirmed — payment due</h2>
        <p className="muted es-dash-table-caption">Newest orders first.</p>
        {payableOrders.length === 0 ? (
          <p className="empty-state empty-state--tight">
            No payments due right now. After an organizer confirms your booking, unpaid orders will show here and on
            your dashboard.
          </p>
        ) : (
          <div className="es-customer-table-wrap">
            <table className="es-customer-table">
              <thead>
                <tr>
                  <th scope="col">Order</th>
                  <th scope="col">Event</th>
                  <th scope="col">Event date</th>
                  <th scope="col">Event status</th>
                  <th scope="col">Vendor</th>
                  <th scope="col">Service</th>
                  <th scope="col">Amount</th>
                  <th scope="col">Payment</th>
                </tr>
              </thead>
              <tbody>
                {payableOrders.map((order) => {
                  const ev = eventsById[order.event_id];
                  return (
                    <tr key={order.id}>
                      <td>
                        <code>{order.id}</code>
                      </td>
                      <td>
                        <code>{order.event_id}</code>
                      </td>
                      <td>{ev ? formatDate(ev.event_date) : '—'}</td>
                      <td>
                        <span className="status-pill">{ev ? String(ev.status) : '—'}</span>
                      </td>
                      <td>{order.company_name}</td>
                      <td>{order.title}</td>
                      <td>${Number(order.final_total_price || 0).toFixed(2)}</td>
                      <td>{String(order.payment_status)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
