# Generated by Django 4.2.4 on 2023-09-19 07:25

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('src', '0002_auto_20230918_1252'),
    ]

    operations = [
        migrations.CreateModel(
            name='SyncReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Время запуска синхронизации')),
                ('report', models.JSONField(verbose_name='Отчет')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sync_reports', to='src.employee', verbose_name='Инициатор')),
                ('server_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sync_reports', to='src.servertype', verbose_name='Что синхронизировали')),
            ],
        ),
    ]
