import { expect, test } from '@playwright/test';
import { E2E_CREDENTIALS, backendAvailable, loginViaUi } from './helpers.js';

test.describe('reports', () => {
  test.beforeEach(async ({ request }, testInfo) => {
    if (!(await backendAvailable(request))) {
      testInfo.skip(true, 'Backend not reachable');
    }
  });

  test('admin can open reports overview and switch report tabs', async ({ page }) => {
    await loginViaUi(page, E2E_CREDENTIALS.admin);
    await page.goto('/reports');
    await expect(page.getByRole('heading', { name: /reports/i })).toBeVisible({ timeout: 15_000 });

    // Overview stats render.
    await expect(page.getByText(/total employees|headcount/i).first()).toBeVisible({ timeout: 15_000 });

    // Switch to the leave report tab and run it.
    await page.getByRole('button', { name: /^leave$/i }).click();
    await expect(page.getByRole('button', { name: /generate|run/i }).first()).toBeVisible({ timeout: 15_000 });
  });

  test('employee role is bounced away from reports', async ({ page }) => {
    await loginViaUi(page, E2E_CREDENTIALS.employee);
    await page.goto('/reports');
    await expect(page).not.toHaveURL(/\/reports/, { timeout: 15_000 });
  });
});
