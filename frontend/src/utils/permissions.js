export const PERMISSION_LABELS = {
  'payroll.view': 'View payroll',
  'payroll.manage': 'Manage payroll',
  'reports.manage': 'Manage reports',
  'sensitive.view': 'View sensitive employee data',
  'attendance.approve': 'Approve attendance',
  'documents.manage': 'Manage documents',
};

export const ALL_PERMISSIONS = Object.keys(PERMISSION_LABELS);

export function hasPermission(user, permission) {
  if (!user) return false;
  if (user.is_admin) return true;
  return Array.isArray(user.permissions) && user.permissions.includes(permission);
}

export function isEmployeeUser(user) {
  return Boolean(user) && !user.is_admin && !user.is_manager;
}

export function canManageHr(user) {
  return Boolean(user?.is_admin || user?.is_manager);
}

export function canViewPayroll(user) {
  return hasPermission(user, 'payroll.view');
}

export function canManagePayroll(user) {
  return hasPermission(user, 'payroll.manage');
}

export function canManageReports(user) {
  return hasPermission(user, 'reports.manage');
}

export function canViewSensitive(user) {
  return hasPermission(user, 'sensitive.view');
}

export function canApproveAttendance(user) {
  return hasPermission(user, 'attendance.approve');
}
