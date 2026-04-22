const CUSTOMER_KEY = 'eventsphere_customer_id';
const ORG_KEY = 'eventsphere_organizer_org_id';

const CUSTOMERS = [
  { id: 'CUST-01', label: 'Alice Smith (CUST-01)' },
  { id: 'CUST-02', label: 'Bob Jones (CUST-02)' },
  { id: 'CUST-03', label: 'Charlie Brown (CUST-03)' },
];

export function getCustomerId() {
  if (typeof localStorage === 'undefined') return 'CUST-01';
  return localStorage.getItem(CUSTOMER_KEY) || 'CUST-01';
}

export function setCustomerId(id) {
  localStorage.setItem(CUSTOMER_KEY, id);
}

export function getOrganizerOrgId() {
  if (typeof localStorage === 'undefined') return 'ORG-01';
  return localStorage.getItem(ORG_KEY) || 'ORG-01';
}

export function setOrganizerOrgId(id) {
  localStorage.setItem(ORG_KEY, id);
}

export { CUSTOMERS };
