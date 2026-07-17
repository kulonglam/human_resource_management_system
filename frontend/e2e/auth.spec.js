import { expect, test } from '@playwright/test';
import { E2E_CREDENTIALS, backendAvailable, loginViaUi } from './helpers.js';

test.describe('authentication', () => {
  test.beforeEach(async ({ request }, testInfo) => {
    if (!(await backendAvailable(request))) {
      testInfo.skip(true, 'Backend not reachable');
    }
  });

  test('admin can log in and reach dashboard', async ({ page }) => {
    await loginViaUi(page, E2E_CREDENTIALS.admin);
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible({ timeout: 15_000 });
  });

  test('employee can log in and reach dashboard', async ({ page }) => {
    await loginViaUi(page, E2E_CREDENTIALS.employee);
    await expect(page).toHaveURL(/\/dashboard/);
  });
});
