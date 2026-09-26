import { describe, expect, it } from 'vitest';
import {
  canManageHr,
  canManageReports,
  canViewPayroll,
  hasPermission,
  isEmployeeUser,
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

  it('hides payroll from employees without payroll.view', () => {
    const employee = { is_admin: false, permissions: [], linked_employee_id: 12 };
    expect(canViewPayroll(employee)).toBe(false);
  });

  it('treats non-admin non-manager users as employees', () => {
    const employee = { is_admin: false, is_manager: false };
    expect(isEmployeeUser(employee)).toBe(true);
    expect(canManageHr(employee)).toBe(false);
    expect(canManageHr({ is_admin: false, is_manager: true })).toBe(true);
    expect(canManageHr({ is_admin: true })).toBe(true);
  });
});
