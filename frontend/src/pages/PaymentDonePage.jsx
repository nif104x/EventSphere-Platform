import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { completePaymentSession } from '../api';

export default function PaymentDonePage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const sessionId = params.get('session_id');
  const [status, setStatus] = useState('working');
  const [detail, setDetail] = useState(null);

  useEffect(() => {
    if (!sessionId) {
      setStatus('error');
      setDetail('Missing session_id. Return to your dashboard.');
      return undefined;
    }
    let cancelled = false;
    let redirectTimer;
    (async () => {
      try {
        const { data } = await completePaymentSession({ session_id: sessionId });
        if (cancelled) return;
        setStatus('ok');
        setDetail(
          data.already_completed
            ? 'Payment was already recorded for these orders.'
            : `Updated ${data.updated ?? 0} order(s).`,
        );
        redirectTimer = setTimeout(() => navigate('/dashboard', { replace: true }), 1600);
      } catch (e) {
        if (cancelled) return;
        console.error(e);
        setStatus('error');
        const d = e.response?.data?.detail;
        const msg =
          typeof d === 'string'
            ? d
            : Array.isArray(d)
              ? d.map((x) => (typeof x === 'string' ? x : x?.msg || JSON.stringify(x))).join(' ')
              : e.message || 'Could not confirm payment';
        setDetail(msg);
      }
    })();
    return () => {
      cancelled = true;
      if (redirectTimer) clearTimeout(redirectTimer);
    };
  }, [sessionId, navigate]);

  return (
    <div className="page-wrap org-page es-page es-page--payment">
      <h1 className="es-page-title">Payment result</h1>
      {status === 'working' && <p className="muted">Confirming your payment…</p>}
      {status === 'ok' && (
        <p className="es-pay-success">
          Thank you! {detail} Redirecting to your dashboard…
        </p>
      )}
      {status === 'error' && (
        <>
          <p className="error-banner">{typeof detail === 'string' ? detail : 'Something went wrong.'}</p>
          <Link to="/dashboard" className="btn primary">
            My dashboard
          </Link>
        </>
      )}
    </div>
  );
}
