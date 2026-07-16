import io

from django.utils import timezone
from openpyxl import load_workbook

from payroll.models import Salary

from .base import HRAPITestCase


class ReportAPITests(HRAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        today = timezone.now().date()
        Salary.objects.create(
            employee=cls.employee,
            month=today.month,
            year=today.year,
            basic_salary=1_000_000,
            allowances=100_000,
            deductions=50_000,
            tax=20_000,
        )

    def test_employee_cannot_access_management_reports(self):
        self.login('employee', 'EmployeePass123!')

        for path in (
            '/api/v1/reports/analytics/',
            '/api/v1/reports/filters/',
            '/api/v1/reports/attendance/',
            '/api/v1/reports/leave/',
            '/api/v1/reports/payroll/',
            '/api/v1/reports/performance/',
            '/api/v1/reports/recruitment/',
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 403)

    def test_manager_can_access_management_reports(self):
        self.login('manager', 'ManagerPass123!')

        self.assertEqual(self.client.get('/api/v1/reports/analytics/').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/reports/payroll/').status_code, 200)

    def test_payroll_workbook_is_branded_and_uses_ugx(self):
        self.login('manager', 'ManagerPass123!')
        today = timezone.now().date()

        response = self.client.get(
            f'/api/v1/payroll/export/?month={today.month}&year={today.year}&export_format=xlsx'
        )

        self.assertEqual(response.status_code, 200)
        workbook = load_workbook(io.BytesIO(response.content))
        sheet = workbook.active
        self.assertEqual(sheet['A1'].value, 'Payroll')
        self.assertIn('Currency: UGX (Uganda Shilling)', sheet['A2'].value)
        self.assertEqual(sheet.freeze_panes, 'A5')
        self.assertEqual(sheet['E5'].number_format, '"UGX" #,##0')

    def test_csv_export_uses_display_labels(self):
        self.login('manager', 'ManagerPass123!')

        response = self.client.get('/api/v1/reports/attendance/?export_format=csv')

        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8-sig')
        self.assertTrue(content.startswith('Employee,Date,Status,Time In,Time Out'))
