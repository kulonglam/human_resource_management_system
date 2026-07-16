from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Register django-q schedules for recurring HR maintenance tasks.'

    def handle(self, *args, **options):
        from django_q.models import Schedule

        schedules = [
            {
                'name': 'hrmis-daily-scheduled-reports',
                'func': 'reports.tasks.task_run_due_scheduled_reports',
                'schedule_type': Schedule.DAILY,
            },
            {
                'name': 'hrmis-monthly-maintenance',
                'func': 'reports.tasks.task_run_scheduled_maintenance',
                'schedule_type': Schedule.MONTHLY,
            },
        ]
        for entry in schedules:
            Schedule.objects.update_or_create(
                name=entry['name'],
                defaults={
                    'func': entry['func'],
                    'schedule_type': entry['schedule_type'],
                    'repeats': -1,
                },
            )
        self.stdout.write(self.style.SUCCESS(f'Registered {len(schedules)} django-q schedule(s).'))
