import axios from 'axios';
import { clearCustomerSession, getCustomerAccessToken } from './customerStorage';

// Dev: Vite proxies `/api` → FastAPI. Prod default: call API on :8000 unless VITE_API_BASE is set.
const raw =
  import.meta.env.VITE_API_BASE ||
  (import.meta.env.DEV ? '/api' : 'http://localhost:8000/api');
const API_BASE = raw.replace(/\/$/, '');

const api = axios.create({
  baseURL: API_BASE,
});

api.interceptors.request.use((config) => {
  const token = getCustomerAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err.response?.status;
    const url = String(err.config?.url || '');
    const hadAuth = Boolean((err.config?.headers?.Authorization || '').toString().trim());
    if (
      status === 401 &&
      hadAuth &&
      !url.includes('customer/login') &&
      typeof window !== 'undefined'
    ) {
      clearCustomerSession();
      const next = `${window.location.origin}/customer/login`;
      if (window.location.pathname !== '/customer/login') {
        window.location.assign(next);
      }
    }
    return Promise.reject(err);
  },
);

export const loginCustomer = (body) => api.post('/customer/login', body);

export const getOrganizers = () => api.get('/organizers');
export const getServices = (orgId) => api.get(`/services/${orgId}`);
export const getAddons = (listingId) => api.get(`/addons/${listingId}`);
export const createEvent = (data) => api.post('/events', data);
export const createOrder = (data) => api.post('/orders', data);
export const createPaymentCheckout = (data) => api.post('/payment/stripe-checkout', data);
export const completePaymentSession = (data) => api.post('/payment/complete-session', data);
export const getDashboard = (customerId) => api.get(`/customer/${customerId}/dashboard`);
export const getEventHistory = (customerId) =>
  api.get(`/customer/${customerId}/event-history`);
/** Customer marks their own confirmed event complete (Bearer required). */
export const markEventComplete = (eventId) => api.patch(`/events/${eventId}/complete`);
export const submitRating = (eventId, data) => api.post(`/events/${eventId}/rating`, data);
export const getOrganizerAnalytics = (orgId) => api.get(`/organizer/${orgId}/analytics`);
export const getOrganizerEvents = (orgId) => api.get(`/organizer/${orgId}/events`);
export const getOrganizerReviews = (orgId) => api.get(`/organizer/${orgId}/reviews`);
export const getOrganizerListings = (orgId) => api.get(`/organizer/${orgId}/listings`);
export const respondToEvent = (eventId, data) =>
  api.patch(`/events/${eventId}/organizer-response`, data);

export const getChatRooms = () => api.get('/customer/chat/rooms');
export const openChatRoomForEvent = (event_id) =>
  api.post('/customer/chat/rooms/open', { event_id });
export const getChatMessages = (roomId) =>
  api.get(`/customer/chat/rooms/${encodeURIComponent(roomId)}/messages`);
export const sendChatMessage = (room_id, text) =>
  api.post('/customer/chat/messages', { room_id, text });

export default api;
