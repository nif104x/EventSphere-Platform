const SESSION_KEY = 'eventsphere_customer_session';
const ORG_KEY = 'eventsphere_organizer_org_id';

/** @returns {{ customer_id: string, full_name: string, username: string, access_token: string } | null} */
export function getCustomerSession() {
  if (typeof localStorage === 'undefined') return null;
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw);
    if (!data?.customer_id) return null;
    return data;
  } catch {
    return null;
  }
}

export function setCustomerSession({ customer_id, full_name, username, access_token }) {
  localStorage.setItem(
    SESSION_KEY,
    JSON.stringify({ customer_id, full_name, username, access_token })
  );
}

export function clearCustomerSession() {
  localStorage.removeItem(SESSION_KEY);
}

export function getCustomerId() {
  const s = getCustomerSession();
  return s?.customer_id ?? null;
}

export function getCustomerAccessToken() {
  return getCustomerSession()?.access_token ?? null;
}

export function getOrganizerOrgId() {
  if (typeof localStorage === 'undefined') return 'ORG-01';
  return localStorage.getItem(ORG_KEY) || 'ORG-01';
}

export function setOrganizerOrgId(id) {
  localStorage.setItem(ORG_KEY, id);
}
