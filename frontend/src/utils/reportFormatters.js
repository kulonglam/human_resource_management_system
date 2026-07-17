export const REPORT_PAGE_SIZE = 25;

export const REPORT_TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'attendance', label: 'Attendance' },
  { id: 'leave', label: 'Leave' },
  { id: 'payroll', label: 'Payroll' },
  { id: 'performance', label: 'Performance' },
  { id: 'recruitment', label: 'Recruitment' },
];

const UGX_FORMATTER = new Intl.NumberFormat('en-UG', {
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

export function formatUGX(value) {
  return `UGX ${UGX_FORMATTER.format(Number(value) || 0)}`;
}

export function formatDate(value) {
  if (!value) return '—';
  const date = new Date(`${value}T00:00:00`);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleDateString('en-UG', { day: '2-digit', month: 'short', year: 'numeric' });
}

export function formatLabel(value) {
  if (value == null || value === '') return '—';
  return String(value)
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}
