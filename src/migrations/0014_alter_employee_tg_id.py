# Generated by Django 4.2.7 on 2023-11-07 07:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('src', '0013_alter_group_rights'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='tg_id',
            field=models.PositiveBigIntegerField(db_index=True, unique=True, verbose_name='Telegram_id'),
        ),
    ]
