from django.db import migrations, models


def use_uganda_shillings(apps, schema_editor):
    JobOffer = apps.get_model('recruitment', 'JobOffer')
    JobOffer.objects.filter(currency='KES').update(currency='UGX')


class Migration(migrations.Migration):
    dependencies = [
        ('recruitment', '0004_seed_enterprise_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='joboffer',
            name='currency',
            field=models.CharField(default='UGX', max_length=3),
        ),
        migrations.RunPython(use_uganda_shillings, migrations.RunPython.noop),
    ]
