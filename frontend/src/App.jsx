import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import HomePage from './pages/HomePage';
import BookingPage from './pages/BookingPage';
import DashboardPage from './pages/DashboardPage';
import OrganizerDashboardPage from './pages/OrganizerDashboardPage';
import OrganizerPlaceholderPage from './pages/OrganizerPlaceholderPage';
import OrganizerLayout from './layouts/OrganizerLayout';
import CustomerLayout from './layouts/CustomerLayout';

function AppShell() {
  return (
    <Routes>
      <Route element={<CustomerLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/book" element={<BookingPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
      </Route>
      <Route path="/organizer" element={<OrganizerLayout />}>
        <Route index element={<OrganizerDashboardPage />} />
        <Route
          path="create-gig"
          element={<OrganizerPlaceholderPage title="Create Gig" pageClass="es-page--organizer-create" />}
        />
        <Route
          path="messages"
          element={<OrganizerPlaceholderPage title="Messages" pageClass="es-page--organizer-messages" />}
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
