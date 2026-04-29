import { sortCustomerEventsLatest, sortCustomerOrdersLatest } from './customerSort';
import { isConfirmedEventStatus, isPendingEventStatus } from './eventUi';

function isOrderPaid(order) {
  return String(order?.payment_status || '').toLowerCase() === 'paid';
}

/**
 * Normalized slices for customer dashboard / payments-due page.
 * @param {{ events?: unknown[], orders?: unknown[] }} data
 */
export function getSortedDashboardSlices(data) {
  const sortedEvents = sortCustomerEventsLatest(data?.events || []);
  const sortedOrders = sortCustomerOrdersLatest(data?.orders || []);
  const eventsById = Object.fromEntries(sortedEvents.map((e) => [e.id, e]));

  const payableOrders = sortedOrders.filter((order) => {
    if (isOrderPaid(order)) return false;
    const ev = eventsById[order.event_id];
    return Boolean(ev && isConfirmedEventStatus(ev.status));
  });

  const awaitingVendorOrders = sortedOrders.filter((order) => {
    if (isOrderPaid(order)) return false;
    const ev = eventsById[order.event_id];
    return Boolean(ev && isPendingEventStatus(ev.status));
  });

  return {
    sortedEvents,
    sortedOrders,
    eventsById,
    payableOrders,
    awaitingVendorOrders,
  };
}
