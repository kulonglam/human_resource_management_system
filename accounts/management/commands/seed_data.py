import os
from datetime import date

from django.core.management.base import BaseCommand, CommandError
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


def resolve_seed_password(spec):
    """Env password wins. Hosted (DATABASE_URL) rejects published demo defaults."""
    from_env = os.environ.get(spec['password_env'])
    if from_env:
        return from_env
    hosted = bool(os.environ.get('DATABASE_URL'))
    allow_defaults = os.environ.get('ALLOW_DEFAULT_SEED_PASSWORDS', '').lower() in (
        '1', 'true', 'yes',
    )
    if hosted and not allow_defaults:
        raise CommandError(
            f'Set {spec["password_env"]} before seeding on a hosted database. '
            'Demo defaults are blocked when DATABASE_URL is set '
            '(override with ALLOW_DEFAULT_SEED_PASSWORDS=1 only for temporary demos).'
        )
    return spec['default_password']


class Command(BaseCommand):
    help = 'Create default roles, login users, and sample HR data for local/Render deploys.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-password',
            action='store_true',
            help='Reset passwords for seed users from environment variables (or defaults).',
        )
        parser.add_argument(
            '--demo',
            action='store_true',
            help='Also seed full demo data for every major page (see seed_demo_data).',
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
        passwords_used = {}

        for spec in DEFAULT_USERS:
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

            if created or reset_password:
                password = resolve_seed_password(spec)
                passwords_used[spec['username']] = password
                user.set_password(password)
                if reset_password and not created:
                    user.role = role
                    user.is_superuser = spec['is_superuser']
                    user.is_staff = spec['is_staff']
                user.save()
                if created:
                    created_users.append(spec['username'])
                else:
                    updated_users.append(spec['username'])
            elif not os.environ.get('DATABASE_URL'):
                # Local: show known defaults for convenience without resetting.
                passwords_used[spec['username']] = os.environ.get(
                    spec['password_env'], spec['default_password']
                )

        dept, dept_created = Department.objects.get_or_create(
            name='Human Resources',
            defaults={
                'location': 'Kampala HQ',
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
                    'address': 'Kampala, Uganda',
                    'emergency_contact': '0700000009',
                    'job_title': emp_data['job_title'],
                    'department': dept,
                    'date_joined': date(2022, 1, 10),
                    'account_number': '1234567890',
                    'bank': 'Centenary Bank',
                    'salary': 85000,
                },
            )
            if created:
                employees_created += 1

        from django.core.management import call_command
        from leave_policies.services import sync_all_employees

        call_command('seed_workflows')
        sync_summary = sync_all_employees()

        self.stdout.write(self.style.SUCCESS('Seed data ready.'))
        if dept_created:
            self.stdout.write(f'  Department created: {dept.name}')
        if employees_created:
            self.stdout.write(f'  Sample employees created: {employees_created}')
        self.stdout.write(f'  Leave policy allocations synced: {sync_summary["allocations"]}')
        if created_users:
            self.stdout.write(f'  Users created: {", ".join(created_users)}')
        if updated_users:
            self.stdout.write(f'  Passwords reset for: {", ".join(updated_users)}')

        self.stdout.write('')
        if os.environ.get('DATABASE_URL') and not os.environ.get('ALLOW_DEFAULT_SEED_PASSWORDS'):
            self.stdout.write(
                self.style.WARNING(
                    'Login usernames (passwords come from SEED_*_PASSWORD env vars; not printed):'
                )
            )
            for spec in DEFAULT_USERS:
                self.stdout.write(f'  {spec["role"].upper():8}  username: {spec["username"]}')
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Local login credentials (override with SEED_*_PASSWORD env vars):'
                )
            )
            for spec in DEFAULT_USERS:
                password = passwords_used.get(
                    spec['username'],
                    os.environ.get(spec['password_env'], spec['default_password']),
                )
                self.stdout.write(
                    f'  {spec["role"].upper():8}  username: {spec["username"]:<10}  '
                    f'password: {password}'
                )

        if options.get('demo'):
            from django.core.management import call_command
            call_command('seed_demo_data', skip_base=True)
