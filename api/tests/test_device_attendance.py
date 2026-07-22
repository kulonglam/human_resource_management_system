"""Biometric / device attendance and mobile punch tests."""

from django.utils import timezone

from attendance.models import Attendance, DevicePunch
from attendance.services import create_attendance_device, ingest_device_punch
from employees.models import Employee

from .base import HRAPITestCase


class DeviceAttendanceTests(HRAPITestCase):
    def test_device_ingest_creates_attendance(self):
        self.employee.device_badge_id = 'BADGE-100'
        self.employee.save(update_fields=['device_badge_id'])
        device, token = create_attendance_device(
            name='Lobby FP', device_code='lobby-fp', device_type='fingerprint',
        )
        response = self.client.post(
            '/api/v1/device-punches/ingest/',
            {'badge_id': 'BADGE-100', 'punch_type': 'in'},
            format='json',
            HTTP_X_DEVICE_TOKEN=token,
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertTrue(response.json()['applied'])
        self.assertTrue(
            Attendance.objects.filter(employee=self.employee, date=timezone.localdate()).exists(),
        )

    def test_mobile_punch_for_linked_employee(self):
        self.login('employee', 'EmployeePass123!')
        response = self.client.post(
            '/api/v1/attendance/mobile-punch/',
            {'punch_type': 'in', 'client_punch_id': 'e2e-mobile-1'},
            format='json',
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(DevicePunch.objects.filter(client_punch_id='e2e-mobile-1').count(), 1)

    def test_offline_sync_is_idempotent(self):
        self.login('employee', 'EmployeePass123!')
        payload = {
            'punches': [{
                'punch_type': 'in',
                'punched_at': timezone.now().isoformat(),
                'client_punch_id': 'offline-abc',
            }],
        }
        first = self.client.post('/api/v1/attendance/mobile-sync/', payload, format='json')
        second = self.client.post('/api/v1/attendance/mobile-sync/', payload, format='json')
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(DevicePunch.objects.filter(client_punch_id='offline-abc').count(), 1)

    def test_unmatched_badge_records_error(self):
        punch = ingest_device_punch(badge_id='UNKNOWN-X', punch_type='in')
        self.assertFalse(punch.applied)
        self.assertIn('No employee matched', punch.error_message)
