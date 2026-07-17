import { expect, test } from '@playwright/test';
import { E2E_CREDENTIALS, backendAvailable, loginViaUi } from './helpers.js';

test.describe('ops center', () => {
  test.beforeEach(async ({ request }, testInfo) => {
    if (!(await backendAvailable(request))) {
      testInfo.skip(true, 'Backend not reachable');
    }
  });

  test('admin sees ops status, SLOs, alerts and runbooks', async ({ page }) => {
    await loginViaUi(page, E2E_CREDENTIALS.admin);
    await page.goto('/settings/ops');

    await expect(page.getByRole('heading', { name: /ops center|operations/i })).toBeVisible({ timeout: 20_000 });
    // The page must not render blank: SLO + alerts cards should appear.
    await expect(page.getByText(/slo/i).first()).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText(/alert/i).first()).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText(/runbook/i).first()).toBeVisible({ timeout: 20_000 });
  });

  test('employee role cannot open ops center', async ({ page }) => {
    await loginViaUi(page, E2E_CREDENTIALS.employee);
    await page.goto('/settings/ops');
    await expect(page).not.toHaveURL(/\/settings\/ops/, { timeout: 15_000 });
  });
});
