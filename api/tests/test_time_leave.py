from datetime import date

from django.utils import timezone

from attendance.models import PublicHoliday
from leaves.models import Leave, LeaveBalance
from leaves.services import calculate_leave_duration, count_working_days

from .base import HRAPITestCase


class WorkingDayLeaveTests(HRAPITestCase):
    def test_leave_excludes_weekend(self):
        PublicHoliday.objects.create(name='Test Holiday', date=date(2026, 7, 10))
        # Mon 6 Jul - Fri 10 Jul 2026: 10th is Friday but also holiday -> 4 working days
        duration = calculate_leave_duration(date(2026, 7, 6), date(2026, 7, 10))
        self.assertEqual(duration, 4)

    def test_recurring_holiday_applies_each_year(self):
        PublicHoliday.objects.create(name='Labour Day', date=date(2020, 5, 1), is_recurring=True)
        duration_2026 = calculate_leave_duration(date(2026, 5, 1), date(2026, 5, 1))
        self.assertEqual(duration_2026, 0)
        duration_2025 = calculate_leave_duration(date(2025, 5, 1), date(2025, 5, 5))
        self.assertEqual(duration_2025, 2)

    def test_half_day_leave(self):
        duration = calculate_leave_duration(date(2026, 7, 6), date(2026, 7, 6), is_half_day=True)
        self.assertEqual(duration, 0.5)

    def test_create_leave_uses_working_days(self):
        self.login('admin', 'AdminPass123!')
        year = timezone.now().year
        response = self.client.post(
            '/api/v1/leaves/',
            {
                'employee': self.employee.id,
                'leave_type': 'annual',
                'start_date': f'{year}-07-06',
                'end_date': f'{year}-07-10',
                'reason': 'Break',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        leave = Leave.objects.get(id=response.data['id'])
        self.assertEqual(leave.working_days, count_working_days(leave.start_date, leave.end_date))


class PublicHolidayAPITests(HRAPITestCase):
    def test_admin_lists_holidays(self):
        PublicHoliday.objects.create(name='Labour Day', date=date(2026, 5, 1))
        self.login('admin', 'AdminPass123!')
        response = self.client.get('/api/v1/public-holidays/')
        self.assertEqual(response.status_code, 200)
        rows = response.data.get('results', response.data)
        self.assertEqual(len(rows), 1)


class AttendanceWorkflowTests(HRAPITestCase):
    def test_submit_and_approve_attendance(self):
        from attendance.models import Attendance

        record = Attendance.objects.create(
            employee=self.employee,
            date=date(2026, 7, 7),
            status='present',
            approval_status='draft',
        )
        self.login('employee', 'EmployeePass123!')
        submit = self.client.post(f'/api/v1/attendance/{record.id}/submit/', {}, format='json')
        self.assertEqual(submit.status_code, 200)
        self.assertEqual(submit.data['approval_status'], 'submitted')

        self.client.logout()
        self.login('admin', 'AdminPass123!')
        approve = self.client.post(f'/api/v1/attendance/{record.id}/approve/', {}, format='json')
        self.assertEqual(approve.status_code, 200)
        self.assertEqual(approve.data['approval_status'], 'approved')
