import { Navigate, Outlet } from 'react-router-dom';
import { getCustomerSession } from '../customerStorage';

export default function CustomerProtectedLayout() {
  if (!getCustomerSession()?.customer_id) {
    return <Navigate to="/customer/login" replace />;
  }
  return <Outlet />;
}
