# Generated by Django 4.2.8 on 2024-02-06 15:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('src', '0050_alter_customuser_groups'),
    ]

    operations = [
        migrations.AlterField(
            model_name='botcommand',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='category_bot_commands', to='src.botcommandcategory', verbose_name='Категория команды'),
        ),
        migrations.AlterField(
            model_name='syncreport',
            name='employee',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='sync_reports', to='src.employee', verbose_name='Инициатор'),
        ),
    ]