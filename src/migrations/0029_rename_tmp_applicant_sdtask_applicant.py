# Generated by Django 4.2.7 on 2023-11-29 11:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('src', '0028_remove_sdtask_applicant_alter_sdtask_tmp_applicant'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sdtask',
            old_name='tmp_applicant',
            new_name='applicant',
        ),
    ]
