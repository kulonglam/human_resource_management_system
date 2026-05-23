from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from employees.models import Employee
from departments.models import Department
from .models import (
    Skill, EmployeeSkill, TrainingCourse, TrainingRecord,
    Certification, EmployeeCertification, DevelopmentPlan
)

User = get_user_model()


class SkillTestCase(TestCase):
    def setUp(self):
        self.skill = Skill.objects.create(
            name='Python',
            category='technical',
            description='Python programming language'
        )

    def test_create_skill(self):
        self.assertEqual(self.skill.name, 'Python')
        self.assertEqual(self.skill.category, 'technical')


class EmployeeSkillTestCase(TestCase):
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
        self.skill = Skill.objects.create(name='Python', category='technical')

    def test_add_employee_skill(self):
        emp_skill = EmployeeSkill.objects.create(
            employee=self.employee,
            skill=self.skill,
            proficiency_level='advanced',
            acquired_date=date.today()
        )
        self.assertEqual(str(emp_skill), f'{self.employee.full_name} - Python (advanced)')


class TrainingCourseTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='pass123')
        self.course = TrainingCourse.objects.create(
            title='Python Advanced',
            description='Advanced Python training',
            category='technical',
            provider='Tech Academy',
            duration_hours=40,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=10),
            created_by=self.user
        )

    def test_create_course(self):
        self.assertEqual(self.course.title, 'Python Advanced')
        self.assertEqual(self.course.status, 'planned')
