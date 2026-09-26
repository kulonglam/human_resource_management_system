import { employeeField, renderStatus } from './shared';

const formatUGX = (value) => `UGX ${Number(value || 0).toLocaleString('en-UG')}`;

export const attendanceTabs = [{
  id: 'records', label: 'Attendance Records', endpoint: 'attendance',
  importCsv: true,
  importCsvHelp: 'CSV columns: employee_number, date (YYYY-MM-DD), time_in, time_out, status, notes',
  columns: [
    { key: 'employee_name', label: 'Employee' }, { key: 'date', label: 'Date' },
    { key: 'time_in', label: 'In' }, { key: 'time_out', label: 'Out' },
    { key: 'status', label: 'Status', render: (r) => renderStatus(r.status) },
    { key: 'approval_status', label: 'Approval', render: (r) => renderStatus(r.approval_status) },
    { key: 'shift_name', label: 'Shift' },
  ],
  formFields: [
    employeeField, { name: 'date', type: 'date', required: true },
    { name: 'time_in', type: 'time' }, { name: 'time_out', type: 'time' },
    { name: 'status', type: 'select', choices: [
      { value: 'present', label: 'Present' }, { value: 'absent', label: 'Absent' },
      { value: 'late', label: 'Late' }, { value: 'half_day', label: 'Half Day' },
    ]},
    { name: 'source', type: 'select', choices: [
      { value: 'manual', label: 'Manual' }, { value: 'import', label: 'Import' },
      { value: 'device', label: 'Biometric / device' }, { value: 'mobile', label: 'Mobile' },
    ]},
    { name: 'notes', type: 'textarea', fullWidth: true },
  ],
  hideCreateForEmployee: true,
  hideEditForEmployee: true,
  rowActions: [
    { name: 'submit', label: 'Submit', variant: 'outline-primary', show: (r) => ['draft', 'rejected'].includes(r.approval_status) },
    { name: 'approve', label: 'Approve', variant: 'success', managerOnly: true, show: (r) => r.approval_status === 'submitted' },
    { name: 'reject', label: 'Reject', variant: 'danger', managerOnly: true, show: (r) => r.approval_status === 'submitted' },
  ],
}, {
  id: 'timesheets', label: 'Timesheets', endpoint: 'timesheets',
  selfServiceEmployee: true,
  columns: [
    { key: 'employee_name', label: 'Employee' }, { key: 'date', label: 'Date' },
    { key: 'regular_hours', label: 'Regular Hrs' }, { key: 'overtime_hours', label: 'OT Hrs' },
    { key: 'status', label: 'Status', render: (r) => renderStatus(r.status) },
  ],
  formFields: [
    employeeField, { name: 'date', type: 'date', required: true },
    { name: 'clock_in', type: 'time' }, { name: 'clock_out', type: 'time' },
    { name: 'regular_hours', type: 'number', step: '0.01', required: true },
    { name: 'project_code', label: 'Project code' },
    { name: 'notes', type: 'textarea', fullWidth: true },
  ],
  rowActions: [
    { name: 'submit', label: 'Submit', variant: 'outline-primary', show: (r) => ['draft', 'rejected'].includes(r.status) },
    { name: 'approve', label: 'Approve', variant: 'success', managerOnly: true, show: (r) => r.status === 'submitted' },
  ],
}, {
  id: 'overtime', label: 'Overtime', endpoint: 'overtime-records',
  selfServiceEmployee: true,
  columns: [
    { key: 'employee_name', label: 'Employee' }, { key: 'date', label: 'Date' },
    { key: 'hours', label: 'Hours' }, { key: 'status', label: 'Status', render: (r) => renderStatus(r.status) },
    { key: 'reason', label: 'Reason' },
  ],
  formFields: [
    employeeField, { name: 'date', type: 'date', required: true },
    { name: 'hours', type: 'number', step: '0.01', required: true },
    { name: 'reason', type: 'textarea', fullWidth: true, required: true },
  ],
  rowActions: [
    { name: 'approve', label: 'Approve', variant: 'success', managerOnly: true, show: (r) => r.status === 'pending' },
    { name: 'reject', label: 'Reject', variant: 'danger', managerOnly: true, show: (r) => r.status === 'pending' },
  ],
}, {
  id: 'devices', label: 'Devices', endpoint: 'attendance-devices',
  adminOnly: true,
  columns: [
    { key: 'name', label: 'Device' }, { key: 'device_code', label: 'Code' },
    { key: 'device_type', label: 'Type' }, { key: 'location', label: 'Location' },
    { key: 'is_active', label: 'Active', render: (r) => (r.is_active ? 'Yes' : 'No') },
    { key: 'last_seen_at', label: 'Last seen' },
  ],
  formFields: [
    { name: 'name', required: true },
    { name: 'device_code', required: true, label: 'Device code' },
    { name: 'device_type', type: 'select', choices: [
      { value: 'fingerprint', label: 'Fingerprint' },
      { value: 'face', label: 'Face recognition' },
      { value: 'rfid', label: 'RFID / badge' },
      { value: 'mobile', label: 'Mobile app' },
      { value: 'other', label: 'Other' },
    ]},
    { name: 'location' },
  ],
  hideCreateForEmployee: true,
}, {
  id: 'punches', label: 'Device punches', endpoint: 'device-punches',
  hideCreate: true,
  columns: [
    { key: 'employee_name', label: 'Employee' }, { key: 'badge_id', label: 'Badge' },
    { key: 'device_name', label: 'Device' }, { key: 'punched_at', label: 'When' },
    { key: 'punch_type', label: 'Type' }, { key: 'source', label: 'Source' },
    { key: 'applied', label: 'Applied', render: (r) => (r.applied ? 'Yes' : 'No') },
  ],
  formFields: [],
  hideCreateForEmployee: true,
}, {
  id: 'holidays', label: 'Public Holidays', endpoint: 'public-holidays',
  columns: [
    { key: 'name', label: 'Holiday' }, { key: 'date', label: 'Date' },
    { key: 'is_recurring', label: 'Recurring', render: (r) => (r.is_recurring ? 'Yes' : 'No') },
  ],
  formFields: [
    { name: 'name', required: true }, { name: 'date', type: 'date', required: true },
    { name: 'is_recurring', type: 'checkbox', label: 'Recurring annually', default: true },
    { name: 'notes', type: 'textarea', fullWidth: true },
  ],
  hideCreateForEmployee: true,
  hideEditForEmployee: true,
}];

