# Graph Report - frontend  (2026-09-26)

## Corpus Check
- 120 files · ~42,186 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 382 nodes · 907 edges · 18 communities (17 shown, 1 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 3 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3f8ec0a6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- useAuth
- client.js
- scripts
- Dashboard.jsx
- EmployeeForm.jsx
- App.jsx
- Reports.jsx
- UsersSettings.jsx
- helpers.js
- ResourceManager.jsx
- OpsAlertsCard.jsx
- hrModules.jsx
- MobileClock.jsx
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
- `DepartmentModal()` --calls--> `errorMessage()`  [EXTRACTED]
  src/pages/Departments.jsx → src/utils/apiErrors.js
- `Layout()` --calls--> `useAuth()`  [EXTRACTED]
  src/components/Layout.jsx → src/context/AuthContext.jsx
- `ResourceManager()` --calls--> `useAuth()`  [EXTRACTED]
  src/components/ResourceManager.jsx → src/context/AuthContext.jsx
- `ResourceManager()` --calls--> `errorMessage()`  [EXTRACTED]
  src/components/ResourceManager.jsx → src/utils/apiErrors.js
- `ApplicationScorecards()` --calls--> `useAuth()`  [EXTRACTED]
  src/components/recruitment/ApplicationScorecards.jsx → src/context/AuthContext.jsx

## Import Cycles
- None detected.

## Communities (18 total, 1 thin omitted)

### Community 0 - "useAuth"
Cohesion: 0.07
Nodes (28): App(), OpsBackupsCard(), OpsJobsCard(), OpsRunbooksPanel(), OpsSLOCard(), asArray(), OpsUsageCard(), PermissionRoute() (+20 more)

### Community 1 - "client.js"
Cohesion: 0.07
Nodes (27): api, getCookie(), request(), ApplicationInterviews(), STATUS_OPTIONS, ApplicationNotes(), ApplicationOffers(), ApplicationScorecards() (+19 more)

### Community 2 - "scripts"
Cohesion: 0.05
Nodes (36): bootstrap, bootstrap-icons, otplib, dependencies, bootstrap, bootstrap-icons, react, react-dom (+28 more)

### Community 3 - "Dashboard.jsx"
Cohesion: 0.08
Nodes (18): ActivityPanel(), formatWhen(), AttentionBanner(), SEVERITY_CLASS, DashboardHero(), formatAsOf(), ROLE_LABELS, DeltaBadge() (+10 more)

### Community 4 - "EmployeeForm.jsx"
Cohesion: 0.22
Nodes (13): ResourceDataTable(), defaultLabel(), ResourceFormField(), ResourceFormModal(), EmployeeForm(), emptyForm, FIELD_KINDS, FieldLabel() (+5 more)

### Community 5 - "App.jsx"
Cohesion: 0.08
Nodes (26): PublicFooter(), YEAR, DETAIL_CONFIGS, assetTabs, benefitTabs, disciplineTabs, exitTabs, expenseTabs (+18 more)

### Community 6 - "Reports.jsx"
Cohesion: 0.18
Nodes (13): ReportFilterForm(), ReportOverviewPanel(), ReportResults(), ReportSchedulingPanel(), ReportTable(), StatCard(), Reports(), formatDate() (+5 more)

### Community 7 - "UsersSettings.jsx"
Cohesion: 0.22
Nodes (9): Register(), ResetPassword(), EMPTY_FORM, UserModal(), UsersSettings(), errorMessage(), formatApiErrors(), ALL_PERMISSIONS (+1 more)

### Community 8 - "helpers.js"
Cohesion: 0.30
Nodes (7): backendAvailable(), createLeaveViaApi(), E2E_CREDENTIALS, E2E_MFA_SECRET, futureLeaveDates(), loginViaUi(), repoRoot

### Community 9 - "ResourceManager.jsx"
Cohesion: 0.10
Nodes (26): ConfirmModal(), adminNavItems, canSeeNavItem(), Layout(), managerNavItems, navItems, NotificationBell(), ResourceManager() (+18 more)

### Community 10 - "OpsAlertsCard.jsx"
Cohesion: 0.60
Nodes (5): asArray(), formatRemaining(), formatWhen(), levelBadge(), OpsAlertsCard()

### Community 11 - "hrModules.jsx"
Cohesion: 0.11
Nodes (16): FeedbackWorkflow(), GIVER_TYPES, RATING_FIELDS, RATING_OPTIONS, attendanceTabs, leaveTabs, recruitmentApplicationsTab, recruitmentJobsTab (+8 more)

### Community 12 - "MobileClock.jsx"
Cohesion: 0.41
Nodes (9): MobileClock(), flushQueue(), punch(), refreshQueue(), clearQueuedPunches(), enqueuePunch(), listQueuedPunches(), makeClientPunchId() (+1 more)

## Knowledge Gaps
- **54 isolated node(s):** `repoRoot`, `name`, `private`, `version`, `type` (+49 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `useAuth()` connect `useAuth` to `client.js`, `Dashboard.jsx`, `EmployeeForm.jsx`, `App.jsx`, `Reports.jsx`, `UsersSettings.jsx`, `ResourceManager.jsx`, `hrModules.jsx`, `MobileClock.jsx`?**
  _High betweenness centrality (0.109) - this node is a cross-community bridge._
- **Why does `api` connect `client.js` to `useAuth`, `Dashboard.jsx`, `EmployeeForm.jsx`, `App.jsx`, `Reports.jsx`, `UsersSettings.jsx`, `ResourceManager.jsx`, `hrModules.jsx`, `MobileClock.jsx`?**
  _High betweenness centrality (0.094) - this node is a cross-community bridge._
- **Why does `MobileClock()` connect `MobileClock.jsx` to `useAuth`, `App.jsx`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **What connects `repoRoot`, `name`, `private` to the rest of the system?**
  _54 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `useAuth` be split into smaller, more focused modules?**
  _Cohesion score 0.07137254901960784 - nodes in this community are weakly interconnected._
- **Should `client.js` be split into smaller, more focused modules?**
  _Cohesion score 0.07142857142857142 - nodes in this community are weakly interconnected._
- **Should `scripts` be split into smaller, more focused modules?**
  _Cohesion score 0.05405405405405406 - nodes in this community are weakly interconnected._