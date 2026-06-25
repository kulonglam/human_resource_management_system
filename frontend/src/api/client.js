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
    const error = new Error(data?.detail || 'Request failed');
    error.status = response.status;
    error.data = data;
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
  getAuthConfig: () => request('/auth/config/'),
  getSsoConfig: () => request('/auth/sso/config/'),
  startSso: (provider) => request(`/auth/sso/${provider}/start/`),
  getOrgChart: () => request('/departments/org_chart/'),
  getWebhookEvents: () => request('/webhooks/events/'),
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
