import { employeeField, renderStatus } from './shared';

export const performanceTabs = [
  {
    id: 'goals', label: 'Goals', endpoint: 'performance-goals',
    detailPath: '/performance/goals',
    columns: [
      { key: 'employee_name', label: 'Employee' }, { key: 'goal_title', label: 'Title' },
      { key: 'progress', label: 'Progress %' }, { key: 'status', label: 'Status', render: (r) => renderStatus(r.status) },
    ],
    formFields: [
      employeeField, { name: 'goal_title', required: true },
      { name: 'goal_description', type: 'textarea', fullWidth: true, required: true },
      { name: 'start_date', type: 'date', required: true }, { name: 'end_date', type: 'date', required: true },
      { name: 'target_metric', required: true }, { name: 'progress', type: 'number', default: 0 },
    ],
  },
  {
    id: 'appraisals', label: 'Appraisals', endpoint: 'performance-appraisals',
    detailPath: '/performance/appraisals',
    columns: [
      { key: 'employee_name', label: 'Employee' },
      { key: 'appraisal_period_start', label: 'Start' }, { key: 'appraisal_period_end', label: 'End' },
      { key: 'overall_rating', label: 'Rating' }, { key: 'status', label: 'Status', render: (r) => renderStatus(r.status) },
    ],
    formFields: [
      employeeField, { name: 'appraisal_period_start', type: 'date', required: true },
      { name: 'appraisal_period_end', type: 'date', required: true },
      { name: 'job_knowledge', type: 'number', required: true }, { name: 'work_quality', type: 'number', required: true },
      { name: 'productivity', type: 'number', required: true }, { name: 'communication', type: 'number', required: true },
      { name: 'teamwork', type: 'number', required: true }, { name: 'initiative', type: 'number', required: true },
      { name: 'reliability', type: 'number', required: true },
      { name: 'strengths', type: 'textarea', fullWidth: true, required: true },
      { name: 'areas_for_improvement', type: 'textarea', fullWidth: true, required: true },
      { name: 'next_goals', type: 'textarea', fullWidth: true, required: true },
    ],
    rowActions: [
      { name: 'submit', label: 'Submit', variant: 'success', show: (r) => r.status === 'draft' },
      { name: 'approve', label: 'Approve', variant: 'primary', show: (r) => r.status === 'submitted' },
    ],
  },
  {
    id: 'feedback-rounds', label: 'Feedback Rounds', endpoint: 'feedback-rounds',
    columns: [
      { key: 'name', label: 'Name' }, { key: 'start_date', label: 'Start' },
      { key: 'end_date', label: 'End' }, { key: 'status', label: 'Status', render: (r) => renderStatus(r.status) },
    ],
    formFields: [
      { name: 'name', required: true }, { name: 'description', type: 'textarea', fullWidth: true },
      { name: 'start_date', type: 'date', required: true }, { name: 'end_date', type: 'date', required: true },
    ],
  },
];

