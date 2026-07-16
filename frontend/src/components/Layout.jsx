import { useState } from 'react';
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import NotificationBell from './NotificationBell';
import { useAuth } from '../context/AuthContext';
import { canManageReports, canViewPayroll } from '../utils/permissions';

const navItems = [
  { to: '/dashboard', icon: 'bi-house-door', label: 'Dashboard' },
  { to: '/employees', icon: 'bi-people', label: 'Employees' },
  { to: '/departments', icon: 'bi-building', label: 'Departments' },
  { to: '/attendance', icon: 'bi-calendar-check', label: 'Attendance' },
  { to: '/leaves', icon: 'bi-calendar-x', label: 'Leaves' },
  { to: '/recruitment', icon: 'bi-briefcase', label: 'Recruitment' },
  { to: '/payroll', icon: 'bi-cash-coin', label: 'Payroll', requiresPayroll: true },
  { to: '/performance', icon: 'bi-graph-up-arrow', label: 'Performance' },
  { to: '/training', icon: 'bi-book', label: 'Training' },
  { to: '/reports', icon: 'bi-bar-chart', label: 'Reports', requiresReports: true },
  { to: '/documents', icon: 'bi-folder2-open', label: 'Documents' },
  { to: '/exits', icon: 'bi-door-closed', label: 'Exit Management' },
  { to: '/assets', icon: 'bi-laptop', label: 'Assets' },
  { to: '/shifts', icon: 'bi-clock', label: 'Shifts' },
  { to: '/expenses', icon: 'bi-receipt', label: 'Expenses' },
  { to: '/benefits', icon: 'bi-heart-pulse', label: 'Benefits' },
  { to: '/leave-policies', icon: 'bi-file-earmark-text', label: 'Leave Policies', managerOnly: true },
  { to: '/discipline', icon: 'bi-exclamation-triangle', label: 'Discipline' },
  { to: '/surveys', icon: 'bi-clipboard-data', label: 'Surveys' },
  { to: '/kin', icon: 'bi-person-hearts', label: 'Next of Kin' },
];

const managerNavItems = [
  { to: '/approvals', icon: 'bi-inbox', label: 'Approvals' },
  { to: '/workforce-structure', icon: 'bi-diagram-3', label: 'Workforce Structure' },
];

const adminNavItems = [
  { to: '/approvals', icon: 'bi-inbox', label: 'Approvals' },
  { to: '/settings/users', icon: 'bi-people-fill', label: 'Users' },
  { to: '/org-chart', icon: 'bi-diagram-3', label: 'Org Chart' },
  { to: '/workforce-structure', icon: 'bi-person-workspace', label: 'Workforce Structure' },
  { to: '/audit-logs', icon: 'bi-journal-text', label: 'Audit Log' },
  { to: '/settings/sensitive-access', icon: 'bi-shield-exclamation', label: 'Sensitive Access' },
  { to: '/settings/ops', icon: 'bi-hdd-rack', label: 'Operations' },
  { to: '/settings/security', icon: 'bi-shield-lock', label: 'Security' },
  { to: '/settings/integrations', icon: 'bi-plug', label: 'Integrations' },
  { to: '/settings/compliance', icon: 'bi-shield-check', label: 'Compliance' },
];

function canSeeNavItem(item, user) {
  if (item.requiresReports && !canManageReports(user)) return false;
  if (item.requiresPayroll && !canViewPayroll(user)) return false;
  if (item.managerOnly && !user?.is_admin && !user?.is_manager) return false;
  return true;
}

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const closeSidebar = () => setSidebarOpen(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <>
      <div className={`sidebar ${sidebarOpen ? 'active' : ''}`} id="sidebarNav">
        <Link to="/dashboard" className="sidebar-brand" onClick={closeSidebar}>
          <i className="bi bi-house" /> FCA HRMIS
        </Link>

        <nav className="sidebar-nav">
          {navItems
            .filter((item) => canSeeNavItem(item, user))
            .map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => (isActive ? 'active' : undefined)}
              onClick={closeSidebar}
            >
              <i className={`bi ${item.icon}`} />
              <span>{item.label}</span>
            </NavLink>
            ))}

          {user?.is_manager && !user?.is_admin && (
            <>
              <div className="sidebar-section-label px-3 py-2 small text-muted text-uppercase">
                Management
              </div>
              {managerNavItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) => (isActive ? 'active' : undefined)}
                  onClick={closeSidebar}
                >
                  <i className={`bi ${item.icon}`} />
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </>
          )}

          {user?.is_admin && (
            <>
              <div className="sidebar-section-label px-3 py-2 small text-muted text-uppercase">
                Administration
              </div>
              {adminNavItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) => (isActive ? 'active' : undefined)}
                  onClick={closeSidebar}
                >
                  <i className={`bi ${item.icon}`} />
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </>
          )}
        </nav>
      </div>

      {sidebarOpen && (
        <div
          className="sidebar-backdrop active"
          onClick={closeSidebar}
          aria-hidden="true"
        />
      )}

      <div className="main-content">
        <div className="top-bar">
          <button
            type="button"
            className="btn btn-outline-secondary toggle-sidebar"
            onClick={() => setSidebarOpen((open) => !open)}
            aria-label={sidebarOpen ? 'Close navigation menu' : 'Open navigation menu'}
          >
            <i className="bi bi-list" />
          </button>
          <div className="top-bar-user d-flex align-items-center gap-2">
            <NotificationBell />
            <span className="top-bar-username">
              <i className="bi bi-person-circle" /> {user?.username}
            </span>
            <button
              type="button"
              className="btn btn-danger btn-sm top-bar-logout"
              onClick={handleLogout}
            >
              <i className="bi bi-box-arrow-right" />
              <span className="top-bar-logout-label">Logout</span>
            </button>
          </div>
        </div>

        <div className="content">
          <Outlet />
        </div>
      </div>

      <nav className="mobile-bottom-nav d-md-none" aria-label="Quick manager actions">
        <NavLink to="/dashboard" onClick={closeSidebar}><i className="bi bi-house" /><span>Home</span></NavLink>
        <NavLink to="/approvals" onClick={closeSidebar}><i className="bi bi-inbox" /><span>Approvals</span></NavLink>
        <NavLink to="/leaves" onClick={closeSidebar}><i className="bi bi-calendar-x" /><span>Leave</span></NavLink>
        {canViewPayroll(user) && (
          <NavLink to="/payroll" onClick={closeSidebar}><i className="bi bi-cash-coin" /><span>Payroll</span></NavLink>
        )}
        <NavLink to="/employees" onClick={closeSidebar}><i className="bi bi-people" /><span>People</span></NavLink>
      </nav>
    </>
  );
}
