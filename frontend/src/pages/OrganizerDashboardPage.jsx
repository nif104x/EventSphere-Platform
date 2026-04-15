import { useState, useEffect } from 'react';
import { getOrganizers, getOrganizerAnalytics, getOrganizerEvents, markEventComplete } from '../api';
import { getOrganizerOrgId, setOrganizerOrgId } from '../customerStorage';

const formatDate = (d) => {
  if (d == null) return '';
  const s = typeof d === 'string' ? d : String(d);
  return s.slice(0, 10);
};

const OrganizerDashboardPage = () => {
  const [orgList, setOrgList] = useState([]);
  const [orgId, setOrgId] = useState(getOrganizerOrgId);
  const [analytics, setAnalytics] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState(null);

  useEffect(() => {
    getOrganizers()
      .then((res) => {
        setOrgList(res.data);
        const current = getOrganizerOrgId();
        if (res.data.length && !res.data.some((o) => o.org_id === current)) {
          const first = res.data[0].org_id;
          setOrgId(first);
          setOrganizerOrgId(first);
        }
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    let cancelled = false;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- show spinner while refetching for selected vendor
    setLoading(true);
    Promise.all([getOrganizerAnalytics(orgId), getOrganizerEvents(orgId)])
      .then(([a, ev]) => {
        if (cancelled) return;
        setAnalytics(a.data);
        setEvents(ev.data);
        setLoading(false);
      })
      .catch((e) => {
        console.error(e);
        if (!cancelled) {
          setAnalytics(null);
          setEvents([]);
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [orgId]);

  const onOrgChange = (e) => {
    const v = e.target.value;
    setOrgId(v);
    setOrganizerOrgId(v);
  };

  const complete = async (eventId) => {
    setActionId(eventId);
    try {
      await markEventComplete(eventId, orgId);
      const [a, ev] = await Promise.all([
        getOrganizerAnalytics(orgId),
        getOrganizerEvents(orgId),
      ]);
      setAnalytics(a.data);
      setEvents(ev.data);
    } catch (e) {
      console.error(e);
      alert(e.response?.data?.detail || 'Could not update event');
    }
    setActionId(null);
  };

  return (
    <div className="page-wrap organizer-page">
      <h1>Organizer analytics</h1>
      <div className="field inline">
        <label htmlFor="org-select">Vendor account</label>
        <select id="org-select" value={orgId} onChange={onOrgChange}>
          {orgList.map((o) => (
            <option key={o.org_id} value={o.org_id}>
              {o.company_name} ({o.org_id})
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <p>Loading…</p>
      ) : analytics ? (
        <div className="stats-grid">
          <div className="stat-card">
            <span className="stat-label">Events completed</span>
            <span className="stat-value">{analytics.events_served}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Earnings (completed events)</span>
            <span className="stat-value">${Number(analytics.total_earnings).toFixed(2)}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Total bookings</span>
            <span className="stat-value">{analytics.total_bookings}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Gross booking value (all)</span>
            <span className="stat-value">${Number(analytics.gross_booking_value).toFixed(2)}</span>
          </div>
        </div>
      ) : null}

      <section>
        <h2>Events for this organizer</h2>
        {events.length === 0 ? (
          <p className="muted">No events yet.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Event</th>
                <th>Date</th>
                <th>Customer</th>
                <th>Status</th>
                <th>Order total</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {events.map((ev) => (
                <tr key={ev.id}>
                  <td>{ev.id}</td>
                  <td>{formatDate(ev.event_date)}</td>
                  <td>{ev.customer_name || ev.customer_id}</td>
                  <td>{String(ev.status)}</td>
                  <td>{ev.order_total != null ? `$${Number(ev.order_total).toFixed(2)}` : '—'}</td>
                  <td>
                    {String(ev.status) !== 'Completed' && (
                      <button
                        type="button"
                        className="btn small"
                        disabled={actionId === ev.id}
                        onClick={() => complete(ev.id)}
                      >
                        {actionId === ev.id ? '…' : 'Mark completed'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
      <p className="muted small-print">
        Mark an event as completed so the customer can leave a performance rating.
      </p>
    </div>
  );
};

export default OrganizerDashboardPage;
