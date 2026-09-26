import { Link } from 'react-router-dom';
import { defaultLabel } from './ResourceFormField';

export default function ResourceDataTable({
  rows,
  columns,
  loading,
  tab,
  canUseTabEdit,
  isEmployeeUser,
  user,
  visibleFormFields,
  selectedIds,
  onToggleSelect,
  onToggleSelectAll,
  onEdit,
  onDelete,
  onRunAction,
}) {
  const showEditButtons = canUseTabEdit && visibleFormFields.length > 0;
  const showRowActionButtons = Boolean(tab.rowActions?.length)
    && !(isEmployeeUser && tab.hideRowActionsForEmployee);
  const showActions = showEditButtons || showRowActionButtons || Boolean(tab.detailPath);
  const showSelection = canUseTabEdit && tab.canDelete !== false;
  const colSpan = columns.length + (showActions ? 1 : 0) + (showSelection ? 1 : 0);

  if (loading) {
    return (
      <div className="empty-state" role="status" aria-live="polite">
        <div className="spinner-border text-primary" aria-hidden="true" />
        <span className="visually-hidden">Loading records</span>
        <p>Loading records…</p>
      </div>
    );
  }

  return (
    <div className="table-responsive">
      <table className="table table-hover mb-0 align-middle">
        <caption className="visually-hidden">{tab.label} records</caption>
        <thead>
          <tr>
            {showSelection && (
              <th scope="col" style={{ width: 36 }}>
                <input
                  type="checkbox"
                  className="form-check-input"
                  checked={rows.length > 0 && selectedIds.length === rows.length}
                  onChange={onToggleSelectAll}
                  aria-label="Select all rows"
                />
              </th>
            )}
            {columns.map((col) => (
              <th key={col.key || col} scope="col">
                {typeof col === 'string' ? defaultLabel(col) : col.label}
              </th>
            ))}
            {showActions && <th scope="col">Actions</th>}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              {showSelection && (
                <td>
                  <input
                    type="checkbox"
                    className="form-check-input"
                    checked={selectedIds.includes(row.id)}
                    onChange={() => onToggleSelect(row.id)}
                    aria-label={`Select row ${row.id}`}
                  />
                </td>
              )}
              {columns.map((col) => {
                const key = col.key || col;
                const val = col.render ? col.render(row) : row[key];
                return <td key={key}>{val ?? '—'}</td>;
              })}
              {showActions && (
                <td className="text-nowrap">
                  {tab.detailPath && (
                    <Link
                      to={`${tab.detailPath}/${row.id}`}
                      className="btn btn-outline-secondary btn-sm me-1"
                      aria-label={`View record ${row.id}`}
                    >
                      <i className="bi bi-eye" aria-hidden="true" />
                    </Link>
                  )}
                  {canUseTabEdit && visibleFormFields.length > 0 && (
                    <button
                      type="button"
                      className="btn btn-outline-primary btn-sm me-1"
                      onClick={() => onEdit(row)}
                      aria-label={`Edit record ${row.id}`}
                    >
                      <i className="bi bi-pencil" aria-hidden="true" />
                    </button>
                  )}
                  {canUseTabEdit && tab.canDelete !== false && visibleFormFields.length > 0 && (
                    <button
                      type="button"
                      className="btn btn-outline-danger btn-sm me-1"
                      onClick={() => onDelete(row)}
                      aria-label={`Delete record ${row.id}`}
                    >
                      <i className="bi bi-trash" aria-hidden="true" />
                    </button>
                  )}
                  {tab.rowActions?.map((action) =>
                    (!action.show || action.show(row))
                      && !(isEmployeeUser && tab.hideRowActionsForEmployee)
                      && !(action.adminOnly && !user?.is_admin)
                      && !(action.managerOnly && !user?.is_admin && !user?.is_manager) ? (
                        <button
                          key={action.name}
                          type="button"
                          className={`btn btn-sm me-1 btn-${action.variant || 'outline-secondary'}`}
                          onClick={() => onRunAction(row, action)}
                          aria-label={action.label}
                        >
                          {action.label}
                        </button>
                      ) : null
                  )}
                </td>
              )}
            </tr>
          ))}
          {!rows.length && (
            <tr>
              <td colSpan={colSpan}>
                <div className="empty-state py-5">
                  <i className="bi bi-inbox" aria-hidden="true" />
                  <p>No records found.</p>
                </div>
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
