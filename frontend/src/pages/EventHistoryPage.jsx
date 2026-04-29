import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getEventHistory, submitRating, markEventComplete } from '../api';
import { clearCustomerSession, getCustomerId } from '../customerStorage';
import { canMarkEventComplete, truthyApiFlag } from '../eventUi';
import { sortCustomerEventsLatest } from '../customerSort';

const formatDate = (d) => {
  if (d == null) return '';
  const s = typeof d === 'string' ? d : String(d);
  return s.slice(0, 10);
};

export default function EventHistoryPage() {
  const navigate = useNavigate();
  const customerId = getCustomerId();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [ratingFor, setRatingFor] = useState(null);
  const [stars, setStars] = useState(5);
  const [comment, setComment] = useState('');
  const [saving, setSaving] = useState(false);
  const [completingId, setCompletingId] = useState(null);

  const load = () => {
    setLoading(true);
    setError(null);
    getEventHistory(customerId)
      .then((res) => {
        setEvents(sortCustomerEventsLatest(res.data.events || []));
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
        setError('Could not load event history. Sign in again if this persists.');
        setLoading(false);
      });
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reload when customer changes
  }, [customerId]);

  const markComplete = async (eventId) => {
    setCompletingId(eventId);
    try {
      await markEventComplete(eventId);
      load();
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
      load();
    } catch (e) {
      console.error(e);
      const msg = e.response?.data?.detail || e.message || 'Failed to submit rating';
      alert(typeof msg === 'string' ? msg : JSON.stringify(msg));
    }
    setSaving(false);
  };

  if (loading) {
    return (
      <div className="page-wrap org-page es-page es-page--history org-muted">Loading your event history…</div>
    );
  }

  const ratedCount = events.filter((e) => e.rating != null).length;
  const pendingRate = events.filter((e) => truthyApiFlag(e.can_rate)).length;
  const markableCount = events.filter((e) => canMarkEventComplete(e)).length;

  return (
    <div className="page-wrap org-page es-page es-page--history">
      <header className="page-header">
        <h1 className="es-page-title">Events & ratings</h1>
        <p className="muted">
          The vendor <strong>confirms</strong> the booking; <strong>you</strong> mark the event{' '}
          <strong>complete</strong> when the service is delivered. <strong>You</strong> leave a{' '}
          <strong>rating</strong> only after you have marked it complete. Your reviews help other customers choose
          vendors.
        </p>
      </header>
      {error && <p className="error-banner">{error}</p>}

      <div className="es-history-kpis" aria-label="Summary">
        <div className="es-dash-kpi">
          <div className="es-dash-kpi__label">Total events</div>
          <div className="es-dash-kpi__value">{events.length}</div>
        </div>
        <div className="es-dash-kpi">
          <div className="es-dash-kpi__label">Mark complete</div>
          <div className="es-dash-kpi__value">{markableCount}</div>
        </div>
        <div className="es-dash-kpi">
          <div className="es-dash-kpi__label">Rated</div>
          <div className="es-dash-kpi__value">{ratedCount}</div>
        </div>
        <div className="es-dash-kpi es-dash-kpi--accent">
          <div className="es-dash-kpi__label">Awaiting your rating</div>
          <div className="es-dash-kpi__value">{pendingRate}</div>
        </div>
      </div>

      <section className="dash-panel es-history-panel">
        <div className="es-history-panel__head">
          <div>
            <h2>Past events</h2>
            <p className="muted es-dash-table-caption">Newest event dates first.</p>
          </div>
          <Link to="/dashboard" className="btn small">
            Back to dashboard
          </Link>
        </div>
        {events.length === 0 ? (
          <p className="empty-state empty-state--tight">No events yet. Book from the home page to see them here.</p>
        ) : (
          <div className="es-history-table-wrap">
            <table className="es-history-table">
              <thead>
                <tr>
                  <th scope="col">Date</th>
                  <th scope="col">Event</th>
                  <th scope="col">Vendor</th>
                  <th scope="col">Status</th>
                  <th scope="col">Your rating</th>
                  <th scope="col">Actions</th>
                </tr>
              </thead>
              <tbody>
                {events.map((ev) => (
                  <tr key={ev.id}>
                    <td data-label="Date">{formatDate(ev.event_date)}</td>
                    <td data-label="Event">
                      <span className="es-history-event-id">{ev.id}</span>
                      {ev.service_title ? (
                        <span className="es-history-service muted"> · {ev.service_title}</span>
                      ) : null}
                    </td>
                    <td data-label="Vendor">
                      <strong>{ev.company_name}</strong>
                      <span className="muted es-history-org"> ({ev.org_id})</span>
                    </td>
                    <td data-label="Status">
                      <span className="status-pill">{String(ev.status)}</span>
                    </td>
                    <td data-label="Rating">
                      {ev.rating != null ? (
                        <div className="es-history-rating-cell">
                          <span className="es-history-stars" aria-hidden>
                            {'★'.repeat(Number(ev.rating))}
                          </span>
                          <span className="muted"> {Number(ev.rating)}/5</span>
                          {ev.review_comment ? (
                            <div className="es-history-comment muted">
                              {ev.review_comment.length > 120
                                ? `${ev.review_comment.slice(0, 120)}…`
                                : ev.review_comment}
                            </div>
                          ) : null}
                        </div>
                      ) : (
                        <span className="muted">—</span>
                      )}
                    </td>
                    <td data-label="Actions">
                      <div className="es-history-actions">
                        {canMarkEventComplete(ev) && (
                          <button
                            type="button"
                            className="btn primary small"
                            disabled={completingId === ev.id}
                            onClick={() => markComplete(ev.id)}
                          >
                            {completingId === ev.id ? 'Updating…' : 'Mark event complete'}
                          </button>
                        )}
                        {truthyApiFlag(ev.can_rate) && (
                          <button type="button" className="btn primary small" onClick={() => openRate(ev)}>
                            Rate vendor
                          </button>
                        )}
                        <Link
                          to={`/customer/chat?eventId=${encodeURIComponent(ev.id)}`}
                          className="btn small"
                        >
                          Messages
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {ratingFor && (
        <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="hist-rate-title">
          <div className="modal">
            <h2 id="hist-rate-title">Rate {ratingFor.company_name}</h2>
            <p className="muted">Event {ratingFor.id}</p>
            <div className="field">
              <label htmlFor="hist-stars">Rating (1–5)</label>
              <select id="hist-stars" value={stars} onChange={(e) => setStars(Number(e.target.value))}>
                {[1, 2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>
                    {n} — {n === 1 ? 'Poor' : n === 5 ? 'Excellent' : '…'}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="hist-comment">Comment (optional)</label>
              <textarea
                id="hist-comment"
                rows={3}
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="How was the service?"
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
}
