from django.utils import timezone

from accounts.models import AuditLog
from payroll.models import PayrollRun, Salary

from .base import HRAPITestCase


class PayrollAPITests(HRAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        now = timezone.now()
        cls.payroll_run = PayrollRun.objects.create(
            month=now.month,
            year=now.year,
            created_by=cls.admin_user,
        )
        cls.salary = Salary.objects.create(
            employee=cls.employee,
            payroll_run=cls.payroll_run,
            month=now.month,
            year=now.year,
            basic_salary=50000,
            allowances=5000,
            deductions=2000,
            tax=1000,
        )

    def test_admin_lists_salaries(self):
        self.login('admin', 'AdminPass123!')
        response = self.client.get('/api/v1/salaries/')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_salary_uses_uganda_statutory_calculation(self):
        self.salary.refresh_from_db()

        self.assertEqual(self.salary.gross_salary, 55000)
        self.assertEqual(self.salary.tax, 0)
        self.assertEqual(self.salary.nssf_employee, 2750)
        self.assertEqual(self.salary.nssf_employer, 5500)
        self.assertEqual(self.salary.net_salary, 50250)

    def test_employee_sees_own_salary_only(self):
        self.login('employee', 'EmployeePass123!')
        response = self.client.get('/api/v1/salaries/')
        self.assertEqual(response.status_code, 200)
        ids = [row['id'] for row in response.data['results']]
        self.assertIn(self.salary.id, ids)

    def test_admin_create_salary_audit_log(self):
        self.login('admin', 'AdminPass123!')
        now = timezone.now()
        month = now.month - 1 if now.month > 1 else 12
        year = now.year if now.month > 1 else now.year - 1
        response = self.client.post(
            '/api/v1/salaries/',
            {
                'employee': self.employee.id,
                'month': month,
                'year': year,
                'basic_salary': '60000.00',
                'allowances': '3000.00',
                'deductions': '1000.00',
                'tax': '500.00',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            AuditLog.objects.filter(
                action='create',
                model_name='Salary',
                object_id=response.data['id'],
            ).exists()
        )

    def test_admin_downloads_salary_slip_pdf(self):
        self.login('admin', 'AdminPass123!')

        response = self.client.get(f'/api/v1/salaries/{self.salary.id}/slip/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_approved_salary_is_locked_and_can_be_marked_paid(self):
        self.login('admin', 'AdminPass123!')

        approve = self.client.post(f'/api/v1/payroll-runs/{self.payroll_run.id}/approve/', {}, format='json')
        self.assertEqual(approve.status_code, 200)
        self.assertEqual(approve.data['status'], 'approved')

        update = self.client.patch(
            f'/api/v1/salaries/{self.salary.id}/',
            {'allowances': '999999.00'},
            format='json',
        )
        self.assertEqual(update.status_code, 409)

        paid = self.client.post(f'/api/v1/payroll-runs/{self.payroll_run.id}/mark_paid/', {}, format='json')
        self.assertEqual(paid.status_code, 200)
        self.assertEqual(paid.data['status'], 'paid')
        self.salary.refresh_from_db()
        self.assertTrue(self.salary.is_paid)

    def test_manager_cannot_approve_payroll(self):
        self.login('manager', 'ManagerPass123!')

        response = self.client.post(f'/api/v1/payroll-runs/{self.payroll_run.id}/approve/', {}, format='json')

        self.assertEqual(response.status_code, 403)
