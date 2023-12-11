# Generated by Django 4.2.8 on 2023-12-11 09:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('src', '0029_rename_tmp_applicant_sdtask_applicant'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='dispatcher_name',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Имя в диспетчере'),
        ),
        migrations.AddField(
            model_name='sdtask',
            name='is_automatic',
            field=models.BooleanField(default=False, verbose_name='Автоматическая?'),
        ),
        migrations.CreateModel(
            name='Dispatcher',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dispatcher_number', models.PositiveSmallIntegerField(verbose_name='Номер в диспетчере')),
                ('company', models.CharField(blank=True, default='', max_length=100, verbose_name='Компания')),
                ('restaurant', models.CharField(blank=True, default='', max_length=100, verbose_name='Ресторан')),
                ('itsm_number', models.CharField(blank=True, default='', max_length=15, verbose_name='Номер ITSM')),
                ('gsd_numbers', models.CharField(blank=True, default='', max_length=100, verbose_name='Связанные заявки GSD')),
                ('closing_comment', models.TextField(blank=True, null=True, verbose_name='Комментарий закрытия')),
                ('performer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='dispatcher_tasks', to='src.employee', verbose_name='Исполнитель')),
            ],
            options={
                'verbose_name': 'Задача из Диспетчера',
                'verbose_name_plural': 'Задачи из Диспетчера',
            },
        ),
    ]
