import { expect, test } from '@playwright/test';
import { E2E_CREDENTIALS, backendAvailable, loginViaUi } from './helpers.js';

test.describe('mobile clock PWA', () => {
  test.beforeEach(async ({ request }, testInfo) => {
    if (!(await backendAvailable(request))) {
      testInfo.skip(true, 'Backend not reachable');
    }
  });

  test('employee can open mobile clock and see punch controls', async ({ page }) => {
    await loginViaUi(page, E2E_CREDENTIALS.employee);
    await page.goto('/mobile');

    await expect(page.getByText(/hrmis mobile/i)).toBeVisible({ timeout: 15_000 });
    await expect(page.getByRole('button', { name: /clock in/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /clock out/i })).toBeVisible();
    await expect(page.getByText(/offline|online/i).first()).toBeVisible();
    await expect(page.getByText(/queue on this device when offline/i)).toBeVisible();
  });

  test('clock in records a punch when online', async ({ page }) => {
    await loginViaUi(page, E2E_CREDENTIALS.employee);
    await page.goto('/mobile');
    await page.getByRole('button', { name: /clock in/i }).click();
    await expect(page.getByRole('status').or(page.getByText(/recorded|queued|clock-in/i))).toBeVisible({
      timeout: 15_000,
    });
  });
});
