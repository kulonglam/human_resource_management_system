export const DETAIL_CONFIGS = {
  'performance-goals': {
    endpoint: 'performance-goals',
    backPath: '/performance',
    titleKey: 'goal_title',
    subtitleKey: 'employee_name',
    sections: [
      {
        title: 'Goal Details',
        fields: [
          { label: 'Employee', key: 'employee_name' },
          { label: 'Status', key: 'status' },
          { label: 'Progress', key: 'progress', suffix: '%' },
          { label: 'Priority', key: 'priority' },
          { label: 'Start Date', key: 'start_date' },
          { label: 'End Date', key: 'end_date' },
          { label: 'Target Metric', key: 'target_metric' },
          { label: 'Description', key: 'goal_description', fullWidth: true },
          { label: 'Notes', key: 'notes', fullWidth: true },
        ],
      },
    ],
  },
  'performance-appraisals': {
    endpoint: 'performance-appraisals',
    backPath: '/performance',
    titleKey: 'employee_name',
    subtitleKey: 'status',
    sections: [
      {
        title: 'Appraisal Period',
        fields: [
          { label: 'Start', key: 'appraisal_period_start' },
          { label: 'End', key: 'appraisal_period_end' },
          { label: 'Overall Rating', key: 'overall_rating' },
          { label: 'Status', key: 'status' },
        ],
      },
      {
        title: 'Ratings',
        fields: [
          { label: 'Job Knowledge', key: 'job_knowledge' },
          { label: 'Work Quality', key: 'work_quality' },
          { label: 'Productivity', key: 'productivity' },
          { label: 'Communication', key: 'communication' },
          { label: 'Teamwork', key: 'teamwork' },
          { label: 'Initiative', key: 'initiative' },
          { label: 'Reliability', key: 'reliability' },
        ],
      },
      {
        title: 'Comments',
        fields: [
          { label: 'Strengths', key: 'strengths', fullWidth: true },
          { label: 'Areas for Improvement', key: 'areas_for_improvement', fullWidth: true },
          { label: 'Next Goals', key: 'next_goals', fullWidth: true },
          { label: 'Training Needs', key: 'training_needs', fullWidth: true },
        ],
      },
    ],
  },
  'training-courses': {
    endpoint: 'training-courses',
    backPath: '/training',
    titleKey: 'title',
    subtitleKey: 'status',
    sections: [
      {
        title: 'Course Information',
        fields: [
          { label: 'Category', key: 'category' },
          { label: 'Provider', key: 'provider' },
          { label: 'Duration (hours)', key: 'duration_hours' },
          { label: 'Start Date', key: 'start_date' },
          { label: 'End Date', key: 'end_date' },
          { label: 'Location', key: 'location' },
          { label: 'Online', key: 'is_online', render: (v) => (v ? 'Yes' : 'No') },
          { label: 'Max Participants', key: 'max_participants' },
          { label: 'Cost', key: 'cost' },
          { label: 'Participants', key: 'participants_count' },
          { label: 'Description', key: 'description', fullWidth: true },
          { label: 'Notes', key: 'notes', fullWidth: true },
        ],
      },
    ],
  },
  'development-plans': {
    endpoint: 'development-plans',
    backPath: '/training',
    titleKey: 'title',
    subtitleKey: 'employee_name',
    sections: [
      {
        title: 'Plan Details',
        fields: [
          { label: 'Employee', key: 'employee_name' },
          { label: 'Status', key: 'status' },
          { label: 'Progress', key: 'progress', suffix: '%' },
          { label: 'Start Date', key: 'start_date' },
          { label: 'End Date', key: 'end_date' },
          { label: 'Description', key: 'description', fullWidth: true },
          { label: 'Goals', key: 'goals', fullWidth: true },
        ],
      },
    ],
  },
  jobs: {
    endpoint: 'jobs',
    backPath: '/recruitment',
    titleKey: 'title',
    subtitleKey: 'department',
    sections: [
      {
        title: 'Job Posting',
        fields: [
          { label: 'Department', key: 'department' },
          { label: 'Deadline', key: 'deadline' },
          { label: 'Open', key: 'is_open', render: (v) => (v ? 'Yes' : 'No') },
          { label: 'Applications', key: 'application_count' },
          { label: 'Description', key: 'description', fullWidth: true },
          { label: 'Requirements', key: 'requirements', fullWidth: true },
        ],
      },
    ],
    related: {
      title: 'Applications',
      endpoint: 'applications',
      queryKey: 'job',
      columns: [
        { key: 'full_name', label: 'Applicant' },
        { key: 'email', label: 'Email' },
        { key: 'status', label: 'Status' },
      ],
    },
  },
  'exit-processes': {
    endpoint: 'exit-processes',
    backPath: '/exits',
    titleKey: 'employee_name',
    subtitleKey: 'status',
    sections: [
      {
        title: 'Exit Process',
        fields: [
          { label: 'Exit Date', key: 'exit_date' },
          { label: 'Reason', key: 'reason_display' },
          { label: 'Status', key: 'status' },
          { label: 'Notes', key: 'notes', fullWidth: true },
        ],
      },
    ],
    related: {
      title: 'Exit Checklist',
      endpoint: 'exit-checklist-items',
      queryKey: 'exit_process',
      columns: [
        { key: 'item_name', label: 'Item' },
        { key: 'responsible_person', label: 'Responsible' },
        { key: 'status', label: 'Status' },
      ],
    },
  },
};
