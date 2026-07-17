import { useEffect, useMemo, useState } from 'react';
import { REPORT_PAGE_SIZE } from '../../utils/reportFormatters';

export default function ReportTable({ rows, columns, caption }) {
  const [page, setPage] = useState(1);

  useEffect(() => {
    setPage(1);
  }, [rows]);

  const totalPages = Math.max(1, Math.ceil((rows?.length || 0) / REPORT_PAGE_SIZE));
  const pageRows = useMemo(() => {
    if (!rows?.length) return [];
    const start = (page - 1) * REPORT_PAGE_SIZE;
    return rows.slice(start, start + REPORT_PAGE_SIZE);
  }, [rows, page]);

  if (!rows?.length) {
    return (
      <div className="report-empty">
        <i className="bi bi-inbox" aria-hidden="true" />
        <p className="mb-1 fw-semibold">No records found</p>
        <p className="text-muted mb-0">Try changing the selected filters.</p>
      </div>
    );
  }
  return (
    <>
      <div className="table-responsive">
        <table className="table table-hover align-middle report-table mb-0">
          <caption className="visually-hidden">{caption}</caption>
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col.key} scope="col" className={col.className}>{col.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, idx) => (
              <tr key={row.id || idx}>
                {columns.map((col) => (
                  <td key={col.key} className={col.className}>
                    {col.render ? col.render(row[col.key], row) : (row[col.key] ?? '—')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length > REPORT_PAGE_SIZE && (
        <div className="d-flex justify-content-between align-items-center mt-3">
          <p className="text-muted small mb-0">
            Showing {(page - 1) * REPORT_PAGE_SIZE + 1}–{Math.min(page * REPORT_PAGE_SIZE, rows.length)} of {rows.length}
          </p>
          <div className="btn-group btn-group-sm">
            <button type="button" className="btn btn-outline-secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              Previous
            </button>
            <button type="button" className="btn btn-outline-secondary" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
              Next
            </button>
          </div>
        </div>
      )}
    </>
  );
}
