# Generated by Django 4.2.8 on 2024-02-01 19:32

from django.db import migrations


def edit_applicant_performer_in_sd_tasks(apps, _):
    """
    Меняем привязку пользователей в задачах поддержки
    Employee -> CustomUser
    """
    CustomUser = apps.get_model('src', 'CustomUser')
    SDTask = apps.get_model('src', 'SDTask')

    for task in SDTask.objects.iterator():
        try:
            task_applicant = CustomUser.objects.get(name=task.applicant.name)
            task_performer = CustomUser.objects.get(name=task.performer.name)
            task.new_applicant = task_applicant
            task.new_performer = task_performer
            task.save()
        except CustomUser.DoesNotExist:
            print('Задачи поддержки. Проблема с задачей:', task.number)
        except AttributeError:
            print('Задачи поддержки(а). Проблема с задачей:', task.number)


class Migration(migrations.Migration):

    dependencies = [
        ('src', '0038_sdtask_new_applicant_sdtask_new_performer'),
    ]

    operations = [
        migrations.RunPython(edit_applicant_performer_in_sd_tasks),
    ]
