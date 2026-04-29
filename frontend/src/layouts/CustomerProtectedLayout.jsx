import { Navigate, Outlet } from 'react-router-dom';
import { getCustomerSession } from '../customerStorage';

export default function CustomerProtectedLayout() {
  const s = getCustomerSession();
  const token = (s?.access_token || '').trim();
  if (!s?.customer_id || !token || token === 'undefined' || token === 'null') {
    return <Navigate to="/customer/login" replace />;
  }
  return <Outlet />;
}
