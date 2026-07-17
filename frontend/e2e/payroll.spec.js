import { expect, test } from '@playwright/test';
import { E2E_CREDENTIALS, backendAvailable, loginViaUi } from './helpers.js';

test.describe('payroll', () => {
  test.beforeEach(async ({ request }, testInfo) => {
    if (!(await backendAvailable(request))) {
      testInfo.skip(true, 'Backend not reachable');
    }
  });

  test('admin can open payroll module and see statutory exports', async ({ page }) => {
    await loginViaUi(page, E2E_CREDENTIALS.admin);
    await page.goto('/payroll');
    await expect(page.getByRole('heading', { name: /^payroll$/i })).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/statutory filing exports/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /PAYE CSV/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /NSSF CSV/i })).toBeVisible();
  });
});
