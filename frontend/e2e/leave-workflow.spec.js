import { expect, test } from '@playwright/test';
import {
  E2E_CREDENTIALS,
  backendAvailable,
  createLeaveViaApi,
  futureLeaveDates,
  loginViaUi,
} from './helpers.js';

test.describe('leave workflow', () => {
  test.beforeEach(async ({ request }, testInfo) => {
    if (!(await backendAvailable(request))) {
      testInfo.skip(true, 'Backend not reachable at /api/v1/health/ — start Django on :8000 and Vite on :5173');
    }
  });

  test('employee submits leave and admin approves via approvals UI', async ({ page }) => {
    const { start, end } = futureLeaveDates();

    await loginViaUi(page, E2E_CREDENTIALS.employee);
    const createResult = await createLeaveViaApi(page, {
      leave_type: 'annual',
      start_date: start,
      end_date: end,
      reason: 'E2E leave request',
    });
    expect(createResult.ok, JSON.stringify(createResult.data)).toBeTruthy();
    expect(createResult.data.status).toBe('pending');

    await page.getByRole('button', { name: 'Logout' }).click();

    await loginViaUi(page, E2E_CREDENTIALS.admin);
    await page.goto('/approvals');
    await expect(page.getByRole('heading', { name: /approvals/i })).toBeVisible({ timeout: 15_000 });

    const approveBtn = page.getByRole('button', { name: 'Approve' }).first();
    await expect(approveBtn).toBeVisible({ timeout: 15_000 });
    await approveBtn.click();

    await expect(page.getByText(/no pending|all caught up|0 pending/i)).toBeVisible({ timeout: 15_000 }).catch(async () => {
      await expect(page.getByRole('button', { name: 'Approve' })).toHaveCount(0);
    });
  });
});
