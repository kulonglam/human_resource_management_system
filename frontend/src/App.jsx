import { Navigate, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import PermissionRoute from './components/PermissionRoute';
import { canManageReports, canViewPayroll } from './utils/permissions';
import {
  attendanceTabs, workforceStructureTabs,
} from './config/hrModules';
import {
  exitTabs, assetTabs, shiftTabs,
  expenseTabs, benefitTabs, disciplineTabs, kinTabs,
} from './config/opsModules';
import ComplianceSettings from './pages/ComplianceSettings';
import Documents from './pages/Documents';
import DashboardPage from './pages/DashboardPage';
import Departments from './pages/Departments';
import EmployeeDetail from './pages/EmployeeDetail';
import EmployeeForm from './pages/EmployeeForm';
import Employees from './pages/Employees';
import Approvals from './pages/Approvals';
import AuditLogs from './pages/AuditLogs';
import IntegrationsSettings from './pages/IntegrationsSettings';
import LeavePolicies from './pages/LeavePolicies';
import Leaves from './pages/Leaves';
import Login from './pages/Login';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import Privacy from './pages/Privacy';
import OrgChart from './pages/OrgChart';
import ModulePage from './pages/ModulePage';
import Payroll from './pages/Payroll';
import Performance from './pages/Performance';
import RecordDetail from './pages/RecordDetail';
import Register from './pages/Register';
import Reports from './pages/Reports';
import UsersSettings from './pages/UsersSettings';
import SensitiveAccessLogs from './pages/SensitiveAccessLogs';
import OpsCenter from './pages/OpsCenter';
import Settings from './pages/Settings';
import SecuritySettings from './pages/SecuritySettings';
import Surveys from './pages/Surveys';
import SurveyTake from './pages/SurveyTake';
import Training from './pages/Training';
import Recruitment from './pages/Recruitment';
import ApplicationDetail from './pages/ApplicationDetail';
import Careers from './pages/Careers';
import CareerApply from './pages/CareerApply';
import OfferSign from './pages/OfferSign';
import MobileClock from './pages/MobileClock';

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/privacy" element={<Privacy />} />
      <Route path="/register" element={<Register />} />
      <Route path="/mobile" element={<MobileClock />} />
      <Route path="/careers" element={<Careers />} />
      <Route path="/careers/:jobId" element={<CareerApply />} />
      <Route path="/offers/:offerId" element={<OfferSign />} />

      <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="approvals" element={<PermissionRoute check={(u) => u.is_admin || u.is_manager}><Approvals /></PermissionRoute>} />
        <Route path="employees" element={<Employees />} />
        <Route path="employees/new" element={<PermissionRoute check={(u) => u.is_admin}><EmployeeForm /></PermissionRoute>} />
        <Route path="employees/:id" element={<EmployeeDetail />} />
        <Route path="employees/:id/edit" element={<PermissionRoute check={(u) => u.is_admin || u.is_manager}><EmployeeForm /></PermissionRoute>} />
        <Route path="departments" element={<Departments />} />
        <Route path="attendance" element={<ModulePage title="Attendance" icon="bi-calendar-check" tabs={attendanceTabs} />} />
        <Route path="leaves" element={<Leaves />} />
        <Route path="recruitment" element={<PermissionRoute check={(u) => u.is_admin || u.is_manager}><Recruitment /></PermissionRoute>} />
        <Route path="recruitment/applications/:id" element={<PermissionRoute check={(u) => u.is_admin || u.is_manager}><ApplicationDetail /></PermissionRoute>} />
        <Route path="payroll" element={<PermissionRoute check={canViewPayroll}><Payroll /></PermissionRoute>} />
        <Route path="workforce-structure" element={<PermissionRoute check={(u) => u.is_admin || u.is_manager}><ModulePage title="Workforce Structure" icon="bi-diagram-3" tabs={workforceStructureTabs} passUser /></PermissionRoute>} />
        <Route path="performance" element={<Performance />} />
        <Route path="performance/goals/:id" element={<RecordDetail configKey="performance-goals" />} />
        <Route path="performance/appraisals/:id" element={<RecordDetail configKey="performance-appraisals" />} />
        <Route path="training/courses/:id" element={<RecordDetail configKey="training-courses" />} />
        <Route path="training/development-plans/:id" element={<RecordDetail configKey="development-plans" />} />
        <Route path="recruitment/jobs/:id" element={<PermissionRoute check={(u) => u.is_admin || u.is_manager}><RecordDetail configKey="jobs" /></PermissionRoute>} />
        <Route path="exits/:id" element={<RecordDetail configKey="exit-processes" />} />
        <Route path="training" element={<Training />} />
        <Route path="reports" element={<PermissionRoute check={canManageReports}><Reports /></PermissionRoute>} />
        <Route path="documents" element={<Documents />} />
        <Route path="org-chart" element={<PermissionRoute check={(u) => u.is_admin}><OrgChart /></PermissionRoute>} />
        <Route path="settings/integrations" element={<PermissionRoute check={(u) => u.is_admin}><IntegrationsSettings /></PermissionRoute>} />
        <Route path="exits" element={<ModulePage title="Exit Management" icon="bi-door-closed" tabs={exitTabs} />} />
        <Route path="assets" element={<ModulePage title="Assets" icon="bi-laptop" tabs={assetTabs} />} />
        <Route path="shifts" element={<ModulePage title="Shifts" icon="bi-clock" tabs={shiftTabs} />} />
        <Route path="expenses" element={<ModulePage title="Expenses" icon="bi-receipt" tabs={expenseTabs} />} />
        <Route path="benefits" element={<ModulePage title="Benefits" icon="bi-heart-pulse" tabs={benefitTabs} />} />
        <Route path="leave-policies" element={<PermissionRoute check={(u) => u.is_admin || u.is_manager}><LeavePolicies /></PermissionRoute>} />
        <Route path="discipline" element={<ModulePage title="Discipline" icon="bi-exclamation-triangle" tabs={disciplineTabs} />} />
        <Route path="surveys" element={<Surveys />} />
        <Route path="surveys/:id/take" element={<SurveyTake />} />
        <Route path="kin" element={<ModulePage title="Next of Kin" icon="bi-people" tabs={kinTabs} />} />
        <Route path="audit-logs" element={<PermissionRoute check={(u) => u.is_admin}><AuditLogs /></PermissionRoute>} />
        <Route path="settings" element={<Settings />} />
        <Route path="settings/sensitive-access" element={<PermissionRoute check={(u) => u.is_admin}><SensitiveAccessLogs /></PermissionRoute>} />
        <Route path="settings/ops" element={<PermissionRoute check={(u) => u.is_admin}><OpsCenter /></PermissionRoute>} />
        <Route path="settings/users" element={<PermissionRoute check={(u) => u.is_admin}><UsersSettings /></PermissionRoute>} />
        <Route path="settings/security" element={<SecuritySettings />} />
        <Route path="settings/compliance" element={<PermissionRoute check={(u) => u.is_admin}><ComplianceSettings /></PermissionRoute>} />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
