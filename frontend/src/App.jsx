import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import CustomerLoginPage from './pages/CustomerLoginPage';
import HomePage from './pages/HomePage';
import BookingPage from './pages/BookingPage';
import DashboardPage from './pages/DashboardPage';
import CustomerChatPage from './pages/CustomerChatPage';
import EventHistoryPage from './pages/EventHistoryPage';
import PaymentPage from './pages/PaymentPage';
import PaymentDonePage from './pages/PaymentDonePage';
import OrdersDuePage from './pages/OrdersDuePage';
import OrganizerDashboardPage from './pages/OrganizerDashboardPage';
import OrganizerBridgePage from './pages/OrganizerBridgePage';
import OrganizerLayout from './layouts/OrganizerLayout';
import CustomerLayout from './layouts/CustomerLayout';
import CustomerProtectedLayout from './layouts/CustomerProtectedLayout';

function AppShell() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/customer/login" element={<CustomerLoginPage />} />
      <Route element={<CustomerProtectedLayout />}>
        <Route element={<CustomerLayout />}>
          <Route path="/customer" element={<HomePage />} />
          <Route path="/book" element={<BookingPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/customer/orders-due" element={<OrdersDuePage />} />
          <Route path="/customer/history" element={<EventHistoryPage />} />
          <Route path="/customer/payment" element={<PaymentPage />} />
          <Route path="/customer/payment/done" element={<PaymentDonePage />} />
          <Route path="/customer/chat" element={<CustomerChatPage />} />
        </Route>
      </Route>
      <Route path="/organizer" element={<OrganizerLayout />}>
        <Route index element={<OrganizerDashboardPage />} />
        <Route
          path="create-gig"
          element={
            <OrganizerBridgePage title="Create Gig" path="/organizer/creategig" pageClass="es-page--organizer-create" />
          }
        />
        <Route
          path="messages"
          element={
            <OrganizerBridgePage title="Messages" path="/organizer/message" pageClass="es-page--organizer-messages" />
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <Router>
      <AppShell />
    </Router>
  );
}

export default App;
