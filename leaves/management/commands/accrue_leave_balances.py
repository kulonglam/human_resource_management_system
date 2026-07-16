from django.core.management.base import BaseCommand

from leaves.services import accrue_monthly_balances, carry_forward_balances


class Command(BaseCommand):
    help = 'Accrue monthly leave balances and optionally carry forward annual leave.'

    def add_arguments(self, parser):
        parser.add_argument('--year', type=int)
        parser.add_argument('--month', type=int)
        parser.add_argument('--carry-forward', action='store_true')
        parser.add_argument('--from-year', type=int)
        parser.add_argument('--to-year', type=int)

    def handle(self, *args, **options):
        result = accrue_monthly_balances(options.get('year'), options.get('month'))
        self.stdout.write(self.style.SUCCESS(f'Accrual complete: {result}'))

        if options.get('carry_forward'):
            cf = carry_forward_balances(
                options.get('from_year') or (result['year'] - 1),
                options.get('to_year') or result['year'],
            )
            self.stdout.write(self.style.SUCCESS(f'Carry-forward complete: {cf}'))
