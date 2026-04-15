import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import OrganizerCard from '../components/OrganizerCard';
import { getOrganizers } from '../api';

const HomePage = () => {
  const [organizers, setOrganizers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedIds, setSelectedIds] = useState(() => new Set());
  const navigate = useNavigate();

  useEffect(() => {
    getOrganizers()
      .then((res) => {
        setOrganizers(res.data);
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

  if (loading) return <div className="page-wrap">Loading organizers...</div>;

  return (
    <div className="page-wrap">
      <header className="page-header">
        <h1>Choose your organizers</h1>
        <p className="muted">
          Select one or more vendors, then continue to pick services, add-ons, and your event date.
        </p>
        <div className="toolbar">
          <button type="button" className="btn primary" onClick={goToBooking} disabled={selectedIds.size === 0}>
            Continue to booking ({selectedIds.size} selected)
          </button>
        </div>
      </header>
      <div className="card-grid">
        {organizers.map((org) => (
          <OrganizerCard
            key={org.org_id}
            organizer={org}
            selected={selectedIds.has(org.org_id)}
            onToggleSelect={() => toggleOrg(org.org_id)}
          />
        ))}
      </div>
    </div>
  );
};

export default HomePage;