export const leaveTabs = [
  {
    id: 'requests', label: 'Leave Requests', endpoint: 'leaves',
    selfServiceEmployee: true,
    createLabel: 'Apply for Leave',
    columns: [
      { key: 'employee_name', label: 'Employee' }, { key: 'leave_type_display', label: 'Type' },
      { key: 'start_date', label: 'Start' }, { key: 'end_date', label: 'End' },
      { key: 'duration', label: 'Working Days' }, { key: 'is_half_day', label: 'Half Day', render: (r) => (r.is_half_day ? 'Yes' : 'No') },
      { key: 'status', label: 'Status', render: (r) => renderStatus(r.status) },
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
      { name: 'is_half_day', type: 'checkbox', label: 'Half day (same start/end date)' },
      { name: 'reason', type: 'textarea', fullWidth: true, required: true },
    ],
    rowActions: [
      { name: 'approve', label: 'Approve', variant: 'success', managerOnly: true, show: (r) => r.status === 'pending' },
      { name: 'reject', label: 'Reject', variant: 'danger', managerOnly: true, show: (r) => r.status === 'pending' },
    ],
    canDelete: false,
    hideEdit: true,
    hideRowActionsForEmployee: true,
  },
  {
    id: 'balances', label: 'Leave Balances', endpoint: 'leave-balances',
    canCreate: false,
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
    hideCreateForEmployee: true,
    hideEditForEmployee: true,
  },
];

export const recruitmentJobsTab = {
  id: 'jobs', label: 'Job Postings', endpoint: 'jobs',
  detailPath: '/recruitment/jobs',
  columns: [
    { key: 'title', label: 'Title' }, { key: 'department', label: 'Department' },
    { key: 'deadline', label: 'Deadline' },
    { key: 'is_open', label: 'Open', render: (r) => (r.is_open ? 'Yes' : 'No') },
    { key: 'application_count', label: 'Applications' },
  ],
  formFields: [
    { name: 'title', required: true },
    { name: 'department', type: 'select', required: true },
    { name: 'description', type: 'textarea', fullWidth: true, required: true },
    { name: 'requirements', type: 'textarea', fullWidth: true, required: true },
    { name: 'deadline', type: 'date', required: true },
    { name: 'is_open', type: 'checkbox', label: 'Open for applications', default: true },
  ],
  hideCreateForEmployee: true,
  hideEditForEmployee: true,
};

