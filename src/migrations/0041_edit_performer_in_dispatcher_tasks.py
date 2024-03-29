# Generated by Django 4.2.8 on 2024-02-02 07:45

from django.db import migrations


def edit_performer_in_dispatcher_tasks(apps, _):
    """
    Меняем привязку пользователей в задачах диспетчера
    Employee -> CustomUser
    """
    CustomUser = apps.get_model('src', 'CustomUser')
    Dispatcher = apps.get_model('src', 'Dispatcher')

    for task in Dispatcher.objects.iterator():
        try:
            task_performer = CustomUser.objects.get(name=task.performer.name)
            task.new_performer = task_performer
            task.save()
        except CustomUser.DoesNotExist:
            print('Задачи Диспетчера. Проблема с задачей:', task.number)
        except AttributeError:
            print('Задачи Диспетчера(а). Проблема с задачей:', task.number)


class Migration(migrations.Migration):

    dependencies = [
        ('src', '0040_dispatcher_new_performer'),
    ]

    operations = [
        migrations.RunPython(edit_performer_in_dispatcher_tasks),
    ]
