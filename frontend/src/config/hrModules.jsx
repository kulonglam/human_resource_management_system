import { employeeField, renderStatus } from './shared';

export const attendanceTabs = [{
  id: 'records', label: 'Attendance Records', endpoint: 'attendance',
  columns: [
    { key: 'employee_name', label: 'Employee' }, { key: 'date', label: 'Date' },
    { key: 'time_in', label: 'In' }, { key: 'time_out', label: 'Out' },
    { key: 'status', label: 'Status', render: (r) => renderStatus(r.status) },
  ],
  formFields: [
    employeeField, { name: 'date', type: 'date', required: true },
    { name: 'time_in', type: 'time' }, { name: 'time_out', type: 'time' },
    { name: 'status', type: 'select', choices: [
      { value: 'present', label: 'Present' }, { value: 'absent', label: 'Absent' },
      { value: 'late', label: 'Late' }, { value: 'half_day', label: 'Half Day' },
    ]},
    { name: 'notes', type: 'textarea', fullWidth: true },
  ],
}];

export const leaveTabs = [
  {
    id: 'requests', label: 'Leave Requests', endpoint: 'leaves',
    columns: [
      { key: 'employee_name', label: 'Employee' }, { key: 'leave_type_display', label: 'Type' },
      { key: 'start_date', label: 'Start' }, { key: 'end_date', label: 'End' },
      { key: 'duration', label: 'Days' }, { key: 'status', label: 'Status', render: (r) => renderStatus(r.status) },
    ],
    formFields: [
      employeeField,
      { name: 'leave_type', type: 'select', choices: [
        { value: 'annual', label: 'Annual' }, { value: 'sick', label: 'Sick' },
        { value: 'maternity', label: 'Maternity' }, { value: 'paternity', label: 'Paternity' },
        { value: 'unpaid', label: 'Unpaid' },
      ]},
      { name: 'start_date', type: 'date', required: true },
      { name: 'end_date', type: 'date', required: true },
      { name: 'reason', type: 'textarea', fullWidth: true, required: true },
    ],
    rowActions: [
      { name: 'approve', label: 'Approve', variant: 'success', show: (r) => r.status === 'pending' },
      { name: 'reject', label: 'Reject', variant: 'danger', show: (r) => r.status === 'pending' },
    ],
    canDelete: false,
  },
  {
    id: 'balances', label: 'Leave Balances', endpoint: 'leave-balances',
    columns: [
      { key: 'employee_name', label: 'Employee' }, { key: 'leave_type_display', label: 'Type' },
      { key: 'year', label: 'Year' }, { key: 'total_days', label: 'Total' },
      { key: 'used_days', label: 'Used' }, { key: 'available_days', label: 'Available' },
    ],
    formFields: [
      employeeField,
      { name: 'leave_type', type: 'select', choices: [
        { value: 'annual', label: 'Annual' }, { value: 'sick', label: 'Sick' },
      ]},
      { name: 'year', type: 'number', default: new Date().getFullYear() },
      { name: 'total_days', type: 'number', required: true },
    ],
  },
];

export const recruitmentTabs = [
  {
    id: 'jobs', label: 'Job Postings', endpoint: 'jobs',
    detailPath: '/recruitment/jobs',
    columns: [
      { key: 'title', label: 'Title' }, { key: 'department', label: 'Department' },
      { key: 'deadline', label: 'Deadline' }, { key: 'application_count', label: 'Applications' },
    ],
    formFields: [
      { name: 'title', required: true }, { name: 'department', required: true },
      { name: 'description', type: 'textarea', fullWidth: true, required: true },
      { name: 'requirements', type: 'textarea', fullWidth: true, required: true },
      { name: 'deadline', type: 'date', required: true },
    ],
  },
  {
    id: 'applications', label: 'Applications', endpoint: 'applications',
    columns: [
      { key: 'full_name', label: 'Applicant' }, { key: 'job_title', label: 'Job' },
      { key: 'email', label: 'Email' }, { key: 'status', label: 'Status', render: (r) => renderStatus(r.status) },
      { key: 'resume_url', label: 'Resume', render: (r) => (
        r.resume_url ? <a href={r.resume_url} target="_blank" rel="noreferrer">View</a> : '—'
      )},
    ],
    formFields: [
      { name: 'job', type: 'select' }, { name: 'first_name', required: true },
      { name: 'last_name', required: true }, { name: 'email', type: 'email', required: true },
      { name: 'phone', required: true },
      { name: 'resume', type: 'file', accept: '.pdf,.doc,.docx', label: 'Resume' },
      { name: 'status', type: 'select', choices: [
        { value: 'received', label: 'Received' }, { value: 'shortlisted', label: 'Shortlisted' },
        { value: 'hired', label: 'Hired' }, { value: 'rejected', label: 'Rejected' },
      ]},
    ],
  },
];

export const payrollTabs = [{
  id: 'salaries', label: 'Salary Records', endpoint: 'salaries',
  columns: [
    { key: 'employee_name', label: 'Employee' }, { key: 'month_name', label: 'Month' },
    { key: 'year', label: 'Year' }, { key: 'net_salary', label: 'Net' },
    { key: 'is_paid', label: 'Paid', render: (r) => (r.is_paid ? 'Yes' : 'No') },
  ],
  formFields: [
    employeeField, { name: 'month', type: 'number', required: true },
    { name: 'year', type: 'number', required: true },
    { name: 'basic_salary', type: 'number', step: '0.01', required: true },
    { name: 'allowances', type: 'number', step: '0.01', default: 0 },
    { name: 'deductions', type: 'number', step: '0.01', default: 0 },
    { name: 'tax', type: 'number', step: '0.01', default: 0 },
  ],
  rowActions: [{ name: 'slip', label: 'PDF', variant: 'outline-info', method: 'GET' }],
}];