export const recruitmentApplicationsTab = {
  id: 'applications', label: 'Applications', endpoint: 'applications',
  detailPath: '/recruitment/applications',
  columns: [
    { key: 'full_name', label: 'Applicant' }, { key: 'job_title', label: 'Job' },
    { key: 'email', label: 'Email' },
    { key: 'source_display', label: 'Source' },
    { key: 'rating', label: 'Rating', render: (r) => (r.rating ? `${r.rating}/5` : '—') },
    { key: 'status', label: 'Status', render: (r) => renderStatus(r.status) },
    { key: 'resume_url', label: 'Resume', render: (r) => (
      r.resume_url ? <a href={r.resume_url} target="_blank" rel="noreferrer">View</a> : '—'
    )},
  ],
  formFields: [
    { name: 'job', type: 'select' }, { name: 'first_name', required: true },
    { name: 'last_name', required: true }, { name: 'email', type: 'email', required: true },
    { name: 'phone', required: true },
    { name: 'cover_letter', type: 'textarea', fullWidth: true, label: 'Cover letter' },
    { name: 'resume', type: 'file', accept: '.pdf,.doc,.docx', label: 'Resume' },
    { name: 'status', type: 'select', choices: [
      { value: 'received', label: 'Received' }, { value: 'shortlisted', label: 'Shortlisted' },
      { value: 'interviewed', label: 'Interviewed' },
      { value: 'hired', label: 'Hired' }, { value: 'rejected', label: 'Rejected' },
    ]},
  ],
  rowActions: [
    {
      name: 'approve',
      label: 'Advance',
      variant: 'outline-success',
      managerOnly: true,
      show: (row) => ['received', 'shortlisted', 'interviewed'].includes(row.status),
    },
    {
      name: 'reject',
      label: 'Reject',
      variant: 'outline-danger',
      managerOnly: true,
      show: (row) => !['rejected', 'hired'].includes(row.status),
    },
  ],
  hideCreateForEmployee: true,
  hideEditForEmployee: true,
  hideRowActionsForEmployee: true,
};

export const recruitmentTabs = [recruitmentJobsTab, recruitmentApplicationsTab];

export const payrollTabs = [{
  id: 'salaries', label: 'Salary Records', endpoint: 'salaries',
  columns: [
    { key: 'employee_name', label: 'Employee' }, { key: 'month_name', label: 'Month' },
    { key: 'year', label: 'Year' },
    { key: 'gross_salary', label: 'Gross', render: (r) => formatUGX(r.gross_salary) },
    { key: 'tax', label: 'PAYE', render: (r) => formatUGX(r.tax) },
    { key: 'net_salary', label: 'Net', render: (r) => formatUGX(r.net_salary) },
    { key: 'status', label: 'Status', render: (r) => renderStatus(r.status) },
  ],
  formFields: [
    employeeField, { name: 'month', type: 'number', required: true },
    { name: 'year', type: 'number', required: true },
    { name: 'basic_salary', type: 'number', step: '0.01', required: true },
    { name: 'allowances', type: 'number', step: '0.01', default: 0 },
    { name: 'taxable_benefits', type: 'number', step: '0.01', default: 0 },
    { name: 'deductions', type: 'number', step: '0.01', default: 0 },
    { name: 'is_resident', type: 'checkbox', default: true, label: 'Uganda tax resident' },
    { name: 'is_secondary_employment', type: 'checkbox', label: 'Secondary employment (30% PAYE)' },
    { name: 'nssf_applicable', type: 'checkbox', default: true, label: 'NSSF applicable' },
    { name: 'lst_applicable', type: 'checkbox', default: true, label: 'Local Service Tax applicable' },
  ],
  rowActions: [
    { name: 'slip', label: 'PDF', variant: 'outline-info', method: 'GET' },
  ],
  hideCreateForEmployee: true,
  hideEditForEmployee: true,
  hideRowActionsForEmployee: true,
  requiresPayrollManage: true,
}, {
  id: 'runs', label: 'Payroll Runs', endpoint: 'payroll-runs',
  columns: [
    { key: 'period', label: 'Period' },
    { key: 'employee_count', label: 'Employees' },
    { key: 'total_gross', label: 'Gross', render: (r) => formatUGX(r.total_gross) },
    { key: 'total_paye', label: 'PAYE', render: (r) => formatUGX(r.total_paye) },
    { key: 'total_nssf', label: 'Total NSSF', render: (r) => formatUGX(r.total_nssf) },
    { key: 'total_net', label: 'Net', render: (r) => formatUGX(r.total_net) },
    { key: 'status', label: 'Status', render: (r) => renderStatus(r.status) },
  ],
  formFields: [
    { name: 'month', type: 'number', required: true, default: new Date().getMonth() + 1 },
    { name: 'year', type: 'number', required: true, default: new Date().getFullYear() },
    { name: 'notes', type: 'textarea', fullWidth: true },
  ],
  rowActions: [
    { name: 'approve', label: 'Approve Run', variant: 'success', adminOnly: true, show: (r) => r.status === 'draft' },
    { name: 'mark_paid', label: 'Mark Paid', variant: 'primary', adminOnly: true, show: (r) => r.status === 'approved' },
  ],
  hideCreateForEmployee: true,
  hideEditForEmployee: true,
  hideRowActionsForEmployee: true,
  requiresPayrollManage: true,
}];

