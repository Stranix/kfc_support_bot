# Generated by Django 4.2.4 on 2023-10-04 09:11

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('src', '0008_employee_tg_nickname'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='rating',
            field=models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MaxValueValidator(5)], verbose_name='Оценка'),
        ),
    ]
