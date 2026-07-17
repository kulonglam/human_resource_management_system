"""Direct unit tests for domain service use-cases (no HTTP)."""
from datetime import date, time
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from accounts.models import CustomUser, Role
from attendance.models import Attendance, Timesheet
from departments.models import Department
from employees.models import Employee
from expenses.models import Expense, ExpenseCategory
from benefits.models import Benefit
from leaves.models import Leave, LeaveBalance
from payroll.models import PayrollRun, Salary
from recruitment.models import Application, JobOffer, JobPipelineStage, JobPosting, OfferTemplate


class EmployeeServicesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(name='IT', location='HQ')
        cls.employee = Employee.objects.create(
            first_name='Jane',
            last_name='Doe',
            date_of_birth='1990-01-01',
            gender='Female',
            email='jane@test.local',
            mobile='0700000000',
            address='Kampala',
            emergency_contact='0700111111',
            job_title='Developer',
            department=cls.department,
            date_joined='2024-01-01',
            account_number='1234567890',
            bank='Test Bank',
            salary=50000,
        )
        cls.user = CustomUser.objects.create_user(
            username='jane',
            email='jane@test.local',
            password='Pass123!',
            role=Role.objects.create(name=Role.EMPLOYEE),
        )

    @patch('integrations.services.dispatch_webhook')
    def test_terminate_employee_deactivates_user(self, mock_webhook):
        from employees.services import terminate_employee

        terminate_employee(self.employee, exit_reason='resignation', exit_notes='Leaving')
        self.employee.refresh_from_db()
        self.user.refresh_from_db()

        self.assertFalse(self.employee.is_active)
        self.assertEqual(self.employee.exit_reason, 'resignation')
        self.assertFalse(self.user.is_active)
        mock_webhook.assert_called_once()
        self.assertEqual(mock_webhook.call_args[0][0], 'employee.terminated')

    @patch('integrations.services.dispatch_webhook')
    def test_after_employee_created_emits_webhook(self, mock_webhook):
        from employees.services import after_employee_created

        after_employee_created(self.employee)
        mock_webhook.assert_called_once_with('employee.created', mock_webhook.call_args[0][1])

    def test_assign_organization_if_needed(self):
        from accounts.models import Organization
        from employees.services import assign_organization_if_needed

        org = Organization.objects.create(name='Test Org', slug='test-org')
        admin_role = Role.objects.get(name=Role.EMPLOYEE)
        org_user = CustomUser.objects.create_user(
            username='orgadmin',
            email='org@test.local',
            password='Pass123!',
            role=admin_role,
            organization=org,
        )
        employee = Employee.objects.create(
            first_name='New',
            last_name='Hire',
            date_of_birth='1995-01-01',
            gender='Male',
            email='new@test.local',
            mobile='0700222222',
            address='Kampala',
            emergency_contact='0700333333',
            job_title='Analyst',
            department=self.department,
            date_joined='2025-01-01',
            account_number='1111111111',
            bank='Test Bank',
            salary=40000,
        )
        assign_organization_if_needed(employee, org_user)
        employee.refresh_from_db()
        self.assertEqual(employee.organization_id, org.id)


class PayrollServicesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = CustomUser.objects.create_user(
            username='payadmin',
            email='payadmin@test.local',
            password='Pass123!',
            role=Role.objects.create(name=Role.ADMIN),
        )
        cls.department = Department.objects.create(name='Finance', location='HQ')
        cls.employee = Employee.objects.create(
            first_name='Pay',
            last_name='Roll',
            date_of_birth='1988-01-01',
            gender='Male',
            email='pay@test.local',
            mobile='0700444444',
            address='Kampala',
            emergency_contact='0700555555',
            job_title='Accountant',
            department=cls.department,
            date_joined='2024-01-01',
            account_number='2222222222',
            bank='Test Bank',
            salary=60000,
        )
        now = timezone.now()
        cls.payroll_run = PayrollRun.objects.create(
            month=now.month,
            year=now.year,
            created_by=cls.admin,
        )

    def test_approve_payroll_run_requires_salary_records(self):
        from payroll.services import approve_payroll_run

        with self.assertRaises(ValueError):
            approve_payroll_run(self.payroll_run, approved_by=self.admin)

    def test_approve_and_mark_paid_lifecycle(self):
        from payroll.services import approve_payroll_run, mark_payroll_run_paid

        Salary.objects.create(
            employee=self.employee,
            payroll_run=self.payroll_run,
            month=self.payroll_run.month,
            year=self.payroll_run.year,
            basic_salary=60000,
            allowances=0,
            deductions=0,
            tax=0,
        )
        approve_payroll_run(self.payroll_run, approved_by=self.admin)
        self.payroll_run.refresh_from_db()
        self.assertEqual(self.payroll_run.status, 'approved')

        mark_payroll_run_paid(self.payroll_run)
        self.payroll_run.refresh_from_db()
        self.assertEqual(self.payroll_run.status, 'paid')

    def test_mark_paid_rejects_draft_run(self):
        from payroll.services import mark_payroll_run_paid

        with self.assertRaises(ValueError):
            mark_payroll_run_paid(self.payroll_run)

    def test_approve_payroll_run_reloads_latest_locked_status(self):
        from payroll.services import approve_payroll_run

        Salary.objects.create(
            employee=self.employee,
            payroll_run=self.payroll_run,
            month=self.payroll_run.month,
            year=self.payroll_run.year,
            basic_salary=60000,
            allowances=0,
            deductions=0,
            tax=0,
        )
        stale_run = PayrollRun.objects.get(pk=self.payroll_run.pk)
        PayrollRun.objects.filter(pk=self.payroll_run.pk).update(status='approved')

        with self.assertRaises(ValueError):
            approve_payroll_run(stale_run, approved_by=self.admin)


class RecruitmentServicesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(name='Recruiting IT', location='HQ')
        cls.admin = CustomUser.objects.create_user(
            username='recadmin',
            email='recadmin@test.local',
            password='Pass123!',
            role=Role.objects.create(name='recruitment-admin'),
        )
        cls.job = JobPosting.objects.create(
            title='Engineer',
            department='IT',
            description='Build',
            requirements='Python',
            deadline='2099-12-31',
        )
        cls.application = Application.objects.create(
            job=cls.job,
            first_name='Sam',
            last_name='Candidate',
            email='sam@example.com',
            phone='0700666666',
            status='received',
        )
        cls.template = OfferTemplate.objects.create(
            name='Standard',
            body='Hello {{candidate_name}}',
        )

    @patch('api.notifications.notify_application_status')
    def test_update_application_after_save_notifies_on_change(self, mock_notify):
        from recruitment.services import update_application_after_save

        old_status = self.application.status
        self.application.status = 'shortlisted'
        self.application.save()
        update_application_after_save(
            application=self.application,
            old_status=old_status,
            previous_status_label='Received',
        )
        mock_notify.assert_called_once()

    def test_approve_job_offer_requires_pending_status(self):
        from recruitment.services import approve_job_offer

        offer = JobOffer.objects.create(
            application=self.application,
            template=self.template,
            job_title='Engineer',
            department='IT',
            salary=Decimal('5000000'),
            start_date=date.today(),
            body='Offer body',
        )
        with self.assertRaises(ValueError):
            approve_job_offer(offer)

    def test_move_application_to_stage_creates_onboarding_when_hired(self):
        from recruitment.services import ensure_default_pipeline_stages, move_application_to_stage
        from recruitment.models import HireOnboarding

        ensure_default_pipeline_stages(self.job)
        hired_stage = self.job.pipeline_stages.filter(key='hired').first()
        application = move_application_to_stage(application=self.application, stage=hired_stage)
        self.assertEqual(application.status, 'hired')
        self.assertTrue(HireOnboarding.objects.filter(application=application).exists())

    def test_complete_hire_onboarding_is_atomic_and_idempotent(self):
        from recruitment.models import HireOnboarding
        from recruitment.services import complete_hire_onboarding, create_hire_onboarding, ensure_default_pipeline_stages

        ensure_default_pipeline_stages(self.job)
        onboarding = create_hire_onboarding(self.application)
        employee = complete_hire_onboarding(
            onboarding,
            self.admin,
            {
                'date_of_birth': '1995-05-05',
                'department': self.department.id,
                'gender': 'Female',
            },
        )
        onboarding.refresh_from_db()
        self.application.refresh_from_db()
        self.assertEqual(onboarding.status, 'completed')
        self.assertEqual(self.application.employee_id, employee.id)
        with self.assertRaises(ValueError):
            complete_hire_onboarding(
                onboarding,
                self.admin,
                {'date_of_birth': '1995-05-05', 'department': self.department.id},
            )

    def test_send_job_offer_updates_application_stage(self):
        from recruitment.services import (
            approve_job_offer,
            ensure_default_pipeline_stages,
            send_job_offer,
            submit_job_offer,
        )

        ensure_default_pipeline_stages(self.job)
        offer = JobOffer.objects.create(
            application=self.application,
            template=self.template,
            job_title='Engineer',
            department='IT',
            salary=Decimal('5000000'),
            start_date=date.today(),
            body='Offer body',
            status='draft',
        )
        offer = submit_job_offer(offer)
        offer = approve_job_offer(offer)
        offer = send_job_offer(offer)
        self.application.refresh_from_db()
        self.assertEqual(offer.status, 'sent')
        self.assertEqual(self.application.status, 'offer')


class ExpenseServicesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(name='Ops', location='HQ')
        cls.employee = Employee.objects.create(
            first_name='Exp',
            last_name='User',
            date_of_birth='1991-01-01',
            gender='Male',
            email='exp@test.local',
            mobile='0700777777',
            address='Kampala',
            emergency_contact='0700888888',
            job_title='Staff',
            department=cls.department,
            date_joined='2024-01-01',
            account_number='3333333333',
            bank='Test Bank',
            salary=45000,
        )
        cls.admin = CustomUser.objects.create_user(
            username='expadmin',
            email='expadmin@test.local',
            password='Pass123!',
            role=Role.objects.create(name=Role.ADMIN),
        )
        cls.category = ExpenseCategory.objects.create(name='Travel')

    @patch('api.approval_integration.start_expense_approval')
    @patch('api.notifications.notify_expense_submitted')
    def test_submit_expense_starts_workflow(self, mock_notify, mock_start):
        from expenses.services import submit_expense

        expense = Expense.objects.create(
            employee=self.employee,
            category=self.category,
            description='Trip',
            amount='2000.00',
            expense_date='2025-06-01',
            status='submitted',
        )
        submit_expense(expense=expense, submitted_by=self.admin)
        mock_notify.assert_called_once()
        mock_start.assert_called_once()

    def test_finalize_expense_approval_is_idempotent(self):
        from expenses.services import finalize_expense_approval

        expense = Expense.objects.create(
            employee=self.employee,
            category=self.category,
            description='Hotel',
            amount='1500.00',
            expense_date='2025-06-02',
            status='submitted',
        )
        first = finalize_expense_approval(expense=expense)
        second = finalize_expense_approval(expense=first)
        self.assertEqual(first.status, 'approved')
        self.assertEqual(second.status, 'approved')
        self.assertEqual(Expense.objects.filter(pk=expense.pk, status='approved').count(), 1)

    def test_reject_expense_blocks_approved(self):
        from expenses.services import finalize_expense_approval, reject_expense

        expense = Expense.objects.create(
            employee=self.employee,
            category=self.category,
            description='Meals',
            amount='800.00',
            expense_date='2025-06-03',
            status='submitted',
        )
        expense = finalize_expense_approval(expense=expense)
        with self.assertRaises(ValueError):
            reject_expense(expense=expense, reason='too late')


class LeaveServicesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(name='Leave Ops', location='HQ')
        cls.employee = Employee.objects.create(
            first_name='Leave',
            last_name='User',
            date_of_birth='1992-01-01',
            gender='Female',
            email='leave@test.local',
            mobile='0700212121',
            address='Kampala',
            emergency_contact='0700223232',
            job_title='Officer',
            department=cls.department,
            date_joined='2024-01-01',
            account_number='8888888888',
            bank='Test Bank',
            salary=42000,
        )
        cls.admin = CustomUser.objects.create_user(
            username='leaveadmin',
            email='leaveadmin@test.local',
            password='Pass123!',
            role=Role.objects.create(name='leave-admin'),
        )

    @patch('integrations.services.dispatch_webhook')
    @patch('api.approval_integration.start_leave_approval')
    @patch('api.notifications.notify_leave_submitted')
    def test_submit_leave_revalidates_balance_under_lock(
        self, mock_notify, mock_start_approval, mock_webhook,
    ):
        from leaves.services import submit_leave
        from rest_framework import serializers

        current_year = timezone.now().year
        balance = LeaveBalance.objects.create(
            employee=self.employee,
            leave_type='annual',
            year=current_year,
            total_days=5,
            used_days=0,
            pending_days=0,
        )
        stale_balance = LeaveBalance.objects.get(pk=balance.pk)
        leave = Leave.objects.create(
            employee=self.employee,
            leave_type='annual',
            start_date=date(current_year, 8, 4),
            end_date=date(current_year, 8, 7),
            reason='Vacation',
        )

        LeaveBalance.objects.filter(pk=balance.pk).update(used_days=4)

        with self.assertRaises(serializers.ValidationError):
            submit_leave(leave=leave, balance=stale_balance, submitted_by=self.admin)

        balance.refresh_from_db()
        self.assertEqual(balance.pending_days, 0)
        mock_notify.assert_not_called()
        mock_start_approval.assert_not_called()
        mock_webhook.assert_not_called()


class AttendanceServicesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(name='HR', location='HQ')
        cls.employee = Employee.objects.create(
            first_name='Att',
            last_name='User',
            date_of_birth='1989-01-01',
            gender='Female',
            email='att@test.local',
            mobile='0700999999',
            address='Kampala',
            emergency_contact='0700101010',
            job_title='Clerk',
            department=cls.department,
            date_joined='2024-01-01',
            account_number='4444444444',
            bank='Test Bank',
            salary=35000,
        )
        cls.admin = CustomUser.objects.create_user(
            username='attadmin',
            email='attadmin@test.local',
            password='Pass123!',
            role=Role.objects.create(name=Role.ADMIN),
        )

    def test_submit_attendance_transitions_state(self):
        from attendance.services import submit_attendance

        attendance = Attendance.objects.create(
            employee=self.employee,
            date=date.today(),
            approval_status='draft',
            status='present',
        )
        attendance = submit_attendance(attendance)
        self.assertEqual(attendance.approval_status, 'submitted')

    def test_approve_timesheet_syncs_attendance(self):
        from attendance.services import approve_timesheet, submit_timesheet

        timesheet = Timesheet.objects.create(
            employee=self.employee,
            date=date.today(),
            clock_in=time(8, 0),
            clock_out=time(17, 0),
            status='draft',
        )
        timesheet = submit_timesheet(timesheet)
        timesheet = approve_timesheet(timesheet, approved_by=self.admin)
        self.assertEqual(timesheet.status, 'approved')
        self.assertTrue(
            Attendance.objects.filter(employee=self.employee, date=timesheet.date).exists()
        )

    def test_approve_attendance_rejects_non_submitted(self):
        from attendance.services import approve_attendance

        attendance = Attendance.objects.create(
            employee=self.employee,
            date=date.today(),
            approval_status='draft',
            status='present',
        )
        with self.assertRaises(ValueError):
            approve_attendance(attendance, approved_by=self.admin)

    def test_double_approve_timesheet_raises(self):
        from attendance.services import approve_timesheet, submit_timesheet

        timesheet = Timesheet.objects.create(
            employee=self.employee,
            date=date.today(),
            clock_in=time(9, 0),
            clock_out=time(18, 0),
            status='draft',
        )
        timesheet = submit_timesheet(timesheet)
        approve_timesheet(timesheet, approved_by=self.admin)
        with self.assertRaises(ValueError):
            approve_timesheet(timesheet, approved_by=self.admin)


class PerformanceServicesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(name='Perf', location='HQ')
        cls.employee = Employee.objects.create(
            first_name='Perf',
            last_name='User',
            date_of_birth='1990-01-01',
            gender='Male',
            email='perf@test.local',
            mobile='0700121212',
            address='Kampala',
            emergency_contact='0700131313',
            job_title='Staff',
            department=cls.department,
            date_joined='2024-01-01',
            account_number='5555555555',
            bank='Test Bank',
            salary=40000,
        )
        from performance.models import PerformanceAppraisal

        cls.appraisal = PerformanceAppraisal.objects.create(
            employee=cls.employee,
            appraisal_period_start=date(2025, 1, 1),
            appraisal_period_end=date(2025, 12, 31),
            job_knowledge=4,
            work_quality=4,
            productivity=4,
            communication=4,
            teamwork=4,
            initiative=4,
            reliability=4,
            strengths='Good',
            areas_for_improvement='None',
            next_goals='Continue',
            status='draft',
        )

    @patch('api.notifications.notify_appraisal_submitted')
    def test_submit_appraisal(self, mock_notify):
        from performance.services import submit_appraisal

        submit_appraisal(self.appraisal, submitted_by_name='HR Admin')
        self.appraisal.refresh_from_db()
        self.assertEqual(self.appraisal.status, 'submitted')
        mock_notify.assert_called_once()


class BenefitsServicesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(name='Ben', location='HQ')
        cls.employee = Employee.objects.create(
            first_name='Ben',
            last_name='User',
            date_of_birth='1990-01-01',
            gender='Female',
            email='ben@test.local',
            mobile='0700141414',
            address='Kampala',
            emergency_contact='0700151515',
            job_title='Staff',
            department=cls.department,
            date_joined='2024-01-01',
            account_number='6666666666',
            bank='Test Bank',
            salary=40000,
        )
        cls.benefit = Benefit.objects.create(name='Health', benefit_type='health')

    @patch('api.notifications.notify_benefit_enrollment_submitted')
    def test_after_enrollment_created_notifies_pending(self, mock_notify):
        from benefits.models import EmployeeBenefit
        from benefits.services import after_enrollment_created

        enrollment = EmployeeBenefit.objects.create(
            employee=self.employee,
            benefit=self.benefit,
            enrollment_date=date.today(),
            status='pending',
        )
        after_enrollment_created(enrollment)
        mock_notify.assert_called_once_with(enrollment)


class DisciplineServicesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(name='Disc', location='HQ')
        cls.employee = Employee.objects.create(
            first_name='Disc',
            last_name='User',
            date_of_birth='1990-01-01',
            gender='Male',
            email='disc@test.local',
            mobile='0700161616',
            address='Kampala',
            emergency_contact='0700171717',
            job_title='Staff',
            department=cls.department,
            date_joined='2024-01-01',
            account_number='7777777777',
            bank='Test Bank',
            salary=40000,
        )
        from discipline.models import Discipline

        cls.discipline = Discipline.objects.create(
            employee=cls.employee,
            discipline_type='written_warning',
            reason='Late arrival',
            detailed_reason='Repeated lateness',
            incident_date=date.today(),
            status='issued',
        )

    @patch('api.notifications.notify_discipline_appeal_decision')
    def test_approve_discipline_appeal(self, mock_notify):
        from discipline.models import DisciplineAppeal
        from discipline.services import approve_discipline_appeal

        appeal = DisciplineAppeal.objects.create(
            discipline=self.discipline,
            appeal_date=date.today(),
            appeal_reason='Unfair',
            status='pending',
        )
        approve_discipline_appeal(appeal, review_notes='Reviewed')
        appeal.refresh_from_db()
        self.assertEqual(appeal.status, 'approved')
        mock_notify.assert_called_once_with(appeal, 'approved')


class SurveyServicesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from surveys.models import Survey, SurveyQuestion

        cls.survey = Survey.objects.create(
            title='Engagement',
            description='Annual survey',
            start_date=date.today(),
            end_date=date(2099, 12, 31),
            status='active',
            is_anonymous=True,
        )
        cls.question = SurveyQuestion.objects.create(
            survey=cls.survey,
            question_text='How satisfied are you?',
            question_type='rating',
            order=1,
        )

    def test_submit_survey_responses(self):
        from surveys.services import submit_survey_responses

        result = submit_survey_responses(
            survey=self.survey,
            respondent=None,
            answers=[{'question_id': self.question.id, 'response_rating': 5}],
        )
        self.assertIn('submitted successfully', result['detail'])

    def test_build_survey_results(self):
        from surveys.models import SurveyResponse
        from surveys.services import build_survey_results

        SurveyResponse.objects.create(
            survey=self.survey,
            question=self.question,
            response_rating=4,
        )
        results = build_survey_results(self.survey)
        self.assertEqual(results['total_responders'], 1)
        self.assertEqual(len(results['questions']), 1)
        self.assertEqual(results['questions'][0]['average_rating'], 4.0)