export const trainingTabs = [
  {
    id: 'courses', label: 'Courses', endpoint: 'training-courses',
    detailPath: '/training/courses',
    columns: [
      { key: 'title', label: 'Title' }, { key: 'category', label: 'Category' },
      { key: 'start_date', label: 'Start' }, { key: 'status', label: 'Status', render: (r) => renderStatus(r.status) },
    ],
    formFields: [
      { name: 'title', required: true }, { name: 'description', type: 'textarea', fullWidth: true, required: true },
      { name: 'provider', required: true }, { name: 'duration_hours', type: 'number', required: true },
      { name: 'start_date', type: 'date', required: true }, { name: 'end_date', type: 'date', required: true },
    ],
  },
  {
    id: 'records', label: 'Training Records', endpoint: 'training-records',
    columns: [
      { key: 'employee_name', label: 'Employee' }, { key: 'course_title', label: 'Course' },
      { key: 'status', label: 'Status', render: (r) => renderStatus(r.status) }, { key: 'score', label: 'Score' },
    ],
    formFields: [employeeField, { name: 'course', type: 'select' },
      { name: 'status', type: 'select', choices: [
        { value: 'enrolled', label: 'Enrolled' }, { value: 'completed', label: 'Completed' },
      ]},
    ],
  },
  {
    id: 'skills', label: 'Skills', endpoint: 'skills',
    columns: [{ key: 'name', label: 'Skill' }, { key: 'category', label: 'Category' }],
    formFields: [
      { name: 'name', required: true },
      { name: 'category', type: 'select', choices: [
        { value: 'technical', label: 'Technical' }, { value: 'soft_skills', label: 'Soft Skills' },
      ]},
    ],
  },
  {
    id: 'employee-skills', label: 'Employee Skills', endpoint: 'employee-skills',
    columns: [
      { key: 'employee_name', label: 'Employee' }, { key: 'skill_name', label: 'Skill' },
      { key: 'proficiency_level', label: 'Level' }, { key: 'years_of_experience', label: 'Years' },
      { key: 'verified', label: 'Verified', render: (r) => (r.verified ? 'Yes' : 'No') },
    ],
    formFields: [
      employeeField, { name: 'skill', type: 'select' },
      { name: 'proficiency_level', type: 'select', choices: [
        { value: 'beginner', label: 'Beginner' }, { value: 'intermediate', label: 'Intermediate' },
        { value: 'advanced', label: 'Advanced' }, { value: 'expert', label: 'Expert' },
      ]},
      { name: 'years_of_experience', type: 'number', step: '0.1', default: 0 },
      { name: 'acquired_date', type: 'date', required: true },
      { name: 'notes', type: 'textarea', fullWidth: true },
    ],
  },
  {
    id: 'certifications', label: 'Certifications', endpoint: 'certifications',
    columns: [
      { key: 'name', label: 'Certification' }, { key: 'issuing_body', label: 'Issuer' },
      { key: 'validity_years', label: 'Validity (years)' },
    ],
    formFields: [
      { name: 'name', required: true }, { name: 'issuing_body', required: true },
      { name: 'description', type: 'textarea', fullWidth: true },
      { name: 'validity_years', type: 'number', required: true },
    ],
  },
  {
    id: 'employee-certifications', label: 'Employee Certifications', endpoint: 'employee-certifications',
    columns: [
      { key: 'employee_name', label: 'Employee' }, { key: 'certification_name', label: 'Certification' },
      { key: 'issue_date', label: 'Issued' }, { key: 'expiry_date', label: 'Expires' },
      { key: 'days_until_expiry', label: 'Days Left' },
    ],
    formFields: [
      employeeField, { name: 'certification', type: 'select' },
      { name: 'issue_date', type: 'date', required: true },
      { name: 'expiry_date', type: 'date' }, { name: 'certificate_number', label: 'Certificate #' },
    ],
  },
  {
    id: 'development-plans', label: 'Development Plans', endpoint: 'development-plans',
    detailPath: '/training/development-plans',
    columns: [
      { key: 'employee_name', label: 'Employee' }, { key: 'title', label: 'Title' },
      { key: 'progress', label: 'Progress %' }, { key: 'status', label: 'Status', render: (r) => renderStatus(r.status) },
    ],
    formFields: [
      employeeField, { name: 'title', required: true },
      { name: 'description', type: 'textarea', fullWidth: true, required: true },
      { name: 'goals', type: 'textarea', fullWidth: true, required: true },
      { name: 'start_date', type: 'date', required: true }, { name: 'end_date', type: 'date', required: true },
    ],
  },
];

export const exitTabs = [
  {
    id: 'processes', label: 'Exit Processes', endpoint: 'exit-processes',
    detailPath: '/exits',
    columns: [
      { key: 'employee_name', label: 'Employee' }, { key: 'exit_date', label: 'Exit Date' },
      { key: 'reason_display', label: 'Reason' }, { key: 'status', label: 'Status', render: (r) => renderStatus(r.status) },
    ],
    formFields: [
      employeeField, { name: 'exit_date', type: 'date', required: true },
      { name: 'reason', type: 'select', choices: [
        { value: 'resignation', label: 'Resignation' }, { value: 'termination', label: 'Termination' },
        { value: 'retirement', label: 'Retirement' },
      ]},
      { name: 'notes', type: 'textarea', fullWidth: true },
    ],
  },
  {
    id: 'checklist', label: 'Checklist', endpoint: 'exit-checklist-items',
    columns: [
      { key: 'item_name', label: 'Item' }, { key: 'responsible_person', label: 'Responsible' },
      { key: 'status', label: 'Status', render: (r) => renderStatus(r.status) },
    ],
    formFields: [
      { name: 'exit_process', type: 'select' }, { name: 'item_name', required: true },
      { name: 'responsible_person', label: 'Responsible Person' },
    ],
  },
];

export const assetTabs = [
  {
    id: 'assets', label: 'Assets', endpoint: 'assets',
    columns: [
      { key: 'asset_code', label: 'Code' }, { key: 'name', label: 'Name' },
      { key: 'category', label: 'Category' }, { key: 'current_status', label: 'Status', render: (r) => renderStatus(r.current_status) },
    ],
    formFields: [
      { name: 'asset_code', required: true }, { name: 'name', required: true },
      { name: 'category', required: true }, { name: 'purchase_date', type: 'date', required: true },
      { name: 'purchase_price', type: 'number', step: '0.01', required: true },
    ],
  },
  {
    id: 'assignments', label: 'Assignments', endpoint: 'asset-assignments',
    columns: [
      { key: 'asset_name', label: 'Asset' }, { key: 'employee_name', label: 'Employee' },
      { key: 'assignment_date', label: 'Assigned' }, { key: 'status', label: 'Status', render: (r) => renderStatus(r.status) },
    ],
    formFields: [{ name: 'asset', type: 'select' }, employeeField],
  },
];

