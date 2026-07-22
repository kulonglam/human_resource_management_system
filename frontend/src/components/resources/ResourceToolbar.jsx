export default function ResourceToolbar({
  title,
  icon,
  tab,
  user,
  canUseTabCreate,
  importing,
  onCreate,
  onImportCsv,
}) {
  return (
    <div className="page-header">
      <div className="page-header-main">
        <p className="page-eyebrow">Module</p>
        <h1 className="page-heading mb-0">
          {icon && <i className={`bi ${icon}`} aria-hidden="true" />}
          {title}
        </h1>
      </div>
      <div className="d-flex flex-wrap gap-2">
        {canUseTabCreate && (
          <button type="button" className="btn btn-primary btn-sm" onClick={onCreate}>
            <i className="bi bi-plus-lg" aria-hidden="true" /> {tab.createLabel || 'Add'}
          </button>
        )}
        {tab.importCsv && (user?.is_admin || user?.is_manager) && (
          <label className="btn btn-outline-secondary btn-sm mb-0">
            {importing ? (
              <span className="spinner-border spinner-border-sm" role="status" aria-label="Importing" />
            ) : (
              <><i className="bi bi-upload" aria-hidden="true" /> Import CSV</>
            )}
            <input
              type="file"
              accept=".csv,text/csv"
              className="d-none"
              onChange={onImportCsv}
              disabled={importing}
              aria-label="Import CSV file"
            />
          </label>
        )}
      </div>
    </div>
  );
}
