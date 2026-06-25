export const employeeField = { name: 'employee', label: 'Employee', type: 'select' };

export function statusBadge(val) {
  const color =
    ['approved', 'active', 'completed', 'assigned'].includes(val) ? 'success'
    : ['pending', 'draft', 'initiated'].includes(val) ? 'warning'
    : ['rejected', 'expired'].includes(val) ? 'danger' : 'secondary';
  return { __html: `<span class="badge bg-${color}">${val}</span>` };
}

export function renderStatus(val) {
  const color =
    ['approved', 'active', 'completed', 'assigned', 'hired'].includes(val) ? 'success'
    : ['pending', 'draft', 'initiated', 'received'].includes(val) ? 'warning'
    : ['rejected', 'expired'].includes(val) ? 'danger'
    : ['shortlisted', 'interviewed'].includes(val) ? 'info'
    : 'secondary';
  return <span className={`badge bg-${color}`}>{val}</span>;
}
