# Generated migration for Salary timestamps

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='salary',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='salary',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
