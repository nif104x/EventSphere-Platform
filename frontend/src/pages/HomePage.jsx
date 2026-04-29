import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getOrganizers } from '../api';
import { sortOrganizersLatest } from '../customerSort';

const HomePage = () => {
  const [organizers, setOrganizers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedIds, setSelectedIds] = useState(() => new Set());
  const navigate = useNavigate();

  useEffect(() => {
    getOrganizers()
      .then((res) => {
        setOrganizers(sortOrganizersLatest(res.data));
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching organizers:', err);
        setLoading(false);
      });
  }, []);

  const toggleOrg = (orgId) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(orgId)) next.delete(orgId);
      else next.add(orgId);
      return next;
    });
  };

  const goToBooking = () => {
    if (selectedIds.size === 0) {
      alert('Select at least one event organizer.');
      return;
    }
    const chosen = organizers.filter((o) => selectedIds.has(o.org_id));
    navigate('/book', { state: { organizers: chosen } });
  };

  if (loading) {
    return (
      <div className="page-wrap org-page es-page es-page--home org-muted">Loading organizers…</div>
    );
  }

  return (
    <div className="page-wrap org-page es-page es-page--home">
      <div className="es-home-top">
        <header className="page-header es-home-hero">
          <span className="es-home-hero__eyebrow">Step 1 · Customer</span>
          <h1 className="es-page-title">Choose your organizers</h1>
          <p className="muted es-home-hero__desc">
            Select one or more vendors, then continue to pick services, add-ons, and your event date. After the vendor
            confirms, open <Link to="/dashboard">My dashboard</Link> to <strong>pay</strong>, then{' '}
            <strong>mark the event complete</strong> and leave a rating.
          </p>
        </header>
        <aside className="es-home-aside" aria-label="Selection summary">
          <div className="es-home-meta" aria-live="polite">
            <span className="es-home-chip">{organizers.length} organizers</span>
            <span className="es-home-chip">{selectedIds.size} selected</span>
          </div>
          <div className="toolbar es-home-aside__actions">
            <button type="button" className="btn primary" onClick={goToBooking} disabled={selectedIds.size === 0}>
              Continue to booking ({selectedIds.size} selected)
            </button>
            <Link to="/dashboard" className="btn small">
              My dashboard
            </Link>
          </div>
        </aside>
      </div>

      <section className="dash-panel es-home-organizers-panel" aria-label="Organizer directory">
        <h2 className="es-page-title es-home-table-title">Organizers</h2>
        <p className="muted es-dash-table-caption">
          Sorted by review activity (most reviews first), then average rating.
        </p>
        {organizers.length === 0 ? (
          <p className="empty-state empty-state--tight">No organizers available.</p>
        ) : (
          <div className="es-customer-table-wrap">
            <table className="es-customer-table">
              <thead>
                <tr>
                  <th scope="col">Select</th>
                  <th scope="col">Company</th>
                  <th scope="col">Category</th>
                  <th scope="col">Avg rating</th>
                  <th scope="col">Reviews</th>
                  <th scope="col">Email</th>
                </tr>
              </thead>
              <tbody>
                {organizers.map((org) => (
                  <tr key={org.org_id}>
                    <td data-label="Select">
                      <input
                        type="checkbox"
                        checked={selectedIds.has(org.org_id)}
                        onChange={() => toggleOrg(org.org_id)}
                        aria-label={`Select ${org.company_name}`}
                      />
                    </td>
                    <td data-label="Company">
                      <strong>{org.company_name}</strong>
                      <div className="muted">
                        <code>{org.org_id}</code>
                      </div>
                    </td>
                    <td data-label="Category">{org.primary_category || '—'}</td>
                    <td data-label="Avg rating">{Number(org.avg_rating || 0).toFixed(2)}</td>
                    <td data-label="Reviews">{org.review_count ?? 0}</td>
                    <td data-label="Email">{org.email || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
};

export default HomePage;
