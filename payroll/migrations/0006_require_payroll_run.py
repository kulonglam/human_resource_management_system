import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('payroll', '0005_payrollrun_salary_payroll_run'),
    ]

    operations = [
        migrations.AlterField(
            model_name='salary',
            name='payroll_run',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='salary_records',
                to='payroll.payrollrun',
            ),
        ),
    ]
