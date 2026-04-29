/** Shared “latest first” helpers for customer portal lists. */

function parseEventDateMs(d) {
  if (d == null) return 0;
  const s = String(d).slice(0, 10);
  const t = Date.parse(`${s}T12:00:00`);
  return Number.isNaN(t) ? 0 : t;
}

/** Events: newest event date first, then id descending. */
export function sortCustomerEventsLatest(events) {
  return [...(events || [])].sort((a, b) => {
    const dt = parseEventDateMs(b.event_date) - parseEventDateMs(a.event_date);
    if (dt !== 0) return dt;
    return String(b.id || '').localeCompare(String(a.id || ''), undefined, { numeric: true });
  });
}

/** Orders: API uses id like ORD-…; descending id approximates latest created. */
export function sortCustomerOrdersLatest(orders) {
  return [...(orders || [])].sort((a, b) =>
    String(b.id || '').localeCompare(String(a.id || ''), undefined, { numeric: true }),
  );
}

/** Stripe checkout lines: latest order id first. */
export function sortPaymentLinesLatest(lines) {
  return [...(lines || [])].sort((a, b) =>
    String(b.order_id || '').localeCompare(String(a.order_id || ''), undefined, { numeric: true }),
  );
}

/** Chat rooms: server orders by id DESC; keep same. */
export function sortChatRoomsLatest(rooms) {
  return [...(rooms || [])].sort((a, b) =>
    String(b.room_id || '').localeCompare(String(a.room_id || ''), undefined, { numeric: true }),
  );
}

/** Organizers: most reviewed / highest rated first, then name. */
export function sortOrganizersLatest(organizers) {
  return [...(organizers || [])].sort((a, b) => {
    const rc = Number(b.review_count || 0) - Number(a.review_count || 0);
    if (rc !== 0) return rc;
    const ar = Number(b.avg_rating || 0) - Number(a.avg_rating || 0);
    if (ar !== 0) return ar;
    return String(a.company_name || '').localeCompare(String(b.company_name || ''), undefined, {
      sensitivity: 'base',
    });
  });
}

export function sortCustomerServicesLatest(services) {
  return [...(services || [])].sort((a, b) =>
    String(a.title || '').localeCompare(String(b.title || ''), undefined, { sensitivity: 'base' }),
  );
}

export function sortCustomerAddonsLatest(addons) {
  return [...(addons || [])].sort((a, b) =>
    String(a.name || '').localeCompare(String(b.name || ''), undefined, { sensitivity: 'base' }),
  );
}