export const shiftTabs = [
  {
    id: 'shifts', label: 'Shifts', endpoint: 'shifts',
    columns: [
      { key: 'shift_name', label: 'Shift' }, { key: 'start_time', label: 'Start' },
      { key: 'end_time', label: 'End' }, { key: 'working_hours', label: 'Hours' },
    ],
    formFields: [
      { name: 'shift_name', required: true }, { name: 'start_time', type: 'time', required: true },
      { name: 'end_time', type: 'time', required: true }, { name: 'working_hours', type: 'number', required: true },
    ],
  },
  {
    id: 'assignments', label: 'Assignments', endpoint: 'shift-assignments',
    columns: [
      { key: 'employee_name', label: 'Employee' }, { key: 'shift_name', label: 'Shift' },
      { key: 'start_date', label: 'Start' }, { key: 'status', label: 'Status', render: (r) => renderStatus(r.status) },
    ],
    formFields: [employeeField, { name: 'shift', type: 'select' }, { name: 'start_date', type: 'date', required: true }],
  },
];

export const expenseTabs = [
  {
    id: 'expenses', label: 'Expenses', endpoint: 'expenses',
    columns: [
      { key: 'employee_name', label: 'Employee' }, { key: 'category_name', label: 'Category' },
      { key: 'amount', label: 'Amount' }, { key: 'status', label: 'Status', render: (r) => renderStatus(r.status) },
      { key: 'receipt_url', label: 'Receipt', render: (r) => (
        r.receipt_url ? <a href={r.receipt_url} target="_blank" rel="noreferrer">View</a> : '—'
      )},
    ],
    formFields: [
      employeeField, { name: 'category', type: 'select' },
      { name: 'description', required: true }, { name: 'amount', type: 'number', step: '0.01', required: true },
      { name: 'expense_date', type: 'date', required: true },
      { name: 'receipt_file', type: 'file', accept: 'image/*,.pdf', label: 'Receipt' },
    ],
    rowActions: [
      { name: 'approve', label: 'Approve', variant: 'success', show: (r) => r.status === 'submitted' },
      { name: 'reject', label: 'Reject', variant: 'danger', show: (r) => r.status === 'submitted' },
    ],
  },
  {
    id: 'categories', label: 'Categories', endpoint: 'expense-categories',
    columns: [{ key: 'name', label: 'Name' }],
    formFields: [{ name: 'name', required: true }, { name: 'description', type: 'textarea', fullWidth: true }],
  },
];

export const benefitTabs = [
  {
    id: 'benefits', label: 'Benefits', endpoint: 'benefits',
    columns: [{ key: 'name', label: 'Benefit' }, { key: 'type_display', label: 'Type' }, { key: 'provider', label: 'Provider' }],
    formFields: [
      { name: 'name', required: true },
      { name: 'benefit_type', type: 'select', choices: [
        { value: 'health', label: 'Health' }, { value: 'retirement', label: 'Retirement' },
      ]},
      { name: 'provider', label: 'Provider' },
    ],
  },
  {
    id: 'enrollments', label: 'Enrollments', endpoint: 'employee-benefits',
    columns: [
      { key: 'employee_name', label: 'Employee' }, { key: 'benefit_name', label: 'Benefit' },
      { key: 'status', label: 'Status', render: (r) => renderStatus(r.status) },
    ],
    formFields: [employeeField, { name: 'benefit', type: 'select' }, { name: 'enrollment_date', type: 'date', required: true }],
  },
];

export const leavePolicyTabs = [
  {
    id: 'policies', label: 'Policies', endpoint: 'leave-policies',
    columns: [
      { key: 'name', label: 'Policy' }, { key: 'leave_type_display', label: 'Type' }, { key: 'days_per_year', label: 'Days/Year' },
    ],
    formFields: [
      { name: 'name', required: true },
      { name: 'leave_type', type: 'select', choices: [{ value: 'annual', label: 'Annual' }, { value: 'sick', label: 'Sick' }] },
      { name: 'days_per_year', type: 'number', required: true },
    ],
  },
  {
    id: 'allocations', label: 'Allocations', endpoint: 'leave-policy-allocations',
    columns: [
      { key: 'employee_name', label: 'Employee' }, { key: 'policy_name', label: 'Policy' },
      { key: 'allocation_year', label: 'Year' }, { key: 'allocated_days', label: 'Allocated' },
      { key: 'used_days', label: 'Used' }, { key: 'pending_days', label: 'Pending' },
    ],
    formFields: [
      employeeField, { name: 'policy', type: 'select' },
      { name: 'allocation_year', type: 'number', default: new Date().getFullYear(), required: true },
      { name: 'allocated_days', type: 'number', required: true },
      { name: 'carryforward_days', type: 'number', default: 0 },
      { name: 'notes', type: 'textarea', fullWidth: true },
    ],
  },
];

