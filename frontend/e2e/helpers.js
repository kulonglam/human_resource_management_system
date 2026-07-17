/** Shared helpers for Playwright E2E tests against the HRMIS stack. */

export const E2E_MFA_SECRET = 'E2ETESTMFASECRETKEY000000';

export const E2E_CREDENTIALS = {
  admin: {
    username: process.env.E2E_ADMIN_USER || 'admin',
    password: process.env.E2E_ADMIN_PASSWORD || 'Admin@HRMIS2026!',
  },
  employee: {
    username: process.env.E2E_EMPLOYEE_USER || 'employee',
    password: process.env.E2E_EMPLOYEE_PASSWORD || 'Employee@HRMIS2026!',
  },
};

export async function backendAvailable(request) {
  try {
    const health = await request.get('/api/v1/health/');
    return health.ok();
  } catch {
    return false;
  }
}

export async function loginViaUi(page, { username, password }) {
  await page.goto('/login');
  await page.getByLabel('Username').fill(username);
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: /login/i }).click();
  await page.waitForURL(/\/dashboard/, { timeout: 20_000 });
}

export async function createLeaveViaApi(page, payload) {
  return page.evaluate(async (body) => {
    const csrfMatch = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    const csrf = csrfMatch ? decodeURIComponent(csrfMatch[1]) : '';
    const response = await fetch('/api/v1/leaves/', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...(csrf ? { 'X-CSRFToken': csrf } : {}),
      },
      body: JSON.stringify(body),
    });
    const data = await response.json().catch(() => ({}));
    return { ok: response.ok, status: response.status, data };
  }, payload);
}

export function futureLeaveDates() {
  const year = new Date().getFullYear();
  const month = String(new Date().getMonth() + 1).padStart(2, '0');
  const day = String(Math.min(new Date().getDate() + 5, 25)).padStart(2, '0');
  const start = `${year}-${month}-${day}`;
  const endDay = String(Math.min(Number(day) + 1, 26)).padStart(2, '0');
  const end = `${year}-${month}-${endDay}`;
  return { start, end };
}
