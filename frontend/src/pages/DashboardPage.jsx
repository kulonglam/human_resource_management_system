import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import Dashboard from './Dashboard';

export default function DashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    api.getDashboard()
      .then(setData)
      .catch((err) => setError(err.message));
  }, []);

  if (error) {
    return <div className="alert alert-danger">{error}</div>;
  }

  if (!data) {
    return (
      <div className="text-center py-5">
        <div className="spinner-border text-primary" role="status" />
      </div>
    );
  }

  return <Dashboard data={data} user={user} />;
}
