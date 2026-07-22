import { useState } from 'react';
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import ConfirmModal from './ConfirmModal';
import NotificationBell from './NotificationBell';
import { useAuth } from '../context/AuthContext';
import { canManageReports, canViewPayroll } from '../utils/permissions';

const navItems = [
  { to: '/dashboard', icon: 'bi-house-door', label: 'Dashboard' },
  { to: '/employees', icon: 'bi-people', label: 'Employees' },
  { to: '/departments', icon: 'bi-building', label: 'Departments' },
  { to: '/attendance', icon: 'bi-calendar-check', label: 'Attendance' },
  { to: '/mobile', icon: 'bi-phone', label: 'Mobile clock' },
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
  { to: '/org-chart', icon: 'bi-diagram-3', label: 'Org Chart' },
  { to: '/workforce-structure', icon: 'bi-person-workspace', label: 'Workforce Structure' },
  { to: '/settings', icon: 'bi-gear', label: 'Settings' },
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
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);

  const closeSidebar = () => setSidebarOpen(false);

  const handleLogout = async () => {
    setLoggingOut(true);
    try {
      await logout();
      navigate('/login');
    } finally {
      setLoggingOut(false);
      setShowLogoutConfirm(false);
    }
  };

  return (
    <>
      <div className={`sidebar ${sidebarOpen ? 'active' : ''}`} id="sidebarNav">
        <Link to="/dashboard" className="sidebar-brand" onClick={closeSidebar}>
          <span className="sidebar-brand-mark" aria-hidden="true">
            <i className="bi bi-hexagon-fill" />
          </span>
          <span className="sidebar-brand-text">FCA HRMIS</span>
          <span className="sidebar-brand-tag">Workforce platform</span>
        </Link>

        <nav className="sidebar-nav" aria-label="Primary">
          {navItems
            .filter((item) => canSeeNavItem(item, user))
            .map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => (isActive ? 'active' : undefined)}
              onClick={closeSidebar}
            >
              <i className={`bi ${item.icon}`} aria-hidden="true" />
              <span>{item.label}</span>
            </NavLink>
            ))}

          {user?.is_manager && !user?.is_admin && (
            <>
              <div className="sidebar-section-label">Management</div>
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
              <div className="sidebar-section-label">Administration</div>
              {adminNavItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/settings' ? false : undefined}
                  className={({ isActive }) => (isActive ? 'active' : undefined)}
                  onClick={closeSidebar}
                >
                  <i className={`bi ${item.icon}`} />
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </>
          )}

          {!user?.is_admin && (
            <NavLink
              to="/settings"
              className={({ isActive }) => (isActive ? 'active' : undefined)}
              onClick={closeSidebar}
            >
              <i className="bi bi-gear" />
              <span>Settings</span>
            </NavLink>
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
          <div className="top-bar-user">
            <NotificationBell />
            <span className="top-bar-username">
              <i className="bi bi-person-circle" aria-hidden="true" />
              {user?.username}
            </span>
            <button
              type="button"
              className="btn btn-danger btn-sm top-bar-logout"
              onClick={() => setShowLogoutConfirm(true)}
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

      <ConfirmModal
        open={showLogoutConfirm}
        title="Log out"
        message="Are you sure you want to log out of FCA HRMIS?"
        confirmLabel="Log out"
        confirmVariant="danger"
        busy={loggingOut}
        onCancel={() => setShowLogoutConfirm(false)}
        onConfirm={handleLogout}
      />
    </>
  );
}
