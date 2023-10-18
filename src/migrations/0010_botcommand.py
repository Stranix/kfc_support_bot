# Generated by Django 4.2.4 on 2023-10-09 09:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('src', '0009_task_rating'),
    ]

    operations = [
        migrations.CreateModel(
            name='BotCommand',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=25, unique=True, verbose_name='Команда')),
                ('description', models.TextField(blank=True, default='', verbose_name='Описание команды')),
                ('groups', models.ManyToManyField(blank=True, related_name='bot_commands', to='src.group', verbose_name='Доступна для групп')),
            ],
            options={
                'verbose_name': 'Команда Бота',
                'verbose_name_plural': 'Команды Бота',
            },
        ),
    ]