# Generated by Django 4.2.11 on 2024-03-22 12:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('src', '0061_sdtask_legal'),
    ]

    operations = [
        migrations.AlterField(
            model_name='simpleonetask',
            name='sys_id',
            field=models.PositiveBigIntegerField(verbose_name='Id Задачи в simple'),
        ),
    ]