const API_BASE = '/api/v1';

function getCookie(name) {
  const match = document.cookie.match(new RegExp(`(^| )${name}=([^;]+)`));
  return match ? decodeURIComponent(match[2]) : null;
}

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) };

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const csrfToken = getCookie('csrftoken');
  if (csrfToken && options.method && options.method !== 'GET') {
    headers['X-CSRFToken'] = csrfToken;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    ...options,
    headers,
    body:
      options.body instanceof FormData || options.body == null
        ? options.body
        : JSON.stringify(options.body),
  });

  const contentType = response.headers.get('content-type') || '';
  const isJson = contentType.includes('application/json');
  const data = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const message = typeof data === 'string'
      ? (data.trimStart().startsWith('<')
        ? `Server error (${response.status}). If this persists, ensure database migrations are applied.`
        : data)
      : (data?.detail || 'Request failed');
    const error = new Error(message);
    error.status = response.status;
    error.data = typeof data === 'object' ? data : null;
    throw error;
  }

  return data;
}

function unwrapList(data) {
  return data.results || data;
}

export const api = {
  ensureCsrf: () => request('/auth/csrf/'),
  login: (username, password) =>
    request('/auth/login/', { method: 'POST', body: { username, password } }),
  verifyMfa: (mfaToken, code) =>
    request('/auth/mfa/verify/', { method: 'POST', body: { mfa_token: mfaToken, code } }),
  getMfaSetup: () => request('/auth/mfa/setup/'),
  enableMfa: (code) => request('/auth/mfa/setup/', { method: 'POST', body: { code } }),
  getHealth: () => request('/health/'),
  logout: () => request('/auth/logout/', { method: 'POST' }),
  register: (payload) => request('/auth/register/', { method: 'POST', body: payload }),
  getMe: () => request('/auth/me/'),
  getRoles: () => request('/roles/'),
  getDashboard: () => request('/dashboard/'),
  getRecruitmentSummary: (query = '') =>
    request(`/recruitment/summary/${query ? `?${query}` : ''}`),
  getRecruitmentEEOReport: (query = '') =>
    request(`/recruitment/eeo-report/${query ? `?${query}` : ''}`),
  createOfferFromTemplate: (payload) =>
    request('/offers/from-template/', { method: 'POST', body: payload }),
  offerAction: (id, action) =>
    request(`/offers/${id}/${action}/`, { method: 'POST', body: {} }),
  getPublicOffer: (id) => request(`/offers/${id}/public/`),
  signOffer: (id, payload) =>
    request(`/offers/${id}/sign/`, { method: 'POST', body: payload }),
  moveApplicationStage: (applicationId, stageId) =>
    request(`/applications/${applicationId}/move_stage/`, { method: 'POST', body: { stage_id: stageId } }),
  completeOnboarding: (id, payload) =>
    request(`/hire-onboarding/${id}/complete/`, { method: 'POST', body: payload }),
  getCareersJobs: () => request('/careers/jobs/'),
  getCareersJob: (id) => request(`/careers/jobs/${id}/`),
  applyToCareersJob: (id, formData) =>
    request(`/careers/jobs/${id}/apply/`, { method: 'POST', body: formData }),
  getAuthConfig: () => request('/auth/config/'),
  getSsoConfig: () => request('/auth/sso/config/'),
  startSso: (provider) => request(`/auth/sso/${provider}/start/`),
  getOrgChart: () => request('/departments/org_chart/'),
  getWebhookEvents: () => request('/webhooks/events/'),
  getWebhookDeliveries: (id) => request(`/webhooks/${id}/deliveries/`),
  getWebhookDeliveryLog: (query = '') => request(`/webhooks/delivery-log/${query ? `?${query}` : ''}`),
  getApprovalWorkflows: () => request('/approval-workflows/'),
  getRetentionPolicies: () => request('/compliance/retention-policies/'),
  getRetentionPreview: () => request('/compliance/retention-policies/preview/'),
  updateRetentionPolicy: (id, payload) => api.update('compliance/retention-policies', id, payload),
  runRetentionPolicies: (dryRun = false) =>
    request('/compliance/retention-policies/run/', { method: 'POST', body: { dry_run: dryRun } }),
  downloadGdprExport: async (employeeId = null) => {
    const path = employeeId
      ? `/compliance/data-export/employees/${employeeId}/?download=1`
      : '/compliance/data-export/me/?download=1';
    const csrfToken = document.cookie.match(/(^| )csrftoken=([^;]+)/)?.[2];
    const response = await fetch(`/api/v1${path}`, {
      credentials: 'include',
      headers: csrfToken ? { 'X-CSRFToken': decodeURIComponent(csrfToken) } : {},
    });
    if (!response.ok) throw new Error('GDPR export failed');
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = employeeId ? `gdpr_export_${employeeId}.json` : 'my_data_export.json';
    link.click();
    window.URL.revokeObjectURL(url);
  },
  requestGDPRErasure: (employeeId, confirmEmail) =>
    request(`/compliance/erasure/${employeeId}/`, {
      method: 'POST',
      body: { confirm: confirmEmail },
    }),
  downloadAuditLog: async (format = 'csv', query = '') => {
    const params = new URLSearchParams(query);
    const csrfToken = document.cookie.match(/(^| )csrftoken=([^;]+)/)?.[2];
    const suffix = format === 'xlsx' ? '.xlsx' : '.csv';
    const response = await fetch(`/api/v1/audit-logs/export${suffix}/`, {
      credentials: 'include',
      headers: csrfToken ? { 'X-CSRFToken': decodeURIComponent(csrfToken) } : {},
    });
    if (!response.ok) throw new Error('Audit log export failed');
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `audit_log.${format}`;
    link.click();
    window.URL.revokeObjectURL(url);
  },
  getApprovalRequests: (query = '') =>
    request(`/approval-requests/${query ? `?${query}` : ''}`),
  approvalAction: (id, action, comment = '') =>
    request(`/approval-requests/${id}/${action}/`, {
      method: 'POST',
      body: { comment },
    }),
  syncLeavePolicies: (payload) =>
    request('/leave-policy-allocations/sync/', { method: 'POST', body: payload }),
  downloadPayroll: async (query = '', format = 'xlsx') => {
    const params = new URLSearchParams(query);
    params.set('format', format);
    const csrfToken = document.cookie.match(/(^| )csrftoken=([^;]+)/)?.[2];
    const response = await fetch(`/api/v1/payroll/export/?${params.toString()}`, {
      credentials: 'include',
      headers: csrfToken ? { 'X-CSRFToken': decodeURIComponent(csrfToken) } : {},
    });
    if (!response.ok) throw new Error('Payroll export failed');
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `payroll_export.${format}`;
    link.click();
    window.URL.revokeObjectURL(url);
  },
  getReportsAnalytics: () => request('/reports/analytics/'),
  getReportFilters: () => request('/reports/filters/'),
  getReport: (type, query = '') =>
    request(`/reports/${type}/${query ? `?${query}` : ''}`),

  downloadReport: async (type, query = '', format = 'xlsx') => {
    const params = new URLSearchParams(query);
    params.set('format', format);
    const csrfToken = document.cookie.match(/(^| )csrftoken=([^;]+)/)?.[2];
    const response = await fetch(`/api/v1/reports/${type}/?${params.toString()}`, {
      credentials: 'include',
      headers: csrfToken ? { 'X-CSRFToken': decodeURIComponent(csrfToken) } : {},
    });
    if (!response.ok) throw new Error('Export failed');
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${type}_report.${format}`;
    link.click();
    window.URL.revokeObjectURL(url);
  },

  list: (resource, query = '') =>
    request(`/${resource}/${query ? `?${query}` : ''}`).then(unwrapList),

  listRaw: (resource, query = '') =>
    request(`/${resource}/${query ? `?${query}` : ''}`),

  get: (resource, id) => request(`/${resource}/${id}/`),

  create: (resource, payload) =>
    request(`/${resource}/`, { method: 'POST', body: payload }),

  createForm: (resource, formData) =>
    request(`/${resource}/`, { method: 'POST', body: formData }),

  update: (resource, id, payload) =>
    request(`/${resource}/${id}/`, { method: 'PATCH', body: payload }),

  remove: (resource, id) =>
    request(`/${resource}/${id}/`, { method: 'DELETE' }),

  action: (resource, id, actionName, payload = {}) =>
    request(`/${resource}/${id}/${actionName}/`, { method: 'POST', body: payload }),

  collectionAction: (resource, actionName, payload = null, query = '') =>
    request(`/${resource}/${actionName}/${query ? `?${query}` : ''}`, {
      method: payload != null ? 'POST' : 'GET',
      body: payload,
    }),

  getUsers: () => request('/users/'),
  getRoles: () => request('/roles/'),
  createUser: (payload) => api.create('users', payload),
  updateUser: (id, payload) => api.update('users', id, payload),
  getMyFeedbackRequests: () => request('/feedback-requests/mine/'),
  submitFeedback: (requestId, payload) =>
    api.action('feedback-requests', requestId, 'submit', payload),
  getFeedbackRoundDetail: (id) => api.get('feedback-rounds', id),
  createFeedbackRequests: (roundId, requests) =>
    api.action('feedback-rounds', roundId, 'create-requests', { requests }),
  getEmployeeFeedbackSummary: (employeeId, roundId = '') => {
    const q = new URLSearchParams({ employee: employeeId });
    if (roundId) q.set('round', roundId);
    return api.collectionAction('feedback-requests', 'employee-summary', null, q.toString());
  },

  getAvailableSurveys: () => request('/surveys/available/'),
  getSurveyResults: (surveyId) => request(`/surveys/${surveyId}/results/`),
  submitSurvey: (surveyId, answers) =>
    request(`/surveys/${surveyId}/submit/`, { method: 'POST', body: { answers } }),

  // Convenience shortcuts
  getEmployees: (q = '') => api.list('employees', q ? `q=${encodeURIComponent(q)}` : ''),
  getEmployee: (id) => api.get('employees', id),
  createEmployee: (payload) => api.create('employees', payload),
  updateEmployee: (id, payload) => api.update('employees', id, payload),
  terminateEmployee: (id, payload) => api.action('employees', id, 'terminate', payload),
  getDepartments: () => api.list('departments'),
  createDepartment: (payload) => api.create('departments', payload),
  updateDepartment: (id, payload) => api.update('departments', id, payload),
  deleteDepartment: (id) => api.remove('departments', id),
};
