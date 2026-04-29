import { useMemo, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { createPaymentCheckout } from '../api';
import { sortPaymentLinesLatest } from '../customerSort';

export default function PaymentPage() {
  const location = useLocation();
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const payload = location.state;
  const lines = useMemo(() => {
    const raw = payload && Array.isArray(payload.lines) ? payload.lines : [];
    return sortPaymentLinesLatest(raw);
  }, [payload]);
  const orderIds = useMemo(() => lines.map((l) => l.order_id).filter(Boolean), [lines]);
  const grandTotal = typeof payload?.grandTotal === 'number' ? payload.grandTotal : 0;

  if (!payload || !lines.length || !orderIds.length) {
    return (
      <div className="page-wrap org-page es-page es-page--payment">
        <h1 className="es-page-title">Payment</h1>
        <p className="muted">Nothing to pay. Open your dashboard after an organizer confirms your booking.</p>
        <Link to="/dashboard" className="btn primary">
          My dashboard
        </Link>
      </div>
    );
  }

  const successUrl = `${window.location.origin}/customer/payment/done?session_id={CHECKOUT_SESSION_ID}`;
  const cancelUrl = `${window.location.origin}/book`;

  const onStripe = async () => {
    setErr(null);
    setBusy(true);
    try {
      const { data } = await createPaymentCheckout({
        order_ids: orderIds,
        success_url: successUrl,
        cancel_url: cancelUrl,
      });
      if (data.url) {
        window.location.assign(data.url);
        return;
      }
      setErr('No checkout URL returned.');
    } catch (e) {
      console.error(e);
      const d = e.response?.data?.detail;
      setErr(typeof d === 'string' ? d : e.message || 'Payment could not start');
    }
    setBusy(false);
  };

  return (
    <div className="page-wrap org-page es-page es-page--payment">
      <nav className="es-book-crumb" aria-label="Breadcrumb">
        <Link to="/customer">Customer</Link>
        <span className="es-book-crumb__sep">/</span>
        <span>Payment</span>
      </nav>

      <header className="es-pay-header">
        <h1 className="es-page-title">Payment</h1>
      </header>

      {err && <p className="error-banner">{err}</p>}

      <section className="dash-panel es-pay-panel">
        <h2>Summary</h2>
        <p className="muted es-dash-table-caption">Newest orders first.</p>
        <div className="es-customer-table-wrap">
          <table className="es-customer-table">
            <thead>
              <tr>
                <th scope="col">Order</th>
                <th scope="col">Vendor</th>
                <th scope="col">Amount</th>
              </tr>
            </thead>
            <tbody>
              {lines.map((line) => (
                <tr key={line.order_id}>
                  <td data-label="Order">
                    <code>{line.order_id}</code>
                  </td>
                  <td data-label="Vendor">{line.company_name || 'Vendor'}</td>
                  <td data-label="Amount">${Number(line.amount || 0).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="es-pay-total">
          Total <strong>${grandTotal.toFixed(2)}</strong>
        </p>

        <div className="es-pay-actions">
          <button type="button" className="btn primary" disabled={busy} onClick={onStripe}>
            {busy ? 'Redirecting…' : 'Pay with Stripe'}
          </button>
        </div>
      </section>
    </div>
  );
}
