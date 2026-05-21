# Generated migration for AuditLog model

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('create', 'Create'), ('update', 'Update'), ('delete', 'Delete'), ('approve', 'Approve'), ('reject', 'Reject'), ('login', 'Login'), ('logout', 'Logout'), ('export', 'Export'), ('other', 'Other')], default='other', max_length=20)),
                ('model_name', models.CharField(help_text='Name of the model/object affected', max_length=100)),
                ('object_id', models.IntegerField(blank=True, help_text='ID of the affected object', null=True)),
                ('object_description', models.CharField(blank=True, help_text='Description of the affected object', max_length=255)),
                ('details', models.TextField(blank=True, help_text='Additional details about the action')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-timestamp',),
            },
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['-timestamp'], name='accounts_au_timesta_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['user', '-timestamp'], name='accounts_au_user_id_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['action', '-timestamp'], name='accounts_au_action_idx'),
        ),
    ]