export const workforceStructureTabs = [
  {
    id: 'positions', label: 'Positions', endpoint: 'positions',
    columns: [
      { key: 'code', label: 'Code' }, { key: 'title', label: 'Position' },
      { key: 'department_name', label: 'Department' }, { key: 'grade_name', label: 'Grade' },
      { key: 'reports_to_title', label: 'Reports To' },
    ],
    formFields: [
      { name: 'code', required: true }, { name: 'title', required: true },
      { name: 'department', type: 'select', required: true },
      { name: 'grade', type: 'select' }, { name: 'reports_to', type: 'select' },
      { name: 'description', type: 'textarea', fullWidth: true },
      { name: 'is_active', type: 'checkbox', default: true },
    ],
    hideCreateForEmployee: true,
    hideEditForEmployee: true,
  },
  {
    id: 'grades', label: 'Job Grades', endpoint: 'job-grades',
    columns: [
      { key: 'code', label: 'Code' }, { key: 'name', label: 'Grade' },
      { key: 'rank', label: 'Rank' },
      { key: 'minimum_salary', label: 'Minimum', render: (r) => formatUGX(r.minimum_salary) },
      { key: 'maximum_salary', label: 'Maximum', render: (r) => formatUGX(r.maximum_salary) },
    ],
    formFields: [
      { name: 'code', required: true }, { name: 'name', required: true },
      { name: 'rank', type: 'number', required: true },
      { name: 'minimum_salary', type: 'number', step: '0.01' },
      { name: 'maximum_salary', type: 'number', step: '0.01' },
      { name: 'is_active', type: 'checkbox', default: true },
    ],
    hideCreateForEmployee: true,
    hideEditForEmployee: true,
  },
  {
    id: 'contracts', label: 'Contracts', endpoint: 'employment-contracts',
    columns: [
      { key: 'employee_name', label: 'Employee' }, { key: 'contract_type', label: 'Type' },
      { key: 'start_date', label: 'Start' }, { key: 'end_date', label: 'End' },
      { key: 'status', label: 'Status', render: (r) => renderStatus(r.status) },
    ],
    formFields: [
      employeeField,
      { name: 'contract_type', type: 'select', required: true, choices: [
        { value: 'permanent', label: 'Permanent' }, { value: 'fixed_term', label: 'Fixed Term' },
        { value: 'temporary', label: 'Temporary' }, { value: 'internship', label: 'Internship' },
        { value: 'consultancy', label: 'Consultancy' },
      ] },
      { name: 'start_date', type: 'date', required: true }, { name: 'end_date', type: 'date' },
      { name: 'probation_end_date', type: 'date' },
      { name: 'salary', type: 'number', step: '0.01', required: true },
      { name: 'status', type: 'select', choices: [
        { value: 'draft', label: 'Draft' }, { value: 'active', label: 'Active' },
        { value: 'expired', label: 'Expired' }, { value: 'terminated', label: 'Terminated' },
      ] },
      { name: 'document', type: 'file', accept: '.pdf,.doc,.docx' },
      { name: 'notes', type: 'textarea', fullWidth: true },
    ],
    hideCreateForEmployee: true,
    hideEditForEmployee: true,
  },
  {
    id: 'history', label: 'Employment History', endpoint: 'employment-history',
    columns: [
      { key: 'employee_name', label: 'Employee' }, { key: 'event_type_display', label: 'Change' },
      { key: 'effective_date', label: 'Effective Date' }, { key: 'notes', label: 'Notes' },
    ],
    formFields: [
      employeeField,
      { name: 'event_type', type: 'select', required: true, choices: [
        { value: 'hire', label: 'Hire' }, { value: 'promotion', label: 'Promotion' },
        { value: 'transfer', label: 'Transfer' }, { value: 'grade_change', label: 'Grade Change' },
        { value: 'salary_change', label: 'Salary Change' },
        { value: 'contract_change', label: 'Contract Change' }, { value: 'exit', label: 'Exit' },
      ] },
      { name: 'effective_date', type: 'date', required: true },
      { name: 'previous_position', type: 'select' }, { name: 'new_position', type: 'select' },
      { name: 'previous_department', type: 'select' }, { name: 'new_department', type: 'select' },
      { name: 'previous_grade', type: 'select' }, { name: 'new_grade', type: 'select' },
      { name: 'notes', type: 'textarea', fullWidth: true },
    ],
    hideCreateForEmployee: true,
    hideEditForEmployee: true,
  },
];
