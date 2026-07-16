from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('employees', '0003_jobgrade_employee_cost_center_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='employee_number',
            field=models.CharField(editable=False, max_length=30, unique=True),
        ),
    ]