export const disciplineTabs = [
  {
    id: 'records', label: 'Discipline Records', endpoint: 'discipline-records',
    columns: [
      { key: 'employee_name', label: 'Employee' }, { key: 'type_display', label: 'Type' },
      { key: 'reason', label: 'Reason' }, { key: 'status', label: 'Status', render: (r) => renderStatus(r.status) },
    ],
    formFields: [
      employeeField,
      { name: 'discipline_type', type: 'select', choices: [
        { value: 'verbal_warning', label: 'Verbal Warning' }, { value: 'written_warning', label: 'Written Warning' },
      ]},
      { name: 'reason', required: true }, { name: 'detailed_reason', type: 'textarea', fullWidth: true, required: true },
      { name: 'incident_date', type: 'date', required: true },
    ],
  },
  {
    id: 'appeals', label: 'Appeals', endpoint: 'discipline-appeals',
    columns: [
      { key: 'discipline', label: 'Discipline ID' }, { key: 'appeal_date', label: 'Appeal Date' },
      { key: 'status', label: 'Status', render: (r) => renderStatus(r.status) },
    ],
    formFields: [
      { name: 'discipline', type: 'select', label: 'Discipline Record' },
      { name: 'appeal_date', type: 'date', required: true },
      { name: 'appeal_reason', type: 'textarea', fullWidth: true, required: true },
      { name: 'status', type: 'select', choices: [
        { value: 'pending', label: 'Pending' }, { value: 'approved', label: 'Approved' },
        { value: 'rejected', label: 'Rejected' }, { value: 'dismissed', label: 'Dismissed' },
      ]},
    ],
  },
];

export const surveyManageTabs = [{
  id: 'surveys', label: 'Surveys', endpoint: 'surveys',
  columns: [
    { key: 'title', label: 'Title' }, { key: 'survey_type', label: 'Type' },
    { key: 'start_date', label: 'Start' }, { key: 'status', label: 'Status', render: (r) => renderStatus(r.status) },
  ],
  formFields: [
    { name: 'title', required: true }, { name: 'description', type: 'textarea', fullWidth: true },
    { name: 'survey_type', type: 'select', choices: [
      { value: 'feedback', label: 'Feedback' }, { value: 'satisfaction', label: 'Satisfaction' },
      { value: 'engagement', label: 'Engagement' },
    ]},
    { name: 'status', type: 'select', choices: [
      { value: 'draft', label: 'Draft' }, { value: 'active', label: 'Active' }, { value: 'closed', label: 'Closed' },
    ]},
    { name: 'start_date', type: 'date', required: true }, { name: 'end_date', type: 'date', required: true },
  ],
}];

export const surveyQuestionTab = {
  id: 'questions', label: 'Questions', endpoint: 'survey-questions',
  columns: [
    { key: 'survey', label: 'Survey ID' }, { key: 'question_text', label: 'Question' },
    { key: 'question_type', label: 'Type' }, { key: 'order', label: 'Order' },
    { key: 'is_required', label: 'Required', render: (r) => (r.is_required ? 'Yes' : 'No') },
  ],
  formFields: [
    { name: 'survey', type: 'select', label: 'Survey', required: true },
    { name: 'question_text', required: true, fullWidth: true },
    { name: 'question_type', type: 'select', choices: [
      { value: 'text', label: 'Text' }, { value: 'rating', label: 'Rating (1-5)' },
      { value: 'multiple_choice', label: 'Multiple Choice' }, { value: 'checkbox', label: 'Checkbox' },
    ]},
    { name: 'options', type: 'textarea', fullWidth: true, label: 'Options (comma-separated)' },
    { name: 'order', type: 'number', default: 0 },
    { name: 'is_required', type: 'select', choices: [{ value: 'true', label: 'Yes' }, { value: 'false', label: 'No' }] },
  ],
};

export const kinTabs = [{
  id: 'kin', label: 'Next of Kin', endpoint: 'kin',
  columns: [
    { key: 'employee_name', label: 'Employee' }, { key: 'first_name', label: 'First Name' },
    { key: 'last_name', label: 'Last Name' }, { key: 'relationship', label: 'Relationship' },
  ],
  formFields: [
    employeeField, { name: 'first_name', required: true }, { name: 'last_name', required: true },
    { name: 'relationship', required: true }, { name: 'mobile', required: true },
    { name: 'address', required: true }, { name: 'occupation', required: true },
  ],
}];
