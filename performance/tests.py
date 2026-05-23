from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from employees.models import Employee
from departments.models import Department
from .models import (
    PerformanceGoal, PerformanceAppraisal, FeedbackRound,
    FeedbackRequest, Feedback
)

User = get_user_model()


class PerformanceGoalTestCase(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name='IT', location='Office')
        self.employee = Employee.objects.create(
            first_name='John',
            last_name='Doe',
            date_of_birth='1990-01-01',
            gender='Male',
            email='john@example.com',
            mobile='1234567890',
            address='123 Main St',
            emergency_contact='9876543210',
            job_title='Developer',
            department=self.dept,
            date_joined='2020-01-01',
            account_number='123456789',
            bank='XYZ Bank',
            salary=50000
        )
        self.user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='pass123'
        )

    def test_create_performance_goal(self):
        goal = PerformanceGoal.objects.create(
            employee=self.employee,
            goal_title='Increase Sales',
            goal_description='Increase quarterly sales by 25%',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=90),
            target_metric='25% increase',
            set_by=self.user
        )
        self.assertEqual(goal.employee.full_name, 'John Doe')
        self.assertEqual(goal.status, 'not_started')


class PerformanceAppraisalTestCase(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name='HR', location='Office')
        self.employee = Employee.objects.create(
            first_name='Jane',
            last_name='Smith',
            date_of_birth='1992-05-15',
            gender='Female',
            email='jane@example.com',
            mobile='9876543210',
            address='456 Oak Ave',
            emergency_contact='1234567890',
            job_title='Manager',
            department=self.dept,
            date_joined='2019-01-01',
            account_number='987654321',
            bank='ABC Bank',
            salary=60000
        )
        self.appraiser = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='pass123'
        )

    def test_create_appraisal(self):
        appraisal = PerformanceAppraisal.objects.create(
            employee=self.employee,
            appraisal_period_start=date(2024, 1, 1),
            appraisal_period_end=date(2024, 6, 30),
            appraiser=self.appraiser,
            job_knowledge=4,
            work_quality=5,
            productivity=4,
            communication=4,
            teamwork=5,
            initiative=4,
            reliability=5,
            strengths='Great leadership skills',
            areas_for_improvement='Time management',
            next_goals='Lead team projects',
            status='draft'
        )
        self.assertEqual(appraisal.overall_rating, 4)


class FeedbackTestCase(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name='Finance', location='Office')
        self.employee = Employee.objects.create(
            first_name='Bob',
            last_name='Johnson',
            date_of_birth='1988-03-20',
            gender='Male',
            email='bob@example.com',
            mobile='5555555555',
            address='789 Pine St',
            emergency_contact='4444444444',
            job_title='Analyst',
            department=self.dept,
            date_joined='2021-01-01',
            account_number='111111111',
            bank='DEF Bank',
            salary=45000
        )
        self.feedback_giver = User.objects.create_user(
            username='peer',
            email='peer@example.com',
            password='pass123'
        )
        self.feedback_round = FeedbackRound.objects.create(
            name='Q1 360 Review',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            created_by=self.feedback_giver
        )

    def test_create_feedback_request(self):
        request = FeedbackRequest.objects.create(
            feedback_round=self.feedback_round,
            recipient=self.employee,
            feedback_giver=self.feedback_giver,
            giver_type='peer'
        )
        self.assertEqual(request.status, 'pending')

    def test_submit_feedback(self):
        feedback_request = FeedbackRequest.objects.create(
            feedback_round=self.feedback_round,
            recipient=self.employee,
            feedback_giver=self.feedback_giver,
            giver_type='peer'
        )
        feedback = Feedback.objects.create(
            request=feedback_request,
            communication=4,
            leadership=3,
            teamwork=5,
            reliability=4,
            initiative=4,
            problem_solving=3,
            strengths='Good problem solver',
            areas_for_improvement='Communication skills'
        )
        self.assertIsNotNone(feedback.created_at)
