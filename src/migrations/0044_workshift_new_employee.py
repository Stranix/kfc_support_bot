# Generated by Django 4.2.8 on 2024-02-02 12:22

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('src', '0043_edit_employee_in_breakshift'),
    ]

    operations = [
        migrations.AddField(
            model_name='workshift',
            name='new_employee',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='new_work_shifts', to=settings.AUTH_USER_MODEL, verbose_name='Сотрудник'),
        ),
    ]