import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  getOrganizers,
  getOrganizerAnalytics,
  getOrganizerEvents,
  markEventComplete,
  getOrganizerReviews,
  getOrganizerListings,
  respondToEvent,
} from '../api';
import { getOrganizerOrgId, setOrganizerOrgId } from '../customerStorage';

const formatDate = (d) => {
  if (d == null) return '—';
  try {
    const x = typeof d === 'string' ? d.slice(0, 10) : String(d).slice(0, 10);
    const dt = new Date(x + 'T12:00:00');
    if (Number.isNaN(dt.getTime())) return x;
    return dt.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return String(d);
  }
};

const Stars = ({ value }) => (
  <span className="org-stars" aria-hidden>
    {[1, 2, 3, 4, 5].map((n) => (
      <span key={n} className={n <= value ? 'org-star org-star--on' : 'org-star'}>
        ★
      </span>
    ))}
  </span>
);

export default function OrganizerDashboardPage() {
  const [orgList, setOrgList] = useState([]);
  const [orgId, setOrgId] = useState(getOrganizerOrgId);
  const [analytics, setAnalytics] = useState(null);
  const [events, setEvents] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [listings, setListings] = useState([]);
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

  const companyName = useMemo(() => {
    return orgList.find((x) => x.org_id === orgId)?.company_name || orgId;
  }, [orgList, orgId]);

  useEffect(() => {
    let cancelled = false;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- loading gate for dashboard fetch
    setLoading(true);
    Promise.all([
      getOrganizerAnalytics(orgId),
      getOrganizerEvents(orgId),
      getOrganizerReviews(orgId),
      getOrganizerListings(orgId),
    ])
      .then(([a, ev, rv, ls]) => {
        if (cancelled) return;
        setAnalytics(a.data);
        setEvents(ev.data);
        setReviews(rv.data);
        setListings(ls.data);
        setLoading(false);
      })
      .catch((e) => {
        console.error(e);
        if (!cancelled) {
          setAnalytics(null);
          setEvents([]);
          setReviews([]);
          setListings([]);
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [orgId]);

  const refresh = async () => {
    const [a, ev, rv, ls] = await Promise.all([
      getOrganizerAnalytics(orgId),
      getOrganizerEvents(orgId),
      getOrganizerReviews(orgId),
      getOrganizerListings(orgId),
    ]);
    setAnalytics(a.data);
    setEvents(ev.data);
    setReviews(rv.data);
    setListings(ls.data);
  };

  const complete = async (eventId) => {
    setActionId(eventId);
    try {
      await markEventComplete(eventId, orgId);
      await refresh();
    } catch (e) {
      console.error(e);
      alert(e.response?.data?.detail || 'Could not update event');
    }
    setActionId(null);
  };

  const respond = async (eventId, action) => {
    setActionId(eventId);
    try {
      await respondToEvent(eventId, { org_id: orgId, action });
      await refresh();
    } catch (e) {
      console.error(e);
      alert(e.response?.data?.detail || 'Could not update order');
    }
    setActionId(null);
  };

  const pending = events.filter((e) => String(e.status) === 'Pending');
  const completed = events.filter((e) => String(e.status) === 'Completed');

  const earnings = analytics ? Number(analytics.total_earnings).toFixed(2) : '0.00';
  const ratingDisplay = analytics ? Number(analytics.avg_rating || 0).toFixed(1) : '0.0';

  return (
    <div className="org-page es-page es-page--organizer-dash es-od-page">
      <header className="org-header org-header--split">
        <div>
          <h1 className="org-header__welcome">Welcome back, {companyName}</h1>
        </div>
        <div className="org-header__actions">
          <select
            className="org-select-org"
            value={orgId}
            onChange={(e) => {
              const v = e.target.value;
              setOrgId(v);
              setOrganizerOrgId(v);
            }}
            aria-label="Organization"
          >
            {orgList.map((o) => (
              <option key={o.org_id} value={o.org_id}>
                {o.company_name}
              </option>
            ))}
          </select>
          <Link to="/organizer/create-gig" className="org-btn org-btn--primary org-btn--link">
            + New Service
          </Link>
        </div>
      </header>

      {loading ? (
        <p className="org-muted">Loading…</p>
      ) : (
        <>
          <section className="org-stat-row org-stat-row--inline">
            <div className="org-stat-card">
              <div className="org-stat-card__label">TOTAL EARNINGS</div>
              <div className="org-stat-card__value">${earnings}</div>
            </div>
            <div className="org-stat-card">
              <div className="org-stat-card__label">COMPLETED EVENTS</div>
              <div className="org-stat-card__value">{analytics?.events_served ?? 0}</div>
            </div>
            <div className="org-stat-card org-stat-card--rating">
              <div className="org-stat-card__label">AVERAGE RATING</div>
              <div className="org-stat-card__value org-stat-card__value--rating">
                <span>{ratingDisplay}</span>
                <span className="org-stat-card__rating-star" title="Average rating">
                  ★
                </span>
              </div>
            </div>
          </section>

          <div className="org-grid-2 org-grid-2--reviews-first">
            <section className="org-panel">
              <h2 className="org-panel__title org-panel__title--sm">Recent Reviews</h2>
              <div className="org-review-list">
                {reviews.length === 0 ? (
                  <p className="org-muted">No reviews yet.</p>
                ) : (
                  reviews.map((r) => (
                    <div key={r.id} className="org-review-card">
                      <div className="org-review-card__top">
                        <Stars value={r.rating} />
                        <span className="org-review-card__date">{formatDate(r.event_date)}</span>
                      </div>
                      <p className="org-review-card__text">
                        {r.comment ? `“${r.comment}”` : '—'}
                      </p>
                      <div className="org-review-card__by">
                        — {r.customer_name || 'Customer'} ({r.event_id})
                      </div>
                    </div>
                  ))
                )}
              </div>
            </section>

            <section className="org-panel">
              <h2 className="org-panel__title org-panel__title--sm">Your Active Gigs</h2>
              <div className="org-gig-list">
                {listings.length === 0 ? (
                  <p className="org-muted">No listings yet.</p>
                ) : (
                  listings.map((g) => (
                    <div key={g.id} className="org-gig-card">
                      <div className="org-gig-card__thumb">
                        {g.image_url && g.image_url !== 'null.jpg' ? (
                          <img src={g.image_url} alt="" />
                        ) : (
                          <span className="org-gig-card__placeholder">No image</span>
                        )}
                      </div>
                      <div className="org-gig-card__body">
                        <div className="org-gig-card__title">{g.title}</div>
                        <div className="org-gig-card__price">
                          From ${Number(g.base_price).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </div>
                        <span className="org-gig-card__status">Paused</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </section>
          </div>

          <section className="org-panel">
            <div className="org-panel__head">
              <h2 className="org-panel__title">Action Required: Pending Orders</h2>
              {pending.length > 0 && (
                <span className="org-pill org-pill--warn">{pending.length} Pending</span>
              )}
            </div>
            <div className="org-table-wrap">
              <table className="org-table">
                <thead>
                  <tr>
                    <th>Order ID</th>
                    <th>Customer</th>
                    <th>Event Date</th>
                    <th>Service Requested</th>
                    <th>Total Price</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {pending.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="org-table__empty">
                        No pending orders.
                      </td>
                    </tr>
                  ) : (
                    pending.map((ev) => (
                      <tr key={ev.id}>
                        <td>{ev.id}</td>
                        <td>{ev.customer_name || ev.customer_id || '—'}</td>
                        <td>{ev.event_date != null ? formatDate(ev.event_date) : 'N/A'}</td>
                        <td>{ev.service_title || 'N/A'}</td>
                        <td>
                          {ev.order_total != null
                            ? `$${Number(ev.order_total).toFixed(2)}`
                            : '$0.00'}
                        </td>
                        <td>
                          <div className="org-actions">
                            <button
                              type="button"
                              className="org-btn org-btn--success org-btn--sm"
                              disabled={actionId === ev.id}
                              onClick={() => respond(ev.id, 'confirm')}
                            >
                              Confirm
                            </button>
                            <button
                              type="button"
                              className="org-btn org-btn--danger org-btn--sm"
                              disabled={actionId === ev.id}
                              onClick={() => respond(ev.id, 'decline')}
                            >
                              Decline
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section className="org-panel org-panel--footer">
            <h2 className="org-panel__title org-panel__title--sm">Completed Event History</h2>
            <div className="org-table-wrap">
              <table className="org-table">
                <thead>
                  <tr>
                    <th>Event ID</th>
                    <th>Date</th>
                    <th>Customer</th>
                    <th>Order total</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {completed.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="org-table__empty">
                        No completed events yet.
                      </td>
                    </tr>
                  ) : (
                    completed.map((ev) => (
                      <tr key={ev.id}>
                        <td>{ev.id}</td>
                        <td>{formatDate(ev.event_date)}</td>
                        <td>{ev.customer_name || ev.customer_id}</td>
                        <td>
                          {ev.order_total != null
                            ? `$${Number(ev.order_total).toFixed(2)}`
                            : '—'}
                        </td>
                        <td>
                          <button
                            type="button"
                            className="org-btn org-btn--sm"
                            disabled={actionId === ev.id}
                            onClick={() => complete(ev.id)}
                          >
                            {actionId === ev.id ? '…' : 'Mark completed'}
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
            <p className="org-hint">
              Confirm pending orders first. Mark completed after the event so customers can rate you.
            </p>
          </section>
        </>
      )}
    </div>
  );
}
