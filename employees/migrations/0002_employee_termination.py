# Generated migration for Employee termination fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='termination_date',
            field=models.DateField(blank=True, null=True, help_text='Employee exit date'),
        ),
        migrations.AddField(
            model_name='employee',
            name='exit_reason',
            field=models.CharField(
                blank=True,
                choices=[
                    ('resignation', 'Resignation'),
                    ('termination', 'Termination'),
                    ('retirement', 'Retirement'),
                    ('contract_end', 'Contract End'),
                    ('medical', 'Medical Grounds'),
                    ('redundancy', 'Redundancy'),
                    ('other', 'Other'),
                ],
                help_text='Reason for employee termination',
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='employee',
            name='exit_notes',
            field=models.TextField(blank=True, help_text='Additional notes about termination'),
        ),
    ]
