import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import OpsAlertsCard from '../components/ops/OpsAlertsCard';
import OpsBackupsCard from '../components/ops/OpsBackupsCard';
import OpsJobsCard from '../components/ops/OpsJobsCard';
import OpsRunbooksPanel from '../components/ops/OpsRunbooksPanel';
import OpsSLOCard from '../components/ops/OpsSLOCard';
import OpsUsageCard from '../components/ops/OpsUsageCard';
import SettingsBackLink from '../components/SettingsBackLink';

export default function OpsCenter() {
  const { user } = useAuth();
  const [ops, setOps] = useState(null);
  const [slos, setSlos] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user?.is_admin) {
      setLoading(false);
      return undefined;
    }

    let cancelled = false;
    setLoading(true);
    setError('');

    (async () => {
      const errors = [];
      try {
        const [opsResult, sloResult] = await Promise.allSettled([
          api.getOpsStatus(),
          api.getSLOMetrics(),
        ]);
        if (cancelled) return;

        if (opsResult.status === 'fulfilled') {
          setOps(opsResult.value);
        } else {
          errors.push(opsResult.reason?.message || 'Failed to load ops status');
          setOps(null);
        }

        if (sloResult.status === 'fulfilled') {
          setSlos(sloResult.value);
        } else {
          errors.push(sloResult.reason?.message || 'Failed to load SLO metrics');
          setSlos(null);
        }

        if (errors.length) {
          setError(errors.join(' · '));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [user]);

  if (!user?.is_admin) return <Navigate to="/dashboard" replace />;

  return (
    <div>
      <SettingsBackLink />
      <h1 className="page-heading mb-3">
        <i className="bi bi-hdd-rack" aria-hidden="true" /> Operations Center
      </h1>
      <p className="text-muted mb-4">
        Background jobs, backups, SLO health, alert history, and incident runbooks.
      </p>

      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}
      {loading ? (
        <div className="text-center py-5" role="status">
          <div className="spinner-border text-primary" aria-hidden="true" />
          <span className="visually-hidden">Loading operations status</span>
        </div>
      ) : (
        <div className="row g-3">
          <OpsJobsCard ops={ops} />
          <OpsSLOCard slos={slos} />
          <OpsBackupsCard ops={ops} />
          <OpsAlertsCard alerts={ops?.alerts} />
          <OpsUsageCard usage={ops?.usage} />
          <OpsRunbooksPanel runbooks={ops?.runbooks} />
        </div>
      )}
    </div>
  );
}
