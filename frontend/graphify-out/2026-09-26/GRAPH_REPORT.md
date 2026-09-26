# Graph Report - frontend  (2026-09-26)

## Corpus Check
- 128 files · ~42,871 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 410 nodes · 928 edges · 25 communities (24 shown, 1 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 3 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `049e86a7`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- App.jsx
- client.js
- scripts
- Dashboard.jsx
- ResourceManager.jsx
- Recruitment.jsx
- Reports.jsx
- UsersSettings.jsx
- helpers.js
- permissions.js
- OpsCenter.jsx
- hrModules.jsx
- MobileClock.jsx
- approvals-approvals-queue-admin-can-open-approvals-page-chromium/error-context.md
- auth-authentication-admin-can-log-in-and-reach-dashboard-chromium/error-context.md
- auth-authentication-employee-can-log-in-and-reach-dashboard-chromium/error-context.md
- leave-workflow-leave-workf-588ca-n-approves-via-approvals-UI-chromium/error-context.md
- mfa-multi-factor-authentic-f8cac--open-MFA-security-settings-chromium/error-context.md
- payroll-payroll-admin-can--035a5-e-and-see-statutory-exports-chromium/error-context.md
- smoke-critical-smoke-login-10b74-and-health-API-is-reachable-chromium/error-context.md
- sw.js

## God Nodes (most connected - your core abstractions)
1. `useAuth()` - 65 edges
2. `api` - 50 edges
3. `canManageHr()` - 16 edges
4. `errorMessage()` - 15 edges
5. `E2E_CREDENTIALS` - 11 edges
6. `backendAvailable()` - 11 edges
7. `loginViaUi()` - 11 edges
8. `ResourceManager()` - 10 edges
9. `PublicFooter()` - 9 edges
10. `canViewPayroll()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `Layout()` --calls--> `useAuth()`  [EXTRACTED]
  src/components/Layout.jsx → src/context/AuthContext.jsx
- `ResourceManager()` --calls--> `errorMessage()`  [EXTRACTED]
  src/components/ResourceManager.jsx → src/utils/apiErrors.js
- `ResourceManager()` --calls--> `canManagePayroll()`  [EXTRACTED]
  src/components/ResourceManager.jsx → src/utils/permissions.js
- `ApplicationScorecards()` --calls--> `useAuth()`  [EXTRACTED]
  src/components/recruitment/ApplicationScorecards.jsx → src/context/AuthContext.jsx
- `ReportResults()` --indirect_call--> `formatDate()`  [INFERRED]
  src/components/reports/ReportResults.jsx → src/utils/reportFormatters.js

## Import Cycles
- None detected.

## Communities (25 total, 1 thin omitted)

### Community 0 - "App.jsx"
Cohesion: 0.06
Nodes (45): App(), PermissionRoute(), ProtectedRoute(), ResourceManager(), SettingsBackLink(), leaveTabs, assetTabs, benefitTabs (+37 more)

### Community 1 - "client.js"
Cohesion: 0.07
Nodes (25): api, getCookie(), request(), PublicFooter(), YEAR, ApplicationInterviews(), STATUS_OPTIONS, ApplicationNotes() (+17 more)

### Community 2 - "scripts"
Cohesion: 0.05
Nodes (36): bootstrap, bootstrap-icons, otplib, dependencies, bootstrap, bootstrap-icons, react, react-dom (+28 more)

### Community 3 - "Dashboard.jsx"
Cohesion: 0.08
Nodes (18): ActivityPanel(), formatWhen(), AttentionBanner(), SEVERITY_CLASS, DashboardHero(), formatAsOf(), ROLE_LABELS, DeltaBadge() (+10 more)

### Community 4 - "ResourceManager.jsx"
Cohesion: 0.17
Nodes (15): ResourceDataTable(), defaultLabel(), ResourceFormField(), ResourceFormModal(), ResourceTabs(), ResourceToolbar(), EmployeeForm(), emptyForm (+7 more)

### Community 5 - "Recruitment.jsx"
Cohesion: 0.13
Nodes (14): JobEnterpriseConfig(), ROLES, RecruitmentAnalytics(), RecruitmentCompliance(), RecruitmentJobsPanel(), daysSince(), DEFAULT_COLUMNS, ICONS (+6 more)

### Community 6 - "Reports.jsx"
Cohesion: 0.18
Nodes (13): ReportFilterForm(), ReportOverviewPanel(), ReportResults(), ReportSchedulingPanel(), ReportTable(), StatCard(), Reports(), formatDate() (+5 more)

### Community 7 - "UsersSettings.jsx"
Cohesion: 0.16
Nodes (12): ConfirmModal(), DepartmentModal(), Departments(), Register(), ResetPassword(), EMPTY_FORM, UserModal(), UsersSettings() (+4 more)

### Community 8 - "helpers.js"
Cohesion: 0.30
Nodes (7): backendAvailable(), createLeaveViaApi(), E2E_CREDENTIALS, E2E_MFA_SECRET, futureLeaveDates(), loginViaUi(), repoRoot

### Community 9 - "permissions.js"
Cohesion: 0.22
Nodes (14): adminNavItems, canSeeNavItem(), Layout(), managerNavItems, navItems, NotificationBell(), Payroll(), canApproveAttendance() (+6 more)

### Community 10 - "OpsCenter.jsx"
Cohesion: 0.17
Nodes (12): asArray(), formatRemaining(), formatWhen(), levelBadge(), OpsAlertsCard(), OpsBackupsCard(), OpsJobsCard(), OpsRunbooksPanel() (+4 more)

### Community 11 - "hrModules.jsx"
Cohesion: 0.14
Nodes (13): FeedbackWorkflow(), GIVER_TYPES, RATING_FIELDS, RATING_OPTIONS, attendanceTabs, payrollTabs, recruitmentApplicationsTab, recruitmentJobsTab (+5 more)

### Community 12 - "MobileClock.jsx"
Cohesion: 0.41
Nodes (9): MobileClock(), flushQueue(), punch(), refreshQueue(), clearQueuedPunches(), enqueuePunch(), listQueuedPunches(), makeClientPunchId() (+1 more)

### Community 13 - "approvals-approvals-queue-admin-can-open-approvals-page-chromium/error-context.md"
Cohesion: 0.50
Nodes (3): Error details, Instructions, Test info

### Community 14 - "auth-authentication-admin-can-log-in-and-reach-dashboard-chromium/error-context.md"
Cohesion: 0.50
Nodes (3): Error details, Instructions, Test info

### Community 15 - "auth-authentication-employee-can-log-in-and-reach-dashboard-chromium/error-context.md"
Cohesion: 0.50
Nodes (3): Error details, Instructions, Test info

### Community 16 - "leave-workflow-leave-workf-588ca-n-approves-via-approvals-UI-chromium/error-context.md"
Cohesion: 0.50
Nodes (3): Error details, Instructions, Test info

### Community 17 - "mfa-multi-factor-authentic-f8cac--open-MFA-security-settings-chromium/error-context.md"
Cohesion: 0.50
Nodes (3): Error details, Instructions, Test info

### Community 18 - "payroll-payroll-admin-can--035a5-e-and-see-statutory-exports-chromium/error-context.md"
Cohesion: 0.50
Nodes (3): Error details, Instructions, Test info

### Community 19 - "smoke-critical-smoke-login-10b74-and-health-API-is-reachable-chromium/error-context.md"
Cohesion: 0.50
Nodes (3): Error details, Instructions, Test info

## Knowledge Gaps
- **75 isolated node(s):** `repoRoot`, `name`, `private`, `version`, `type` (+70 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `useAuth()` connect `App.jsx` to `client.js`, `Dashboard.jsx`, `ResourceManager.jsx`, `Recruitment.jsx`, `Reports.jsx`, `UsersSettings.jsx`, `permissions.js`, `OpsCenter.jsx`, `hrModules.jsx`, `MobileClock.jsx`?**
  _High betweenness centrality (0.095) - this node is a cross-community bridge._
- **Why does `api` connect `client.js` to `App.jsx`, `Dashboard.jsx`, `ResourceManager.jsx`, `Recruitment.jsx`, `Reports.jsx`, `UsersSettings.jsx`, `permissions.js`, `OpsCenter.jsx`, `hrModules.jsx`, `MobileClock.jsx`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Why does `MobileClock()` connect `MobileClock.jsx` to `App.jsx`?**
  _High betweenness centrality (0.011) - this node is a cross-community bridge._
- **What connects `repoRoot`, `name`, `private` to the rest of the system?**
  _75 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `App.jsx` be split into smaller, more focused modules?**
  _Cohesion score 0.06493506493506493 - nodes in this community are weakly interconnected._
- **Should `client.js` be split into smaller, more focused modules?**
  _Cohesion score 0.06711915535444947 - nodes in this community are weakly interconnected._
- **Should `scripts` be split into smaller, more focused modules?**
  _Cohesion score 0.05405405405405406 - nodes in this community are weakly interconnected._