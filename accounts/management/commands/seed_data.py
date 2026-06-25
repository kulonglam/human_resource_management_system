import os
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import CustomUser, Role
from departments.models import Department
from employees.models import Employee


DEFAULT_USERS = [
    {
        'username': 'admin',
        'email': 'admin@hrmis.local',
        'password_env': 'SEED_ADMIN_PASSWORD',
        'default_password': 'Admin@HRMIS2026!',
        'role': Role.ADMIN,
        'is_superuser': True,
        'is_staff': True,
        'first_name': 'System',
        'last_name': 'Admin',
    },
    {
        'username': 'manager',
        'email': 'manager@hrmis.local',
        'password_env': 'SEED_MANAGER_PASSWORD',
        'default_password': 'Manager@HRMIS2026!',
        'role': Role.MANAGER,
        'is_superuser': False,
        'is_staff': False,
        'first_name': 'Jane',
        'last_name': 'Manager',
    },
    {
        'username': 'employee',
        'email': 'employee@hrmis.local',
        'password_env': 'SEED_EMPLOYEE_PASSWORD',
        'default_password': 'Employee@HRMIS2026!',
        'role': Role.EMPLOYEE,
        'is_superuser': False,
        'is_staff': False,
        'first_name': 'John',
        'last_name': 'Employee',
    },
]


class Command(BaseCommand):
    help = 'Create default roles, login users, and sample HR data for local/Render deploys.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-password',
            action='store_true',
            help='Reset passwords for seed users from environment variables (or defaults).',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        reset_password = options['reset_password']

        roles = {}
        for role_name in (Role.ADMIN, Role.MANAGER, Role.EMPLOYEE):
            role, _ = Role.objects.get_or_create(name=role_name)
            roles[role_name] = role

        created_users = []
        updated_users = []

        for spec in DEFAULT_USERS:
            password = os.environ.get(spec['password_env'], spec['default_password'])
            role = roles[spec['role']]

            user, created = CustomUser.objects.get_or_create(
                username=spec['username'],
                defaults={
                    'email': spec['email'],
                    'first_name': spec['first_name'],
                    'last_name': spec['last_name'],
                    'role': role,
                    'is_superuser': spec['is_superuser'],
                    'is_staff': spec['is_staff'],
                },
            )

            if created:
                user.set_password(password)
                user.save()
                created_users.append(spec['username'])
            elif reset_password:
                user.set_password(password)
                user.role = role
                user.is_superuser = spec['is_superuser']
                user.is_staff = spec['is_staff']
                user.save()
                updated_users.append(spec['username'])

        dept, dept_created = Department.objects.get_or_create(
            name='Human Resources',
            defaults={
                'location': 'Nairobi HQ',
                'history': 'Core HR department.',
                'manager_name': 'Jane Manager',
                'manager_contact': '0700000001',
            },
        )

        sample_employees = [
            {
                'first_name': 'Jane',
                'last_name': 'Manager',
                'email': 'manager@hrmis.local',
                'job_title': 'HR Manager',
            },
            {
                'first_name': 'John',
                'last_name': 'Employee',
                'email': 'employee@hrmis.local',
                'job_title': 'Analyst',
            },
        ]

        employees_created = 0
        for emp_data in sample_employees:
            _, created = Employee.objects.get_or_create(
                email=emp_data['email'],
                defaults={
                    'first_name': emp_data['first_name'],
                    'last_name': emp_data['last_name'],
                    'date_of_birth': date(1990, 5, 15),
                    'gender': 'Female' if emp_data['first_name'] == 'Jane' else 'Male',
                    'mobile': '0700000000',
                    'address': 'Nairobi, Kenya',
                    'emergency_contact': '0700000009',
                    'job_title': emp_data['job_title'],
                    'department': dept,
                    'date_joined': date(2022, 1, 10),
                    'account_number': '1234567890',
                    'bank': 'KCB Bank',
                    'salary': 85000,
                },
            )
            if created:
                employees_created += 1

        self.stdout.write(self.style.SUCCESS('Seed data ready.'))
        if dept_created:
            self.stdout.write(f'  Department created: {dept.name}')
        if employees_created:
            self.stdout.write(f'  Sample employees created: {employees_created}')
        if created_users:
            self.stdout.write(f'  Users created: {", ".join(created_users)}')
        if updated_users:
            self.stdout.write(f'  Passwords reset for: {", ".join(updated_users)}')

        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Login credentials (set env vars on Render to override passwords):'))
        for spec in DEFAULT_USERS:
            password = os.environ.get(spec['password_env'], spec['default_password'])
            self.stdout.write(f'  {spec["role"].upper():8}  username: {spec["username"]:<10}  password: {password}')
