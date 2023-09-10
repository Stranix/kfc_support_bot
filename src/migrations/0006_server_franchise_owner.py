# Generated by Django 4.2.4 on 2023-09-09 14:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('src', '0005_alter_server_ip'),
    ]

    operations = [
        migrations.AddField(
            model_name='server',
            name='franchise_owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='servers', to='src.franchiseowner', verbose_name='Франшиза'),
        ),
    ]