# Generated migration for LeaveBalance model

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('leaves', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LeaveBalance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('leave_type', models.CharField(choices=[('annual', 'Annual Leave'), ('sick', 'Sick Leave'), ('maternity', 'Maternity Leave'), ('paternity', 'Paternity Leave'), ('unpaid', 'Unpaid Leave')], max_length=20)),
                ('year', models.IntegerField(default=django.utils.timezone.now().year)),
                ('total_days', models.IntegerField(default=0, help_text='Total leave days allocated')),
                ('used_days', models.FloatField(default=0, help_text='Days already used')),
                ('pending_days', models.FloatField(default=0, help_text='Days in pending approval')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leave_balances', to='employees.employee')),
            ],
            options={
                'ordering': ('year', 'leave_type'),
                'unique_together': {('employee', 'leave_type', 'year')},
            },
        ),
    ]
