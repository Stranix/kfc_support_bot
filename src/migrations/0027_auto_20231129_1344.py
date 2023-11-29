# Generated by Django 4.2.7 on 2023-11-29 10:44

from django.db import migrations


def move_sd_task_applicant(apps, schema_editor):
    """
    Сопоставляем постановщика задачи с Сотрудником.
    """
    SDTask = apps.get_model('src', 'SDTask')
    Employee = apps.get_model('src', 'Employee')

    for task in SDTask.objects.iterator():
        if not task.applicant:
            continue
        try:
            applicant = Employee.objects.get(name=task.applicant)
            task.tmp_applicant = applicant
            task.save()
        except Employee.DoesNotExist:
            print('Не смог найти работника с именем', task.applicant)
            print('Проблемная задача', task.number)


class Migration(migrations.Migration):

    dependencies = [
        ('src', '0026_sdtask_tmp_applicant_alter_employee_groups'),
    ]

    operations = [
        migrations.RunPython(move_sd_task_applicant),
    ]
