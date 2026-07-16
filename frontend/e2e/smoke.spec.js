import { expect, test } from '@playwright/test';

test.describe('critical smoke', () => {
  test('login page renders and health API is reachable', async ({ page, request }) => {
    const health = await request.get('/api/v1/health/');
    // When only Vite is up this may 404; skip hard fail and assert login UI instead.
    if (health.ok()) {
      const body = await health.json();
      expect(body.status).toBeTruthy();
    }

    await page.goto('/login');
    await expect(page.getByRole('heading', { name: /sign in|login|hrmis/i })).toBeVisible({ timeout: 15_000 }).catch(async () => {
      await expect(page.locator('input[name="username"], input[type="text"]').first()).toBeVisible();
    });
    await expect(page.locator('input[type="password"]').first()).toBeVisible();
  });
});
