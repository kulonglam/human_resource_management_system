import { Navigate, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import {
  attendanceTabs, leaveTabs, recruitmentTabs, payrollTabs,
} from './config/hrModules';
import {
  exitTabs, assetTabs, shiftTabs,
  expenseTabs, benefitTabs, leavePolicyTabs, disciplineTabs, kinTabs,
} from './config/opsModules';
import Documents from './pages/Documents';
import DashboardPage from './pages/DashboardPage';
import Departments from './pages/Departments';
import EmployeeDetail from './pages/EmployeeDetail';
import EmployeeForm from './pages/EmployeeForm';
import Employees from './pages/Employees';
import AuditLogs from './pages/AuditLogs';
import IntegrationsSettings from './pages/IntegrationsSettings';
import Login from './pages/Login';
import OrgChart from './pages/OrgChart';
import ModulePage from './pages/ModulePage';
import Performance from './pages/Performance';
import RecordDetail from './pages/RecordDetail';
import Register from './pages/Register';
import Reports from './pages/Reports';
import SecuritySettings from './pages/SecuritySettings';
import Surveys from './pages/Surveys';
import SurveyTake from './pages/SurveyTake';
import Training from './pages/Training';

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="employees" element={<Employees />} />
        <Route path="employees/new" element={<EmployeeForm />} />
        <Route path="employees/:id" element={<EmployeeDetail />} />
        <Route path="employees/:id/edit" element={<EmployeeForm />} />
        <Route path="departments" element={<Departments />} />
        <Route path="attendance" element={<ModulePage title="Attendance" icon="bi-calendar-check" tabs={attendanceTabs} />} />
        <Route path="leaves" element={<ModulePage title="Leaves" icon="bi-calendar-x" tabs={leaveTabs} />} />
        <Route path="recruitment" element={<ModulePage title="Recruitment" icon="bi-briefcase" tabs={recruitmentTabs} />} />
        <Route path="payroll" element={<ModulePage title="Payroll" icon="bi-cash-coin" tabs={payrollTabs} />} />
        <Route path="performance" element={<Performance />} />
        <Route path="performance/goals/:id" element={<RecordDetail configKey="performance-goals" />} />
        <Route path="performance/appraisals/:id" element={<RecordDetail configKey="performance-appraisals" />} />
        <Route path="training/courses/:id" element={<RecordDetail configKey="training-courses" />} />
        <Route path="training/development-plans/:id" element={<RecordDetail configKey="development-plans" />} />
        <Route path="recruitment/jobs/:id" element={<RecordDetail configKey="jobs" />} />
        <Route path="exits/:id" element={<RecordDetail configKey="exit-processes" />} />
        <Route path="training" element={<Training />} />
        <Route path="reports" element={<Reports />} />
        <Route path="documents" element={<Documents />} />
        <Route path="org-chart" element={<OrgChart />} />
        <Route path="settings/integrations" element={<IntegrationsSettings />} />
        <Route path="exits" element={<ModulePage title="Exit Management" icon="bi-door-closed" tabs={exitTabs} />} />
        <Route path="assets" element={<ModulePage title="Assets" icon="bi-laptop" tabs={assetTabs} />} />
        <Route path="shifts" element={<ModulePage title="Shifts" icon="bi-clock" tabs={shiftTabs} />} />
        <Route path="expenses" element={<ModulePage title="Expenses" icon="bi-receipt" tabs={expenseTabs} />} />
        <Route path="benefits" element={<ModulePage title="Benefits" icon="bi-heart-pulse" tabs={benefitTabs} />} />
        <Route path="leave-policies" element={<ModulePage title="Leave Policies" icon="bi-file-earmark-text" tabs={leavePolicyTabs} />} />
        <Route path="discipline" element={<ModulePage title="Discipline" icon="bi-exclamation-triangle" tabs={disciplineTabs} />} />
        <Route path="surveys" element={<Surveys />} />
        <Route path="surveys/:id/take" element={<SurveyTake />} />
        <Route path="kin" element={<ModulePage title="Next of Kin" icon="bi-people" tabs={kinTabs} />} />
        <Route path="audit-logs" element={<AuditLogs />} />
        <Route path="settings/security" element={<SecuritySettings />} />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
