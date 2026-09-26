import { useCallback, useEffect, useState } from 'react';
import { api } from '../api/client';
import { errorMessage } from '../utils/apiErrors';
import ConfirmModal from './ConfirmModal';
import ResourceFormModal from './resources/ResourceFormModal';
import ResourceDataTable from './resources/ResourceDataTable';
import ResourceTabs from './resources/ResourceTabs';
import ResourceToolbar from './resources/ResourceToolbar';

export default function ResourceManager({
  title,
  icon,
  tabs,
  lookupOptions = {},
  onLookupsRefresh,
  user,
  headerExtra,
  embedded = false,
}) {
  const [activeTab, setActiveTab] = useState(tabs[0]?.id);
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({});
  const [files, setFiles] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [selectedIds, setSelectedIds] = useState([]);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [formLookups, setFormLookups] = useState(lookupOptions);

  const tab = tabs.find((t) => t.id === activeTab) || tabs[0];
  const isEmployeeUser = user && !user.is_admin && !user.is_manager;

  const canUseTabCreate = tab?.canCreate !== false && tab?.formFields?.length > 0
    && !tab?.hideCreate
    && !(isEmployeeUser && tab?.hideCreateForEmployee)
    && !(tab?.adminOnly && !user?.is_admin);
  const canUseTabEdit = !(isEmployeeUser && tab?.hideEditForEmployee);

  const visibleFormFields = tab?.formFields?.filter((field) => {
    if (tab.selfServiceEmployee && isEmployeeUser && field.name === 'employee') {
      return false;
    }
    return true;
  }) || [];

  const load = useCallback(async () => {
    if (!tab) return;
    setLoading(true);
    setError('');
    try {
      const data = await api.list(tab.endpoint, tab.query || '');
      setRows(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [tab]);

  useEffect(() => {
    load();
    setSelectedIds([]);
  }, [load]);

  useEffect(() => {
    setFormLookups(lookupOptions);
  }, [lookupOptions]);

  const refreshLookups = async () => {
    if (typeof onLookupsRefresh !== 'function') return;
    const next = await onLookupsRefresh();
    if (next && typeof next === 'object') {
      setFormLookups(next);
    }
  };

  const toggleSelect = (id) => {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const toggleSelectAll = () => {
    if (selectedIds.length === rows.length) setSelectedIds([]);
    else setSelectedIds(rows.map((r) => r.id));
  };

  const requestBulkDelete = () => {
    if (!selectedIds.length) return;
    setConfirmDelete({
      mode: 'bulk',
      title: 'Delete selected records',
      message: `Delete ${selectedIds.length} selected record(s)? This cannot be undone.`,
    });
  };

  const openCreate = async () => {
    try {
      await refreshLookups();
    } catch {
      /* keep last known lookups */
    }
    const initial = {};
    tab.formFields?.forEach((f) => {
      initial[f.name] = f.default ?? (f.type === 'checkbox' ? false : '');
    });
    if (tab.selfServiceEmployee && isEmployeeUser && user?.linked_employee_id) {
      initial.employee = user.linked_employee_id;
    }
    setForm(initial);
    setFiles({});
    setEditing(null);
    setShowModal(true);
  };

  const openEdit = (row) => {
    const initial = {};
    tab.formFields?.forEach((f) => {
      if (f.type !== 'file') {
        initial[f.name] = f.type === 'checkbox' ? Boolean(row[f.name]) : (row[f.name] ?? '');
      }
    });
    setForm(initial);
    setFiles({});
    setEditing(row);
    setShowModal(true);
  };

  const handleChange = (e) => {
    const { name, value, type, files: inputFiles } = e.target;
    if (type === 'file') {
      setFiles((prev) => ({ ...prev, [name]: inputFiles[0] || null }));
      return;
    }
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const buildPayload = () => {
    const fields = visibleFormFields.length ? visibleFormFields : tab.formFields;
    const hasFiles = fields?.some((f) => f.type === 'file' && files[f.name]);
    if (!hasFiles) {
      const payload = { ...form };
      if (tab.selfServiceEmployee && isEmployeeUser && user?.linked_employee_id) {
        payload.employee = user.linked_employee_id;
      }
      fields?.forEach((f) => {
        if (f.type === 'time' && payload[f.name] === '') {
          payload[f.name] = null;
        }
        if (f.type === 'number' && payload[f.name] !== '') {
          payload[f.name] = Number(payload[f.name]);
        }
        if (f.type === 'select' && payload[f.name] !== '') {
          payload[f.name] = /^\d+$/.test(String(payload[f.name]))
            ? Number(payload[f.name])
            : payload[f.name];
        }
        if (f.type === 'checkbox') {
          payload[f.name] = Boolean(payload[f.name]);
        }
      });
      return payload;
    }

    const formData = new FormData();
    fields?.forEach((f) => {
      if (f.type === 'file') {
        if (files[f.name]) formData.append(f.name, files[f.name]);
        return;
      }
      let val = form[f.name];
      if (f.type === 'number' && val !== '') val = Number(val);
      if (f.type === 'select' && val !== '' && /^\d+$/.test(String(val))) val = Number(val);
      if (f.type === 'checkbox') val = val ? 'true' : 'false';
      if (val !== '' && val != null) formData.append(f.name, val);
    });
    return formData;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      const payload = buildPayload();
      if (payload.start_date && payload.end_date && payload.end_date < payload.start_date) {
        setError('end_date: End date cannot be before start date.');
        setSubmitting(false);
        return;
      }
      if (editing) {
        await api.update(tab.endpoint, editing.id, payload);
      } else {
        await api.create(tab.endpoint, payload);
      }
      await load();
      try {
        await refreshLookups();
      } catch {
        /* table already reloaded */
      }
      setShowModal(false);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const requestDelete = (row) => {
    setConfirmDelete({
      mode: 'single',
      row,
      title: 'Delete record',
      message: `Delete this ${tab?.label?.toLowerCase?.() || 'record'}? This cannot be undone.`,
    });
  };

  const confirmDeleteAction = async () => {
    if (!confirmDelete || !tab) return;
    setDeleting(true);
    setError('');
    try {
      if (confirmDelete.mode === 'bulk') {
        await Promise.all(selectedIds.map((id) => api.remove(tab.endpoint, id)));
        setSelectedIds([]);
      } else if (confirmDelete.row) {
        await api.remove(tab.endpoint, confirmDelete.row.id);
      }
      setConfirmDelete(null);
      await load();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setDeleting(false);
    }
  };

  const runAction = async (row, action) => {
    if (action.method === 'GET') {
      window.open(`/api/v1/${tab.endpoint}/${row.id}/${action.name}/`, '_blank');
      return;
    }
    try {
      await api.action(tab.endpoint, row.id, action.name, action.payload || {});
      load();
    } catch (err) {
      setError(errorMessage(err));
    }
  };

  const handleImportCsv = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    setImporting(true);
    setError('');
    setImportResult(null);
    try {
      const result = await api.importAttendanceCsv(file);
      setImportResult(result);
      await load();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setImporting(false);
    }
  };

  const columns = tab.columns || (rows[0] ? Object.keys(rows[0]).slice(0, 6) : []);

  return (
    <div className={embedded ? 'resource-shell resource-shell--embedded' : 'resource-shell page-shell'}>
      {!embedded && (
        <ResourceToolbar
          title={title}
          icon={icon}
          tab={tab}
          user={user}
          canUseTabCreate={canUseTabCreate}
          importing={importing}
          onCreate={openCreate}
          onImportCsv={handleImportCsv}
        />
      )}

      {embedded && canUseTabCreate && (
        <div className="d-flex justify-content-end mb-3">
          <button type="button" className="btn btn-primary btn-sm" onClick={openCreate}>
            <i className="bi bi-plus-lg" aria-hidden="true" /> {tab.createLabel || 'Add'}
          </button>
        </div>
      )}

      {headerExtra}

      {tab.importCsvHelp && (user?.is_admin || user?.is_manager) && (
        <p className="small text-muted mb-2">{tab.importCsvHelp}</p>
      )}
      {importResult && (
        <div className="alert alert-success py-2 small" role="status">
          Imported {importResult.created} new, updated {importResult.updated}.
          {importResult.errors?.length > 0 && (
            <span className="text-warning"> {importResult.errors.length} row(s) skipped.</span>
          )}
        </div>
      )}

      <ResourceTabs
        tabs={tabs}
        activeTab={activeTab}
        onChange={setActiveTab}
        ariaLabel={`${title || 'Resource'} sections`}
      />

      {error && <div className="alert alert-danger" role="alert">{error}</div>}

      {selectedIds.length > 0 && canUseTabEdit && tab.canDelete !== false && (
        <div className="alert alert-secondary py-2 d-flex justify-content-between align-items-center" role="status">
          <span className="small">{selectedIds.length} selected</span>
          <button type="button" className="btn btn-danger btn-sm" onClick={requestBulkDelete}>
            Delete selected
          </button>
        </div>
      )}

      <div className="resource-table-wrap">
        <div
          role="tabpanel"
          id={`resource-panel-${tab?.id}`}
          aria-labelledby={tabs.length > 1 ? `resource-tab-${tab?.id}` : undefined}
        >
          <ResourceDataTable
            rows={rows}
            columns={columns}
            loading={loading}
            tab={tab}
            canUseTabEdit={canUseTabEdit}
            isEmployeeUser={isEmployeeUser}
            user={user}
            visibleFormFields={visibleFormFields}
            selectedIds={selectedIds}
            onToggleSelect={toggleSelect}
            onToggleSelectAll={toggleSelectAll}
            onEdit={openEdit}
            onDelete={requestDelete}
            onRunAction={runAction}
          />
        </div>
      </div>

      <ConfirmModal
        open={Boolean(confirmDelete)}
        title={confirmDelete?.title || 'Delete'}
        message={confirmDelete?.message || ''}
        confirmLabel="Delete"
        confirmVariant="danger"
        busy={deleting}
        onCancel={() => !deleting && setConfirmDelete(null)}
        onConfirm={confirmDeleteAction}
      />

      {showModal && (
        <ResourceFormModal
          tab={tab}
          editing={editing}
          form={form}
          visibleFormFields={visibleFormFields}
          lookupOptions={formLookups}
          isEmployeeUser={isEmployeeUser}
          user={user}
          submitting={submitting}
          onClose={() => setShowModal(false)}
          onSubmit={handleSubmit}
          onChange={handleChange}
        />
      )}
    </div>
  );
}
