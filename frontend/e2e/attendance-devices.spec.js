import { expect, test } from '@playwright/test';
import { E2E_CREDENTIALS, backendAvailable, loginViaUi } from './helpers.js';

test.describe('attendance devices', () => {
  test.beforeEach(async ({ request }, testInfo) => {
    if (!(await backendAvailable(request))) {
      testInfo.skip(true, 'Backend not reachable');
    }
  });

  test('admin can open attendance and switch to Devices tab', async ({ page }) => {
    await loginViaUi(page, E2E_CREDENTIALS.admin);
    await page.goto('/attendance');

    await expect(page.getByRole('heading', { name: /attendance/i })).toBeVisible({ timeout: 15_000 });

    const devicesTab = page.getByRole('tab', { name: /^devices$/i })
      .or(page.getByRole('button', { name: /^devices$/i }))
      .or(page.getByText(/^devices$/i));
    await expect(devicesTab.first()).toBeVisible({ timeout: 15_000 });
    await devicesTab.first().click();

    await expect(
      page.getByText(/device|device code|biometric/i).first(),
    ).toBeVisible({ timeout: 15_000 });
  });

  test('admin can open Device punches tab', async ({ page }) => {
    await loginViaUi(page, E2E_CREDENTIALS.admin);
    await page.goto('/attendance');

    const punchesTab = page.getByRole('tab', { name: /device punches/i })
      .or(page.getByRole('button', { name: /device punches/i }))
      .or(page.getByText(/device punches/i));
    await expect(punchesTab.first()).toBeVisible({ timeout: 15_000 });
    await punchesTab.first().click();

    await expect(page.getByText(/punch|device|when/i).first()).toBeVisible({ timeout: 15_000 });
  });
});
