import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function PermissionRoute({ children, check }) {
  const { user } = useAuth();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (typeof check === 'function' && !check(user)) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}
