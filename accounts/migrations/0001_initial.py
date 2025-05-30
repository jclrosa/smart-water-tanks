# Generated by Django 4.2.21 on 2025-05-30 20:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('admin', 'System Administrator'), ('manager', 'Tank Manager'), ('operator', 'Operator'), ('viewer', 'Viewer')], default='viewer', max_length=20)),
                ('phone_number', models.CharField(blank=True, max_length=20)),
                ('organization', models.CharField(blank=True, max_length=200)),
                ('department', models.CharField(blank=True, max_length=100)),
                ('email_notifications', models.BooleanField(default=True)),
                ('sms_notifications', models.BooleanField(default=False)),
                ('alert_threshold', models.CharField(choices=[('all', 'All Alerts'), ('high', 'High & Critical Only'), ('critical', 'Critical Only')], default='high', max_length=10)),
                ('can_manage_tanks', models.BooleanField(default=False)),
                ('can_view_all_tanks', models.BooleanField(default=False)),
                ('can_export_data', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['user__last_name', 'user__first_name'],
            },
        ),
    ]
