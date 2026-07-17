import { expect, test } from '@playwright/test';
import { E2E_CREDENTIALS, backendAvailable, loginViaUi } from './helpers.js';

test.describe('employee directory', () => {
  test.beforeEach(async ({ request }, testInfo) => {
    if (!(await backendAvailable(request))) {
      testInfo.skip(true, 'Backend not reachable');
    }
  });

  test('admin can browse the directory and open an employee profile', async ({ page }) => {
    await loginViaUi(page, E2E_CREDENTIALS.admin);
    await page.goto('/employees');
    await expect(page.getByRole('heading', { name: /employees/i })).toBeVisible({ timeout: 15_000 });

    // At least one employee row/card links to a detail page.
    const detailLink = page.locator('a[href^="/employees/"]').first();
    await expect(detailLink).toBeVisible({ timeout: 15_000 });
    await detailLink.click();
    await page.waitForURL(/\/employees\/\d+/, { timeout: 15_000 });

    // Profile view shows core identity fields.
    await expect(page.getByText(/job title|department|email/i).first()).toBeVisible({ timeout: 15_000 });
  });

  test('directory search narrows results', async ({ page }) => {
    await loginViaUi(page, E2E_CREDENTIALS.admin);
    await page.goto('/employees');

    const search = page.getByPlaceholder(/search/i).first();
    await expect(search).toBeVisible({ timeout: 15_000 });
    await search.fill('zzz-no-such-employee-zzz');
    await expect(page.getByText(/no employees|no results|nothing found/i)).toBeVisible({ timeout: 15_000 }).catch(async () => {
      await expect(page.locator('a[href^="/employees/"]')).toHaveCount(0, { timeout: 15_000 });
    });
  });

  test('employee role cannot open the new-employee form', async ({ page }) => {
    await loginViaUi(page, E2E_CREDENTIALS.employee);
    await page.goto('/employees/new');
    // PermissionRoute should bounce non-admins away from the create form.
    await expect(page).not.toHaveURL(/\/employees\/new/, { timeout: 15_000 });
  });
});
