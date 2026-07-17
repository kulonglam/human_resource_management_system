import { expect, test } from '@playwright/test';
import { E2E_CREDENTIALS, backendAvailable, loginViaUi } from './helpers.js';

test.describe('approvals queue', () => {
  test.beforeEach(async ({ request }, testInfo) => {
    if (!(await backendAvailable(request))) {
      testInfo.skip(true, 'Backend not reachable');
    }
  });

  test('admin can open approvals page', async ({ page }) => {
    await loginViaUi(page, E2E_CREDENTIALS.admin);
    await page.goto('/approvals');
    await expect(page.getByRole('heading', { name: /approvals/i })).toBeVisible({ timeout: 15_000 });
  });
});
