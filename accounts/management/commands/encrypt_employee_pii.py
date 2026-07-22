from django.core.management.base import BaseCommand
from django.db import connection

from accounts.encryption import encrypt_value, is_encrypted
from employees.models import Employee

PII_FIELDS = (
    'national_id_number',
    'tax_identification_number',
    'nssf_number',
    'account_number',
    'bank',
    'salary',
)


class Command(BaseCommand):
    help = 'Encrypt existing plaintext employee PII fields at rest.'

    def handle(self, *args, **options):
        table = Employee._meta.db_table
        columns = ', '.join(['id', *PII_FIELDS])
        updated = 0

        with connection.cursor() as cursor:
            # Identifiers come from Django model meta / fixed field list, not user input.
            cursor.execute(f'SELECT {columns} FROM {table}')  # nosec B608
            rows = cursor.fetchall()

        for row in rows:
            employee_id = row[0]
            changes = {}
            for index, field in enumerate(PII_FIELDS, start=1):
                raw = row[index]
                if raw and not is_encrypted(raw):
                    changes[field] = encrypt_value(raw)
            if not changes:
                continue
            set_clause = ', '.join(f'{field} = %s' for field in changes)
            params = [*changes.values(), employee_id]
            with connection.cursor() as cursor:
                sql = f'UPDATE {table} SET {set_clause} WHERE id = %s'  # nosec B608
                cursor.execute(sql, params)
            updated += 1

        self.stdout.write(self.style.SUCCESS(f'Encrypted PII for {updated} employee(s).'))
