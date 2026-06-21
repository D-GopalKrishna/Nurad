import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import { isAuthenticated } from './api';
import Login from './pages/Login';
import Worklist from './pages/Worklist';
import './App.css';

function PrivateRoute({ children }) {
  return isAuthenticated() ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/worklist"
          element={
            <PrivateRoute>
              <Worklist />
            </PrivateRoute>
          }
        />
        <Route path="/" element={<Navigate to="/worklist" replace />} />
      </Routes>
    </Router>
  );
}
