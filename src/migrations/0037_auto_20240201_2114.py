# Generated by Django 4.2.8 on 2024-02-01 18:14

from django.db import migrations


def move_users(apps, schema_editor):
    """
    Двигаем пользователей из модели Employee в кастомную модель
    пользователей Django CustomUser
    """
    CustomUser = apps.get_model('src', 'CustomUser')
    Employee = apps.get_model('src', 'Employee')
    CustomGroup = apps.get_model('src', 'CustomGroup')

    for employee in Employee.objects.iterator():
        try:
            user, _ = CustomUser.objects.update_or_create(
                name=employee.name,
                defaults={
                    'login': f'user_{employee.id}',
                    'tg_id': employee.tg_id,
                    'tg_nickname': employee.tg_nickname,
                    'dispatcher_name': employee.dispatcher_name,
                    'is_active': employee.is_active,
                    'date_joined': employee.registered_at,
                },
            )
            for employee_group in employee.groups.all():
                group = CustomGroup.objects.get(name=employee_group.name)
                user.groups.add(group)
            user.save()
        except Exception:
            print('Не смог перенести пользователя:', employee.name)


class Migration(migrations.Migration):

    dependencies = [
        ('src', '0036_auto_20240201_2056'),
    ]

    operations = [
        migrations.RunPython(move_users),
    ]