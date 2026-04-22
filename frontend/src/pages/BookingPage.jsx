import { useState, useEffect, useMemo } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { getServices, getAddons, createEvent, createOrder } from '../api';
import { getCustomerId } from '../customerStorage';

const emptyBlock = () => ({
  services: [],
  addons: [],
  selectedService: '',
  selectedAddons: [],
  loading: true,
});

const BookingPage = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const organizers = useMemo(() => {
    const st = location.state || {};
    if (Array.isArray(st.organizers) && st.organizers.length) return st.organizers;
    if (st.orgId && st.organizer) {
      return [{ ...st.organizer, org_id: st.orgId }];
    }
    return [];
  }, [location.state]);

  const [byOrg, setByOrg] = useState({});
  const [eventDate, setEventDate] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!organizers.length) return;
    let cancelled = false;
    (async () => {
      const next = {};
      for (const o of organizers) {
        try {
          const { data } = await getServices(o.org_id);
          if (cancelled) return;
          next[o.org_id] = { ...emptyBlock(), services: data, loading: false };
        } catch (e) {
          console.error(e);
          next[o.org_id] = { ...emptyBlock(), services: [], loading: false };
        }
      }
      if (!cancelled) setByOrg(next);
    })();
    return () => {
      cancelled = true;
    };
  }, [organizers]);

  const updateOrg = (orgId, patch) => {
    setByOrg((prev) => ({
      ...prev,
      [orgId]: { ...prev[orgId], ...patch },
    }));
  };

  const onServiceChange = async (orgId, listingId) => {
    if (!listingId) {
      updateOrg(orgId, { selectedService: '', addons: [], selectedAddons: [] });
      return;
    }
    updateOrg(orgId, { selectedService: listingId, selectedAddons: [] });
    try {
      const { data } = await getAddons(listingId);
      updateOrg(orgId, { addons: data });
    } catch (e) {
      console.error(e);
      updateOrg(orgId, { addons: [] });
    }
  };

  const toggleAddon = (orgId, addonId) => {
    setByOrg((prev) => {
      const b = prev[orgId];
      if (!b) return prev;
      const set = new Set(b.selectedAddons);
      if (set.has(addonId)) set.delete(addonId);
      else set.add(addonId);
      return {
        ...prev,
        [orgId]: { ...b, selectedAddons: [...set] },
      };
    });
  };

  const computeLineTotal = (orgId) => {
    const b = byOrg[orgId];
    if (!b?.selectedService) return 0;
    const svc = b.services.find((s) => s.id === b.selectedService);
    if (!svc) return 0;
    const base = parseFloat(svc.base_price);
    const addonsTotal = b.selectedAddons.reduce((sum, id) => {
      const a = b.addons.find((x) => x.id === id);
      return sum + (a ? parseFloat(a.price) : 0);
    }, 0);
    return base + addonsTotal;
  };

  const grandTotal = organizers.reduce((sum, o) => sum + computeLineTotal(o.org_id), 0);

  const handleBook = async () => {
    if (!eventDate) {
      alert('Choose an event date.');
      return;
    }
    const customerId = getCustomerId();
    for (const o of organizers) {
      const b = byOrg[o.org_id];
      if (!b?.selectedService) {
        alert(`Select a service for ${o.company_name}.`);
        return;
      }
    }

    setSubmitting(true);
    try {
      for (const o of organizers) {
        const b = byOrg[o.org_id];
        const svc = b.services.find((s) => s.id === b.selectedService);
        const addonsTotal = b.selectedAddons.reduce((sum, id) => {
          const a = b.addons.find((x) => x.id === id);
          return sum + (a ? parseFloat(a.price) : 0);
        }, 0);
        const base = parseFloat(svc.base_price);
        const totalPrice = base + addonsTotal;

        const eventRes = await createEvent({
          customer_id: customerId,
          org_id: o.org_id,
          event_date: eventDate,
        });
        await createOrder({
          event_id: eventRes.data.event_id,
          listing_id: svc.id,
          base_price: base,
          addons_cost: addonsTotal,
          total_price: totalPrice,
        });
      }
      alert(`Booking confirmed! Total: $${grandTotal.toFixed(2)}`);
      navigate('/dashboard');
    } catch (err) {
      console.error(err);
      alert('Booking failed. Check the API and database.');
    }
    setSubmitting(false);
  };

  if (!organizers.length) {
    return (
      <div className="page-wrap org-page es-page es-page--book es-page--book-empty">
        <nav className="es-book-crumb" aria-label="Breadcrumb">
          <Link to="/customer">Customer</Link>
          <span className="es-book-crumb__sep">/</span>
          <span>Book</span>
        </nav>
        <h1 className="es-page-title">Book</h1>
        <div className="es-book-empty-panel">
          <p className="muted es-book-empty-panel__lead">
            No organizers selected. Start from the customer home and choose vendors to book.
          </p>
          <button type="button" className="btn primary" onClick={() => navigate('/customer')}>
            Back to customer home
          </button>
        </div>
      </div>
    );
  }

  const ready =
    eventDate &&
    organizers.every((o) => {
      const b = byOrg[o.org_id];
      return b && !b.loading && b.selectedService;
    });

  return (
    <div className="page-wrap org-page booking-page es-page es-page--book">
      <div className="es-book-layout">
        <div className="es-book-main">
          <nav className="es-book-crumb" aria-label="Breadcrumb">
            <Link to="/customer">Customer</Link>
            <span className="es-book-crumb__sep">/</span>
            <span>Checkout</span>
          </nav>
          <header className="es-book-intro">
            <h1 className="es-page-title">Complete your booking</h1>
            <p className="muted es-book-intro__lead">
              One shared event date applies to all selected organizers below.
            </p>
          </header>

          {organizers.map((o) => {
            const b = byOrg[o.org_id] || { ...emptyBlock() };
            const addonsTotal = b.selectedAddons.reduce((sum, id) => {
              const a = b.addons.find((x) => x.id === id);
              return sum + (a ? parseFloat(a.price) : 0);
            }, 0);
            const svc = b.services.find((s) => s.id === b.selectedService);

            return (
              <section key={o.org_id} className="booking-block">
                <h2>{o.company_name}</h2>
                {b.loading ? (
                  <p>Loading services…</p>
                ) : (
                  <>
                    <div className="field">
                      <label htmlFor={`svc-${o.org_id}`}>Service</label>
                      <select
                        id={`svc-${o.org_id}`}
                        value={b.selectedService}
                        onChange={(e) => onServiceChange(o.org_id, e.target.value)}
                      >
                        <option value="">Choose a service…</option>
                        {b.services.map((s) => (
                          <option key={s.id} value={s.id}>
                            {s.title} — ${s.base_price}
                          </option>
                        ))}
                      </select>
                    </div>
                    {b.addons.length > 0 && (
                      <div className="field">
                        <span className="label">Add-ons from this vendor</span>
                        <ul className="addon-list">
                          {b.addons.map((addon) => (
                            <li key={addon.id}>
                              <label>
                                <input
                                  type="checkbox"
                                  checked={b.selectedAddons.includes(addon.id)}
                                  onChange={() => toggleAddon(o.org_id, addon.id)}
                                />
                                {addon.name} (+${addon.price})
                              </label>
                            </li>
                          ))}
                        </ul>
                        <p className="muted">Add-ons subtotal: ${addonsTotal.toFixed(2)}</p>
                      </div>
                    )}
                    {svc && (
                      <p className="line-total">
                        <strong>
                          Subtotal for {o.company_name}: ${computeLineTotal(o.org_id).toFixed(2)}
                        </strong>
                      </p>
                    )}
                  </>
                )}
              </section>
            );
          })}
        </div>

        <aside className="es-book-aside" aria-label="Date and order total">
          <div className="booking-date-card es-book-aside__date">
            <div className="field">
              <label htmlFor="event-date">Event date</label>
              <input
                id="event-date"
                type="date"
                value={eventDate}
                onChange={(e) => setEventDate(e.target.value)}
              />
            </div>
          </div>
          <div className="booking-footer es-book-aside__summary">
            <p className="grand-total">Grand total: ${grandTotal.toFixed(2)}</p>
            <button type="button" className="btn primary" disabled={!ready || submitting} onClick={handleBook}>
              {submitting ? 'Confirming…' : 'Confirm order'}
            </button>
          </div>
        </aside>
      </div>
    </div>
  );
};

export default BookingPage;
