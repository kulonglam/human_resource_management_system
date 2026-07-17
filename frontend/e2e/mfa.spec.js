import { execSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { expect, test } from '@playwright/test';
import { authenticator } from 'otplib';
import { E2E_CREDENTIALS, E2E_MFA_SECRET, backendAvailable, loginViaUi } from './helpers.js';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');

function runManageCommand(args) {
  const python = process.env.E2E_PYTHON || 'python';
  execSync(`${python} manage.py ${args}`, {
    cwd: repoRoot,
    stdio: 'pipe',
    env: {
      ...process.env,
      SECRET_KEY: process.env.SECRET_KEY || 'test-secret-key-not-for-production',
      ENFORCE_MFA_FOR_ADMINS: 'False',
      ENFORCE_MFA_FOR_MANAGERS: 'False',
      ENFORCE_MFA_FOR_PAYROLL: 'False',
      REQUIRE_FIELD_ENCRYPTION_KEY: 'False',
      FIELD_ENCRYPTION_KEY: process.env.FIELD_ENCRYPTION_KEY || 'test-field-encryption-key-for-ci',
    },
  });
}

test.describe('multi-factor authentication', () => {
  test.describe.configure({ mode: 'serial' });

  test.beforeEach(async ({ request }, testInfo) => {
    if (!(await backendAvailable(request))) {
      testInfo.skip(true, 'Backend not reachable');
    }
  });

  test('admin can open MFA security settings', async ({ page }) => {
    await loginViaUi(page, E2E_CREDENTIALS.admin);
    await page.goto('/settings/security');
    await expect(
      page.getByRole('heading', { name: /enable multi-factor authentication/i }),
    ).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/authenticator/i).first()).toBeVisible();
  });

  test.describe('enabled login', () => {
    test.beforeAll(() => {
      runManageCommand('prepare_e2e_mfa');
    });

    test.afterAll(() => {
      runManageCommand('prepare_e2e_mfa --disable');
    });

    test('admin with MFA enabled completes login challenge', async ({ page }) => {
      await page.goto('/login');
      await page.getByLabel('Username').fill(E2E_CREDENTIALS.admin.username);
      await page.getByLabel('Password').fill(E2E_CREDENTIALS.admin.password);
      await page.getByRole('button', { name: /login/i }).click();

      await expect(page.getByLabel('Verification code')).toBeVisible({ timeout: 15_000 });
      const code = authenticator.generate(E2E_MFA_SECRET);
      await page.getByLabel('Verification code').fill(code);
      await page.getByRole('button', { name: /^verify$/i }).click();

      await page.waitForURL(/\/dashboard/, { timeout: 20_000 });
      await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible({ timeout: 15_000 });
    });
  });
});
