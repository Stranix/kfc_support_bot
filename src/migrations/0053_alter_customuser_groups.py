# Generated by Django 4.2.8 on 2024-02-07 14:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('src', '0052_alter_breakshift_employee_alter_workshift_employee'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='groups',
            field=models.ManyToManyField(blank=True, related_name='employees', to='src.customgroup', verbose_name='Группа Доступа'),
        ),
    ]
