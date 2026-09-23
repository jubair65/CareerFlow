import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DataAccessLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('resource_path', models.CharField(help_text='Path of the requested file or resource', max_length=500)),
                ('action', models.CharField(choices=[('VIEW', 'View Resource'), ('DOWNLOAD', 'Download File'), ('UPLOAD', 'Upload File'), ('DELETE', 'Delete Resource')], default='VIEW', max_length=20)),
                ('status', models.CharField(choices=[('GRANTED', 'Access Granted'), ('DENIED', 'Access Denied')], default='GRANTED', max_length=20)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True, default='')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, help_text='User attempting the access (null if unauthenticated)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='access_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'careerflow_data_access_logs',
                'ordering': ['-timestamp'],
                'indexes': [models.Index(fields=['resource_path', 'status'], name='careerflow__resourc_70041d_idx'), models.Index(fields=['timestamp'], name='careerflow__timesta_8a4363_idx')],
            },
        ),
    ]
