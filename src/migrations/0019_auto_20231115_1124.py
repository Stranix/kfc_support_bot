# Generated by Django 4.2.7 on 2023-11-15 08:24

from django.db import migrations


def add_new_group_and_bot_command(apps, schema_editor):
    """
    Добавляем новую группу и команду для бота.
    """
    group = apps.get_model('src', 'Group')
    group.objects.update_or_create(name='Диспетчеры')

    bot_command = apps.get_model('src', 'BotCommand')
    bot_command.objects.update_or_create(
        name='/unclosed_tasks',
        description='Показать все не закрытые задачи за все время',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('src', '0018_task_closing_comment_task_doc_path_and_more'),
    ]

    operations = [
        migrations.RunPython(add_new_group_and_bot_command),
    ]