# Generated by Django 4.2.8 on 2024-03-21 17:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('src', '0060_simpleoneciservice_simpleonecompany_simpleonecred_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sdtask',
            name='legal',
            field=models.CharField(blank=True, max_length=25, null=True, verbose_name='Выбранное юр лицо'),
        ),
    ]
