# Mobile / offline attendance

English-only mobile clock for employees. No additional languages are shipped.

## Features

- Route: `/mobile` (installable PWA via `manifest.webmanifest` + `sw.js`)
- Online punch: `POST /api/v1/attendance/mobile-punch/`
- Offline queue: IndexedDB (`offlinePunchQueue`) then `POST /api/v1/attendance/mobile-sync/`
- Device terminals: register under Attendance → Devices; ingest with `X-Device-Token` at `/api/v1/device-punches/ingest/`

## Employee setup

1. Set `device_badge_id` on the employee (or use `employee_number` as the badge).
2. Open `/mobile` while logged in; optionally “Add to Home Screen”.
3. Clock in/out; when offline, punches queue and sync automatically on reconnect.

## Device terminal setup

1. Admin creates a device in Attendance → Devices (token returned once).
2. Terminal posts:

```http
POST /api/v1/device-punches/ingest/
X-Device-Token: <token>
Content-Type: application/json

{"badge_id":"BADGE-100","punch_type":"in"}
```
