import { describe, expect, it } from 'vitest';
import {
  canManageReports,
  canViewPayroll,
  hasPermission,
} from './permissions';

describe('permissions', () => {
  it('grants admins all permissions', () => {
    const admin = { is_admin: true, permissions: [] };
    expect(hasPermission(admin, 'payroll.manage')).toBe(true);
    expect(canManageReports(admin)).toBe(true);
  });

  it('checks explicit manager permissions', () => {
    const manager = { is_admin: false, permissions: ['reports.manage'] };
    expect(canManageReports(manager)).toBe(true);
    expect(canViewPayroll(manager)).toBe(false);
  });

  it('allows employees to view own payroll linkage', () => {
    const employee = { is_admin: false, permissions: [], linked_employee_id: 12 };
    expect(canViewPayroll(employee)).toBe(true);
  });
});
