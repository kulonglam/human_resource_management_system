"""Seed realistic demo data across all major HRMIS pages for full manual/E2E testing."""

from __future__ import annotations

from datetime import date, time, timedelta
from decimal import Decimal

from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import CustomUser, Notification
from assets.models import Asset, AssetAssignment
from attendance.models import Attendance, AttendanceDevice, OvertimeRecord, Timesheet
from attendance.services import create_attendance_device
from benefits.models import Benefit, EmployeeBenefit
from departments.models import Department
from discipline.models import Discipline, DisciplineAppeal
from documents.models import HRDocument
from employees.models import (
    Employee,
    EmploymentContract,
    EmploymentHistory,
    JobGrade,
    Position,
)
from expenses.models import Expense, ExpenseCategory
from exits.models import ExitChecklist, ExitProcess
from kin.models import Kin
from leave_policies.models import LeavePolicy
from leave_policies.services import sync_all_employees
from leaves.models import Leave
from payroll.models import PayrollRun, Salary
from performance.models import FeedbackRound, PerformanceAppraisal, PerformanceGoal
from recruitment.models import Application, JobPosting, OfferTemplate
from shifts.models import Shift, ShiftAssignment
from surveys.models import Survey, SurveyQuestion
from training.models import (
    Certification,
    DevelopmentPlan,
    EmployeeCertification,
    EmployeeSkill,
    Skill,
    TrainingCourse,
    TrainingRecord,
)


