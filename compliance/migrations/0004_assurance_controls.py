from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compliance', '0003_maturity_features'),
    ]

    operations = [
        migrations.AlterField(
            model_name='complianceevidencepack',
            name='control',
            field=models.CharField(
                choices=[
                    ('access_control', 'Access control'),
                    ('encryption', 'Encryption at rest'),
                    ('backup_restore', 'Backup & restore'),
                    ('audit_logging', 'Audit logging'),
                    ('data_retention', 'Data retention'),
                    ('incident_response', 'Incident response'),
                    ('vulnerability_mgmt', 'Vulnerability management'),
                    ('penetration_testing', 'Penetration testing'),
                    ('change_management', 'Change management'),
                    ('availability_slo', 'Availability / SLO'),
                    ('access_reviews', 'Access reviews'),
                ],
                max_length=40,
            ),
        ),
    ]
