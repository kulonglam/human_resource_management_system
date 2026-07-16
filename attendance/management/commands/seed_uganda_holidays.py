from django.core.management.base import BaseCommand

from attendance.models import PublicHoliday


UGANDA_HOLIDAYS = [
    ('New Year\'s Day', (1, 1)),
    ('Liberation Day', (1, 26)),
    ('International Women\'s Day', (3, 8)),
    ('Good Friday', None),
    ('Easter Monday', None),
    ('Labour Day', (5, 1)),
    ('Martyrs\' Day', (6, 3)),
    ('National Heroes Day', (6, 9)),
    ('Independence Day', (10, 9)),
    ('Christmas Day', (12, 25)),
    ('Boxing Day', (12, 26)),
]


class Command(BaseCommand):
    help = 'Seed recurring Uganda public holidays (fixed dates; Easter dates must be added manually).'

    def add_arguments(self, parser):
        parser.add_argument('--year', type=int, help='Year to seed fixed-date holidays for')

    def handle(self, *args, **options):
        from datetime import date

        year = options.get('year') or date.today().year
        created = 0
        for name, parts in UGANDA_HOLIDAYS:
            if parts is None:
                continue
            month, day = parts
            holiday_date = date(year, month, day)
            _, was_created = PublicHoliday.objects.get_or_create(
                date=holiday_date,
                defaults={'name': name, 'is_recurring': True},
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Seeded {created} holidays for {year}'))
