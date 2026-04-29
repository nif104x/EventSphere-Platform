/**
 * API / drivers sometimes return booleans as strings or other truthy forms.
 */
export function truthyApiFlag(v) {
  if (v === true || v === 1) return true;
  if (v === false || v === 0 || v == null) return false;
  const s = String(v).trim().toLowerCase();
  return s === 'true' || s === 't' || s === '1' || s === 'yes';
}

/** Normalize event status from API (enum name, PG label, etc.) */
export function normalizedEventStatus(status) {
  if (status == null) return '';
  let s = String(status).trim();
  s = s.replace(/^EventStatusEnum\./i, '');
  s = s.replace(/^['"]|['"]$/g, '');
  return s.trim().toLowerCase();
}

export function isConfirmedEventStatus(status) {
  return normalizedEventStatus(status) === 'confirmed';
}

export function isPendingEventStatus(status) {
  return normalizedEventStatus(status) === 'pending';
}

/** Confirmed + all orders paid (server sets can_mark_complete). */
export function canMarkEventComplete(event) {
  if (!event) return false;
  return truthyApiFlag(event.can_mark_complete);
}
