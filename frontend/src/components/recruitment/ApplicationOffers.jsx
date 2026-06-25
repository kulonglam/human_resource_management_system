import { useCallback, useEffect, useState } from 'react';
import { api } from '../../api/client';

export default function ApplicationOffers({ applicationId, canManage }) {
  const [offers, setOffers] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [form, setForm] = useState({ template: '', salary: '', start_date: '' });
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const [offerRows, templateRows] = await Promise.all([
      api.list('offers', `application=${applicationId}`),
      api.list('offer-templates'),
    ]);
    setOffers(offerRows);
    setTemplates(templateRows);
    if (templateRows[0] && !form.template) {
      setForm((f) => ({ ...f, template: String(templateRows[0].id) }));
    }
  }, [applicationId, form.template]);

  useEffect(() => {
    load();
  }, [load]);

  const createOffer = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.createOfferFromTemplate({
        application: Number(applicationId),
        template: Number(form.template),
        salary: form.salary,
        start_date: form.start_date,
      });
      load();
    } finally {
      setBusy(false);
    }
  };

  const runOfferAction = async (offerId, action) => {
    await api.offerAction(offerId, action);
    load();
  };

  const copySignLink = (offerId) => {
    const url = `${window.location.origin}/offers/${offerId}`;
    navigator.clipboard.writeText(url);
  };

  return (
    <div className="card mb-3">
      <div className="card-body">
        <h5 className="card-title">Offers</h5>
        {offers.map((offer) => (
          <div className="recruitment-offer mb-3 p-3 border rounded" key={offer.id}>
            <div className="d-flex justify-content-between align-items-start">
              <div>
                <strong>{offer.job_title}</strong>
                <div className="small text-muted">{offer.currency} {offer.salary} · Start {offer.start_date}</div>
              </div>
              <span className="badge bg-secondary">{offer.status_display || offer.status}</span>
            </div>
            {canManage && (
              <div className="d-flex flex-wrap gap-1 mt-2">
                {offer.status === 'draft' && <button type="button" className="btn btn-outline-primary btn-sm" onClick={() => runOfferAction(offer.id, 'submit')}>Submit for approval</button>}
                {offer.status === 'pending_approval' && <button type="button" className="btn btn-outline-success btn-sm" onClick={() => runOfferAction(offer.id, 'approve')}>Approve</button>}
                {['approved', 'draft'].includes(offer.status) && <button type="button" className="btn btn-outline-info btn-sm" onClick={() => runOfferAction(offer.id, 'send')}>Send to candidate</button>}
                {offer.status === 'sent' && <button type="button" className="btn btn-outline-secondary btn-sm" onClick={() => copySignLink(offer.id)}>Copy sign link</button>}
              </div>
            )}
          </div>
        ))}
        {canManage && templates.length > 0 && (
          <form onSubmit={createOffer} className="border-top pt-3">
            <p className="small text-muted">Create offer from template</p>
            <div className="row g-2">
              <div className="col-md-4">
                <select className="form-select form-select-sm" value={form.template} onChange={(e) => setForm({ ...form, template: e.target.value })}>
                  {templates.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
                </select>
              </div>
              <div className="col-md-3">
                <input type="number" step="0.01" className="form-control form-control-sm" placeholder="Salary" required value={form.salary} onChange={(e) => setForm({ ...form, salary: e.target.value })} />
              </div>
              <div className="col-md-3">
                <input type="date" className="form-control form-control-sm" required value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} />
              </div>
              <div className="col-md-2">
                <button type="submit" className="btn btn-primary btn-sm w-100" disabled={busy}>Create</button>
              </div>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
