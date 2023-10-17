# Generated by Django 4.2.4 on 2023-10-17 08:41

from django.db import migrations


def add_default_privilege_groups(apps, schema_editor):
    """
    Заполняем группы доступа
    """
    groups_names = [
        'Администраторы',
        'Ведущие инженеры',
        'Старшие инженеры',
        'Инженеры',
        'Подрядчик',
        'Задачи',
    ]

    group = apps.get_model('src', 'Group')

    for group_name in groups_names:
        group.objects.update_or_create(name=group_name)


class Migration(migrations.Migration):
    dependencies = [
        ('src', '0011_remove_workshift_shift_end_break_at_and_more'),
    ]

    operations = [
        migrations.RunPython(add_default_privilege_groups),
    ]
