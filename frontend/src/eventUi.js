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

/** Prefer API flag; fall back to status text so the button still shows if flags are wrong. */
export function canMarkEventComplete(event) {
  if (!event) return false;
  if (truthyApiFlag(event.can_mark_complete)) return true;
  return isConfirmedEventStatus(event.status);
}