class Command(BaseCommand):
    help = (
        'Seed demo data for all major modules (employees, leave, attendance, payroll, '
        'recruitment, performance, training, ops modules, settings packs). Idempotent.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-base',
            action='store_true',
            help='Do not call seed_data / seed_workflows first (assumes users already exist).',
        )
        parser.add_argument(
            '--reset-password',
            action='store_true',
            help='Forwarded to seed_data when base seeding runs.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if not options['skip_base']:
            call_command('seed_data', reset_password=options['reset_password'])
            call_command('seed_compliance_evidence')
            call_command('seed_document_access')
            try:
                call_command('seed_uganda_holidays')
            except Exception as exc:  # pragma: no cover - optional calendar data
                self.stdout.write(self.style.WARNING(f'Holidays seed skipped: {exc}'))

        admin = CustomUser.objects.filter(username='admin').first()
        manager = CustomUser.objects.filter(username='manager').first()
        employee_user = CustomUser.objects.filter(username='employee').first()

        counts = {}
        hr, eng, fin = self._seed_departments(counts)
        grades = self._seed_grades(counts)
        positions = self._seed_positions(hr, eng, fin, grades, counts)
        jane, john, alice, bob = self._seed_employees(hr, eng, fin, positions, grades, counts)
        if manager and jane:
            manager.managed_department = hr
            manager.save(update_fields=['managed_department'])

        self._seed_workforce(jane, john, alice, counts)
        self._seed_leave(jane, john, alice, counts)
        self._seed_attendance(jane, john, alice, counts)
        self._seed_payroll(jane, john, alice, bob, admin, counts)
        self._seed_recruitment(hr, eng, admin, counts)
        self._seed_performance(jane, john, alice, admin, counts)
        self._seed_training(john, alice, counts)
        self._seed_documents(jane, john, counts)
        self._seed_ops_modules(jane, john, alice, bob, counts)
        self._seed_surveys(counts)
        self._seed_notifications(admin, manager, employee_user, counts)

        sync_summary = sync_all_employees()
        counts['leave_allocations'] = sync_summary.get('allocations', 0)

        self.stdout.write(self.style.SUCCESS('Full demo seed complete.'))
        for key, value in sorted(counts.items()):
            self.stdout.write(f'  {key}: {value}')
        self.stdout.write('')
        self.stdout.write('Log in and browse every sidebar page - sample rows should appear.')
        self.stdout.write('  Usernames: admin, manager, employee')
        self.stdout.write(
            '  Passwords: SEED_*_PASSWORD env vars on hosted DBs; '
            'local defaults are Admin@HRMIS2026! / Manager@HRMIS2026! / Employee@HRMIS2026!'
        )

    def _bump(self, counts, key, created):
        if created:
            counts[key] = counts.get(key, 0) + 1

    def _seed_departments(self, counts):
        specs = [
            ('Human Resources', 'Kampala HQ', 'Jane Manager', '0700000001'),
            ('Engineering', 'Kampala HQ', 'Alice Engineer', '0700000002'),
            ('Finance', 'Kampala HQ', 'Bob Finance', '0700000003'),
        ]
        depts = []
        for name, location, manager_name, contact in specs:
            dept, created = Department.objects.get_or_create(
                name=name,
                defaults={
                    'location': location,
                    'history': f'{name} department (demo).',
                    'manager_name': manager_name,
                    'manager_contact': contact,
                },
            )
            self._bump(counts, 'departments', created)
            depts.append(dept)
        return depts[0], depts[1], depts[2]

    def _seed_grades(self, counts):
        grades = {}
        for code, name, lo, hi in (
            ('G3', 'Officer', 1_500_000, 3_000_000),
            ('G4', 'Senior Officer', 3_000_000, 5_000_000),
            ('G5', 'Manager', 5_000_000, 9_000_000),
        ):
            grade, created = JobGrade.objects.get_or_create(
                code=code,
                defaults={'name': name, 'minimum_salary': lo, 'maximum_salary': hi},
            )
            self._bump(counts, 'job_grades', created)
            grades[code] = grade
        return grades

    def _seed_positions(self, hr, eng, fin, grades, counts):
        specs = [
            ('HR-MGR', 'HR Manager', hr, 'G5'),
            ('ENG-SE', 'Software Engineer', eng, 'G4'),
            ('FIN-AN', 'Finance Analyst', fin, 'G3'),
            ('HR-AN', 'HR Analyst', hr, 'G3'),
        ]
        positions = {}
        for code, title, dept, grade_code in specs:
            pos, created = Position.objects.get_or_create(
                code=code,
                defaults={
                    'title': title,
                    'department': dept,
                    'grade': grades.get(grade_code),
                    'description': f'Demo position: {title}',
                    'is_active': True,
                },
            )
            self._bump(counts, 'positions', created)
            positions[code] = pos
        return positions

    def _employee_defaults(self, **extra):
        base = {
            'date_of_birth': date(1992, 3, 12),
            'mobile': '0700123456',
            'address': 'Kampala, Uganda',
            'emergency_contact': '0700987654',
            'date_joined': date(2023, 2, 1),
            'account_number': '9988776655',
            'bank': 'Stanbic Bank',
            'national_id_number': 'CM9000000000000',
            'tax_identification_number': '1000000000',
            'nssf_number': 'NSSF000001',
            'is_active': True,
        }
        base.update(extra)
        return base

    def _seed_employees(self, hr, eng, fin, positions, grades, counts):
        specs = [
            {
                'email': 'manager@hrmis.local',
                'first_name': 'Jane',
                'last_name': 'Manager',
                'gender': 'Female',
                'job_title': 'HR Manager',
                'department': hr,
                'position': positions.get('HR-MGR'),
                'grade': grades.get('G5'),
                'salary': Decimal('7500000'),
                'device_badge_id': 'BADGE-JANE',
            },
            {
                'email': 'employee@hrmis.local',
                'first_name': 'John',
                'last_name': 'Employee',
                'gender': 'Male',
                'job_title': 'HR Analyst',
                'department': hr,
                'position': positions.get('HR-AN'),
                'grade': grades.get('G3'),
                'salary': Decimal('2800000'),
                'device_badge_id': 'BADGE-JOHN',
            },
            {
                'email': 'alice@hrmis.local',
                'first_name': 'Alice',
                'last_name': 'Engineer',
                'gender': 'Female',
                'job_title': 'Software Engineer',
                'department': eng,
                'position': positions.get('ENG-SE'),
                'grade': grades.get('G4'),
                'salary': Decimal('4500000'),
                'device_badge_id': 'BADGE-ALICE',
            },
            {
                'email': 'bob@hrmis.local',
                'first_name': 'Bob',
                'last_name': 'Finance',
                'gender': 'Male',
                'job_title': 'Finance Analyst',
                'department': fin,
                'position': positions.get('FIN-AN'),
                'grade': grades.get('G3'),
                'salary': Decimal('3200000'),
                'device_badge_id': 'BADGE-BOB',
                'is_active': False,
                'termination_date': date(2025, 11, 30),
                'exit_reason': 'resignation',
            },
        ]
        employees = []
        for spec in specs:
            email = spec.pop('email')
            emp, created = Employee.objects.get_or_create(
                email=email,
                defaults=self._employee_defaults(**spec),
            )
            self._bump(counts, 'employees', created)
            employees.append(emp)

        # Link supervisor
        jane, john, alice, bob = employees
        if john.supervisor_id != jane.id:
            john.supervisor = jane
            john.save(update_fields=['supervisor'])
        return jane, john, alice, bob

    def _seed_workforce(self, jane, john, alice, counts):
        for emp, ctype, salary in (
            (jane, 'permanent', Decimal('7500000')),
            (john, 'permanent', Decimal('2800000')),
            (alice, 'fixed_term', Decimal('4500000')),
        ):
            _, created = EmploymentContract.objects.get_or_create(
                employee=emp,
                contract_type=ctype,
                start_date=emp.date_joined,
                defaults={
                    'salary': salary,
                    'end_date': date(2027, 12, 31) if ctype == 'fixed_term' else None,
                    'status': 'active',
                },
            )
            self._bump(counts, 'contracts', created)

        _, created = EmploymentHistory.objects.get_or_create(
            employee=john,
            event_type='promotion',
            effective_date=date(2024, 6, 1),
            defaults={'notes': 'Promoted from HR Assistant to HR Analyst (demo).'},
        )
        self._bump(counts, 'employment_history', created)

        _, created = Kin.objects.get_or_create(
            employee=john,
            first_name='Mary',
            last_name='Employee',
            defaults={
                'address': 'Entebbe, Uganda',
                'occupation': 'Teacher',
                'mobile': '0700111222',
                'relationship': 'Spouse',
            },
        )
        self._bump(counts, 'kin', created)

    def _seed_leave(self, jane, john, alice, counts):
        for name, leave_type, days in (
            ('Annual Leave', 'annual', 21),
            ('Sick Leave', 'sick', 14),
            ('Maternity Leave', 'maternity', 60),
        ):
            _, created = LeavePolicy.objects.get_or_create(
                name=name,
                defaults={
                    'leave_type': leave_type,
                    'days_per_year': days,
                    'applicable_to_all': True,
                    'is_active': True,
                    'description': f'Demo {name} policy.',
                },
            )
            self._bump(counts, 'leave_policies', created)

        today = timezone.localdate()
        leave_specs = [
            (john, 'annual', today + timedelta(days=14), today + timedelta(days=16), 'Family trip', 'pending'),
            (alice, 'sick', today - timedelta(days=10), today - timedelta(days=9), 'Flu', 'approved'),
            (jane, 'annual', today + timedelta(days=30), today + timedelta(days=32), 'Personal', 'pending'),
        ]
        for emp, leave_type, start, end, reason, status in leave_specs:
            _, created = Leave.objects.get_or_create(
                employee=emp,
                leave_type=leave_type,
                start_date=start,
                end_date=end,
                defaults={'reason': reason, 'status': status},
            )
            self._bump(counts, 'leaves', created)

    def _seed_attendance(self, jane, john, alice, counts):
        today = timezone.localdate()
        for emp in (jane, john, alice):
            for offset in range(1, 6):
                day = today - timedelta(days=offset)
                if day.weekday() >= 5:
                    continue
                _, created = Attendance.objects.get_or_create(
                    employee=emp,
                    date=day,
                    defaults={
                        'time_in': time(8, 30),
                        'time_out': time(17, 15),
                        'status': 'present',
                        'source': 'manual',
                    },
                )
                self._bump(counts, 'attendance', created)
                _, created = Timesheet.objects.get_or_create(
                    employee=emp,
                    date=day,
                    defaults={
                        'clock_in': time(8, 30),
                        'clock_out': time(17, 15),
                        'regular_hours': Decimal('8.00'),
                        'project_code': 'HRMIS-DEMO',
                        'notes': 'Regular work day',
                        'status': 'approved' if offset > 2 else 'submitted',
                    },
                )
                self._bump(counts, 'timesheets', created)

        _, created = OvertimeRecord.objects.get_or_create(
            employee=john,
            date=today - timedelta(days=2),
            defaults={
                'hours': Decimal('2.00'),
                'reason': 'Month-end payroll support',
                'status': 'pending',
            },
        )
        self._bump(counts, 'overtime', created)

        if not AttendanceDevice.objects.filter(device_code='HQ-GATE-01').exists():
            create_attendance_device(
                name='HQ Main Gate',
                device_code='HQ-GATE-01',
                device_type='fingerprint',
                location='Kampala HQ Lobby',
            )
            self._bump(counts, 'attendance_devices', True)

        shift, created = Shift.objects.get_or_create(
            shift_name='Day Shift',
            defaults={
                'start_time': time(8, 0),
                'end_time': time(17, 0),
                'working_hours': Decimal('8.00'),
                'is_active': True,
            },
        )
        self._bump(counts, 'shifts', created)
        for emp in (john, alice):
            _, created = ShiftAssignment.objects.get_or_create(
                employee=emp,
                shift=shift,
                start_date=date(2026, 1, 1),
                defaults={'end_date': None, 'status': 'active'},
            )
            self._bump(counts, 'shift_assignments', created)

    def _seed_payroll(self, jane, john, alice, bob, admin, counts):
        today = timezone.localdate()
        month, year = today.month, today.year
        run, created = PayrollRun.objects.get_or_create(
            month=month,
            year=year,
            defaults={'notes': 'Current month demo run', 'created_by': admin, 'status': 'draft'},
        )
        self._bump(counts, 'payroll_runs', created)

        for emp, basic in (
            (jane, Decimal('7500000')),
            (john, Decimal('2800000')),
            (alice, Decimal('4500000')),
        ):
            _, created = Salary.objects.get_or_create(
                employee=emp,
                month=month,
                year=year,
                defaults={
                    'payroll_run': run,
                    'basic_salary': basic,
                    'allowances': Decimal('200000'),
                    'taxable_benefits': Decimal('0'),
                    'deductions': Decimal('50000'),
                    'status': 'draft',
                },
            )
            self._bump(counts, 'salaries', created)

        # Prior paid month for "paid" status testing
        prev = date(year, month, 1) - timedelta(days=1)
        paid_run, created = PayrollRun.objects.get_or_create(
            month=prev.month,
            year=prev.year,
            defaults={
                'notes': 'Previous month — paid',
                'created_by': admin,
                'status': 'paid',
                'approved_by': admin,
                'approved_at': timezone.now() - timedelta(days=20),
                'paid_at': timezone.now() - timedelta(days=15),
            },
        )
        self._bump(counts, 'payroll_runs', created)
        if paid_run.status != 'paid':
            paid_run.status = 'paid'
            paid_run.paid_at = paid_run.paid_at or timezone.now() - timedelta(days=15)
            paid_run.save(update_fields=['status', 'paid_at', 'updated_at'])

        for emp, basic in ((jane, Decimal('7500000')), (john, Decimal('2800000'))):
            sal, created = Salary.objects.get_or_create(
                employee=emp,
                month=prev.month,
                year=prev.year,
                defaults={
                    'payroll_run': paid_run,
                    'basic_salary': basic,
                    'allowances': Decimal('200000'),
                    'status': 'paid',
                    'is_paid': True,
                    'paid_on': prev.replace(day=28) if prev.day >= 28 else prev,
                },
            )
            if not created and sal.status != 'paid':
                sal.status = 'paid'
                sal.is_paid = True
                sal.save()
            self._bump(counts, 'salaries', created)

    def _seed_recruitment(self, hr, eng, admin, counts):
        deadline = timezone.localdate() + timedelta(days=30)
        job, created = JobPosting.objects.get_or_create(
            title='Software Engineer',
            department=eng,
            defaults={
                'description': 'Build and maintain the HRMIS platform.',
                'requirements': 'Python/Django, React, 3+ years experience.',
                'deadline': deadline,
                'is_open': True,
            },
        )
        self._bump(counts, 'jobs', created)

        _, created = Application.objects.get_or_create(
            job=job,
            email='candidate@example.com',
            defaults={
                'first_name': 'Chris',
                'last_name': 'Candidate',
                'phone': '0700555666',
                'status': 'shortlisted',
                'cover_letter': 'Excited to join the engineering team.',
            },
        )
        self._bump(counts, 'applications', created)

        _, created = OfferTemplate.objects.get_or_create(
            name='Standard Offer',
            defaults={
                'body': (
                    'Dear {{candidate_name}},\n\n'
                    'We are pleased to offer you the position of {{job_title}} '
                    'in {{department}} starting {{start_date}} at UGX {{salary}}.\n\n'
                    'Regards,\nHR'
                ),
            },
        )
        self._bump(counts, 'offer_templates', created)

        JobPosting.objects.get_or_create(
            title='HR Intern',
            department=hr,
            defaults={
                'description': 'Support HR operations.',
                'requirements': 'Diploma or undergraduate student.',
                'deadline': deadline,
                'is_open': True,
            },
        )

    def _seed_performance(self, jane, john, alice, admin, counts):
        today = timezone.localdate()
        _, created = PerformanceGoal.objects.get_or_create(
            employee=john,
            goal_title='Improve leave turnaround',
            defaults={
                'goal_description': 'Reduce average leave approval time to under 2 days.',
                'start_date': date(today.year, 1, 1),
                'end_date': date(today.year, 12, 31),
                'target_metric': '≤ 2 days average',
                'progress': 40,
                'status': 'in_progress',
                'priority': 'high',
            },
        )
        self._bump(counts, 'goals', created)

        _, created = PerformanceAppraisal.objects.get_or_create(
            employee=alice,
            appraisal_period_start=date(today.year - 1, 1, 1),
            appraisal_period_end=date(today.year - 1, 12, 31),
            defaults={
                'job_knowledge': 4,
                'work_quality': 4,
                'productivity': 4,
                'communication': 3,
                'teamwork': 4,
                'initiative': 4,
                'reliability': 5,
                'overall_rating': 4,
                'strengths': 'Strong delivery and ownership.',
                'areas_for_improvement': 'Broader stakeholder communication.',
                'next_goals': 'Lead a cross-team initiative.',
                'status': 'completed',
                'appraiser': admin,
            },
        )
        self._bump(counts, 'appraisals', created)

        _, created = FeedbackRound.objects.get_or_create(
            name=f'{today.year} Mid-year feedback',
            defaults={
                'start_date': date(today.year, 6, 1),
                'end_date': date(today.year, 6, 30),
                'status': 'active',
                'description': 'Demo feedback cycle.',
            },
        )
        self._bump(counts, 'feedback_rounds', created)

    def _seed_training(self, john, alice, counts):
        skill, created = Skill.objects.get_or_create(
            name='Python',
            defaults={'category': 'Technical', 'description': 'Python programming'},
        )
        self._bump(counts, 'skills', created)
        _, created = EmployeeSkill.objects.get_or_create(
            employee=alice,
            skill=skill,
            defaults={'proficiency_level': 'advanced', 'acquired_date': date(2022, 1, 1)},
        )
        self._bump(counts, 'employee_skills', created)

        course, created = TrainingCourse.objects.get_or_create(
            title='Workplace Safety',
            defaults={
                'description': 'Mandatory HSE awareness.',
                'category': 'Compliance',
                'provider': 'Internal L&D',
                'duration_hours': 8,
                'start_date': timezone.localdate() - timedelta(days=60),
                'end_date': timezone.localdate() - timedelta(days=59),
                'status': 'completed',
            },
        )
        self._bump(counts, 'courses', created)
        _, created = TrainingRecord.objects.get_or_create(
            employee=john,
            course=course,
            defaults={'status': 'completed', 'completion_date': timezone.localdate() - timedelta(days=50), 'score': 88},
        )
        self._bump(counts, 'training_records', created)

        cert, created = Certification.objects.get_or_create(
            name='First Aid',
            defaults={'issuing_body': 'Red Cross', 'validity_years': 2},
        )
        self._bump(counts, 'certifications', created)
        issue = timezone.localdate() - timedelta(days=200)
        _, created = EmployeeCertification.objects.get_or_create(
            employee=john,
            certification=cert,
            defaults={
                'issue_date': issue,
                'expiry_date': issue + timedelta(days=730),
                'certificate_number': 'FA-DEMO-001',
            },
        )
        self._bump(counts, 'employee_certifications', created)

        _, created = DevelopmentPlan.objects.get_or_create(
            employee=alice,
            title='Tech lead path',
            defaults={
                'description': 'Grow into a tech lead role.',
                'goals': 'Mentor juniors; own a module roadmap.',
                'start_date': date(timezone.localdate().year, 1, 1),
                'end_date': date(timezone.localdate().year, 12, 31),
                'status': 'active',
            },
        )
        self._bump(counts, 'development_plans', created)

    def _seed_documents(self, jane, john, counts):
        if not HRDocument.objects.filter(title='Employee Handbook (Demo)').exists():
            doc = HRDocument(
                title='Employee Handbook (Demo)',
                category='policy',
                description='Demo handbook for testing documents page.',
                requires_acknowledgement=True,
            )
            doc.file.save(
                'employee_handbook_demo.txt',
                ContentFile(b'FCA HRMIS demo employee handbook.\n'),
                save=False,
            )
            doc.save()
            self._bump(counts, 'documents', True)

    def _seed_ops_modules(self, jane, john, alice, bob, counts):
        cat, created = ExpenseCategory.objects.get_or_create(
            name='Travel',
            defaults={'description': 'Transport and travel costs', 'is_active': True},
        )
        self._bump(counts, 'expense_categories', created)
        _, created = Expense.objects.get_or_create(
            employee=john,
            description='Client meeting taxi',
            expense_date=timezone.localdate() - timedelta(days=3),
            defaults={
                'category': cat,
                'amount': Decimal('45000'),
                'status': 'submitted',
            },
        )
        self._bump(counts, 'expenses', created)

        benefit, created = Benefit.objects.get_or_create(
            name='Medical Insurance',
            defaults={
                'benefit_type': 'health',
                'description': 'Company medical cover',
                'employer_contribution': Decimal('200000'),
                'employee_contribution': Decimal('50000'),
                'is_active': True,
            },
        )
        self._bump(counts, 'benefits', created)
        _, created = EmployeeBenefit.objects.get_or_create(
            employee=john,
            benefit=benefit,
            defaults={'enrollment_date': date(2024, 1, 1), 'status': 'active'},
        )
        self._bump(counts, 'employee_benefits', created)

        disc, created = Discipline.objects.get_or_create(
            employee=alice,
            incident_date=timezone.localdate() - timedelta(days=40),
            defaults={
                'discipline_type': 'verbal_warning',
                'reason': 'Late arrivals (demo)',
                'detailed_reason': 'Multiple late clock-ins in a week — demo record.',
                'status': 'active',
            },
        )
        self._bump(counts, 'discipline', created)
        if created:
            DisciplineAppeal.objects.get_or_create(
                discipline=disc,
                defaults={
                    'appeal_date': timezone.localdate() - timedelta(days=35),
                    'appeal_reason': 'Traffic due to road works (demo).',
                    'status': 'pending',
                },
            )
            self._bump(counts, 'discipline_appeals', True)

        asset, created = Asset.objects.get_or_create(
            asset_code='LAP-001',
            defaults={
                'name': 'Dell Latitude 5440',
                'category': 'laptop',
                'purchase_date': date(2024, 5, 10),
                'purchase_price': Decimal('4500000'),
                'current_status': 'assigned',
                'serial_number': 'DL-DEMO-001',
            },
        )
        self._bump(counts, 'assets', created)
        _, created = AssetAssignment.objects.get_or_create(
            asset=asset,
            employee=alice,
            defaults={
                'assignment_date': date(2024, 5, 15),
                'condition_on_assignment': 'new',
                'status': 'assigned',
            },
        )
        self._bump(counts, 'asset_assignments', created)

        if bob and not ExitProcess.objects.filter(employee=bob).exists():
            exit_proc = ExitProcess.objects.create(
                employee=bob,
                exit_date=bob.termination_date or date(2025, 11, 30),
                reason='resignation',
                notes='Demo exit process.',
                status='in_progress',
            )
            ExitChecklist.objects.create(
                exit_process=exit_proc,
                item_name='Return laptop',
                status='completed',
                completion_date=timezone.localdate() - timedelta(days=10),
            )
            ExitChecklist.objects.create(
                exit_process=exit_proc,
                item_name='Clearance from Finance',
                status='pending',
            )
            self._bump(counts, 'exit_processes', True)
            counts['exit_checklist'] = counts.get('exit_checklist', 0) + 2

    def _seed_surveys(self, counts):
        today = timezone.localdate()
        survey, created = Survey.objects.get_or_create(
            title='Employee Engagement (Demo)',
            defaults={
                'survey_type': 'engagement',
                'description': 'Quarterly pulse survey.',
                'start_date': today - timedelta(days=7),
                'end_date': today + timedelta(days=21),
                'is_anonymous': True,
                'status': 'active',
            },
        )
        self._bump(counts, 'surveys', created)
        if created or not survey.questions.exists():
            for idx, text in enumerate(
                (
                    'I am proud to work here.',
                    'I have the tools I need to do my job.',
                    'Any comments?',
                ),
                start=1,
            ):
                qtype = 'text' if idx == 3 else 'rating'
                SurveyQuestion.objects.get_or_create(
                    survey=survey,
                    question_text=text,
                    defaults={'question_type': qtype, 'order': idx, 'is_required': idx < 3},
                )
            self._bump(counts, 'survey_questions', True)

    def _seed_notifications(self, admin, manager, employee_user, counts):
        for user, title, message in (
            (admin, 'Demo: Ops reminder', 'Review Ops Center SLOs and backup status.'),
            (manager, 'Demo: Approvals waiting', 'Check the Approvals inbox for leave/expense requests.'),
            (employee_user, 'Demo: Welcome', 'Your demo employee account is ready. Try Mobile clock and Leaves.'),
        ):
            if not user:
                continue
            _, created = Notification.objects.get_or_create(
                user=user,
                title=title,
                defaults={'message': message, 'is_read': False},
            )
            self._bump(counts, 'notifications', created)
