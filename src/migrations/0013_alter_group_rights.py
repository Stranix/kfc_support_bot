# Generated by Django 4.2.6 on 2023-10-29 12:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('src', '0012_auto_20231017_1141'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='rights',
            field=models.ManyToManyField(blank=True, related_name='groups', to='src.right', verbose_name='Права'),
        ),
    ]
