import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../api/client';

export default function OfferSign() {
  const { offerId } = useParams();
  const [offer, setOffer] = useState(null);
  const [signerName, setSignerName] = useState('');
  const [error, setError] = useState('');
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.ensureCsrf().catch(() => {});
    api.getPublicOffer(offerId)
      .then(setOffer)
      .catch((err) => setError(err.message));
  }, [offerId]);

  const sign = async (accept) => {
    setBusy(true);
    setError('');
    try {
      await api.signOffer(offerId, { signer_name: signerName, accept });
      setDone(true);
      setOffer((o) => ({ ...o, status: accept ? 'accepted' : 'declined' }));
    } catch (err) {
      setError(err.data?.detail || err.message);
    } finally {
      setBusy(false);
    }
  };

  if (error && !offer) {
    return (
      <div className="careers-layout">
        <main className="careers-main"><div className="alert alert-danger">{error}</div></main>
      </div>
    );
  }

  if (!offer) {
    return (
      <div className="careers-layout text-center py-5">
        <div className="spinner-border text-primary" role="status" />
      </div>
    );
  }

  if (done || offer.status === 'accepted') {
    return (
      <div className="careers-layout">
        <main className="careers-main careers-apply-success">
          <div className="card"><div className="card-body text-center py-5">
            <i className="bi bi-check-circle display-4 text-success mb-3" />
            <h2>Offer accepted</h2>
            <p className="text-muted">Thank you, {offer.signer_name || signerName}. We look forward to your start on {offer.start_date}.</p>
          </div></div>
        </main>
      </div>
    );
  }

  return (
    <div className="careers-layout">
      <header className="careers-header careers-header-compact">
        <div className="careers-header-inner">
          <span className="careers-back">Job offer</span>
        </div>
      </header>
      <main className="careers-main">
        <div className="card">
          <div className="card-body">
            <h1 className="h4 mb-3">{offer.job_title}</h1>
            <p className="text-muted">{offer.department} · {offer.currency} {offer.salary} · Start {offer.start_date}</p>
            <div className="recruitment-offer-body text-pre-wrap mb-4">{offer.body}</div>
            {error && <div className="alert alert-danger py-2">{error}</div>}
            {offer.status === 'sent' && (
              <>
                <label className="form-label">Full legal name (signature)</label>
                <input className="form-control mb-3" value={signerName} onChange={(e) => setSignerName(e.target.value)} />
                <div className="d-flex gap-2">
                  <button type="button" className="btn btn-success" disabled={busy || !signerName.trim()} onClick={() => sign(true)}>Accept offer</button>
                  <button type="button" className="btn btn-outline-danger" disabled={busy || !signerName.trim()} onClick={() => sign(false)}>Decline</button>
                </div>
              </>
            )}
            {offer.status !== 'sent' && (
              <p className="text-muted">This offer is not available for signing (status: {offer.status}).</p>
            )}
            <Link to="/careers" className="btn btn-link btn-sm mt-3">Back to careers</Link>
          </div>
        </div>
      </main>
    </div>
  );
}
